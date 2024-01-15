import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import argparse
from typing import Optional, List

from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from database.knowledge_graph.graph_construct import KnowledgeGraphDataBase

db = KnowledgeGraphDataBase()

class KGDBSearchTool(BaseTool):
    name = "Knowledge Graph Search"
    description = """You can search the knowledge graph"""

    def _run(
        self, query: str, project_id=None) -> str:
        """Use the tool."""
        return self.parse_output(db.search(query, project_id))

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
    
    def parse_output(self, result_list):
        return result_list
    
    def get_chunk_num(self, project_id):
        return db.get_chunk_num(project_id)
    
# example usage
# python knowledge_graph_tool.py --query "전기차 시장의 규모"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='전기차 시장의 규모')
    args = parser.parse_args()

    db_search_tool = KGDBSearchTool()
    result = db_search_tool(args.query)
    print(f'{args.query} search result:\n{result}')