import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import uuid
import argparse

import PyPDF2
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTAnno
from pdf2image import convert_from_path

from models.loader.base_loader import BaseLoader

class PdfLoader(BaseLoader):
    def __init__(self, file_uuid, project_id, file_path, save_dir, screenshot_dir):
        super().__init__(file_uuid, project_id, file_path, save_dir, screenshot_dir)
        self.page_height = None

    def get_data(self, file_path, screenshot_dir):
        data = []
        for page_num, page_layout in enumerate(extract_pages(file_path)):
            self.page_height = page_layout.height
            for element in page_layout:
                single_data = self.data_from_element(element, page_num+1)
                data.append(single_data) if single_data else None
        return data

    def get_title(self, file_path):
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            info = pdf_reader.metadata
            title = info.title
            if title:
                return title
            else:
                basename = os.path.basename(file_path)
                name_without_extension, _ = os.path.splitext(basename)
                return name_without_extension

    def get_screenshot(self, file_path, screenshot_dir):
        os.makedirs(screenshot_dir, exist_ok=True)

        output_path = os.path.join(screenshot_dir, f"{uuid.uuid4()}.png")
        images = convert_from_path(file_path, first_page=1, last_page=1)
        if images:
            images[0].save(output_path, 'PNG')
            return output_path
        return None

    def get_favicon(self, file_path):
        return None
    
    def data_from_element(self, element, page_num):
        text_list = []
        bbox = {'left_x': float('inf'), 'top_y': float('inf'), 'right_x': float('-inf'), 'bottom_y': float('-inf')}
        if isinstance(element, LTTextContainer):
            for text_line in element:
                if isinstance(text_line, LTAnno):
                    continue
                if text_line.get_text().strip() and ('cid' not in text_line.get_text()):
                    text_list.append(text_line.get_text().strip())
                    bbox['left_x'] = int(min(bbox['left_x'], text_line.bbox[0]))
                    bbox['top_y'] = int(min(bbox['top_y'], self.page_height-text_line.bbox[3]))
                    bbox['right_x'] = int(max(bbox['right_x'], text_line.bbox[2]))
                    bbox['bottom_y'] = int(max(bbox['bottom_y'], self.page_height-text_line.bbox[1]))
        data = {'text': ' '.join(text_list), 'page': page_num, 'bbox': bbox}
        return data if data['text'] else None
    
# example usage
# python pdf_loader.py --file_path "../../test_data/pdf_loader_test.pdf" --save_dir "../../test_data/"
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True)
    parser.add_argument('--save_dir', type=str, default='../../test_data/')
    parser.add_argument('--file_uuid', type=str, default=str(uuid.uuid4()))
    parser.add_argument('--project_id', type=str, default=-1)
    args = parser.parse_args()
    pdf_loader = PdfLoader(file_path=args.file_path, file_uuid=args.file_uuid, project_id=args.project_id)
    save_path = pdf_loader.save_data(args.save_dir)
    print('file saved at', save_path)