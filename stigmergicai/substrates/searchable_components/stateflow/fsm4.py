from dotenv import load_dotenv
from llm_fsm import API
import os
load_dotenv()
# Ensure your API key is set via environment variable or .env file
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not found. Please set it in your environment or .env file.")
    exit()

# Initialize the API with your FSM definition
# (Assumes my_first_bot.json and .env are in the same directory)
api = API.from_file("fsm.json") # Model and API key are picked from .env

# Start the conversation
conversation_id, response = api.start_conversation()
print(f"Bot: {response}") 

# Interact with the bot
user_name = input("You: ")
response = api.converse(user_name, conversation_id)
print(f"Bot: {response}") 

# Check the collected data
collected_data = api.get_data(conversation_id)
print(f"Data collected by bot: {collected_data}") 

print("Conversation ended." if api.has_conversation_ended(conversation_id) else "Conversation ongoing.")