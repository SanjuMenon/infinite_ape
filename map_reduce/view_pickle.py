import pickle
import json
from pathlib import Path

def main():
    # Get the path to the pickle file (in the same directory as this script)
    script_dir = Path(__file__).parent
    pickle_path = script_dir / "most_current_data.pkl"
    
    # Read the pickle file
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    # Convert to JSON and print with pretty formatting
    json_output = json.dumps(data, indent=2, default=str)
    print(json_output)

if __name__ == "__main__":
    main()
