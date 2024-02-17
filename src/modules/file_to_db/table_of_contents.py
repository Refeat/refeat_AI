import re

class Section:
    def __init__(self, title, level, parent=None):
        self.title = title.strip()
        self.level = level
        self.parent = parent
        self.subsection_list = []
        self.information_list = []

    def add_subsection(self, subsection):
        subsection.parent = self
        self.subsection_list.append(subsection)

    def add_information(self, information):
        if isinstance(information, str):
            self.information_list.append(information)
        elif isinstance(information, list):
            self.information_list.extend(information)  # Assuming information is a list
        else:
            raise ValueError("Information must be a string or a list of strings")

    def __repr__(self, level=0):
        # Represent the title and any information
        ret = "\t"*level + repr(self.title) + "\n"
        if self.information_list:
            for info in self.information_list:
                ret += "\t"*(level+1) + "- " + repr(info) + "\n"
        # Recursively represent subsections
        for subsection in self.subsection_list:
            ret += subsection.__repr__(level+1)
        return ret
    
    def get_parent_titles(self, parent_text_list):
        if len(parent_text_list) == 0:
            parent_text_list.append(self.title)
        if self.parent.title != "Document Root":
            parent_text_list.insert(0, self.parent.title)
            self.parent.get_parent_titles(parent_text_list)
        return parent_text_list

class TableOfContents:
    def __init__(self, text):
        self.text = text
        self.root = Section("Document Root", level=0)
        self._parse_text()

    def _parse_text(self):
        lines = self.text.split('\n')
        stack = [self.root]  # Use a stack to keep track of the section hierarchy

        for line in lines:
            if line.startswith('#'):
                level = line.count('#')
                title = line.strip('# ').strip()
                new_section = Section(title, level)

                while stack and stack[-1].level >= level:
                    stack.pop()

                if stack:
                    stack[-1].add_subsection(new_section)

                stack.append(new_section)

    def get_section(self, section_number):
        def _find(section, numbers):
            if not numbers:
                return section
            for i, subsection in enumerate(section.subsection_list, start=1):
                if str(i) == numbers[0]:
                    return _find(subsection, numbers[1:])
            raise ValueError(f"Section {section_number} not found")

        section_number = self.extract_number_from_text_updated(section_number).strip()
        numbers = section_number.split('.')
        return _find(self.root, numbers)
    
    def extract_number_from_text_updated(self, text):
        # 숫자와 소수점을 포함하는 문자열을 저장할 변수를 초기화합니다.
        number_str = ''
        
        # 입력 텍스트를 순회하면서 숫자와 소수점을 찾습니다.
        for char in text:
            if char.isdigit() or char == '.':
                number_str += char
            else:
                # 숫자/소수점 이후의 첫 번째 비숫자 문자를 만나면 반복을 중단합니다.
                break
                
        # 마지막 문자가 소수점인 경우 제거합니다.
        if number_str and number_str[-1] == '.':
            number_str = number_str[:-1]
            
        # 추출된 숫자 문자열을 반환합니다. 문자열이 비어있지 않은 경우만 반환합니다.
        return number_str if number_str else None

    def add_information_to_section(self, section, information):
        section.add_information(information)

    def __repr__(self):
        return repr(self.root)
    
if __name__ == "__main__":
    text = '''# 1. Introduction to Electric Vehicle Market
## 1.1 Growing Interest in Electric Vehicles (EVs) despite COVID-19 Disruptions
## 1.2 Sales of Battery Electric Vehicles (BEVs) and Plug-in Hybrid Electric Vehicles (PHEVs) in 2019
## 1.3 Significant Investments by OEMs in New EV Models and Changing Consumer Behaviors
## 1.4 Adjusting Market Forecasts due to Global Demand and Supply Disruptions
## 1.5 Continued Growth in the EV Market until 2030
## 1.6 Opportunities and Challenges for OEMs
## 1.7 Revisiting Customer Targeting and Strategies
## 1.8 Insights from the UK Automotive Market
## 1.9 Accelerating the Transition to an EV-Centric Future
## 1.10 Sustained Growth of the EV Market and Positive Outlook

# 2. Market Share of Electric Vehicles
## 2.1 Market Share in Europe, China, and Globally
## 2.2 Diminishing Concerns about Charging Infrastructure
## 2.3 Obstacles Expected to Disappear
## 2.4 Factors Contributing to Increasing Sales of Electric Cars
## 2.5 Impact of Government Initiatives post-COVID-19
## 2.6 Consumer Concerns Regarding Battery-Powered Electric Vehicles

# 3. Car Manufacturers' Plans for Electric Vehicles
## 3.1 Plans of Various Car Manufacturers
## 3.2 Increasing Competition in the Electric Car Market
## 3.3 Growth of Electric Vehicle Production in China
## 3.4 Industry Consolidation, Partnerships, and Investments

# 4. Consumer Hesitation and Strategies for OEMs
## 4.1 Consumer Hesitation to Purchase Electric Cars
## 4.2 Strategies to Target Loyal Customers for Electric Car Conversion
## 4.3 Exploring Consumer Priorities and Segmentation'''
    table_of_contents = TableOfContents(text)
    print(table_of_contents)
    print(table_of_contents.get_section('1'))