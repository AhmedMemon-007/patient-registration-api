import sqlite3
from pathlib import Path
import os
DB_PATH = Path(os.environ.get("DB_PATH", "/data/patients.db"))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with open(Path(__file__).parent / "schema.sql") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()