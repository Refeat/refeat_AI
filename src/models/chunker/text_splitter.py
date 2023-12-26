import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json
import argparse

from models.tokenizer.utils import get_tokenizer

class TextSplitter:
    def __init__(self, tokenizer, max_token_num=256, overlap=16):
        self.tokenizer = tokenizer
        self.max_token_num = max_token_num
        self.overlap = overlap

    def split_text(self, text):
        tokenized_text = self.tokenizer(text)
        splitted_text = self._split_tokenized_text(tokenized_text)
        return splitted_text

    def _split_tokenized_text(self, tokenized_text):
        splitted_text = []
        for i in range(0, len(tokenized_text['input_ids']), self.max_token_num-self.overlap):
            splitted_text.append(tokenized_text['input_ids'][i:i+self.max_token_num])
        splitted_text = [self.tokenizer.decode(ids) for ids in splitted_text]
        return splitted_text
    

class TextSplitter:
    def __init__(self, tokenizer, max_token_num=256, overlap=16):
        self.tokenizer = tokenizer
        self.max_token_num = max_token_num
        self.overlap = overlap

    def split_text(self, text):
        tokenized_text = self.tokenizer(text)
        splitted_text = self._split_tokenized_text(tokenized_text)
        return splitted_text

    def _split_tokenized_text(self, tokenized_text):
        splitted_text = []
        for i in range(0, len(tokenized_text['input_ids']), self.max_token_num-self.overlap):
            splitted_text.append(tokenized_text['input_ids'][i:i+self.max_token_num])
        splitted_text = [self.tokenizer.decode(ids) for ids in splitted_text]
        return splitted_text
    

class ChunkTextSplitter:
    def __init__(self, tokenizer, max_token_num=256, overlap=8):
        self.tokenizer = tokenizer
        self.max_token_num = max_token_num
        self.overlap = overlap

    def sorted_data(self, data):
        # 왼쪽 위 좌표를 기준으로 정렬. 만약 'page' key가 있으면 page를 가장 우선순위로 정렬
        data = sorted(data, key=lambda x: (x['page'], x['bbox']['top_y'], x['bbox']['left_x'] if 'page' in x else x['bbox']['top_y'], x['bbox']['left_x']))
        return data

    def split_chunk_list(self, chunk_list):
        self.get_token_num(chunk_list)
        merge_chunk_list = self.merge_chunk(chunk_list)
        processed_merge_chunk_list = self.postprocess_merge_chunk(merge_chunk_list)
        return processed_merge_chunk_list

    def get_token_num(self, chunk_list):
        text_list = [chunk['text'] for chunk in chunk_list]
        token_num_list = self.tokenizer.get_token_num(text_list)
        for chunk, token_num in zip(chunk_list, token_num_list):
            chunk['token_num'] = token_num

    def merge_chunk(self, chunk_list):
        merge_chunk_list = []
        total_token_num = self.get_total_token_num(chunk_list)
        for i in range(0, total_token_num, self.max_token_num-self.overlap):
            merge_chunk = self.find_chunk_list_by_start_end_index(chunk_list, i, i+self.max_token_num)
            merge_chunk_list.append(merge_chunk)
        return merge_chunk_list
    
    def get_total_token_num(self, chunk_list):
        total_token_num = 0
        for chunk in chunk_list:
            total_token_num += chunk['token_num']
        return total_token_num

    def find_chunk_by_index(self, chunk_list, index):
        accumulated_count = 0

        for chunk_idx, chunk in enumerate(chunk_list):
            count = chunk['token_num']
            accumulated_count += count
            if accumulated_count > index:
                return chunk_idx

        return None
    
    def find_chunk_list_by_start_end_index(self, chunk_list, start_index, end_index):
        start_chunk_idx = self.find_chunk_by_index(chunk_list, start_index)
        end_chunk_idx = self.find_chunk_by_index(chunk_list, end_index)

        return chunk_list[start_chunk_idx:end_chunk_idx+1] if end_chunk_idx else chunk_list[start_chunk_idx:]

    def postprocess_merge_chunk(self, merge_chunk_list):
        processed_merge_chunk_list = []
        for merge_chunk in merge_chunk_list:
            merge_text = ' '.join([chunk['text'] for chunk in merge_chunk])
            merge_bbox = self.get_merge_bbox(merge_chunk)
            page = merge_chunk[0]['page'] if 'page' in merge_chunk[0] else None
            processed_merge_chunk = {
                'text': merge_text,
                'bbox': merge_bbox,
                'page': page
            }
            processed_merge_chunk_list.append(processed_merge_chunk)                
                
        return processed_merge_chunk_list
    
    def get_merge_bbox(self, merge_chunk):
        merge_bbox = {
            'left_x': min(list(chunk['bbox']['left_x'] for chunk in merge_chunk)),
            'top_y': min(list(chunk['bbox']['top_y'] for chunk in merge_chunk)),
            'right_x': max(list(chunk['bbox']['right_x'] for chunk in merge_chunk)),
            'bottom_y': max(list(chunk['bbox']['bottom_y'] for chunk in merge_chunk))
        }
        return merge_bbox
    
if __name__ == '__main__':
    json_file_path = '../loader/test_data/medium.com_thirdai-blog_neuraldb-enterprise-full-stack-llm-driven-generative-search-at-scale-f4e28fecc3af_source=author_recirc-----861ffa0516e7----0---------------------3a853758_b666_41c3_8022_3fcc7269527f-------_2023-12-26 14_40_15.json'
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)['data']
    print(data[0])

    # tokenizer = get_tokenizer(model_name='multilingual-e5-large')
    tokenizer = get_tokenizer(model_name='openai')
    text_splitter = TextSplitter(tokenizer, max_token_num=256, overlap=16)
    chunk_text_splitter = ChunkTextSplitter(tokenizer, max_token_num=256, overlap=16)
    new_data = chunk_text_splitter.split_chunk_list(data)

    print(new_data)