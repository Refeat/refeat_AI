import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from models.llm.base_chain import BaseChain
from models.tokenizer.utils import get_tokenizer

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class summaryChain(BaseChain):
    def __init__(self, 
                summary_template=None, 
                summary_template_path=os.path.join(current_file_folder_path, './templates/summary_chain_template.txt'), 
                model='gpt-3.5-turbo-1106', 
                verbose=False) -> None:
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