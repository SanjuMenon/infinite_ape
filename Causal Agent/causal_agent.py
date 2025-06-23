"""
Counterfactual Question Classification Example for LLM-FSM

This script demonstrates using LLM-FSM to implement a structured conversation
for classifying and understanding counterfactual questions.
"""

import os
from llm_fsm import API
from dotenv import load_dotenv
from llm_fsm.handlers import HandlerTiming
from counterfactual_models import query_model
load_dotenv()

# --------------------------------------------------------------

def generate_causal_response(context):
    """Extract entities from conversation"""
    user_input = context.get("summary", "")
    scenarios = []
    for summary in query_model(options_file="saved_models/student-por_th0_3_G1_available_options.yaml", prompt=user_input):
        print("Summary Generated: ", summary)
        scenarios.append(summary)
    
    return {"scenarios": scenarios}

def main():
    # Get API key from environment or set it directly
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set your OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY=your-api-key-here")
        return

    # Load the FSM definition from the JSON file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fsm_path = os.path.join(current_dir, "form_filling.json")

    try:
        # Create the LLM-FSM instance using the simplified API
        api = API.from_file(
            path=fsm_path,
            model="gpt-4",  # Using GPT-4 for better understanding of causal relationships
            api_key=api_key,
            temperature=0.3  # Lower temperature for more consistent responses
        )

        

        api.register_handler(
            api.create_handler("CausalResponseGenerator")
                .at(HandlerTiming.CONTEXT_UPDATE)
                .when_keys_updated("summary")
                .with_priority(10)
                .do(generate_causal_response)
        )

        # Start a new conversation with an empty message
        conversation_id, response = api.start_conversation()
        print(f"System: {response}")

        # Main conversation loop
        while not api.has_conversation_ended(conversation_id):
            # Get user input
            user_input = input("You: ")

            # Check for manual exit command
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting conversation.")
                break

            # Store the user message in context for logic conditions
            context = api.get_data(conversation_id)
            context["user_message"] = user_input.lower()

            # Process the user input
            try:
                response = api.converse(user_input, conversation_id)
                print(f"System: {response}")

                # Get the current state for debugging (optional)
                current_state = api.get_current_state(conversation_id)

                # Check if we've reached a terminal state
                if api.has_conversation_ended(conversation_id):
                    print("Conversation has ended.")

                    # Display the final classification and variables
                    data = api.get_data(conversation_id)
                    print("\nQuestion Classification Results:")

                    # Filter out system keys and display relevant information
                    classification_data = {
                        k: v for k, v in data.items() 
                        if not k.startswith('_') 
                        and k not in ['user_message']
                        and k in ['user_question', 'question_type', 'target_variable', 'input_variables', 'scenarios']
                    }

                    for key, value in classification_data.items():
                        print(f"- {key.replace('_', ' ').title()}: {value}")

            except Exception as e:
                print(f"Error: {str(e)}")

        # Clean up
        api.end_conversation(conversation_id)

    except FileNotFoundError:
        print(f"Error: Could not find FSM definition at {fsm_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

# --------------------------------------------------------------


if __name__ == "__main__":
    main()