from database import init_db, add_project, update_project_status, get_user_projects

def test_complete_student_to_admin_flow():
    db = "test_journey.db"
    # 0. INITIALIZE THE DATABASE FIRST (The missing step!)
    init_db(db_path=db)
    
    uid = 55555
    
    # 1. Student submits
    pid = add_project(uid, "Calculus", "Dr. A", "Friday", "Help!", None, db_path=db)
    
    # 2. Check if student sees it as Pending
    projs = get_user_projects(uid, db_path=db)
    assert projs[0][2] == "Pending"
    
    # 3. Admin updates status (Simulating the workflow)
    update_project_status(pid, "Accepted", db_path=db)
    
    # 4. Final check
    final_projs = get_user_projects(uid, db_path=db)
    assert final_projs[0][2] == "Accepted"