import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json
import uuid
import argparse
import cProfile
from itertools import accumulate
import time

from models.loader.unified_loader import UnifiedLoader
from models.chunker.json_chunker import JsonChunker
from models.embedder.utils import get_embedder
from models.llm.chain.summary_chain import SummaryChain
from models.text_ranker.text_ranker import TextRanker
from database.elastic_search.custom_elastic_search import CustomElasticSearch
from database.knowledge_graph.graph_construct import KnowledgeGraphDataBase

# es = CustomElasticSearch(index_name='refeat_ai', host="http://10.10.10.27:9200")
# es._create_index() # delete index and create new index
# summary_chain = SummaryChain()
# knowledge_graph_db = KnowledgeGraphDataBase()

class FileProcessor:
    def __init__(self, es: CustomElasticSearch, summary_chain, knowledge_graph_db, model_name='openai', json_save_dir='../test_data', screenshot_dir='../test_data/screenshots', html_save_dir='../test_data/html'):
        self.es = es
        self.summary_chain = summary_chain
        self.knowledge_graph_db = knowledge_graph_db
        self.chunker = JsonChunker(model_name=model_name)
        self.embedder = get_embedder(model_name)
        self.text_ranker = TextRanker()
        self.json_save_dir = json_save_dir
        self.screenshot_dir = screenshot_dir
        self.html_save_dir = html_save_dir
        os.makedirs(self.json_save_dir, exist_ok=True)

    def __call__(self, file_uuid, project_id, file_path):
        data = self.load_file(file_uuid, project_id, file_path)
        self.add_summary(data)
        self.process_data(data)
        save_path = self.get_save_path(data)
        self.save_data(data, save_path)
        self.save_to_db(save_path, project_id)

    def load_file(self, file_uuid, project_id, file_path):
        loader = UnifiedLoader()
        data = loader.load_file(file_uuid, project_id, file_path, self.json_save_dir, self.screenshot_dir, self.html_save_dir)
        return data
    
    def process_data(self, data):
        self.add_chunked_data(data)
        self.add_embedding(data)
        self.add_child_embedding(data)
        self.add_chunk_list_by_text_rank(data)

    def get_summary(self, data):
        summary = self.add_summary(data)
        return summary

    def get_title_favicon_screenshot_path(self, data):
        return data['title'], data['favicon'], data['screenshot_path']
    
    def get_save_path(self, data):
        return data['processed_path']

    def save_to_db(self, saved_json_path, project_id):
        start  = time.time()
        self.add_data_to_elastic_search(saved_json_path)
        self.add_data_to_db_kg(saved_json_path, project_id)

    def delete(self, file_uuid, project_id):
        try:
            self.delete_data_from_elastic_search(file_uuid)
        except Exception as e:
            print(e)
        try:
            self.delete_data_from_db_kg(file_uuid, project_id)
        except Exception as e:
            print(e)

    def add_chunked_data(self, data):
        category = self.get_file_category(data)
        data['data'] = self.chunker.get_chunked_data(data['data'], category)

    def get_file_category(self, data):
        file_path = data['file_path']
        if file_path.endswith('.pdf'):
            return 'pdf'
        elif file_path.startswith('http'):
            return 'web'
        else:
            raise ValueError('Invalid category while chunking. Only pdf and web are allowed.')

    def add_embedding(self, data):
        text_list = [chunk['text'] for chunk in data['data']]
        embedding_list = self.embedder.get_embedding(text_list)
        for chunk, embedding in zip(data['data'], embedding_list):
            chunk['embedding'] = embedding

    def add_child_embedding(self, data):
        child_text_list = [chunk['child_texts'] for chunk in data['data']]
        expand_child_text_list = [child_text for child_text_list in child_text_list for child_text in child_text_list]
        accumulate_index_list = [0] + list(accumulate([len(child_text_list) for child_text_list in child_text_list]))
        embedding_list = self.embedder.get_embedding(expand_child_text_list)
        for idx in range(len(accumulate_index_list)-1):
            start_idx = accumulate_index_list[idx]
            end_idx = accumulate_index_list[idx+1]
            data['data'][idx]['child_embeddings'] = embedding_list[start_idx:end_idx]

    def add_summary(self, data):
        summary = self.summary_chain.run(full_text=data['full_text'])
        data['summary'] = summary
        return summary
    
    def add_chunk_list_by_text_rank(self, data):
        ranked_chunks = self.text_ranker.get_text_rank(data['data'])
        data['chunk_list_by_text_rank'] = ranked_chunks

    def add_data_to_elastic_search(self, file_path):
        self.es.add_document_from_json(file_path)
        self.es.refresh_index()

    def save_data(self, data, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def delete_data_from_elastic_search(self, file_uuid):
        self.es.delete_document(file_uuid)

    def add_data_to_db_kg(self, file_path, project_id):
        self.knowledge_graph_db.add_document_from_json(file_path, project_id)

    def delete_data_from_db_kg(self, file_uuid, project_id):
        self.knowledge_graph_db.delete_document(file_uuid, project_id)

    def save_graph(self):
        self.knowledge_graph_db.save_graph_data()

    def visualize_graph(self, project_id):
        self.knowledge_graph_db.visualize_graph(project_id)

    def print_graph(self):
        print(self.knowledge_graph_db)

    def __str__(self):
        return f"File Processor: {self.chunker}, {self.embedder}, {self.save_dir}"

def profile_run(file_uuid, project_id, file_path, file_processor):
    """
    Function for profiling the file processor.

    Args:
        file_uuid (List[str]): file uuid list for database search
        project_id (str): project id for database search
        file_path (str): file path for database search
    """
    file_processor(file_uuid, project_id, file_path)

# example usage
# web
# python file_processor.py --file_path "https://zdnet.co.kr/view/?no=20230925133558" --test_query "2023 EV Rank"
# pdf
# python file_processor.py --file_path "../test_data/전기차 시장 규모.pdf" --test_query "전기차 시장 규모"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, default='https://automobilepedia.com/index.php/2023/10/21/2023-ev-rank/')
    parser.add_argument('--test_query', type=str, default='2023 EV Rank')
    parser.add_argument('--json_save_dir', type=str, default='../test_data')
    parser.add_argument('--screenshot_dir', type=str, default='../test_data/screenshots')
    parser.add_argument('--html_save_dir', type=str, default='../test_data/html')
    args = parser.parse_args()
    
    # es = CustomElasticSearch(index_name='refeat_ai') # default host is localhost:9200
    es = CustomElasticSearch(index_name='refeat_ai', host="http://10.10.10.27:9200")
    # es._create_index() # delete index and create new index

    summary_chain = SummaryChain()
    knowledge_graph_db = KnowledgeGraphDataBase()

    file_processor = FileProcessor(es, summary_chain, knowledge_graph_db, json_save_dir=args.json_save_dir, screenshot_dir=args.screenshot_dir, html_save_dir=args.html_save_dir)
    file_uuid = str(uuid.uuid4())
    project_id = -5
    print('file_uuid:', file_uuid)
    
    # ------ add data ------ #
    # version1: __call__로 호출하는 방식
    # try:
    #     file_processor(file_uuid, project_id, args.file_path)
    # except Exception as e:
    #     print(e)

    # version2: 각 함수를 직접 호출하는 방식
    # data = file_processor.load_file(file_uuid, project_id, args.file_path)
    # title, favicon, screenshot_path = file_processor.get_title_favicon_screenshot_path(data) # backend에서 가져가는 title, favicon, screenshot_path
    # print('title:', title)
    # print('favicon:', favicon)
    # print('screenshot_path:', screenshot_path)
    # summary = file_processor.get_summary(data) # backend에서 가져가는 summary
    # print('summary:', summary)
    # file_processor.process_data(data)
    # save_path = file_processor.get_save_path(data)
    # file_processor.save_data(data, save_path)
    # file_processor.save_to_db(save_path, project_id)

    # ------ Time profiling ------ #
    cProfile.runctx('profile_run(file_uuid, project_id, args.file_path, file_processor)', 
                    globals(), locals(), 'output1.prof')

    # ------ visualize graph ------ #
    file_processor.visualize_graph(project_id)
    # file_processor.print_graph()

    # ------ save graph ------ #
    file_processor.save_graph()

    # ------ add data test ------ #
    # 파일이 db에 저장되어 있다면 정상적으로 검색이 됨
    # print('------ add data test ------')
    # search_result = es.search(args.test_query) 
    # for i, result in enumerate(search_result):
    #     chunk_score = result['chunk_score'] if 'chunk_score' in result else None
    #     chunk_info = result['chunk_info'] if 'chunk_info' in result else None
    #     document_score = result['document_score'] if 'document_score' in result else None
    #     document_info = result['document_info'] if 'document_info' in result else None
    #     inner_contents = result['inner_contents'] if 'inner_contents' in result else None

    #     print(f"Result {i}:")
    #     if chunk_score and chunk_info:
    #         print(f"Chunk score: {chunk_score}")
    #         print(f"Chunk content: {chunk_info['content']}")
    #     print(f"Document score: {document_score}")
    #     print(f"Document file path: {document_info['file_uuid']}")
    #     if inner_contents:
    #         for inner_content in inner_contents:
    #             print(f"\tInner Content Score: {inner_content['score']}, Content: {inner_content['content']}")

    # ------ delete data ------ #
    # file_processor.delete(file_uuid, project_id)

    # ------ delete test ------ #
    # 파일이 정상적으로 삭제되었다면 검색이 되지 않음
    # print('------ delete test ------')
    # search_result = es.search(args.test_query) 
    # for i, result in enumerate(search_result):
    #     chunk_score = result['chunk_score'] if 'chunk_score' in result else None
    #     chunk_info = result['chunk_info'] if 'chunk_info' in result else None
    #     document_score = result['document_score'] if 'document_score' in result else None
    #     document_info = result['document_info'] if 'document_info' in result else None
    #     inner_contents = result['inner_contents'] if 'inner_contents' in result else None

    #     print(f"Result {i}:")
    #     if chunk_score and chunk_info:
    #         print(f"Chunk score: {chunk_score}")
    #         print(f"Chunk content: {chunk_info['content']}")
    #     print(f"Document score: {document_score}")
    #     print(f"Document file path: {document_info['file_uuid']}")
    #     if inner_contents:
    #         for inner_content in inner_contents:
    #             print(f"\tInner Content Score: {inner_content['score']}, Content: {inner_content['content']}")

    # ------ visualize graph ------ #
    # file_processor.visualize_graph(project_id)