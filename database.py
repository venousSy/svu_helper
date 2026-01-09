import sqlite3
import os

# Default DB name
DB_NAME = "bot_requests.db"

def execute_query(query, params=(), fetch=False, fetch_one=False, db_path=DB_NAME):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        if fetch_one: return cursor.fetchone()
        if fetch: return cursor.fetchall()
        return cursor.lastrowid

def init_db(db_path=DB_NAME):
    execute_query('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_name TEXT,
            tutor_name TEXT,
            deadline TEXT,
            details TEXT,
            file_id TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''', db_path=db_path)

def add_project(user_id, subject, tutor, deadline, details, file_id, db_path=DB_NAME):
    return execute_query('''
        INSERT INTO projects (user_id, subject_name, tutor_name, deadline, details, file_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, subject, tutor, deadline, details, file_id), db_path=db_path)

def get_pending_projects(db_path=DB_NAME):
    return execute_query("SELECT id, subject_name, user_id FROM projects WHERE status = 'Pending'", fetch=True, db_path=db_path)

def get_user_projects(user_id, db_path=DB_NAME):
    return execute_query("SELECT id, subject_name, status FROM projects WHERE user_id = ?", (user_id,), fetch=True, db_path=db_path)

def update_project_status(project_id, new_status, db_path=DB_NAME):
    return execute_query(
        "UPDATE projects SET status = ? WHERE id = ?",
        (new_status, project_id), db_path=db_path
    )

def get_all_projects_categorized(db_path=DB_NAME): 
    """Returns a dictionary of projects grouped by their status."""
    statuses = ["Pending", "Accepted", "Finished", "Denied"]
    report = {}
    
    for status in statuses:
        # Pass the db_path into the execute_query call
        query = "SELECT id, subject_name FROM projects WHERE status LIKE ?"
        results = execute_query(query, (f"{status}%",), fetch=True, db_path=db_path)
        report[status] = results
    
    return report
def get_all_users(db_path=DB_NAME):
    """Returns a list of unique user_ids who have submitted projects."""
    rows = execute_query("SELECT DISTINCT user_id FROM projects", fetch=True, db_path=db_path)
    return [row[0] for row in rows]