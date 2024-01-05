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

from models.llm.base_chain import BaseChatToolChain
from models.llm.templates.custom_qna_agent_template import SYSTEM, USER, TOOLS, TOOLS_RESPONSE, TOOL_RESPONSE_SUFFIX
from models.tools import DBSearchTool
from models.llm.chain import DBToolQueryGeneratorChain

class CustomChatAgent:
    def __init__(self,  
                 streaming=False,
                 verbose=False,
                 tools=None):
        self.tools = tools
        self.tool_dict = self.create_tool_dict(tools)
        system_prompt_template:str=SYSTEM
        user_prompt_template:str=USER
        tool_prompt_template:str=TOOLS
        response_format="json"
        self.llm = BaseChatToolChain(
            system_prompt_template=system_prompt_template,
            user_prompt_template=user_prompt_template,
            tool_prompt_template=tool_prompt_template,
            streaming=streaming,
            response_format=response_format,
            verbose=verbose,
            temperature=0.7,
            tools=tools,
        )
        self.max_iterations = 5
        self.db_tool_query_generator = DBToolQueryGeneratorChain(verbose=verbose)

    def run(self, query, database_filename='', chat_history: list=[], callbacks=None):
        iter_count = 0
        history_list = []
        action_input = self.db_tool_query_generator.run(query=query)
        dummy_llm_result = f'```json\n    "action": "Database Search",\n    "action_input": "{action_input["query"]}"\n```'
        tool_result = self.execute_tool('Database Search', action_input["query"])
        history_list.append([dummy_llm_result, tool_result])
        while iter_count < self.max_iterations:
            agent_scratchpad = self.get_agent_scratchpad(history_list)
            llm_result = self.llm.run(input=query, database_filename=database_filename, chat_history=chat_history, agent_scratchpad=agent_scratchpad, callbacks=callbacks)
            print(llm_result)
            action, action_input = self.parse_output(llm_result)
            if action == 'Final Answer':
                return action_input
            else:
                tool_result = self.execute_tool(action, action_input)
            history_list.append([llm_result, tool_result])
    
    def onestep_run(self, query, chat_history: list=[], agent_scratchpad=''):
        result = self.llm.run(input=query, chat_history=chat_history, agent_scratchpad=agent_scratchpad)
        return self.parse_output(result)
    
    def get_agent_scratchpad(self, history_list):
        agent_scratchpad = ''
        for llm_result, tool_result in history_list:
            agent_scratchpad += TOOLS_RESPONSE.format(llm_result=llm_result, tool_result=tool_result)
        agent_scratchpad += TOOL_RESPONSE_SUFFIX
        return agent_scratchpad
    
    def parse_output(self, result):
        result = ast.literal_eval(result)
        return result['action'], result['action_input']
    
    def execute_tool(self, tool_name, tool_input):
        if tool_name in self.tool_dict:
            return self.tool_dict[tool_name].run(tool_input)

    def create_tool_dict(self, tools):
        return {tool.name: tool for tool in tools}

# example usage
# python custom_chat_agent.py --query "전기차 2020년부터 2022년 시장 규모"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, default='Use Database Search to find the market size of the electric vehicle industry for the year 2021.')
    args = parser.parse_args()
    
    tools = [DBSearchTool()]
    chat_agent = CustomChatAgent(tools=tools, verbose=True)

    result = chat_agent.run(args.query)
    print(f'chat result: {result}')
    