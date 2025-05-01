import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename="billy.log", format="%(asctime)s %(levelname)s:%(message)s")

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
    logging.debug(f"Loaded {len(rows)} memory entries from database")
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
    logging.info(f"Saved memory entry: [Category: {category}] Prompt: {prompt}")

def get_memory_context(category=None):
    """Get memory context for a specific category."""
    memory = load_memory()
    if not memory:
        return "No past interactions found."
    context = "\nPast interactions:\n"
    for entry in memory:
        entry_category = entry.get("category", "general")
        if category is None or entry_category == category:
            context += f"[{entry_category}] User: {entry['prompt']}\nBilly: {entry['response']}\n"
            if "tool_code" in entry and "tool_result" in entry and entry["tool_code"] and entry["tool_result"]:
                context += f"[Tool] Code: {entry['tool_code']}\n[Tool] Result: {entry['tool_result']}\n"
    result = context if context != "\nPast interactions:\n" else f"No past interactions found for category '{category}'."
    logging.debug(f"Retrieved memory context for category '{category}': {result[:100]}...")
    return result

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
    logging.info(f"Saved learning entry: Prompt: {prompt}, Success: {success}")

def analyze_common_errors():
    """Analyze common errors from the learning table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT error, COUNT(*) as count FROM learning WHERE error IS NOT NULL GROUP BY error ORDER BY count DESC LIMIT 3")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        logging.info("No common errors found in learning table")
        return "No common errors found in past executions."
    common_errors = "\n".join([f"Error: {row['error']} (occurred {row['count']} times)" for row in rows])
    result = f"Common errors in past executions:\n{common_errors}"
    logging.info("Analyzed common errors from learning table")
    return result

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
    logging.info(f"Saved documentation entry: {title}")

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
    logging.debug(f"Retrieved {len(rows)} documentation entries for query: {query}")
    return [dict(row) for row in rows]