"""
Course Utilities
================
Predefined list of common SVU course abbreviations used for team
matchmaking. Students select from these when creating or searching
for teams.
"""
from typing import List

# Common SVU course abbreviations used by students
DEFAULT_COURSES: List[str] = [
    "STP", "DBS", "NTP", "WEB", "PRG", "OOP",
    "DSA", "OS", "CN", "SE", "AI", "ML",
    "PHY", "MATH", "STAT", "ENG", "ARB",
]


def get_all_courses() -> List[str]:
    """Returns all known course abbreviations."""
    return list(DEFAULT_COURSES)
