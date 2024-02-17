import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from concurrent.futures import ThreadPoolExecutor

from models.tokenizer.utils import get_tokenizer
from models.llm.chain import ExtractInformationDocumentChain, MakeTableofContentsChain, ExtractTableofContentsInformationChain, ReviseTableofContentsChain, DetermineWhatTableofContentsSupportChain, ExtractInformationDocumentTableofContentsChain
from modules.file_to_db.table_of_contents import TableOfContents

class HierarchyDocumentAnalysisModule:
    def __init__(self, ):
        self.extract_information_document_chain = ExtractInformationDocumentChain(verbose=True)
        self.make_table_of_contents_chain = MakeTableofContentsChain(verbose=True)
        self.revise_table_of_contents_chain = ReviseTableofContentsChain(verbose=True)
        self.determine_what_table_of_contents_support_chain = DetermineWhatTableofContentsSupportChain(verbose=True)
        self.extract_information_document_table_of_contents_chain = ExtractInformationDocumentTableofContentsChain(verbose=True)
        self.extract_table_of_contents_information_chain = ExtractTableofContentsInformationChain(verbose=True)
        self.tokenizer = get_tokenizer(model_name='openai')
        self.table_of_contents = None

    def analyze(self, title, context):        
        table_of_contents = self.make_table_of_content(title, context, split_length=128000)
        
        # second_information_list = self.extract_information_document(context, split_length=1000)
        # second_information_text = self.parse_information_list(second_information_list)
        # revised_table_of_contents = self.revise_table_of_content(table_of_contents, second_information_text)
        # print(revised_table_of_contents)
        self.table_of_contents = TableOfContents(table_of_contents)
        self.extract_table_of_contents_information(self.table_of_contents, context, split_length=4000)
        self.save_table_of_contents('table_of_content.txt')
        return self.table_of_contents
    
    def revise_table_of_content(self, table_of_contents, context):
        revised_table_of_content = self.revise_table_of_contents_chain.run(table_of_contents=table_of_contents, context=context)
        return revised_table_of_content
    
    def extract_table_of_contents_information(self, table_of_contents, context, split_length=2000):
        context_parts = self.parse_input_context(context, split_length=split_length)
        
        def extract_information_for_context_part(context_part):
            return self.extract_information_document_table_of_contents_chain.run(
                table_of_contents=table_of_contents.text, context=context_part)

        with ThreadPoolExecutor() as executor:
            # 각 context_part에 대해 정보 추출 작업을 비동기적으로 실행합니다.
            futures = [executor.submit(extract_information_for_context_part, context_part) for context_part in context_parts]
            
            # futures 리스트의 결과를 순서대로 기다립니다.
            extracted_information_lists = [future.result() for future in futures]

        # 순서대로 결과를 처리합니다.
        for extracted_information_list in extracted_information_lists:
            for extracted_information_dict in extracted_information_list:
                try:
                    for section_number, extracted_information in extracted_information_dict.items():
                        section = table_of_contents.get_section(section_number)
                        table_of_contents.add_information_to_section(section, extracted_information)
                except Exception as e:
                    print('Error')
                    print(extracted_information_dict)
                    
                
    def parse_input_context(self, context, split_length=4000):
        encoded_context = self.tokenizer.get_encoding(context)
        context_parts = []
        for i in range(0, len(encoded_context), split_length):
            context_parts.append(self.tokenizer.get_decoding(encoded_context[i:i+split_length]))
        return context_parts
    
    def parse_information_list(self, information_list):
        information_text = ''
        for idx, information in enumerate(information_list):
            information_text += f'Content {idx}: ' + information + '\n'
        return information_text
    
    def save_table_of_contents(self, file_path):
        # save as json file
        with open(file_path, 'w') as f:
            f.write(repr(self.table_of_contents))
    
    def extract_information_document(self, context, split_length=4000, summary=True):
        context_parts = self.parse_input_context(context, split_length)
        information_list = []

        # 멀티 스레드를 사용하여 extract_information_document_chain.run 함수 실행
        with ThreadPoolExecutor() as executor:
            # Future 객체 리스트 생성
            if summary:
                # futures = [executor.submit(self.extract_information_document_chain.run, context=context_part) for context_part in context_parts]
                # for future in futures:
                #     result = future.result()
                #     information_list.append(result)
                information_list = context_parts
            else:
                futures = [executor.submit(self.extract_table_of_contents_information_chain.run, context=context_part) for context_part in context_parts]
                for future in futures:
                    result = future.result()
                    information_list.extend(result)

        return information_list
    
    def make_table_of_content(self, title, context, split_length=4000):
        first_information_list = self.extract_information_document(context, split_length=split_length)
        first_information_text = self.parse_information_list(first_information_list)
        table_of_content = self.make_table_of_contents_chain.run(title=title, context=first_information_text)
        return table_of_content    
    

if __name__ == '__main__':
    text_file = '/home/ubuntu/refeat/ai_module/src/models/test_data/test_text.txt'
    with open(text_file, 'r') as f:
        context = f.read()
    hda_module = HierarchyDocumentAnalysisModule()
    result = hda_module.analyze('Corrective Retrieval Augmented Generation', context)
    print(result)