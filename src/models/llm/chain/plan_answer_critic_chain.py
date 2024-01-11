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
from models.llm.templates.plan_answer_critic_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class PlanAnswerCriticChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                model='gpt-3.5-turbo-1106',
                temperature=0.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature)

    def run(self, query=None, answer=None, chat_history=[]):
        return super().run(input=query, answer=answer, chat_history=chat_history)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        return {
            'success': result.get('success', None),
            'reason': result.get('reason', None),
            'answer': result.get('answer', None),
            'feedback': result.get('feedback', None),
        }

# example usage
# python plan_answer_critic_chain.py --query "인공지능 분야에 대해 설명해줘" --answer "인공지능은 인간의 지능을 컴퓨터로 구현하는 것을 말한다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="인공지능 분야에 대해 설명해줘")
    parser.add_argument('--answer', type=str, default="인공지능은 인간의 지능을 컴퓨터로 구현하는 것을 말한다.")
    args = parser.parse_args()
    plan_answer_critic_chain = PlanAnswerCriticChain(verbose=True)
    result = plan_answer_critic_chain.run(query=args.query, answer=args.answer, chat_history=[])
    print(result)