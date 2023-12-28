import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json

from models.tokenizer.utils import get_tokenizer

class TextSplitter:
    def __init__(self, tokenizer, max_token_num=256, overlap=16):
        """
        token수를 기준으로 전체 text를 split하는 class

        Args:
            tokenizer: tokenizer. openai 또는 multilingual-e5-large 사용
            max_token_num: text를 자르기 위한 기준 token 수.
            overlap: chunk간 겹치는 token 수
        """
        self.tokenizer = tokenizer
        self.max_token_num = max_token_num
        self.overlap = overlap

    def split_text(self, text):
        """
        text를 token화 한 후, max_token_num 기준으로 split
        """
        tokenized_text = self.tokenizer(text)
        splitted_text = self._split_tokenized_text(tokenized_text)
        return splitted_text

    def _split_tokenized_text(self, tokenized_text):
        splitted_text = []
        for i in range(0, len(tokenized_text), self.max_token_num-self.overlap):
            splitted_text.append(tokenized_text[i:i+self.max_token_num])
        splitted_text = [self.tokenizer.get_decoding(ids) for ids in splitted_text]
        return splitted_text

class ChunkTextSplitter:
    def __init__(self, tokenizer, max_token_num=512, overlap=8):
        """
        token수를 기준으로 전체 chunk list를 merge한 후 split하는 class

        Args:
            tokenizer: tokenizer. openai 또는 multilingual-e5-large 사용
            max_token_num: text를 자르기 위한 기준 token 수.
            overlap: chunk간 겹치는 token 수        
        """
        self.tokenizer = tokenizer
        self.max_token_num = max_token_num
        self.overlap = overlap

    def split_chunk_list(self, chunk_list):
        """
        chunk list를 merge한 후, max_token_num 기준으로 split
        """
        # chunk_list = self.sorted_data(chunk_list)
        self.get_token_num(chunk_list)
        chunk_list = self.split_chunk_by_token_num(chunk_list, filter_length=self.max_token_num//2, overlap=self.overlap)
        self.get_token_num(chunk_list)
        merge_chunk_list = self.merge_chunk(chunk_list)
        processed_merge_chunk_list = self.postprocess_merge_chunk(merge_chunk_list)
        self.get_token_num(processed_merge_chunk_list)
        return processed_merge_chunk_list
    
    def sorted_data(self, data):
        """
        data를 page, top_y, left_x 기준으로 정렬
        """
        data = sorted(data, key=lambda x: (x['page'], x['bbox']['top_y'], x['bbox']['left_x'] if 'page' in x else x['bbox']['top_y'], x['bbox']['left_x']))
        return data

    def get_token_num(self, chunk_list):
        """
        chunk list의 각 chunk의 token 수를 구함
        """
        text_list = [chunk['text'] for chunk in chunk_list]
        token_num_list = self.tokenizer.get_token_num(text_list)
        for chunk, token_num in zip(chunk_list, token_num_list):
            chunk['token_num'] = token_num

    def split_chunk_by_token_num(self, chunk_list, filter_length, overlap=0):
        """
        chunk list중 chunk가 max_token_num 보다 큰 경우 chunk를 split
        """
        splitted_chunk = []
        for chunk in chunk_list:
            token_num = chunk['token_num']
            if token_num <= filter_length:
                splitted_chunk.append(chunk)
            else:
                tokenized_text = self.tokenizer(chunk['text'])
                for i in range(0, token_num, filter_length-overlap):
                    splitted_chunk.append({
                        'text': self.tokenizer.get_decoding(tokenized_text[i:i+filter_length]),
                        'bbox': chunk['bbox'],
                        'page': chunk['page'] if 'page' in chunk else None
                    })
            
        return splitted_chunk

    def merge_chunk(self, chunk_list):
        """
        chunk list를 max_token_num 기준으로 merge
        """
        merge_chunk_list = []
        total_token_num = self.get_total_token_num(chunk_list)
        for i in range(0, total_token_num, self.max_token_num):
            merge_chunk = self.find_chunk_list_by_start_end_index(chunk_list, i, i+self.max_token_num)
            merge_chunk_list.append(merge_chunk)
        return merge_chunk_list
    
    def get_total_token_num(self, chunk_list):
        """
        chunk list의 총 token 수를 구함
        """
        total_token_num = 0
        for chunk in chunk_list:
            total_token_num += chunk['token_num']
        return total_token_num
    
    def find_chunk_list_by_start_end_index(self, chunk_list, start_index, end_index):
        """
        chunk list에서 token index를 기준으로 start_index와 end_index 사이에 있는 chunk list를 구함
        """
        start_chunk_idx = self.find_chunk_by_index(chunk_list, start_index)
        end_chunk_idx = self.find_chunk_by_index(chunk_list, end_index)
        return chunk_list[start_chunk_idx:end_chunk_idx] if end_chunk_idx else chunk_list[start_chunk_idx:]
    
    def find_chunk_by_index(self, chunk_list, index):
        """
        chunk list에서 token index를 기준으로 해당 index가 속한 chunk의 index를 구함
        """
        accumulated_count = 0
        for chunk_idx, chunk in enumerate(chunk_list):
            count = chunk['token_num']
            accumulated_count += count
            if accumulated_count > index:
                return chunk_idx
        return None
    
    def postprocess_merge_chunk(self, merge_chunk_list):
        """
        merge된 chunk list를 postprocess.
        1. merge된 chunk의 text를 merge
        2. merge된 chunk의 bbox를 구함
        3. merge된 chunk의 page를 구함
        """
        processed_merge_chunk_list = []
        for merge_chunk in merge_chunk_list:
            merge_text = ''.join([chunk['text'] for chunk in merge_chunk])
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
        """
        merge된 chunk의 bbox를 구함. 새로운 bbox는 chunk list를 모두 포함하는 가장 작은 bbox
        """
        merge_bbox = {
            'left_x': min(list(chunk['bbox']['left_x'] for chunk in merge_chunk)),
            'top_y': min(list(chunk['bbox']['top_y'] for chunk in merge_chunk)),
            'right_x': max(list(chunk['bbox']['right_x'] for chunk in merge_chunk)),
            'bottom_y': max(list(chunk['bbox']['bottom_y'] for chunk in merge_chunk))
        }
        return merge_bbox
    
# example usage
# python text_splitter.py
if __name__ == '__main__':
    # tokenizer = get_tokenizer(model_name='multilingual-e5-large')
    tokenizer = get_tokenizer(model_name='openai')

    # ------ text splitter test ------ #
    # text_splitter = TextSplitter(tokenizer, max_token_num=256, overlap=16)
    # with open('../test_data/text_splitter_test.txt', 'r', encoding='utf-8') as f:
    #     text = f.read()
    # splitted_text = text_splitter.split_text(text)
    # for idx, splitted in enumerate(splitted_text):
    #     print(f'chunk {idx}: {splitted}')
    #     print('----------------------------------')

    # ------ chunk list splitter test ------ #
    json_file_path = '../test_data/chunk_splitter_test.json'
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)['data']

    chunk_text_splitter = ChunkTextSplitter(tokenizer, max_token_num=512, overlap=0)
    new_data = chunk_text_splitter.split_chunk_list(data)
    for idx, chunk in enumerate(new_data):
        print(f'chunk {idx}: {chunk}')
        print('----------------------------------')