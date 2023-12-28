import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import argparse

from models.loader.pdf.pdf_loader import PdfLoader
from models.loader.web.web_loader import WebLoader

class Loader:
    def __init__(self):
        self.loader = None

    def load_file(self, file_path):
        if file_path.endswith('.pdf'):
            self.loader = PdfLoader(file_path)
        elif file_path.startswith('http'):
            self.loader = WebLoader(file_path)
        return self.loader.to_dict()

    def save_data(self, output_path):
        self.loader.save_data(output_path)

    def get_save_path(self, output_dir):
        return self.loader.get_save_path(output_dir)

# example usage
# web
# python unified_loader.py --file_path https://www.naver.com --save_dir ../test_data/
# pdf
# python unified_loader.py --file_path ../test_data/pdf_loader_test.pdf --save_dir ../test_data/
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True)
    parser.add_argument('--save_dir', type=str, default='../test_data/')
    args = parser.parse_args()
    
    loader = Loader()
    data = loader.load_file(args.file_path)
    loader.save_data(args.save_dir)
    print('file saved at', loader.get_save_path(args.save_dir))