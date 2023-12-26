import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

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