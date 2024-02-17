import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import copy
import json
import threading

from prettytable import PrettyTable, ALL

from models.llm.chain import ExtractIntentAndQueryChain, ExtractEvidenceChain, PlanAnswerChain, DocumentCoverageCheckerChain, CommonChatChain, ExtractColumnValueChain, ExtractRelevanceChain

class TestChain:
    def __init__(self, chain, test_json_path, save_dir='./'):
        self.chain = chain
        self.class_name = chain.__class__.__name__
        self.input_keys = self.chain.input_keys
        self.output_keys = self.chain.output_keys
        self.test_set = self.load_json(test_json_path)['data']
        self.save_dir = save_dir
        
    def load_json(self, json_path):
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        return json_data
            
    def test_thread(self, test_case):
        input_dict, golden_output = test_case['input'], test_case['golden output']
        test_case['output'] = {}
        result = self.chain.run(**input_dict)
        for idx, output_key in enumerate(self.output_keys):                
            if type(result) == tuple:
                result_value = result[idx]
            else:
                result_value = result
            test_case['output'][output_key] = result_value

    def test(self):
        threads = []
        cp_test_set = copy.deepcopy(self.test_set)  # 테스트할 케이스 수 제한

        for test_case in cp_test_set:
            thread = threading.Thread(target=self.test_thread, args=(test_case,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()  # 모든 스레드가 완료될 때까지 기다림

        self.visualize_result(cp_test_set)
        self.save_results(cp_test_set)
            
    def visualize_result(self, test_set):
        table = PrettyTable()
        table.hrules = ALL
        table.field_names = ["id"] + ["Input " + key for key in self.input_keys] + ["Output " + key for key in self.output_keys] + ["Golden " + key for key in self.output_keys]
        for idx, test_result in enumerate(test_set):
            row = []
            row.append(idx+1)
            for input_key in self.input_keys:
                cell_input = test_result['input'][input_key]
                cell = self.format_cell(self.parse_to_str(cell_input))
                row.append(cell)
            for output_key in self.output_keys:
                cell_input = test_result['output'][output_key]
                cell = self.format_cell(self.parse_to_str(cell_input))
                row.append(cell)
            for output_key in self.output_keys:
                cell_input = test_result['golden output'][output_key]
                cell = self.format_cell(self.parse_to_str(cell_input))
                row.append(cell)
            table.add_row(row)
        with open(f"./{self.class_name}_results_table.txt", "w") as f:
            f.write(str(table))
        print(table)
        
    def save_results(self, results):
        output_data = {"data": results}
        with open(f"{self.save_dir}/{self.class_name}_results.json", "w") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
            
    def parse_chat_history(self, chat_history):
        chat_history_text = ''
        for chat in chat_history:
            user, assistant = chat
            chat_history_text += f"U: {user}\nA: {assistant}\n"
        return chat_history_text
    
    def parse_to_str(self, result):
        if isinstance(result, list):
            result = [str(item) for item in result]
            text = ', '.join(result)
        elif isinstance(result, bool):
            text = str(result)
        elif isinstance(result, str):
            text = result
        else:
            text = str(result)
        return text
            
    def format_cell(self, data):
        # max_width = 28 # input, ouput key 수가 합쳐서 6개
        max_width = 46
        # max_width = 50 # input, ouput key 수가 합쳐서 4개
        return '\n'.join([data[i:i+max_width] for i in range(0, len(data), max_width)])

if __name__ == "__main__":
    # extract_evidence_chain = ExtractEvidenceChain(verbose=True)
    # test_chain = TestChain(extract_evidence_chain, './extract_evidence_chain_test.json')
    
    # plan_answer_chain = PlanAnswerChain(verbose=True)
    # test_chain = TestChain(plan_answer_chain, './plan_answer_chain_test.json')
    
    # extract_intent_and_query_chain = ExtractIntentAndQueryChain(verbose=True)
    # test_chain = TestChain(extract_intent_and_query_chain, './extract_intent_and_query_chain_test.json')
    
    # document_coverage_checker_chain = DocumentCoverageCheckerChain(verbose=True)
    # test_chain = TestChain(document_coverage_checker_chain, './document_coverage_checker_chain_test.json')
    
    # common_chat_chain = CommonChatChain(verbose=True)
    # test_chain = TestChain(common_chat_chain, './common_chat_chain_test.json')
    
    extract_column_value_chain = ExtractColumnValueChain(verbose=True)
    test_chain = TestChain(extract_column_value_chain, './extract_column_value_chain_test.json')
    
    # extract_relevance_chain = ExtractRelevanceChain(verbose=True)
    # test_chain = TestChain(extract_relevance_chain, './extract_relevance_chain_test.json')
    
    test_chain.test()