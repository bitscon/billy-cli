import subprocess
import shutil
import sys
import readline
import os
import time
import requests
import json

from skills import CommandSafetyChecker

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"
HISTORY_LOG = os.path.expanduser("~/.billy_history.log")

safety_checker = CommandSafetyChecker()

def is_tool_installed(tool_name):
    return shutil.which(tool_name) is not None

def try_install_tool(tool_name):
    print(f"\n[🛠️  Attempting to install '{tool_name}' using apt...]")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", tool_name], check=True)
        print(f"[✅ Installed '{tool_name}']")
    except subprocess.CalledProcessError:
        print(f"[❌ Failed to install '{tool_name}']")

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[⚠️ Command failed: {e.stderr.strip()}]"

def log_command(cmd):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_LOG, "a") as f:
        f.write(f"[{timestamp}] {cmd}\n")

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

def billy_loop():
    print("\n🤖  Welcome to Billy — your local AI Linux shell. Type 'exit' or Ctrl+D to quit.\n")
    while True:
        try:
            user_input = input("💬 You: ").strip()
            if user_input.lower() in ('exit', 'quit'): break
            if not user_input: continue

            print("\n🧠 Billy is thinking...")
            generated_cmd = ask_ollama_for_command(user_input)

            if generated_cmd.startswith("[❌"):
                print(generated_cmd)
                continue

            print(f"\n💡 Suggested command: \033[1;36m{generated_cmd}\033[0m")

            safe, reason = safety_checker.analyze(generated_cmd)
            print(f"\n🔎 Safety Check: {reason}")
            if not safe:
                confirm = input("❗ Are you sure you want to run this command? [y/N]: ").strip().lower()
                if confirm != 'y':
                    print("[🛑 Command canceled by user.]")
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

            log_command(generated_cmd)
            print("\n⚙️  Running command...")
            output = run_command(generated_cmd)
            print(f"\n📤 Output:\n{output}\n")

        except (EOFError, KeyboardInterrupt):
            print("\n👋 Exiting Billy. Goodbye!")
            break

if __name__ == "__main__":
    billy_loop()
