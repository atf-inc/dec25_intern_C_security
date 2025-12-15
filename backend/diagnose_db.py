
import sqlite3
import os

DB_FILE = "cyber_defense.db"

def diagnose():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found.")
        return

    print(f"Connecting to {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables found: {tables}")

        for table in tables:
            table_name = table[0]
            print(f"\n--- Schema for {table_name} ---")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(col)

    except Exception as e:
        print(f"Diagnosis failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    diagnose()
