import sqlite3
import os
from contextlib import contextmanager

# Default DB name
DB_NAME = "bot_requests.db"

@contextmanager
def get_db_connection(db_path=DB_NAME):
    """Context manager for database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=(), fetch=False, fetch_one=False, db_path=DB_NAME):
    """
    Executes a query safely using the context manager.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch_one:
            result = cursor.fetchone()
            return dict(result) if result else None
        
        if fetch:
            results = cursor.fetchall()
            return [dict(row) for row in results]
        
        conn.commit()
        return cursor.lastrowid

def init_db(db_path=DB_NAME):
    """Initializes the database with all necessary columns for the full workflow."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject_name TEXT,
                tutor_name TEXT,
                deadline TEXT,
                details TEXT,
                file_id TEXT,
                status TEXT DEFAULT 'Pending',
                price TEXT,           -- Admin's offered price
                delivery_date TEXT,   -- Admin's offered delivery date
                admin_price TEXT,     -- Legacy column (keep for compatibility)
                admin_time TEXT       -- Legacy column (keep for compatibility)
            )
        ''')
        conn.commit()

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

def get_all_projects_categorized(db_path="bot_requests.db"):
    """Returns a dictionary of projects grouped by status."""
    pending = execute_query(
        "SELECT id, subject_name, tutor_name FROM projects WHERE status = 'Pending'", 
        fetch=True, db_path=db_path
    )
    
    ongoing = execute_query(
        "SELECT id, subject_name, tutor_name FROM projects WHERE status IN ('Accepted', 'Awaiting Verification')", 
        fetch=True, db_path=db_path
    )
    
    # Selecting the 3rd value as 'status' for the History category logic
    history = execute_query(
        "SELECT id, subject_name, status FROM projects WHERE status IN ('Finished', 'Denied') "
        "OR status LIKE 'Rejected%' OR status LIKE 'Denied%'", 
        fetch=True, db_path=db_path
    )
    offered = execute_query(
        "SELECT id, subject_name, tutor_name FROM projects WHERE status = 'Offered'", 
        fetch=True, db_path=db_path
    )
    return {
        "New / Pending": pending,
        "Offered / Waiting": offered,
        "Ongoing": ongoing,
        "History": history
    }

def get_all_users(db_path=DB_NAME):
    """Returns a list of unique user_ids who have submitted projects."""
    rows = execute_query("SELECT DISTINCT user_id FROM projects", fetch=True, db_path=db_path)
    return [row['user_id'] for row in rows]

def get_student_offers(user_id, db_path="bot_requests.db"):
    """Retrieves all projects for a user that currently have an active offer."""
    query = "SELECT id, subject_name, tutor_name FROM projects WHERE user_id = ? AND status = 'Offered'"
    return execute_query(query, (user_id,), fetch=True, db_path=db_path)

def update_offer_details(proj_id, price, delivery, db_path="bot_requests.db"):
    query = "UPDATE projects SET status = 'Offered', price = ?, delivery_date = ? WHERE id = ?"
    execute_query(query, (price, delivery, proj_id), db_path=db_path)