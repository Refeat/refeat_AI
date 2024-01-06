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
from models.llm.chain import InstantlyAnswerableDiscriminatorChain, PlanAnswerChain, DBToolQueryGeneratorChain, ExtractEvidenceChain, ExtractIntentChain

class ChatAgentModule:
    def __init__(self, verbose=False):
        self.tools = [DBSearchTool()]
        self.tool_dict = self.create_tool_dict(self.tools)
        self.instantly_answerable_discriminator = InstantlyAnswerableDiscriminatorChain(verbose=verbose)
        self.extract_intent_chain = ExtractIntentChain(verbose=verbose)
        self.db_tool_query_generator = DBToolQueryGeneratorChain(verbose=verbose)
        self.extract_evidence_chain = ExtractEvidenceChain(verbose=verbose)
        self.plan_answer_chain = PlanAnswerChain(verbose=verbose)
    
    def run(self, query, chat_history: List[List[str]]=[], project_id=-1):
        """
        Args:
            query (str): 사용자 입력
            chat_history (List[List[str]]): [[사용자 입력, 챗봇 출력], ...]
        """
        self.queue = [] # TODO: 나중에 backend에서 주면 삭제
        self.streaming_callback = CustomStreamingStdOutCallbackHandler(queue=self.queue)
        enrich_query = self.extract_intent_chain.run(query=query, chat_history=chat_history)
        result = self.instantly_answerable_discriminator.run(query=enrich_query, chat_history=chat_history)
        
        print(result)
        if result['instantly answerable'] == 'yes':
            answer = result['answer']
        else:
            db_query_list = self.db_tool_query_generator.run(query=enrich_query)
            tool_result = []
            k = 12 // len(db_query_list)
            for db_query in db_query_list:
                print(db_query)
                tool_result.extend(self.execute_tool('Database Search', db_query)[:k])
            evidence_list = []
            for result_chunk in tool_result:
                evidence_list.extend(self.extract_evidence_chain.run(query=enrich_query, context=result_chunk))
            evidence_text = self.evidence_list_to_text(evidence_list)
            answer = self.plan_answer_chain.run(query=enrich_query, context=evidence_text)
    
        return answer
    
    def execute_tool(self, action, action_input):
        if action in self.tool_dict:
            tool = self.tool_dict[action]
            return tool.run(action_input)
        
    def create_tool_dict(self, tools):
        return {tool.name: tool for tool in tools}
    
    def evidence_list_to_text(self, evidence_list):
        evidence_text = ''
        for evidence in evidence_list:
            evidence_text += f'- {evidence}\n'
        return evidence_text


# example usage
# python chat_agent.py --query '안녕하세요'
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='곡성군의 총 인구수와 혼인 비율을 알려줘.')
    args = parser.parse_args()
    
    chat_agent = ChatAgentModule(verbose=True)
    result = chat_agent.run(args.query, chat_history=[])
    print(f'chat result: {result}')