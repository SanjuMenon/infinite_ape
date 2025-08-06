import openai

def send_plan_request_to_openai(plan_request, model="o1-mini", temperature=0.7, max_tokens=1500):
    """
    Sends a plan request to the OpenAI API using a structured prompt for generating a project plan and modifying the agent-role hierarchy.

    Parameters:
        plan_request (str): The user-provided description of the project or plan.
        model (str): The OpenAI model to use. Default is 'o1'.
        temperature (float): Sampling temperature. Default is 0.7.
        max_tokens (int): Maximum number of tokens to generate. Default is 1500.

    Returns:
        str: The response text from the OpenAI model.
    """
    try:
        # Define the structured prompt
        prompt = f"""
        Below is a **summarized prompt** that encapsulates the entire process of taking a user plan request, generating a detailed plan, modifying the agent-role hierarchy accordingly, and providing a summary of the changes. This prompt is designed to guide a Language Learning Model (LLM) like GPT to perform these tasks effectively while adhering to the established entropy rules.

        ---

        ### **Prompt for Generating a Project Plan and Modifying Agent-Role Hierarchy**

        **Objective:**  
        Given a user’s project request, generate a comprehensive plan to execute the project, modify the existing agent-role hierarchy to accommodate any new requirements, and provide a summary of the changes made to the hierarchy. Ensure that the top levels of the hierarchy remain stable (low entropy) while the lower levels are flexible and adaptable (high entropy) in accordance with Jaynes’s Maximum Entropy Principle.

        ---

        #### **Guidelines:**

        1. **Hierarchy Entropy Rules:**
           - **Top-Level Stability (Low Entropy):**
             - Maintain existing high-level roles without renaming or restructuring unless absolutely necessary.
             - Top-level roles define the core identity and strategic direction of the organization.
           - **Bottom-Level Flexibility (High Entropy):**
             - Define lower-level (leaf) roles broadly to allow for adaptability and multiple responsibilities.
             - Avoid over-specifying roles to enable seamless integration of new tasks and projects.

        2. **Hierarchy Structure:**
           - **Tree-Like Structure:** Ensure the hierarchy remains a branching tree with no single-child supercategories to promote clear distinctions and facilitate role mixing.
           - **Multiple Siblings:** When adding new subcategories, ensure they have multiple siblings to maintain a balanced tree structure.

        3. **Plan Generation:**
           - **Project Identification:** Determine the main category under which the project falls.
           - **Role Assignment:** Assign tasks to existing roles or create new roles at the lowest feasible level if necessary.
           - **Step-by-Step Plan:** Outline detailed steps required to execute the project, assigning each step to the appropriate agent role.

        4. **Change Tracking:**
           - **Summary of Changes:** Clearly note any additions or modifications to the agent-role hierarchy, specifying which subcategories or roles were added and where.

        ---

        #### **Input:**

        A natural language description of the project or plan requested by the user:
        {plan_request}

        ---

        #### **Expected Output:**

        1. **Updated Agent-Role Hierarchy (YAML Format):**
           - Reflect any new subcategories or roles added to accommodate the project.
           - Ensure compliance with entropy rules (low entropy at top, high entropy at bottom).

        2. **Project Plan:**
           - **Project Title:** Brief title of the project.
           - **Description:** Overview of the project objectives and scope.
           - **Steps:** Detailed, step-by-step actions required to execute the project, each assigned to the relevant agent role.

        3. **Summary of Changes:**
           - List of all modifications made to the agent-role hierarchy, including added subcategories and roles.

        ---
        """

        # Send the prompt to the OpenAI API
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            # temperature=temperature,
            # max_tokens=max_tokens
        )

        # Extract and return the response content
        return response.choices[0].message.content
    except Exception as e:
        # Handle errors
        return f"An error occurred: {e}"

# Example usage
if __name__ == "__main__":
    plan_request = "Create a 1-hour documentary video on the topic of diabetes."
    print(send_plan_request_to_openai(plan_request))

