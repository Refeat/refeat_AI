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
from models.llm.templates.new_planning_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class NewPlanningChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-0125',
                temperature=1.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature)

    def run(self, previous_command=None, feedback=None, chat_history=[]):
        return super().run(previous_command=previous_command, feedback=feedback, chat_history=chat_history)
    
    def parse_output(self, output):
        return ast.literal_eval(output)
    
# example usage
# python new_planning_chain.py --previous_command "2020-2022년 전기차 시장 규모 검색" --feedback "2022년 전기차 시장 규모가 나와있지 않습니다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--previous_command', type=str, default="2020-2022년 전기차 시장 규모 검색")
    parser.add_argument('--feedback', type=str, default="2022년 전기차 시장 규모가 나와있지 않습니다.")
    args = parser.parse_args()

    new_planning_chain = NewPlanningChain(verbose=True)
    result = new_planning_chain.run(previous_command=args.previous_command, feedback=args.feedback, chat_history=[])
    print(result)
