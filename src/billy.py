from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import json # This import is necessary for JSON parsing

app = Flask(__name__)
CORS(app)

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    user_prompt = data.get("messages", [{"content": ""}])[-1]["content"]

    print(f"Received prompt from Open WebUI: {user_prompt}")

    full_response_content = "" # This will accumulate the full response from Ollama
    
    try:
        ollama_payload = {
            "model": "llama3",
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "stream": True # Explicitly request streaming from Ollama, though it's often default for /api/chat
        }
        print(f"Sending to Ollama: {json.dumps(ollama_payload, indent=2)}")

        # Make the request with stream=True so requests.post keeps the connection open for iterating
        ollama_response = requests.post(
            "http://localhost:11434/api/chat",
            json=ollama_payload,
            timeout=120, # Still good to have a timeout for the overall request
            stream=True # Crucial: enables iterating over the response body
        )
        ollama_response.raise_for_status()

        print(f"Received initial status from Ollama: {ollama_response.status_code}")

        # Iterate over the streamed lines from Ollama
        for line in ollama_response.iter_lines():
            if line: # Ensure the line is not empty
                try:
                    # Decode the line to a string, then parse it as JSON
                    json_chunk = json.loads(line.decode('utf-8'))
                    
                    # Debug print each chunk received from Ollama
                    # print(f"Received chunk: {json.dumps(json_chunk, indent=2)}") 

                    # Extract content if available
                    if "message" in json_chunk and "content" in json_chunk["message"]:
                        full_response_content += json_chunk["message"]["content"]
                    
                    # Check if the streaming is done
                    if json_chunk.get("done"):
                        print(f"Ollama stream finished. Total content received: {full_response_content[:200]}...")
                        break # Exit the loop if the stream is done

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON chunk from Ollama: {e} - Line: {line.decode('utf-8')}")
                    # You might want to break here or handle differently if a bad chunk breaks parsing
                    full_response_content = f"Error: Malformed JSON from Ollama in stream: {e}. Last partial content: {full_response_content[:100]}"
                    break
                
    except requests.exceptions.Timeout as e:
        full_response_content = f"Error: Ollama request timed out after 120 seconds. Is Ollama running and responsive? Error: {e}"
        print(full_response_content)

    except requests.exceptions.RequestException as e:
        full_response_content = f"Error communicating with Ollama: {e}. Check if Ollama is running and accessible on http://localhost:11434."
        print(full_response_content)

    except Exception as e:
        full_response_content = f"An unexpected error occurred in Flask app: {e}"
        print(full_response_content)

    prompt_tokens = len(user_prompt.split())
    completion_tokens = len(full_response_content.split())

    final_response_payload = jsonify({
        "id": "chatcmpl-custom-billy",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "billy",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": full_response_content # Use the accumulated content
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
    })
    
    print(f"Sending final response to Open WebUI (truncated): {str(final_response_payload.data)[:200]}...")
    return final_response_payload

@app.route('/v1/models', methods=['GET'])
def list_models():
    print("Received /v1/models request from Open WebUI")
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