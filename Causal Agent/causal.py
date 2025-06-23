import warnings
import pandas as pd
import numpy as np
from causalnex.structure import StructureModel
from causalnex.plots import plot_structure, NODE_STYLE, EDGE_STYLE
from causalnex.structure.notears import from_pandas
from causalnex.network import BayesianNetwork
from causalnex.discretiser import Discretiser
from causalnex.inference import InferenceEngine
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import networkx as nx
import pickle
import os
import yaml
from pathlib import Path

warnings.filterwarnings("ignore")  # silence warnings

class CausalInferenceModel:
    def __init__(self, data_file, model_path, target_column, threshold=0.3, config_file=None):
        """
        Initialize the Causal Inference Model
        
        Args:
            data_file (str): Path to the input data file
            model_path (str): Path where the model should be saved/loaded from
            target_column (str): The target variable to predict
            threshold (float): Threshold for edge removal in structure learning
            config_file (str, optional): Path to YAML configuration file for preprocessing
        """
        self.data_file = data_file
        self.model_path = model_path
        self.target_column = target_column
        self.threshold = threshold
        self.config_file = config_file
        
        # Create model name from data file name, threshold, and target variable
        data_file_name = os.path.splitext(os.path.basename(data_file))[0]
        # Replace dot in threshold with underscore for safe file naming
        safe_threshold = str(threshold).replace('.', '_')
        self.model_name = f"{data_file_name}_th{safe_threshold}_{target_column}"
        self.full_model_path = os.path.join(model_path, self.model_name)
        
        # Initialize model components as None
        self._model = None
        self.label_encoders = {}  # Initialize label_encoders as empty dict
        
    @property
    def model(self):
        """Get the current model instance"""
        return self._model
        
    @model.setter
    def model(self, value):
        """Set the current model instance"""
        self._model = value
        # Update related attributes
        if value is not None:
            self.sm = value.sm
            self.bn = value.bn
            self.ie = value.ie
            self.discretised_data = value.discretised_data
            self.label_encoders = value.label_encoders
        else:
            self.sm = None
            self.bn = None
            self.ie = None
            self.discretised_data = None
            self.label_encoders = {}

    def _load_config(self):
        """Load preprocessing configuration from YAML file or return defaults"""
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        return None

    def _get_categorical_mappings(self, data):
        """Get categorical variable mappings based on data values or config file"""
        config = self._load_config()
        if config and 'categorical_mappings' in config:
            return config['categorical_mappings']
            
        return {
            'failures': {
                v: 'no-failure' if v == 0 else 'have-failure' 
                for v in data['failures'].unique()
            },
            'studytime': {
                v: 'short-studytime' if v in [1,2] else 'long-studytime'
                for v in data['studytime'].unique()
            }
        }
    
    def _get_discretize_params(self):
        """Get discretization parameters from config file or defaults"""
        config = self._load_config()
        if config and 'discretize_params' in config:
            return config['discretize_params']
        
        # For synthetic dataset, no discretization needed
        if 'synthetic_dataset' in self.data_file:
            return {}
            
        # Default for student dataset
        return {
            'absences': {'split_points': [1, 10]},
            'G1': {'split_points': [10]},
            'G2': {'split_points': [10]},
            'G3': {'split_points': [10]}
        }
        
    def _get_drop_columns(self):
        """Get columns to drop from config file or defaults"""
        config = self._load_config()
        if config and 'drop_columns' in config:
            return config['drop_columns']
        
        # For synthetic dataset, don't drop any columns
        if 'synthetic_dataset' in self.data_file:
            return []
            
        # Default for student dataset
        return ['school', 'sex', 'age', 'Mjob', 'Fjob', 'reason', 'guardian']

    def _get_tabu_edges(self):
        """Get tabu edges from config file or defaults"""
        config = self._load_config()
        if config and 'tabu_edges' in config:
            return config['tabu_edges']
        
        # For synthetic dataset, no tabu edges defined
        if 'synthetic_dataset' in self.data_file:
            return []
            
        # Default for student dataset
        return [("higher", "Medu")]

    def preprocess_data(self, data, drop_columns=None, discretize_columns=None, categorical_mappings=None):
        """
        Preprocess the input data by handling categorical variables and discretizing numeric columns
        
        Args:
            data (pd.DataFrame): Input dataframe
            drop_columns (list): List of columns to drop
            discretize_columns (dict): Dictionary of columns and their discretization parameters
            categorical_mappings (dict): Dictionary of columns and their value mappings
        """
        if self.target_column not in data.columns:
            raise ValueError(f"Target column '{self.target_column}' not found in data")
            
        if drop_columns:
            if self.target_column in drop_columns:
                raise ValueError(f"Cannot drop target column '{self.target_column}'")
            data = data.drop(columns=drop_columns)
            
        # Apply custom categorical mappings first
        if categorical_mappings:
            for col, mapping in categorical_mappings.items():
                if col in data.columns:
                    data[col] = data[col].astype(str).str.strip()
                    data[col] = data[col].map(mapping).fillna(data[col])
                    print(f"After mapping {col}: {data[col].unique()}")
        
        # Now label encode all non-numeric columns
        non_numeric_columns = list(data.select_dtypes(exclude=[np.number]).columns)
        for col in non_numeric_columns:
            le = LabelEncoder()
            data[col] = le.fit_transform(data[col])
            self.label_encoders[col] = le
        
        # Discretize specified columns
        if discretize_columns:
            for col, params in discretize_columns.items():
                if col in data.columns:
                    data[col] = Discretiser(
                        method=params.get('method', 'fixed'),
                        numeric_split_points=params.get('split_points', [])
                    ).transform(data[col].values)
        
        # Ensure all columns are numeric
        for col in data.columns:
            if not np.issubdtype(data[col].dtype, np.number):
                raise ValueError(f"Column '{col}' is not numeric after preprocessing")
        
        # Check for any NaN or infinite values
        if data.isna().any().any():
            raise ValueError("Data contains NaN values after preprocessing")
        if np.isinf(data.values).any():
            raise ValueError("Data contains infinite values after preprocessing")
        
        # Ensure all values are non-negative
        if (data < 0).any().any():
            raise ValueError("Data contains negative values after preprocessing")
        
        # Ensure all columns have at least 2 unique values
        for col in data.columns:
            if len(data[col].unique()) < 2:
                raise ValueError(f"Column '{col}' has less than 2 unique values after preprocessing")
        
        self.discretised_data = data
        return data
    
    def _remove_cycles(self, data):
        """
        Remove cycles from the structure model by removing the weakest edge in each cycle
        
        Args:
            data (pd.DataFrame): The data used to compute edge strengths
        """
        while True:
            # Find all cycles
            try:
                cycle = nx.find_cycle(self.sm, orientation='original')
            except nx.NetworkXNoCycle:
                # No cycles found, we're done
                break
                
            # Find the weakest edge in the cycle
            weakest_edge = None
            min_correlation = float('inf')
            
            for edge in cycle:
                # Get the correlation between the nodes
                # edge[0] is the source, edge[1] is the target
                corr = abs(data[edge[0]].corr(data[edge[1]]))
                if corr < min_correlation:
                    min_correlation = corr
                    weakest_edge = (edge[0], edge[1])  # Store as tuple of (source, target)
                    
            # Remove the weakest edge
            if weakest_edge:
                self.sm.remove_edge(weakest_edge[0], weakest_edge[1])
                
    def learn_structure(self, data, tabu_edges=None):
        """
        Learn the causal structure from data
        
        Args:
            data (pd.DataFrame): Preprocessed data
            tabu_edges (list): List of edges to forbid in structure learning
        """
        if self.target_column not in data.columns:
            raise ValueError(f"Target column '{self.target_column}' not found in data")
            
        # Learn initial structure
        self.sm = from_pandas(data, tabu_edges=tabu_edges, w_threshold=self.threshold)
        
        # First try using the largest subgraph
        largest_component = self.sm.get_largest_subgraph()
        if self.target_column in largest_component.nodes():
            self.sm = largest_component
        else:
            # If target not in largest component, find the component containing target
            components = list(nx.connected_components(self.sm.to_undirected()))
            target_component = None
            for component in components:
                if self.target_column in component:
                    target_component = component
                    break
                    
            if target_component is None:
                raise ValueError(f"Target column '{self.target_column}' is isolated in the graph")
                
            # Create new structure model with target component and its edges
            new_sm = StructureModel()
            for edge in self.sm.edges():
                if edge[0] in target_component and edge[1] in target_component:
                    new_sm.add_edge(edge[0], edge[1])
                    
            # Ensure target has at least one incoming edge
            if not any(edge[1] == self.target_column for edge in new_sm.edges()):
                # Find strongest predictor for target
                target_correlations = data.corr()[self.target_column].abs()
                target_correlations = target_correlations.drop(self.target_column)
                if not target_correlations.empty:
                    strongest_predictor = target_correlations.idxmax()
                    new_sm.add_edge(strongest_predictor, self.target_column)
                    
            self.sm = new_sm
            
        # Remove any cycles from the structure
        self._remove_cycles(data)
        
        return self.sm
    
    def fit_model(self, train_size=0.9, random_state=7):
        """
        Fit the Bayesian Network model
        
        Args:
            train_size (float): Proportion of data to use for training
            random_state (int): Random seed for reproducibility
        """
        if self.discretised_data is None:
            raise ValueError("Data must be preprocessed before fitting the model")
            
        if self.sm is None:
            raise ValueError("Structure must be learned before fitting the model")
            
        if self.target_column not in self.sm.nodes():
            raise ValueError(f"Target column '{self.target_column}' not found in structure model")
            
        # Print debugging information
        print("Structure model nodes:", self.sm.nodes())
        print("Structure model edges:", self.sm.edges())
        print("\nData info:")
        print(self.discretised_data.info())
        print("\nData sample:")
        print(self.discretised_data.head())
        print("\nUnique values per column:")
        for col in self.discretised_data.columns:
            print(f"{col}: {self.discretised_data[col].unique()}")
            
        # Ensure data only contains columns in the structure model
        data = self.discretised_data[list(self.sm.nodes())].copy()
        
        # Split data
        train, test = train_test_split(
            data, 
            train_size=train_size, 
            test_size=1-train_size, 
            random_state=random_state
        )
        
        # Initialize and fit Bayesian Network
        self.bn = BayesianNetwork(self.sm)
        
        # Fit node states first
        print("\nFitting node states...")
        self.bn = self.bn.fit_node_states(data)
        
        # Fit CPDs
        print("\nFitting CPDs...")
        self.bn = self.bn.fit_cpds(train, method="BayesianEstimator", bayes_prior="K2")
        
        # Initialize inference engine
        self.ie = InferenceEngine(self.bn)
        
        return self.bn
    
    def predict(self, data, target_column=None):
        """
        Make predictions using the fitted model
        
        Args:
            data (pd.DataFrame): Data to make predictions on
            target_column (str, optional): Column to predict. If None, uses the target_column from initialization
        """
        if self.bn is None:
            raise ValueError("Model must be fitted before making predictions")
            
        target = target_column if target_column is not None else self.target_column
        if target != self.target_column:
            raise ValueError(f"Prediction target '{target}' does not match initialized target '{self.target_column}'")
            
        return self.bn.predict(data, target)
    
    def query_marginals(self, observations=None):
        """
        Query the marginal probabilities
        Args:
            observations (dict): Dictionary of observed values. Can use original categorical values (strings)
                                   which will be automatically converted to their numeric encodings.
        """
        if self.ie is None:
            raise ValueError("Model must be fitted before querying marginals")
        
        if observations:
            # Convert categorical string values to their numeric encodings
            encoded_observations = {}
            for var, val in observations.items():
                if var in self.label_encoders:
                    le = self.label_encoders[var]
                    # If value is not in classes_, raise a helpful error
                    if val not in le.classes_:
                        raise ValueError(f"Value '{val}' not valid for variable '{var}'. Valid values: {list(le.classes_)}")
                    encoded_observations[var] = le.transform([val])[0]
                else:
                    encoded_observations[var] = val
            return self.ie.query(encoded_observations)
        return self.ie.query()

    def do_intervention(self, node, distribution):
        """
        Perform do-calculus intervention
        Args:
            node (str): Node to intervene on
            distribution (dict): New distribution for the node. Can use original categorical values (strings)
                                   which will be automatically converted to their numeric encodings.
        """
        if self.ie is None:
            raise ValueError("Model must be fitted before performing interventions")
        
        if node in self.label_encoders:
            le = self.label_encoders[node]
            encoded_distribution = {}
            for val, prob in distribution.items():
                # If value is not in classes_, raise a helpful error
                if val not in le.classes_:
                    raise ValueError(f"Value '{val}' not valid for variable '{node}'. Valid values: {list(le.classes_)}")
                encoded_val = le.transform([val])[0]
                encoded_distribution[encoded_val] = prob
            self.ie.do_intervention(node, encoded_distribution)
        else:
            self.ie.do_intervention(node, distribution)
        
    def reset_intervention(self, node):
        """
        Reset an intervention
        
        Args:
            node (str): Node to reset
        """
        if self.ie is None:
            raise ValueError("Model must be fitted before resetting interventions")
        self.ie.reset_do(node)
        
    def plot_structure(self, output_path=None):
        """
        Plot the causal structure
        
        Args:
            output_path (str): Path to save the plot
        """
        if self.sm is None:
            raise ValueError("Structure must be learned before plotting")
            
        viz = plot_structure(
            self.sm,
            all_node_attributes=NODE_STYLE.WEAK,
            all_edge_attributes=EDGE_STYLE.WEAK,
        )
        
        if output_path:
            html = viz.generate_html()
            with open(output_path, mode='w', encoding='utf-8') as fp:
                fp.write(html)
                
        return viz
    
    def save_model(self, path):
        """
        Save the fitted model to disk
        
        Args:
            path (str): Directory path to save the model
        """
        if self.bn is None or self.sm is None:
            raise ValueError("Model must be fitted before saving")
            
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)
        
        # Save all model data in a single pickle file
        model_data = {
            'sm': self.sm,
            'bn': self.bn,
            'label_encoders': self.label_encoders,
            'target_column': self.target_column,
            'threshold': self.threshold,
            'data_file': self.data_file,
            'model_path': self.model_path,
            'model_name': self.model_name,
            'discretised_data': self.discretised_data
        }
        
        with open(os.path.join(path, 'model.pkl'), 'wb') as f:
            pickle.dump(model_data, f)
            
    @classmethod
    def load_model(cls, path):
        """
        Load a saved model from disk
        
        Args:
            path (str): Directory path containing the saved model
            
        Returns:
            CausalInferenceModel: Loaded model instance
        """
        # Load all model data from pickle file
        with open(os.path.join(path, 'model.pkl'), 'rb') as f:
            model_data = pickle.load(f)
            
        # Create new instance
        model = cls(
            data_file=model_data['data_file'],
            model_path=model_data['model_path'],
            target_column=model_data['target_column'],
            threshold=model_data['threshold']
        )
        
        # Restore state
        model.sm = model_data['sm']
        model.bn = model_data['bn']
        model.label_encoders = model_data['label_encoders']
        model.discretised_data = model_data.get('discretised_data')  # Load discretised data if available
        model.ie = InferenceEngine(model.bn)
        
        return model

    def run_causal_analysis(self, intervention=None, query=None, preprocessing_config=None):
        """
        Run causal analysis using the initialized model.
        
        Args:
            intervention (dict, optional): Dictionary specifying the intervention
            query (dict, optional): Dictionary specifying the query conditions
            preprocessing_config (dict, optional): Override configuration for data preprocessing
        """
        try:
            # Check if model exists
            if os.path.exists(os.path.join(self.full_model_path, 'model.pkl')):
                print(f"Loading existing model from {self.full_model_path}")
                self.model = self.load_model(self.full_model_path)
            else:
                print(f"Creating new model and saving to {self.full_model_path}")
                
                # Determine delimiter based on file content
                delimiter = self._detect_delimiter()
                print(f"Detected delimiter: '{delimiter}'")
                
                # Load and preprocess data
                data = pd.read_csv(self.data_file, delimiter=delimiter)
                print("Columns in loaded data:", data.columns.tolist())
                for col in data.columns:
                    unique_vals = data[col].unique()
                    print(f"Column '{col}' unique values ({len(unique_vals)}): {unique_vals}")
                    if len(unique_vals) < 2:
                        print(f"WARNING: Column '{col}' has less than 2 unique values in the raw input data!")
                
                # Sanitize column names to be valid variable names
                data.columns = [col.strip().replace(' ', '_').replace('-', '_') for col in data.columns]
                
                # Define preprocessing configuration
                if preprocessing_config is None:
                    preprocessing_config = {
                        'drop_columns': self._get_drop_columns(),
                        'categorical_mappings': self._get_categorical_mappings(data),
                        'discretize_params': self._get_discretize_params()
                    }
                
                processed_data = self.preprocess_data(
                    data, 
                    drop_columns=preprocessing_config['drop_columns'],
                    discretize_columns=preprocessing_config['discretize_params'],
                    categorical_mappings=preprocessing_config['categorical_mappings']
                )

                # Learn structure with tabu edges from config
                tabu_edges = self._get_tabu_edges()
                self.learn_structure(processed_data, tabu_edges=tabu_edges)

                # Fit model
                self.fit_model()

                # Save the fitted model
                self.save_model(self.full_model_path)
                self.model = self
        
            # Perform intervention if specified
            if intervention:
                print(f"Performing intervention: {intervention}")
                for node, distribution in intervention.items():
                    self.model.do_intervention(node, distribution)
            
            # Query marginals
            print(f"Querying marginals with conditions: {query}")
            marginals = self.model.query_marginals(query)
            
            # Return only the target variable's probabilities, mapped back to original values if categorical
            if self.target_column in marginals:
                result = marginals[self.target_column]
                if self.target_column in self.label_encoders:
                    le = self.label_encoders[self.target_column]
                    # Map keys back to original values
                    result = {le.inverse_transform([k])[0]: v for k, v in result.items()}
                return {self.target_column: result}
            else:
                raise ValueError(f"Target column '{self.target_column}' not found in marginals")
        except Exception as e:
            print(f"Error in run_causal_analysis: {e}")
            return None

    def _detect_delimiter(self):
        """
        Detect the delimiter used in the CSV file by reading the first few lines
        """
        try:
            with open(self.data_file, 'r') as f:
                first_line = f.readline().strip()
                
            # Check for common delimiters
            if ';' in first_line:
                return ';'
            elif ',' in first_line:
                return ','
            elif '\t' in first_line:
                return '\t'
            else:
                # Default to comma if no obvious delimiter found
                return ','
        except Exception as e:
            print(f"Warning: Could not detect delimiter, using comma as default: {e}")
            return ','

    def show_available_options(self):
        """
        Write all available nodes and their possible states for interventions and queries to a YAML file.
        This is a read-only method that doesn't modify any model state.
        """
        if not self.model or not self.model.bn or not self.model.sm:
            print("No model loaded. Please run causal analysis first.")
            return None
            
        # Create options dictionary
        options = {
            'nodes': {}
        }
        
        for node in self.model.sm.nodes():
            # Skip the target column
            if node == self.target_column:
                continue
                
            node_options = {}
            if node in self.model.label_encoders:
                # For categorical variables
                le = self.model.label_encoders[node]
                node_options['type'] = 'categorical'
                # Convert numpy types to native Python types
                node_options['values'] = [str(val) for val in le.classes_]
            else:
                # For discretized variables
                states = self.model.bn.node_states[node]
                node_options['type'] = 'discretized'
                # Convert numpy types to native Python types
                node_options['states'] = [int(val) if isinstance(val, np.integer) else float(val) for val in states]
            
            options['nodes'][node] = node_options
            
        # Add notes about usage
        options['notes'] = {
            'interventions': 'Probabilities must sum to 1.0',
            'queries': 'Use the original categorical values or discretized states',
            'target_column': f'Target column {self.target_column} is excluded from available options'
        }
        
        # Write to YAML file
        output_file = os.path.join(self.model_path, f"{self.model_name}_available_options.yaml")
        with open(output_file, 'w') as f:
            yaml.dump(options, f, default_flow_style=False, sort_keys=False)
            
        print(f"Available options written to: {output_file}")
        return output_file

