import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import json
import signal
from typing import List, Any, Dict

from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

from models.errors.llm_error import ChainRunError, run_chain_with_timeout, timeout_handler

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

LIMIT_CHAIN_TIMEOUT = 3
def run_chain_with_timeout(chain, input_dict, callbacks, timeout_duration):
    # signal.signal(signal.SIGALRM, timeout_handler) # UNIX 운영체제에서만 작동함
    # signal.alarm(timeout_duration)

    result = chain.run(input_dict, callbacks=callbacks)
    # signal.alarm(0)
    return result

class BaseChain:
    def __init__(self, 
                 prompt_template:str=None, 
                 prompt_template_path:str=None, 
                 model="gpt-3.5-turbo-1106",
                 verbose=False,
                 streaming=False,
                 temperature=0.0,
                 seed=42,
                 response_format="text",
                 callbacks=None) -> None:
        if response_format == "text":
            llm_response_format = {"type":"text"}
        elif response_format == "json":
            llm_response_format = {"type":"json_object"}
        self.prompt = self._get_prompt(prompt_template, prompt_template_path)
        self.llm = ChatOpenAI(model=model, temperature=temperature, streaming=streaming, seed=seed, response_format=llm_response_format)
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=verbose, callbacks=callbacks)
        self.max_tries = 5

    def _get_prompt(self, template, template_path):
        if template_path:
            file_ext = os.path.splitext(template_path)[1]
            if file_ext == '.txt':
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()
        if not template:
            raise ValueError("Either template or template_path should be provided.")
        return PromptTemplate.from_template(template=template)

    def run(self, callbacks=None, **kwargs):
        input_dict = self.parse_input(**kwargs)
        for _ in range(self.max_tries):
            try:
                result = run_chain_with_timeout(self.chain, input_dict, callbacks, LIMIT_CHAIN_TIMEOUT)
                return self.parse_output(result)
            except Exception as e:
                print(e)
                continue            
        raise ChainRunError(class_name=self.__class__.__name__)

    def parse_input(self, **kwargs):
        return kwargs

    def parse_output(self, output):
        return output.strip()

class BaseToolChain(BaseChain):
    def __init__(self, 
                 prompt_template:str=None, 
                 tool_prompt_template:str=None,
                 prompt_template_path:str=None,
                 model="gpt-3.5-turbo-1106",
                 verbose=False,
                 streaming=False,
                 temperature=0.0,
                 seed=42,
                 response_format="text",
                 callbacks=None,
                 tools=None) -> None:
        if response_format == "text":
            llm_response_format = {"type":"text"}
        elif response_format == "json":
            llm_response_format = {"type":"json_object"}
        self.prompt = self._get_prompt(prompt_template, tool_prompt_template, prompt_template_path, tools)
        self.llm = ChatOpenAI(model=model, temperature=temperature, streaming=streaming, seed=seed, response_format=llm_response_format)
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=verbose, callbacks=callbacks)
        self.max_tries = 5

    def _get_prompt(self, prompt_template, tool_prompt_template, prompt_template_path, tools):
        if not (prompt_template_path or (prompt_template and tool_prompt_template)):
            raise ValueError("Either template_path or prompt_template, tool_prompt_template, should be provided.")
        
        if prompt_template_path:
            file_ext = os.path.splitext(prompt_template_path)[1]
            if file_ext == '.json':
                with open(prompt_template_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
            prompt_template = template.get('prompt', prompt_template)
            tool_prompt_template = template.get('tool_prompt', tool_prompt_template)

        if (not prompt_template) or (not tool_prompt_template):
            raise ValueError("Either template or template_path should be provided.")
        
        tool_template = self._get_tool_prompt(tool_prompt_template, tools)
        prompt_template = prompt_template.format(tool_template=tool_template)
        return PromptTemplate.from_template(template=prompt_template)
    
    def _get_tool_prompt(self, tool_template, tools):
        tool_description_list = []
        for tool in tools:
            tool_description_list.append(f'{tool.name}: {tool.description}')
        tool_description = '\n'.join(tool_description_list)
        tool_template = tool_template.format(tools=tool_description)
        return tool_template

class BaseChatChain(BaseChain):
    def __init__(self, 
                 system_prompt_template:str=None,
                 user_prompt_template:str=None,
                 prompt_template_path:str=None, 
                 model="gpt-3.5-turbo-1106",
                 streaming=False,
                 temperature=0.0,
                 seed=42,
                 response_format="text",
                 verbose=False,) -> None:
        if response_format == "text":
            llm_response_format = {"type":"text"}
        elif response_format == "json":
            llm_response_format = {"type":"json_object"}
        self.prompt = self._get_prompt(system_prompt_template, user_prompt_template, prompt_template_path)
        self.llm = ChatOpenAI(model=model, temperature=temperature, streaming=streaming, seed=seed, response_format=llm_response_format)
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=verbose)
        self.max_tries = 1

    def _get_prompt(self, system_prompt_template=None, user_prompt_template=None, prompt_template_path=None):
        if not (prompt_template_path or (system_prompt_template and user_prompt_template)):
            raise ValueError("Either prompt_template_path or system_prompt_template, user_prompt_template should be provided.")

        if prompt_template_path:
            file_ext = os.path.splitext(prompt_template_path)[1]
            if file_ext == '.json':
                with open(prompt_template_path, 'r', encoding='utf-8') as f:
                    prompt_template = json.load(f)
            system_prompt_template = prompt_template.get('system_prompt', system_prompt_template)
            user_prompt_template = prompt_template.get('user_prompt', user_prompt_template)

        messages = []
        if system_prompt_template:
            messages.append(('system', system_prompt_template))
        messages.append(MessagesPlaceholder(variable_name="chat_history"),)
        if user_prompt_template:
            messages.append(('human', user_prompt_template))

        return ChatPromptTemplate.from_messages(messages=messages)

    def run(self, chat_history=[], callbacks=None, **kwargs):
        input_dict = self.parse_input(chat_history=chat_history, **kwargs)
        for _ in range(self.max_tries):
            try:
                result = run_chain_with_timeout(self.chain, input_dict, callbacks, LIMIT_CHAIN_TIMEOUT)
                return self.parse_output(result)
            except Exception as e:
                print(e)
                continue
        raise ChainRunError(class_name=self.__class__.__name__)
    
    def parse_input(self, chat_history=[], **kwargs):
        chat_history = self.parse_chat_history(chat_history)
        return {'chat_history': chat_history, **kwargs}
    
    def parse_chat_history(self, chat_history):
        parsed_chat_history = []
        for human, assistant in chat_history:
            parsed_chat_history.append(HumanMessage(content=human))
            parsed_chat_history.append(AIMessage(content=assistant))
        return parsed_chat_history
    
