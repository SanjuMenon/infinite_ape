import numpy as np
from hmmlearn import hmm
import pickle

class LooselyCoupledAgentStates:
    def __init__(self, agent_names):
        self.agent_names = agent_names
        self.n_states = len(agent_names)
        self.model = hmm.MultinomialHMM(n_components=self.n_states, n_iter=100)
        self.model.transmat_ = self._initialize_transition_matrix()

    def _initialize_transition_matrix(self):
        """Initialize a random transition matrix with valid probabilities."""
        matrix = np.random.rand(self.n_states, self.n_states)
        return matrix / matrix.sum(axis=1, keepdims=True)

    def load_model(self, filename):
        with open(filename, 'rb') as f:
            self.model = pickle.load(f)

    def save_model(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.model, f)

    def update_transitions(self, target_agent_chain, base_alpha=0.1, coupling_threshold=0.2):
        """
        Update the transition matrix using a minimal weighted blend of the existing and new matrix.
        The update is more sensitive to larger changes but keeps small updates minimal.
        Loose coupling is enforced by limiting transition updates if the probability is below `coupling_threshold`.
        """
        new_transmat = target_agent_chain.get_transition_matrix()
        if new_transmat.shape[0] <= self.model.transmat_.shape[0]:
            expanded_matrix = np.eye(self.model.transmat_.shape[0])
            expanded_matrix[:new_transmat.shape[0], :new_transmat.shape[1]] = new_transmat
            diff = np.abs(expanded_matrix - self.model.transmat_)
            
            # Apply minimal updates where the transition probability is below the threshold
            loose_coupling_mask = expanded_matrix < coupling_threshold
            dynamic_alpha = base_alpha * (1 + diff)
            dynamic_alpha[loose_coupling_mask] *= 0.5  # Reduce updates for loosely coupled states

            self.model.transmat_ = dynamic_alpha * expanded_matrix + (1 - dynamic_alpha) * self.model.transmat_
        else:
            raise ValueError("Target transition matrix has more states than reference.")

    def display_chain_structure(self, message, structure):
        """Display the Markov chain as a loosely coupled structure."""
        print(message)
        print(structure)

    def display_transition_matrix(self, message, matrix=None):
        """Display the given transition matrix with agent names for clarity."""
        print(message)
        print("\t" + "\t".join(self.agent_names))
        matrix_to_display = matrix if matrix is not None else self.model.transmat_
        for i, row in enumerate(matrix_to_display):
            print(f"{self.agent_names[i]}\t" + "\t".join(map(lambda x: f"{x:.2f}", row)))

class TargetAgentChain:
    def __init__(self, agent_names, structure):
        self.agent_names = agent_names
        self.n_states = len(agent_names)
        self.structure = structure
        self.transition_matrix = np.random.rand(self.n_states, self.n_states)
        self.transition_matrix /= self.transition_matrix.sum(axis=1, keepdims=True)

    def get_transition_matrix(self):
        return self.transition_matrix

    def get_structure(self):
        return self.structure

# Example Usage
if __name__ == "__main__":
    reference_agent_names = ["Agent A", "Agent B", "Agent C", "Agent D", "Agent E", "Agent F", "Agent G", "Agent H"]
    target_agent_names = ["Agent A", "Agent B", "Agent C", "Agent D", "Agent E"]
    reference_structure = "A -> B -> C * D -> E -> F * G -> H"
    target_structure = "A -> B * C -> D -> E"
    
    # Create and save a reference agent state model if it does not exist
    reference_mc = LooselyCoupledAgentStates(reference_agent_names)
    reference_mc.save_model("reference_agent_states.pkl")
    print("Reference agent state Markov model created and saved.")
    
    # Load the reference agent state Markov model
    reference_mc.load_model("reference_agent_states.pkl")
    
    # Display the original transition matrix and chain structure
    reference_mc.display_chain_structure("Original Chain Structure:", reference_structure)
    reference_mc.display_transition_matrix("Original Transition Matrix:")
    
    # Create a target agent state model and update the reference model
    target_mc = TargetAgentChain(target_agent_names, target_structure)
    target_matrix = target_mc.get_transition_matrix()
    
    # Display the target transition matrix before updating
    reference_mc.display_chain_structure("Target Chain Structure:", target_structure)
    reference_mc.display_transition_matrix("Target Transition Matrix:", target_matrix)
    
    # Apply updates
    reference_mc.update_transitions(target_mc, base_alpha=0.1, coupling_threshold=0.2)
    
    # Display the updated transition matrix and chain structure
    reference_mc.display_chain_structure("Updated Chain Structure:", reference_structure)
    reference_mc.display_transition_matrix("Updated Transition Matrix:")
    
    # Save the updated reference agent state Markov model
    reference_mc.save_model("reference_agent_states.pkl")
    print("Updated transition matrix saved.")

