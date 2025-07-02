from flask import Flask, request, Response, jsonify
import time

app = Flask(__name__)

@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    data = request.json
    stream = data.get("stream", False)

    if stream:
        def generate():
            # Example streamed response tokens
            for token in ["Hello", "from", "Billy"]:
                yield f"data: {token}\n\n"
                time.sleep(0.5)
            yield "data: [DONE]\n\n"
        
        return Response(generate(), mimetype="text/event-stream")
    
    # Non-streaming response
    return jsonify({
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello from Billy"
                }
            }
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
