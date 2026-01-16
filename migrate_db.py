import sqlite3

def migrate_database():
    """Migrate existing database to new schema."""
    conn = sqlite3.connect("bot_requests.db")
    cursor = conn.cursor()
    
    # Check if new columns exist
    cursor.execute("PRAGMA table_info(projects)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add missing columns
    if 'price' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN price TEXT")
        print("Added 'price' column")
    
    if 'delivery_date' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN delivery_date TEXT")
        print("Added 'delivery_date' column")
    
    # Migrate data from old columns to new
    cursor.execute("UPDATE projects SET price = admin_price WHERE price IS NULL AND admin_price IS NOT NULL")
    cursor.execute("UPDATE projects SET delivery_date = admin_time WHERE delivery_date IS NULL AND admin_time IS NOT NULL")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_database()