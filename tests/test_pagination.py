"""
Unit tests for utils/pagination.py
"""
import pytest
from utils.pagination import paginate, PAGE_SIZE


def test_paginate_empty_list():
    slice_, total_pages, page = paginate([], page=0)
    assert slice_ == []
    assert total_pages == 1
    assert page == 0


def test_paginate_single_page():
    items = list(range(3))
    slice_, total_pages, page = paginate(items, page=0, page_size=5)
    assert slice_ == [0, 1, 2]
    assert total_pages == 1
    assert page == 0


def test_paginate_exact_boundary():
    items = list(range(5))
    slice_, total_pages, page = paginate(items, page=0, page_size=5)
    assert len(slice_) == 5
    assert total_pages == 1


def test_paginate_two_pages():
    items = list(range(8))
    slice_p0, total_pages, _ = paginate(items, page=0, page_size=5)
    assert total_pages == 2
    assert slice_p0 == [0, 1, 2, 3, 4]

    slice_p1, _, _ = paginate(items, page=1, page_size=5)
    assert slice_p1 == [5, 6, 7]


def test_paginate_clamps_negative_page():
    items = list(range(10))
    _, _, page = paginate(items, page=-5, page_size=5)
    assert page == 0


def test_paginate_clamps_overflow_page():
    items = list(range(10))
    slice_, total_pages, page = paginate(items, page=999, page_size=5)
    assert page == total_pages - 1
    assert len(slice_) > 0


def test_paginate_ceiling_division():
    items = list(range(11))
    _, total_pages, _ = paginate(items, page=0, page_size=5)
    assert total_pages == 3   # ceil(11/5) = 3


@pytest.mark.parametrize("n_items,page_size,expected_pages", [
    (0,  5, 1),
    (1,  5, 1),
    (5,  5, 1),
    (6,  5, 2),
    (10, 5, 2),
    (11, 5, 3),
    (25, 5, 5),
])
def test_paginate_total_pages(n_items, page_size, expected_pages):
    items = list(range(n_items))
    _, total_pages, _ = paginate(items, page=0, page_size=page_size)
    assert total_pages == expected_pages
