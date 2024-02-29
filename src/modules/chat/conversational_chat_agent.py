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

from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor
from langchain.chat_models import ChatOpenAI

from models.llm.agent.conversational_chat_agent import ConversationalChatAgent
from models.tools import WebSearchTool, DBSearchTool
from models.llm.agent.custom_streming_callback import CustomStreamingStdOutCallbackHandler

class ChatAgentModule:
    def __init__(self, verbose=False):
        llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.7, streaming=True, seed=42)
        self.tools = []
        agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=self.tools)
        self.queue = [] # TODO: 나중에 backend에서 주면 삭제
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=verbose)
        self.streaming_callback = CustomStreamingStdOutCallbackHandler(queue=self.queue)
    
    def run(self, query, chat_history: List[List[str]]=[]):
        """
        Args:
            query (str): 사용자 입력
            chat_history (List[List[str]]): [[사용자 입력, 챗봇 출력], ...]
        """
        input_dict = self.parse_input(query, chat_history)
        result = self.agent_executor.run(input_dict, callbacks=[self.streaming_callback])
        return result

    def parse_input(self, query, chat_history):
        parsed_chat_history = []
        for human, assistant in chat_history:
            parsed_chat_history.append(HumanMessage(content=human))
            parsed_chat_history.append(AIMessage(content=assistant))
        return {"input": query, "chat_history": parsed_chat_history}

# example usage
# python chat_agent.py --query '안녕하세요'
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='S3 Standard의 가격 정책에 대해서 알려줘')
    args = parser.parse_args()
    
    chat_agent = ChatAgentModule(verbose=True)
    result = chat_agent.run(args.query)
    print(f'chat result: {result}')