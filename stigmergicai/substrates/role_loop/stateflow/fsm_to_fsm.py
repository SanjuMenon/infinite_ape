from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, Any
from llm_fsm import API
from llm_fsm.api import ContextMergeStrategy
from typing import List, Dict, Optional
from pydantic import BaseModel
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    output_guardrail,
)

load_dotenv()
client = OpenAI()



class Transition(BaseModel):
    target_state: str
    description: str
    priority: int


class FSMState(BaseModel):
    id: str
    description: str
    purpose: str
    instructions: str
    required_context_keys: Optional[List[str]] = None
    transitions: List[Transition]


class FSMMetadataCollector(BaseModel):
    name: str
    description: str
    version: str
    persona: str
    initial_state: str
    states: Dict[str, FSMState]

class Meta(BaseModel):
    name: str 
    description : str
    version : str
    persona: str

api = API.from_file("metafsm.json")

conversation_id, response = api.start_conversation()
print(f"Bot: {response}") 

while not api.has_conversation_ended(conversation_id=conversation_id):
    

    # Interact with the bot
    user_name = input("You: ")
    response = api.converse(user_name, conversation_id)
    print(f"Bot: {response}") 

# Check the collected data
collected_data = api.get_data(conversation_id)
print(f"Data collected by bot: {collected_data}") 

print("Conversation ended." if api.has_conversation_ended(conversation_id) else "Conversation ongoing.")
current_context = api.get_data(conversation_id=conversation_id)

# Push the product recommendation FSM onto the stack
specialist_response = api.push_fsm(
    conversation_id,
    "metafsm.json",
    context_to_pass={
        "fsm_name": current_context.get("fsm_name"),
        "fsm_version": current_context.get("fsm_version"),
        "fsm_persona": current_context.get("fsm_persona"),
        "fsm_description": current_context.get("fsm_description"),
    },
    return_context={
        "specialist_session_completed": True,
        "referral_source": "main_customer_service"
    },
    shared_context_keys=["customer_name", "session_id", "final_recommendations"],
    preserve_history=True,
    inherit_context=True
)

print(f"🤖 Product Specialist: {specialist_response}")
print(f"📊 Stack depth after push: {api.get_stack_depth(conversation_id)}")

# Simulate interaction with product specialist
specialist_messages = [
    "I mainly need it for programming in Python and Java, some web development, and general college work like writing papers.",
    "I'd prefer something portable since I'll be carrying it around campus. Battery life is important too.",
    "Those sound great! I think the ThinkPad would be perfect for my needs."
]

for specialist_msg in specialist_messages:
    print(f"\n👤 Customer: {specialist_msg}")
    specialist_resp = api.converse(specialist_msg, conversation_id)
    print(f"🤖 Product Specialist: {specialist_resp}")

    # Check if we've reached the end of specialist conversation
    if api.get_current_state(conversation_id) == "specialist_handoff":
        print("\n�� Product specialist ready to hand back to main service...")

        # Get the context from specialist before popping
        specialist_context = api.get_data(conversation_id)
        print(f"📋 Specialist context: {list(specialist_context.keys())}")

        # Pop back to main FSM with comprehensive context return
        return_response = api.pop_fsm(
            conversation_id,
            context_to_return={
                "product_recommendations_completed": True,
                "recommended_product": "Lenovo ThinkPad E14",
                "specialist_notes": "Customer prefers portable laptop for programming",
                "estimated_price": "$1100",
                "customer_satisfaction": "high"
            },
            merge_strategy=ContextMergeStrategy.UPDATE
        )

        print(f"🤖 Back to Customer Service: {return_response}")
        print(f"📊 Stack depth after pop: {api.get_stack_depth(conversation_id)}")
        break









response = client.responses.parse(
    model="gpt-4o-2024-08-06",
    input=[
        {"role": "system", "content": f'You are a helpful assistant. Your job is to take the input json dump {collected_data} and create an output in the format specified, When unclear use null value'},
        {
            "role": "user",
            "content": "Extract in the format specified.",
        },
    ],
    text_format=Meta,
)
# agent = Agent(
#     name="Assistant",
#     instructions=f"You are a helpful assistant. Your job is to take the input json dump {collected_data} and create an output in the format specified, When unclear use null value",
#     output_type=FSMMetadataCollector,
    
    
# )
# result = Runner.run_sync(agent, input="Create the output in the desired format.")

print(response.output_parsed.model_dump_json())