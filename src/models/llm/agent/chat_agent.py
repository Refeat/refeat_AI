import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(3):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

from langchain.agents import Tool
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.tools.render import render_text_description

from langchain import hub
from langchain.chat_models import ChatOpenAI
from langchain.agents.format_scratchpad import format_log_to_messages
from langchain.agents.output_parsers import JSONAgentOutputParser
from langchain_core.messages import HumanMessage, AIMessage

prompt = hub.pull("hwchase17/react-chat-json")
print(prompt)
chat_model = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-1106")

search = GoogleSerperAPIWrapper()
tools = [
    Tool(
        name="Current Search",
        func=search.run,
        description="useful for when you need to ask with search",
    ),
]

prompt = prompt.partial(
    tools=render_text_description(tools),
    tool_names=", ".join([t.name for t in tools]),
)

chat_model_with_stop = chat_model.bind(stop=["\nObservation"])

# We need some extra steering, or the chat model forgets how to respond sometimes
TEMPLATE_TOOL_RESPONSE = """TOOL RESPONSE: 
---------------------
{observation}

USER'S INPUT
--------------------

Okay, so what is the response to my last comment? If using information obtained from the tools you must mention it explicitly without mentioning the tool names - I have forgotten all TOOL RESPONSES! Remember to respond with a markdown code snippet of a json blob with a single action, and NOTHING else - even if you just want to respond to the user. Do NOT respond with anything except a JSON snippet no matter what!"""

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_log_to_messages(
            x["intermediate_steps"], template_tool_response=TEMPLATE_TOOL_RESPONSE
        ),
        "chat_history": lambda x: x["chat_history"],
    }
    | prompt
    | chat_model_with_stop
    | JSONAgentOutputParser()
)

from langchain.agents import AgentExecutor

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
chat_history = [
    HumanMessage(content="hi, i am bob"),
    AIMessage(content="Hello Bob! How can I assist you today?"),
                ]
print(agent_executor.invoke({"input": "Current weather on san francisco", "chat_history":chat_history})["output"])

