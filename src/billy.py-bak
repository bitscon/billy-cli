import requests
import json
import os
from googlesearch import search
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Load configuration
def load_config():
    with open("src/config.json", "r") as config_file:
        return json.load(config_file)

def save_config(config):
    with open("src/config.json", "w") as config_file:
        json.dump(config, config_file, indent=4)

config = load_config()
TONE = config["tone"]
ELEVEN_LABS_API_KEY = config.get("eleven_labs_api_key", None)  # Placeholder for Eleven Labs API key

def load_memory():
    if os.path.exists("src/memory.json"):
        with open("src/memory.json", "r") as f:
            return json.load(f)
    return []

def save_memory(prompt, response, category="general"):
    memory = load_memory()
    memory.append({"prompt": prompt, "response": response, "category": category})
    with open("src/memory.json", "w") as f:
        json.dump(memory, f, indent=4)

def get_memory_context(category=None):
    memory = load_memory()
    if not memory:
        return "No past interactions."
    context = "\nPast interactions:\n"
    for entry in memory:
        entry_category = entry.get("category", "general")
        if category is None or entry_category == category:
            context += f"[{entry_category}] User: {entry['prompt']}\nBilly: {entry['response']}\n"
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

def text_to_speech_eleven_labs(text):
    if not ELEVEN_LABS_API_KEY:
        return {"error": "Eleven Labs API key not configured"}, 400
    # Placeholder for Eleven Labs TTS integration
    # When ready, implement the API call to Eleven Labs here
    # Example (commented out for now):
    # url = "https://api.elevenlabs.io/v1/text-to-speech/<voice-id>"
    # headers = {"xi-api-key": ELEVEN_LABS_API_KEY, "Content-Type": "application/json"}
    # payload = {"text": text, "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}}
    # response = requests.post(url, json=payload, headers=headers)
    # if response.status_code == 200:
    #     return response.content  # Audio data
    # return {"error": "Failed to generate speech"}, 500
    return {"message": "Eleven Labs TTS placeholder - not implemented yet"}, 200

@app.route("/", methods=["GET", "POST"])
def chat():
    global TONE
    chat_history = []
    memory = load_memory()
    for entry in memory:
        chat_history.append({"role": "user", "content": entry["prompt"]})
        chat_history.append({"role": "billy", "content": entry["response"]})

    if request.method == "POST":
        user_input = request.form["prompt"]
        if not user_input:
            return render_template("index.html", chat_history=chat_history, tone=TONE)

        # Determine category
        category = "general"
        if "code" in user_input.lower() or "write a" in user_input.lower():
            category = "coding"
        elif "search for" in user_input.lower():
            category = "research"

        # Check for memory recall
        include_memory = False
        memory_category = None
        if "recall" in user_input.lower():
            include_memory = True
            if "coding" in user_input.lower():
                memory_category = "coding"
            elif "research" in user_input.lower():
                memory_category = "research"
            user_input = user_input.replace("recall coding", "").replace("recall research", "").replace("recall past", "").strip()

        # Handle web search
        web_results = ""
        if "search for" in user_input.lower():
            search_query = user_input.replace("search for", "").strip()
            web_results = web_search(search_query)
            user_input = f"{user_input}\nWeb search results:\n{web_results}"

        # Query Ollama
        response = query_ollama(user_input, include_memory, memory_category)
        save_memory(user_input, response, category)

        # Update chat history
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "billy", "content": response})

    return render_template("index.html", chat_history=chat_history, tone=TONE)

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

@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    return text_to_speech_eleven_labs(text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
