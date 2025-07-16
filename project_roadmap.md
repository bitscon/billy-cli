# 🧠 Billy Roadmap

> A local Linux-native AI assistant inspired by HAL, Jarvis, and Alexa.  
> Uses an LLM to interpret natural language, executes system commands safely, and evolves iteratively.

---

## 🔧 PHASE 1 — Core Shell + Command Engine ✅

> _Goal: Make Billy understand, decide, and execute safe commands._

| Feature | Status |
|--------|--------|
| Accept natural language input | ✅ Done |
| Use LLM to convert user request to Linux command | ✅ Done |
| Confirm command plan with user before execution | ✅ Done |
| Execute using `subprocess` (safe context) | ✅ Done |
| Return and format results in readable output | ✅ Done |
| Handle common errors gracefully | ✅ Done |
| Maintain command history in a local log | ✅ Done |

---

## 🧩 PHASE 2 — Skills + Toolchains (Modular Tools)

> _Goal: Expand Billy’s capabilities with structured tools, checks, and output formatters._

| Feature | Status |
|--------|--------|
| Modular “skills” system (detect special tasks) | ⬜ Planned |
| Built-in skills: system health, disk usage, logs, ports | ⬜ Planned |
| Command safety scoring / classification | ⬜ Planned |
| Tool presence checker (e.g. `docker`, `git`) | ⬜ Planned |
| Rich text or colorized CLI output formatting | ⬜ Planned |

---

## 🛰️ PHASE 3 — API + Network Awareness

> _Goal: Give Billy the ability to interact across networks and systems._

| Feature | Status |
|--------|--------|
| Ping, traceroute, dig, nmap tools | ⬜ Planned |
| Scan and identify devices on local network | ⬜ Planned |
| Check external connectivity / DNS status | ⬜ Planned |
| Smart curl/wget for pulling resources | ⬜ Planned |

---

## 🤖 PHASE 4 — Smart Context + Memory

> _Goal: Enable recall, notes, persistence and personal memory._

| Feature | Status |
|--------|--------|
| Save and recall previous Q&A or task sessions | ⬜ Planned |
| Named memory (e.g. “remember my router IP is…”) | ⬜ Planned |
| File-based persistent notes or task logs | ⬜ Planned |
| Searchable local context memory | ⬜ Planned |

---

## 🎙️ PHASE 5 — Voice + Interaction Modes

> _Goal: Turn Billy into a voice or desktop-style assistant._

| Feature | Status |
|--------|--------|
| Speech-to-text CLI interface | ⬜ Planned |
| Text-to-speech responses | ⬜ Planned |
| Wake-word activation | ⬜ Planned |
| Optional system tray UI | ⬜ Planned |

---

## 📦 PHASE 6 — Packages + Plugins

> _Goal: Let users extend Billy with their own tools._

| Feature | Status |
|--------|--------|
| Plugin execution system (local Python modules) | ⬜ Planned |
| Community skills repo (installable add-ons) | ⬜ Planned |
| Custom tool registration (per user/system) | ⬜ Planned |

---

## 🛡️ Security & Sandboxing (Ongoing)

| Feature | Status |
|--------|--------|
| Isolated user account (`billy`) | ✅ Done |
| Ask before running privileged or destructive commands | ✅ Done |
| Limit scope of writable dirs and permissions | ⬜ Planned |
| Optional AppArmor or chroot sandboxing | ⬜ Planned |

---

> Next up: **Phase 2** — Let’s begin adding modular skills to make Billy smarter.
