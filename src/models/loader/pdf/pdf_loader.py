import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import uuid
import argparse
import subprocess

import fitz
from bs4 import BeautifulSoup
from models.loader.base_loader import BaseLoader

class PdfLoader(BaseLoader):
    def __init__(self, file_uuid, project_id, file_path, json_save_dir, screenshot_dir, html_save_dir, pdf_save_dir):
        super().__init__(file_uuid, project_id, file_path, json_save_dir, screenshot_dir, html_save_dir, pdf_save_dir)
        self.page_height = None

    def get_data(self, file_path, file_uuid, screenshot_dir, html_save_dir, pdf_save_dir):
        data = []
        doc = fitz.open(file_path)

        for page_num, page in enumerate(doc):
            self.page_height = page.rect.height
            for block in page.get_text("dict")["blocks"]:
                if "lines" in block:  # Check if block has text
                    single_data = self.data_from_block(block, page_num + 1)
                    data.append(single_data) if single_data else None

        doc.close()
        return data

    def data_from_block(self, block, page_num):
        text_list = []
        bbox = block["bbox"]
        for line in block["lines"]:
            for span in line["spans"]:
                if span["text"].strip() and ('cid' not in span["text"]):
                    text_list.append(span["text"].strip())

        adjusted_bbox = {
            'left_x': int(bbox[0]),
            'top_y': int(self.page_height - bbox[3]) + page_num * self.page_height,
            'right_x': int(bbox[2]),
            'bottom_y': int(self.page_height - bbox[1]) + page_num * self.page_height
        }

        data = {'text': ' '.join(text_list), 'page': page_num, 'bbox': adjusted_bbox}
        return data if data['text'] else None

    def get_title(self, file_path):
        doc = fitz.open(file_path)
        info = doc.metadata
        doc.close()
        title = info.get("title")

        if title:
            return title
        else:
            basename = os.path.basename(file_path)
            name_without_extension, _ = os.path.splitext(basename)
            return name_without_extension

    def get_screenshot(self, file_path, file_uuid, screenshot_dir):
        os.makedirs(screenshot_dir, exist_ok=True)
        output_path = os.path.join(screenshot_dir, f"{file_uuid}.png")
        
        doc = fitz.open(file_path)
        if len(doc) > 0:
            page = doc.load_page(0)  # first page
            pix = page.get_pixmap()
            pix.save(output_path)
        
        doc.close()
        return output_path if os.path.exists(output_path) else None
    
    def get_html_path(self, file_path, file_uuid, html_save_dir):
        command = ["pdf2htmlEX", "--dest-dir", html_save_dir, "--embed-javascript", "0", "--zoom", "1.3", file_path]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        html_path = self.change_html_name_to_uuid(file_path, file_uuid, html_save_dir)        
        self.postprocess_html(html_path)
        return 
    
    def get_pdf_path(self, file_path, file_uuid, pdf_save_dir):
        return self.file_path
    
    def postprocess_html(self, html_path):
        with open(html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')

        for script_tag in soup.find_all('script'):
            script_tag.decompose()

        with open(html_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))
    
    def change_html_name_to_uuid(self, file_path, file_uuid, html_save_dir):
        basename = os.path.basename(file_path)
        name_without_extension, _ = os.path.splitext(basename)
        html_path = os.path.join(html_save_dir, f'{name_without_extension}.html')
        new_html_path = os.path.join(html_save_dir, f'{file_uuid}.html')
        os.rename(html_path, new_html_path)
        return new_html_path
        
    def get_favicon(self, file_path):
        return None
    
# example usage
# python pdf_loader.py --file_path "../../test_data/pdf_loader_test.pdf" --json_save_dir "../../test_data/" 
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True)
    parser.add_argument('--json_save_dir', type=str, default='../../test_data/') 
    parser.add_argument('--screenshot_dir', type=str, default='../../test_data/screenshots/')
    parser.add_argument('--html_save_dir', type=str, default='../../test_data/html/')
    parser.add_argument('--file_uuid', type=str, default=str(uuid.uuid4()))
    parser.add_argument('--project_id', type=str, default=-1)
    args = parser.parse_args()
    pdf_loader = PdfLoader(file_path=args.file_path, file_uuid=args.file_uuid, project_id=args.project_id, json_save_dir=args.json_save_dir, screenshot_dir=args.screenshot_dir, html_save_dir=args.html_save_dir)
    save_path = pdf_loader.save_data(args.json_save_dir)
    print('file saved at', save_path)