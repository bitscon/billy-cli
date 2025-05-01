import logging
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from config import Config
from database import load_memory, save_memory, analyze_common_errors
from github_manager import get_local_repo_contents, analyze_repo_for_improvements, get_own_code
from file_manager import create_file_with_test, update_file_with_test, delete_file_with_commit
from web_search import web_search
from ollama import query_ollama

app = Flask(__name__)
app.secret_key = "your-secret-key-here"  # Ensure this is a secure, unique key
app.config["SESSION_TYPE"] = "filesystem"  # Use filesystem for session storage
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename="billy.log", format="%(asctime)s %(levelname)s:%(message)s")

config = Config()

# Store the last executed code and result for potential saving
last_code = None
last_execution_result = None

def execute_python_code(code):
    """Execute Python code in the Docker sandbox."""
    try:
        # Write the code to a temporary file
        with open("/tmp/temp_code.py", "w") as f:
            f.write(code)
        # Run the code in the Docker container
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

def get_recent_conversation(count=3, filter_criteria=None):
    """Get the last 'count' user inputs from session, optionally filtered by criteria."""
    recent_inputs = session.get("recent_inputs", [])
    logging.debug(f"Recent inputs from session: {recent_inputs}")
    if not recent_inputs:
        return "I don't have any recent conversation to recall. What's on your mind?"
    
    if filter_criteria:
        filtered_inputs = [req for req in recent_inputs if any(criterion in req.lower() for criterion in filter_criteria)]
        if not filtered_inputs:
            return "I couldn't find any requests matching your criteria in our recent chat history."
        return "\n".join([f"- {input}" for input in filtered_inputs[-count:]])
    
    return "\n".join([f"- {input}" for input in recent_inputs[-count:]])

@app.route("/", methods=["GET", "POST"])
def chat():
    global last_code, last_execution_result

    # Initialize session if not already set
    if "recent_inputs" not in session:
        session["recent_inputs"] = []
        logging.debug("Initialized session['recent_inputs'] as empty list")

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

        # Store the user input in session
        recent_inputs = session.get("recent_inputs", [])
        recent_inputs.append(user_input)
        if len(recent_inputs) > 3:
            recent_inputs.pop(0)
        session["recent_inputs"] = recent_inputs
        logging.debug(f"Updated session['recent_inputs']: {session['recent_inputs']}")

        # Initialize response and category
        response = None
        category = "general"

        # Use LLM to detect intent
        user_input_lower = user_input.lower()
        recall_intent_prompt = (
            f"Determine if the following user input is a request to recall recent conversation history. "
            f"If it is, specify the number of items to recall (default to 1 if not specified) and any specific criteria (e.g., 'funny', 'joke'). "
            f"Return the result in the format: 'recall:<number>:<criteria1>,<criteria2>'. "
            f"If it's not a recall request, return 'no_recall'. Input: '{user_input}'"
        )
        intent_response = query_ollama(recall_intent_prompt)
        logging.debug(f"Intent response from LLM: {intent_response}")

        if intent_response.startswith("recall:"):
            parts = intent_response.split(":")
            recall_count = int(parts[1]) if parts[1].isdigit() else 1
            criteria = parts[2].split(",") if len(parts) > 2 and parts[2] else None
            if criteria and criteria[0]:
                response = get_recent_conversation(recall_count, criteria)
            else:
                response = get_recent_conversation(recall_count)
            category = "memory"

        elif user_input_lower == "save this tool":
            if last_code and last_execution_result:
                save_memory("Saved tool", "Tool saved for future use.", "tool", last_code, last_execution_result)
                response = "I’ve saved that tool in my toolbox for later!"
            else:
                response = "I don’t have a recent tool to save. Ask me to write and run some code first!"
            category = "tool"

        elif user_input_lower.startswith("run this code:"):
            code = user_input[14:].strip()
            execution_result = execute_python_code(code)
            response = f"Running saved code:\n```python\n{code}\n```\n\nExecution Result:\n{execution_result}"
            last_code = code
            last_execution_result = execution_result
            category = "coding"

        elif user_input_lower == "analyze my errors":
            response = analyze_common_errors()
            category = "learning"

        elif user_input_lower == "show my code":
            response = get_own_code()
            category = "self-awareness"

        elif user_input_lower == "analyze my repo":
            response = analyze_repo_for_improvements()
            category = "self-awareness"

        elif user_input_lower.startswith("create file "):
            file_path = user_input[len("create file "):].strip()
            content = "This is a new file created by Billy."
            response = create_file_with_test(file_path, content, f"Created {file_path} via Billy")
            category = "repo-management"

        elif user_input_lower.startswith("update file "):
            parts = user_input[len("update file "):].strip().split(" with content ")
            if len(parts) != 2:
                response = "Please use the format: 'update file <file_path> with content <content>'"
            else:
                file_path, content = parts
                response = update_file_with_test(file_path, content, f"Updated {file_path} via Billy")
            category = "repo-management"

        elif user_input_lower.startswith("delete file "):
            file_path = user_input[len("delete file "):].strip()
            response = delete_file_with_commit(file_path, f"Deleted {file_path} via Billy")
            category = "repo-management"

        else:
            if "code" in user_input_lower or "write a" in user_input_lower:
                category = "coding"
            elif "search for" in user_input_lower:
                category = "research"

            include_memory = False
            memory_category = None
            if "recall" in user_input_lower:
                include_memory = True
                if "coding" in user_input_lower:
                    memory_category = "coding"
                elif "research" in user_input_lower:
                    memory_category = "research"
                elif "tool" in user_input_lower:
                    memory_category = "tool"
                user_input = user_input.replace("recall coding", "").replace("recall research", "").replace("recall tool", "").replace("recall past", "").strip()

            web_results = ""
            if "search for" in user_input_lower:
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
                if "include a syntax error" in user_input_lower:
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

        # Save the conversation to memory
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