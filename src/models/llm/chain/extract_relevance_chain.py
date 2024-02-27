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
from models.llm.templates.extract_relevance_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

other_openai_api_key = os.getenv('OPENAI_API_KEY_1')

class ExtractRelevanceChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="text",
                # model='gpt-4-0125-preview',
                model='gpt-3.5-turbo-0125',
                temperature=0.0,
                verbose=False,
                top_p=0.0,
                openai_api_key=other_openai_api_key) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p, openai_api_key=openai_api_key)
        self.input_keys = ['query', 'context']
        self.output_keys = ['evidence response']
        self.max_tries = 1

    def run(self, query=None, context=None, chat_history=[], callbacks=None):
        input_dict = self.parse_input(chat_history=chat_history, query=query, context=context)
        for _ in range(self.max_tries):
            try:
                result = self.chain.run(input_dict, callbacks=callbacks)
                return self.parse_output(result, len(context))
            except Exception as e:
                print(e)
                continue
        raise Exception('Failed to run chain.')
    
    # def parse_input(self, query=None, context=None, chat_history=[]):
    #     context_text = '||'.join(context)
    #     chat_history = self.parse_chat_history(chat_history)
    #     return {'query':query, 'context': context_text, 'chat_history': chat_history}
    
    def parse_output(self, output, context_length):
        result = ast.literal_eval(output)
        # True for yes and False for no
        evidence_relevance_list = result['evidence response list']
        evidence_relevance_list = [True if relevance == 'yes' or relevance == 'Yes' else False for relevance in evidence_relevance_list]
        if len(evidence_relevance_list) < context_length:
            evidence_relevance_list.extend([True] * (context_length - len(evidence_relevance_list)))
        return evidence_relevance_list
    