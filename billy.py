import subprocess
import shutil
import os
import time
import requests
import json
from skills import CommandSafetyChecker, SkillManager
from colorama import init as colorama_init, Fore, Style

colorama_init(autoreset=True)

# -- CONFIG --
USE_N8N = True
N8N_ENDPOINT = "http://localhost:5678/webhook/billy-ask"
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"
HISTORY_LOG = os.path.expanduser("~/.billy_history.log")

safety_checker = CommandSafetyChecker()
skill_manager = SkillManager()

def is_tool_installed(tool_name):
    return shutil.which(tool_name) is not None

def try_install_tool(tool_name):
    print(f\"{Fore.YELLOW}[Installing '{tool_name}' via apt...] \")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", tool_name], check=True)
        print(f\"{Fore.GREEN}[Installed '{tool_name}']\")
    except subprocess.CalledProcessError:
        print(f\"{Fore.RED}[Failed to install '{tool_name}']\")

def run_command(cmd):
    try:
        res = subprocess.run(cmd, shell=True, check=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f\"{Fore.RED}[Command failed: {e.stderr.strip()}]{Style.RESET_ALL}\"

def log_command(cmd):
    ts = time.strftime(\"%Y-%m-%d %H:%M:%S\")
    with open(HISTORY_LOG, "a") as f:
        f.write(f\"[{ts}] {cmd}\\n\")

def ask_n8n(prompt):
    payload = { "prompt": prompt }
    try:
        r = requests.post(N8N_ENDPOINT, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data.get("intent",""), data.get("plan",""), data.get("command","")
    except Exception as e:
        print(f\"{Fore.RED}[Failed to reach n8n: {e}]\")
        return None, None, None

def ask_ollama_direct(prompt):
    headers = {"Content-Type":"application/json"}
    payload = {"model":OLLAMA_MODEL, "prompt":prompt, "stream":False}
    try:
        r = requests.post(OLLAMA_ENDPOINT, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json().get("response","")
    except:
        return ""

def billy_loop():
    print(f\"\\n{Style.BRIGHT}🤖  Welcome to {Fore.CYAN}Billy{Style.RESET_ALL} — your local AI shell.{Style.RESET_ALL}\\n\")
    while True:
        try:
            user_input = input(f\"{Fore.GREEN}💬 You:{Style.RESET_ALL} \").strip()
            if user_input.lower() in ('exit','quit'): break
            if not user_input: continue

            # built-in skills first
            skill = skill_manager.get_skill(user_input)
            if skill:
                print(f\"{Fore.MAGENTA}[Running skill: {skill.name}]\")
                print(skill.handle(), end=\"\\n\\n\")
                continue

            # use n8n or fallback LLM
            if USE_N8N:
                intent, plan, cmd = ask_n8n(user_input)
                if not cmd:
                    print(f\"{Fore.RED}[n8n flow failed, falling back to direct LLM]\")
                    cmd = ask_ollama_direct(user_input)
                else:
                    print(f\"\\n{Fore.YELLOW}🔍 Intent: {Style.RESET_ALL}{intent}\")
                    print(f\"\\n{Fore.YELLOW}📝 Plan: {Style.RESET_ALL}{plan}\\n\")
            else:
                cmd = ask_ollama_direct(user_input)

            # safety & confirm
            print(f\"{Style.BRIGHT}💡 Suggest: {Fore.CYAN}{cmd}{Style.RESET_ALL}\\n\")
            safe, reason, score = safety_checker.analyze_with_score(cmd)
            print(f\"🔎 Safety: {reason} (score {score:.2f})\")
            if not safe and input(f\"{Fore.RED}❗ Run anyway? [y/N]: {Style.RESET_ALL}\").lower()!='y':
                print(f\"{Fore.YELLOW}[Canceled]\\n\")
                continue

            tool = cmd.split()[0]
            if not is_tool_installed(tool):
                if input(f\"{Fore.YELLOW}❓ Install '{tool}'? [y/N]: {Style.RESET_ALL}\").lower()=='y':
                    try_install_tool(tool)
                    if not is_tool_installed(tool):
                        print(f\"{Fore.RED}[Still missing '{tool}'], skipping]\\n\")
                        continue
                else:
                    print(f\"{Fore.YELLOW}[Skipped]\\n\")
                    continue

            log_command(cmd)
            print(f\"⚙️  Running...\\n\")
            print(run_command(cmd), end=\"\\n\\n\")

        except (EOFError, KeyboardInterrupt):
            print(f\"\\n{Style.BRIGHT}👋 Goodbye!{Style.RESET_ALL}\")
            break

if __name__ == \"__main__\":
    billy_loop()
