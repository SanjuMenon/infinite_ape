import numpy as np
import networkx as nx
import pandas as pd
from openai import OpenAI
from scipy.stats import entropy
from pydantic import BaseModel
from tqdm import tqdm

# Initialize OpenAI client
client = OpenAI()

# Define structured response models
class BeliefRefinement(BaseModel):
    refinements: list[str]

class CoherenceScore(BaseModel):
    score: float

class BeliefNetwork:
    """
    In this fragmented telescopic text based active inference model, this translates to:
    
    - The text represents a generative model: The telescopic text has an underlying true structure that no single agent fully observes.
    - Agents act as Bayesian learners: They try to infer the best possible expansions based on their limited observations.
    - Expanding text = active inference: Agents iteratively refine their expansions to reduce uncertainty (free energy) about the meaning and coherence of the text.
    
    User instructions influence the belief expansion process, guiding which beliefs to expand and how they are refined.
    """
    def __init__(self, beliefs, agents, dependencies, user_instructions, num_refinements=3):
        self.client = OpenAI()
        self.beliefs = beliefs
        self.user_instructions = user_instructions
        self.num_refinements = num_refinements
        self.refinements = self.generate_all_refinements()
        self.agents = agents
        self.dependencies = dependencies
        self.graph = self.create_graph()
    
    def generate_refinements(self, belief_id, belief):
        """
        Generate refinements for a given belief while considering user instructions.
        """
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"""
            Refine the given belief in {self.num_refinements} different ways while following these strict rules:
            - You **must** preserve the original sentence structure.
            - You **can** add words but **cannot** remove core elements of the belief.
            - Only **small changes** (word insertions or slight modifications) are allowed.
            - Do **not** completely rewrite the belief.
            - Follow these user instructions: {self.user_instructions}
            
            ## Examples:
            **Initial Belief:** 'User wants a quick response.'
            **Valid Expansions:**
            - 'User wants a quick response from the assistant.'
            - 'User wants a quick and precise response, without unnecessary details.'
            - 'User wants a quick response, preferably in under 10 seconds.'
            
            **Invalid Expansions:**
            - 'A helpful assistant should always be fast.' (Too different from original)
            - 'I believe kindness leads to better communication.' (Completely unrelated)
            - 'People generally expect efficiency and accuracy in their responses.' (Loses original structure)"""}, {"role": "user", "content": belief}],
            response_format=BeliefRefinement
        )
        return completion.choices[0].message.parsed.refinements
    
    def generate_all_refinements(self):
        return {belief_id: self.generate_refinements(belief_id, belief) for belief_id, belief in self.beliefs.items()}
    
    def create_graph(self):
        G = nx.Graph()
        for b1, b2 in self.dependencies:
            G.add_edge(b1, b2)
        return G
    
    def local_free_energy(self, belief_id, refinement, refined_beliefs):
        neighbor_beliefs = [refined_beliefs[neighbor] for neighbor in self.graph.neighbors(belief_id) if neighbor in refined_beliefs]
        
        prompt = f"Evaluate how well the following refinement \"{refinement}\" fits with its neighboring beliefs: {neighbor_beliefs}. Output a numerical coherence score between 0 (poor fit) and 1 (excellent fit)."
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Evaluate belief coherence."},
                      {"role": "user", "content": prompt}],
            response_format=CoherenceScore
        )
        coherence_score = completion.choices[0].message.parsed.score
        
        # Compute KL divergence to measure uncertainty
        p_distribution = np.array([coherence_score, 1 - coherence_score])
        q_distribution = np.array([0.5, 0.5])  # Assume a uniform prior
        kl_div = entropy(p_distribution, q_distribution)
        
        return kl_div
    
    def global_free_energy(self, refined_beliefs):
        overall_coherence_scores = [self.local_free_energy(belief_id, refinement, refined_beliefs) for belief_id, refinement in refined_beliefs.items()]
        return np.mean(overall_coherence_scores)
    
    def refine_beliefs(self, num_iterations):
        self.history = []  # Store belief refinements over time
        self.refined_beliefs = self.beliefs.copy()
        
        for iteration in tqdm(range(num_iterations), desc="Belief Expansion Progress"):
            iteration_history = {}  # Track changes for this iteration
            for agent, beliefs in self.agents.items():
                for belief_id in beliefs:
                    best_refinement = min(self.refinements[belief_id], key=lambda ref: self.local_free_energy(belief_id, ref, self.refined_beliefs))
                    iteration_history[belief_id] = (self.refined_beliefs[belief_id], best_refinement)
                    self.refined_beliefs[belief_id] = best_refinement
        
            # Adjust refinements for global coherence
            self.history.append(iteration_history)
            if self.global_free_energy(self.refined_beliefs) > 0.1:  # Threshold for high uncertainty
                for belief_id in self.refined_beliefs:
                    best_refinement = min(self.refinements[belief_id], key=lambda ref: self.local_free_energy(belief_id, ref, self.refined_beliefs))
                    self.refined_beliefs[belief_id] = best_refinement
        
    def display_refined_beliefs(self):
        print("Belief Expansion History:")
        for iteration, changes in enumerate(self.history):
            print(f"Iteration {iteration + 1}:")
            for belief_id, (old, new) in changes.items():
                print(f"  Belief {belief_id}: '{old}' → '{new}'")
        print("Final Refined Beliefs:")
        for belief_id, text in self.refined_beliefs.items():
            print(f"{belief_id}: {text}")

if __name__ == "__main__":
    beliefs = {
        1: "User wants a quick response.",
        2: "User prefers detailed explanations.",
        3: "User is looking for examples.",
        4: "User values efficiency.",
        5: "User expects accuracy."
    }
    
    agents = {
        "A1": [1, 5],
        "A2": [2, 4],
        "A3": [3]
    }
    
    dependencies = [(1, 3), (2, 4), (3, 5), (4, 5)]
    
    user_instructions = "Ensure that responses align with a friendly and informative tone. Prioritize clarity and avoid excessive technical jargon."
    num_refinements = 5  # Set the number of refinements explicitly
    belief_network = BeliefNetwork(beliefs, agents, dependencies, user_instructions, num_refinements)
    num_iterations = 5  # Specify the number of iterations explicitly
    belief_network.refine_beliefs(num_iterations)
    belief_network.display_refined_beliefs()
    
    # Second refinement phase with different instructions
    second_user_instructions = "Transform responses into highly abstract and metaphorical statements. Prioritize poetic expressions, analogies, and philosophical depth over direct explanations."
    belief_network = BeliefNetwork(belief_network.refined_beliefs, agents, dependencies, second_user_instructions, num_refinements)
    belief_network.refine_beliefs(num_iterations)
    print('Refined Beliefs after Second User Instructions:')
    belief_network.display_refined_beliefs()
