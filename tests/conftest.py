import os
import sys

# Mock Environment Variables BEFORE importing project modules
os.environ.setdefault("BOT_TOKEN", "test_token")
os.environ.setdefault("ADMIN_IDS", "12345,67890")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")

# Ensure the root directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
