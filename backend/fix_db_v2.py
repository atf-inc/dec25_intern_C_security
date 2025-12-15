
import sys
import os
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

from app.db.session import engine

def fix_db():
    print(f"Connecting to DB at: {engine.url}...")
    
    with engine.connect() as conn:
        try:
            # Check table existence (SQLite specific)
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='voice_scans';"))
            if result.fetchone():
                print("Table 'voice_scans' exists.")
                # Check column
                result = conn.execute(text("PRAGMA table_info(voice_scans)"))
                columns = [row[1] for row in result.fetchall()]
                if "file_path" not in columns:
                    print("Adding 'file_path' column...")
                    conn.execute(text("ALTER TABLE voice_scans ADD COLUMN file_path TEXT"))
                    conn.commit()
                    print("Column added.")
                else:
                    print("'file_path' column already exists.")
            else:
                print("Table 'voice_scans' does NOT exist. Creating it...")
                conn.execute(text("""
                CREATE TABLE voice_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash VARCHAR NOT NULL,
                    file_name VARCHAR NOT NULL,
                    file_path VARCHAR,
                    file_size INTEGER,
                    duration FLOAT,
                    is_deepfake BOOLEAN NOT NULL,
                    confidence FLOAT NOT NULL,
                    risk_level VARCHAR NOT NULL,
                    raw_model_confidence FLOAT,
                    artifact_score FLOAT,
                    artifacts JSON,
                    explanation VARCHAR,
                    highlights JSON,
                    created_at DATETIME,
                    processing_time FLOAT,
                    model_version VARCHAR
                );
                """))
                conn.execute(text("CREATE UNIQUE INDEX ix_voice_scans_file_hash ON voice_scans (file_hash);"))
                conn.execute(text("CREATE INDEX ix_voice_scans_id ON voice_scans (id);"))
                conn.commit()
                print("Table 'voice_scans' created.")
                
        except Exception as e:
            print(f"Fix failed: {e}")

if __name__ == "__main__":
    fix_db()
