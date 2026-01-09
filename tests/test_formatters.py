from utils.formatters import format_project_history, format_master_report

def test_history_icons():
    # Test that Denied gets a cross and Finished gets a flag
    data = [(1, "Math", "Denied"), (2, "Bio", "Finished")]
    result = format_project_history(data)
    assert "❌ #1" in result
    assert "🏁 #2" in result

def test_master_report_categorization():
    # Old way (List): data = [(1, "Math", "Pending")] ❌
    
    # New way (Dictionary): ✅
    data = {
        "Pending": [(1, "Math")],
        "Accepted": [(2, "Code")],
        "Finished": [],
        "Denied": []
    }
    result = format_master_report(data)
    assert "Math" in result
    assert "PENDING" in result.upper()