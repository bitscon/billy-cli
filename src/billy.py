import logging
import subprocess
import os
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from config import Config
from database import load_memory, save_memory, analyze_common_errors, get_memory_context, prune_old_data
from database import initialize_database
initialize_database()
from database import initialize_database
initialize_database()
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
    """Get the last 'count' user inputs from the database, optionally filtered by criteria."""
    memory = load_memory(limit=count + 1)  # +1 to exclude the current request
    if not memory:
        return "I don't have any recent conversation to recall. What's on your mind?"
    
    recent_inputs = [entry["prompt"] for entry in memory[:-1]][-count:]  # Exclude the current request
    if not recent_inputs:
        return "I don't have any recent conversation to recall. What's on your mind?"
    
    if filter_criteria:
        filtered_inputs = [req for req in recent_inputs if any(criterion in req.lower() for criterion in filter_criteria)]
        if not filtered_inputs:
            return "I couldn't find any requests matching your criteria in our recent chat history."
        return "\n".join([f"- {input}" for input in filtered_inputs[-count:]])
    
    return "\n".join([f"- {input}" for input in recent_inputs])

def detect_intent_and_extract_params(user_input, recent_inputs):
    """Use the LLM to detect the intent of the user input and extract parameters."""
    # Include recent conversation context in the prompt
    recent_context = "\n".join([f"- {input}" for input in recent_inputs[:-1]]) if recent_inputs else "No previous conversation."
    intent_prompt = (
        "Classify the intent of the following user input and extract relevant parameters, considering the recent conversation context. "
        "Recent conversation:\n"
        f"{recent_context}\n\n"
        "Return the result strictly in the format: '<intent>:<parameters>'. "
        "For example: 'recall_conversation:1:joke,funny' or 'general:'. "
        "If the intent is a recall request (e.g., asking about past conversation, what was asked, or history), use 'recall_conversation'. "
        "Possible intents include: "
        "- recall_conversation (parameters: count, criteria1,criteria2,...; e.g., '1:joke,funny' for recalling 1 entry related to jokes or funny topics)"
        "- save_tool (parameters: none)"
        "- run_code (parameters: code)"
        "- analyze_errors (parameters: none)"
        "- show_code (parameters: none)"
        "- analyze_repo (parameters: none)"
        "- create_file (parameters: file_path,content)"
        "- update_file (parameters: file_path,content)"
        "- delete_file (parameters: file_path)"
        "- web_search (parameters: query)"
        "- general (parameters: none)"
        "If the intent doesn't match any of the above, use 'general'. "
        "Ensure the output format is correct and avoid additional text. "
        f"Input: '{user_input}'"
    )
    intent_response = query_ollama(intent_prompt)
    logging.debug(f"Intent response from LLM: {intent_response}")
    
    # Fallback if LLM fails to provide a valid response
    if not intent_response or ":" not in intent_response:
        logging.warning(f"LLM intent detection failed, falling back to 'general' intent: {intent_response}")
        return "general", []

    # Parse the response
    parts = intent_response.split(":", 1)
    intent = parts[0].strip()
    params = parts[1].split(",") if len(parts) > 1 and parts[1] else []
    params = [param.strip() for param in params if param.strip()]  # Clean up parameters

    # Fallback for recall requests if LLM misclassifies
    user_input_lower = user_input.lower()
    recall_keywords = ["what did i ask", "last thing i asked", "recall our conversation", "look back in our chat", "recently asked"]
    if any(keyword in user_input_lower for keyword in recall_keywords) and intent != "recall_conversation":
        logging.warning(f"LLM missed recall intent, falling back to recall_conversation: {user_input}")
        intent = "recall_conversation"
        # Default to recalling 1 entry, look for "funny" or "joke" in the input as criteria
        count = "3" if "last 3" in user_input_lower else "1"
        criteria = []
        if "funny" in user_input_lower or "joke" in user_input_lower:
            criteria = ["funny", "joke"]
        params = [count] + criteria

    return intent, params

