const puppeteer = require('puppeteer');
const cheerio = require('cheerio');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid'); 
const beautify_html = require('js-beautify').html;

function isImageElement(element) {
    if (element.is('img')) {
        return true;
    }

    // 요소 내 전체 HTML에서 이미지 파일 확장자 검사
    // const htmlContent = element.html().toLowerCase();
    // if (htmlContent.includes('.png') || htmlContent.includes('.jpg') || htmlContent.includes('.jpeg') ||
    //     htmlContent.includes('.gif') || htmlContent.includes('.bmp') || htmlContent.includes('.svg')) {
    //     return true;
    // }

    return false;
}

function findImageElements($) {
    const imageElements = [];

    $('*').each((index, element) => {
        const jqElement = $(element);
        if (isImageElement(jqElement)) { 
            imageElements.push(jqElement);
        }
    });
    return imageElements; // This should always be an array
}

function addTagsToElements(imageElements, fileUuid) {
    imageElements.forEach((element, index) => {
        // 이미지 태그에 ID 추가
        element.attr('id', `image-${fileUuid}-${index}`);
    });
}

class WebLoader {
    constructor(filePath = null, fileUuid = null, screenshotDir = null, htmlSaveDir = null) {
        this.filePath = filePath;
        this.fileUuid = fileUuid;
        this.screenshotDir = screenshotDir;
        this.htmlSaveDir = htmlSaveDir;
    }

    async get_data(filePath, fileUuid, screenshotDir, htmlSaveDir) {
        const page = await this.fetch_data(filePath);
        const baseUrl = new URL(page.url()).origin;    
        let content = await page.content();
        
        const $ = cheerio.load(content);
        await this.processPageContent($, baseUrl, fileUuid); // Refactored code used here

        content = $.html();
        const title = await page.title();
        const favicon = await this.get_favicon(page, $);
        const screenshotPath = await this.take_screenshot(page, fileUuid, screenshotDir);
        const htmlPath = await this.saveHtml(content, fileUuid, htmlSaveDir);
    
        let data = [];
        const elementHandles = await page.$$('p, div, span, h1, h2, h3, h4, h5, h6, em, figcaption, strong, a, b');
    
        for (const elementHandle of elementHandles) {
            // Evaluate all child nodes and concatenate text content
            const textContent = await page.evaluate(element => {
                return Array.from(element.childNodes).reduce((acc, node) => {
                    return node.nodeType === Node.TEXT_NODE ? acc + node.textContent.trim() : acc;
                }, '');
            }, elementHandle);
    
            if (textContent) {
                const bbox = await elementHandle.boundingBox();
    
                if (bbox) {
                    const left_x = Math.round(bbox.x);
                    const bottom_y = Math.round(bbox.y + bbox.height);
                    const right_x = Math.round(bbox.x + bbox.width);
                    const top_y = Math.round(bbox.y);
    
                    const formattedBbox = {
                        left_x,
                        top_y,
                        right_x,
                        bottom_y
                    };
    
                    data.push({ text: textContent.trim(), bbox: formattedBbox });
                }
            }
        }
        
        await page.browser().close();
        return { title, data, favicon, screenshotPath, htmlPath };
    }

    async processPageContent($, baseUrl, fileUuid) {
        await this.convertRelativePathsToAbsolute($, baseUrl);
        $('script').remove();
        let imageElements = findImageElements($);
        addTagsToElements(imageElements, fileUuid);
    }

    async get_favicon(page, $) {
        let favicon = $('link[rel="shortcut icon"]').attr('href') || $('link[rel="icon"]').attr('href');
    
        if (favicon) {
            // Check if the favicon URL is relative
            if (!favicon.startsWith('http://') && !favicon.startsWith('https://')) {
                // Prepend the base URL of the page to make the URL absolute
                const baseUrl = new URL(await page.url());
                if (favicon.startsWith('/')){
                    favicon = `${baseUrl.origin}${favicon}`;
                }
                else {
                    favicon = `${baseUrl.origin}/${favicon}`;
                }                
            }
            return favicon;
        } else {
            return 'No favicon found';
        }
    }

