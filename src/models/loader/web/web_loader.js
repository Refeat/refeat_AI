const puppeteer = require('puppeteer');
const cheerio = require('cheerio');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid'); 

class WebLoader {
    constructor(file_path = null, screenshotDir = null) {
        this.file_path = file_path;
        this.screenshotDir = screenshotDir;
    }

    async get_data(file_path, screenshotDir) {
        const page = await this.fetch_data(file_path);        
        const content = await page.content();
        const $ = cheerio.load(content);
        const title = await page.title();
        const favicon = await this.get_favicon(page, $);
        const screenshotPath = await this.take_screenshot(page, screenshotDir);
    
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
        return { title, data, favicon, screenshotPath };
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

    async take_screenshot(page, screenshotDir) {
        const uuid = uuidv4(); // Generate a UUID
        const screenshotPath = `${screenshotDir}/${uuid}.png`;

        if (!fs.existsSync(screenshotDir)){
            fs.mkdirSync(screenshotDir);
        }

        await page.screenshot({ 
            path: screenshotPath,
            fullPage: true
        });
        return screenshotPath;
    }

    async fetch_data(file_path) {
        const browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const page = await browser.newPage();
    
        // 일반적인 브라우저처럼 보이게 사용자 에이전트 설정
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36');
    
        try {
            const navigationPromise = page.waitForNavigation({ waitUntil: 'networkidle2' });
            await page.goto(file_path, { waitUntil: 'networkidle2' });
            await navigationPromise;
    
        } catch (error) {
            console.error(error);
            await browser.close();
            throw error;
        }
    
        return page;
    }
}

// example usage
// node web_loader.js "https://www.naver.com/" "./screenshots/"

const url = process.argv[2];  // 커맨드 라인에서 URL 받기
const screenshotDir = process.argv[3];  // 커맨드 라인에서 스크린샷 저장 경로 받기

async function loadData() {
    const webLoader = new WebLoader();
    const data = await webLoader.get_data(url, screenshotDir);
    console.log(JSON.stringify(data));  // JSON 형식으로 출력
    return data;
}

loadData();
