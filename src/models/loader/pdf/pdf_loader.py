import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import argparse

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTAnno

from models.loader.base_loader import BaseLoader

class PdfLoader(BaseLoader):
    def __init__(self, file_path=None):
        super().__init__(file_path=file_path)
        self.page_height = None

    def get_data(self, file_path):
        data = []
        for page_num, page_layout in enumerate(extract_pages(file_path)):
            self.page_height = page_layout.height
            for element in page_layout:
                single_data = self.data_from_element(element, page_num+1)
                data.append(single_data) if single_data else None
        return data
    
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
    
    def get_base_name(self, file_path):
        return os.path.basename(file_path).split('.')[0]
    
# example usage
# python pdf_loader.py --file_path ../../test_data/pdf_loader_test.pdf --save_dir ../../test_data/
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True)
    parser.add_argument('--save_dir', type=str, default='../../test_data/')
    args = parser.parse_args()
    pdf_loader = PdfLoader(file_path=args.file_path)
    save_path = pdf_loader.save_data(args.save_dir)
    print('file saved at', save_path)