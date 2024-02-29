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
from models.llm.templates.extract_intent_from_column_of_multi_documents_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class ExtractIntentFromColumnOfMultiDocumentsChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-0125',
                temperature=0.7,
                top_p=1.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p)

    def run(self, column, document_summaries, chat_history=[], callbacks=None):
        return super().run(column=column, document_summaries=document_summaries, chat_history=chat_history, callbacks=callbacks)
    
    def parse_input(self, column, document_summaries, chat_history=[]):
        chat_history = self.parse_chat_history(chat_history)
        documents_summary_text = self.parse_documents_summary(document_summaries)
        return {'input': column, 'document': documents_summary_text, 'chat_history': chat_history}
    
    def parse_documents_summary(self, document_summaries):
        document_summary_text = ''
        for idx, summary in enumerate(document_summaries):
            document_summary_text += f"Document Summary {idx+1}: {summary}\n"
        return document_summary_text
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        print(f'chat result: {result}')
        return result.get('Search Query', '')
    
# example usage
# python extract_intent_from_column_of_multi_documents_chain.py --column "주주의 수" --document_summaries "삼성전자 전자공시 자료" "sk 하이닉스 전자공시 자료" "삼성전자와 sk 하이닉스 매출 비교" "LG 전자의 현상황과 비전"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--column', type=str, default="인공지능 분야에 대해 설명해줘")
    parser.add_argument('--document_summaries', type=str, nargs='+')
    args = parser.parse_args()

    extract_intent_from_column_of_multi_documents_chain = ExtractIntentFromColumnOfMultiDocumentsChain(verbose=True)
    result = extract_intent_from_column_of_multi_documents_chain.run(column=args.column, document_summaries=args.document_summaries)
    print(f'chat result: {result}')