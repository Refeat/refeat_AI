import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import argparse
from typing import Optional, List

from database.elastic_search.custom_elastic_search import CustomElasticSearch
from database.elastic_search.elastic_search_config import ElasticSearchConfig
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
)

es = CustomElasticSearch(index_name='refeat_ai')
current_file_folder_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_file_folder_path, '../../database/elastic_search/search_config/similarity_chunk.json')

class DBSearchTool(BaseTool):
    name = "Database Search"
    description = """You can search the database."""

    def _run(
        self, query: str, filter:List[str]=None, project_id=None
    ) -> str:
        """Use the tool."""
        es_config = self.set_search_config(query, filter, project_id)
        result_list = es.multi_search(es_config)
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
    
    def set_search_config(self, query, filter, project_id):
        es_config = ElasticSearchConfig(json_path=config_path)
        es_config.set_query(query)
        es_config.set_filter(filter)
        es_config.set_project_id(project_id)
        return es_config

    def get_summary_by_project_id(self, project_id):
        summarys = es.get_summary_by_project_id(project_id)
        summary_text = ''
        for idx, summary in enumerate(summarys):
            summary_text += f'file {idx+1}: {summary}\n'
        return summary_text
    
# example usage
# python db_tool.py --query 'Cross-lingual Language Model Pretraining bleu score'
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='Cross-lingual Language Model Pretraining bleu score')
    args = parser.parse_args()

    db_search_tool = DBSearchTool()
    result = db_search_tool(args.query)
    print(f'{args.query} search result:\n{result}')