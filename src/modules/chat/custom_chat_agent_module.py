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

from database.elastic_search.custom_elastic_search import CustomElasticSearch
from database.knowledge_graph.graph_construct import KnowledgeGraphDataBase
from models.tools import DBSearchTool, KGDBSearchTool
from models.llm.agent.custom_streming_callback import CustomStreamingStdOutCallbackHandler
from models.llm.agent.streaming_queue import StreamingQueue
from models.llm.chain import CommonChatChain, PlanAnswerChain, DBToolQueryGeneratorChain, ExtractEvidenceChain, ExtractIntentChain, ExtractIntentAndQueryChain, ExtractRelevanceChain

class ChatAgentModule:
    def __init__(self, es, knowledge_graph_db, streaming=True, verbose=False, limit_chunk_num=1000000, chain_input_chat_history_num=2):
        self.tools = [DBSearchTool(es), KGDBSearchTool(knowledge_graph_db)]
        self.tool_dict = self.create_tool_dict(self.tools)
        self.streaming = streaming
        self.common_chat_chain = CommonChatChain(verbose=verbose, streaming=self.streaming)
        self.extract_intent_and_query_chain = ExtractIntentAndQueryChain(verbose=verbose)
        self.extract_relevance_chain = ExtractRelevanceChain(verbose=verbose)
        self.extract_evidence_chain = ExtractEvidenceChain(verbose=verbose)
        self.plan_answer_chain = PlanAnswerChain(verbose=verbose, streaming=self.streaming)
        self.limit_chunk_num = limit_chunk_num # project의 chunk수가 limit_chunk_num보다 작으면 elastic search로 검색, limit_chunk_num보다 크면 knowledge graph로 검색
        self.chain_input_chat_history_num = chain_input_chat_history_num
    
    def run(self, query, file_uuid:List[str]=None, project_id=None, chat_history: List[List[str]]=[], queue=None, idx_evidence_use=True):
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
            queue = StreamingQueue()
        callbacks = [CustomStreamingStdOutCallbackHandler(queue=queue)] if self.streaming else None
        chat_history = chat_history[-self.chain_input_chat_history_num:]

        # version1: enrich_query와 db_query_list를 분리된 chain으로 실행
        # enrich_query = self.extract_intent_chain.run(query=query, chat_history=chat_history)
        # db_query_list = self.db_tool_query_generator.run(query=enrich_query)
        
        # version2: enrich_query와 db_query_list를 하나의 chain으로 실행
        enrich_query, db_query_list = self.extract_intent_and_query_chain.run(query=query, chat_history=chat_history)
        if len(db_query_list) == 0:
            # answer = self.common_chat_chain.run(query=query, chat_history=chat_history, callbacks=callbacks)
            is_lang_ko = self.contains_korean(query)
            answer = callbacks[0].dummy_tokens  # "죄송합니다. 저는 입력하신 문서에 대해서만 답변드릴 수 있습니다."
            callbacks[0].add_dummy_tokens(is_lang_ko)
            file_uuid_bbox_dict = {} # "안녕" 같은 단순한 질문에 대한 답변은 evidence가 없으므로 빈 dict를 반환
            queue.set_document_info(file_uuid_bbox_dict)  
            queue.document_end()
            return file_uuid_bbox_dict, answer
        
        # chunk_num = self.get_chunk_num(file_uuid=file_uuid, project_id=project_id)
        chunk_num = 100
        tool_results = self.execute_search_tools(db_query_list, file_uuid, project_id, chunk_num)
        evidence_num = self.calculate_evidence_num(chunk_num)
        tool_result = self.process_search_tool_results(tool_results, evidence_num)
        evidence_list = self.extract_evidence(tool_result, enrich_query, evidence_num)
        evidence_text = self.evidence_list_to_text(evidence_list)

        answer, used_evidence_idx_list = self.plan_answer_chain.run(query=enrich_query, context=evidence_text, callbacks=callbacks)
        if idx_evidence_use:
            file_uuid_bbox_dict= self.post_process_evidence_with_idx(evidence_list, used_evidence_idx_list, queue)
        else:
            file_uuid_bbox_dict= self.post_process_evidence(evidence_list, used_evidence_idx_list, queue)
        return file_uuid_bbox_dict, answer
    
    def post_process_evidence(self, evidence_list, used_evidence_idx_list, queue):
        document_list, file_uuid_chunk_list = [], []
        used_evidence_list = [evidence_list[idx] for idx in used_evidence_idx_list]
        for used_evidence in used_evidence_list:
            evidence, document, chunk = used_evidence[0], used_evidence[1], used_evidence[2]
            if document not in document_list:
                document_list.append(document)
                file_uuid_chunk_list.append({document: {"text":chunk}}) # queue는 backend에서 넘겨준다
        file_uuid_chunk_dict = self.merge_dict(file_uuid_chunk_list)
        queue.set_document_info(file_uuid_chunk_dict) 
        queue.document_end()
        return file_uuid_chunk_dict
    
    def post_process_evidence_with_idx(self, evidence_list, used_evidence_idx_list, queue):
        file_uuid_chunk_list = []
        idx_used_evidence_list = [[idx, evidence_list[idx]] for idx in used_evidence_idx_list]
        for idx_used_evidence in idx_used_evidence_list:
            idx, used_evidence = idx_used_evidence[0], idx_used_evidence[1]
            evidence, document, chunk = used_evidence[0], used_evidence[1], used_evidence[2]
            file_uuid_chunk_list.append({idx:{"file_uuid":document, "text":chunk}}) # queue는 backend에서 넘겨준다
        file_uuid_chunk_dict = self.merge_dict(file_uuid_chunk_list)
        queue.set_document_info(file_uuid_chunk_dict) 
        queue.document_end()
        return file_uuid_chunk_dict
    
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
        if len(db_query_list) == 0:
            return []
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

    def extract_evidence(self, tool_results, enrich_query, evidence_num):
        args_list = [(enrich_query, tool_result['document'], tool_result['chunk'], tool_result['bbox']) for tool_result in tool_results]
        evidence_list = []
        if evidence_num == 0:
            return []
        with concurrent.futures.ThreadPoolExecutor(max_workers=evidence_num) as executor:
            future_to_chunk = {executor.submit(self.process_chunk, args): args for args in args_list}
            for future in concurrent.futures.as_completed(future_to_chunk):
                result = future.result()
                evidences, document, context = result[0], result[1], result[2]
                for evidence in evidences:
                    evidence_list.append([evidence, document, context])
        
        return evidence_list
        
    def create_tool_dict(self, tools):
        return {tool.name: tool for tool in tools}
    
    def evidence_list_to_text(self, evidence_list):
        evidence_text = ''
        for idx, (evidence, document, bbox) in enumerate(evidence_list):
            evidence_text += f'Content {idx}: {evidence}\n'
        return evidence_text

    def process_chunk(self, args):
        enrich_query, document, chunk, bbox = args
        evidence_list, document, context = self.extract_evidence_chain.run(query=enrich_query, context=chunk, document=document, bbox=bbox)
        evidence_relevance_list = self.extract_relevance_chain.run(query=enrich_query, context=evidence_list)
        # if len(evidence_list) != len(evidence_relevance_list):
        #     print(evidence_list, evidence_relevance_list)
        evidence_list = [evidence_list[i] for i in range(len(evidence_list)) if evidence_relevance_list[i]]
        return evidence_list, document, context
    
    def merge_dict(self, file_uuid_chunk_list):
        file_uuid_chunk_dict = {}
        for file_uuid_chunk in file_uuid_chunk_list:
            file_uuid_chunk_dict.update(file_uuid_chunk)
        return file_uuid_chunk_dict
    
    def process_search_tool_results(self, tool_results, evidence_num):
        processed_tool_result = []

        max_length = max(len(tool_result) for tool_result in tool_results)

        for i in range(max_length):
            for tool_result in tool_results:
                if len(tool_result) > i and tool_result[i] not in processed_tool_result:
                    processed_tool_result.append(tool_result[i])
        return processed_tool_result[:evidence_num]
    
    def calculate_evidence_num(self, chunk_num, chunk_evidence_ratio=0.2, min_evidence_num=10, max_evidence_num=50):
        evidence_num = min(max(min_evidence_num, int(chunk_num*chunk_evidence_ratio)), max_evidence_num)
        return evidence_num

    def get_chunk_num(self, project_id, file_uuid=None):        
        return self.tool_dict['Knowledge Graph Search'].get_chunk_num(project_id, file_uuid)
    
    def contains_korean(self, text):
        # 한글 유니코드 범위 확인
        for char in text:
            if '\uac00' <= char <= '\ud7a3':
                return True  # 한글 문자가 발견되면 True 반환
        return False

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
# python custom_chat_agent_module.py --query "UX 향상시키는 서비스 예시" --file_uuid 06d0a9c5-5f95-4ff9-8807-1a9b87a44591
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='타입드의 대표가 누구야?')
    parser.add_argument('--file_uuid', type=str, nargs='*', default=None)
    parser.add_argument('--project_id', type=int, default=-5)
    args = parser.parse_args()
    
    es = CustomElasticSearch(index_name='refeat_ai', host="http://10.10.10.27:9200")
    knowledge_graph_db = KnowledgeGraphDataBase()
    
    chat_agent = ChatAgentModule(es, knowledge_graph_db, verbose=True)
    file_uuid_bbox_dict, result = chat_agent.run(args.query, args.file_uuid, args.project_id, chat_history=[])
    print(f'file_uuid_bbox_dict: {file_uuid_bbox_dict}')
    print(f'chat result: {result}')
    # cProfile.runctx('profile_run(args.query, args.file_uuid, args.project_id, chat_agent)', 
    #                 globals(), locals(), 'base-gpt4.prof')
