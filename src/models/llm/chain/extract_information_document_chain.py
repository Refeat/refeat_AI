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
from models.llm.templates.extract_information_document_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class ExtractInformationDocumentChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                # model='gpt-4-0125-preview',
                model='gpt-3.5-turbo-0125',
                temperature=0.0,
                top_p=1.0,
                verbose=False) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p)
        self.input_keys = ['context']
        self.output_keys = ['summary']

    def run(self, context=None, chat_history=[], callbacks=None):
        return super().run(context=context, chat_history=chat_history, callbacks=callbacks)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        values = result['summary']
        return values
    
# example usage
# python extract_information_document_chain.py --context "인공지능 분야는 컴퓨터 공학의 한 분야로서 인간의 지능을 컴퓨터로 구현하는 것을 연구한다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--context', type=str, default="")
    parser.add_argument('--context_file', type=str, default="../../test_data/test_text.txt")
    args = parser.parse_args()
    
    if args.context:
        context = args.context
    else:
        with open(args.context_file, "r") as f:
            context = f.read()
    
    extract_information_document_chain = ExtractInformationDocumentChain(verbose=True)
    result = extract_information_document_chain.run(context=context, chat_history=[])
    print(result)