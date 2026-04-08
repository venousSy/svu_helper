import os
import sys

# Mock Environment Variables BEFORE importing project modules
# These mocks are essential because the local environment lacks a .env file (variables are on Railway)
print("DEBUG: conftest.py loaded, setting env vars (Railway variables are mocked locally)")
os.environ["BOT_TOKEN"] = "test_token"
os.environ["ADMIN_IDS"] = "12345,67890"  # Comma-separated as expected by config.py
os.environ["MONGO_URI"] = "mongodb://localhost:27017"

# Ensure the root directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
