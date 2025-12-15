
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal, init_db, engine
from app.db.crud_voice import create_voice_scan
from sqlalchemy import inspect

def test_db():
    print(f"DB URL: {engine.url}")
    
    # Check tables via SQLAlchemy inspector
    insp = inspect(engine)
    print(f"Tables in DB: {insp.get_table_names()}")
    
    print("Initializing DB...")
    init_db() 
    
    # Check again
    insp = inspect(engine)
    print(f"Tables after init: {insp.get_table_names()}")

    db = SessionLocal()
    try:
        print("Attempting to create voice scan...")
        scan = create_voice_scan(
            db=db,
            file_hash="test_hash_12345",
            file_name="test_file.wav",
            file_path="uploads/voice/test_file.wav",
            file_size=1024,
            duration=5.5,
            is_deepfake=True,
            confidence=0.99,
            risk_level="high",
            artifacts={"test": 123},
            highlights=["test highlight"]
        )
        print(f"SUCCESS! Created scan with ID: {scan.id}")
    except Exception as e:
        print(f"DB FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_db()
