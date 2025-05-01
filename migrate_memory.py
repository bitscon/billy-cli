import json
import sqlite3
from datetime import datetime

# Load existing memory.json
with open("src/memory.json", "r") as f:
    memory = json.load(f)

# Connect to SQLite database
conn = sqlite3.connect("/home/billybs/Projects/billy/db/billy.db")
cursor = conn.cursor()

# Migrate data
for entry in memory:
    cursor.execute('''
        INSERT INTO memory (prompt, response, category, tool_code, tool_result, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        entry.get("prompt"),
        entry.get("response"),
        entry.get("category", "general"),
        entry.get("tool_code"),
        entry.get("tool_result"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

conn.commit()
conn.close()
