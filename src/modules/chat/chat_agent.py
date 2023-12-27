import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

from typing import List

from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor
from langchain.chat_models import ChatOpenAI

from models.llm.agent.conversational_chat_agent import ConversationalChatAgent
from models.tools import WebSearchTool, DBSearchTool
from models.llm.agent.custom_streming_callback import CustomStreamingStdOutCallbackHandler

class ChatAgent:
    def __init__(self):
        llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0.0, streaming=True, seed=42)
        tools = [WebSearchTool(), DBSearchTool()]
        agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools)
        self.queue = [] # TODO: 나중에 backend에서 주면 삭제
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        self.streaming_callback = CustomStreamingStdOutCallbackHandler(queue=self.queue)
    
    def run(self, query, chat_history: List[List[str]]):
        input_dict = self.parse_input(query, chat_history)
        result = self.agent_executor.run(input_dict, callbacks=[self.streaming_callback])
        return result

    def parse_input(self, query, chat_history):
        parsed_chat_history = []
        for human, assistant in chat_history:
            parsed_chat_history.append(HumanMessage(content=human))
            parsed_chat_history.append(AIMessage(content=assistant))
        return {"input": query, "chat_history": parsed_chat_history}
    
if __name__ == '__main__':
    chat_agent = ChatAgent()
    chat_agent.run("데이터베이스에 저장된 Cross-lingual Language Model Pretraining bleu score", [["안녕하세요", "무엇을 도와드릴까요?"]])