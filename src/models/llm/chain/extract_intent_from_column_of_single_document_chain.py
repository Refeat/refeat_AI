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
from models.llm.templates.extract_intent_from_column_of_single_document_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class ExtractIntentFromColumnOfSingleDocumentChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-0125',
                temperature=0.0,
                top_p=0.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p)

    def run(self, column, document_summary, chat_history=[], callbacks=None):
        return super().run(column=column, document_summary=document_summary, chat_history=chat_history, callbacks=callbacks)
    
    def parse_input(self, column, document_summary, chat_history=[]):
        chat_history = self.parse_chat_history(chat_history)
        return {'input': column, 'document': document_summary, 'chat_history': chat_history}
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        print(result)
        return result.get('Enriched User Query', '')
    
# example usage
# python extract_intent_from_column_of_single_document_chain.py --column "저자" --document_summary "이 논문의 내용은 인공지능 분야에 대해 설명하고 있습니다. 인공지능은 인간의 지능을 컴퓨터로 구현하는 것을 말한다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--column', type=str, default="인공지능 분야에 대해 설명해줘")
    parser.add_argument('--document_summary', type=str)
    args = parser.parse_args()

    extract_intent_from_column_of_single_document_chain = ExtractIntentFromColumnOfSingleDocumentChain(verbose=True)
    result = extract_intent_from_column_of_single_document_chain.run(column=args.column, document_summary=args.document_summary)
    print(f'chat result: {result}')