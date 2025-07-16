import subprocess
import shutil
import sys
import readline
import os
import time
import requests
import json

# Configuration
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama4:latest"
HISTORY_LOG = os.path.expanduser("~/.billy_history.log")

# Helper: Check if a tool exists in PATH
def is_tool_installed(tool_name):
    return shutil.which(tool_name) is not None

# Helper: Install missing tool (safely)
def try_install_tool(tool_name):
    print(f"\n[🛠️  Attempting to install '{tool_name}' using apt...]")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", tool_name], check=True)
        print(f"[✅ Installed '{tool_name}']")
    except subprocess.CalledProcessError:
        print(f"[❌ Failed to install '{tool_name}']")

# Helper: Run shell command and return output
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[⚠️ Command failed: {e.stderr.strip()}]"

# Helper: Log command to history
def log_command(cmd):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_LOG, "a") as f:
        f.write(f"[{timestamp}] {cmd}\n")

# Use Ollama to interpret the user's intent and generate a shell command
def ask_ollama_for_command(user_prompt):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"You are a Linux command-line assistant. Given this user input, generate the correct bash command only (no explanations):\n\n'{user_prompt}'",
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_ENDPOINT, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        parsed = response.json()
        return parsed.get("response", "")
    except Exception as e:
        return f"[❌ Failed to reach Ollama: {e}]"

# Main interactive loop
def billy_loop():
    print("\n🤖  Welcome to Billy — your local AI Linux shell. Type 'exit' or Ctrl+D to quit.\n")
    while True:
        try:
            user_input = input("💬 You: ").strip()
            if user_input.lower() in ('exit', 'quit'): break
            if not user_input:
                continue

            print("\n🧠 Billy is thinking...")
            generated_cmd = ask_ollama_for_command(user_input)

            if generated_cmd.startswith("[❌"):
                print(generated_cmd)
                continue

            print(f"\n💡 Suggested command: \033[1;36m{generated_cmd}\033[0m")

            required_tool = generated_cmd.split()[0]
            if not is_tool_installed(required_tool):
                print(f"[🔍 Tool '{required_tool}' not found on system]")
                confirm = input(f"❓ Install '{required_tool}' using apt? [y/N]: ").strip().lower()
                if confirm == 'y':
                    try_install_tool(required_tool)
                    if not is_tool_installed(required_tool):
                        print(f"[⛔ Aborting. '{required_tool}' still not available.]")
                        continue
                else:
                    print("[🚫 Skipping execution.]")
                    continue

            log_command(generated_cmd)  # ✅ Log to history
            print("\n⚙️  Running command...")
            output = run_command(generated_cmd)
            print(f"\n📤 Output:\n{output}\n")

        except (EOFError, KeyboardInterrupt):
            print("\n👋 Exiting Billy. Goodbye!")
            break

if __name__ == "__main__":
    billy_loop()
