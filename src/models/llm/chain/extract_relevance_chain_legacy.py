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
from models.llm.templates.extract_relevance_chain_legacy_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class ExtractRelevanceChainLegacy(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                # model='gpt-4-0125-preview',
                model='gpt-3.5-turbo-0125',
                temperature=0.7,
                verbose=False,
                top_p=1.0,
                ) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p)
        self.input_keys = ['query', 'context']
        self.output_keys = ['answer presence']

    def run(self, query=None, context=None):
        result = super().run(query=query, context=context)
        print(context)
        return result
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        print(result)
        relevance = result['answer presence']
        if relevance == 'yes' or relevance == 'Yes':
            return True
        else:
            return False
    