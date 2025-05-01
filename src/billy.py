from flask import Flask, request, render_template, jsonify, redirect, url_for
from config import Config
from database import load_memory, save_memory, analyze_common_errors
from github_manager import get_local_repo_contents, analyze_repo_for_improvements, get_own_code
from file_manager import create_file_with_test, update_file_with_test, delete_file_with_commit
from web_search import web_search
from ollama import query_ollama

app = Flask(__name__)
config = Config()

# Store the last executed code and result for potential saving
last_code = None
last_execution_result = None

@app.route("/", methods=["GET", "POST"])
def chat():
    global last_code, last_execution_result
    chat_history = []
    memory = load_memory()
    tools = [entry for entry in memory if entry.get("category") == "tool"]
    for entry in memory:
        chat_history.append({"role": "user", "content": entry["prompt"]})
        chat_history.append({"role": "billy", "content": entry["response"]})

    if request.method == "POST":
        user_input = request.form["prompt"].strip()
        if not user_input:
            return render_template("index.html", chat_history=chat_history, tone=config.TONE, tools=tools)

        if user_input.lower() == "save this tool":
            if last_code and last_execution_result:
                save_memory("Saved tool", "Tool saved for future use.", "tool", last_code, last_execution_result)
                response = "I’ve saved that tool in my toolbox for later!"
            else:
                response = "I don’t have a recent tool to save. Ask me to write and run some code first!"
            category = "tool"
        elif user_input.lower().startswith("run this code:"):
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
            response = create_file_with_test(file_path, content, f"Created {file_path} via Billy")
            category = "repo-management"
        elif user_input.lower().startswith("update file "):
            parts = user_input[len("update file "):].strip().split(" with content ")
            if len(parts) != 2:
                response = "Please use the format: 'update file <file_path> with content <content>'"
            else:
                file_path, content = parts
                response = update_file_with_test(file_path, content, f"Updated {file_path} via Billy")
            category = "repo-management"
        elif user_input.lower().startswith("delete file "):
            file_path = user_input[len("delete file "):].strip()
            response = delete_file_with_commit(file_path, f"Deleted {file_path} via Billy")
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

    return render_template("index.html", chat_history=chat_history, tone=config.TONE, tools=tools)

@app.route("/admin.html", methods=["GET"])
def admin_redirect():
    return redirect(url_for("admin"))

@app.route("/admin", methods=["GET"])
def admin():
    from database import get_db_connection
    connectors_list = load_connectors()
    return render_template("admin.html", connectors=connectors_list.values())

@app.route("/admin/update_connector", methods=["POST"])
def update_connector():
    from database import get_db_connection
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
    global config
    data = request.get_json()
    new_tone = data.get("tone")
    if new_tone in ["casual", "formal", "humorous"]:
        config.TONE = new_tone
        config.save_config()
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