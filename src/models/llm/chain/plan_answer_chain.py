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
from models.tokenizer.utils import get_tokenizer
from models.llm.templates.plan_answer_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class PlanAnswerChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                # model='gpt-4-0125-preview',
                model='gpt-3.5-turbo-0125',
                temperature=0.5,
                top_p=0.5,
                verbose=False,
                streaming=False) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, streaming=streaming, top_p=top_p)
        self.input_keys = ['query', 'context']
        self.output_keys = ['answer', 'evidence used']

    def run(self, query=None, context=None, chat_history=[], callbacks=None):
        return super().run(input=query, context=context, chat_history=chat_history, callbacks=callbacks)
    
    def parse_output(self, output):
        result = ast.literal_eval(output.strip())
        final_answer, used_evidence_idx_list = result['answer'], result['content used']
        used_evidence_idx_list = [int(idx) for idx in used_evidence_idx_list]
        return final_answer, used_evidence_idx_list
    
# example usage
# python plan_answer_chain.py --query "생성형 AI 시장의 글로벌 및 국내 규모, 세분화된 시장 세그먼트 및 예측된 성장률에 대해 자세히 알려주세요." --context "- Evidence 0: 2025년까지 생성형 AI 지출 비율이 다소 제한적일 것이라고 릭 빌러스가 언급했다.\n- Evidence 1: 생성형 AI 지출을 제한할 수 있는 요인으로는 가격 책정, 프라이버시 및 보안에 대한 우려, 기술에 대한 소비자 반감, 정부 개입을 유발하는 실존적 위기 등이 있다.\n- Evidence 2: 생성형 AI 솔루션 지출은 전체 AI 지출 증가율의 2배 이상이다.\n- Evidence 3: 생성형 AI 기술 지출은 전 세계 IT 지출의 연평균 성장율보다 약 13배 크다.\n- Evidence 4: 2027년까지 생성형 AI 기술 지출의 시장 점유율은 전체 AI 지출에서 28.1%를 차지할 것으로 예측된다.\n- Evidence 5: 2023년 생성형 AI 기술 지출의 시장 점유율은 9.0%이다.\n- Evidence 6: 생성형 AI 서비스 부문의 연평균 성장률은 76.8%로 예측된다.\n- Evidence 7: 생성형 AI 소프트웨어 부문은 2023년-2027년 예측기간 내 가장 빠른 성장을 보일 것으로 예측된다.\n- Evidence 8: 생성형 AI 플랫폼/모델의 연평균 성장률은 96.4%로 기록될 것이다.\n- Evidence 9: 생성형 AI 애플리케이션 개발 및 배포(AD&D) 및 애플리케이션 소프트웨어의 연평균성장률은 82.7%로 예측된다.\n- Evidence 10: IDC의 전체적인 AI 지출은 예측, 해석 및 생성형 AI 솔루션을 구현하기 위한 인프라 하드웨어, 소프트웨어 및 IT/비즈니스 서비스에 대한 수익을 포함한다.\n- Evidence 11: AI 소프트웨어에는 애플리케이션 소프트웨어, 플랫폼/모델 및 애플리케이션 개발 및 배포 소프트웨어가 포함된다.\n- Evidence 12: AI 애플리케이션은 애플리케이션(AI 중심)에 필수적인 AI 구성 요소가 있어야하며 만약 AI 구성 요소가 없으면 애플리케이션이 작동하지 않는 것으로 간주한다.\n- Evidence 13: 2023년 전세계 생성형 AI 솔루션 지출이 약 160억 달러 규모를 기록할 것으로 예상된다.\n- Evidence 14: 5년간의 연평균 성장율(CAGR)은 73.3%로, 2027년 해당 시장 지출은 1,430억 달러 규모를 형성할 것으로 전망된다.\n- Evidence 15: 생성형 AI 솔루션이 기업의 디지털 비즈니스 제어 플랫폼의 기반 요소로 부상하면서 해당 시장은 견조한 성장세를 유지할 것으로 분석됐다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default="아마존 aws s3의 가격 정책에 대해 알려줘")
    parser.add_argument('--context', type=str)
    args = parser.parse_args()
    
    # from models.tools import WebSearchTool
    # web_search_tool = WebSearchTool()
    
    # context = web_search_tool.run(args.query)
    plan_answer_chain = PlanAnswerChain(verbose=True)
    result = plan_answer_chain.run(query=args.query, context=args.context, chat_history=[])
    print(result)