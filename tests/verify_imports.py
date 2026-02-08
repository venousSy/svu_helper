import sys
import os
import asyncio

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set env vars for config
os.environ.setdefault("BOT_TOKEN", "test_token")
os.environ.setdefault("ADMIN_IDS", "123")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")

print("Verifying imports...")
try:
    import keyboards.callbacks
    print("keyboards.callbacks imported")
    import keyboards.client_kb
    print("keyboards.client_kb imported")
    import keyboards.admin_kb
    print("keyboards.admin_kb imported")
    import handlers.client
    print("handlers.client imported")
    import handlers.admin_routes
    print("handlers.admin_routes imported")
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)
