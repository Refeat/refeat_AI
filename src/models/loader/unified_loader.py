import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import uuid
import argparse

from models.loader.pdf.pdf_loader import PdfLoader
from models.loader.web.web_loader import WebLoader

class UnifiedLoader:
    def __init__(self):
        self.loader = None

    def load_file(self, file_uuid, project_id, file_path, json_save_dir, screenshot_dir, html_save_dir, pdf_save_dir, favicon_save_dir=None):
        if file_path.endswith('.pdf'):
            self.loader = PdfLoader(file_uuid, project_id, file_path, json_save_dir, screenshot_dir, html_save_dir, pdf_save_dir, favicon_save_dir)
        elif file_path.startswith('http'):
            self.loader = WebLoader(file_uuid, project_id, file_path, json_save_dir, screenshot_dir, html_save_dir, pdf_save_dir, favicon_save_dir)
        return self.loader.to_dict()

    def save_data(self, output_path):
        self.loader.save_data(output_path)

    def get_save_path(self, output_dir):
        return self.loader.get_save_path(output_dir)

# example usage
# web
# python unified_loader.py --file_path "https://automobilepedia.com/index.php/2023/10/21/2023-ev-rank/" --save_dir ../test_data/
# pdf
# python unified_loader.py --file_path "../test_data/전기차 시장 규모.pdf" --save_dir ../test_data/
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True)
    parser.add_argument('--project_id', type=int, default=-1)
    parser.add_argument('--file_uuid', type=str, default=str(uuid.uuid4()))
    parser.add_argument('--save_dir', type=str, default='../test_data/')
    parser.add_argument('--screenshot_dir', type=str, default='../test_data/')
    args = parser.parse_args()
    
    loader = UnifiedLoader()
    data = loader.load_file(args.file_uuid, args.project_id, args.file_path, args.save_dir, args.screenshot_dir)
    loader.save_data(args.save_dir)
    print('file saved at', loader.get_save_path(args.save_dir))