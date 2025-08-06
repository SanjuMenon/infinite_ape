import itertools
from typing import List, Tuple, Dict
from openai import OpenAI

client = OpenAI()

# Function to create all possible payoff matrices between choices of two players
def create_payoff_matrices(
    choice_sets_1: List[List[str]], 
    choice_sets_2: List[List[str]], 
    calculate_payoff_fn
) -> List[Dict]:
    """
    Create payoff matrices for all pairs of choices between choice sets of two players and calculate Nash equilibria.

    Args:
        choice_sets_1 (List[List[str]]): List of mutually exclusive choice sets for player 1.
        choice_sets_2 (List[List[str]]): List of mutually exclusive choice sets for player 2.
        calculate_payoff_fn (function): A function that uses an LLM to calculate payoff matrices.

    Returns:
        List[Dict]: A list of dictionaries with each containing the matrix, Nash equilibria, and payoffs.
    """
    matrices_results = []

    # Generate all combinations of choice sets from both players
    for choices_1, choices_2 in itertools.product(choice_sets_1, choice_sets_2):
        # Generate all pair combinations of individual choices from the current sets
        response_data = calculate_payoff_fn(choices_1, choices_2)

        # Extract the payoff matrix
        payoff_matrix = response_data.get("payoff_matrix")

        # Format the payoff matrix for better readability
        formatted_matrix = format_payoff_matrix(payoff_matrix)

        # Analyze Nash Equilibria for the generated payoff matrix
        nash_equilibria = find_nash_equilibria_with_choices(formatted_matrix, choices_1, choices_2)

        # Add results for this pair
        matrices_results.append({
            "choice_pair": (choices_1, choices_2),
            "payoff_matrix": formatted_matrix,
            "nash_equilibria": nash_equilibria,
        })

    return matrices_results

# Function to find Nash equilibria in a 2x2 payoff matrix

def find_nash_equilibria_with_choices(
    matrix: List[List[Tuple[int, int]]],
    choices_player_1: List[str],
    choices_player_2: List[str]
) -> List[Dict]:
    """
    Find Nash equilibria in a 2x2 payoff matrix and return them with the associated choices.

    Args:
        matrix (List[List[Tuple[int, int]]]): The payoff matrix where each cell contains a tuple of payoffs.
        choices_player_1 (List[str]): List of Player 1's choices corresponding to rows.
        choices_player_2 (List[str]): List of Player 2's choices corresponding to columns.

    Returns:
        List[Dict]: List of Nash equilibria with choices and indices.
    """
    equilibria = []

    for i, row in enumerate(matrix):
        for j, (p1, p2) in enumerate(row):
            # Check if Player 1's choice is a best response
            if all(p1 >= matrix[alt_i][j][0] for alt_i in range(len(matrix))):
                # Check if Player 2's choice is a best response
                if all(p2 >= matrix[i][alt_j][1] for alt_j in range(len(row))):
                    equilibria.append({
                        "player_1_choice": choices_player_1[i],
                        "player_2_choice": choices_player_2[j],
                        "payoff": (p1, p2),
                        "indices": (i, j)
                    })

    return equilibria

# Function to format the payoff matrix for better readability
def format_payoff_matrix(matrix: List[List[Tuple[int, int]]]) -> List[List[Tuple[int, int]]]:
    """
    Ensure the payoff matrix is well-formatted and consistent.

    Args:
        matrix (List[List[Tuple[int, int]]]): The raw payoff matrix.

    Returns:
        List[List[Tuple[int, int]]]: A formatted payoff matrix.
    """
    formatted = []
    for row in matrix:
        formatted_row = []
        for cell in row:
            if isinstance(cell, list) and len(cell) == 2:
                formatted_row.append(tuple(cell))
            elif isinstance(cell, tuple) and len(cell) == 2:
                formatted_row.append(cell)
            else:
                raise ValueError(f"Invalid cell format: {cell}. Each cell must be a tuple of two integers.")
        formatted.append(formatted_row)
    return formatted

# Function to simulate LLM-based payoff matrix calculation using function calling
def calculate_payoff_matrix(choices_player_1: List[str], choices_player_2: List[str]) -> Dict:
    """
    Use an LLM to generate a payoff matrix for a pair of choice sets via function calling.

    Args:
        choices_player_1 (List[str]): List of choices for Player 1.
        choices_player_2 (List[str]): List of choices for Player 2.

    Returns:
        Dict: A response containing the payoff matrix and other metadata.
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generate_payoff_matrix",
                "description": (
                    "Generate a 2x2 payoff matrix for two players' choices. Each cell must contain a tuple of two integers "
                    "representing the payoffs for Player 1 and Player 2. Return the matrix as [[(1, 2), (3, 4)], [(5, 6), (7, 8)]]."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "choices_player_1": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "The list of choices made by Player 1."
                        },
                        "choices_player_2": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "The list of choices made by Player 2."
                        },
                        "payoff_matrix": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "integer"
                                    },
                                    "description": "A tuple of two integers representing the payoffs for Player 1 and Player 2."
                                },
                                "description": "A row in the payoff matrix."
                            },
                            "description": "A 2x2 payoff matrix for the choices of the players."
                        }
                    },
                    "required": ["choices_player_1", "choices_player_2", "payoff_matrix"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    ]

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Player 1 has choices {choices_player_1} and Player 2 has choices {choices_player_2}. "
                    "Generate a 2x2 payoff matrix where each cell contains a tuple of two integers representing the payoffs for "
                    "Player 1 and Player 2, such as [[(1, 2), (3, 4)], [(5, 6), (7, 8)]]."
                )
            }
        ],
        tools=tools
    )

    # Extract the generated response
    tool_calls = completion.choices[0].message.tool_calls

    # Debugging: Print tool calls to check the structure
    print("DEBUG: Tool calls response:", tool_calls)

    if not tool_calls:
        print("DEBUG: Full completion response:", completion)
        raise ValueError("No tool calls were returned by the API. Ensure the function call is correctly configured.")

    function_response = tool_calls[0].function.arguments
    if not function_response:
        raise ValueError("No arguments were returned by the tool call.")

    # Parse the response into a dictionary
    response_data = eval(function_response)

    # Debugging: Log the full response data
    print("DEBUG: Full response data:", response_data)

    return response_data

def analyze_nash_equilibria(player_1_choice_sets: List[List[str]], player_2_choice_sets: List[List[str]]) -> List[Dict]:
    """
    Analyze Nash equilibria for given choice sets of two players.

    Args:
        player_1_choice_sets (List[List[str]]): List of Player 1's choice sets.
        player_2_choice_sets (List[List[str]]): List of Player 2's choice sets.

    Returns:
        List[Dict]: List of Nash equilibria with choices and payoffs.
    """
    results = create_payoff_matrices(player_1_choice_sets, player_2_choice_sets, calculate_payoff_matrix)
    all_equilibria = []
    for result in results:
        all_equilibria.extend(result["nash_equilibria"])
    return all_equilibria

# Example usage
if __name__ == "__main__":
    player_1_choice_sets = [["Attack", "Defend"], ["Invest", "Save"]]
    player_2_choice_sets = [["Counter", "Withdraw"], ["Expand", "Conserve"]]

    equilibria = analyze_nash_equilibria(player_1_choice_sets, player_2_choice_sets)
    for eq in equilibria:
        print(eq)
