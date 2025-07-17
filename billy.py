import os
import time
import socketio
import eventlet
import requests
from eventlet import wsgi, static

# Config
N8N_WEBHOOK = "http://localhost:5678/webhook/billy-ask"
PORT = 5001
LOGFILE = os.path.expanduser("~/.billy_history.log")

# Socket.IO setup (no Flask)
sio = socketio.Server(cors_allowed_origins="*")

# Serve static files from ./static folder
static_app = static.Cling(os.path.join(os.path.dirname(__file__), 'static'))
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
    print(f"🧠 Billy Socket.IO server (with static HTML) on port {PORT}...")
    wsgi.server(eventlet.listen(('', PORT)), app)
