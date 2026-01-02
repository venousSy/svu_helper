import sqlite3

def read_all_requests():
    # 1. Connect to the database
    conn = sqlite3.connect("projects.db")
    cursor = conn.cursor()

    # 2. Select all columns from our 'requests' table
    cursor.execute("SELECT id, user_id, status, subject_name FROM projects")
    
    # 3. Fetch all rows
    rows = cursor.fetchall()

    print(f"{'ID':<5} | {'User ID':<15} | {'Status':<10} | {'Message'}")
    print("-" * 50)

    for row in rows:
        # row[0] is ID, row[1] is user_id, row[2] is text, row[3] is status
        print(f"{row[0]:<5} | {row[1]:<15} | {row[3]:<10} | {row[2]}")

    conn.close()

if __name__ == "__main__":
    read_all_requests()