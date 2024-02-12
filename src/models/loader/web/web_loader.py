import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
js_path = os.path.join(current_path, 'web_loader.js')
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json
import uuid
import argparse
import subprocess

from models.loader.base_loader import BaseLoader
from models.errors.error import WebLoadException
from models.loader.web.pdf_merge import merge_pdf_pages_into_one, delete_text_from_pdf

class WebLoader(BaseLoader):
    def __init__(self, file_uuid, project_id, file_path, json_save_dir, screenshot_dir, html_save_dir, pdf_save_dir):
        self.js_path = js_path
        super().__init__(file_uuid, project_id, file_path, json_save_dir, screenshot_dir, html_save_dir, pdf_save_dir)

    def get_data(self, file_path, file_uuid, screenshot_dir, html_save_dir, pdf_save_dir):
        result = subprocess.run(['node', self.js_path, file_path, file_uuid, screenshot_dir, html_save_dir, pdf_save_dir], capture_output=True, text=True, encoding='utf-8')
        if result.stdout.startswith('Error'):
            raise WebLoadException()
        else:
            print('-'*30)
            print(result.stdout)
            print('-'*30)
            try:
                result = json.loads(result.stdout)
            except:
                raise WebLoadException()
        self.title, data, self.favicon, self.screenshot_path, self.html_path, self.pdf_path = result['title'], result['data'], result['favicon'], result['screenshotPath'], result['htmlPath'], result['pdfPath']
        self.postprocess_pdf()
        self.favicon = None if self.favicon == 'No favicon found' else self.favicon
        return data
    
    def postprocess_pdf(self):
        os.rename(self.pdf_path, self.pdf_path.replace('.pdf', 'raw.pdf'))
        merge_pdf_pages_into_one(self.pdf_path.replace('.pdf', 'raw.pdf'), self.pdf_path.replace('.pdf', 'modified.pdf'))
        delete_text_from_pdf(self.pdf_path.replace('.pdf', 'modified.pdf'), self.pdf_path)
        os.remove(self.pdf_path.replace('.pdf', 'raw.pdf'))
        os.remove(self.pdf_path.replace('.pdf', 'modified.pdf'))
    
    def get_title(self, file_path):
        if self.title:
            return self.title
        else:
            basename = os.path.basename(file_path)
            name_without_extension, _ = os.path.splitext(basename)
            return name_without_extension

    def get_screenshot(self, file_path, file_uuid, screenshot_dir):
        return self.screenshot_path

    def get_favicon(self, file_path):
        return self.favicon
    
    def get_html_path(self, file_path, file_uuid, html_save_dir):
        return self.html_path
    
    def get_pdf_path(self, file_path, file_uuid, pdf_save_dir):
        return self.pdf_path

# example usage
# python web_loader.py --file_path "https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/rethinking-knowledge-work-a-strategic-approach" --json_save_dir ../../test_data/ 
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True)
    parser.add_argument('--json_save_dir', type=str, default='../../test_data/')
    parser.add_argument('--screenshot_dir', type=str, default='../../test_data/screenshot/')
    parser.add_argument('--html_save_dir', type=str, default='../../test_data/html/')
    parser.add_argument('--file_uuid', type=str, default=str(uuid.uuid4()))
    parser.add_argument('--project_id', type=str, default=-1)

    args = parser.parse_args()

    web_loader = WebLoader(file_path=args.file_path, file_uuid=args.file_uuid, project_id=args.project_id, json_save_dir=args.json_save_dir, screenshot_dir=args.screenshot_dir, html_save_dir=args.html_save_dir)
    save_path = web_loader.save_data(args.json_save_dir)
    print('file saved at', save_path)