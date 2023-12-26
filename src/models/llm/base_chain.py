import os
import json
from typing import List, Any, Dict

from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))

class BaseChain:
    def __init__(self, 
                 prompt_template:str=None, 
                 prompt_template_path:str=None, 
                 model="gpt-3.5-turbo-1106",
                 verbose=False,
                 streaming=False,
                 temperature=0.0,
                 seed=42,
                 response_format="text") -> None:
        if response_format == "text":
            llm_response_format = {"type":"text"}
        elif response_format == "json":
            llm_response_format = {"type":"json_object"}
        self.prompt = self._get_prompt(prompt_template, prompt_template_path)
        self.llm = ChatOpenAI(model=model, temperature=temperature, streaming=streaming, seed=seed, response_format=llm_response_format)
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=verbose)

    def _get_prompt(self, template, template_path):
        if template_path:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        if not template:
            raise ValueError("Either template or template_path should be provided.")
        return PromptTemplate.from_template(template=template)

    def run(self, callbacks=None, **kwargs):
        input_dict = self.parse_input(**kwargs)
        max_tries = 5
        for _ in range(max_tries):
            try:
                result = self.chain.run(input_dict, callbacks=callbacks)
                return self.parse_output(result)
            except Exception as e:
                print(e)
                continue
        print('Failed to run chain.')
        return None

    async def arun(self, **kwargs):
        input_dict = self.parse_input(**kwargs)
        result = await self.chain.arun(input_dict)
        return self.parse_output(result)

    def parse_input(self, **kwargs):
        return kwargs

    def parse_output(self, output):
        return output.strip()

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

    def _get_prompt(self, system_prompt_template=None, user_prompt_template=None, prompt_template_path=None):
        if not (prompt_template_path or (system_prompt_template and user_prompt_template)):
            raise ValueError("Either prompt_template_path or system_prompt_template, user_prompt_template, input_variables should be provided.")

        if prompt_template_path:
            with open(prompt_template_path, 'r', encoding='utf-8') as f:
                prompt_template = json.load(f)
            system_prompt = prompt_template.get('system_prompt', system_prompt_template)
            user_prompt = prompt_template.get('user_prompt', user_prompt_template)
        else:
            system_prompt = system_prompt_template
            user_prompt = user_prompt_template

        messages = []
        if system_prompt:
            messages.append(('system', system_prompt))
        if user_prompt:
            messages.append(('human', user_prompt))

        return ChatPromptTemplate.from_messages(messages=messages)