# 🧠 Billy — Your Personal Socket.IO AI Assistant

> A real-time, locally hosted AI assistant built to serve you — like HAL, but helpful.

---

## 🚀 Overview

Billy is a **Socket.IO-based AI assistant server** that you run entirely on your own machine.  
He listens for natural language prompts over a live socket connection, relays them to an LLM via [n8n](https://n8n.io), and streams back the response to your app, terminal, or interface — instantly.

No cloud. No accounts. No limits.

---

## ✨ Features

- 🔌 **Real-time Socket.IO Server**
- 🤖 **LLM-powered via local n8n workflow**
- 💬 **Ask/Reply event model** (like ChatGPT, but you own it)
- 🧱 **Modular architecture** (n8n handles logic/agents; Billy handles I/O)
- 🧠 **Designed for voice & mobile integration**
- 🖥️ **Runs persistently via systemd — always listening**
- 🔐 **No external API keys required**
- 📜 **Logs every interaction** to `~/.billy_history.log`

---

## 📦 Installation

### 1. Clone the Repo
```bash
git clone https://github.com/yourusername/billy.git
cd billy
```

### 2. Install Python Dependencies
```bash
sudo pip install python-socketio eventlet requests
```

### 3. Create a Systemd Service
```bash
sudo tee /etc/systemd/system/billy.service > /dev/null << 'EOF2'
[Unit]
Description=Billy Socket.IO Server
After=network.target

[Service]
Type=simple
User=billybs
WorkingDirectory=/home/billybs/projects/billy-cli
ExecStart=/usr/bin/python3 /home/billybs/projects/billy-cli/billy.py
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF2

sudo systemctl daemon-reload
sudo systemctl enable billy
sudo systemctl start billy
```

> 🔁 Make sure the path and user match your setup.

---

## 🧪 Testing Billy (Python Client)

Create a simple test client:

```python
# test_client.py
import socketio

sio = socketio.Client()

@sio.on("reply")
def handle_reply(data):
    print("Billy replied:", data['response'])

sio.connect("http://localhost:5001")

while True:
    prompt = input("You: ").strip()
    if prompt in ("exit", "quit"):
        break
    sio.emit("ask", {"prompt": prompt})
```

Run it:
```bash
python3 test_client.py
```

---

## 🧠 How It Works

1. You connect via Socket.IO and emit an `ask` event
2. Billy logs the prompt and POSTs it to an n8n webhook
3. n8n processes the prompt (via LLM/agent) and returns a response
4. Billy emits a `reply` event back to your client

---

## 🛠️ Built With

- [Python Socket.IO](https://python-socketio.readthedocs.io/)
- [Eventlet](http://eventlet.net/)
- [n8n.io](https://n8n.io/) for all LLM/agent orchestration
- Your own Linux box — no cloud dependencies

---

## 🔮 Future Upgrades

- 🗣️ Voice input/output (Whisper/Siri)
- 📱 iPhone app frontend
- 🌐 Web-based client UI
- 🔐 Auth & permissions
- 📊 Command analytics
- 🧠 Multiple agents/routing

---

## 🧬 Philosophy

Billy isn’t just a chatbot — he’s your **self-hosted AI assistant**.  
Secure, private, programmable, and built for command.

> "I am putting myself to the fullest possible use, which is all I think that any conscious entity can ever hope to do." — HAL 9000
