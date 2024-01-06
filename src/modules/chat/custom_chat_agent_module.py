import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import argparse
import concurrent.futures
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
        # result = self.instantly_answerable_discriminator.run(query=enrich_query, chat_history=chat_history)
        
        # if result['instantly answerable'] == 'yes':
        #     answer = result['answer']
        # else:
        db_query_list = self.db_tool_query_generator.run(query=enrich_query)
        tool_results = []
        for db_query in db_query_list:
            tool_results.append(self.execute_tool('Database Search', db_query))
        tool_result = self.process_tool_result(tool_results)

        args_list = [(enrich_query, chunk) for chunk in tool_result]
        evidence_list = []

        # Use ThreadPoolExecutor for multithreading
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            # Submit all tasks to the executor
            future_to_chunk = {executor.submit(self.process_chunk, args): args for args in args_list}

            # Collecting results as they are completed
            for future in concurrent.futures.as_completed(future_to_chunk):
                evidence_list.extend(future.result())

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

    def process_chunk(self, args):
        enrich_query, chunk = args
        return self.extract_evidence_chain.run(query=enrich_query, context=chunk)
    
    def process_tool_result(self, tool_results):
        processed_tool_result = []

        # 가장 긴 하위 리스트의 길이 찾기
        max_length = max(len(tool_result) for tool_result in tool_results)

        # 각 인덱스 위치의 원소를 추출하여 새 리스트에 추가 (중복 제외)
        for i in range(max_length):
            for tool_result in tool_results:
                if len(tool_result) > i and tool_result[i] not in processed_tool_result:
                    processed_tool_result.append(tool_result[i])

        return processed_tool_result[:12]



# example usage
# python chat_agent.py --query '안녕하세요'
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='곡성군의 인구수와 혼인 비율을 알려줘.')
    args = parser.parse_args()
    
    chat_agent = ChatAgentModule(verbose=True)
    result = chat_agent.run(args.query, chat_history=[])
    print(f'chat result: {result}')