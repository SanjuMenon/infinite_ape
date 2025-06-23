from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Union, List
from pydantic import ValidationError
import yaml
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import numpy as np
load_dotenv()


class InterventionDistribution(BaseModel):
    """Model for intervention distribution probabilities"""
    probabilities: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping values to their probabilities",
        json_schema_extra={
            "type": "object",
            "properties": {
                "additionalProperties": {"type": "number"}
            }
        }
    )

    @field_validator('probabilities')
    @classmethod
    def validate_probabilities(cls, v):
        """Validate that probabilities sum to 1.0"""
        total = sum(v.values())
        if not abs(total - 1.0) < 1e-6:
            raise ValueError(f"Probabilities must sum to 1.0, got {total}")
        return v

class Intervention(BaseModel):
    """Model for a single intervention"""
    node: str = Field(..., description="Node to intervene on")
    distribution: InterventionDistribution = Field(..., description="Distribution to apply")

    class Config:
        json_schema_extra = {
            "type": "object",
            "properties": {
                "node": {"type": "string"},
                "distribution": {
                    "type": "object",
                    "properties": {
                        "probabilities": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": {"type": "number"}
                        }
                    },
                    "required": ["probabilities"]
                }
            },
            "required": ["node", "distribution"]
        }

class Query(BaseModel):
    """Model for a single query condition"""
    node: str = Field(..., description="Node to query")
    value: Union[str, int, float] = Field(..., description="Value to query for")

    class Config:
        json_schema_extra = {
            "type": "object",
            "properties": {
                "node": {"type": "string"},
                "value": {"type": ["string", "number"]}
            },
            "required": ["node", "value"]
        }

class Input(BaseModel):
    """Model for causal analysis input"""
    interventions: Optional[List[Intervention]] = Field(None, description="List of interventions to apply")
    queries: Optional[List[Query]] = Field(None, description="List of query conditions")

    class Config:
        json_schema_extra = {
            "type": "object",
            "properties": {
                "interventions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "node": {"type": "string"},
                            "distribution": {
                                "type": "object",
                                "properties": {
                                    "probabilities": {
                                        "type": "object",
                                        "additionalProperties": {"type": "number"}
                                    }
                                }
                            }
                        },
                        "required": ["node", "distribution"]
                    }
                },
                "queries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "node": {"type": "string"},
                            "value": {"type": ["string", "number"]}
                        },
                        "required": ["node", "value"]
                    }
                }
            }
        }

