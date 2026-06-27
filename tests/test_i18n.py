import pytest
import json
import os
from unittest.mock import patch, mock_open
from utils.i18n import load_messages

def test_load_messages_success():
    mock_data = '{"messages": {"test": "value"}}'
    with patch("builtins.open", mock_open(read_data=mock_data)):
        result = load_messages("ar")
        assert result == {"messages": {"test": "value"}}

def test_load_messages_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="Locale file not found"):
            load_messages("ar")

def test_load_messages_invalid_json():
    mock_data = '{"invalid_json'
    with patch("builtins.open", mock_open(read_data=mock_data)):
        with pytest.raises(RuntimeError, match="Invalid JSON in locale file"):
            load_messages("ar")
