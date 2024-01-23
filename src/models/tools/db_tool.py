import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import argparse
from typing import Optional, List, Any

from database.elastic_search.custom_elastic_search import CustomElasticSearch
from database.elastic_search.elastic_search_config import ElasticSearchConfig
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
)

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_file_folder_path, '../../database/elastic_search/search_config/similarity_chunk.json')

class DBSearchTool(BaseTool):
    name = "Database Search"
    description = """You can search the database."""
    es: Optional[Any] = None
    
    def __init__(self, es, **kwargs):
        super().__init__(**kwargs)
        self.es = es
    
    def run(
        self, query: str, file_uuid:List[str]=None, project_id=None, callbacks=None) -> str:
        """Use the tool."""
        return self._run(query, file_uuid=file_uuid, project_id=project_id)
    
    def _run(
        self, query: str, file_uuid:List[str]=None, project_id=None
    ) -> str:
        """Use the tool."""
        es_config = self.set_search_config(query, file_uuid, project_id)
        result_list = self.es.multi_search(es_config)
        result_list = self.parse_output(result_list)
        return result_list

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("Database search does not support async")
    
    def parse_output(self, result_list):
        result_list = [{'document':result['document_info']['file_uuid'], 'chunk':result['chunk_info']['content'], 'bbox':result['chunk_info']['bbox']} for result in result_list]
        return result_list
    
    def set_search_config(self, query, file_uuid, project_id):
        es_config = ElasticSearchConfig(json_path=config_path)
        es_config.set_query(query)
        es_config.set_filter(file_uuid)
        es_config.set_project_id(project_id)
        return es_config

    def get_summary_by_project_id(self, project_id):
        summarys = self.es.get_summary_by_project_id(project_id)
        summary_text = ''
        for idx, summary in enumerate(summarys):
            summary_text += f'file {idx+1}: {summary}\n'
        return summary_text
    
# example usage
# python db_tool.py --query 'Cross-lingual Language Model Pretraining bleu score'
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='document analysis 기술')
    args = parser.parse_args()


    es = CustomElasticSearch(index_name='refeat_ai') # default host is localhost:9200
    # es = CustomElasticSearch(index_name='refeat_ai', host="http://10.10.10.27:9200")
    db_search_tool = DBSearchTool(es=es)
    result = db_search_tool.run(args.query)
    print(f'{args.query} search result:\n{result}')