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
from models.llm.chain import InstantlyAnswerableDiscriminatorChain, PlanAnswerChain, DBToolQueryGeneratorChain, ExtractEvidenceChain, ExtractIntentChain

class ChatAgentModule:
    def __init__(self, verbose=False):
        self.tools = [DBSearchTool(), KGDBSearchTool()]
        self.tool_dict = self.create_tool_dict(self.tools)
        self.instantly_answerable_discriminator = InstantlyAnswerableDiscriminatorChain(verbose=verbose)
        self.extract_intent_chain = ExtractIntentChain(verbose=verbose)
        self.db_tool_query_generator = DBToolQueryGeneratorChain(verbose=verbose)
        self.extract_evidence_chain = ExtractEvidenceChain(verbose=verbose)
        self.plan_answer_chain = PlanAnswerChain(verbose=verbose, streaming=True)
    
    def run(self, query, file_uuid:List[str]=None, project_id=None, chat_history: List[List[str]]=[], queue=None):
        """
        Args:
            query (str): user input
            file_uuid (List[str]): file uuid list for database search
            project_id (str): project id for database search
            queue (Queue): queue for streaming
            chat_history (List[List[str]]): [[user input, assistant output], ...]
        """
        queue = queue if queue else []
        streaming_callback = CustomStreamingStdOutCallbackHandler(queue=queue)
        enrich_query = self.extract_intent_chain.run(query=query, chat_history=chat_history)
        instantly_answerable, answer = self.instantly_answerable_discriminator.run(query=enrich_query, chat_history=chat_history)
        
        if instantly_answerable:
            return answer
        
        tool_results = self.execute_search_tools(enrich_query, file_uuid, project_id)
        tool_result = self.process_search_tool_results(tool_results)
        evidence_list = self.extract_evidence(tool_result, enrich_query, queue)
        evidence_text = self.evidence_list_to_text(evidence_list)

        answer = self.plan_answer_chain.run(query=enrich_query, context=evidence_text, callbacks=[streaming_callback])
        print('queue', queue)
        return answer
    
    def execute_tool(self, args):
        action, action_input = args[0], args[1:]
        action_input = self.parse_tool_args(action, action_input)
        if action in self.tool_dict:
            tool = self.tool_dict[action]
            return tool.run(action_input)
        
    def parse_tool_args(self, action, action_input):
        if action == 'Database Search':
            query, file_uuid, project_id = action_input
            return {'query': query, 'file_uuid': file_uuid, 'project_id': project_id}
        elif action == 'Knowledge Graph Search':
            query, project_id = action_input
            return {'query': query, 'project_id': project_id}

    def execute_search_tools(self, query, file_uuid, project_id):
        db_query_list = self.db_tool_query_generator.run(query=query)
        tool_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            args_list = self.prepare_tool_args(db_query_list, file_uuid, project_id)
            future_to_tool = {executor.submit(self.execute_tool, args): args for args in args_list}
            for future in concurrent.futures.as_completed(future_to_tool):
                tool_results.append(future.result())
        return tool_results

    def prepare_tool_args(self, db_query_list, file_uuid, project_id):
        if file_uuid:
            return [('Database Search', db_query, file_uuid, project_id) for db_query in db_query_list]
        else:
            return [('Knowledge Graph Search', db_query, project_id) for db_query in db_query_list]

    def extract_evidence(self, tool_results, enrich_query, queue):
        args_list = [(enrich_query, tool_result['document'], tool_result['chunk'], tool_result['bbox']) for tool_result in tool_results]
        evidence_list, document_list = [], []
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            future_to_chunk = {executor.submit(self.process_chunk, args): args for args in args_list}
            for future in concurrent.futures.as_completed(future_to_chunk):
                result = future.result()
                evidence_list.extend(result[0])
                if result[1] not in document_list:
                    document_list.append(result[1])
                    queue.append([result[1], result[2]])
        queue.append('DOCUMENT END')
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
    
    def process_search_tool_results(self, tool_results):
        processed_tool_result = []

        max_length = max(len(tool_result) for tool_result in tool_results)

        for i in range(max_length):
            for tool_result in tool_results:
                if len(tool_result) > i and tool_result[i] not in processed_tool_result:
                    processed_tool_result.append(tool_result[i])
        return processed_tool_result[:12]

# example usage
# python custom_chat_agent_module.py --query "국내 전기차 1위부터 10위까지 표로 그려줘" --file_uuid ee0f98fa-c58a-4dfb-b869-85d9587c7c4f
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='국내 전기차 1위부터 10위까지 표로 그려줘')
    parser.add_argument('--file_uuid', type=str, nargs='*', default=None)
    parser.add_argument('--project_id', type=int, default=-1)
    args = parser.parse_args()
    
    chat_agent = ChatAgentModule(verbose=True)
    result = chat_agent.run(args.query, args.file_uuid, args.project_id)
    print(f'chat result: {result}')