# Example usage:
if __name__ == "__main__":
    # # Initialize the model once
    # model = CausalInferenceModel(
    #     data_file='student-por.csv',
    #     model_path='saved_models',
    #     target_column='G1',
    #     threshold=0.3,
    #     config_file='preprocessing_config.yaml'
    # )
    
    # # Basic query
    # results = model.run_causal_analysis()
    # print("\nBasic query results:")
    # print(results)
    
    # # With intervention
    # results = model.run_causal_analysis(
    #     intervention={'higher': {'yes': 1.0, 'no': 0.0}}
    # )
    # print("\nResults with intervention:")
    # print(results)
    

    # # With intervention and query
    # results = model.run_causal_analysis(
    #     intervention={'higher': {'yes': 1.0, 'no': 0.0}},
    #     query={'studytime': 'short-studytime'}
    # )
    # print("\nResults with intervention and query:")
    # print(results)
    # print(model.show_available_options())

    # Synthetic Dataset Example
    print("\n" + "="*50)
    print("SYNTHETIC DATASET ANALYSIS")
    print("="*50)
    
    # Initialize the synthetic dataset model
    synthetic_model = CausalInferenceModel(
        data_file='synthetic_dataset.csv',
        model_path='saved_models_synthetic',
        target_column='Margin_Utilisation_Category',
        threshold=0.0,
        config_file='preprocessing_config_synthetic.yaml'
    )
    
    print("\nRunning basic query (no intervention, no query):")
    results = synthetic_model.run_causal_analysis()
    print("Results:", results)

    print("\nRunning intervention on Currency (USD):")
    results = synthetic_model.run_causal_analysis(
        intervention={'Currency': {'USD': 1.0, 'SGD': 0.0, 'HKD': 0.0}}
    )
    print("Results:", results)

    print("\nRunning intervention on Amount_Bucket (More_than_50m_USD) and query Currency=USD:")
    results = synthetic_model.run_causal_analysis(
        intervention={'Amount_Bucket': {'More_than_50m_USD': 1.0, 'Between_10m_and_50m_USD': 0.0, 'Less_than_10m_USD': 0.0}},
        query={'Currency': 'USD'}
    )
    print("Results:", results)
    
    # Show available options for synthetic dataset
    print(synthetic_model.show_available_options())

    for col in synthetic_model.label_encoders:
        print(f"Label encoder for {col}: {synthetic_model.label_encoders[col].classes_}")



