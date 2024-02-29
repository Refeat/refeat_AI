import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import os
import ast
import argparse

from models.llm.base_chain import BaseChatChain
from models.tokenizer.utils import get_tokenizer
from models.llm.templates.extract_column_value_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

other_openai_api_key = os.getenv('OPENAI_API_KEY_1')

class ExtractColumnValueChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                # model='gpt-4-0125-preview',
                model='gpt-3.5-turbo-0125',
                temperature=0.7,
                top_p=1.0,
                verbose=False,
                openai_api_key=None) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p, openai_api_key=openai_api_key)
        self.input_keys = ['query']
        self.output_keys = ['extracted content']

    def run(self, query=None, context=None, chat_history=[], callbacks=None):
        return super().run(input=query, context=context, chat_history=chat_history, callbacks=callbacks)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        values = result['extracted content']
        return values
    
# example usage
# python extract_column_value_chain.py --query "인공지능 분야에 대해 설명해줘" --context "인공지능 분야는 컴퓨터 공학의 한 분야로서 인간의 지능을 컴퓨터로 구현하는 것을 연구한다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="아마존 aws s3의 가격 정책에 대해 알려줘")
    parser.add_argument('--context', type=str, default="아마존 aws s3의 가격은 1GB당 0.023달러이다.")
    args = parser.parse_args()
    
    extract_column_value_chain = ExtractColumnValueChain(verbose=True)
    result = extract_column_value_chain.run(query=args.query, context=args.context, chat_history=[])
    print(result)