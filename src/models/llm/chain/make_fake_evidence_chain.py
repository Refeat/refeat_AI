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
from models.llm.templates.make_fake_evidence_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class MakeFakeEvidenceChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-0125',
                temperature=1.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature)

    def run(self, query=None, evidence=None):
        return super().run(input=query, evidence=evidence)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        return result['evidence']
    
# example usage
# python extract_evidence_chain.py --query "오늘의 날씨와 내일의 날씨는 어때?" --evidence "오늘 날씨는 24도이고, 습도는 50%입니다. 미세먼지는 좋음입니다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="오늘의 날씨와 내일의 날씨는 어때?")
    parser.add_argument('--evidence', type=str, default="오늘 날씨는 24도이고, 습도는 50%입니다. 미세먼지는 좋음입니다.")
    args = parser.parse_args()
    
    make_fake_evidence_chain = MakeFakeEvidenceChain(verbose=True)
    result = make_fake_evidence_chain.run(query=args.query, evidence=args.evidence)
    print(result)
    