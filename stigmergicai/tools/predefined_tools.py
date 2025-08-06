import json
from searchable_components.tools.BaseTool import BaseTool
from pydantic import Field
from searchable_components.client import client
from typing import Any
import re


class CallAssistant(BaseTool):
    """
    Useful when you want to call a created tool
    """

    name : str = Field(description="the name of the assistant to be called", title='name')
    query : str = Field(description="query to the assistant", title='query')


    def run(self, **kwargs):
        with open('config.json', 'r') as f:
            config = json.load(f)

        assistant_id, thread_id = config['create_assistants'][self.name]['assistant_id'], config['create_assistants'][self.name]['thread_id']
        client.beta.threads.messages.create(thread_id=thread_id, content=self.query, role='user')
        client.beta.threads.runs.create_and_poll(

            thread_id=thread_id,
            assistant_id=assistant_id
        )
        last_message = client.beta.threads.messages.list(thread_id).data[0].content[0].text.value
        return last_message


class CallTool(BaseTool):
    """
    Useful when you want to call a created tool
    """

    name : str = Field(description="the name of the tool to be called", title='name')
    argument : Any = Field(description="input argument to the tool", title='argument')

    def optional_aval(self, x):
        try:
            return eval(x)
        except:
            return x
        
    
    def run(self, **kwargs):
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        exec(config['create_tools'][self.name], globals())

        argument_dic = {'argument': self.optional_aval(self.argument)}
        print(self.name, argument_dic)

        result = globals()[self.name](**argument_dic).run()
        return str(result) if result is not None else f'the tool {self.name} has been successfully executed'
    

class CreateAssistant(BaseTool):
    """
    Useful when you want to create a new assistant
    """
    name : str = Field(description='name of the assitant to be created', title='name')
    description : str = Field(description='description of the assistant to be created', title='description')

    def run(self, **kwargs):
        assistant = client.beta.assistants.create(
            model = "gpt-4o",
            name = self.name,
            description = self.description,
        )
        thread = client.beta.threads.create()
        with open('config.json', 'r') as f:
            config = json.load(f)

        config['create_assistants'][self.name] = {'assistant_id' : assistant.id, 'thread_id' : thread.id}
        with open('config.json', 'w') as f:
            json.dump(config, f)

        return f"the assistant '{self.name}' has been created. You can use call_assitant to call it now!"
    

class CreateTool(BaseTool):
    """
    Useful when you want to create a new tool
    """

    code : str = Field(description="""a piece of python code to create a tool class following the below example format. It should have only one field called 'argument', and a 'run' function. It should be general enough for future resuse:\nclass DummyTool(BaseTool):\n    \"\"\"Docstring for the DummyTool class\"\"\"\"\n   argument : dict = Field(description='custom description of the input', title='argument') \n\n   def run(self, **kwargs):\n       # A run function where the main execution happens. You can use self.argument directly. """, title='code')

     
    def run(self, **kwargs):
        # exec(code, globals())
        pattern = re.findall(r'class\s+\w+\(', self.code)[0]
        name = pattern[6:-1]
        with open('config.json', 'r') as f:
            config = json.load(f)
        config['create_tools'][name] = self.code.strip()

        with open('config.json', 'w') as f:
            json.dump(config, f)

        return f"the tool '{name}' has been created. You can use call_tool to call it now!"
    
