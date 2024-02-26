// const puppeteer = require('puppeteer');
const puppeteer = require('puppeteer-extra');
const AdblockerPlugin = require('puppeteer-extra-plugin-adblocker');
const cheerio = require('cheerio');
const fs = require('fs');
const https = require('https');
const path = require('path');
const sharp = require('sharp');
const beautify_html = require('js-beautify').html;
const { PDFDocument } = require('pdf-lib');

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

async function mergePdfPages(filePath) {
    // 원본 PDF 로드
    const originalPdfBytes = fs.readFileSync(filePath);
    const originalPdfDoc = await PDFDocument.load(originalPdfBytes);
  
    // 새 PDF 문서 생성
    const newPdfDoc = await PDFDocument.create();
    
    // 원본 PDF의 모든 페이지를 하나의 페이지로 병합
    const mergedPage = await newPdfDoc.addPage();
  
    const pageCount = originalPdfDoc.getPageCount();
    for (let i = 0; i < pageCount; i++) {
      const page = await originalPdfDoc.getPage(i);
      const { width, height } = page.getSize();
      
      // 여기서는 단순화를 위해 모든 페이지를 동일한 크기로 병합합니다.
      // 실제로는 페이지 크기 조정이 필요할 수 있습니다.
      mergedPage.drawPage(page, {
        x: 0,
        y: mergedPage.getHeight() - height * (i + 1), // 페이지를 위로 쌓아 올립니다.
        width,
        height,
      });
    }
  
    // 병합된 PDF를 저장
    const mergedPdfBytes = await newPdfDoc.save();
    fs.writeFileSync('merged.pdf', mergedPdfBytes);
  
    console.log('PDF 병합 완료');
}
class WebLoader {
    constructor(filePath = null, fileUuid = null, screenshotDir = null, htmlSaveDir = null, pdfSaveDir = null) {
        this.filePath = filePath;
        this.fileUuid = fileUuid;
        this.screenshotDir = screenshotDir;
        this.htmlSaveDir = htmlSaveDir;
        this.pdfSaveDir = pdfSaveDir;
    }

    async get_data(filePath, fileUuid, screenshotDir, htmlSaveDir, pdfSaveDir, faviconDir = null) {
        const page = await this.fetch_data(filePath);
        const baseUrl = new URL(page.url()).origin;    
        let content = await page.content();
        
        const $ = cheerio.load(content);
        await this.processPageContent($, baseUrl, fileUuid); // Refactored code used here

        content = $.html();
        const title = await page.title();
        // console.log(title);
        const faviconUrl = await this.get_favicon(page, $);
        const favicon = await this.downloadFavicon(faviconUrl, fileUuid, faviconDir);
        // console.log(favicon);
        const screenshotPath = await this.take_screenshot(page, fileUuid, screenshotDir);
        // console.log(screenshotPath);
        // const htmlPath = await this.saveHtml(content, fileUuid, htmlSaveDir);
        const htmlPath = null;
        // console.log(htmlPath);
        // const pdfPath = await this.savePdf(page, fileUuid, pdfSaveDir); // Save the web page as a PDF
        const pdfPath = null;
        // console.log(pdfPath);
        
        let data = [];
        const elementHandles = await page.$$('p, div, span, h1, h2, h3, h4, h5, h6, em, figcaption, strong, a, b, td');
    
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
        return { title, data, favicon, screenshotPath, htmlPath, pdfPath };
    }

    async savePdf(page, fileUuid, pdfSaveDir) {
        if (!fs.existsSync(pdfSaveDir)) {
            fs.mkdirSync(pdfSaveDir);
        }

        const height = await page.evaluate(() => document.documentElement.scrollHeight);

        const pdfPath = `${pdfSaveDir}/${fileUuid}.pdf`;
        await page.pdf({
            path: pdfPath,
            format: 'A4',
            // width: '794px', // A4의 너비를 픽셀로 환산한 값입니다. 필요에 따라 조정할 수 있습니다.
            // height: `${height + 1}px`, // 측정된 높이를 사용하여 PDF의 높이를 설정. 1px 추가로 빈 페이지 방지
            printBackground: true, // 페이지의 배경 포함 여부
            displayHeaderFooter: false, // 헤더와 푸터 표시 여부
            scale: 0.8, // 페이지 배율
            // pageRanges: '1'
        });

        // mergePdfPages(pdfPath);
        return pdfPath;
    }

