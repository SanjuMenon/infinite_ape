def calculate_entropy_changes(fractions, n_before, n_after):
    import math

    # Calculate \(\Delta S_{\text{mixing}}\)
    def calculate_mixing_entropy(fractions):
        total_entropy_mixing = 0
        for unit_fractions in fractions:
            for f in unit_fractions:
                if f > 0:
                    total_entropy_mixing += f * math.log2(f)
        return -total_entropy_mixing

    # Calculate \(\Delta S_{\text{exp/cont}}\)
    def calculate_exp_cont_entropy(n_before, n_after):
        total_entropy_exp_cont = 0
        for n_b, n_a in zip(n_before, n_after):
            if n_b > 0 and n_a > 0:
                total_entropy_exp_cont += math.log2(n_a / n_b)
        return total_entropy_exp_cont

    delta_s_mixing = calculate_mixing_entropy(fractions)
    delta_s_exp_cont = calculate_exp_cont_entropy(n_before, n_after)

    return delta_s_mixing, delta_s_exp_cont

def process_hierarchical_tree(tree):
    """
    Convert a hierarchical tree of agents into inputs for entropy calculations.

    Args:
    - tree: dict, where each key is a unit and the value is a dictionary with:
        'before': Total agents before changes
        'after': Total agents after changes
        'components': dict with component counts after changes

    Returns:
    - fractions: List of lists of component fractions for each unit
    - n_before: List of total agents before changes for each unit
    - n_after: List of total agents after changes for each unit
    """
    fractions = []
    n_before = []
    n_after = []

    for unit, data in tree.items():
        n_before.append(data['before'])
        n_after.append(data['after'])

        # Calculate fractions for the unit
        total_after = data['after']
        unit_fractions = [
            count / total_after for count in data['components'].values()
        ]
        fractions.append(unit_fractions)

    return fractions, n_before, n_after






if __name__ == "__main__":
    # Example hierarchical tree
    tree = {
        "Group1": {
            "before": 10,
            "after": 15,
            "components": {"Decider": 6, "RAG": 9}
        },
        "Group2": {
            "before": 20,
            "after": 25,
            "components": {"Decider": 10, "RAG": 15}
        }
    }
    fractions, n_before, n_after = process_hierarchical_tree(tree)
    print("Fractions:", fractions)
    print("n_before:", n_before)
    print("n_after:", n_after)
        
    # # Example usage:
    # fractions = [
    #     [0.4, 0.6],  # Fractions for the first unit
    #     [0.3, 0.7]   # Fractions for the second unit
    # ]
    # n_before = [10, 20]  # Staff counts before changes
    # n_after = [15, 25]   # Staff counts after changes

    mixing_entropy, exp_cont_entropy = calculate_entropy_changes(fractions, n_before, n_after)
    print(f"\u0394S_mixing: {mixing_entropy}")
    print(f"\u0394S_exp/cont: {exp_cont_entropy}")

    