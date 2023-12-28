import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json
import argparse

from models.tokenizer.utils import get_tokenizer
from models.chunker.text_splitter import ChunkTextSplitter

class JsonChunker:
    def __init__(self, max_token_num=512, overlap=8, model_name='openai'):
        self.tokenizer = get_tokenizer(model_name=model_name)
        self.chunk_text_splitter = ChunkTextSplitter(self.tokenizer, max_token_num=max_token_num, overlap=overlap)

    def __call__(self, file_path, save_path):
        data = self.get_file_data(file_path)
        data['data'] = self.get_chunked_data(data['data'])
        self.save_chunked_data(data, save_path)

    def get_file_data(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def get_chunked_data(self, data):
        chunked_data = self.chunk_text_splitter.split_chunk_list(data)
        return chunked_data
    
    def save_chunked_data(self, data, save_path):
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

# example usage
# python json_chunker.py --file_path ../test_data/chunk_splitter_test.json --save_path ../test_data/chunk_splitter_test_chunked.json --max_token_num 256 --overlap 16 --model_name openai
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, default='../test_data/chunk_splitter_test.json')
    parser.add_argument('--save_path', type=str, default='../test_data/chunk_splitter_test_chunked.json')
    parser.add_argument('--max_token_num', type=int, default=512)
    parser.add_argument('--overlap', type=int, default=8)
    parser.add_argument('--model_name', type=str, choices=['multilingual-e5-large', 'openai'], default='openai')
    args = parser.parse_args()

    json_chunker = JsonChunker(max_token_num=args.max_token_num, overlap=args.overlap, model_name=args.model_name)
    json_chunker(args.file_path, args.save_path)