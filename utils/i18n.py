
import json
import os
from typing import Dict, Any

def load_messages(lang: str = "ar") -> Dict[str, Any]:
    """
    Loads localization strings from the specified locale file.
    Default language is Arabic ('ar').
    """
    # Assuming locales are stored in a 'locales' directory at the project root
    base_path = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_path, "locales", f"{lang}.json")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Locale file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in locale file {file_path}: {e}")
