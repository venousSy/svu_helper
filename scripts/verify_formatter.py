
import asyncio
import os
import sys

# Add the project root to the path
sys.path.append(os.getcwd())

from utils.formatters import format_master_report

def test_formatter():
    print("Testing formatter with dicts...")
    
    # Simulate DB output (dicts)
    fake_data = {
        "New / Pending": [{'id': 1, 'subject_name': 'Math', 'tutor_name': 'Prof X'}],
        "Ongoing": [{'id': 2, 'subject_name': 'Physics', 'tutor_name': 'Prof Y'}],
        "History": [{'id': 3, 'subject_name': 'Hist', 'status': 'Finished'}]
    }
    
    try:
        output = format_master_report(fake_data)
        # Avoid printing unicode to console to prevent CP1252 errors
        print("Output generated. Length:", len(output))
        
        if "Math" in output and "Physics" in output and "Hist" in output:
             print("\n[OK] All items found in report.")
             return True
        else:
             print("\n[FAIL] Missing items in report.")
             return False
             
    except Exception as e:
        print(f"\n[FAIL] Formatter crashed: {e}")
        return False

if __name__ == "__main__":
    test_formatter()
