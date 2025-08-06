#from tools.predefined_tools import *
from searchable_components.client import client
from searchable_components.tools.predefined_tools import CallAssistant, CallTool, CreateAssistant, CreateTool
from searchable_components.utils import clear_write_json, run_and_poll


assistant = client.beta.assistants.create(
    model="gpt-4o",
    temperature=0,
    #response_format={'type':'json_object'}, 
    description="You are a helpful assistant, you should awlays call available assistants or tools to help you complete the task. You can also create new assistants and tools based on your needs", 
    instructions=''' You are a helpful assistant, you should always call available assistants or tools to helpu you complete the task. You can also create new assistants or tools to help you complete the task. You can also create new assistants and tools based on on your needs.
    
    Here is the definitions of a tool and assistant:
    tool: useful when you need to do calculation, drawing diagrams, etc. in python
    assistant: useful when you need to search for domain specific information

    When the task is completed, simply answer "END"
    ''', 
    tools = [CreateTool.openai_schema, CreateAssistant.openai_schema, CallAssistant.openai_schema, CallTool.openai_schema]
)

thread = client.beta.threads.create(messages=[
    {
        "role" : "user", 
        "content" : f"search for the annual revenue of Apple from 2010 to 2020, calculate the average for every two consequent years, and draw a diagram "
    }
])

d = {'main_assistant_id' : assistant.id, 'main_thread_id' : thread.id, 'create_assistants' : {}, 'create_tools' : {} }
clear_write_json('config.json', d)

run_and_poll(client, thread_id=thread.id, assistant_id=assistant.id)
