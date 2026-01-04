# Save this in tests/test_full_journey.py
from database import add_project, update_project_status, get_user_projects

def test_complete_student_to_admin_flow():
    db = "test_journey.db"
    uid = 55555
    
    # 1. Student submits
    pid = add_project(uid, "Calculus", "Dr. A", "Friday", "Help!", None, db_path=db)
    
    # 2. Check if student sees it as Pending
    projs = get_user_projects(uid, db_path=db)
    assert projs[0][2] == "Pending"
    
    # 3. Admin updates to Awaiting Verification (Student accepted offer)
    update_project_status(pid, "Awaiting Verification", db_path=db)
    
    # 4. Admin confirms payment (Ongoing)
    update_project_status(pid, "Accepted", db_path=db)
    
    # 5. Admin finishes
    update_project_status(pid, "Finished", db_path=db)
    
    # 6. Final check
    final_projs = get_user_projects(uid, db_path=db)
    assert final_projs[0][2] == "Finished"