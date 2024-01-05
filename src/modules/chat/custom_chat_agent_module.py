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

from models.llm.agent.custom_chat_agent import CustomChatAgent
from models.tools import DBSearchTool
from models.llm.agent.custom_streming_callback import CustomStreamingStdOutCallbackHandler
from models.llm.chain import InstantlyAnswerableDiscriminatorChain, PlanAnswerChain, DBToolQueryGeneratorChain

class ChatAgentModule:
    def __init__(self, verbose=False):
        self.tools = [DBSearchTool()]
        self.tool_dict = self.create_tool_dict(self.tools)
        self.instantly_answerable_discriminator = InstantlyAnswerableDiscriminatorChain(verbose=verbose)
        self.db_tool_query_generator = DBToolQueryGeneratorChain(verbose=verbose)
        self.plan_answer_chain = PlanAnswerChain(verbose=verbose)
    
    def run(self, query, chat_history: List[List[str]]=[], project_id=-1):
        """
        Args:
            query (str): 사용자 입력
            chat_history (List[List[str]]): [[사용자 입력, 챗봇 출력], ...]
        """
        self.queue = [] # TODO: 나중에 backend에서 주면 삭제
        self.streaming_callback = CustomStreamingStdOutCallbackHandler(queue=self.queue)
        result = self.instantly_answerable_discriminator.run(query=query, chat_history=chat_history)
        
        print(result)
        if result['instantly answerable'] == 'yes':
            answer = result['answer']
        else:
            db_query = self.db_tool_query_generator.run(query=query, chat_history=chat_history)
            print(db_query)
            tool_result = self.execute_tool('Database Search', db_query['query'])
            answer = self.plan_answer_chain.run(query=query, context=tool_result)
        # final_answer = self.final_answer_chain.run(query=query, answer=answer, chat_history=chat_history)
    
        return answer
    
    def execute_tool(self, action, action_input):
        if action in self.tool_dict:
            tool = self.tool_dict[action]
            return tool.run(action_input)
        
    def create_tool_dict(self, tools):
        return {tool.name: tool for tool in tools}


# example usage
# python chat_agent.py --query '안녕하세요'
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='전기차 시장 규모')
    args = parser.parse_args()
    
    chat_agent = ChatAgentModule(verbose=True)
    result = chat_agent.run(args.query, chat_history=[])
    print(f'chat result: {result}')