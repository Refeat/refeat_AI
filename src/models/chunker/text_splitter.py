import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import copy
import json
import heapq
import threading

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from models.tokenizer.utils import get_tokenizer
from models.embedder.utils import get_embedder

class TextSplitter:
    def __init__(self, tokenizer, max_token_num=512, overlap=0):
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
    
    def split_text(self, text, max_length, last_split_length=50):
        tokens = self.tokenizer(text)
        split_texts = []

        for i in range(0, len(tokens), max_length):
            if len(tokens) - i - max_length < last_split_length:
                split_text = self.tokenizer.get_decoding(tokens[i:])
                split_texts.append(split_text)
                break
            else:
                split_text = self.tokenizer.get_decoding(tokens[i:i+max_length])
                split_texts.append(split_text)
        return split_texts
    
    def postprocess_merge_chunk(self, merge_chunk_list, child_text_length=256):
        """
        merge된 chunk list를 postprocess.
        1. merge된 chunk의 text를 merge
        2. merge된 chunk의 bbox를 구함
        3. merge된 chunk의 page를 구함
        """
        processed_merge_chunk_list = []
        for merge_chunk in merge_chunk_list:
            merge_text = ' '.join([chunk['text'] for chunk in merge_chunk])
            merge_bbox = self.get_merge_bbox(merge_chunk)
            page = merge_chunk[0]['page'] if 'page' in merge_chunk[0] else None
            child_texts = self.split_text(merge_text, child_text_length)
            processed_merge_chunk = {
                'text': merge_text,
                'child_texts': child_texts,
                'bbox': merge_bbox,
                'page': page
            }
            processed_merge_chunk_list.append(processed_merge_chunk)                
                
        return processed_merge_chunk_list
    
    def get_merge_bbox(self, merge_chunk):
        """
        merge된 chunk의 bbox를 구함. 새로운 bbox는 chunk list를 모두 포함하는 가장 작은 bbox
        """
        if 'page' not in merge_chunk[0]:
            merge_bbox = {
                'left_x': min(list(chunk['bbox']['left_x'] for chunk in merge_chunk)),
                'top_y': min(list(chunk['bbox']['top_y'] for chunk in merge_chunk)),
                'right_x': max(list(chunk['bbox']['right_x'] for chunk in merge_chunk)),
                'bottom_y': max(list(chunk['bbox']['bottom_y'] for chunk in merge_chunk))
            }
        else:
            min_page = min(list(chunk['page'] for chunk in merge_chunk))
            merge_bbox = {
                'left_x': min(list(chunk['bbox']['left_x'] for chunk in merge_chunk if chunk['page'] == min_page)),
                'top_y': min(list(chunk['bbox']['top_y'] for chunk in merge_chunk if chunk['page'] == min_page)),
                'right_x': max(list(chunk['bbox']['right_x'] for chunk in merge_chunk if chunk['page'] == min_page)),
                'bottom_y': max(list(chunk['bbox']['bottom_y'] for chunk in merge_chunk if chunk['page'] == min_page))
            }
        return merge_bbox
    
