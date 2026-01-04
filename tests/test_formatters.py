from utils.formatters import format_project_history, format_master_report

def test_history_icons():
    # Test that Denied gets a cross and Finished gets a flag
    data = [(1, "Math", "Denied"), (2, "Bio", "Finished")]
    result = format_project_history(data)
    assert "❌ #1" in result
    assert "🏁 #2" in result

def test_master_report_categorization():
    data = [(1, "Math", "Pending"), (2, "Code", "Awaiting Verification")]
    result = format_master_report(data)
    assert "⏳ PENDING" in result
    assert "🚀 ONGOING" in result
    assert "Awaiting Verification" in result
    