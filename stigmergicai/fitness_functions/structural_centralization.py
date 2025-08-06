# Python code to calculate inbound, outbound, and betweenness centralization scores for tree-like organizational structures

import networkx as nx

def calculate_centralization_difference(target_tree_edges, reference_tree_edges, lower_bound, upper_bound):
    """
    Calculate the difference in inbound degree centralization, outbound degree centralization,
    and betweenness centralization between a target tree and a reference tree.

    Args:
        target_tree_edges (list of tuples): List of edges representing the target tree (parent, child).
        reference_tree_edges (list of tuples): List of edges representing the reference tree (parent, child).
        lower_bound (float): Lower bound for the centralization score differences.
        upper_bound (float): Upper bound for the centralization score differences.

    Returns:
        dict: A dictionary containing the differences and whether they exceed the bounds.
    """
    def calculate_centralization_scores(tree_edges):
        """
        Calculate normalized centralization scores for a given tree.
        """
        # Create a directed graph from the input tree edges
        tree = nx.DiGraph(tree_edges)

        # Ensure the input graph is a tree
        if not nx.is_tree(tree):
            raise ValueError("The provided structure is not a tree.")

        # Number of nodes in the tree
        num_nodes = len(tree.nodes)

        # Calculate degree centralizations
        in_degree_centrality = nx.in_degree_centrality(tree)
        out_degree_centrality = nx.out_degree_centrality(tree)

        # Normalize inbound and outbound centralization scores
        max_inbound = max(in_degree_centrality.values(), default=0)
        max_outbound = max(out_degree_centrality.values(), default=0)

        inbound_centralization = sum(in_degree_centrality.values()) / max(1, max_inbound * num_nodes)
        outbound_centralization = sum(out_degree_centrality.values()) / max(1, max_outbound * num_nodes)

        # Calculate betweenness centralization
        betweenness_centrality = nx.betweenness_centrality(tree)
        max_betweenness = max(betweenness_centrality.values(), default=0)
        betweenness_centralization = sum(betweenness_centrality.values()) / max(1, max_betweenness * num_nodes)

        return {
            "inbound_centralization": inbound_centralization,
            "outbound_centralization": outbound_centralization,
            "betweenness_centralization": betweenness_centralization
        }

    # Calculate scores for both trees
    target_scores = calculate_centralization_scores(target_tree_edges)
    reference_scores = calculate_centralization_scores(reference_tree_edges)

    # Compute the differences
    differences = {
        "inbound_centralization_diff": target_scores["inbound_centralization"] - reference_scores["inbound_centralization"],
        "outbound_centralization_diff": target_scores["outbound_centralization"] - reference_scores["outbound_centralization"],
        "betweenness_centralization_diff": target_scores["betweenness_centralization"] - reference_scores["betweenness_centralization"]
    }

    # Check if the differences exceed the bounds
    results = {
        "differences": differences,
        "exceeds_bounds": {
            "inbound_exceeds_bounds": not (lower_bound <= differences["inbound_centralization_diff"] <= upper_bound),
            "outbound_exceeds_bounds": not (lower_bound <= differences["outbound_centralization_diff"] <= upper_bound),
            "betweenness_exceeds_bounds": not (lower_bound <= differences["betweenness_centralization_diff"] <= upper_bound)
        }
    }

    return results

# Example usage
if __name__ == "__main__":
    # Define target and reference trees as lists of edges (parent, child)
    target_tree = [
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("B", "E"),
        ("D", "H"),
        ("C", "F"),
        ("F", "I"),
        ("C", "G"),
        ("G", "J")
    ]

    reference_tree = [
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("C", "E"),
        ("C", "F"),
        ("C", "G")
    ]

    lower_bound = 0.0
    upper_bound = 0.1

    # Calculate centralization score differences and check bounds
    results = calculate_centralization_difference(target_tree, reference_tree, lower_bound, upper_bound)

    # Output the results
    print("Centralization Score Differences and Bounds Check:")
    print(f"Differences: {results['differences']}")
    print(f"Inbound Exceeds Bounds: {results['exceeds_bounds']['inbound_exceeds_bounds']}")
    print(f"Outbound Exceeds Bounds: {results['exceeds_bounds']['outbound_exceeds_bounds']}")
    print(f"Betweenness Exceeds Bounds: {results['exceeds_bounds']['betweenness_exceeds_bounds']}")

