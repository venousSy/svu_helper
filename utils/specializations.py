import json
import os
from typing import List, Dict, Any
from infrastructure.mongo_db import get_db

_JSON_PATH = os.path.join(os.path.dirname(__file__), "specializations.json")

def _load_static_data() -> Dict[str, Any]:
    """Load the JSON data into memory."""
    if os.path.exists(_JSON_PATH):
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

async def get_all_specializations() -> List[str]:
    """
    Retrieve a flat list of all specialization names across all categories,
    including any custom ones persisted in the database.
    """
    data = _load_static_data()
    flat_list = []
    programs = data.get("programs", {})
    for category in programs.values():
        for program in category:
            flat_list.append(program["name"])
            
    # Fetch from DB to ensure runtime additions persist across Railway deploys
    db = await get_db()
    cursor = db.custom_specializations.find({})
    async for spec in cursor:
        if spec["name"] not in flat_list:
            flat_list.append(spec["name"])
            
    return flat_list

async def get_specializations_by_category(category: str) -> List[Dict[str, str]]:
    """
    Retrieve specializations for a specific category.
    Custom ones are fetched from the database under the given category.
    """
    data = _load_static_data()
    programs = data.get("programs", {})
    results = programs.get(category, [])
    
    # Fetch from DB
    db = await get_db()
    cursor = db.custom_specializations.find({"category": category})
    async for spec in cursor:
        results.append({
            "name": spec["name"],
            "abbreviation": spec.get("abbreviation")
        })
        
    return results

async def add_specialization(spec_name: str, category: str = "additional_programs", abbreviation: str = None) -> None:
    """
    Add a new specialization to the database.
    This persists it across redeployments on ephemeral platforms.
    """
    db = await get_db()
    
    # Check if exists in DB
    existing = await db.custom_specializations.find_one({
        "name": {"$regex": f"^{spec_name.strip()}$", "$options": "i"}
    })
    if existing:
        return
        
    # Also check JSON to prevent inserting duplicates of static data
    static_data = _load_static_data()
    for cat, progs in static_data.get("programs", {}).items():
        for prog in progs:
            if prog["name"].lower() == spec_name.strip().lower():
                return
                
    new_doc = {
        "name": spec_name.strip(),
        "category": category
    }
    if abbreviation:
        new_doc["abbreviation"] = abbreviation.strip()
        
    await db.custom_specializations.insert_one(new_doc)
