import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import argparse
import concurrent.futures

from database.elastic_search.custom_elastic_search import CustomElasticSearch
from models.tools import DBSearchTool
from models.llm.chain import DocumentCoverageCheckerChain, ExtractIntentFromColumnOfMultiDocumentsChain, ExtractColumnValueChain, ExtractIntentFromColumnOfSingleDocumentChain, ExtractEvidenceChain, ExtractRelevanceChain

class AddColumnModule:
    def __init__(self, es, trigger_file_num=4, verbose=True):
        self.document_coverage_checker_chain = DocumentCoverageCheckerChain(verbose=verbose)
        self.extract_column_value_chain = ExtractColumnValueChain(verbose=verbose)
        self.extract_relevance_chain = ExtractRelevanceChain(verbose=verbose)
        self.extract_evidence_chain = ExtractEvidenceChain(verbose=verbose)
        self.trigger_file_num = trigger_file_num
        self.db_tool = DBSearchTool(es=es)
        self.chunks_num = 5
        self.text_length_filter = 50
        
    def merge_dict(self, file_uuid_column_value_list):
        file_uuid_column_value_dict = {}
        for file_uuid_column_value in file_uuid_column_value_list:
            file_uuid_column_value_dict.update(file_uuid_column_value)
        return file_uuid_column_value_dict
    
    def get_is_general_query(self, query):
        result = self.document_coverage_checker_chain.run(query=query)        
        if result == 'general':
            return True
        elif result == 'specific':
            return False
        else:
            raise ValueError(f"Invalid query nature: {result}. It should be either 'general' or 'specific'")
            
    def get_column_value_by_file(self, column, file_uuid, is_general_query=False):
        if is_general_query:
            chunks = self.db_tool.get_schema_data_by_file_uuid(file_uuid, 'chunk_list_by_text_rank')
            chunks = [chunk for chunk in chunks if len(chunk) > self.text_length_filter]
        else:
            chunks = self.db_tool.run(query=column, file_uuid=[file_uuid])
            chunks = [chunk['chunk'] for chunk in chunks]
            chunks = [chunk for chunk in chunks if len(chunk) > self.text_length_filter]
        chunks = chunks[:self.chunks_num]
        context = self.chunks_list_to_text(chunks)
        
        # evidence_list = self.extract_evidence(column, chunks)
        # context = self.evidence_list_to_text(evidence_list)
        
        column_value = self.extract_column_value_chain.run(query=column, context=context)
        if column_value is None or len(column_value) == 0:
            column_text = '해당 사항 없음'
        else:
            column_text = self.post_process_column_value(column_value)
        return file_uuid, column_text
    
    def chunks_list_to_text(self, chunks_list):
        chunks_text = ''
        for idx, chunk in enumerate(chunks_list[:self.chunks_num]):
            chunks_text += f'- Content {idx+1}: {chunk}\n'
        return chunks_text
    
    def post_process_column_value(self, column_value):
        column_value_text = ''
        for value in column_value:
            column_value_text += f'- {value}\n'
        return column_value_text

    def evidence_list_to_text(self, evidence_list):
        evidence_text = '\n'.join(evidence_list)
        return evidence_text
    
    def extract_evidence(self, query, chunks):
        args_list = [(query, chunk) for chunk in chunks]
        evidence_list = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks)) as executor:
            future_to_chunk = {executor.submit(self.process_chunk, args): args for args in args_list}
            for future in concurrent.futures.as_completed(future_to_chunk):
                result = future.result()
                evidence_list.extend(result)
        return evidence_list
    
    def process_chunk(self, args):
        query, chunk = args
        relevance = self.extract_relevance_chain.run(query=query, context=chunk)
        if relevance:
            return self.extract_evidence_chain.run(query=query, context=chunk)
        else:
            return []
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--column', type=str, default="도쿄에서 로맨틱한 장소")
    parser.add_argument('--project_id', type=str, default="41")
    parser.add_argument('--file_uuid', type=str, default="76750076-e703-4b70-8c12-1cb25e167cda")
    args = parser.parse_args()
    
    es = CustomElasticSearch(index_name='refeat_ai', host="http://10.10.10.27:9200")
    add_column_module = AddColumnModule(es=es, verbose=True)
    
    is_general_query = add_column_module.get_is_general_query(query=args.column)
    print(is_general_query)
    
    # ------ get column by file uuid ------ #
    file_uuid_column_value = add_column_module.get_column_value_by_file(column=args.column, file_uuid=args.file_uuid, is_general_query=is_general_query)
    print(file_uuid_column_value)