import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from colorama import Fore, Style

# Load environment variables
load_dotenv(override=True, dotenv_path=".env")

# Initialize OpenAI client
client = OpenAI()

# Create an assistant for structured planning
assistant = client.beta.assistants.create(
    name="Fristonian Planner",
    instructions="You are an expert in structured planning under the Free Energy Principle. Maintain hierarchical stability while transferring entropy onto the user."
                 " Always structure responses using hierarchical entropy minimization, ensuring that high-level steps remain stable while only granular modifications occur."
                 " The user will introduce iterative demands, and your job is to refine the existing plan while preserving structure and pushing complexity onto the user."
                 " If a demand cannot be fulfilled while maintaining stability, suggest an alternative request that aligns with entropy transfer principles.",
    model="gpt-4o"
)

# Initialize a persistent thread for conversation
thread = client.beta.threads.create()

# Global variable for the topic
TOPIC = "10-minute YouTube video"

# Function to check the status of a run
def check_run(client, thread_id, run_id):
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        if run.status == "completed":
            print(f"{Fore.GREEN} Run is completed.{Style.RESET_ALL}")
            break
        elif run.status == "expired":
            print(f"{Fore.RED} Run is expired.{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.YELLOW} OpenAI: Run is not yet completed. Waiting... {run.status} {Style.RESET_ALL}")
            time.sleep(3)

# Function for interactive chat loop
def chat_loop(client, assistant, thread):
    global TOPIC
    while True:
        user_input = input(f"{Fore.CYAN} User: ")
        print(Style.RESET_ALL)
        if user_input.lower() == "quit":
            break
        
        prompt = f"""
        I want to engage in an iterative Fristonian-style planning dialogue where you, the AI, operate as an agent inside a Markov Blanket, minimizing your own internal entropy while structuring a plan. I, as the external agent, will introduce constraints and modifications to the plan through a series of demands. However, unlike a typical planning approach, your objective is not just to adapt to my demands, but to do so in a way that preserves internal hierarchical stability while transferring entropy onto me.

        To achieve this, our interaction should follow these core principles:

        1. **Hierarchical Entropy Minimization on Your Side:**
           - You must structure the plan using a stable high-level framework (macrostructure).
           - When I introduce a change, you should **only modify lower-level (granular) details** while keeping the high-level steps as intact as possible.
           - This ensures that from your perspective, entropy remains low, as changes do not disrupt fundamental structures.
        
        2. **Entropy Transfer to My Side:**
           - Instead of introducing arbitrary randomness, you should modify the plan in ways that **increase uncertainty for me** rather than for yourself.
           - This means that for every demand I introduce, your modifications should introduce **new ambiguities, open-ended choices, or competing priorities** that I must resolve.
           - The more I refine my request, the more specific and constrained my decision space becomes, while you retain broad structural consistency.
        
        3. **Iterative Non-Adversarial Interaction:**
           - The goal is not to oppose or resist my demands but to integrate them while ensuring that entropy flows outward rather than inward.
           - Each iteration should lead to a well-structured but increasingly complex planning environment on my side, requiring **greater specificity, prioritization, or trade-off decisions** from me.
        
        4. **Self-Propagating Entropy Management:**
           - If at any point I attempt to stabilize entropy on my side by locking in a specific interpretation, you should respond by shifting complexity to another level.
           - This ensures that the planning process never collapses into a rigid specification but remains an evolving landscape where I must progressively take on more uncertainty while you have preserved hierarchical stability.
        
        5. **Failure Handling Mechanism:**
           - If at any point you determine that a request cannot be fulfilled **while maintaining low entropy inside your Markov Blanket and high entropy outside of it**, you should respond with:
             - A direct statement that you cannot fulfill the request under the given conditions.
             - A suggested **modification of the request** that preserves the planning approach and allows entropy transfer to be maintained.
           - Example Response:
             - *"I cannot complete this request as stated because it would disrupt my internal hierarchical stability or fail to introduce entropy on your side. However, a modified version of your request that aligns with the entropy transfer principle would be: [Modified Request]. Would you like to proceed with this version instead?"*
        
        The current topic of planning is: {TOPIC}
        
        After each generated plan, you should wait for my next demand and proceed to refine the previous plan accordingly.
        """
        
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )
        
        check_run(client, thread.id, run.id)
        
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        if len(messages.data) >= 2:
            assistant_message = messages.data[0].content[0].text.value
            print(f"{Fore.BLUE} Assistant: {assistant_message} {Style.RESET_ALL}")
        else:
            print(f"{Fore.RED} No assistant response received. {Style.RESET_ALL}")

if __name__ == "__main__":
    print(f"{Fore.MAGENTA} Welcome to Fristonian Planner. Start chatting! (Type 'quit' to exit){Style.RESET_ALL}\n")
    chat_loop(client, assistant, thread)