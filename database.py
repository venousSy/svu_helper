import sqlite3

DB_NAME = "bot_requests.db"

def execute_query(query, params=(), fetch=False, fetch_one=False):
    """Internal helper to handle repetitive connection logic."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch_one:
            return cursor.fetchone()
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid

def init_db():
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
    ''')

def add_project(user_id, subject, tutor, deadline, details, file_id):
    return execute_query('''
        INSERT INTO projects (user_id, subject_name, tutor_name, deadline, details, file_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, subject, tutor, deadline, details, file_id))

def get_pending_projects():
    return execute_query("SELECT id, subject_name, user_id FROM projects WHERE status = 'Pending'", fetch=True)

def get_user_projects(user_id):
    return execute_query("SELECT id, subject_name, status FROM projects WHERE user_id = ?", (user_id,), fetch=True)

def update_project_status(project_id, status):
    """Updates the status of a specific project (e.g., 'Accepted' or 'Denied')."""
    return execute_query(
        "UPDATE projects SET status = ? WHERE id = ?", 
        (status, project_id)
    )
def update_project_status(project_id, new_status):
    """Updates the status of a project with a descriptive string."""
    execute_query(
        "UPDATE projects SET status = ? WHERE id = ?",
        (new_status, project_id)
    )

def get_all_projects_categorized():
    """Fetches all projects to be sorted in the Admin panel."""
    return execute_query("SELECT id, subject_name, status FROM projects", fetch=True)