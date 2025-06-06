# Entry point for the Databricks AI Chatbot application

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent))

from src.app import main

if __name__ == "__main__":
    main()