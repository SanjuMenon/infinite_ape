import numpy as np
import io
import pandas as pd

def load_adjacency_matrix(file_path):
    """
    Loads an adjacency matrix from a flat file or virtual file with row and column headers.

    Parameters:
        file_path (str or io.StringIO): Path to the file or virtual file containing the adjacency matrix.

    Returns:
        pd.DataFrame: The adjacency matrix as a pandas DataFrame.
    """
    if isinstance(file_path, io.StringIO):
        return pd.read_csv(file_path, index_col=0)
    return pd.read_csv(file_path, index_col=0)

def dfs(node, visited, adjacency_matrix, component):
    """
    Depth-First Search (DFS) to explore connected components.

    Parameters:
        node (str): Current node.
        visited (set): Set of visited nodes.
        adjacency_matrix (pd.DataFrame): The adjacency matrix as a DataFrame.
        component (list): List to store the current connected component.

    Returns:
        None
    """
    visited.add(node)
    component.append(node)
    for neighbor, weight in adjacency_matrix.loc[node].items():
        if weight > 0 and neighbor not in visited:
            dfs(neighbor, visited, adjacency_matrix, component)

def count_connected_components_in_list(adjacency_matrix, agents):
    """
    Counts the number of connected components in a subset of agents using the adjacency matrix
    and identifies the strongest connected components that overlap with the list in the given order.

    Parameters:
        adjacency_matrix (pd.DataFrame): The adjacency matrix as a DataFrame with positive weights.
        agents (list): List of agent names.

    Returns:
        tuple: Total number of connected components, list of connected components, and strongest ordered overlapping components as a list of lists.
    """
    valid_agents = [agent for agent in agents if agent in adjacency_matrix.index]

    if not valid_agents:
        return 0, [], []

    visited = set()
    components = []

    for agent in valid_agents:
        if agent not in visited:
            component = []
            dfs(agent, visited, adjacency_matrix, component)
            components.append(component)

    # Find the strongest ordered overlapping connected components
    overlapping_components = []
    current_overlap = []
    current_weight = 0

    for i in range(len(agents) - 1):
        if agents[i] in adjacency_matrix.index and agents[i + 1] in adjacency_matrix.index:
            weight = adjacency_matrix.loc[agents[i], agents[i + 1]]
            if weight > 0:
                if not current_overlap:
                    current_overlap.append(agents[i])
                current_overlap.append(agents[i + 1])
                current_weight += weight
            else:
                if current_overlap:
                    overlapping_components.append((current_weight, current_overlap))
                current_overlap = []
                current_weight = 0
        else:
            if current_overlap:
                overlapping_components.append((current_weight, current_overlap))
            current_overlap = []
            current_weight = 0

    # Final check for the last overlap
    if current_overlap:
        overlapping_components.append((current_weight, current_overlap))

    # Sort overlapping components by weight in descending order
    overlapping_components.sort(key=lambda x: x[0], reverse=True)

    # Return only the ordered lists of components
    sorted_overlapping_components = [component[1] for component in overlapping_components]

    return len(components), components, sorted_overlapping_components

# Example of creating a virtual path for a flat file with headers
virtual_file = io.StringIO("""Agent,A,B,C,D,E,F
A,0,2.5,0,0,0,0
B,2.5,0,0,3.1,0,0
C,0,0,0,1.2,4.5,0
D,0,3.1,1.2,0,0,0
E,0,0,4.5,0,0,2.8
F,0,0,0,0,2.8,0
""")

# Load adjacency matrix from the virtual file
adjacency_matrix = load_adjacency_matrix(virtual_file)

# Example usage
agents = ["A", "B", "C", "D", "E", "F"]  # List of agents with weighted connections
num_components, components, strongest_overlaps = count_connected_components_in_list(adjacency_matrix, agents)
print("Total connected components:", num_components)
print("Connected components:", components)
print("Strongest ordered overlapping connected components in list:", strongest_overlaps)

