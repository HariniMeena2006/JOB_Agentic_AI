import sqlite3
import uuid
import json
import os

DB_PATH = "data/output.db"

def init_db():
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_job(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Guarantee job_id exists
    job_id = data.get("job_id", str(uuid.uuid4()))
    data["job_id"] = job_id

    c.execute(
        "INSERT OR REPLACE INTO jobs (job_id, data) VALUES (?, ?)",
        (job_id, json.dumps(data))
    )

    conn.commit()
    conn.close()

    print(f"💾 Saved job → {job_id}")
