import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
js_path = os.path.join(current_path, 'web_loader.js')
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json
import subprocess
import argparse

from models.loader.base_loader import BaseLoader

class WebLoader(BaseLoader):
    def __init__(self, file_path=None):
        self.js_path = js_path
        super().__init__(file_path=file_path)

    def get_data(self, file_path):
        result = subprocess.run(['node', self.js_path, file_path], capture_output=True, text=True, encoding='utf-8')
        data = json.loads(result.stdout)
        return data

    def get_base_name(self, file_path):
        return file_path.split('//')[1]

# example usage
# python web_loader.py --file_path https://www.naver.com --save_dir ../test_data/
# python web_loader.py --file_path "https://medium.com/thirdai-blog/neuraldb-enterprise-full-stack-llm-driven-generative-search-at-scale-f4e28fecc3af?source=author_recirc-----861ffa0516e7----0---------------------3a853758_b666_41c3_8022_3fcc7269527f-------" --save_dir ../test_data/
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True)
    parser.add_argument('--save_dir', type=str, default='../test_data/')
    args = parser.parse_args()

    web_loader = WebLoader(file_path=args.file_path)
    web_loader.save_data(args.save_dir)
    print(web_loader)