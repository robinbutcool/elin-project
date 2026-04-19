import os
import subprocess
import requests
import re
import json
import sys
import select
import time
import threading
import readline
from openai import OpenAI

ELIN_MODE = os.environ.get("ELIN_MODE", "local")
NO_MEMORY = "--no-memory" in sys.argv  # start fresh even if memory exists
MAX_MESSAGES = 100  # max messages to keep in memory file

if ELIN_MODE == "cloud":
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY"))
    MODEL_NAME = "llama-3.3-70b-versatile"
    TOKEN_LIMIT = 90000
else:
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="sk-no-key-required")
    MODEL_NAME = "qwen2.5-coder:3b"
    TOKEN_LIMIT = 8000

SEARXNG_URL = "http://172.17.0.1:8080/search"
MAX_OUTPUT_LEN = 3000

MEM_DIR = os.path.expanduser("~/elin-project/memory")
MEM_FILE = os.path.join(MEM_DIR, "latest.json")

token_count = 0

HELP_TEXT = """\033[1;36m
elin commands:
  /help          show this message
  /sc            save current conversation
  /lc            load saved conversation
  /clear         reset context and token counter
  /tokens        show estimated token usage

launch flags:
  --no-memory    start fresh, ignore saved memory

elin keywords (for the AI):
  EXEC: <cmd>    run a shell command
  SEARCH: <q>    search the web via SearXNG
  OPEN: <url>    open a URL in the browser
\033[0m"""

def estimate_tokens(text):
    return len(text) // 4

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

def save_memory(messages):
    os.makedirs(MEM_DIR, exist_ok=True)
    # cap stored messages: keep system message + last MAX_MESSAGES
    capped = [messages[0]] + messages[1:][-MAX_MESSAGES:]
    with open(MEM_FILE, "w") as f:
        json.dump(capped, f)

def autosave(messages_ref):
    while True:
        time.sleep(60)
        save_memory(messages_ref[0])

def truncate_context(messages, system_prompt):
    total = estimate_tokens(system_prompt)
    kept = []
    for msg in reversed(messages[1:]):
        total += estimate_tokens(msg["content"])
        if total > TOKEN_LIMIT:
            break
        kept.insert(0, msg)
    if len(kept) < len(messages) - 1:
        print(f"\033[1;33m[context truncated, dropped {len(messages) - 1 - len(kept)} old messages]\033[0m")
    return [messages[0]] + kept

def run_linux_command(command):
    if "pacman" in command and "--noconfirm" not in command:
        command = command.replace("pacman", "pacman --noconfirm")
    if "yay" in command and "--noconfirm" not in command:
        command = command.replace("yay", "yay --noconfirm")
    risky = ["rm", "dd", "mkfs", "mv", ">", "pacman -R", "wget", "curl", "python"]
    if any(r in command for r in risky):
        print(f"\n\033[1;33melin wants to run: [{command}]. allow? (y/N): \033[0m", end="")
        confirm = input()
        if confirm.lower() != 'y':
            return "User denied execution for security."
    print(f"\n\033[2mexecuting: {command}\033[0m")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    if len(output) > MAX_OUTPUT_LEN:
        output = output[:MAX_OUTPUT_LEN] + "\n[output truncated to avoid token limit]"
    return output

