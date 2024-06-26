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
from models.llm.templates.revise_table_of_contents_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class ReviseTableofContentsChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                # model='gpt-4-0125-preview',
                model='gpt-3.5-turbo-0125',
                temperature=0.7,
                top_p=1.0,
                verbose=False) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p)
        self.input_keys = ['table_of_contents', 'context']
        self.output_keys = ['modified table of contents']

    def run(self, table_of_contents=None, context=None, chat_history=[], callbacks=None):
        return super().run(table_of_contents=table_of_contents, context=context, chat_history=chat_history, callbacks=callbacks)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        values = result['modified table of contents']
        return values