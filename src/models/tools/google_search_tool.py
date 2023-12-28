
import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import argparse
from typing import Optional

from langchain.utilities import GoogleSerperAPIWrapper
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

search = GoogleSerperAPIWrapper(gl='kr', hl='ko')

class WebSearchTool(BaseTool):
    name = "Current Search"
    description = "useful for when you need to ask with search"

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return search.run(query)

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
    
# example usage
# python google_search_tool.py --query '2023년 롤드컵 우승팀은?'
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='2023년 롤드컵 우승팀은?')
    args = parser.parse_args()

    web_search_tool = WebSearchTool()
    result = web_search_tool(args.query)
    print(f'"{args.query}" search result:\n{result}')