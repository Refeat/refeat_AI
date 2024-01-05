import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import argparse
from typing import List

from models.tools import DBSearchTool
from models.llm.agent.custom_streming_callback import CustomStreamingStdOutCallbackHandler
from models.llm.chain import InstantlyAnswerableDiscriminatorChain, PlanningChain

class ChatAgentModule:
    def __init__(self, verbose=False):
        self.tools = [DBSearchTool()]
        self.instantly_answerable_discriminator = InstantlyAnswerableDiscriminatorChain(verbose=verbose)
        self.planning_chain = PlanningChain(tools=self.tools, verbose=verbose)
    
    def run(self, query, chat_history: List[List[str]]=[], project_id=-1):
        """
        Args:
            query (str): 사용자 입력
            chat_history (List[List[str]]): [[사용자 입력, 챗봇 출력], ...]
        """
        self.queue = [] # TODO: 나중에 backend에서 주면 삭제
        self.streaming_callback = CustomStreamingStdOutCallbackHandler(queue=self.queue)
        result = self.instantly_answerable_discriminator.run(query=query, chat_history=chat_history)
        if result['instantly answerable'] == 'yes':
            return result['answer']
        else:
            file_name_text = self.tools[0].get_summary_by_project_id(project_id)
            result = self.planning_chain.run(query=query, database_filename=file_name_text, chat_history=chat_history, callbacks=[self.streaming_callback])
            plan_list = list(result[key] for key in result.keys() if 'plan' in key)
            return plan_list

# example usage
# python chat_agent.py --query '안녕하세요'
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='전기차 시장 규모')
    args = parser.parse_args()
    
    chat_agent = ChatAgentModule(verbose=True)
    result = chat_agent.run(args.query, chat_history=[])
    print(f'chat result: {result}')