"""
Tests for utils/formatters.py
==============================
All paginated formatters return (text, total_pages) tuples.
Tests verify:
  - Empty lists return (str, 1)
  - Content is correct on the default page (0)
  - Multi-page slicing works correctly
  - Boundary pages are clamped
"""
import pytest

from utils.constants import STATUS_ACCEPTED, STATUS_FINISHED, STATUS_PENDING
from utils.formatters import (
    escape_md,
    format_offer_list,
    format_payment_list,
    format_project_history,
    format_project_list,
    format_master_report,
    format_student_projects,
)


# ---------------------------------------------------------------------------
# escape_md
# ---------------------------------------------------------------------------

def test_escape_md_basic():
    assert escape_md("word") == "word"


def test_escape_md_special_chars():
    raw = "hello_world *bold* `code`"
    expected = r"hello\_world \*bold\* \`code\`"
    assert escape_md(raw) == expected


def test_escape_md_none():
    assert escape_md(None) == ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project(pid, subject="Math", tutor="Dr. X", deadline="2025-12-31",
                  user_id=1, username="ali", full_name="Ali"):
    return {
        "id": pid, "subject_name": subject, "tutor_name": tutor,
        "deadline": deadline, "user_id": user_id, "username": username,
        "user_full_name": full_name,
    }


def _make_history_project(pid, subject="Math", status=STATUS_FINISHED):
    return {"id": pid, "subject_name": subject, "status": status}


def _make_payment(pid, project_id=10, user_id=99, status="pending"):
    return {"id": pid, "project_id": project_id, "user_id": user_id, "status": status}


def _make_offer(pid, subject="Math", tutor="Dr. Y"):
    return {"id": pid, "subject_name": subject, "tutor_name": tutor}


# ---------------------------------------------------------------------------
# format_project_list
# ---------------------------------------------------------------------------

def test_format_project_list_empty():
    text, pages = format_project_list([])
    assert "لا توجد مشاريع" in text
    assert pages == 1


def test_format_project_list_single_page():
    projects = [_make_project(1)]
    text, pages = format_project_list(projects)
    assert pages == 1


def test_format_project_list_multi_page_slicing():
    projects = [_make_project(i) for i in range(1, 12)]  # 11 items → 3 pages of 5
    text_p0, pages = format_project_list(projects, page=0, page_size=5)
    assert pages == 3

    text_p1, _ = format_project_list(projects, page=1, page_size=5)
    assert pages == 3

    text_p2, _ = format_project_list(projects, page=2, page_size=5)
    assert pages == 3


def test_format_project_list_page_clamp():
    projects = [_make_project(i) for i in range(1, 4)]
    text, pages = format_project_list(projects, page=99, page_size=5)
    assert pages == 1


# ---------------------------------------------------------------------------
# format_project_history
# ---------------------------------------------------------------------------

def test_format_project_history_empty():
    text, pages = format_project_history([])
    assert "فارغ" in text
    assert pages == 1


def test_format_project_history_content():
    items = [_make_history_project(1)]
    text, pages = format_project_history(items)
    assert "#1" in text
    assert "🏁" in text   # STATUS_FINISHED icon
    assert pages == 1


def test_format_project_history_pagination():
    items = [_make_history_project(i) for i in range(1, 8)]  # 7 items → 2 pages
    text_p0, pages = format_project_history(items, page=0, page_size=5)
    assert pages == 2
    assert "#5" in text_p0
    assert "#6" not in text_p0

    text_p1, _ = format_project_history(items, page=1, page_size=5)
    assert "#6" in text_p1


# ---------------------------------------------------------------------------
# format_master_report
# ---------------------------------------------------------------------------

def _categorized(n_new=3, n_ongoing=3, n_hist=3):
    return {
        "New / Pending": [_make_project(i) for i in range(1, n_new + 1)],
        "Offered / Waiting": [],
        "Ongoing": [_make_project(i) for i in range(100, 100 + n_ongoing)],
        "History": [_make_history_project(i) for i in range(200, 200 + n_hist)],
    }


def test_format_master_report_empty():
    text, pages = format_master_report({"New / Pending": [], "Offered / Waiting": [],
                                        "Ongoing": [], "History": []})
    assert "لا توجد مشاريع" in text
    assert pages == 1


def test_format_master_report_single_page():
    data = _categorized(n_new=1, n_ongoing=0, n_hist=0)
    text, pages = format_master_report(data)
    assert "#1" in text
    assert pages == 1


def test_format_master_report_multi_page():
    data = _categorized(n_new=5, n_ongoing=5, n_hist=2)  # 12 total → 3 pages
    text_p0, pages = format_master_report(data, page=0, page_size=5)
    assert pages == 3
    text_p2, _ = format_master_report(data, page=2, page_size=5)
    assert "صفحة 3/3" in text_p2


# ---------------------------------------------------------------------------
# format_payment_list
# ---------------------------------------------------------------------------

def test_format_payment_list_empty():
    text, pages = format_payment_list([])
    assert "فارغ" in text
    assert pages == 1


def test_format_payment_list_content():
    payments = [_make_payment(1, status="accepted")]
    text, pages = format_payment_list(payments)
    assert "D#1" in text
    assert "✅" in text


def test_format_payment_list_pagination():
    payments = [_make_payment(i) for i in range(1, 9)]  # 8 items → 2 pages
    text_p0, pages = format_payment_list(payments, page=0, page_size=5)
    assert pages == 2
    assert "D#5" in text_p0
    assert "D#6" not in text_p0

    text_p1, _ = format_payment_list(payments, page=1, page_size=5)
    assert "D#6" in text_p1


# ---------------------------------------------------------------------------
# format_student_projects
# ---------------------------------------------------------------------------

def test_format_student_projects_empty():
    text, pages = format_student_projects([])
    assert "لم تقم بتقديم أي مشاريع" in text
    assert pages == 1


def test_format_student_projects_statuses():
    projects = [
        {"id": 101, "subject_name": "Physics", "status": STATUS_PENDING},
        {"id": 102, "subject_name": "Chemistry", "status": STATUS_ACCEPTED},
        {"id": 103, "subject_name": "Biology", "status": STATUS_FINISHED},
    ]
    text, pages = format_student_projects(projects)
    assert "#101" in text and "#102" in text and "#103" in text
    assert "⏳" in text and "🚀" in text and "✅" in text
    assert pages == 1


def test_format_student_projects_pagination():
    projects = [{"id": i, "subject_name": f"S{i}", "status": STATUS_PENDING}
                for i in range(1, 12)]
    text_p0, pages = format_student_projects(projects, page=0, page_size=5)
    assert pages == 3
    assert "#5" in text_p0
    assert "#6" not in text_p0


# ---------------------------------------------------------------------------
# format_offer_list
# ---------------------------------------------------------------------------

def test_format_offer_list_empty():
    text, pages = format_offer_list([])
    assert pages == 1


def test_format_offer_list_content():
    offers = [_make_offer(1)]
    text, pages = format_offer_list(offers)
    assert pages == 1


def test_format_offer_list_pagination():
    offers = [_make_offer(i) for i in range(1, 9)]
    text_p0, pages = format_offer_list(offers, page=0, page_size=5)
    assert pages == 2

    text_p1, _ = format_offer_list(offers, page=1, page_size=5)
    assert pages == 2
