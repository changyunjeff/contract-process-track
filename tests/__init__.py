"""
Test initialization module.

This module is automatically imported by pytest before running tests.
It loads environment variables from the .env file in the project root.
"""
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if it exists
# tests/__init__.py is in tests/ directory, so we go up one level to get project root
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=False)
