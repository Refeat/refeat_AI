import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import ast
import argparse

from models.llm.base_chain import BaseChatChain
from models.llm.templates.extract_evidence_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class ExtractEvidenceChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                # model='gpt-4-0125-preview',
                model='gpt-3.5-turbo-0125',
                temperature=0.0,
                top_p=0.0,
                verbose=False,) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p)
        self.input_keys = ['query', 'context']
        self.output_keys = ['concise evidence']

    def run(self, query=None, context=None, document=None, bbox=None, chat_history=[]):
        input_dict = self.parse_input(input=query, context=context, chat_history=chat_history)
        for _ in range(self.max_tries):
            try:
                result = self.chain.run(input_dict)
                return self.parse_output(result, document, bbox)
            except Exception as e:
                print(e)
                continue
        print('Failed to run chain.')
        return None
    
    def parse_output(self, output, document, bbox):
        result = ast.literal_eval(output)
        if (document is not None) and (bbox is not None):
            return result['concise evidence'], document, bbox
        else:
            return result['concise evidence']
    
# example usage
# python extract_evidence_chain.py --query "인공지능 분야에 대해 설명해줘" --context "인공지능은 인간의 지능을 컴퓨터로 구현하는 것을 말한다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="저자가 누구야?")
    parser.add_argument('--context', type=str, default="D E P LOT : One-shot visual language reasoning by plot-to-table translation Fangyu Liu ♠♣ ∗ § Julian Martin Eisenschlos ♣∗ Francesco Piccinno ♣ Syrine Krichene ♣ Chenxi Pang ♣ Kenton Lee ♣ Mandar Joshi ♣ Wenhu Chen ♣ Nigel Collier ♠ Yasemin Altun ♣ ♣ Google DeepMind ♠ University of Cambridge Abstract Visual language such as charts and plots is ubiq- uitous in the human world. Comprehending plots and charts requires strong reasoning skills. Prior state-of-the-art (SOTA) models require at least tens of thousands of training examples and their reasoning capabilities are still much limited, especially on complex human-written queries. This paper presents the first few(one)- shot solution to visual language reasoning. We decompose the challenge of visual language reasoning into two steps: (1) plot-to-text trans- lation, and (2) reasoning over the translated text. The key in this method is a modality conver- sion module, named as D E P LOT , which trans- lates the image of a plot or chart to a linearized table. The output of D E P LOT can then be di- rectly used to prompt a pretrained large lan- guage model (LLM), exploiting the few-shot reasoning capabilities of LLMs. To obtain D E - P LOT , we standardize the plot-to-table task by establishing unified task formats and metrics, and train D E P LOT end-to-end on this task. D E - P LOT can then be used off-the-shelf together with LLMs in a plug-and-play fashion. Com- pared with a SOTA model finetuned on thou- sands of data points, D E P LOT +LLM with just one-shot prompting achieves a 29.4% improve- ment over finetuned SOTA on human-written queries from the task of chart QA. 12")
    args = parser.parse_args()
    
    extract_evidence_chain = ExtractEvidenceChain(verbose=True)
    result = extract_evidence_chain.run(query=args.query, context=args.context)
    print(result)
    