import sys
import os
sys.path.append(os.getcwd())
from utils.formatters import format_master_report

def test_formatting():
    # Mock data structure matching new database query output
    mock_data = {
        "New / Pending": [
            {'id': 1, 'subject_name': 'Math', 'tutor_name': 'TutorA', 'user_id': 123, 'username': 'student1', 'user_full_name': 'Student One'}
        ],
        "Ongoing": [
            {'id': 2, 'subject_name': 'Physics', 'tutor_name': 'TutorB', 'user_id': 456, 'username': None, 'user_full_name': 'Student Two'}
        ]
    }
    
    report = format_master_report(mock_data)
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    print(report)

if __name__ == "__main__":
    test_formatting()
