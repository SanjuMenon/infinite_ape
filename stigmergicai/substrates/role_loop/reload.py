import json
from role_loop.utils import run_and_poll
from role_loop.client import client

with open('config.json', 'r') as f:
    config = json.load(f)

assistant = client.beta.assistants.retrieve(config['main_assistant_id'])

thread = client.beta.threads.retrieve(config['main_thread_id'])

assistant_thread_dic = config['create_assistants']

tool_dic = config['create_tools']

client.beta.threads.messages.create(thread_id=thread.id, content="Search for the annual revenue of Apple from 2010 to 2020, calculate the average for every two consequent years, and draw a diagram ", role = 'user')

run_and_poll(client, thread_id=thread.id, assistant_id=assistant.id)
