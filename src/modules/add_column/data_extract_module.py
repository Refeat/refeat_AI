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
from models.llm.chain import DocumentCoverageCheckerChain, ExtractIntentFromColumnOfMultiDocumentsChain, ExtractColumnValueChain, ExtractIntentFromColumnOfSingleDocumentChain, ExtractEvidenceChain

class AddColumnModule:
    def __init__(self, es, trigger_file_num=4, verbose=True):
        self.extract_intent_from_column_of_multi_documents_chain = ExtractIntentFromColumnOfMultiDocumentsChain(verbose=verbose)
        self.extract_intent_from_column_of_single_document_chain = ExtractIntentFromColumnOfSingleDocumentChain(verbose=verbose)
        self.document_coverage_checker_chain = DocumentCoverageCheckerChain(verbose=verbose)
        self.extract_column_value_chain = ExtractColumnValueChain(verbose=verbose)
        self.extract_evidence_chain = ExtractEvidenceChain(verbose=verbose)
        self.trigger_file_num = trigger_file_num
        self.db_tool = DBSearchTool(es=es)
        self.chunks_num = 3

    def get_column_value_by_project(self, column, project_id):
        # summaries = self.db_tool.get_schema_data_by_project_id(project_id, 'summary')
        # common_query = self.extract_intent_from_column_of_multi_documents_chain.run(column=column, document_summaries=summaries)
        common_query = column
        
        file_uuids = self.db_tool.get_schema_data_by_project_id(project_id, 'file_uuid')
        file_uuid_column_value_list = []
        for file_uuid in file_uuids:
            file_uuid, column_value = self.get_column_value_by_file(column, file_uuid, common_query)
            file_uuid_column_value_list.append({file_uuid : column_value})
        file_uuid_column_value_dict = self.merge_dict(file_uuid_column_value_list)
        return file_uuid_column_value_dict, common_query
    
    def merge_dict(self, file_uuid_column_value_list):
        file_uuid_column_value_dict = {}
        for file_uuid_column_value in file_uuid_column_value_list:
            file_uuid_column_value_dict.update(file_uuid_column_value)
        return file_uuid_column_value_dict
    
    def get_column_value_by_file(self, column, file_uuid, query=None, is_general_query=False):
        if query:
            pass
        else:            
            query = column
        column_value = self.get_column_value_by_file_and_query(query, file_uuid, is_general_query=is_general_query)
        return file_uuid, column_value
    
    def get_is_general_query(self, query):
        return self.document_coverage_checker_chain.run(query=query)        
            
    def get_column_value_by_file_and_query(self, query, file_uuid, is_general_query=False):
        if is_general_query:
            chunks = self.db_tool.get_schema_data_by_file_uuid(file_uuid, 'chunk_list_by_text_rank')
        else:
            document_summary = self.db_tool.get_schema_data_by_file_uuid(file_uuid, 'summary')
            query = self.extract_intent_from_column_of_single_document_chain.run(column=query, document_summary=document_summary)
            chunks = self.db_tool.run(query=query, file_uuid=[file_uuid])
            chunks = [chunk['chunk'] for chunk in chunks]
        chunks = chunks[:self.chunks_num]
        # context = self.chunks_list_to_text(evidence_list)
        
        evidence_list = self.extract_evidence(query, chunks)
        context = self.evidence_list_to_text(evidence_list)
        
        column_value = self.extract_column_value_chain.run(query=query, context=context)
        return column_value
    
    def chunks_list_to_text(self, chunks_list):
        chunks_text = ''
        for idx, chunk in enumerate(chunks_list[:self.chunks_num]):
            chunks_text += f'- Document {idx+1}: {chunk}\n'
        return chunks_text

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
        return self.extract_evidence_chain.run(query=query, context=chunk)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--column', type=str, default="키워드")
    parser.add_argument('--project_id', type=str, default="-1")
    parser.add_argument('--file_uuid', type=str, default="bfb7ca33-8ba4-4881-a32a-ac0e4adbe66c")
    args = parser.parse_args()
    
    es = CustomElasticSearch(index_name='refeat_ai', host="http://10.10.10.27:9200")
    add_column_module = AddColumnModule(es=es, verbose=True)
    
    is_general_query = add_column_module.get_is_general_query(query=args.column)
    print(is_general_query)
    
    # ------ get column by project id ------ #
    # file_uuid_column_value_dict, common_query = add_column_module.get_column_value_by_project(column=args.column, project_id=args.project_id)
    # print(file_uuid_column_value_dict)
    # print(common_query)
    
    # ------ get column by file uuid ------ #
    file_uuid_column_value = add_column_module.get_column_value_by_file(column=args.column, file_uuid=args.file_uuid, is_general_query=is_general_query)
    print(file_uuid_column_value)