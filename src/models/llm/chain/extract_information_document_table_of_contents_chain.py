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
from models.llm.templates.extract_information_document_table_of_contents_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class ExtractInformationDocumentTableofContentsChain(BaseChatChain):
    def __init__(self, 
                system_prompt_template:str=SYSTEM,
                user_prompt_template:str=USER,
                response_format="json",
                # model='gpt-4-0125-preview',
                model='gpt-3.5-turbo-0125',
                temperature=0.0,
                top_p=0.0,
                verbose=False) -> None:
        super().__init__(system_prompt_template=system_prompt_template, user_prompt_template=user_prompt_template, response_format=response_format, verbose=verbose, model=model, temperature=temperature, top_p=top_p)
        self.input_keys = ['table_of_contents', 'context']
        self.output_keys = ['extracted information']

    def run(self, table_of_contents=None, context=None, chat_history=[], callbacks=None):
        return super().run(table_of_contents=table_of_contents, context=context, chat_history=chat_history, callbacks=callbacks)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        values = result['extracted information']
        return values
    
if __name__ == '__main__':
    table_of_contents = '# 1. Introduction to Electric Vehicle Market\n## 1.1 Growing Interest in Electric Vehicles (EVs) Post-COVID-19'
    context = 'Deloitte Insights Global Insights 30 전기차 시장 전망 2030년을 대비하기 위한 전략 Global Insights 30 Deloitte Insights Dr. Jamie Hamilton, Dr. Bryn Walton 외 4인 전기차 시장 전망 31 자동차 산업 전문팀 특집 COVID-19 팬데믹이 자동차를 비롯한 모든 비즈니스를 혼란에 빠뜨리기 전까지 전기차에 대한 관 심도는 계속해서 높아지고 있었다. 배터리 전기차와 하이브리드 전기차의 판매량 합계는 2019년 처음으로 2백만 대를 넘어섰다. 비록 경제 불확실성과 소비자 구매 행태 변화로 성장세가 다소 주 춤하고 있지만, 전기차 시장에 계속해서 관심을 가질 필요가 있다. 최근 전기차 시장은 단순 판매량 증가를 넘어서는 변화를 보이고 있다. 완성차제조사(OEM)들은 새로 운 전기차 모델을 생산하기 위해 R&D서부터 공장 재 정비에 이르는 부문에 수억 달러를 투자하였으며, 소 비자의 행동과 생각에도 변화가 생기고 있다. 하지만 COVID-19로 전세계적인 수요와 공급에 모두 차질이 생기고 말았으며, 현 상황을 반영한 데이터에 기반하여 시장 전망을 수정할 필요가 있다. 본 리포트 제 1장에서는 전세계 전기차 시장의 현 황을 살펴보고, 다양한 부문에서 성장을 견인하는 요 소들을 분석하여 향후 10년 간의 시장 변화를 예측하 였다. 2030년까지 지속될 것으로 보이는 전기차 시장 의 성장은 기존 OEM, 신규 진입 OEM, OEM 연계 금 융사(captive finance), 딜러사 등에게 기회와 위기 를 동시에 가져올 것으로 보인다. 특히, 경쟁이 심화되 어가는 현 상황에서 기존 OEM에게 본 리포트가 공략 대상 고객 및 전략을 재정비하는 데 도움이 될 수 있 을 것이다. 새로운 기회를 포착하고 리스크를 관리하기 위해 서는 기존과 다른 시장 세분화 전략을 취하는 것이 중 요하다. 이에 대한 자세한 내용은 제 2장에서 다루고 있는데, 전세계 OEM과 기타 이해관계자들에게 정보 와 인사이트를 제공하기 위한 목적으로 주요 자동차 소 비 시장 중 하나인 영국의 사례를 설명하고 있다. 본 리 포트의 인사이트를 활용하여 미래의 10년을 대비한다 면, 팬데믹이 불러일으킨 위기를 극복하고 전기차 시 장이 중심이 되는 미래로의 도약을 가속화할 수 있을 것이다. 본 리포트에서 사용되는 전기차(EVs: Electric Vehicles) 라는 용어는 배터리 전기(BEV: Battery Electric Vehicles) 플러그인 하이브리드 전기차(PHEV: Plug-in Hybrid Electric Vehicles) 모두를 지칭한다. 1 별도로 언급되지 않는 이상, 본 리포트의 분석은 상기 두 가지 구동 방식을 모두 고려한다. · BEV 는 배터리로만 동력을 얻는다. 전기 모터를 활용하여 구동되며, 탄소를 전혀 배출하지 않는다. · PHEV 는 20-30마일 정도 주행 시 무공해 운행이 가능하나 이보다 장거리를 주행할 때에는 휘발유 나 디젤을 사용한다. 이름에서 알 수 있듯, 무공해 성능을 최대화하기 위해서는 전기 공급원에 연결 되어야 한다. 개요 1 "Fuel Type & Powertrain Technology", SMMT, https://www.smmt.co.uk/industry-topics/emissions/fu- el-type- and-powertrain-technology/, accessed 18 May 2020. Deloitte Insights Global Insights 32 지난 2년간 전기차 시장이 보여준 지속적인 성장 은 2020년대에도 계속될 것으로 예상되며, 이는 COVID-19가 미친 단기적 영향에도 불구하고 희망적 인 전망을 시사한다. BEV와 PHEV의 판매량이 2019 년 2백만 대를 넘어서며(그림 1) 전체 신규 자동차 판 매량의 2.5%를 전기차가 차지하였다. 2019년 BEV 가 전세계 전기차 판매량의 74%를 차지하였고, 이는 2018년 대비 6%p 증가한 수치이다. 이러한 변화는 유럽에서 탄소 배출 기준이 강화되고 자동차 제조사에 무공해 자동차의 생산 및 판매를 촉구하면서 더욱 가속 화되었다. 이 외에도 중국에서 BEV 시장이 타 국가 대 비 높은 성장세를 보인 것이 주 요인으로 보인다. 미국 과 유럽의 전기차 기술은 BEV가 장악하고 있지만, 시 장 점유율은 중국보다 작다. 작년 초반의 실적 발표 이후 각 지역별 전기차 판 매 실적 증가율의 격차가 매우 뚜렷해졌다. 예를 들어, 2018년 대비 2019년 전기차 판매량은 15% 증가했 으며, 유럽(+93%), 중국(+17%), 그리고 기타 지역 (+22%)의 BEV 판매 실적이 이를 견인하였다. 이에 반해, 미국에서의 BEV 판매량은 2% 감소하였다(그 림1). 그리고 2020년 상반기에는 COVID-19 발생 으로 여러 지역에서 전기차 판매 증가율이 다소 주춤 하거나 감소하게 되었다. 회복세 또한 지역별로 상이 할 전망이다. COVID-19가 향후 3년 동안 전체 자동차 판매량에 영향을 미치더라도 향후 10년'
    extract_information_document_table_of_contents_chain = ExtractInformationDocumentTableofContentsChain(verbose=True)
    extracted_information = extract_information_document_table_of_contents_chain.run(table_of_contents=table_of_contents, context=context)
    print(extracted_information)