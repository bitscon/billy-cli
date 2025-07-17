import os
import time
import requests

# Optional: use colorama if installed, otherwise fallback to plain text
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except ImportError:
    class DummyColor:
        def __getattr__(self, name): return ''
    Fore = Style = DummyColor()

N8N_ENDPOINT = "http://localhost:5678/webhook/billy-ask"
HISTORY_LOG = os.path.expanduser("~/.billy_history.log")

def log_prompt(prompt):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_LOG, "a") as f:
        f.write(f"[{ts}] {prompt}\n")

def ask_n8n(prompt):
    try:
        print(f"{Fore.BLUE}[DEBUG] Posting to: {N8N_ENDPOINT}")
        r = requests.post(N8N_ENDPOINT, json={"prompt": prompt}, timeout=60)
        print(f"{Fore.BLUE}[DEBUG] HTTP Status: {r.status_code}")
        print(f"{Fore.BLUE}[DEBUG] Raw Response: {r.text}")
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
