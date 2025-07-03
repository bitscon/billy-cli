from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import json
import time

app = Flask(__name__)
CORS(app)

# --- MODIFIED ---
# Using the older /api/generate endpoint for compatibility
OLLAMA_API_URL = "http://localhost:11434/api/generate" 
OLLAMA_MODELS_URL = "http://localhost:11434/api/tags"

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    request_data = request.get_json()
    model = request_data.get("model", "llama3")
    messages = request_data.get("messages", [])
    stream = request_data.get("stream", False)

    # --- MODIFIED ---
    # The /api/generate endpoint expects a single "prompt" string.
    # We will combine the messages into a single prompt string.
    prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    # Prepare the data payload for the Ollama /api/generate endpoint
    ollama_payload = {
        "model": model,
        "prompt": prompt, # Use "prompt" instead of "messages"
        "stream": stream
    }

    def generate_response():
        try:
            response = requests.post(OLLAMA_API_URL, json=ollama_payload, stream=True)
            response.raise_for_status() # This will now raise an error on 404

            for line in response.iter_lines():
                if line:
                    ollama_chunk = json.loads(line)
                    
                    # --- MODIFIED ---
                    # The /api/generate response format is different.
                    openai_chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "content": ollama_chunk.get("response", "") 
                                },
                                "finish_reason": "stop" if ollama_chunk.get("done") else None
                            }
                        ]
                    }
                    yield f"data: {json.dumps(openai_chunk)}\n\n"
            
            if stream:
                 yield "data: [DONE]\n\n"

        except requests.exceptions.RequestException as e:
            # This will catch the 404 error and log it
            print(f"Error connecting to Ollama: {e}")
            error_response = {"error": "Failed to connect to Ollama.", "details": str(e)}
            yield f"data: {json.dumps(error_response)}\n\n"

    return Response(generate_response(), mimetype='text/event-stream')

@app.route('/v1/models', methods=['GET'])
def list_models():
    try:
        response = requests.get(OLLAMA_MODELS_URL)
        response.raise_for_status()
        ollama_models = response.json().get("models", [])
        model_list = [
            {"id": model["name"], "object": "model", "owned_by": "ollama", "permission": []}
            for model in ollama_models
        ]
        return jsonify({"object": "list", "data": model_list})
    except requests.exceptions.RequestException as e:
        print(f"Error fetching models from Ollama: {e}")
        return jsonify({"error": "Could not fetch models from Ollama.", "data": []}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)