class CausalAnalysisInput(BaseModel):
    """Model for causal analysis input"""
    interventions: Optional[List[Intervention]] = Field(None, description="List of interventions to apply")
    queries: Optional[List[Query]] = Field(None, description="List of query conditions")

    
    def to_dict(self) -> Dict:
        """Convert to dictionary format expected by run_causal_analysis"""
        result = {}
        
        if self.interventions:
            result['intervention'] = {
                intervention.node: intervention.distribution.probabilities
                for intervention in self.interventions
            }
            
        if self.queries:
            result['query'] = {
                query.node: query.value
                for query in self.queries
            }
            
        return result

    @classmethod
    def from_yaml(cls, yaml_file: str) -> 'CausalAnalysisInput':
        """Create CausalAnalysisInput from a YAML file"""
        if not os.path.exists(yaml_file):
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")
            
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            
        return cls(**data)

    def to_yaml(self, yaml_file: str):
        """Save CausalAnalysisInput to a YAML file"""
        with open(yaml_file, 'w') as f:
            yaml.dump(self.dict(), f, default_flow_style=False)

    @classmethod
    def split_into_examples(cls, combined_input: Dict) -> List['CausalAnalysisInput']:
        """
        Split a combined input into multiple separate examples.
        
        Args:
            combined_input: Dictionary containing interventions and queries
            
        Returns:
            List of CausalAnalysisInput objects, each representing a different scenario
        """
        examples = []
        
        # Example 1: Just the first intervention
        if 'intervention' in combined_input:
            first_node = next(iter(combined_input['intervention']))
            examples.append(cls(
                interventions=[Intervention(
                    node=first_node,
                    distribution=InterventionDistribution(
                        probabilities=combined_input['intervention'][first_node]
                    )
                )]
            ))
        
        # Example 2: Just the first query
        if 'query' in combined_input:
            first_node = next(iter(combined_input['query']))
            examples.append(cls(
                queries=[Query(
                    node=first_node,
                    value=combined_input['query'][first_node]
                )]
            ))
        
        # Example 3: All interventions
        if 'intervention' in combined_input:
            examples.append(cls(
                interventions=[
                    Intervention(
                        node=node,
                        distribution=InterventionDistribution(
                            probabilities=dist
                        )
                    )
                    for node, dist in combined_input['intervention'].items()
                ]
            ))
        
        # Example 4: All queries
        if 'query' in combined_input:
            examples.append(cls(
                queries=[
                    Query(
                        node=node,
                        value=value
                    )
                    for node, value in combined_input['query'].items()
                ]
            ))
        
        # Example 5: First intervention with first query
        if 'intervention' in combined_input and 'query' in combined_input:
            first_int_node = next(iter(combined_input['intervention']))
            first_query_node = next(iter(combined_input['query']))
            examples.append(cls(
                interventions=[Intervention(
                    node=first_int_node,
                    distribution=InterventionDistribution(
                        probabilities=combined_input['intervention'][first_int_node]
                    )
                )],
                queries=[Query(
                    node=first_query_node,
                    value=combined_input['query'][first_query_node]
                )]
            ))
        
        return examples

    @classmethod
    def generate_from_llm(cls, available_options_file: str, prompt: str) -> List['CausalAnalysisInput']:
        """
        Generate interventions and queries using OpenAI parse method and validate them.
        
        Args:
            available_options_file: Path to YAML file with available options
            prompt: Additional context or instructions for the LLM
            
        Returns:
            List of validated CausalAnalysisInput instances
        """
        # Load available options
        with open(available_options_file, 'r') as f:
            available_options = yaml.safe_load(f)
            
        # Extract target column from filename
        # Format is: student-por_th0_3_G1_available_options.yaml
        target_column = os.path.basename(available_options_file).split('_')[-2]
            
        # Create system prompt
        system_prompt = f"""You are a causal analysis expert. Generate multiple examples of valid interventions and queries based on the available options.
Available options:
{yaml.dump(available_options, default_flow_style=False)}

IMPORTANT: The target column is '{target_column}'. DO NOT include this column in any interventions or queries.

{prompt}

Generate 7-10 different examples that demonstrate:
1. An intervention alone (e.g., changing study habits)
2. A query alone (e.g., checking probability of good grades)
3. A combination of interventions and queries (e.g., how does changing study habits affect grades)
4. Multiple interventions (e.g., changing both study habits and family support)

Each example should follow these rules:
1. All node names and values must exist in the available options
2. For interventions, probabilities must sum to 1.0
3. Use correct data types (strings for categorical, numbers for discretized)
4. Make the examples realistic and meaningful for student performance analysis
5. NEVER use the target column '{target_column}' in any interventions or queries

Format each example as a separate object in the interventions array."""

        # Call OpenAI parse
        client = OpenAI()
        response = client.responses.parse(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate some example interventions and queries."}
            ],
            text_format=cls
        )
        
        # Convert the parsed response to our Pydantic model and split into examples
        combined_input = response.output_parsed
        return cls.split_into_examples(combined_input.to_dict())

