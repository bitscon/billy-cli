import sqlite3
from datetime import datetime

def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect("/home/billybs/Projects/billy/db/billy.db")
    conn.row_factory = sqlite3.Row
    return conn

def load_memory():
    """Load all memory entries from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memory")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_memory(prompt, response, category="general", tool_code=None, tool_result=None):
    """Save a memory entry to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO memory (prompt, response, category, tool_code, tool_result, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (prompt, response, category, tool_code, tool_result, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_memory_context(category=None):
    """Get memory context for a specific category."""
    memory = load_memory()
    if not memory:
        return "No past interactions."
    context = "\nPast interactions:\n"
    for entry in memory:
        entry_category = entry.get("category", "general")
        if category is None or entry_category == category:
            context += f"[{entry_category}] User: {entry['prompt']}\nBilly: {entry['response']}\n"
            if "tool_code" in entry and "tool_result" in entry and entry["tool_code"] and entry["tool_result"]:
                context += f"[Tool] Code: {entry['tool_code']}\n[Tool] Result: {entry['tool_result']}\n"
    return context if context != "\nPast interactions:\n" else f"No past interactions for category '{category}'."

def save_learning_entry(prompt, response, error, success, feedback):
    """Save a learning entry to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO learning (prompt, response, error, success, feedback, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (prompt, response, error, success, feedback, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def analyze_common_errors():
    """Analyze common errors from the learning table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT error, COUNT(*) as count FROM learning WHERE error IS NOT NULL GROUP BY error ORDER BY count DESC LIMIT 3")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return "No common errors found in past executions."
    common_errors = "\n".join([f"Error: {row['error']} (occurred {row['count']} times)" for row in rows])
    return f"Common errors in past executions:\n{common_errors}"

def save_documentation(title, content, source, url=None):
    """Save a documentation entry to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO documentation (title, content, source, url, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, content, source, url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_documentation(query=None):
    """Get documentation entries from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if query:
        cursor.execute("SELECT * FROM documentation WHERE content LIKE ?", (f"%{query}%",))
    else:
        cursor.execute("SELECT * FROM documentation")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
