import json
from agency_swarm import Agency, Agent
from role_loop.init_agency import init_agency
import os
from role_loop.client import client

def load_threads():
    with open('thread_update.json', 'r') as f:
        return json.load(f)
    
def save_threads(thread):
    with open('thread_update.json', 'w') as f:
        json.dump(thread, f)

def load_settings():
    f = open("hierarchical_settings_update.json", "r")
    return json.loads(f.read())

def save_settings(new_settings):
    with open('hierarchical_settings_update.json', 'w') as f:
        json.dump(new_settings, f)


def agency_to_json(agency: Agency):
    user = [{'name' : 'user', 'description' : None, 'edges' : [agent.name for agent in agency.main_recipients]}]
    agent_nodes = [{'name' : agent.name, 'description': agent.description, 'edges' : list(agency.agents_and_threads[agent.name].keys()) if agent.name in agency.agents_and_threads.keys() else []} for agent in agency.agents]
    nodes = user + agent_nodes
    return json.dumps({'nodes' : nodes}, indent=2)

def json_to_agency(dic: dict):
    connections = []
    nodes_record = dict()
    nodes_name = set()
    for e in dic['nodes']:
        nodes_name.add(e['name'])
        nodes_name.update(e['edges'])
    nodes_name.remove('user')
    for n in nodes_name:
        exec('nodes_record[n] = Agent(name=n)')

    for e in dic['nodes']:
        if e['name'] == 'user':
            entries = [nodes_record[n] for n in e['edges']]
        else:
            connection = [[nodes_record[e['name']], nodes_record[n]] for n in e['edges']]
            connections += connection
    chart = entries + connections

    agency = Agency(chart, 
                threads_callbacks = {
                    "load" : lambda : load_threads(), 
                    "save" : lambda new_threads: save_threads(new_threads)
                }, 
                settings_callbacks = {
                    'load' : lambda: load_settings(), 
                    'save' : lambda new_settings: save_settings(new_settings)
                }, temperature = 0 )
    
    return agency


def assistant_to_json_simple(name):
    with open('config.json', 'r') as f:
        config = json.loads(f.read())

    id = config['create_assistants'][name]['assistant_id']
    assistant = client.beta.assistants.retrieve(id)
    return json.dumps({'name': name, 'description': assistant.description}, indent = 2)

def assistant_to_json_full(name): 
    with open('config.json', 'r') as f:
        config = json.loads(f.read())
    id = config['create_assistants'][name]['assistant_id']
    assistant = client.beta.assistants.retrieve(id)
    assistant.name = name
    return assistant.model_dump()



# assistant = client.beta.assistants.create(

# model = "gpt-4o", 
# temperature=0, 
# response_format={'type': 'json_object'}, 
# description='you are an assigner agent. Your task is to assign a new member into a team structure', 
# instructions = """
# given a team structure representing in json format, and a new member, you should assign the new member into a team structure based on the description of agents and the nature of the task. Yous answer should simply be in json format. 
# Here is the schema:
# {"properties" : 
#     "result": {
#         "type": array, 
#         "items" : {
#         "properties" : {
#             "parent" : {
#                 "type" : "string"
#             }, 
#             "child" : {
#                 "type" : "string"
#             }
#         }
#         }  
#     }
# }
#     the value for "parent" and "child" should be the name of new member or existing member

#     """, 
# )

# task = "compare the revenue between Apple of our company"


new_agent = 'FinancialDataAssistant'

agency = init_agency()


# thread = client.beta.threads.create(

# messages = [{
# "role" : "user", 
# "content" : f"Give a team structure: {agency_to_json(agency)}\n, and a new agent: {assistant_to_json_simple(new_agent)}\n Given the task: {task}\n ASsign the new agent into the team structure so that it can facilite with the task "
# }])

# run = client.beta.threads.runs.create_and_poll(assistant_id=assistant.id, thread_id=thread.id)
# messages = client.beta.threads.messages.list(thread.id)
# last_message = messages.data[0].content[0].text.value
# print(last_message)


# update structure
last_message = """{

  "result" : [
  
     {
        "parent" : "cmo", 
        "child": "FinancialDataAssistant"
     
     }  
  
  ]
}
"""

# update agents config

update_message = json.loads(last_message)['result']
new_agent_settings = assistant_to_json_full(new_agent)

agents_settings_path = 'hierarchical_settings.json'
with open(agents_settings_path, 'r') as f:
    agents_settings = json.load(f)

agents_settings.append(new_agent_settings)
name, ext = os.path.splitext(agents_settings_path)
agents_settings_path = f'{name}_update{ext}'

with open(agents_settings_path, 'w') as f:
    json.dump(agents_settings, f, indent=4)

#create new threads
update_messages = json.loads(last_message)['result']
threads_setting_path = "thread.json"
with open(threads_setting_path, 'r') as f:
    threads_setting = json.load(f)

for d in update_messages:
    parent, child = d['parent'], d['child']
    new_thread = client.beta.threads.create()
    threads_setting[parent][child] = new_thread.id

name, ext = os.path.splitext(threads_setting_path)
threads_setting_path = f'{name}_update{ext}'
with open(threads_setting_path, 'w') as f:
    json.dump(threads_setting, f, indent=4)

#read & update structure
agency_json = json.loads(agency_to_json(agency))
for d in update_messages:
    parent, child= d['parent'], d['child']
    for e in agency_json['nodes']:
        if e['name'] == parent:
            e['edges'].append(child)

agency = json_to_agency(agency_json)

agency.demo_gradio(height=900)