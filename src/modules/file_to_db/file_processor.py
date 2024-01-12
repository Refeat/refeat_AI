import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json
import uuid
import argparse

from models.loader.unified_loader import UnifiedLoader
from models.chunker.json_chunker import JsonChunker
from models.embedder.utils import get_embedder
from models.llm.chain.summary_chain import SummaryChain
from database.elastic_search.custom_elastic_search import CustomElasticSearch
from database.knowledge_graph.graph_construct import KnowledgeGraphDataBase

es = CustomElasticSearch(index_name='refeat_ai')
es._create_index() # delete index and create new index
summary_chain = SummaryChain()
knowledge_graph_db = KnowledgeGraphDataBase()

class FileProcessor:
    def __init__(self, model_name='openai', save_dir='../test_data', screenshot_dir='../test_data/screenshot'):
        self.chunker = JsonChunker(model_name=model_name)
        self.embedder = get_embedder(model_name)
        self.save_dir = save_dir
        self.screenshot_dir = screenshot_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def __call__(self, file_uuid, project_id, file_path):
        data = self.load_file(file_uuid, project_id, file_path)
        self.process_data(data)
        save_path = self.get_save_path(data)
        self.save_data(data, save_path)
        self.save_to_db(save_path, project_id)

    def load_file(self, file_uuid, project_id, file_path):
        loader = UnifiedLoader()
        data = loader.load_file(file_uuid, project_id, file_path, self.save_dir, self.screenshot_dir)
        return data
    
    def process_data(self, data):
        self.add_chunked_data(data)
        self.add_embedding(data)
        self.add_summary(data)

    def get_title_favicon_screenshot_path(self, data):
        return data['title'], data['favicon'], data['screenshot_path']
    
    def get_summary(self, data):
        return data['summary']
    
    def get_save_path(self, data):
        return data['processed_path']

    def save_to_db(self, saved_json_path, project_id):
        self.add_data_to_elastic_search(saved_json_path)
        self.add_data_to_db_kg(saved_json_path, project_id)

    def delete(self, file_uuid, project_id):
        self.delete_data_from_elastic_search(file_uuid)
        self.delete_data_from_db_kg(file_uuid, project_id)

    def add_chunked_data(self, data):
        data['data'] = self.chunker.get_chunked_data(data['data'])

    def add_embedding(self, data):
        text_list = [chunk['text'] for chunk in data['data']]
        embedding_list = self.embedder.get_embedding(text_list)
        for chunk, embedding in zip(data['data'], embedding_list):
            chunk['embedding'] = embedding

    def add_summary(self, data):
        summary = summary_chain.run(full_text=data['full_text'])
        data['summary'] = summary

    def add_data_to_elastic_search(self, file_path):
        es.add_document_from_json(file_path)
        es.refresh_index()

    def save_data(self, data, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def delete_data_from_elastic_search(self, file_uuid):
        es.delete_document(file_uuid)

    def add_data_to_db_kg(self, file_path, project_id):
        knowledge_graph_db.add_document_from_json(file_path, project_id)

    def delete_data_from_db_kg(self, file_uuid, project_id):
        knowledge_graph_db.delete_document(file_uuid, project_id)

    def save_graph(self):
        knowledge_graph_db.save_graph_data()

    def visualize_graph(self, project_id):
        knowledge_graph_db.visualize_graph(project_id)

    def print_graph(self):
        print(knowledge_graph_db)

    def __str__(self):
        return f"File Processor: {self.chunker}, {self.embedder}, {self.save_dir}"

# example usage
# web
# python file_processor.py --file_path "https://www.asiae.co.kr/article/2023120117510759146" --test_query "인도 경제 성장률"
# pdf
# python file_processor.py --file_path "../test_data/pdf_test.pdf" --test_query "BLEU score on WMT’16 German-English"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, default='https://automobilepedia.com/index.php/2023/10/21/2023-ev-rank/')
    parser.add_argument('--test_query', type=str, default='인도 경제 성장률')
    parser.add_argument('--save_dir', type=str, default='../test_data')
    parser.add_argument('--screenshot_dir', type=str, default='../test_data/screenshot')
    args = parser.parse_args()

    file_processor = FileProcessor(save_dir=args.save_dir, screenshot_dir=args.screenshot_dir)
    file_uuid = str(uuid.uuid4())
    project_id = -1
    
    # ------ add data ------ #
    # version1: __call__로 호출하는 방식
    # file_processor(file_uuid, project_id, args.file_path)

    # version2: 각 함수를 직접 호출하는 방식
    data = file_processor.load_file(file_uuid, project_id, args.file_path)
    title, favicon, screenshot_path = file_processor.get_title_favicon_screenshot_path(data) # backend에서 가져가는 title, favicon, screenshot_path
    print('title:', title)
    print('favicon:', favicon)
    print('screenshot_path:', screenshot_path)
    file_processor.process_data(data)
    summary = file_processor.get_summary(data) # backend에서 가져가는 summary
    print('summary:', summary)
    save_path = file_processor.get_save_path(data)
    file_processor.save_data(data, save_path)
    file_processor.save_to_db(save_path, project_id)

    # ------ visualize graph ------ #
    file_processor.visualize_graph(project_id)
    # file_processor.print_graph()

    # ------ save graph ------ #
    file_processor.save_graph()

    # ------ add data test ------ #
    # 파일이 db에 저장되어 있다면 정상적으로 검색이 됨
    print('------ add data test ------')
    search_result = es.search(args.test_query) 
    for i, result in enumerate(search_result):
        chunk_score = result['chunk_score'] if 'chunk_score' in result else None
        chunk_info = result['chunk_info'] if 'chunk_info' in result else None
        document_score = result['document_score'] if 'document_score' in result else None
        document_info = result['document_info'] if 'document_info' in result else None
        inner_contents = result['inner_contents'] if 'inner_contents' in result else None

        print(f"Result {i}:")
        if chunk_score and chunk_info:
            print(f"Chunk score: {chunk_score}")
            print(f"Chunk content: {chunk_info['content']}")
        print(f"Document score: {document_score}")
        print(f"Document file path: {document_info['file_uuid']}")
        if inner_contents:
            for inner_content in inner_contents:
                print(f"\tInner Content Score: {inner_content['score']}, Content: {inner_content['content']}")

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