@app.route("/", methods=["GET", "POST"])
def chat():
    global last_code, last_execution_result

    chat_history = []
    memory = load_memory(limit=50)  # Limit to recent entries for display
    tools = [entry for entry in memory if entry.get("category") == "tool"]
    for entry in memory:
        chat_history.append({"role": "user", "content": entry["prompt"]})
        chat_history.append({"role": "billy", "content": entry["response"]})

    if request.method == "POST":
        user_input = request.form["prompt"].strip()
        if not user_input:
            return render_template("index.html", chat_history=chat_history, tone=config.TONE, tools=tools)

        # Get recent inputs from the database
        recent_inputs = [entry["prompt"] for entry in memory]

        # Initialize response and category
        response = None
        category = "general"

        # Detect intent using the LLM
        intent, params = detect_intent_and_extract_params(user_input, recent_inputs)

        if intent == "recall_conversation":
            count = int(params[0]) if params and params[0].isdigit() else 1
            criteria = params[1:] if len(params) > 1 else None
            if criteria and criteria[0]:
                response = get_recent_conversation(count, criteria)
            else:
                response = get_recent_conversation(count)
            category = "memory"

        elif intent == "save_tool":
            if last_code and last_execution_result:
                save_memory("Saved tool", "Tool saved for future use.", "tool", last_code, last_execution_result)
                response = "I’ve saved that tool in my toolbox for later!"
            else:
                response = "I don’t have a recent tool to save. Ask me to write and run some code first!"
            category = "tool"

        elif intent == "run_code":
            if params:
                code = params[0]
                execution_result = execute_python_code(code)
                response = f"Running saved code:\n```python\n{code}\n```\n\nExecution Result:\n{execution_result}"
                last_code = code
                last_execution_result = execution_result
            else:
                response = "I couldn't find any code to run in your request. Please provide the code you'd like to execute."
            category = "coding"

        elif intent == "analyze_errors":
            response = analyze_common_errors()
            category = "learning"

        elif intent == "show_code":
            response = get_own_code()
            category = "self-awareness"

        elif intent == "analyze_repo":
            response = analyze_repo_for_improvements()
            category = "self-awareness"

        elif intent == "create_file":
            if len(params) >= 2:
                file_path, content = params[0], params[1]
                response = create_file_with_test(file_path, content, f"Created {file_path} via Billy")
            else:
                response = "Please provide both a file path and content to create a file (e.g., 'create file test.txt with content Hello World')."
            category = "repo-management"

        elif intent == "update_file":
            if len(params) >= 2:
                file_path, content = params[0], params[1]
                response = update_file_with_test(file_path, content, f"Updated {file_path} via Billy")
            else:
                response = "Please provide both a file path and content to update a file (e.g., 'update file test.txt with content Updated content')."
            category = "repo-management"

        elif intent == "delete_file":
            if params:
                file_path = params[0]
                response = delete_file_with_commit(file_path, f"Deleted {file_path} via Billy")
            else:
                response = "Please provide a file path to delete (e.g., 'delete file test.txt')."
            category = "repo-management"

        elif intent == "web_search":
            if params:
                search_query = params[0]
                web_results = web_search(search_query)
                user_input = f"{user_input}\nWeb search results:\n{web_results}"
                response = query_ollama(user_input)
            else:
                response = "I couldn't identify a search query in your request. Please specify what you'd like to search for."
            category = "research"

        else:
            # General intent: let the LLM handle the response
            include_memory = "recall" in user_input.lower()
            memory_category = None
            if include_memory:
                if "coding" in user_input.lower():
                    memory_category = "coding"
                elif "research" in user_input.lower():
                    memory_category = "research"
                elif "tool" in user_input.lower():
                    memory_category = "tool"
                user_input = user_input.replace("recall coding", "").replace("recall research", "").replace("recall tool", "").replace("recall past", "").strip()

            response = query_ollama(user_input, include_memory, memory_category)

            # Check if the response contains Python code that might need execution
            if "```python" in response:
                code_start = response.index("```python") + 9
                code_end = response.index("```", code_start)
                code = response[code_start:code_end].strip()
                if "include a syntax error" in user_input.lower():
                    # Introduce a deliberate syntax error if requested
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
            category = "coding" if "code" in user_input.lower() or "write a" in user_input.lower() else "general"

        # Save the conversation to memory
        save_memory(user_input, response, category)

        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "billy", "content": response})

        # Prune old data periodically (e.g., every 100 requests)
        if len(chat_history) % 100 == 0:
            prune_old_data()

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