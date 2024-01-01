import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import argparse

from models.llm.base_chain import BaseChain
from models.tokenizer.utils import get_tokenizer

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class SummaryChain(BaseChain):
    def __init__(self, 
                summary_template=None, 
                summary_template_path=os.path.join(current_file_folder_path, './templates/summary_chain_template.txt'), 
                model='gpt-3.5-turbo-1106', 
                verbose=False,) -> None:
        super().__init__(prompt_template=summary_template, prompt_template_path=summary_template_path, model=model, verbose=verbose)
        self.tokenizer = get_tokenizer(model_name='openai')
        self.max_token_num = 8000

    def run(self, **kwargs):
        return super().run(**kwargs)
    
    def parse_input(self, full_text):
        encoded_text = self.tokenizer.get_encoding(full_text)
        if len(encoded_text) > self.max_token_num:
            encoded_text = encoded_text[:self.max_token_num]
            decoded_text = self.tokenizer.get_decoding(encoded_text)
            return {'context': decoded_text}
        else:
            return {'context': full_text}

# example usage
# python summary_chain.py --text_file ../test_data/summary_chain_test.txt
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', type=str, default=None)
    parser.add_argument('--text_file', type=str, default="../test_data/summary_chain_test.txt")
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