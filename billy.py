from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)  # enable Open WebUI access from any origin

# === [ PATCHED /v1/chat/completions endpoint with token counts ] ===
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    user_prompt = data.get("messages", [{"content": ""}])[-1]["content"]
    response_text = "Hello from Billy"  # Replace with your actual processing call

    prompt_tokens = len(user_prompt.split())
    completion_tokens = len(response_text.split())

    return jsonify({
        "id": "chatcmpl-xyz",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "billy",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response_text
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
    })

# --- OpenAI-compatible model listing for Open WebUI ---
@app.route('/v1/models', methods=['GET'])
def list_models():
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "billy",
                "object": "model",
                "owned_by": "local",
                "permission": []
            }
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
