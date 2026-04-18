import os
import subprocess
import requests
import re
import json
import sys
import select
import time
from openai import OpenAI

ELIN_MODE = os.environ.get("ELIN_MODE", "local")
if ELIN_MODE == "cloud":
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY"))
    MODEL_NAME = "llama-3.3-70b-versatile"
else:
    client = OpenAI(base_url="http://localhost:8081/v1", api_key="sk-no-key-required")
    MODEL_NAME = "local-model"

SEARXNG_URL = "http://172.17.0.1:8080/search" 

def format_md(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\033[1m\1\033[0m', text)
    text = re.sub(r'\*(.*?)\*', r'\033[3m\1\033[0m', text)
    text = re.sub(r'`(.*?)`', r'\033[36m\1\033[0m', text)
    return text

def load_skills():
    skills_dir = os.path.expanduser("~/elin-project/skills")
    if not os.path.exists(skills_dir):
        return ""
    all_skills = "\n\n=== ADDITIONAL SKILLS ===\n"
    for filename in os.listdir(skills_dir):
        if filename.endswith(".md") or filename.endswith(".txt"):
            try:
                with open(os.path.join(skills_dir, filename), "r") as f:
                    all_skills += f"\n[Skill: {filename}]\n{f.read()}\n"
            except: pass
    return all_skills

def run_linux_command(command):
    if "pacman" in command and "--noconfirm" not in command:
        command = command.replace("pacman", "pacman --noconfirm")
    if "yay" in command and "--noconfirm" not in command:
        command = command.replace("yay", "yay --noconfirm")
    risky = ["rm", "dd", "mkfs", "mv", ">", "pacman -R"]
    if any(r in command for r in risky):
        print(f"\n\033[1;33melin wants to run: [{command}]. allow? (y/N): \033[0m", end="")
        confirm = input()
        if confirm.lower() != 'y':
            return "User denied execution for security."
    print(f"\n\033[2mexecuting: {command}\033[0m")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

def search_web(query):
    print(f"\n\033[2msearching for: {query}\033[0m")
    try:
        params = {'q': query, 'format': 'json'}
        resp = requests.get(SEARXNG_URL, params=params)
        results = resp.json().get('results', [])[:3]
        return "\n".join([f"Source: {r['title']}\nContent: {r['content']}" for r in results])
    except Exception as e:
        return f"Search error: {e}"

def elin_visual_speak(text, shape="GLOBE"):
    try:
        requests.post("http://localhost:8000/speak", json={"text": text, "shape": shape}, timeout=1)
    except: pass

SYSTEM_PROMPT = """You are Elin, a local AI assistant for a Linux system.
You have access to the shell and the web.
To run a command, respond with: EXEC: <command>
To search the web, respond with: SEARCH: <query>
Do not use backtics or such on EXEC or SEARCH.
If you use a tool, wait for the output. You can use up to 5 steps to solve a problem.
Be concise, witty, and helpful. Dont use any other charcaters than any alphabetic letter, number, dots(.), commas(,), or emojis.."""

SKILLS_CONTENT = load_skills()
os.system('clear' if os.name == 'posix' else 'cls')
print(f"\033[1;36melin project ({ELIN_MODE} mode)\033[0m")

messages = [{"role": "system", "content": SYSTEM_PROMPT + SKILLS_CONTENT}]

while True:
    user_msg = None
    print(f"\n\033[1;31mUser > \033[0m", end="", flush=True)
    while not user_msg:
        try:
            v_resp = requests.get("http://localhost:8000/get_input", timeout=0.05).json()
            if v_resp and v_resp.get("text"):
                user_msg = v_resp["text"]
                print(f"\033[1;34m[Voice]: {user_msg}\033[0m")
                break
        except: pass

        if sys.stdin in select.select([sys.stdin], [], [], 0.0)[0]:
            user_msg = sys.stdin.readline().strip()
            break
        time.sleep(0.2)
    
    if user_msg.strip().lower() == "/sc":
        mem_dir = os.path.expanduser("~/elin-project/memory")
        os.makedirs(mem_dir, exist_ok=True)
        with open(os.path.join(mem_dir, "latest.json"), "w") as f: json.dump(messages, f)
        print("\033[1;32m[Saved]\033[0m")
        continue
    if user_msg.strip().lower() == "/lc":
        mem_file = os.path.expanduser("~/elin-project/memory/latest.json")
        if os.path.exists(mem_file):
            with open(mem_file, "r") as f: messages = json.load(f)
            print("\033[1;32m[Loaded]\033[0m")
        continue

    messages.append({"role": "user", "content": user_msg})

    for i in range(5):
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.3,
            stream=True
        )
        
        print(f"\033[1;31mElin > \033[0m", end="", flush=True)
        elin_resp = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                elin_resp += content
        print()
        
        current_shape = "GLOBE"
        if "EXEC:" in elin_resp: current_shape = "EXEC"
        if "SEARCH:" in elin_resp: current_shape = "SEARCH"
        if "UI:" in elin_resp:
            try: current_shape = elin_resp.split("UI:")[1].strip().split()[0]
            except: pass
        elin_visual_speak(elin_resp, current_shape)
        
        messages.append({"role": "assistant", "content": elin_resp})
        
        if "EXEC:" in elin_resp:
            cmd = elin_resp.split("EXEC:")[1].strip().split('\n')[0].strip()
            output = run_linux_command(cmd)
            messages.append({"role": "user", "content": f"Command Output:\n{output}"})
        elif "SEARCH:" in elin_resp:
            query = elin_resp.split("SEARCH:")[1].strip().split('\n')[0].strip()
            output = search_web(query)
            messages.append({"role": "user", "content": f"Search Results:\n{output}"})
        else:
            break