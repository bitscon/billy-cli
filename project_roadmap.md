# 🧠 Billy AI - Roadmap

This roadmap outlines the phased development plan for **Billy**, your local Linux-native AI assistant. The goal is to create a secure, intelligent, voice-capable, command-line assistant — blending the precision of **HAL**, the responsiveness of **Jarvis**, and the convenience of **Alexa/Google Assistant**.

Billy will:
- Interpret natural language via LLM (Ollama backend)
- Execute safe, sandboxed Linux commands
- Install tools when required
- Learn and grow with permission
- Eventually interact with APIs, files, voice, and more

---

## ✅ PHASE 0 — Baseline Setup (Done)
- [x] `billy.py` responds from terminal via CLI
- [x] Connects to `Ollama` model (e.g., `llama3`)
- [x] Logs interactions
- [x] Can interpret and echo back text
- [x] Systemd service for background API if needed

---

## 🔧 PHASE 1 — Core Shell + Command Engine

> _Goal: Make Billy understand, decide, and execute safe commands._

- [ ] Accept natural language input
- [ ] Use LLM to convert user request to Linux command
- [ ] Confirm command plan with user before execution
- [ ] Execute using `subprocess` (safe context)
- [ ] Return and format results in readable output
- [ ] Handle common errors gracefully
- [ ] Maintain command history in a local log

**Example Use Cases:**
- "What is my IP?" → `curl ifconfig.me`
- "Install htop" → `sudo apt install htop`
- "Check disk space" → `df -h`

---

## 🔐 PHASE 2 — Safety & Permissions

> _Goal: Prevent Billy from harming the OS or escalating unintentionally._

- [ ] Run under limited `billy` user account
- [ ] Block dangerous commands (e.g., `rm -rf /`, `kill -9 1`)
- [ ] Validate apt installs with package name check
- [ ] Prompt for sudo when required (and log)
- [ ] Add config setting for "confirm before run" toggle
- [ ] Dry-run preview of actions before execution (optional mode)

---

## 🧠 PHASE 3 — Smart Tooling & Learning

> _Goal: Let Billy get better with time and help you faster._

- [ ] Let Billy auto-detect missing tools (`which`, `command -v`)
- [ ] Offer to install tools via `apt`
- [ ] Store tool knowledge in a local registry (`~/.billy/known_tools.json`)
- [ ] Save user preferences (e.g., preferred editor)
- [ ] Provide summary of last tasks done ("What did I ask earlier?")

---

## 📡 PHASE 4 — Internet Awareness & APIs

> _Goal: Expand Billy's reach beyond local machine._

- [ ] Add safe internet search using DuckDuckGo
- [ ] Allow calling APIs with `curl` or prebuilt wrappers
- [ ] Enable `n8n` integration for complex automation
- [ ] Allow configuring and hitting local APIs (e.g., Home Assistant, OpenWebUI)

---

## 🔊 PHASE 5 — Voice & Audio I/O

> _Goal: Enable hands-free assistant functionality._

- [ ] Add text-to-speech using `espeak` or `flite`
- [ ] Add speech-to-text using `whisper` or `vosk`
- [ ] Enable hotword detection or push-to-talk
- [ ] Configure audio input/output device preferences

---

## 🧠 PHASE 6 — Memory, Context & Personality

> _Goal: Give Billy continuity and depth._

- [ ] Store task summaries and user interaction history
- [ ] Allow optional memory of past commands/responses
- [ ] Let Billy recall names, preferences, and past actions
- [ ] Enable personality configuration ("Be witty", "Formal", etc.)
- [ ] Expose `billy config` command-line tool for tuning

---

## 🚀 PHASE 7 — Autonomous Tasking (Optional + Opt-in)

> _Goal: Let Billy act on your behalf — safely._

- [ ] Schedule tasks via cron or systemd
- [ ] Monitor system health and notify you
- [ ] Autoupdate packages or config
- [ ] Safely retry failed commands
- [ ] Ask for approval before autonomous actions

---

## 🗂️ Project Files To Track This Roadmap
- `billy.py` — Core executable
- `README.md` — Intro and usage
- `ROADMAP.md` — This file
- `CHANGELOG.md` — Milestone logs
- `billy_config.json` — Settings (coming in Phase 3–6)

---

## 🧭 Next Milestone
Start **Phase 1: Shell + Command Engine**

- Begin writing CLI parser + LLM-to-command function
- Use dry-run confirmation
- Execute simple safe commands

Let’s keep building.

---

