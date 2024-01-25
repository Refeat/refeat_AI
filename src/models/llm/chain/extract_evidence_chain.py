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
from models.llm.templates.extract_evidence_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class ExtractEvidenceChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-1106',
                temperature=0.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature)

    def run(self, query=None, context=None, document=None, bbox=None, chat_history=[]):
        input_dict = self.parse_input(input=query, context=context, chat_history=chat_history)
        for _ in range(self.max_tries):
            try:
                result = self.chain.run(input_dict)
                return self.parse_output(result, document, bbox)
            except Exception as e:
                print(e)
                continue
        print('Failed to run chain.')
        return None
    
    def parse_output(self, output, document, bbox):
        result = ast.literal_eval(output)
        if (document is not None) and (bbox is not None):
            return result['evidence'], document, bbox
        else:
            return result['evidence']
    
# example usage
# python extract_evidence_chain.py --query "인공지능 분야에 대해 설명해줘" --context "인공지능은 인간의 지능을 컴퓨터로 구현하는 것을 말한다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="인공지능 분야에 대해 설명해줘")
    parser.add_argument('--context', type=str, default="인공지능(AI)은 인간의 학습, 추론, 지각 능력을 컴퓨터 과학으로 구현하려는 분야입니다. 컴퓨터가 인간처럼 사고하고 행동하는 것을 목표로 합니다. 인공지능은 컴퓨터 공학, 데이터 분석, 통계, 신경 과학, 철학, 심리학 등 다양한 학문의 연구 결과를 바탕으로 개발되고 있습니다. 로보틱스(Robotics)는 로봇과 테크닉스(공학)의 합성어로, 로봇에 관한 과학이자 기술학입니다. 로봇공학자는 로봇을 설계, 제조하고 응용 분야를 다루는 일을 합니다. 로보틱스는 로봇의 연구개발, 설계, 작동, 제어부터 로봇을 어떻게 활용하여 어떤 문제를 해결할 수 있을지에 이르기까지 종합적으로 연구하는 학문 및 기술 분야입니다.")
    args = parser.parse_args()
    
    extract_evidence_chain = ExtractEvidenceChain(verbose=True)
    result = extract_evidence_chain.run(query=args.query, context=args.context)
    print(result)
    