class BaseChatToolChain(BaseChatChain):
    def __init__(self, 
                 system_prompt_template:str=None,
                 user_prompt_template:str=None,
                 tool_prompt_template:str=None,
                 prompt_template_path:str=None, 
                 model="gpt-3.5-turbo-1106",
                 streaming=False,
                 temperature=0.0,
                 seed=42,
                 response_format="text",
                 verbose=False,
                 tools=None,) -> None:
        if response_format == "text":
            llm_response_format = {"type":"text"}
        elif response_format == "json":
            llm_response_format = {"type":"json_object"}
        self.prompt = self._get_prompt(system_prompt_template, user_prompt_template, tool_prompt_template, prompt_template_path, tools)
        self.llm = ChatOpenAI(model=model, temperature=temperature, streaming=streaming, seed=seed, response_format=llm_response_format)
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=verbose)
        self.max_tries = 5

    def _get_prompt(self, system_prompt_template=None, user_prompt_template=None, tool_prompt_template=None, prompt_template_path=None, tools=None):
        if not (prompt_template_path or (system_prompt_template and user_prompt_template and tool_prompt_template)):
            raise ValueError("Either prompt_template_path or system_prompt_template, user_prompt_template, input_variables should be provided.")

        if prompt_template_path:
            with open(prompt_template_path, 'r', encoding='utf-8') as f:
                prompt_template = json.load(f)
            system_prompt_template = prompt_template.get('system_prompt', system_prompt_template)
            user_prompt_template = prompt_template.get('user_prompt', user_prompt_template)
            tool_prompt_template = prompt_template.get('tool_prompt', tool_prompt_template)

        messages = []
        tool_template = self._get_tool_prompt(tool_prompt_template, tools)
        if system_prompt_template:
            system_prompt_template = system_prompt_template.format(tool_template=tool_template)
            messages.append(('system', system_prompt_template))
        messages.append(MessagesPlaceholder(variable_name="chat_history"),)
        if user_prompt_template:
            messages.append(('human', user_prompt_template))

        return ChatPromptTemplate.from_messages(messages=messages)
    
    def _get_tool_prompt(self, template, tools):        
        tool_description_list = []
        for tool in tools:
            tool_description_list.append(f'### {tool.name}\n{tool.description}')
        tool_description = '\n'.join(tool_description_list)
        tool_template = template.format(tools=tool_description)
        return tool_template
    
    def run(self, chat_history=[], agent_scratchpad='', callbacks=None, **kwargs):
        input_dict = self.parse_input(chat_history=chat_history, agent_scratchpad=agent_scratchpad, **kwargs)
        for _ in range(self.max_tries):
            try:
                result = run_chain_with_timeout(self.chain, input_dict, callbacks, LIMIT_CHAIN_TIMEOUT)
                return self.parse_output(result)
            except Exception as e:
                print(e)
                continue
        raise ChainRunError(class_name=self.__class__.__name__)
    
    def parse_input(self, chat_history=[], agent_scratchpad='', **kwargs):
        chat_history = self.parse_chat_history(chat_history)
        return {'chat_history': chat_history, 'agent_scratchpad':agent_scratchpad, **kwargs}