from openai import OpenAI
import json

client = OpenAI()

def generate_pareto_choice(choice_a, choice_b, context):
    """
    Generate a Pareto choice using an LLM that combines the essence of two compulsory choices.

    Parameters:
    choice_a (str): The compulsory choice for person X.
    choice_b (str): The compulsory choice for person Y.
    context (str): The context within which to evaluate and generate the Pareto choice.

    Returns:
    str: A new choice that is a wiser version of both choice_a and choice_b.
    """
    prompt = (
        f"Context: {context}\n"
        f"Person X's choice: {choice_a}\n"
        f"Person Y's choice: {choice_b}\n"
        f"Generate a single, unified choice that is wiser than both choices, encapsulating their essence."
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "generate_pareto_choice",
                "description": "Generate a new Pareto choice that is wiser than both input choices.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "unified_choice": {"type": "string"}
                    },
                    "required": ["unified_choice"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    ]

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ],
        tools=tools
    )

    # Safely parse the arguments as JSON if needed
    try:
        arguments = completion.choices[0].message.tool_calls[0].function.arguments
        if isinstance(arguments, str):
            arguments = json.loads(arguments)  # Convert string to dictionary
        return arguments["unified_choice"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        raise ValueError("Unexpected response format or missing data: " + str(e))

def pareto_choices(set1, set2, context):
    """
    This function takes two sets of compulsory choices, generates Pareto choices for each pair using LLMs,
    and returns a list of these Pareto choices.

    Parameters:
    set1 (set): The first set of compulsory choices.
    set2 (set): The second set of compulsory choices.
    context (str): The context within which to evaluate and generate Pareto choices.

    Returns:
    list: A list of Pareto choices.
    """
    if not isinstance(set1, set) or not isinstance(set2, set):
        raise ValueError("Both inputs must be sets.")

    pareto_list = []
    for choice_a in set1:
        for choice_b in set2:
            pareto_choice = generate_pareto_choice(choice_a, choice_b, context)
            pareto_list.append(pareto_choice)

    return pareto_list

# Example usage
if __name__ == "__main__":
    set1 = {"Optimize speed", "Increase safety"}
    set2 = {"Reduce cost", "Enhance user experience"}
    context = "Developing an autonomous vehicle system."

    print("Input Set 1:", set1)
    print("Input Set 2:", set2)
    print("Context:", context)

    try:
        pareto_results = pareto_choices(set1, set2, context)
        print("Pareto Choices:", pareto_results)
    except ValueError as e:
        print("Error generating Pareto choices:", e)

