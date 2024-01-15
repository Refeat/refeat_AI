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
from models.llm.templates.extract_intent_and_query_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class ExtractIntentAndQueryChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-1106',
                temperature=0.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature)

    def run(self, query=None, context=None, chat_history=[], callbacks=None):
        return super().run(input=query, context=context, chat_history=chat_history, callbacks=callbacks)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        return result['user words'], result['query list']
    
# example usage
# python extract_intent_and_query_chain.py --query "인공지능 분야에 대해 설명해줘"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="전기차 시장 규모 측면에서 가장 크게 성장하고 있는 대륙은 어디야? 그리고 성장동력은 뭐야?")
    args = parser.parse_args()
    
    extract_intent_and_query_chain = ExtractIntentAndQueryChain(verbose=True)
    result = extract_intent_and_query_chain.run(query=args.query, chat_history=[])
    print(result)
    