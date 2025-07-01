import logging
import subprocess
import os
import time
import datetime
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from config import Config
from database import (
    load_memory, save_memory, analyze_common_errors, get_memory_context, prune_old_data,
    initialize_database, get_db_connection
)
from github_manager import get_local_repo_contents, analyze_repo_for_improvements, get_own_code
from file_manager import create_file_with_test, update_file_with_test, delete_file_with_commit
from web_search import web_search
from ollama import query_ollama
from chroma_memory import get_semantic_memory

# Initialize DB
initialize_database()

app = Flask(__name__)
app.secret_key = "your-secret-key-here"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename="billy.log", format="%(asctime)s %(levelname)s:%(message)s")

config = Config()
last_code = None
last_execution_result = None

def execute_python_code(code):
    try:
        with open("/tmp/temp_code.py", "w") as f:
            f.write(code)
        result = subprocess.run(
            ["docker", "run", "--rm", "-v", "/tmp/temp_code.py:/app/temp_code.py",
             "--security-opt", "no-new-privileges", "--cap-drop", "ALL", "--network", "none",
             "billy-python-sandbox", "python", "temp_code.py"],
            capture_output=True, text=True, timeout=5
        )
        os.remove("/tmp/temp_code.py")
        if result.stderr:
            return f"Error: {result.stderr}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out after 5 seconds."
    except Exception as e:
        return f"Error: {str(e)}"

def detect_intent_and_extract_params(user_input, recent_inputs):
    intent_prompt = (
        f"Classify the intent of this input strictly as '<intent>:<parameters>'\nInput: '{user_input}'"
    )
    intent_response = query_ollama(intent_prompt)
    if not intent_response or ":" not in intent_response:
        return "general", []
    parts = intent_response.split(":", 1)
    intent = parts[0].strip()
    params = [p.strip() for p in parts[1].split(",") if p.strip()] if len(parts) > 1 else []
    return intent, params

@app.route("/", methods=["GET", "POST"])
def chat():
    global last_code, last_execution_result
    chat_history = []
    memory = load_memory(limit=50)
    tools = [entry for entry in memory if entry.get("category") == "tool"]

    for entry in memory:
        chat_history.append({"role": "user", "content": entry["prompt"]})
        chat_history.append({"role": "billy", "content": entry["response"]})

    if request.method == "POST":
        user_input = request.form["prompt"].strip()
        if not user_input:
            return render_template("index.html", chat_history=chat_history, tone=config.TONE, tools=tools)

        recent_inputs = [entry["prompt"] for entry in memory]
        intent, params = detect_intent_and_extract_params(user_input, recent_inputs)
        response = ""

        if intent == "general":
            memory_context = "\n".join(get_semantic_memory(user_input, n_results=3))
            prompt = f"""
You are Billy, an AI assistant with memory and context awareness.

Conversation Context:
{memory_context}

User Input:
{user_input}

Respond in a helpful, formal tone.
"""
            response = query_ollama(prompt)
        else:
            response = f"Intent {intent} handling not yet implemented."

        save_memory(user_input, response, intent)
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "billy", "content": response})

    return render_template("index.html", chat_history=chat_history, tone=config.TONE, tools=tools)

@app.route("/api/v1/generate", methods=["POST"])
def api_generate_v1():
    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    save_memory(prompt, "", "api_request")
    response_text = query_ollama(prompt)
    save_memory(prompt, response_text, "api_response")

    return jsonify({
        "model": "billy",
        "version": "v1",
        "created_at": datetime.datetime.now().isoformat(),
        "message": {"role": "assistant", "content": response_text}
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    user_prompt = data.get("messages", [{"content": ""}])[-1]["content"]
    memory_context = "\n".join(get_semantic_memory(user_prompt, n_results=3))
    prompt = f"""
You are Billy, an AI assistant with memory and context awareness.

Conversation Context:
{memory_context}

User Input:
{user_prompt}

Respond in a helpful, formal tone.
"""
    response_text = query_ollama(prompt)
    return jsonify({
        "id": "chatcmpl-xyz",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "billy",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response_text},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    })

@app.route("/update_tone", methods=["POST"])
def update_tone():
    data = request.get_json()
    new_tone = data.get("tone")
    if new_tone in ["casual", "formal", "humorous"]:
        config.TONE = new_tone
        config.save_config()
        return jsonify({"message": f"Tone updated to {new_tone}"}), 200
    return jsonify({"message": "Invalid tone"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
