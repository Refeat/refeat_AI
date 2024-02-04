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
from models.llm.templates.summary_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class SummaryChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-0125',
                temperature=0.0,
                top_p=0.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p)
        self.tokenizer = get_tokenizer(model_name='openai')
        self.max_token_num = 6000
        self.first_token_index = 0

    def run(self, title=None, full_text=None, chat_history=[]):
        return super().run(title=title, context=full_text, chat_history=chat_history)
    
    def parse_input(self, title, context, chat_history=[]):
        chat_history = self.parse_chat_history(chat_history)
        encoded_text = self.tokenizer.get_encoding(context)
        if len(encoded_text) > self.max_token_num:
            encoded_text = encoded_text[self.first_token_index:self.first_token_index+self.max_token_num]
            decoded_text = self.tokenizer.get_decoding(encoded_text)
            return {'title':title, 'context': decoded_text, 'chat_history': chat_history}
        else:
            return {'title':title, 'context': context, 'chat_history': chat_history}
        
    def parse_output(self, output):
        print(output)
        result = ast.literal_eval(output)
        return result['summary']
    
# example usage
# python summary_chain.py --text_file ../test_data/summary_chain_test.txt
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', type=str, default=None)
    parser.add_argument('--text_file', type=str, default="../../test_data/summary_chain_test.txt")
    args = parser.parse_args()
    if args.text_file:
        with open(args.text_file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        raise ValueError('Either text or text_file should be provided')

    summary_chain = SummaryChain(verbose=True)
    result = summary_chain.run(full_text=text)
    print(f'summary: {result}')