    async take_screenshot(page, fileUuid, screenshotDir) {
        if (!fs.existsSync(screenshotDir)){
            fs.mkdirSync(screenshotDir);
        }
        
        const screenshotPath = `${screenshotDir}/${fileUuid}.png`;

        await page.screenshot({ 
            path: screenshotPath,
            fullPage: true
        });
        return screenshotPath;
    }

    async fetch_data(filePath) {
        const browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const page = await browser.newPage();
    
        // 일반적인 브라우저처럼 보이게 사용자 에이전트 설정
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36');
    
        try {
            const navigationPromise = page.waitForNavigation({ waitUntil: 'networkidle2' });
            await page.goto(filePath, { waitUntil: 'networkidle2' });
            await navigationPromise;
    
        } catch (error) {
            console.error(error);
            await browser.close();
            throw error;
        }
    
        return page;
    }

    async saveHtml(content, fileUuid, htmlSaveDir) {
        if (!fs.existsSync(htmlSaveDir)){
            fs.mkdirSync(htmlSaveDir);
        }

        // 이미지 제대로 id가 추가되었는지 확인(테스트용)
        // const style = `
        //     <style>
        //         [id^='image-']:hover {
        //             border: 4px solid red; /* 빨간색 테두리 추가 */
        //             box-sizing: border-box; /* 테두리 너비가 요소 크기에 포함되도록 설정 */
        //         }
        //     </style>
        // `;
        // content = content.replace('</head>', `${style}</head>`);

        const formattedContent = beautify_html(content, {
            indent_size: 4, // 또는 원하는 들여쓰기 크기
            extra_liners: [] // 필요에 따라 추가 옵션을 설정할 수 있습니다
        });
        
        const htmlPath = `${htmlSaveDir}/${fileUuid}.html`;
        fs.writeFileSync(htmlPath, formattedContent);
        return htmlPath;
    }

    async convertRelativePathsToAbsolute($, baseUrl) {
        // <a> 태그의 href 속성 처리
        $('a').each(function() {
            const href = $(this).attr('href');
            if (href && !href.startsWith('http://') && !href.startsWith('https://')) {
                $(this).attr('href', new URL(href, baseUrl).href);
            }
        });

        // <img> 태그의 src 속성 처리
        $('img').each(function() {
            const src = $(this).attr('src');
            if (src && !src.startsWith('http://') && !src.startsWith('https://')) {
                $(this).attr('src', new URL(src, baseUrl).href);
            }
        });

        // 스타일 속성 내의 배경 이미지 URL 처리
        $('[style]').each(function() {
            const style = $(this).attr('style');
            if (style && style.includes('url(')) {
                const newStyle = style.replace(/url\(['"]?(.*?)['"]?\)/g, (match, url) => {
                    if (!url.startsWith('http://') && !url.startsWith('https://')) {
                        return `url(${new URL(url, baseUrl).href})`;
                    }
                    return match;
                });
                $(this).attr('style', newStyle);
            }
        });
    }
}

// example usage
// node web_loader.js "https://medium.com/thirdai-blog/neuraldb-enterprise-full-stack-llm-driven-generative-search-at-scale-f4e28fecc3af" "ce0137db-48dc-4c9b-b336-d8a7f654736d" "./screenshots" "./html"
const url = process.argv[2];  // 커맨드 라인에서 URL 받기
const fileUuid = process.argv[3];
const screenshotDir = process.argv[4];  // 커맨드 라인에서 스크린샷 저장 경로 받기
const htmlSaveDir = process.argv[5];  // 커맨드 라인에서 HTML 저장 경로 받기

async function loadData() {
    const webLoader = new WebLoader();
    const data = await webLoader.get_data(url, fileUuid, screenshotDir, htmlSaveDir);
    console.log(JSON.stringify(data));  // JSON 형식으로 출력
    return data;
}

loadData();
