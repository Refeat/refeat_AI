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

from models.llm.base_chain import BaseChatChain
from models.tokenizer.utils import get_tokenizer
from models.llm.templates.plan_answer_chain_template import SYSTEM, USER
from models.tools import WebSearchTool

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class PlanAnswerChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-1106',
                temperature=0.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature)

    def run(self, query=None, context=None, chat_history=[]):
        return super().run(input=query, context=context, chat_history=chat_history)
    
    def parse_output(self, output):
        print(output)
        return ast.literal_eval(output)['final answer']
    
# example usage
# python plan_answer_chain.py --query "인공지능 분야에 대해 설명해줘"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="아마존 aws s3의 가격 정책에 대해 알려줘")
    args = parser.parse_args()
    web_search_tool = WebSearchTool()
    context = web_search_tool.run(args.query)
    plan_answer_chain = PlanAnswerChain(verbose=True)
    result = plan_answer_chain.run(query=args.query, context=context, chat_history=[])
    print(result)