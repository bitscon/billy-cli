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
OLLAMA_MODEL = "llama3.2:latest"

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
        return result.stdout.strip() or result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return f"[⚠️ Command failed: {e.stderr.strip()}]"

# Basic safety filter to block dangerous commands
def is_command_safe(cmd):
    dangerous = ['rm -rf /', 'mkfs', ':(){:|:&};:', 'dd if=']
    return not any(d in cmd for d in dangerous)

# Use Ollama to interpret the user's intent and generate a shell command
def ask_ollama_for_command(user_prompt):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"You are Billy, a helpful Linux assistant. Output ONLY the exact bash command a user would run to do the following task:\n\n'{user_prompt}'\n\nDo not include explanations or formatting — just a valid bash command.",
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_ENDPOINT, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        parsed = response.json()
        return parsed.get("response", "").strip()
    except Exception as e:
        return f"[❌ Failed to reach Ollama: {e}]"

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

            if not is_command_safe(generated_cmd):
                print("[🚫 Dangerous command detected. Skipping execution for safety.]")
                continue

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

            print("\n⚙️  Running command...")
            output = run_command(generated_cmd)
            print(f"\n📤 Output:\n{output}\n")

        except (EOFError, KeyboardInterrupt):
            print("\n👋 Exiting Billy. Goodbye!")
            break

if __name__ == "__main__":
    billy_loop()
