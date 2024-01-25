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

from models.tools import DBSearchTool, KGDBSearchTool
from models.llm.agent.custom_streming_callback import CustomStreamingStdOutCallbackHandler
from models.llm.chain import CommonChatChain, PlanAnswerChain, DBToolQueryGeneratorChain, ExtractEvidenceChain, ExtractIntentChain, ExtractIntentAndQueryChain

class ChatAgentModule:
    def __init__(self, es, knowledge_graph_db, streaming=True, verbose=False, limit_chunk_num=40):
        self.tools = [DBSearchTool(es), KGDBSearchTool(knowledge_graph_db)]
        self.tool_dict = self.create_tool_dict(self.tools)
        self.streaming = streaming
        self.common_chat_chain = CommonChatChain(verbose=verbose)
        self.extract_intent_and_query_chain = ExtractIntentAndQueryChain(verbose=verbose)
        self.extract_evidence_chain = ExtractEvidenceChain(verbose=verbose)
        self.plan_answer_chain = PlanAnswerChain(verbose=verbose, streaming=self.streaming)        
        self.limit_chunk_num = limit_chunk_num # project의 chunk수가 limit_chunk_num보다 작으면 elastic search로 검색, limit_chunk_num보다 크면 knowledge graph로 검색
    
    def run(self, query, file_uuid:List[str]=None, project_id=None, chat_history: List[List[str]]=[], queue=None, chain_input_chat_history_num=3):
        """
        Args:
            query (str): user input
            file_uuid (List[str]): file uuid list for database search
            project_id (str): project id for database search
            chat_history (List[List[str]]): [[user input, assistant output], ...]
            queue (Queue): queue for streaming
            chain_input_chat_history_num (int): number of chat history to input to chain
        """
        if queue is None:
            queue = []
        callbacks = [CustomStreamingStdOutCallbackHandler(queue=queue)] if self.streaming else None
        chat_history = chat_history[-chain_input_chat_history_num:]

        # version1: enrich_query와 db_query_list를 분리된 chain으로 실행
        # enrich_query = self.extract_intent_chain.run(query=query, chat_history=chat_history)
        # db_query_list = self.db_tool_query_generator.run(query=enrich_query)
        
        # version2: enrich_query와 db_query_list를 하나의 chain으로 실행
        enrich_query, db_query_list = self.extract_intent_and_query_chain.run(query=query, chat_history=chat_history)

        if len(db_query_list) == 0:
            answer = self.common_chat_chain.run(query=query, chat_history=chat_history, callbacks=callbacks)
            return answer
        
        chunk_num = self.get_chunk_num(file_uuid=file_uuid, project_id=project_id)
        tool_results = self.execute_search_tools(db_query_list, file_uuid, project_id, chunk_num)
        evidence_num = self.calculate_evidence_num(chunk_num)
        tool_result = self.process_search_tool_results(tool_results, evidence_num)
        evidence_list = self.extract_evidence(tool_result, enrich_query, queue, evidence_num)
        evidence_text = self.evidence_list_to_text(evidence_list)

        answer = self.plan_answer_chain.run(query=enrich_query, context=evidence_text, callbacks=callbacks)
        return answer
    
    def execute_tool(self, args):
        action, action_input = args[0], args[1:]
        action_input = self.parse_tool_args(action, action_input)
        if action in self.tool_dict:
            tool = self.tool_dict[action]
            return tool.run(**action_input)
        
    def parse_tool_args(self, action, action_input):
        if action == 'Database Search':
            if len(action_input) == 2:
                query, project_id = action_input
                return {'query': query, 'project_id': project_id}
            elif len(action_input) == 3:
                query, file_uuid, project_id = action_input
                return {'query': query, 'file_uuid': file_uuid, 'project_id': project_id}
        elif action == 'Knowledge Graph Search':
            query, project_id = action_input
            return {'query': query, 'project_id': project_id}
        else:
            raise ValueError(f'Invalid action: {action}. Only Database Search and Knowledge Graph Search are supported')

    def execute_search_tools(self, db_query_list, file_uuid, project_id, chunk_num):
        tool_results = []
        args_list = self.prepare_tool_args(db_query_list, file_uuid, project_id, chunk_num)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(db_query_list)) as executor:
            future_to_tool = {executor.submit(self.execute_tool, args): args for args in args_list}
            for future in concurrent.futures.as_completed(future_to_tool):
                tool_results.append(future.result())
        return tool_results

    def prepare_tool_args(self, db_query_list, file_uuid, project_id, chunk_num):
        if file_uuid:
            return [('Database Search', db_query, file_uuid, project_id) for db_query in db_query_list]
        else:
            if chunk_num < self.limit_chunk_num:
                return [('Database Search', db_query, project_id) for db_query in db_query_list]
            else:
                return [('Knowledge Graph Search', db_query, project_id) for db_query in db_query_list]

    def extract_evidence(self, tool_results, enrich_query, queue, evidence_num):
        args_list = [(enrich_query, tool_result['document'], tool_result['chunk'], tool_result['bbox']) for tool_result in tool_results]
        evidence_list, document_list, file_uuid_bbox_list = [], [], []
        with concurrent.futures.ThreadPoolExecutor(max_workers=evidence_num) as executor:
            future_to_chunk = {executor.submit(self.process_chunk, args): args for args in args_list}
            for future in concurrent.futures.as_completed(future_to_chunk):
                result = future.result()
                evidence_list.extend(result[0])
                if result[1] not in document_list:
                    document_list.append(result[1])
                    file_uuid_bbox_list.append({result[1]: result[2]}) # queue는 backend에서 넘겨준다
        file_uuid_bbox_dict = self.merge_dict(file_uuid_bbox_list)
        queue.set_document_info(file_uuid_bbox_dict) 
        queue.document_end()
        return evidence_list
        
    def create_tool_dict(self, tools):
        return {tool.name: tool for tool in tools}
    
    def evidence_list_to_text(self, evidence_list):
        evidence_text = ''
        for evidence in evidence_list:
            evidence_text += f'- {evidence}\n'
        return evidence_text

    def process_chunk(self, args):
        enrich_query, document, chunk, bbox = args
        return self.extract_evidence_chain.run(query=enrich_query, context=chunk, document=document, bbox=bbox)
    
    def merge_dict(self, file_uuid_bbox_list):
        file_uuid_bbox_dict = {}
        for file_uuid_bbox in file_uuid_bbox_list:
            file_uuid_bbox_dict.update(file_uuid_bbox)
        return file_uuid_bbox_dict
    
    def process_search_tool_results(self, tool_results, evidence_num):
        processed_tool_result = []

        max_length = max(len(tool_result) for tool_result in tool_results)

        for i in range(max_length):
            for tool_result in tool_results:
                if len(tool_result) > i and tool_result[i] not in processed_tool_result:
                    processed_tool_result.append(tool_result[i])
        return processed_tool_result[:evidence_num]
    
    def calculate_evidence_num(self, chunk_num, chunk_evidence_ratio=0.1, min_evidence_num=4, max_evidence_num=12):
        evidence_num = min(max(min_evidence_num, int(chunk_num*chunk_evidence_ratio)), max_evidence_num)
        return evidence_num

    def get_chunk_num(self, project_id, file_uuid=None):        
        return self.tool_dict['Knowledge Graph Search'].get_chunk_num(project_id)

def profile_run(query, file_uuid, project_id, chat_agent):
    """
    Function to be profiled, calling the run method of ChatAgentModule.

    Args:
        query (str): user input
        file_uuid (List[str]): file uuid list for database search
        project_id (str): project id for database search
        chat_agent (ChatAgentModule): instance of ChatAgentModule
    """
    for _ in range(5):
        chat_agent.run(query, file_uuid, project_id)

# example usage
# python custom_chat_agent_module.py --query "국내 전기차 1위부터 10위까지 표로 그려줘" --file_uuid 002d8864-88c2-498c-91df-3e749489616f
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='타입드의 대표가 누구야?')
    parser.add_argument('--file_uuid', type=str, nargs='*', default=None)
    parser.add_argument('--project_id', type=int, default=-1)
    args = parser.parse_args()
    
    chat_agent = ChatAgentModule(verbose=True)
    result = chat_agent.run(args.query, args.file_uuid, args.project_id)
    print(f'chat result: {result}')
    # cProfile.runctx('profile_run(args.query, args.file_uuid, args.project_id, chat_agent)', 
    #                 globals(), locals(), 'base-gpt4.prof')
