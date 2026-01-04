from utils.formatters import format_student_projects

def test_student_emoji_logic():
    mock_data = [
        (1, "Math", "Pending"),
        (2, "Physics", "Awaiting Verification"),
        (3, "History", "Finished"),
        (4, "Art", "Denied: Admin Rejected")
    ]
    
    result = format_student_projects(mock_data)
    
    assert "⏳ Pending" in result
    assert "🚀 Awaiting Verification" in result
    assert "✅ Finished" in result
    assert "❌ Denied: Admin Rejected" in result

def test_student_empty_projects():
    result = format_student_projects([])
    assert "You haven't submitted any projects" in result