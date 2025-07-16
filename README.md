# Billy — Your Local AI Linux Assistant 🧠🖥️

> A command-line AI assistant inspired by Jarvis, HAL, and a touch of Alexa.  
> Billy interprets your natural language, generates smart Linux commands using LLMs, executes them safely, and evolves to serve you better on your own machine.

---

## 🚀 Overview

Billy is a **local, secure, Linux-native CLI assistant**.  
He uses a local LLM via [Ollama](https://ollama.com) to understand your natural language and translate it into executable Linux commands.  
Billy runs entirely on your machine, with no cloud dependency, internet requirement, or external API calls.

---

## ✨ Features (Current)

- 💬 **Natural language interface in the terminal**
- 🧠 **Uses local LLM (via Ollama) to generate shell commands**
- 🧪 **Confirms the command before execution**
- ⚙️ **Runs safe commands via subprocess**
- 🧯 **Error handling for failed or risky actions**
- 📜 **Maintains history log of actions**
- 🧰 **Can auto-install missing tools using apt**
- 🔗 **(In Progress)** n8n integration for trigger-based workflows via webhook

---

## 🛠️ Installation

### 1. Clone the Project

```bash
git clone https://github.com/bitscon/billy.git
cd billy
```

### 2. Setup Requirements

- Python 3.10+
- Node.js with n8n (installed globally or via systemd)
- [Ollama](https://ollama.com) with `llama3.2` or compatible local model
- `n8n` must be running locally with the `billy-ask` workflow enabled (see roadmap)

---

## 📡 API/Webhook Usage (WIP)

Once `n8n` is running with the webhook workflow:

```bash
curl -X POST http://localhost:5678/webhook/billy-ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "List 5 Linux commands to check disk usage"}'
```

Response will be returned from the local LLM.

> n8n webhook setup is working, but full response routing and memory logging are still in progress — see `project_roadmap.md`.

---
