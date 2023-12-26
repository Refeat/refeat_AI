import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

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
                single_data = self.data_from_element(element, page_num)
                data.append(single_data) if single_data else None
        return data
    
    def data_from_element(self, element, page_num):
        data = None
        if isinstance(element, LTTextContainer):
            for text_line in element:
                if isinstance(text_line, LTAnno):
                    continue
                bbox = text_line.bbox
                adjusted_bbox = (
                    bbox[0],  
                    self.page_height - bbox[3],  
                    bbox[2],  
                    self.page_height - bbox[1]  
                )
                data = {
                    'text': text_line.get_text(),
                    'bbox': adjusted_bbox,
                    'page': page_num + 1
                }
        return data
    
    def get_base_name(self, file_path):
        return os.path.basename(file_path).split('.')[0]
    
if __name__ == '__main__':
    file_path = '../test_data/Cross-lingual Language Model Pretraining.pdf'
    pdf_loader = PdfLoader(file_path=file_path)
    pdf_loader.save_data('../test_data/')
    print(pdf_loader)