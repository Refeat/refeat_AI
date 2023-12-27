import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from typing import Optional, List

from database.elastic_search.custom_elastic_search import CustomElasticSearch
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

es = CustomElasticSearch(index_name='refeat_ai')

class DBSearchTool(BaseTool):
    name = "Database Search"
    description = "useful for when you need to search in database. Use this tool primarily for searching."

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        result_list = es.search(query)
        result_text = self.parse_output(result_list)
        return result_text

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
    
    def parse_output(self, result_list):
        result_text = ""
        for idx, result in enumerate(result_list):
            result_text += f"result{idx+1}. {result['chunk_info']['content']}\n\n\n"
        return result_text