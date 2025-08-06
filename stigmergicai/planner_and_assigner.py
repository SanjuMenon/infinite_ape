from openai import AzureOpenAI
from agency_swarm import set_openai_client
from agency_swarm.tools import BaseTool
from agency_swarm import Agent, Agency
from agency_swarm.threads import Thread
from agency_swarm.user import User
from pydantic import Field, field_validator
from searchable_components.client import client
from enum import Enum
from typing import List, Optional
from agency_swarm.tools import BaseTool
from pydantic import Field


set_openai_client(client)

def create_send_message_tool(agent: Agent, threads: List[Thread], recipient_agents: List[Agent]):
    """
    Creates a SendMessage tool to enable an agent to send messages to specified recipient agents.


    Parameters:
        agent (Agent): The agent who will be sending messages.
        recipient_agents (List[Agent]): A list of recipient agents who can receive messages.

    Returns:
        SendMessage: A SendMessage tool class that is dynamically created and configured for the given agent and its recipient agents. This tool allows the agent to send messages to the specified recipients, facilitating inter-agent communication within the agency.
    """
    recipient_names = [agent.name for agent in recipient_agents]
    recipients = Enum("recipient", {name: name for name in recipient_names})
    agent_descriptions = ""
    for recipient_agent in recipient_agents:
        if not recipient_agent.description:
            continue
        agent_descriptions += recipient_agent.name + ": "
        agent_descriptions += recipient_agent.description + "\n"

    class SendMessage(BaseTool):
        my_primary_instructions: str = Field(...,
                                                description="Please repeat your primary instructions step-by-step, including both completed "
                                                            "and the following next steps that you need to perform. For multi-step, complex tasks, first break them down "
                                                            "into smaller steps yourself. Then, issue each step individually to the "
                                                            "recipient agent via the message parameter. Each identified step should be "
                                                            "sent in separate message. Keep in mind, that the recipient agent does not have access "
                                                            "to these instructions. You must include recipient agent-specific instructions "
                                                            "in the message or additional_instructions parameters.")
        recipient: recipients = Field(..., description=agent_descriptions)
        message: str = Field(...,
                                description="Specify the task required for the recipient agent to complete. Focus on "
                                            "clarifying what the task entails, rather than providing exact "
                                            "instructions.")
        message_files: Optional[List[str]] = Field(default=None,
                                                    description="A list of file ids to be sent as attachments to this message. Only use this if you have the file id that starts with 'file-'.",
                                                    examples=["file-1234", "file-5678"])
        additional_instructions: str = Field(default=None,
                                                description="Any additional instructions or clarifications that you would like to provide to the recipient agent.")
        
        #one_call_at_a_time : bool = True

        @field_validator('recipient')
        def check_recipien(cls, value):
            if value.value not in recipient_names:
                    raise ValueError(f"Recipient {value} is not valid. Valid recipients are: {recipient_names}")
            return value
        
        def run(self):
            recipient = next((r for r in recipient_agents if r.name == self.recipient.value), None)
            thread = threads[recipient.name]
            message = thread.get_completion(message=self.message, 
                                            recipient_agent=recipient, 
                                            message_files=self.message_files, 
                                            event_handler=None,
                                            yield_messages=True,
                                            additional_instructions = self.additional_instructions)
            return message or ""
        
        
        
    SendMessage._caller_agent = agent
    SendMessage.__doc__ = """Use this tool to facilitate direct, synchronous communication between specialized agents within your agency. When you send a message using this tool, you receive a response exclusively from the designated recipient agent. To continue the dialogue, invoke this tool again with the desired recipient agent and your follow-up message. Remember, communication here is synchronous; the recipient agent won't perform any tasks post-response. You are responsible for relaying the recipient agent's responses back to the user, as the user does not have direct access to these replies. Keep engaging with the tool for continuous interaction until the task is fully resolved. Do not send more than 1 message at a time."""

    return SendMessage


planner = Agent(name = "planner", description= "You are a planner. You must not complete the task, instead assign a given task to one or more suitable agents")

sales = Agent(name = "sales", description = "I am the sales department head ", instructions = " As a sales department head, you should complete the given task from the perspective of the sales department. If the task is irrelevant to your department, then refuse it. ")

product = Agent(name = "product", description = "I am the product department head ", instructions = " As a product department head, you should complete the given task from the perspective of the sales department. If the task is irrelevant to your department, then refuse it. ")

engineering = Agent(name = "engineering", description = "I am the engineering department head ", instructions = " As the engineering department head, you should complete the given task from the perspective of the sales department. If the task is irrelevant to your department, then refuse it. ")

ai = Agent(name = "ai", description = "I am the ai department head ", instructions = " As the ai department head, you should complete the given task from the perspective of the sales department. If the task is irrelevant to your department, then refuse it. ")

main_thread = Thread(User(), planner)
teams = [sales, product, engineering, ai]

for agent in teams + [planner]:
     agent.init_oai()

task_description = "generate a statement on how ai and sales department can work together to make profiles for company, less that 50 words"
planner_custom_task_description = f"Given the task: {task_description}\n Choose one or more agents that you think are most suitable to complete the task from the list : {list(map(lambda x : x.name, teams))} , Your answer should only include names of agent"

res = main_thread.get_completion(planner_custom_task_description)

assignees = None
while True:
     try:
          next(res)
     except StopIteration as e:
          print(e.value)
          assignees = [agent for agent in teams if agent.name in e.value]
          break
#create task specific tread & run
    
assert len(assignees) > 0

assigner = Agent(name="assigner", description="I am an assigner", instructions= "As an assigner, I must not answer any questions. Instead ask team members ")

tmp_thread = Thread(planner, assigner)

threads = {r.name : Thread(agent, r) for r in assignees}

#add communicatin tool (e.g., hierarchical)
assigner.add_tool(create_send_message_tool(assigner, threads, assignees))
assigner.init_oai()


res = tmp_thread.get_completion(message=task_description + "You must not answer the question directly, Instead ask team members")

while True:
     try:
          next(res)
     except StopIteration as e:
          print(e.value)
          break
     
print("\n-----------------------END OF PROCESS-----------------------\n")     

for thread in threads.values():
    print(f"\n-----------------------{thread.id} LOG-----------------------\n")
    agent_name = thread.agent.name
    recipient_agent_name = thread.recipient_agent.name

    send = lambda x : print(f"[{agent_name}] -> [{recipient_agent_name}]: {x}")
    receive = lambda x : print(f"[{recipient_agent_name}] -> [{agent_name}]: {x}")

    cur = send
    messages = client.beta.threads.messages.list(thread_id=thread.id).data

    for message in reversed(messages):
        cur(message.content[0].text.value)
        cur = receive if cur.__name__ == 'end' else send

         
