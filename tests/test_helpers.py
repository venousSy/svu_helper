from unittest.mock import MagicMock

import pytest

from utils.helpers import get_file_id


def test_get_file_id_document():
    message = MagicMock()
    message.document.file_id = "doc_123"
    message.photo = None

    file_id, file_type = get_file_id(message)
    assert file_id == "doc_123"
    assert file_type == "document"


def test_get_file_id_photo():
    message = MagicMock()
    message.document = None

    # Mocking a list of photos, where the last one is the largest
    photo1 = MagicMock()
    photo1.file_id = "small_123"
    photo2 = MagicMock()
    photo2.file_id = "large_123"

    message.photo = [photo1, photo2]

    file_id, file_type = get_file_id(message)
    assert file_id == "large_123"
    assert file_type == "photo"


def test_get_file_id_none():
    message = MagicMock()
    message.document = None
    message.photo = None

    file_id, file_type = get_file_id(message)
    assert file_id is None
    assert file_type is None
