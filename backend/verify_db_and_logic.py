
import sqlite3
import os
import sys

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

DB_FILE = "cyber_defense.db"

def check_db():
    print(f"Checking {DB_FILE}...")
    if not os.path.exists(DB_FILE):
        print("DB file missing!")
        return
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(voice_scans)")
        cols = c.fetchall()
        if not cols:
            print("Table voice_scans NOT found.")
        else:
            print("Table voice_scans found. Columns:")
            found_file_path = False
            for col in cols:
                print(f" - {col[1]} ({col[2]})")
                if col[1] == 'file_path':
                    found_file_path = True
            
            if found_file_path:
                print("SUCCESS: file_path column exists.")
            else:
                print("FAILURE: file_path column MISSING.")
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()

def check_service():
    print("\nChecking Service Initialization...")
    try:
        from app.services.voice_service import VoiceAnalysisService
        service = VoiceAnalysisService()
        print("Service initialized successfully.")
    except Exception as e:
        print(f"Service Init Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_db()
    check_service()
