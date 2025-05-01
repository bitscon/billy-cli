import requests
import json
import os
import subprocess
import sqlite3
from datetime import datetime
from googlesearch import search
from github import Github
from flask import Flask, request, render_template, jsonify, redirect, url_for
from xml.etree import ElementTree as ET

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

# Load connectors
connectors = load_connectors()
NEXTCLOUD_URL = connectors.get("nextcloud", {}).get("url", "")
NEXTCLOUD_USERNAME = connectors.get("nextcloud", {}).get("username", "")
NEXTCLOUD_PASSWORD = connectors.get("nextcloud", {}).get("password", "")
GITHUB_TOKEN = connectors.get("github", {}).get("api_key", "")
g = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None
REPO_NAME = "bitscon/billy"

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

def save_learning_entry(prompt, response, error, success, feedback):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO learning (prompt, response, error, success, feedback, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (prompt, response, error, success, feedback, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def analyze_common_errors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT error, COUNT(*) as count FROM learning WHERE error IS NOT NULL GROUP BY error ORDER BY count DESC LIMIT 3")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return "No common errors found in past executions."
    common_errors = "\n".join([f"Error: {row['error']} (occurred {row['count']} times)" for row in rows])
    return f"Common errors in past executions:\n{common_errors}"

def get_repo_contents(repo, path=""):
    """Recursively fetch all files and their contents from the GitHub repository."""
    if not g:
        return "GitHub API token not configured. Please set it in the admin panel at /admin."
    try:
        contents = repo.get_contents(path)
        result = []
        for content in contents:
            if content.type == "dir":
                # Recursively fetch contents of directories
                result.extend(get_repo_contents(repo, content.path))
            else:
                try:
                    # Fetch file content
                    file_content = content.decoded_content.decode()
                    result.append({
                        "path": content.path,
                        "content": file_content
                    })
                except Exception as e:
                    result.append({
                        "path": content.path,
                        "content": f"Error fetching file content: {str(e)}"
                    })
        return result
    except Exception as e:
        return f"Error fetching repository contents: {str(e)}"

def get_own_code():
    """Fetch all files in the repository and return their contents."""
    if not g:
        return "GitHub API token not configured. Please set it in the admin panel at /admin."
    try:
        repo = g.get_repo(REPO_NAME)
        files = get_repo_contents(repo)
        if isinstance(files, str):
            return files  # Error message
        # Format the output for display
        output = "Here are the contents of my repository:\n"
        for file in files:
            output += f"\nFile: {file['path']}\n```python\n{file['content']}\n```"
        return output
    except Exception as e:
        return f"Error fetching code from GitHub: {str(e)}"

def create_file_in_repo(file_path, content, commit_message="Created file via Billy"):
    """Create a file in the GitHub repository."""
    if not g:
        return "GitHub API token not configured. Please set it in the admin panel at /admin."
    try:
        repo = g.get_repo(REPO_NAME)
        repo.create_file(file_path, commit_message, content)
        return f"Successfully created {file_path} in the repository."
    except Exception as e:
        return f"Error creating file in GitHub: {str(e)}"

def update_file_in_repo(file_path, content, commit_message="Updated file via Billy"):
    """Update a file in the GitHub repository."""
    if not g:
        return "GitHub API token not configured. Please set it in the admin panel at /admin."
    try:
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(file_path)
        repo.update_file(file_path, commit_message, content, contents.sha)
        return f"Successfully updated {file_path} in the repository."
    except Exception as e:
        return f"Error updating file in GitHub: {str(e)}"

def delete_file_in_repo(file_path, commit_message="Deleted file via Billy"):
    """Delete a file in the GitHub repository."""
    if not g:
        return "GitHub API token not configured. Please set it in the admin panel at /admin."
    try:
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(file_path)
        repo.delete_file(file_path, commit_message, contents.sha)
        return f"Successfully deleted {file_path} from the repository."
    except Exception as e:
        return f"Error deleting file in GitHub: {str(e)}"

def analyze_repo_for_improvements():
    """Analyze the repository and suggest improvements (placeholder for future autonomy)."""
    if not g:
        return "GitHub API token not configured. Please set it in the admin panel at /admin."
    try:
        repo = g.get_repo(REPO_NAME)
        files = get_repo_contents(repo)
        if isinstance(files, str):
            return files  # Error message
        # Basic analysis: Check for missing README.md as an example
        has_readme = any(file["path"].lower() == "readme.md" for file in files)
        suggestions = []
        if not has_readme:
            suggestions.append("I noticed there's no README.md in the repository. Adding one could help document the project. Would you like me to create a README.md with a basic description?")
        return "\n".join(suggestions) if suggestions else "No immediate improvements suggested for the repository."
    except Exception as e:
        return f"Error analyzing repository: {str(e)}"

def save_documentation(title, content, source, url=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO documentation (title, content, source, url, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, content, source, url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_documentation(query=None):
    # First, try local database
    conn = get_db_connection()
    cursor = conn.cursor()
    if query:
        cursor.execute("SELECT * FROM documentation WHERE content LIKE ?", (f"%{query}%",))
    else:
        cursor.execute("SELECT * FROM documentation")
    rows = cursor.fetchall()
    conn.close()
    local_docs = [dict(row) for row in rows]

    # Then, fetch from Nextcloud using WebDAV PROPFIND
    if NEXTCLOUD_URL and NEXTCLOUD_USERNAME and NEXTCLOUD_PASSWORD:
        try:
            # Construct the WebDAV PROPFIND request
            url = f"{NEXTCLOUD_URL}/remote.php/dav/files/{NEXTCLOUD_USERNAME}/"
            headers = {
                "Depth": "1",
                "Content-Type": "application/xml"
            }
            body = '''
            <?xml version="1.0" encoding="UTF-8"?>
            <d:propfind xmlns:d="DAV:">
                <d:prop>
                    <d:displayname/>
                    <d:resourcetype/>
                </d:prop>
            </d:propfind>
            '''
            response = requests.request(
                "PROPFIND",
                url,
                auth=(NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD),
                headers=headers,
                data=body
            )
            if response.status_code == 207:  # Multi-status response
                # Parse the XML response
                root = ET.fromstring(response.content)
                ns = {"d": "DAV:"}
                files = []
                for resp in root.findall(".//d:response", ns):
                    href = resp.find("d:href", ns).text
                    displayname = resp.find(".//d:displayname", ns)
                    resourcetype = resp.find(".//d:resourcetype", ns)
                    # Skip if it's a collection (directory)
                    if not resourcetype.find("d:collection", ns):
                        name = displayname.text if displayname is not None else href.split("/")[-1]
                        if query and query.lower() in name.lower():
                            files.append({"title": name, "content": "Stored in Nextcloud", "source": "nextcloud", "url": href})
                local_docs.extend(files)
            else:
                print(f"Nextcloud fetch failed: Status {response.status_code}")
        except Exception as e:
            print(f"Nextcloud fetch failed: {str(e)}")

    return local_docs

def web_search(query, num_results=3):
    try:
        results = []
        for url in search(query, num_results=num_results):
            results.append(url)
            save_documentation(f"Web Search: {query}", f"Found at {url}", "online", url)
        return "\n".join([f"- {url}" for url in results])
    except Exception as e:
        return f"Web search failed: {str(e)}"

def query_ollama(prompt, include_memory=False, memory_category=None):
    url = "http://localhost:11434/api/generate"
    tone_instruction = f"Respond in a {TONE} tone."
    memory_context = get_memory_context(memory_category) if include_memory else ""
    doc_context = ""
    docs = get_documentation(prompt)
    if docs:
        doc_context = "\nRelevant Documentation:\n" + "\n".join([f"{doc['title']}: {doc['content'][:200]}" for doc in docs])
    full_prompt = f"{tone_instruction}\n{memory_context}\n{doc_context}\nUser: {prompt}"
    
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
        # Write the code to a temporary file
        with open("/tmp/temp_code.py", "w") as f:
            f.write(code)
        # Run the code in a Docker container with subprocess timeout
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", "/tmp/temp_code.py:/app/temp_code.py",
                "--security-opt", "no-new-privileges",
                "--cap-drop", "ALL",
                "--network", "none",
                "billy-python-sandbox",
                "python", "temp_code.py"
            ],
            capture_output=True,
            text=True,
            timeout=5  # Timeout handled by subprocess
        )
        if result.stderr:
            # Log the error in the learning table
            save_learning_entry("Code execution", code, result.stderr, False, "Execution failed")
            # If there's an error, query Ollama for a fix
            error_message = result.stderr
            debug_prompt = f"The following Python code failed with this error:\n\nCode:\n```python\n{code}\n```\n\nError:\n{error_message}\n\nPlease analyze the error, explain why it occurred, and suggest a corrected version of the code."
            fix_suggestion = query_ollama(debug_prompt)
            return f"Error: {error_message}\n\nDebug Suggestion:\n{fix_suggestion}"
        # Log successful execution
        save_learning_entry("Code execution", code, None, True, "Execution succeeded")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        save_learning_entry("Code execution", code, "Timeout", False, "Execution timed out")
        return "Error: Code execution timed out after 5 seconds."
    except Exception as e:
        save_learning_entry("Code execution", code, str(e), False, "Execution failed")
        return f"Error: {str(e)}"
    finally:
        # Clean up the temporary file
        if os.path.exists("/tmp/temp_code.py"):
            os.remove("/tmp/temp_code.py")

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
        elif user_input.lower() == "analyze my errors":
            response = analyze_common_errors()
            category = "learning"
        elif user_input.lower() == "show my code":
            response = get_own_code()
            category = "self-awareness"
        elif user_input.lower() == "analyze my repo":
            response = analyze_repo_for_improvements()
            category = "self-awareness"
        elif user_input.lower().startswith("create file "):
            file_path = user_input[len("create file "):].strip()
            content = "This is a new file created by Billy."
            response = create_file_in_repo(file_path, content, f"Created {file_path} via Billy")
            category = "repo-management"
        elif user_input.lower().startswith("update file "):
            parts = user_input[len("update file "):].strip().split(" with content ")
            if len(parts) != 2:
                response = "Please use the format: 'update file <file_path> with content <content>'"
            else:
                file_path, content = parts
                response = update_file_in_repo(file_path, content, f"Updated {file_path} via Billy")
            category = "repo-management"
        elif user_input.lower().startswith("delete file "):
            file_path = user_input[len("delete file "):].strip()
            response = delete_file_in_repo(file_path, f"Deleted {file_path} via Billy")
            category = "repo-management"
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
                # Introduce a deliberate syntax error if requested
                code_start = response.index("```python") + 9
                code_end = response.index("```", code_start)
                code = response[code_start:code_end].strip()
                if "include a syntax error" in user_input.lower():
                    # Introduce a missing colon after the function definition
                    code_lines = code.split("\n")
                    if code_lines and "def " in code_lines[0]:
                        code_lines[0] = code_lines[0].replace("):", ")")  # Remove colon
                        code = "\n".join(code_lines)
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

@app.route("/admin.html", methods=["GET"])
def admin_redirect():
    return redirect(url_for("admin"))

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