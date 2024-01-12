import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import uuid
import argparse

import fitz
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
            'top_y': int(self.page_height - bbox[3]),
            'right_x': int(bbox[2]),
            'bottom_y': int(self.page_height - bbox[1])
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

    def get_screenshot(self, file_path, screenshot_dir):
        os.makedirs(screenshot_dir, exist_ok=True)
        output_path = os.path.join(screenshot_dir, f"{uuid.uuid4()}.png")
        
        doc = fitz.open(file_path)
        if len(doc) > 0:
            page = doc.load_page(0)  # first page
            pix = page.get_pixmap()
            pix.save(output_path)
        
        doc.close()
        return output_path if os.path.exists(output_path) else None

    def get_favicon(self, file_path):
        return None
    
# example usage
# python pdf_loader.py --file_path "../../test_data/pdf_loader_test.pdf" --save_dir "../../test_data/"
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True)
    parser.add_argument('--save_dir', type=str, default='../../test_data/')
    parser.add_argument('--screenshot_dir', type=str, default='../../test_data/')
    parser.add_argument('--file_uuid', type=str, default=str(uuid.uuid4()))
    parser.add_argument('--project_id', type=str, default=-1)
    args = parser.parse_args()
    pdf_loader = PdfLoader(file_path=args.file_path, file_uuid=args.file_uuid, project_id=args.project_id, save_dir=args.save_dir, screenshot_dir=args.save_dir)
    save_path = pdf_loader.save_data(args.save_dir)
    print('file saved at', save_path)