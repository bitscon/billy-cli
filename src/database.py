import sqlite3
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename="billy.log", format="%(asctime)s %(levelname)s:%(message)s")

def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect("/home/billybs/Projects/billy/db/billy.db")
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initialize the database with indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Add indexes for memory table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_category ON memory(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory(timestamp)")
    # Add indexes for learning table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_learning_error ON learning(error)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_learning_timestamp ON learning(timestamp)")
    # Add indexes for documentation table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documentation_content ON documentation(content)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documentation_timestamp ON documentation(timestamp)")
    conn.commit()
    conn.close()
    logging.info("Database indexes initialized")

def load_memory(limit=100, category=None, since=None):
    """Load memory entries from the database with pagination and filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM memory"
    params = []
    conditions = []
    
    if category:
        conditions.append("category = ?")
        params.append(category)
    if since:
        conditions.append("timestamp >= ?")
        params.append(since.strftime("%Y-%m-%d %H:%M:%S"))
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
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
    memory = load_memory(limit=50, category=category)
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
    """Analyze common errors from the learning table, including trends over time."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the top 3 most frequent errors
    cursor.execute("SELECT error, COUNT(*) as count FROM learning WHERE error IS NOT NULL GROUP BY error ORDER BY count DESC LIMIT 3")
    frequent_errors = cursor.fetchall()
    
    # Get error trends over the last 7 days
    since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT error, COUNT(*) as count, MIN(timestamp) as first_occurrence FROM learning WHERE error IS NOT NULL AND timestamp >= ? GROUP BY error ORDER BY count DESC LIMIT 3", (since,))
    recent_trends = cursor.fetchall()
    
    conn.close()
    
    if not frequent_errors and not recent_trends:
        logging.info("No common errors found in learning table")
        return "No common errors found in past executions."
    
    result = "Common errors in past executions:\n"
    if frequent_errors:
        result += "Top 3 most frequent errors overall:\n"
        result += "\n".join([f"- {row['error']} (occurred {row['count']} times)" for row in frequent_errors])
    
    if recent_trends:
        result += "\n\nError trends in the last 7 days:\n"
        result += "\n".join([f"- {row['error']} (occurred {row['count']} times, first seen at {row['first_occurrence']})" for row in recent_trends])
    
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

def get_documentation(query=None, limit=50):
    """Get documentation entries from the database with pagination."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if query:
        cursor.execute("SELECT * FROM documentation WHERE content LIKE ? LIMIT ?", (f"%{query}%", limit))
    else:
        cursor.execute("SELECT * FROM documentation LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    logging.debug(f"Retrieved {len(rows)} documentation entries for query: {query}")
    return [dict(row) for row in rows]

def prune_old_data(age_days=30, max_records=1000):
    """Prune old data from learning and documentation tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Prune learning table
    cutoff_date = (datetime.now() - timedelta(days=age_days)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM learning WHERE timestamp < ? AND (SELECT COUNT(*) FROM learning) > ?", (cutoff_date, max_records))
    logging.info(f"Pruned old entries from learning table: {cursor.rowcount} rows deleted")
    
    # Prune documentation table
    cursor.execute("DELETE FROM documentation WHERE timestamp < ? AND (SELECT COUNT(*) FROM documentation) > ?", (cutoff_date, max_records))
    logging.info(f"Pruned old entries from documentation table: {cursor.rowcount} rows deleted")
    
    conn.commit()
    conn.close()

# Initialize the database on startup
initialize_database()