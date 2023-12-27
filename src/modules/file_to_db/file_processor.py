import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json

from models.loader.unified_loader import Loader
from models.chunker.json_chunker import JsonChunker
from models.tokenizer.utils import get_tokenizer
from models.embedder.utils import get_embedder

class FileProcessor:
    def __init__(self, model_name='openai', save_dir='../test_data'):
        self.loader = Loader()
        self.chunker = JsonChunker(model_name=model_name)
        self.tokenizer = get_tokenizer(model_name)
        self.embedder = get_embedder(model_name)
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def __call__(self, file_path):
        data = self.loader.load_file(file_path)
        self.get_chunked_data(data)
        self.get_token_num(data)
        self.get_embedding(data)
        save_path = self.loader.get_save_path(self.save_dir)
        self.save_data(data, save_path)

    def get_chunked_data(self, data):
        data['data'] = self.chunker.get_chunked_data(data['data'])

    def get_token_num(self, data):
        text_list = [chunk['text'] for chunk in data['data']]
        token_num_list = self.tokenizer.get_token_num(text_list)
        for chunk in data['data']:
            chunk['token_num'] = token_num_list.pop(0)

    def get_embedding(self, data):
        text_list = [chunk['text'] for chunk in data['data']]
        embedding_list = self.embedder.get_embedding(text_list)
        for chunk in data['data']:
            chunk['embedding'] = embedding_list.pop(0)

    def save_data(self, data, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    file_path = '../../models/loader/test_data/Cross-lingual Language Model Pretraining.pdf'
    file_processor = FileProcessor()
    file_processor(file_path)