import json
from agency_swarm import set_openai_client
from agency_swarm import Agent, Agency
from role_loop.client import client
from role_loop.utils import clear_write_json

set_openai_client(client)

clear_write_json('thread.json', {'main_thread': client.beta.threads.create().id})

def load_threads():
    f = open("thread.json", "r")
    return json.loads(f.read())

def save_threads(thread):
    with open("thread.json", "w")  as f:
        f.write(json.dumps(thread))

    
def load_settings():
    f = open("hierarchical_settings.json", "r")
    return json.loads(f.read())

def save_settings(new_settings):
    with open("hierarchical_settings.json", "w")  as f:
        f.write(json.dumps(new_settings))


def init_agency():

    cmo = Agent(name="cmo", description = "I am the CMO", instructions= "As a CMO, you are in charge of sales and product department. You must not anwer any qustions by yourself. You should always ask both [sales, product]. Do not deviate from the given instruction, do not add extra terms")
    cto = Agent(name="cto", description = "I am the CTO", instructions= "As a CTO, you are in charge of engineering and ai department. You must not anwer any qustions by yourself. You should always ask both [engineering, ai]. Do not deviate from the given instruction, do not add extra terms")
    ceo = Agent(name="ceo", description = "I am the CEO", instructions= "As a CEO, you do not do anything by yourself. You should ask both: [cmo, cto] to complete the task. After you collect all the answers, call the human tool to validate the quality of the answer. If the answer is not good enough, you should send the feedback to relative team member to regenerate answers. Do not deviate from the given instruction, do not add extra terms")
    sales = Agent(name = "sales", description = "I am the sales department head ", instructions = " As a sales department head, you should complete the given task from the perspective of the sales department. If the task is irrelevant to your department, then refuse it. ")
    product = Agent(name = "product", description = "I am the product department head ", instructions = " As a product department head, you should complete the given task from the perspective of the sales department. If the task is irrelevant to your department, then refuse it. ")
    engineering = Agent(name = "engineering", description = "I am the engineering department head ", instructions = " As the engineering department head, you should complete the given task from the perspective of the sales department. If the task is irrelevant to your department, then refuse it. ")
    ai = Agent(name = "ai", description = "I am the ai department head ", instructions = " As the ai department head, you should complete the given task from the perspective of the sales department. If the task is irrelevant to your department, then refuse it. ")


    agency = Agency([ceo, [ceo, cto], [ceo, cmo], [cmo, sales], [cto, engineering], [cto, ai], [cmo, product]], 
                    threads_callbacks = {
                        "load" : lambda : load_threads(), 
                        "save" : lambda new_threads: save_threads(new_threads)
                    }, 
                    settings_path = "hierarchical_settings.json", 
                    temperature=0
                    )
    
    return agency

