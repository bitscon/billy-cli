cat > billy.py << 'EOF'
import requests
import os
import time
from colorama import init as colorama_init, Fore, Style

colorama_init(autoreset=True)

N8N_ENDPOINT = "http://localhost:5678/webhook/billy-ask"
HISTORY_LOG = os.path.expanduser("~/.billy_history.log")

def log_prompt(prompt):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_LOG, "a") as f:
        f.write(f"[{ts}] {prompt}\n")

def ask_n8n(prompt):
    try:
        r = requests.post(N8N_ENDPOINT, json={"prompt": prompt}, timeout=60)
        r.raise_for_status()
        return r.json().get("output", "[No output returned]")
    except Exception as e:
        return f"{Fore.RED}[n8n error: {e}]{Style.RESET_ALL}"

def billy_loop():
    print(f"\n{Style.BRIGHT}🤖  Billy CLI — your AI terminal assistant via n8n\n")
    while True:
        try:
            user_input = input(f"{Fore.GREEN}💬 You:{Style.RESET_ALL} ").strip()
            if user_input.lower() in ("exit", "quit"): break
            if not user_input: continue

            log_prompt(user_input)
            print(f"\n{Fore.YELLOW}📡 Sending to n8n...{Style.RESET_ALL}")
            output = ask_n8n(user_input)
            print(f"\n{Style.BRIGHT}📤 Response:{Style.RESET_ALL}\n")
            print(output + "\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{Style.BRIGHT}👋 Goodbye!{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    billy_loop()
EOF
