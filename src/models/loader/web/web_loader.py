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
    def __init__(self, file_uuid, project_id, file_path):
        self.js_path = js_path
        super().__init__(file_uuid, project_id, file_path)

    def get_data(self, file_path):
        result = subprocess.run(['node', self.js_path, file_path], capture_output=True, text=True, encoding='utf-8')
        result = json.loads(result.stdout)
        self.title, data = result['title'], result['data']
        return data
    
    def get_title(self, file_path):
        if self.title:
            return self.title
        else:
            basename = os.path.basename(file_path)
            name_without_extension, _ = os.path.splitext(basename)
            return name_without_extension

# example usage
# python web_loader.py --file_path "https://www.naver.com" --save_dir ../../test_data/
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, required=True)
    parser.add_argument('--save_dir', type=str, default='../../test_data/')
    args = parser.parse_args()

    web_loader = WebLoader(file_path=args.file_path)
    save_path = web_loader.save_data(args.save_dir)
    print('file saved at', save_path)