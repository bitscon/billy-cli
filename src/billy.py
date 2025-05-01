import requests
import json
import os
import subprocess
import sqlite3
from datetime import datetime
from googlesearch import search
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Database connection
def get_db_connection():
    conn = sqlite3.connect("/home/billybs/Projects/billy/db/billy.db")
    conn.row_factory = sqlite3.Row
    return conn

# Load connectors from database
def load_connectors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connectors")
    rows = cursor.fetchall()
    conn.close()
    connectors = {}
    for row in rows:
        connectors[row["name"]] = dict(row)
    return connectors

# Load configuration
def load_config():
    with open("src/config.json", "r") as config_file:
        return json.load(config_file)

def save_config(config):
    with open("src/config.json", "w") as config_file:
        json.dump(config, config_file, indent=4)

config = load_config()
TONE = config["tone"]

def load_memory():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memory")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_memory(prompt, response, category="general", tool_code=None, tool_result=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO memory (prompt, response, category, tool_code, tool_result, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (prompt, response, category, tool_code, tool_result, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_memory_context(category=None):
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

def web_search(query, num_results=3):
    try:
        results = []
        for url in search(query, num_results=num_results):
            results.append(url)
        return "\n".join([f"- {url}" for url in results])
    except Exception as e:
        return f"Web search failed: {str(e)}"

def query_ollama(prompt, include_memory=False, memory_category=None):
    url = "http://localhost:11434/api/generate"
    tone_instruction = f"Respond in a {TONE} tone."
    memory_context = get_memory_context(memory_category) if include_memory else ""
    full_prompt = f"{tone_instruction}\n{memory_context}\nUser: {prompt}"
    
    payload = {
        "model": "mistral:7b-instruct-v0.3-q4_0",
        "prompt": full_prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return json.loads(response.text)["response"]
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Request failed: {str(e)}"

def execute_python_code(code):
    try:
        with open("temp_code.py", "w") as f:
            f.write(code)
        result = subprocess.run(
            ["python3", "temp_code.py"],
            capture_output=True,
            text=True,
            timeout=5
        )
        os.remove("temp_code.py")
        if result.stderr:
            return f"Error: {result.stderr}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out after 5 seconds."
    except Exception as e:
        return f"Error: {str(e)}"

# Store the last executed code and result for potential saving
last_code = None
last_execution_result = None

@app.route("/", methods=["GET", "POST"])
def chat():
    global TONE, last_code, last_execution_result
    chat_history = []
    memory = load_memory()
    tools = [entry for entry in memory if entry.get("category") == "tool"]
    for entry in memory:
        chat_history.append({"role": "user", "content": entry["prompt"]})
        chat_history.append({"role": "billy", "content": entry["response"]})

    if request.method == "POST":
        user_input = request.form["prompt"].strip()
        if not user_input:
            return render_template("index.html", chat_history=chat_history, tone=TONE, tools=tools)

        if "save this tool" in user_input.lower():
            if last_code and last_execution_result:
                save_memory("Saved tool", "Tool saved for future use.", "tool", last_code, last_execution_result)
                response = "I’ve saved that tool in my toolbox for later!"
            else:
                response = "I don’t have a recent tool to save. Ask me to write and run some code first!"
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "billy", "content": response})
            return render_template("index.html", chat_history=chat_history, tone=TONE, tools=tools)

        if user_input.lower().startswith("run this code:"):
            code = user_input[14:].strip()
            execution_result = execute_python_code(code)
            response = f"Running saved code:\n```python\n{code}\n```\n\nExecution Result:\n{execution_result}"
            last_code = code
            last_execution_result = execution_result
            category = "coding"
        else:
            category = "general"
            if "code" in user_input.lower() or "write a" in user_input.lower():
                category = "coding"
            elif "search for" in user_input.lower():
                category = "research"

            include_memory = False
            memory_category = None
            if "recall" in user_input.lower():
                include_memory = True
                if "coding" in user_input.lower():
                    memory_category = "coding"
                elif "research" in user_input.lower():
                    memory_category = "research"
                elif "tool" in user_input.lower():
                    memory_category = "tool"
                user_input = user_input.replace("recall coding", "").replace("recall research", "").replace("recall tool", "").replace("recall past", "").strip()

            web_results = ""
            if "search for" in user_input.lower():
                search_query = user_input.replace("search for", "").strip()
                web_results = web_search(search_query)
                user_input = f"{user_input}\nWeb search results:\n{web_results}"

            response = query_ollama(user_input, include_memory, memory_category)

            execution_result = ""
            if category == "coding" and "```python" in response:
                code_start = response.index("```python") + 9
                code_end = response.index("```", code_start)
                code = response[code_start:code_end].strip()
                execution_result = execute_python_code(code)
                if execution_result:
                    response += f"\n\nExecution Result:\n{execution_result}"
                    last_code = code
                    last_execution_result = execution_result
                else:
                    last_code = None
                    last_execution_result = None

        save_memory(user_input, response, category)

        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "billy", "content": response})

    return render_template("index.html", chat_history=chat_history, tone=TONE, tools=tools)

@app.route("/admin", methods=["GET"])
def admin():
    connectors_list = load_connectors()
    return render_template("admin.html", connectors=connectors_list.values())

@app.route("/admin/update_connector", methods=["POST"])
def update_connector():
    data = request.get_json()
    id = data.get("id")
    url = data.get("url")
    username = data.get("username")
    password = data.get("password")
    api_key = data.get("api_key")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE connectors
        SET url = ?, username = ?, password = ?, api_key = ?, timestamp = ?
        WHERE id = ?
    ''', (url, username, password, api_key, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Connector updated"}), 200

@app.route("/update_tone", methods=["POST"])
def update_tone():
    global TONE
    data = request.get_json()
    new_tone = data.get("tone")
    if new_tone in ["casual", "formal", "humorous"]:
        TONE = new_tone
        config = load_config()
        config["tone"] = new_tone
        save_config(config)
        return jsonify({"message": f"Tone updated to {new_tone}"}), 200
    return jsonify({"message": "Invalid tone"}), 400

@app.route("/delete_tool", methods=["POST"])
def delete_tool():
    data = request.get_json()
    index = int(data.get("index"))
    memory = load_memory()
    tools = [entry for entry in memory if entry.get("category") == "tool"]
    if 0 <= index < len(tools):
        tool_to_delete = tools[index]
        memory.remove(tool_to_delete)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memory")  # Clear existing memory
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
                entry.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            ))
        conn.commit()
        conn.close()
        return jsonify({"message": "Tool deleted"}), 200
    return jsonify({"error": "Invalid tool index"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)