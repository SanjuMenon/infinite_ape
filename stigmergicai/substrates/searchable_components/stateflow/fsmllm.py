from dotenv import load_dotenv

load_dotenv()
#for azure... need more variables in env https://docs.litellm.ai/docs/providers/azure/



from llm_fsm import LLM_FSM



# Create the bot
api = LLM_FSM.from_file("sample.json", model="gpt-4o")

# Start conversation
conv_id, response = api.start_conversation()
print(f"Bot: {response}")

# Have a conversation
while not api.is_conversation_ended(conv_id):
    user_input = input("You: ")
    response = api.converse(user_input, conv_id)
    print(f"Bot: {response}")

# See what data was collected
print(f"\nCollected data: {api.get_data(conv_id)}")