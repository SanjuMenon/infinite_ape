#!/usr/bin/env python3
"""
Script to run the Causal Agent Streamlit app
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit app"""
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the app directory
    os.chdir(current_dir)
    
    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\nShutting down Streamlit app...")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 