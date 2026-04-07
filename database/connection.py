"""
Backward-compatibility shim.
The canonical implementation is now infrastructure.mongo_db.
All new code should import from there directly.
"""
from infrastructure.mongo_db import (  # noqa: F401
    Database,
    get_db,
    init_db,
    mongo_client,
)

__all__ = ["Database", "get_db", "init_db", "mongo_client"]
