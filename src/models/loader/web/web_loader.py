import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
js_path = os.path.join(current_path, 'web_loader.js')
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json
import subprocess

from models.loader.base_loader import BaseLoader

class WebLoader(BaseLoader):
    def __init__(self, file_path=None):
        self.js_path = js_path
        super().__init__(file_path=file_path)

    def get_data(self, file_path):
        result = subprocess.run(['node', self.js_path, file_path], capture_output=True, text=True, encoding='utf-8')
        print(result.stdout)
        data = json.loads(result.stdout)
        return data

    def get_base_name(self, file_path):
        return file_path.split('//')[1]

if __name__ == '__main__':
    file_path = 'https://www.naver.com/'
    web_loader = WebLoader(file_path=file_path)
    web_loader.save_data('../test_data/')
    print(web_loader)