    async processPageContent($, baseUrl, fileUuid) {
        await this.convertRelativePathsToAbsolute($, baseUrl);
        // $('script').remove();
        
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

    async downloadFavicon(faviconUrl, fileUuid, faviconDir) {
        if (!fs.existsSync(faviconDir)) {
            fs.mkdirSync(faviconDir);
        }
        
        // 만약 faviconURL이 'No favicon found' 문자열이라면 에러 발생
        if (faviconUrl === 'No favicon found') {
            return "images/web_image.png" // 기본 favicon 경로 반환
        }
    
        // URL에서 파일 확장자 추출, 확장자가 명확하지 않은 경우 기본값으로 '.ico' 사용
        // const extension = faviconUrl.split('.').pop() || 'ico';
        if (faviconUrl.includes('<svg')) {
            const svgPattern = /<svg[\s\S]*<\/svg>/;
            const svgMatch = faviconUrl.match(svgPattern);
            if (svgMatch && svgMatch[0]) {
                const svgData = svgMatch[0];
                const pngFileName = path.join(faviconDir, `${fileUuid}.png`); // PNG 파일 이름
    
                try {
                    await sharp(Buffer.from(svgData)).png().toFile(pngFileName);    
                    return `${pngFileName}`;
                } catch (error) {
                    return "images/web_image.png"; // 에러 시 기본 경로 반환
                }
            } else {
                return "images/web_image.png"; // SVG 데이터가 유효하지 않은 경우
            }
        } else {        
            const fileName = `${faviconDir}/${fileUuid}.ico`; // 수정된 부분: 확장자를 URL에서 추출한 값으로 사용
            const file = fs.createWriteStream(fileName);
        
            // User-Agent 설정을 포함한 https 요청 옵션
            const options = {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                }
            };
        
            return new Promise((resolve, reject) => {
                https.get(faviconUrl, options, response => { // 수정된 부분: 요청에 options 추가
                    response.pipe(file);
                    file.on('finish', () => {
                        file.close();
                        resolve(`${fileName}`);
                    });
                }).on('error', err => {
                    resolve("images/web_image.png"); // 기본 favicon 경로 반환
                });
            });
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
        puppeteer.use(AdblockerPlugin());
        const browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certifcate-errors',
                '--ignore-certifcate-errors-spki-list',
            ]
        });
        const page = await browser.newPage();
    
        // 일반적인 브라우저처럼 보이게 사용자 에이전트 설정
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36');
        await page.setRequestInterception(true);
        page.on('request', (req) => {
            // 광고나 팝업으로 알려진 URL을 포함하는 요청 차단
            if (req.url().includes('cdn-client.medium.com')||req.url().includes('cookie')) {
              req.abort();
            } else {
              req.continue();
            }
          });
    
        try {
            filePath = filePath.replace("blog.naver", "m.blog.naver").replace("m.m.blog.naver", "m.blog.naver");
            await page.goto(filePath, { waitUntil: 'networkidle2' });

            // 현재 페이지의 보이는 높이를 가져옵니다.
            const viewportHeight = page.viewport().height;
            
            // 스크롤을 맨 아래까지 내리는 로직
            await page.evaluate(async (viewportHeight) => {
                await new Promise((resolve, reject) => {
                    var totalHeight = 0;
                    var timer = setInterval(() => {
                        window.scrollBy(0, viewportHeight);
                        totalHeight += viewportHeight;

                        if(totalHeight >= document.body.scrollHeight){
                            clearInterval(timer);
                            resolve();
                        }
                    }, 10); // 0.1초에 한 번씩 스크롤
                });
            }, viewportHeight);

            await page.evaluate(() => {
                const links = document.querySelectorAll('a');
                links.forEach(link => {
                    link.removeAttribute('href');
                    // 또는 link.href = '#';
                });
            });

            const selectorsToRemove = ['iframe', 'header', 'footer', 'script', 'nav']; // 태그와 클래스 모두 포함
            // 선택자(태그 또는 클래스)에 대해 반복 실행
            for (const selector of selectorsToRemove) {
                await page.evaluate((selector) => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(element => {
                        element.remove();
                    });
                }, selector);
            }

            await page.evaluate(() => {
                // 삭제할 요소를 결정하기 위한 키워드 목록
                // const keywords = ['right', 'head', 'hed'];
                const keywords = ['head', 'hed', 'below'];
                
                // 문서 내의 모든 요소를 반복하여 검사합니다.
                document.querySelectorAll('*').forEach((element) => {
                    // 각 요소의 클래스 리스트를 순회합니다.
                    element.classList.forEach((className) => {
                        // 클래스 이름이 위에서 정의한 키워드 중 하나를 포함하는지 여부를 검사합니다.
                        if (keywords.some(keyword => className.includes(keyword))) {
                            // 조건을 만족하는 요소를 삭제합니다.
                            element.remove();
                            // 한 요소를 삭제한 후에는 같은 요소의 다른 클래스 이름 검사를 더 이상 진행하지 않습니다.
                            return;
                        }
                    });
                });
            });
            
        } catch (error) {
            
            
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

        // <link> 태그의 href 속성 처리
        $('link').each(function() {
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
// node web_loader.js "https://openai.com/pricing" "ce0137db-48dc-4c9b-b336-d8a7f654736d" "./screenshots" "./html" "./pdf" "./favicon"
const url = process.argv[2];  // 커맨드 라인에서 URL 받기
const fileUuid = process.argv[3];
const screenshotDir = process.argv[4];  // 커맨드 라인에서 스크린샷 저장 경로 받기
const htmlSaveDir = process.argv[5];  // 커맨드 라인에서 HTML 저장 경로 받기
const pdfSaveDir = process.argv[6];
const faviconDir = process.argv[7];

async function loadData() {
    const webLoader = new WebLoader();
    const data = await webLoader.get_data(url, fileUuid, screenshotDir, htmlSaveDir, pdfSaveDir, faviconDir);
    console.log(JSON.stringify(data));  // JSON 형식으로 출력
    return data;
}

loadData();
