import pytest

from utils.constants import STATUS_ACCEPTED, STATUS_FINISHED, STATUS_PENDING
from utils.formatters import escape_md, format_project_list, format_student_projects


# --- Tests for escape_md ---
def test_escape_md_basic():
    assert escape_md("word") == "word"


def test_escape_md_special_chars():
    # Markdown special characters: _, *, `
    raw = "hello_world *bold* `code`"
    expected = r"hello\_world \*bold\* \`code\`"
    assert escape_md(raw) == expected


def test_escape_md_none():
    assert escape_md(None) == ""


# --- Tests for format_project_list ---
def test_format_project_list_empty():
    assert "لا توجد مشاريع" in format_project_list([])


def test_format_project_list_dictionaries():
    projects = [
        {
            "id": 1,
            "subject_name": "Math",
            "user_full_name": "Ali",
            "username": "ali123",
            "user_id": 12345,
            "tutor_name": "Dr. Smith",
            "deadline": "2023-12-31",
        }
    ]
    result = format_project_list(projects)
    assert "#1" in result
    assert "Math" in result
    assert "Ali" in result
    assert "@ali123" in result
    assert "Dr. Smith" in result
    # Check for markdown escaping in result if needed, though here we just check content presence


# --- Tests for format_student_projects ---
def test_format_student_projects_empty():
    # "لم تقم بتقديم أي مشاريع بعد" is part of MSG_NO_PROJECTS
    assert "لم تقم بتقديم أي مشاريع" in format_student_projects([])


def test_format_student_projects_statuses():
    projects = [
        {"id": 101, "subject_name": "Physics", "status": STATUS_PENDING},
        {"id": 102, "subject_name": "Chemistry", "status": STATUS_ACCEPTED},
        {"id": 103, "subject_name": "Biology", "status": STATUS_FINISHED},
    ]
    result = format_student_projects(projects)

    # Check for IDs
    assert "#101" in result
    assert "#102" in result
    assert "#103" in result

    # Check for Status Emojis/Text
    assert "⏳" in result  # Pending
    assert "🚀" in result  # Accepted
    assert "✅" in result  # Finished
