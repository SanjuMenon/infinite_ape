import os
import json
from openai import AzureOpenAI
from inspect import isclass
from searchable_components.tools.predefined_tools import * 

def clear_write_json(path, d):
    """
    clear and write json into file
    """
    if os.path.exists(path):
        os.remove(path)
    with open(path, 'w') as f:
        json.dump(d, f)

def run_and_poll(client: AzureOpenAI, thread_id, assistant_id):
    """
    start the run of a thread until reaching the end of the converastion
    """
    run = client.beta.threads.runs.create_and_poll(
    thread_id = thread_id, 
    assistant_id = assistant_id
    )
    #iterative tool calls
    while True:
        messages = client.beta.threads.messages.list(thread_id)
        last_message = messages.data[0].content[0].text.value
        print(last_message)

        if 'END' in last_message:
            break

        else:
            function_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            for function_call in function_calls:
                action_name = function_call.function.name
                action_args = function_call.function.arguments

                actions ={action_name: action_obj for action_name, action_obj in globals().items() if isclass(action_obj)}
                action_args = json.loads(action_args) if action_args else {}

                print(action_name, action_args)

                action_output = str(actions[action_name](**action_args).run())
                
                print(action_output)

                tool_outputs.append({"tool_call_id": function_call.id, "output" : action_output})
            
            run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id = thread_id, 
                run_id=run.id, 
                tool_outputs=tool_outputs
            )