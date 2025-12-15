
import sqlite3
import os

DB_FILE = "cyber_defense.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found.")
        return

    print(f"Connecting to {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(voice_scans)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "file_path" in columns:
            print("Column 'file_path' already exists in 'voice_scans'.")
        else:
            print("Adding column 'file_path' to 'voice_scans'...")
            cursor.execute("ALTER TABLE voice_scans ADD COLUMN file_path TEXT")
            conn.commit()
            print("Migration successful: Added 'file_path' column.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
