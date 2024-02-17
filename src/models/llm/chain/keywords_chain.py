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
from models.llm.templates.keywords_chain_template import SYSTEM, USER

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class KeywordsChain(BaseChatChain):
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
        self.input_keys = ['context']
        self.output_keys = ['keywords']

    def run(self, context=None, lang='korean', chat_history=[], callbacks=None):
        return super().run(context=context, lang=lang, chat_history=chat_history, callbacks=callbacks)
    
    def parse_output(self, output):
        result = ast.literal_eval(output)
        values = result['keywords']
        return values
    
# example usage
# python keywords_chain.py --context "인공지능 분야는 컴퓨터 공학의 한 분야로서 인간의 지능을 컴퓨터로 구현하는 것을 연구한다."
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--context', type=str, default="아마존 aws s3의 가격은 1GB당 0.023달러이다.")
    args = parser.parse_args()
    
    keywords_chain = KeywordsChain(verbose=True)
    result = keywords_chain.run(context='''"Deloitte Insights Global Insights 30 전기차 시장 전망 2030년을 대비하기 위한 전략 Global Insights 30 Deloitte Insights Dr. Jamie Hamilton, Dr. Bryn Walton 외 4인 전기차 시장 전망 31 자동차 산업 전문팀 특집 COVID-19 팬데믹이 자동차를 비롯한 모든 비즈니스를 혼란에 빠뜨리기 전까지 전기차에 대한 관 심도는 계속해서 높아지고 있었다. 배터리 전기차와 하이브리드 전기차의 판매량 합계는 2019년 처음으로 2백만 대를 넘어섰다. 비록 경제 불확실성과 소비자 구매 행태 변화로 성장세가 다소 주 춤하고 있지만, 전기차 시장에 계속해서 관심을 가질 필요가 있다. 최근 전기차 시장은 단순 판매량 증가를 넘어서는 변화를 보이고 있다. 완성차제조사(OEM)들은 새로 운 전기차 모델을 생산하기 위해 R&D서부터 공장 재 정비에 이르는 부문에 수억 달러를 투자하였으며, 소 비자의 행동과 생각에도 변화가 생기고 있다. 하지만 COVID-19로 전세계적인 수요와 공급에 모두 차질이 생기고 말았으며, 현 상황을 반영한 데이터에 기반하여 시장 전망을 수정할 필요가 있다. 본 리포트 제 1장에서는 전세계 전기차 시장의 현 황을 살펴보고, 다양한 부문에서 성장을 견인하는 요 소들을 분석하여 향후 10년 간의 시장 변화를 예측하 였다. 2030년까지 지속될 것으로 보이는 전기차 시장 의 성장은 기존 OEM, 신규 진입 OEM, OEM 연계 금 융사(captive finance), 딜러사 등에게 기회와 위기 를 동시에 가져올 것으로 보인다. 특히, 경쟁이 심화되 어가는 현 상황에서 기존 OEM에게 본 리포트가 공략 대상 고객 및 전략을 재정비하는 데 도움이 될 수 있 을 것이다. 새로운 기회를 포착하고 리스크를 관리하기 위해 서는 기존과 다른 시장 세분화 전략을 취하는 것이 중 요하다. 이에 대한 자세한 내용은 제 2장에서 다루고 있는데, 전세계 OEM과 기타 이해관계자들에게 정보 와 인사이트를 제공하기 위한 목적으로 주요 자동차 소 비 시장 중 하나인 영국의 사례를 설명하고 있다. 본 리 포트의 인사이트를 활용하여 미래의 10년을 대비한다 면, 팬데믹이 불러일으킨 위기를 극복하고 전기차 시 장이 중심이 되는 미래로의 도약을 가속화할 수 있을 것이다. 본 리포트에서 사용되는 전기차(EVs: Electric Vehicles) 라는 용어는 배터리 전기(BEV: Battery Electric Vehicles) 플러그인 하이브리드 전기차(PHEV: Plug-in Hybrid Electric Vehicles) 모두를",
        "지칭한다. 1 별도로 언급되지 않는 이상, 본 리포트의 분석은 상기 두 가지 구동 방식을 모두 고려한다. · BEV 는 배터리로만 동력을 얻는다. 전기 모터를 활용하여 구동되며, 탄소를 전혀 배출하지 않는다. · PHEV 는 20-30마일 정도 주행 시 무공해 운행이 가능하나 이보다 장거리를 주행할 때에는 휘발유 나 디젤을 사용한다. 이름에서 알 수 있듯, 무공해 성능을 최대화하기 위해서는 전기 공급원에 연결 되어야 한다. 개요 1 \"Fuel Type & Powertrain Technology\", SMMT, https://www.smmt.co.uk/industry-topics/emissions/fu- el-type- and-powertrain-technology/, accessed 18 May 2020. Deloitte Insights Global Insights 32 지난 2년간 전기차 시장이 보여준 지속적인 성장 은 2020년대에도 계속될 것으로 예상되며, 이는 COVID-19가 미친 단기적 영향에도 불구하고 희망적 인 전망을 시사한다. BEV와 PHEV의 판매량이 2019 년 2백만 대를 넘어서며(그림 1) 전체 신규 자동차 판 매량의 2.5%를 전기차가 차지하였다. 2019년 BEV 가 전세계 전기차 판매량의 74%를 차지하였고, 이는 2018년 대비 6%p 증가한 수치이다. 이러한 변화는 유럽에서 탄소 배출 기준이 강화되고 자동차 제조사에 무공해 자동차의 생산 및 판매를 촉구하면서 더욱 가속 화되었다. 이 외에도 중국에서 BEV 시장이 타 국가 대 비 높은 성장세를 보인 것이 주 요인으로 보인다. 미국 과 유럽의 전기차 기술은 BEV가 장악하고 있지만, 시 장 점유율은 중국보다 작다. 작년 초반의 실적 발표 이후 각 지역별 전기차 판 매 실적 증가율의 격차가 매우 뚜렷해졌다. 예를 들어, 2018년 대비 2019년 전기차 판매량은 15% 증가했 으며, 유럽(+93%), 중국(+17%), 그리고 기타 지역 (+22%)의 BEV 판매 실적이 이를 견인하였다. 이에 반해, 미국에서의 BEV 판매량은 2% 감소하였다(그 림1). 그리고 2020년 상반기에는 COVID-19 발생 으로 여러 지역에서 전기차 판매 증가율이 다소 주춤 하거나 감소하게 되었다. 회복세 또한 지역별로 상이 할 전망이다. COVID-19가 향후 3년 동안 전체 자동차 판매량에 영향을 미치더라도 향후 10년 간 시장이 성장할 것이 라는 예측은 유효할 것으로 보인다. 미래에 펼쳐질 상",
        "황을 이해하기 위해 지난 몇 년 동안 각국 시장에서 어 떠한 사건들이 발생하였는지 먼저 파악해야 한다. 제 1장: 글로벌 동향 및 전망 그림 1 전기차: 주요 지역 별 연간 승용차 및 경차 판매량 중국 BEV 기타지역 BEV 기타 지역PHEV EV 점유율 중국 PHEV 유럽 BEV 유럽 PHEV 미국 BEV 미국 PHEV 2500 2000 1500 1000 500 0 전기차 판매량 (천대) 시장 점유율 3.0% 2.5% 2.0% 1.5% 1.0% 0.0% 0.5% 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 출처: 딜로이트 분석, IHS Markit, EV-volumes.com 2 전기차 시장 전망 33 자동차 산업 전문팀 특집 각 국가별 전기차 시장 유럽 2019년 유럽의 전기차 시장은 타 국가에 비해 더욱 괄목할 만한 성장을 보였다. 노르웨이는 시장 점유율 56%를 달성하였으며, 네덜란드에서 가장 잘 팔리는 자동차 10위 중 1, 2위는 모두 BEV가 차지하였다. 즉, 북유럽 국가 및 네덜란드가 이러한 성장의 중심에 있 었다. 3 영국을 비롯한 기타 국가에서 전기차는 연간 세자리 수 성장률을 보였다. 기후 변화 우려로 정부가 정책적 으로 전기차를 지원하고 소비자의 태도가 변화한 것이 촉매제 역할을 했다. 기후 변화 문제는 다수 유럽 정부의 주요 시책 중 하나로 자리잡았다. 영국 정부는 2050년까지 탄소 배 출량을 0으로 줄일 예정이며, 2035년까지 공해 배출 차량의 판매를 금지시킬 것이라 밝혔다. 4 독일은 온실 가스 배출량을 1990년 대비 2020년 말까지 40%, 2040년 말까지 55%, 2050년 말까지 95% 감축할 계획이다. 5 2019년도에 높은 성장을 하였음에도 불구하고, 유 럽 시장 내의 제한적인 전기차 모델, 일부 지역에서 충 전소가 부족하다는 고객 인식 등으로 아직까지는 전기 차의 전면 도입이 다소 정체되고 있다. 6 COVID-19 발생과 봉쇄 조치에 따른 판매 전시장 폐쇄, 생산 중단 등이 유럽 내 자동차 판매량에 영향을 미쳤지만, 전기차 판매량은 기존 내연기관 차량과 비교 하였을 때 여전히 건재하다. 2020년 1분기 EU 국가 의 신규 승용차 수요는 38.5% 감소하였고, 한달 내내",
        "COVID-19 관련 제한 조치가 시행되었던 2020년 4월 판매량의 경우 전년 대비 76.3% 감소하였으며, 일부 주요 시장에서는 전년 대비 95% 감소한 수치를 나타 냈다. 7 다만 서유럽에서는 2020년 4월 전기차 판매량 이 약 31% 정도만 감소했는데, 일부 국가에서는 낮은 수준이지만 전년 대비 판매량이 증가하기도 하였다. 8 중국 중국은 전체 전기차 판매량의 약 절반을 차지하며 시장 지배력을 유지하고 있다. 다만 중국 내 전기차 보 조금 중 일부가 절반으로 삭감되어 2019년 하반기 판 매량은 예상보다 감소하였다. 9 이로 인해 전기차 수 요가 상당히 위축되었고, 연간 총 판매량이 하락하였 다.(2018년 대비 2019년 판매량 PHEV 9%, BEV 17% 감소 10 ) 한편 내연기관 자동차의 판매 둔화가 실 제로는 중국 내 전기차 시장 점유율의 증가를 나타낸다 는 긍정적 시각도 존재한다. 2 Deloitte analysis: Automotive planning solutions, IHS Markit, https://ihsmarkit.com/index.html; EV-volumes.com:  The electric vehicle world sales database, https://www.ev-volumes.com/, accessed 16 June 2020. 3 \"In 2019, Plug-in electric car sales in Norway increased by 10%\", InsideEVs, https://insideevs.com/  news/391146/2019- plugin-car-sales-norway-increased/, accessed 18 May 2020. 4 \"Petrol and diesel car sales ban brought forward to 2035\", BBC, https://www.bbc.co.uk/news/science-environ-  ment- 51366123, accessed 18 May 2020. 5 \"Climate Action Plan 2050 – Germany's long-term emission development strategy\", Federal Ministry for the  Environment, Nature Conservation and Nuclear Safety, https://www.bmu.de/en/topics/climate-energy/climate/  national-climate- policy/greenhouse-gas-neutral-germany-2050/, accessed 18 May 2020. 6 \"2020 Global Auto Consumer Study\", Deloitte Global, https://www2.deloitte.com/global/en/pages/consum-  er-business/ articles/global-automotive-trends-millennials-consumer-study.html, accessed 1 June 2020. 7 \"Passenger car registrations\", European Automobile Association, https://www.acea.be/press-releases/article/  passenger- car-registrations-38.5-four-months-into-2020-76.3-in-april, accessed 18 May 2020. 8 Matthias Schmidt, \"April 2020 West European electric car market update\", Schmidt Automotive Market Intelli-  gence, https://www.schmidtmatthias.de/post/european-electric-car-sales-april-2020, accessed 1 June 2020. 9 China scales back subsidies for electric cars to spur innovation, Bloomberg, https://www.bloomberg.com/news/ articles/2019-03-26/china-scales-back-subsidies-for-electric-cars-to-spur-innovation, accessed 1 June 2020. 10 Roland Irle, \"Global BEV & PHEV sales for 2019\", EV-Volumes.com, https://www.ev-volumes.com/, accessed 1  June 2020. Deloitte Insights Global Insights 34 2019년 하반기 중국 시장의 성장 둔화가 전세계 전 기차 판매량에 영향을 미쳤으나, COVID-19나 지원",
        "금 감소가 장기적으로 전기차 판매량에 큰 영향을 미칠 것으로 보이지는 않는다. 중국 당국은 2020년에 추가 적으로 지원금을 삭감하지 않을 것이라고 밝혔다. 11 여 전히 인센티브 정책이 존재하며, 중국 내 충전소 설비 투자, 중국 제조업체들에 대한 전기차 생산 및 판매 장 려가 이루어지고 있다. COVID-19 팬데믹과 봉쇄 조치로 중국의 2020년 1분기 승용차 판매량은 45% 감소했다. 12 소비자들이 집에 머무는 시간이 증가하고, 전시장이 문을 닫으면서 전기차 판매량(56% 감소)은 전체 자동차 시장보다 더 빠르게 감소하였다. 13 하지만 중국은 신속한 회복 기조 를 나타내고 있다. 2020년 3월 중국 공장들은 생산률 을 75%까지 회복하였으며, 86%의 생산 인력이 업무 에 복귀하였다. 2020년 4월 생산량은 팬데믹 이전 수 준을 되찾았다. 비록 중국 일부 지역에서는 여전히 판매량이 저조하 지만, 보복 소비 경향 및 중국 정부 당국의 우호적인 정 책 기조, 온라인에서의 자동차 판매로 회복에 가속도 가 붙었다. 이러한 분위기는 4월  전년 동기 대비 성장 률에 고스란히 드러났다. 이는 중국의 V자 반등 가능성 을 시사하는 동시에, 일부 전기차 생산업체는 이미 신 차 출시 효과를 누리고 있는 것으로 해석할 수 있다. 14 미국 2019년 초 미국의 전기차 판매실적은 양호한 모습 이었으나, 타 국가 대비 상대적으로 낮은 자차 유지비와 미국 내 원유 가격 하락으로 당해 연도 하반기에는 전기 차 판매 실적이 부진한 것으로 나타났다.  미국의 전기 차 시장은 전체 판매량의 절반 가량을 차지하는 테슬라 의 모델 3가 독주하는 체제라 볼 수 있다. 15 유럽이나 중국처럼, 미국에서도 팬데믹으로 상당 수가 실직자가 되고, 자택 대기 명령이 발효되면서 수 요가 감소하여 2020년 첫 3개월 간 자동차 판매량이 급감하였다. 전기차 생산업체에서 신차 출시를 연기하 고, 소비자들이 저유가의 혜택을 누리게 되면서 타 주 요 국가와 달리 미국에서의 전기차 판매량 회복은 다소 더딜 것으로 보인다. 기타 국가 유럽, 중국, 미국을 제외한 나머지 국가의 전기차 판 매량은 상당히 저조하다. 이는 전기차에 대한 정부 관",
        ''', lang='english'
        )
    print(result)