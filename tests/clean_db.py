import asyncio
import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def clean_e2e_data():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME")
    
    if not mongo_uri or not db_name:
        print("Missing DB credentials.")
        return

    client = AsyncIOMotorClient(mongo_uri, tlsCAFile=certifi.where())
    db = client[db_name]
    team_requests = db["team_requests"]
    
    # Delete any team request created during E2E testing
    result = await team_requests.delete_many({"course_name": "E2E Matchmaking Course"})
    print(f"🧹 Cleaned up {result.deleted_count} E2E test teams from database.")

if __name__ == "__main__":
    asyncio.run(clean_e2e_data())
