import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json
import argparse

from models.tokenizer.utils import get_tokenizer
from models.embedder.utils import get_embedder
from models.chunker.text_splitter import ChunkTextSplitter, SemanticChunkSplitter

class JsonChunker:
    def __init__(self, max_token_num=1024, overlap=0, model_name='openai'):
        self.tokenizer = get_tokenizer(model_name=model_name)
        self.embedder = get_embedder(model_name=model_name)
        self.text_chunk_splitter = ChunkTextSplitter(self.tokenizer, max_token_num=max_token_num, overlap=overlap)
        self.semantic_chunk_splitter = SemanticChunkSplitter(self.tokenizer, self.embedder, max_token_num)

    def __call__(self, file_path, save_path):
        data = self.get_file_data(file_path)
        category = self.get_file_category(data)
        data['data'] = self.get_chunked_data(data['data'], category)
        self.save_chunked_data(data, save_path)

    def get_file_data(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def get_chunked_data(self, data, category):
        if category == 'pdf':
            chunked_data = self.text_chunk_splitter.split_chunk_pdf(data)
        elif category == 'web':
            chunked_data = self.semantic_chunk_splitter.split_chunk_list(data)
        else:
            raise ValueError('Invalid category while chunking. Only pdf and web are allowed.')
        return chunked_data
    
    def save_chunked_data(self, data, save_path):
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_file_category(self, data):
        file_path = data['file_path']
        if file_path.endswith('.pdf'):
            return 'pdf'
        elif file_path.startswith('http'):
            return 'web'
        else:
            raise ValueError('Invalid category while chunking. Only pdf and web are allowed.')

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