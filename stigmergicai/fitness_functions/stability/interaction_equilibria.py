import openai
import itertools
import os

from openai import AzureOpenAI, OpenAI
from dotenv import load_dotenv, dotenv_values


client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_API_KEY")
    cd
)


def find_nash_equilibrium(sentences, player1_matrix, player2_matrix, player1_choices, player2_choices):
    """
    Finds the Nash equilibrium based on sentence descriptions of choices, rather than payoffs.
    
    Parameters:
    - sentences: dict with keys as tuples of choices and values as sentences describing each scenario.
    - player1_matrix: 2D list representing the payoff matrix for player 1.
    - player2_matrix: 2D list representing the payoff matrix for player 2.
    - player1_choices: list of choices available to Player 1.
    - player2_choices: list of choices available to Player 2.

    Returns:
    - A list of tuples with each tuple containing the Nash equilibrium sentences.
    """
    
    equilibria = []

    # Iterate over all possible strategies for Player 1 and Player 2
    for i, p1_choice in enumerate(player1_choices):
        for j, p2_choice in enumerate(player2_choices):
            # Payoffs for the current strategy combination
            payoff1 = player1_matrix[i][j]
            payoff2 = player2_matrix[i][j]

            # Determine if it's a Nash equilibrium:
            # Check if Player 1 has no better response
            player1_best_response = max(player1_matrix[i])
            player2_best_response = max(player2_matrix[k][j] for k in range(len(player2_matrix)))

            if payoff1 == player1_best_response and payoff2 == player2_best_response:
                # Add the sentence corresponding to this choice pair as a Nash equilibrium
                equilibria.append(sentences[(p1_choice, p2_choice)])

    return equilibria if equilibria else ["No Nash Equilibrium found."]





def generate_payoff_matrices(sentences, player1_choices, player2_choices):
    """
    Uses OpenAI API to compute payoffs based on sentence descriptions for an n-choice game.

    Parameters:
    - sentences: dict with keys as tuples representing each choice combination (e.g., ("Choice 1", "Choice A"))
                 and values as sentences describing each combination scenario.
                 Example: {
                    ("Choice 1", "Choice A"): "Player 1 chooses Choice 1, Player 2 chooses Choice A.",
                    ("Choice 2", "Choice B"): "Player 1 chooses Choice 2, Player 2 chooses Choice B."
                 }
    - player1_choices: list of choices available to Player 1 (e.g., ["Choice 1", "Choice 2", "Choice 3"])
    - player2_choices: list of choices available to Player 2 (e.g., ["Choice A", "Choice B"])

    Returns:
    - player1_matrix: 2D list representing the payoff matrix for Player 1.
    - player2_matrix: 2D list representing the payoff matrix for Player 2.
    """
    
    # Initialize payoff matrices for dynamic dimensions based on choices
    player1_matrix = [[0] * len(player2_choices) for _ in range(len(player1_choices))]
    player2_matrix = [[0] * len(player2_choices) for _ in range(len(player1_choices))]

    # Generate all possible choice pairs for Player 1 and Player 2
    for i, p1_choice in enumerate(player1_choices):
        for j, p2_choice in enumerate(player2_choices):
            # Retrieve the scenario description for this combination
            description = sentences.get((p1_choice, p2_choice), "")
            if description:
                response = chat_completion = client.chat.completions.create(
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                    f"In the scenario described: '{description}', please provide a payoff "
                                    f"for each player. Represent it as two numbers where higher numbers indicate "
                                    f"better outcomes for each player. Format the answer as: 'Player 1: [number], Player 2: [number]'."
                                ),
                                }
                            ],
                            model="gpt-3.5-turbo",
                            max_tokens=50,
                    temperature=0
                )
                        

                # Parse the LLM response to extract payoffs
                
                text = response.choices[0].message.content.strip()
                print(response)
                try:
                    # Extract numerical values from the response
                    payoff1, payoff2 = map(int, [s.split(": ")[1] for s in text.split(",")])
                except (IndexError, ValueError):
                    # Default to zero if parsing fails
                    payoff1, payoff2 = 0, 0

                # Store the payoffs in the appropriate cells of the matrices
                player1_matrix[i][j] = payoff1
                player2_matrix[i][j] = payoff2

    return player1_matrix, player2_matrix