class SemanticChunkSplitter:
    def __init__(self, tokenizer, embedder, max_token_num=1000):
        self.tokenizer = tokenizer
        self.embedder = embedder
        self.max_token_num = max_token_num
        self.idx = 0

    def split_chunk_list(self, chunk_list):
        self.get_token_num(chunk_list)
        self.split_by_length(chunk_list)
        init_merge_chunk_list = self.get_split_chunk_list(chunk_list)
        merge_chunk_result_list = []
        self.recursive_split_chunk_list(init_merge_chunk_list, merge_chunk_result_list)
        processed_merge_chunk_list = self.postprocess_merge_chunk(merge_chunk_result_list)
        self.get_token_num(processed_merge_chunk_list)
        return processed_merge_chunk_list
    
    def split_by_length(self, chunk_list, max_length=500, split_length=400):
        i = 0
        while i < len(chunk_list):
            chunk = chunk_list[i]
            if chunk['token_num'] >= max_length:
                split_texts = self.split_text(chunk['text'], split_length)

                new_chunks = []
                for text in split_texts:
                    new_chunk = copy.deepcopy(chunk)  # Copy the original chunk's properties
                    new_chunk['text'] = text
                    new_chunk['token_num'] = len(self.tokenizer(text))  # Recalculate token number
                    new_chunks.append(new_chunk)
                chunk_list[i:i+1] = new_chunks  # Replace the original chunk with new chunks
                i += len(split_texts)  # Move the index past the newly inserted chunks
            else:
                i += 1  # Move to the next chunk

    def split_text(self, text, max_length, last_split_length=50):
        tokens = self.tokenizer(text)
        split_texts = []

        for i in range(0, len(tokens), max_length):
            if len(tokens) - i - max_length < last_split_length:
                split_text = self.tokenizer.get_decoding(tokens[i:])
                split_texts.append(split_text)
                break
            else:
                split_text = self.tokenizer.get_decoding(tokens[i:i+max_length])
                split_texts.append(split_text)
        return split_texts

    def recursive_split_chunk_list(self, chunk_list_list, result_list):
        for chunk_list in chunk_list_list:
            total_token_num = self.get_total_token_num(chunk_list)
            if total_token_num >= self.max_token_num:
                merge_chunk_list = self.get_split_chunk_list(chunk_list, average_window_token_num=20, average_merge_token_num=500)
                self.recursive_split_chunk_list(merge_chunk_list, result_list)
            else:
                result_list.append(chunk_list)

    def get_split_chunk_list(self, chunk_list, average_window_token_num=20, average_merge_token_num=800, window_chunk_list=None, embedding_list=None):
        chunk_num = len(chunk_list)
        average_token_num = self.get_average_token_num(chunk_list)
        median_token_num = self.get_median_token_num(chunk_list)
        window_size = self.calculate_window_size(median_token_num, average_window_token_num)
        average_merge_chunk_num = self.calculate_average_merge_chunk_num(average_token_num, average_merge_token_num)
        split_num = (chunk_num // average_merge_chunk_num)
        window_chunk_list = self.make_window_chunk_list(chunk_list, window_size)
        embedding_list = self.get_embedding(window_chunk_list)
        similarity_list = self.calculate_similarity_window_chunk_list(embedding_list)
        split_index_list = self.get_split_index(chunk_num, similarity_list, split_num, window_size)
        merge_chunk_list = self.get_merge_chunk_list(chunk_list, split_index_list)
        return merge_chunk_list
    
    def calculate_window_size(self, average_token_num, average_window_token_num):
        return average_window_token_num // average_token_num + 1
    
    def calculate_average_merge_chunk_num(self, average_token_num, average_merge_token_num):
        return average_merge_token_num // average_token_num + 1

    def get_merge_chunk_list(self, chunk_list, split_index_list):
        merge_chunk_list = []
        for idx in range(len(split_index_list)-1):
            merge_chunk = chunk_list[split_index_list[idx]:split_index_list[idx+1]]
            if merge_chunk:
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
    
    def get_average_token_num(self, chunk_list):
        token_num_list = list(chunk['token_num'] for chunk in chunk_list)
        return sum(token_num_list) // len(token_num_list)
    
    def get_median_token_num(self, chunk_list):
        token_num_list = [chunk['token_num'] for chunk in chunk_list]
        token_num_list.sort()

        n = len(token_num_list)
        mid = n // 2

        return int(token_num_list[mid])

    def get_split_index(self, chunk_num, similarity_list, split_num, window_size):
        min_k_similarity_index = self.get_min_k_similarity_index(similarity_list, split_num)
        split_index_list = list(idx+window_size-(window_size//2) for idx in min_k_similarity_index)
        split_index_list.insert(0, 0)
        split_index_list.append(chunk_num)
        split_index_list.sort()
        return split_index_list
        
    def get_min_k_similarity_index(self, similarity_list, split_num):
        weighted_averages = [1.1*similarity_list[i] + 1.0*similarity_list[i+1]
                         for i in range(len(similarity_list)-1)]

        return heapq.nsmallest(split_num, range(len(weighted_averages)), key=weighted_averages.__getitem__)

    def calculate_similarity(self, embedding1, embedding2):
        embedding1 = np.array(embedding1).reshape(1, -1)
        embedding2 = np.array(embedding2).reshape(1, -1)
        similarity = cosine_similarity(embedding1, embedding2)[0]
        return similarity

    def calculate_similarity_window_chunk_list(self, embedding_list):
        similarity_list = []
        for idx in range(len(embedding_list)-1):
            similarity = self.calculate_similarity(embedding_list[idx], embedding_list[idx+1])
            similarity_list.append(similarity)
        return similarity_list

    def make_window_chunk_list(self, chunk_list, window_size):
        window_chunk_list = []
        for i in range(len(chunk_list) - window_size + 1):
            window_chunk = chunk_list[i:i + window_size]
            window_chunk_text = ' '.join([chunk['text'] for chunk in window_chunk])
            window_chunk_list.append(window_chunk_text)
        return window_chunk_list
    
    def get_embedding(self, window_chunk_list):
        result, threads = {}, []

        # window_chunk_list를 20개씩 끊어서 각 청크에 대해 스레드 생성
        for i in range(0, len(window_chunk_list), 20):
            chunk = window_chunk_list[i:i + 20]
            thread = threading.Thread(target=self._get_embedding_chunk, args=(chunk, result, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        embedding_list = []
        for i in sorted(result.keys()):
            embedding_list.extend(result[i])

        return embedding_list

    def _get_embedding_chunk(self, chunk, result, index):
        """각 스레드가 수행할 작업을 정의합니다."""
        embedding = self.embedder.get_embedding(chunk)
        result[index] = embedding
    
    def get_token_num(self, chunk_list):
        """
        chunk list의 각 chunk의 token 수를 구함
        """
        text_list = [chunk['text'] for chunk in chunk_list]
        token_num_list = self.tokenizer.get_token_num(text_list)
        for chunk, token_num in zip(chunk_list, token_num_list):
            chunk['token_num'] = token_num

    def postprocess_merge_chunk(self, merge_chunk_list, child_text_length=256):
        """
        merge된 chunk list를 postprocess.
        1. merge된 chunk의 text를 merge
        2. merge된 chunk의 bbox를 구함
        3. merge된 chunk의 page를 구함
        """
        processed_merge_chunk_list = []
        for merge_chunk in merge_chunk_list:
            merge_text = ' '.join([chunk['text'] for chunk in merge_chunk])
            merge_bbox = self.get_merge_bbox(merge_chunk)
            page = merge_chunk[0]['page'] if 'page' in merge_chunk[0] else None
            child_texts = self.split_text(merge_text, child_text_length)
            processed_merge_chunk = {
                'text': merge_text,
                'child_texts': child_texts,
                'bbox': merge_bbox,
                'page': page
            }
            processed_merge_chunk_list.append(processed_merge_chunk)                
                
        return processed_merge_chunk_list
    
    def get_merge_bbox(self, merge_chunk):
        """
        merge된 chunk의 bbox를 구함. 새로운 bbox는 chunk list를 모두 포함하는 가장 작은 bbox
        """
        if 'page' not in merge_chunk[0]:
            merge_bbox = {
                'left_x': min(list(chunk['bbox']['left_x'] for chunk in merge_chunk)),
                'top_y': min(list(chunk['bbox']['top_y'] for chunk in merge_chunk)),
                'right_x': max(list(chunk['bbox']['right_x'] for chunk in merge_chunk)),
                'bottom_y': max(list(chunk['bbox']['bottom_y'] for chunk in merge_chunk))
            }
        else:
            min_page = min(list(chunk['page'] for chunk in merge_chunk))
            merge_bbox = {
                'left_x': min(list(chunk['bbox']['left_x'] for chunk in merge_chunk if chunk['page'] == min_page)),
                'top_y': min(list(chunk['bbox']['top_y'] for chunk in merge_chunk if chunk['page'] == min_page)),
                'right_x': max(list(chunk['bbox']['right_x'] for chunk in merge_chunk if chunk['page'] == min_page)),
                'bottom_y': max(list(chunk['bbox']['bottom_y'] for chunk in merge_chunk if chunk['page'] == min_page))
            }
        return merge_bbox

# example usage
# python text_splitter.py
if __name__ == '__main__':
    # tokenizer = get_tokenizer(model_name='multilingual-e5-large')
    tokenizer = get_tokenizer(model_name='openai')
    embedder = get_embedder(model_name='openai')

    # ------ text splitter test ------ #
    # text_splitter = TextSplitter(tokenizer, max_token_num=256, overlap=16)
    # with open('../test_data/text_splitter_test.txt', 'r', encoding='utf-8') as f:
    #     text = f.read()
    # splitted_text = text_splitter.split_text(text)
    # for idx, splitted in enumerate(splitted_text):
    #     print(f'chunk {idx}: {splitted}')
    #     print('----------------------------------')

    # ------ chunk list splitter test ------ #
    # json_file_path = '../test_data/chunk_splitter_test4.json'
    # with open(json_file_path, 'r', encoding='utf-8') as f:
    #     data = json.load(f)['data']

    # chunk_text_splitter = ChunkTextSplitter(tokenizer, max_token_num=512, overlap=0)
    # new_data = chunk_text_splitter.split_chunk_list(data)
    # for idx, chunk in enumerate(new_data):
    #     print(f'chunk {idx}: {chunk}')
    #     print('----------------------------------')

    # ------ semantic chunk list splitter test ------ #
    json_file_path = '../test_data/chunk_splitter_test2.json'
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)['data']
    
    chunk_text_splitter = SemanticChunkSplitter(tokenizer, embedder)
    new_data = chunk_text_splitter.split_chunk_list(data)
    for idx, chunk in enumerate(new_data):
        print(f'chunk {idx}: {chunk}')
        print('----------------------------------')