def summarize_causal_results(input_example: CausalAnalysisInput, results: dict) -> str:
    """
    Generate a human-readable summary of causal analysis results using an LLM.
    
    Args:
        input_example: The CausalAnalysisInput used for the analysis
        results: The results dictionary from run_causal_analysis
        
    Returns:
        str: A human-readable summary of the results
    """
    client = OpenAI()
    
    # Convert numpy types to Python native types
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {str(k): convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, (np.integer, np.floating)):
            return int(obj) if isinstance(obj, np.integer) else float(obj)
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        return obj
    
    converted_results = convert_numpy_types(results)
    
    summary_prompt = f"""
    Please analyze and summarize the following causal analysis results in plain English:

    Input Scenario:
    {input_example.model_dump_json(indent=2)}

    Results:
    {json.dumps(converted_results, indent=2)}

    Please provide a clear, concise summary that explains:
    1. What intervention or query was performed
    2. What the results mean in terms of the target variable (G1 grade)
    3. Any notable insights or implications
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that explains causal analysis results in clear, understandable language."},
            {"role": "user", "content": summary_prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

# Example usage:
def query_model(options_file, prompt):
    import os
    import re

    def extract_parameters_from_options_file(options_file):
        # Get the filename without path
        filename = os.path.basename(options_file)
        
        # Extract base name (student-por)
        data_file = filename.split('_th')[0]
        
        # Extract model path
        model_path = os.path.dirname(options_file)
        
        # Extract target column using regex to handle underscores
        match = re.match(r'.+_th\d+_\d+_(.+)_available_options\.yaml', filename)
        if match:
            target_column = match.group(1)
        else:
            raise ValueError("Could not extract target column from filename")
        
        # Extract threshold (0.3)
        threshold_match = re.search(r'th(\d+)_(\d+)', filename)
        if threshold_match:
            threshold = float(f"{threshold_match.group(1)}.{threshold_match.group(2)}")
        else:
            raise ValueError("Could not extract threshold from filename")
        
        return {
            'data_file': data_file,
            'model_path': model_path,
            'target_column': target_column,
            'threshold': threshold
        }
    # options_file="saved_models/student-por_th0_3_G1_available_options.yaml"
    params = extract_parameters_from_options_file(options_file)
    print(params)
    try:
        # Generate example inputs
        generated_inputs = CausalAnalysisInput.generate_from_llm(
            available_options_file=options_file,
            prompt=prompt
        )
        print("\nGenerated examples:")
        for i, input_example in enumerate(generated_inputs, 1):
            print(f"\nExample {i}:")
            print(input_example.to_dict())
            
        # Run causal analysis on each example
        print("\nRunning causal analysis on examples...")
        from causal import CausalInferenceModel
        
        # Initialize the model - it will load the existing model
        model = CausalInferenceModel(
            data_file=f'{params["data_file"]}.csv',
            model_path=params['model_path'],
            target_column=params['target_column'],
            threshold=params['threshold'],
            config_file='preprocessing_config.yaml'
        )
        
        # Run each example
        for i, input_example in enumerate(generated_inputs, 1):
            print(f"\nCausal Analysis Results for Example {i}:")
            print("Input:", input_example.to_dict())
            
            # Convert to format expected by run_causal_analysis
            analysis_dict = input_example.to_dict()
            
            # Run the analysis
            results = model.run_causal_analysis(
                intervention=analysis_dict.get('intervention'),
                query=analysis_dict.get('query')
            )
            
            print("Results:", results)
            
            # Generate and print summary
            if results:
                summary = summarize_causal_results(input_example, results)
                yield summary

                
    except ValueError as e:
        print("Error:", e)
    except Exception as e:
        print("Unexpected error:", e)


if __name__ == "__main__":
    # for summary in query_model(options_file="saved_models/student-por_th0_3_G1_available_options.yaml", prompt="Generate an intervention on study habits and a query about academic performance. Make some connections to traveltime as well"):
    #     print("Summary Generated: ", summary)  
    
    for summary in query_model(options_file="saved_models_synthetic\synthetic_dataset_th0_0_Margin_Utilisation_Category_available_options.yaml", prompt="Generate an intervention for currency impacting margin utilisation "):
        print("Summary Generated: ", summary)