if __name__ == "__main__":

    # Example usage with sentences and choices
    player1_choices = ["Choice 1", "Choice 2", "Choice 3"]
    player2_choices = ["Choice A", "Choice B", "Choice C"]

    # Example sentences for each possible choice combination
    sentences = {
        ("Choice 1", "Choice A"): "Player 1 chooses Choice 1, and Player 2 chooses Choice A.",
        ("Choice 1", "Choice B"): "Player 1 chooses Choice 1, and Player 2 chooses Choice B.",
        ("Choice 1", "Choice C"): "Player 1 chooses Choice 1, and Player 2 chooses Choice C.",
        ("Choice 2", "Choice A"): "Player 1 chooses Choice 2, and Player 2 chooses Choice A.",
        ("Choice 2", "Choice B"): "Player 1 chooses Choice 2, and Player 2 chooses Choice B.",
        ("Choice 2", "Choice C"): "Player 1 chooses Choice 2, and Player 2 chooses Choice C.",
        ("Choice 3", "Choice A"): "Player 1 chooses Choice 3, and Player 2 chooses Choice A.",
        ("Choice 3", "Choice B"): "Player 1 chooses Choice 3, and Player 2 chooses Choice B.",
        ("Choice 3", "Choice C"): "Player 1 chooses Choice 3, and Player 2 chooses Choice C."
    }

    # Assuming player1_matrix and player2_matrix are already calculated from generate_payoff_matrices
    player1_matrix, player2_matrix = generate_payoff_matrices(sentences, player1_choices, player2_choices)

    # Find Nash Equilibria based on sentences
    nash_equilibria_sentences = find_nash_equilibrium(sentences, player1_matrix, player2_matrix, player1_choices, player2_choices)
    print("Nash Equilibria (as sentences):", nash_equilibria_sentences)

    """
# Example usage with n choices per player
player1_choices = ["Choice 1", "Choice 2", "Choice 3"]
player2_choices = ["Choice A", "Choice B", "Choice C"]

# Define sentences for each possible combination
sentences = {
    ("Choice 1", "Choice A"): "Player 1 chooses Choice 1, Player 2 chooses Choice A.",
    ("Choice 1", "Choice B"): "Player 1 chooses Choice 1, Player 2 chooses Choice B.",
    ("Choice 1", "Choice C"): "Player 1 chooses Choice 1, Player 2 chooses Choice C.",
    ("Choice 2", "Choice A"): "Player 1 chooses Choice 2, Player 2 chooses Choice A.",
    ("Choice 2", "Choice B"): "Player 1 chooses Choice 2, Player 2 chooses Choice B.",
    ("Choice 2", "Choice C"): "Player 1 chooses Choice 2, Player 2 chooses Choice C.",
    ("Choice 3", "Choice A"): "Player 1 chooses Choice 3, Player 2 chooses Choice A.",
    ("Choice 3", "Choice B"): "Player 1 chooses Choice 3, Player 2 chooses Choice B.",
    ("Choice 3", "Choice C"): "Player 1 chooses Choice 3, Player 2 chooses Choice C."
}

# Generate payoff matrices using LLM
player1_matrix, player2_matrix = generate_payoff_matrices(sentences, player1_choices, player2_choices)
print("Player 1 Payoff Matrix:", player1_matrix)
print("Player 2 Payoff Matrix:", player2_matrix)

# Use matrices with find_nash_equilibrium function
nash_equilibria = find_nash_equilibrium(player1_matrix, player2_matrix)
print("Nash Equilibria:", nash_equilibria)
    
    
    """