def open_url(url):
    print(f"\n\033[2mopening: {url}\033[0m")
    subprocess.Popen(["xdg-open", url])
    return f"Opened {url} in default browser."

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
To open a URL in the browser, respond with: OPEN: <url>
You can use multiple EXEC lines in one response to run several commands.
Do not use backtics or such on EXEC, SEARCH, or OPEN.
If you use a tool, wait for the output. You can use up to 5 steps to solve a problem.
Be concise, witty, and helpful. Dont use any other charcaters than any alphabetic letter, number, dots(.), commas(,), or emojis.."""

SKILLS_CONTENT = load_skills()
FULL_SYSTEM = SYSTEM_PROMPT + SKILLS_CONTENT

os.system('clear' if os.name == 'posix' else 'cls')
print(f"\033[1;36melin project ({ELIN_MODE} mode)\033[0m")
print(f"\033[2mtype /help for commands\033[0m")

if NO_MEMORY:
    messages = [{"role": "system", "content": FULL_SYSTEM}]
    print(f"\033[1;33m[--no-memory: starting fresh]\033[0m")
elif os.path.exists(MEM_FILE):
    with open(MEM_FILE, "r") as f:
        messages = json.load(f)
    print(f"\033[1;32m[Memory autoloaded]\033[0m")
else:
    messages = [{"role": "system", "content": FULL_SYSTEM}]

messages_ref = [messages]
t = threading.Thread(target=autosave, args=(messages_ref,), daemon=True)
t.start()

while True:
    user_msg = None
    tokens_display = f"\033[2m[~{token_count} tokens]\033[0m " if token_count > 0 else ""
    print(f"\n{tokens_display}\033[1;31mUser > \033[0m", end="", flush=True)

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

    if not user_msg:
        continue

    if user_msg.strip().lower() == "/help":
        print(HELP_TEXT)
        continue

    if user_msg.strip().lower() == "/sc":
        save_memory(messages)
        print("\033[1;32m[Saved]\033[0m")
        continue

    if user_msg.strip().lower() == "/lc":
        if os.path.exists(MEM_FILE):
            with open(MEM_FILE, "r") as f:
                messages = json.load(f)
            messages_ref[0] = messages
            print("\033[1;32m[Loaded]\033[0m")
        continue

    if user_msg.strip().lower() == "/clear":
        messages = [{"role": "system", "content": FULL_SYSTEM}]
        messages_ref[0] = messages
        token_count = 0
        print("\033[1;32m[Context cleared]\033[0m")
        continue

    if user_msg.strip().lower() == "/tokens":
        print(f"\033[1;32m[Estimated tokens used this session: ~{token_count}]\033[0m")
        continue

    messages.append({"role": "user", "content": user_msg})
    token_count += estimate_tokens(user_msg)

    messages = truncate_context(messages, FULL_SYSTEM)
    messages_ref[0] = messages

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

        token_count += estimate_tokens(elin_resp)

        current_shape = "GLOBE"
        if "EXEC:" in elin_resp: current_shape = "EXEC"
        if "SEARCH:" in elin_resp: current_shape = "SEARCH"
        if "OPEN:" in elin_resp: current_shape = "OPEN"
        if "UI:" in elin_resp:
            try: current_shape = elin_resp.split("UI:")[1].strip().split()[0]
            except: pass
        elin_visual_speak(elin_resp, current_shape)

        messages.append({"role": "assistant", "content": elin_resp})
        messages_ref[0] = messages

        tool_used = False

        exec_cmds = re.findall(r'EXEC:\s*(.+)', elin_resp)
        if exec_cmds:
            tool_used = True
            all_outputs = []
            for cmd in exec_cmds:
                output = run_linux_command(cmd.strip())
                all_outputs.append(f"$ {cmd.strip()}\n{output}")
            combined = "Command Output:\n" + "\n\n".join(all_outputs)
            messages.append({"role": "user", "content": combined})
            token_count += estimate_tokens(combined)

        if "SEARCH:" in elin_resp:
            tool_used = True
            query = elin_resp.split("SEARCH:")[1].strip().split('\n')[0].strip()
            output = search_web(query)
            messages.append({"role": "user", "content": f"Search Results:\n{output}"})
            token_count += estimate_tokens(output)

        if "OPEN:" in elin_resp:
            tool_used = True
            url = elin_resp.split("OPEN:")[1].strip().split('\n')[0].strip()
            output = open_url(url)
            messages.append({"role": "user", "content": output})

        messages_ref[0] = messages

        if not tool_used:
            break
