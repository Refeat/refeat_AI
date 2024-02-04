import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import ast
import argparse

from models.llm.base_chain import BaseChatToolChain
from models.tokenizer.utils import get_tokenizer
from models.llm.templates.planning_chain_template import SYSTEM, USER, TOOLS

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class PlanningChain(BaseChatToolChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                tool_prompt_template:str=TOOLS,
                tools=None,
                response_format="json",
                model='gpt-3.5-turbo-0125',
                temperature=1.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, tool_prompt_template=tool_prompt_template, tools=tools, response_format=response_format, verbose=verbose, model=model, temperature=temperature)

    def run(self, query=None, database_filename='', chat_history=[]):
        return super().run(input=query, database_filename=database_filename, chat_history=chat_history)
    
    def parse_output(self, output):
        return ast.literal_eval(output)
    
# example usage
# python planning_chain.py --query "인공지능 분야에 대해 설명해줘"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="전기차 시장의 규모를 2021, 2022년을 비교해줘")
    args = parser.parse_args()
    
    from models.tools import WebSearchTool, DBSearchTool
    tools = [WebSearchTool(), DBSearchTool()]
    
    planning = PlanningChain(tools=tools, verbose=True)
    result = planning.run(query=args.query, chat_history=[])
    print(result)