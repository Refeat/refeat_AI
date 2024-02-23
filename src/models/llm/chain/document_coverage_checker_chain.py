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
from models.llm.templates.document_coverage_checker_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

other_openai_api_key = os.getenv('OPENAI_API_KEY_1')

class DocumentCoverageCheckerChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-0125',
                temperature=0.0,
                top_p=0.0,
                verbose=False,
                openai_api_key=other_openai_api_key) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p, openai_api_key=openai_api_key)
        self.input_keys = ['query']
        self.output_keys = ['query nature']

    def run(self, query=None, chat_history=[]):
        """
        Returns:
            bool: True if query is searchable, False otherwise
            
        Examples:
            query = "한국 전자 기업의 주주 수"
            return True
            
            query = "한국 전자 기업의 키워드"
            return False
        """
        return super().run(input=query, chat_history=chat_history)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        return result['query nature']
    
# example usage
# python document_coverage_checker_chain.py --query "한국 전자 기업의 주주 수"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="한국 전자 기업의 키워드")
    args = parser.parse_args()
    
    document_coverage_checker_chain = DocumentCoverageCheckerChain(verbose=True)
    result = document_coverage_checker_chain.run(query=args.query, chat_history=[])
    print(result)