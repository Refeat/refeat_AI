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

from models.llm.base_chain import BaseChatChain, BaseChain
from models.tokenizer.utils import get_tokenizer
from models.llm.templates.common_chat_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class CommonChatChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-0125',
                temperature=0.0,
                verbose=False,
                top_p=0.0,
                streaming=False) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p, streaming=streaming)
        self.input_keys = ['query', 'chat_history']
        self.output_keys = ['answer']

    def run(self, query=None, chat_history=[], callbacks=None):
        return super().run(input=query, chat_history=chat_history, callbacks=callbacks)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        return result.get('answer', '')
    
# example usage
# python instantly_answerable_discriminator_chain.py --query "안녕하세요"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="인공지능 분야에 대해 설명해줘")
    args = parser.parse_args()

    common_chat = CommonChatChain(verbose=True)
    result = common_chat.run(query=args.query, chat_history=[["diffusion model이 뭐야?", "확산 모델은 시간과 공간에 따른 물질의 이동을 설명하는 모델입니다. 이 모델은 다양한 분야에서 사용되며, 화학, 물리학, 생물학 등에서 화학 물질, 열, 미생물, 정보 등의 이동을 연구하는 데 활용됩니다."]])
    print(f'chat result: {result}')