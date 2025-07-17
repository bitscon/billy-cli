import os
import time
import socketio
import requests
from wsgiref.simple_server import make_server
from wsgiref.util import FileWrapper
from urllib.parse import unquote

# Config
N8N_WEBHOOK = "http://localhost:5678/webhook/billy-ask"
PORT = 5001
LOGFILE = os.path.expanduser("~/.billy_history.log")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Socket.IO setup
sio = socketio.Server(cors_allowed_origins="*")
def static_app(environ, start_response):
    path = unquote(environ.get("PATH_INFO", "")).lstrip("/")
    if path == "":
        path = "index.html"
    full_path = os.path.join(STATIC_DIR, path)

    if not os.path.isfile(full_path):
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"404 Not Found"]

    content_type = "text/html" if path.endswith(".html") else "application/octet-stream"
    start_response("200 OK", [("Content-Type", content_type)])
    return FileWrapper(open(full_path, "rb"))

app = socketio.WSGIApp(sio, static_app)

def log(prompt):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGFILE, "a") as f:
        f.write(f"[{ts}] {prompt}\n")

def send_to_n8n(prompt):
    try:
        r = requests.post(N8N_WEBHOOK, json={"prompt": prompt}, timeout=30)
        r.raise_for_status()
        return r.json().get("output", "⚠️ No output from n8n.")
    except Exception as e:
        return f"❌ Error talking to n8n: {e}"

@sio.event
def connect(sid, environ):
    print(f"[+] Client connected: {sid}")

@sio.event
def disconnect(sid):
    print(f"[-] Client disconnected: {sid}")

@sio.event
def ask(sid, data):
    prompt = data.get("prompt", "").strip()
    if not prompt:
        sio.emit("reply", {"response": "❌ Empty prompt"}, to=sid)
        return
    log(prompt)
    response = send_to_n8n(prompt)
    sio.emit("reply", {"response": response}, to=sid)

if __name__ == "__main__":
    print(f"🧠 Billy WSGI Socket.IO server running on http://0.0.0.0:{PORT}")
    with make_server("", PORT, app) as httpd:
        httpd.serve_forever()
