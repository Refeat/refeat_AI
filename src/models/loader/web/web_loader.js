const puppeteer = require('puppeteer');
const cheerio = require('cheerio');

class WebLoader {
    constructor(file_path = null) {
        this.file_path = file_path;
    }

    async get_data(file_path) {
        const page = await this.fetch_data(file_path);
    
        let data = [];
        const elementHandles = await page.$$('p, div, span, h1, h2, h3, h4, h5, h6');
    
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
                    const leftX = bbox.x;
                    const bottomY = bbox.y + bbox.height;
                    const rightX = bbox.x + bbox.width;
                    const topY = bbox.y;
    
                    const formattedBbox = {
                        leftX,
                        topY,
                        rightX,
                        bottomY
                    };
    
                    data.push({ text: textContent, bbox: formattedBbox });
                }
            }
        }
    
        await page.browser().close();
        return data;
    }

    async fetch_data(file_path) {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        await page.goto(file_path);

        const content = await page.content();
        const $ = cheerio.load(content);
        $('script, style').remove();

        return page;
    }
}

// example usage
// node web_loader.js "https://www.naver.com/"

const url = process.argv[2];  // 커맨드 라인에서 URL 받기

async function loadData() {
    const webLoader = new WebLoader();
    const data = await webLoader.get_data(url);
    console.log(JSON.stringify(data));  // JSON 형식으로 출력
    return data;
}

loadData();
