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
    def __init__(self, max_token_num=256, overlap=16, model_name='multilingual-e5-large'):
        self.tokenizer = get_tokenizer(model_name=model_name)
        self.chunk_text_splitter = ChunkTextSplitter(self.tokenizer, max_token_num=max_token_num, overlap=overlap)

    def get_file_data(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def get_chunked_data(self, data):
        chunked_data = self.chunk_text_splitter.split_chunk_list(data['data'])
        return chunked_data
    
    def save_chunked_data(self, data, save_path):
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
    def __call__(self, file_path, save_path):
        data = self.get_file_data(file_path)
        chunked_data = self.get_chunked_data(data)
        self.save_chunked_data(chunked_data, save_path)

# example usage
# python json_chunker.py --file_path "../loader/test_data/medium.com_thirdai-blog_neuraldb-enterprise-full-stack-llm-driven-generative-search-at-scale-f4e28fecc3af_source=author_recirc-----861ffa0516e7----0---------------------3a853758_b666_41c3_8022_3fcc7269527f-------_2023-12-26 15_10_19.json" --save_path "../loader/test_data/medium.com_thirdai-blog_neuraldb-enterprise-full-stack-llm-driven-generative-search-at-scale-chunked.json" --max_token_num 256 --overlap 16 --model_name openai
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, default='../loader/test_data/Cross-lingual Language Model Pretraining_2023-12-26 12_58_48.json')
    parser.add_argument('--save_path', type=str, default='../loader/test_data/Cross-lingual Language Model Pretraining_chunked.json')
    parser.add_argument('--max_token_num', type=int, default=256)
    parser.add_argument('--overlap', type=int, default=16)
    parser.add_argument('--model_name', type=str, choices=['multilingual-e5-large', 'openai'], default='multilingual-e5-large')
    args = parser.parse_args()

    json_chunker = JsonChunker(max_token_num=args.max_token_num, overlap=args.overlap, model_name=args.model_name)
    json_chunker(args.file_path, args.save_path)