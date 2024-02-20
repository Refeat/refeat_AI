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
                # model='gpt-4-0125-preview',
                model='gpt-3.5-turbo-0125',
                temperature=0.0,
                top_p=0.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p)
        self.input_keys = ['query', 'chat_history']
        self.output_keys = ['enriched user question', "search query"]

    def run(self, query=None, chat_history=[], callbacks=None):
        return super().run(input=query, chat_history=chat_history, callbacks=callbacks)
    
    def parse_output(self, output):
        print(output)
        result = ast.literal_eval(output)
        return result['enriched user question'], result['search query']
    
# example usage
# python extract_intent_and_query_chain.py --query "안녕"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="현재 시장 규모랑 앞으로 성장한 시장 규모를 비교해서  그래프로 그려줘")
    args = parser.parse_args()
    
    extract_intent_and_query_chain = ExtractIntentAndQueryChain(verbose=True)
    result = extract_intent_and_query_chain.run(query=args.query, chat_history=[['글로벌 SaaS 시장의 규모와 국내 SaaS 시장의 규모를 알려주세요', '글로벌 SaaS 시장은 2025년까지 723조8천억원으로 예상되고, 국내 SaaS 시장은 2025년에 2조5천억원으로 예상됩니다.']])
    # result = extract_intent_and_query_chain.run(query=args.query, chat_history=[])
    print(result)
    