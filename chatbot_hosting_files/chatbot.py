from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
import random
import sys
import time
import tty
import termios
import PyPDF2
import os
import re
import urllib.request

APP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(APP_DIR, ".env"))

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY. Add it to the .env file.")

client = Groq(api_key=API_KEY)
console = Console()

SYSTEM_PROMPT = "You are a helpful assistant for a student and coder. Use clear formatting when it improves readability, including markdown, lists, and fenced code blocks when useful."

# ── PREP MESSAGE ──────────────────────────────────────────────────────────────
# This is sent to the AI automatically before every one of your messages.
# Fill this in with whatever context, instructions, or priming you want.
PREP_MESSAGE = """"""
# ─────────────────────────────────────────────────────────────────────────────

CHAT_DIR = "/Users/maadhavsaini/aaaa/hello/chats"
IMAGE_DIR = "/Users/maadhavsaini/aaaa/hello/images"
TODO_FILE = "/Users/maadhavsaini/aaaa/hello/todos.txt"
DONE_FILE = "/Users/maadhavsaini/aaaa/hello/done.txt"
LAST_SEEDED_FILE = "/Users/maadhavsaini/aaaa/hello/last_seeded.txt"
NOTES_DIR = "/Users/maadhavsaini/Desktop/Obsidian/notes"

DAILY_TASKS = [
    "25m HOSA",
    "25m Piano",
    "25m Reading",
    "25m Calisthenics",
    "1 Kumon sheet",
]

# Create folders if they don't exist
os.makedirs(CHAT_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(NOTES_DIR, exist_ok=True)

filename = f"{CHAT_DIR}/chat_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
history = [{"role": "system", "content": SYSTEM_PROMPT}]

# Private mode flag — when True, nothing is saved to disk and history is not accumulated
private_mode = False

def seed_daily_tasks():
    today = datetime.now().strftime("%Y-%m-%d")
    last_seeded = ""
    if os.path.exists(LAST_SEEDED_FILE):
        with open(LAST_SEEDED_FILE, "r") as f:
            last_seeded = f.read().strip()
    if last_seeded == today:
        return  # Already seeded today
    todos = []
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r") as f:
            todos = [l for l in f.read().splitlines() if l.strip()]
    for task in DAILY_TASKS:
        if task not in todos:
            todos.append(task)
    with open(TODO_FILE, "w") as f:
        f.write("\n".join(todos))
    with open(LAST_SEEDED_FILE, "w") as f:
        f.write(today)

def clean_path(filepath):
    filepath = filepath.strip()
    if filepath.startswith("'") and filepath.endswith("'"):
        filepath = filepath[1:-1]
    if filepath.startswith('"') and filepath.endswith('"'):
        filepath = filepath[1:-1]
    filepath = re.sub(r'\\(.)', r'\1', filepath)
    return filepath

def read_file(filepath):
    filepath = clean_path(filepath)
    if not os.path.exists(filepath):
        return None, "File not found. Check the path and try again."
    if filepath.lower().endswith(".pdf"):
        try:
            text = ""
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            if not text.strip():
                return None, "PDF loaded but no text could be extracted."
            return text, None
        except Exception as e:
            return None, f"Could not read PDF: {e}"
    else:
        try:
            with open(filepath, "r") as f:
                return f.read(), None
        except Exception as e:
            return None, f"Could not read file: {e}"

def ask_groq(message):
    global history, private_mode
    # Prepend PREP_MESSAGE to the user's message if it has content
    full_message = f"{PREP_MESSAGE}\n\n{message}" if PREP_MESSAGE.strip() else message
    with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
        try:
            if private_mode:
                # In private mode: send only system prompt + this single message, no history saved
                messages_to_send = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_message}
                ]
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_to_send,
                )
                reply = response.choices[0].message.content
                # Do NOT append to history — leaves no trace in memory or disk
            else:
                history.append({"role": "user", "content": full_message})
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=history,
                )
                reply = response.choices[0].message.content
                history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            raise e

# ...existing code...

def ask_groq_once(system_prompt, message):
    with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        )
    return response.choices[0].message.content

def parse_answer_key_map(key_text):
    key_map = {}
    for m in re.finditer(r"(^|\n)\s*(\d+)\s*[:\-]\s*([A-Da-d])\b", key_text):
        key_map[int(m.group(2))] = m.group(3).upper()
    return key_map

def parse_user_answers_map(answer_text):
    answers = {}
    for m in re.finditer(r"(\d+)\s*[:\-]?\s*([A-Da-d])\b", answer_text):
        answers[int(m.group(1))] = m.group(2).upper()
    return answers

def handle_deca():
    DECA_TUTOR_PROMPT = (
        "You are an elite DECA coach specializing only in Principles of Business Management and Administration (PBM). "
        "Teach at ICDC level, with rigorous business logic, realistic examples, and competition-style framing. "
        "Focus on PBM performance indicators and concepts: management functions, leadership, communication, customer relations, "
        "business ethics, economics, finance basics, marketing basics, operations, and entrepreneurship fundamentals. "
        "Be direct, accurate, and exam-focused. Use rich text formatting when it improves clarity."
    )

    DECA_QUIZ_PROMPT = (
        "You create very difficult ICDC-level DECA PBM multiple-choice questions. "
        "Questions must be scenario-based, nuanced, and plausible. "
        "Use exactly four options (A, B, C, D). Exactly one correct answer per question. "
        "Output in this exact format:\n"
        "BEGIN_QUIZ\n"
        "Q1. ...\nA. ...\nB. ...\nC. ...\nD. ...\n"
        "...\n"
        "END_QUIZ\n"
        "BEGIN_KEY\n"
        "1: C | short rationale\n"
        "2: A | short rationale\n"
        "...\n"
        "END_KEY\n"
    )

    while True:
        console.print("\n[bold cyan]DECA PBM Prep[/bold cyan]")
        console.print("[dim]learn / quiz / back[/dim]")
        action = console.input("[bold green]deca> [/bold green]").strip().lower()

        if action == "back":
            break

        elif action == "learn":
            topic = console.input("[yellow]PBM topic or question: [/yellow]").strip()
            if not topic:
                continue
            try:
                reply = ask_groq_once(
                    DECA_TUTOR_PROMPT,
                    f"Teach me this PBM concept for DECA ICDC prep: {topic}. "
                    f"Include what judges test, common traps, and one quick practice check question."
                )
                console.print(Panel(reply, title="[bold cyan]DECA PBM Coach[/bold cyan]", border_style="cyan", padding=(1, 2)))
                if not private_mode:
                    with open(filename, "a") as f:
                        f.write(f"You: deca learn - {topic}\nGroq: {reply}\n\n")
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")

        elif action == "quiz":
            topic = console.input("[yellow]Topic focus (or Enter for mixed PBM): [/yellow]").strip()
            count_in = console.input("[yellow]Number of questions (default 8): [/yellow]").strip()
            try:
                count = int(count_in) if count_in else 8
                count = max(3, min(count, 20))
            except ValueError:
                count = 8

            topic_text = topic if topic else "mixed PBM"
            try:
                raw = ask_groq_once(
                    DECA_QUIZ_PROMPT,
                    f"Generate {count} very hard ICDC-level PBM questions focused on: {topic_text}."
                )

                quiz_match = re.search(r"BEGIN_QUIZ\s*(.*?)\s*END_QUIZ", raw, flags=re.DOTALL | re.IGNORECASE)
                key_match = re.search(r"BEGIN_KEY\s*(.*?)\s*END_KEY", raw, flags=re.DOTALL | re.IGNORECASE)

                quiz_text = quiz_match.group(1).strip() if quiz_match else raw.strip()
                key_text = key_match.group(1).strip() if key_match else ""

                console.print(Panel(quiz_text, title="[bold cyan]DECA PBM ICDC Quiz[/bold cyan]", border_style="cyan", padding=(1, 2)))

                while True:
                    sub = console.input("[dim]answers / reveal / back: [/dim]").strip().lower()
                    if sub == "back":
                        break
                    elif sub == "reveal":
                        if key_text:
                            console.print(Panel(key_text, title="[bold magenta]Answer Key[/bold magenta]", border_style="magenta", padding=(1, 2)))
                        else:
                            console.print("[yellow]No answer key found in model output.[/yellow]")
                    elif sub == "answers":
                        entered = console.input("[yellow]Enter like 1A 2C 3D ... : [/yellow]").strip()
                        user_map = parse_user_answers_map(entered)
                        key_map = parse_answer_key_map(key_text)
                        if not key_map:
                            console.print("[yellow]Cannot grade automatically because key format was missing.[/yellow]")
                            continue
                        total = len(key_map)
                        correct = sum(1 for q, ans in key_map.items() if user_map.get(q) == ans)
                        pct = (correct / total) * 100 if total else 0.0
                        console.print(f"[bold cyan]Score:[/bold cyan] {correct}/{total} ({pct:.1f}%)")
                        missed = [q for q in sorted(key_map.keys()) if user_map.get(q) != key_map[q]]
                        if missed:
                            miss_str = ", ".join([f"Q{q}={key_map[q]}" for q in missed])
                            console.print(f"[yellow]Missed:[/yellow] {miss_str}")
                        else:
                            console.print("[green]Perfect score.[/green]")
                    else:
                        console.print("[red]Unknown command.[/red]")

                if not private_mode:
                    with open(filename, "a") as f:
                        f.write(f"You: deca quiz - topic={topic_text}, n={count}\nGroq: {raw}\n\n")
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")

        else:
            console.print("[red]Unknown command.[/red]")

# ...existing code...
def handle_todo():
    while True:
        if os.path.exists(TODO_FILE):
            with open(TODO_FILE, "r") as f:
                todos = [l for l in f.read().splitlines() if l.strip()]
        else:
            todos = []

        console.print("\n[bold cyan]Your To-Do List[/bold cyan]")
        if not todos:
            console.print("[dim]No tasks yet.[/dim]")
        else:
            for i, task in enumerate(todos, 1):
                marker = "[yellow]★[/yellow] " if task in DAILY_TASKS else "  "
                console.print(f"{marker}[cyan]{i}.[/cyan] {task}")

        console.print("\n[dim]add / done <number> / clear / history / back[/dim]")
        action = console.input("[bold green]todo> [/bold green]").strip().lower()

        if action == "back":
            break
        elif action == "history":
            if os.path.exists(DONE_FILE):
                with open(DONE_FILE, "r") as f:
                    entries = f.read().strip()
                if entries:
                    console.print("\n[bold cyan]Completed Tasks[/bold cyan]")
                    console.print(entries + "\n")
                else:
                    console.print("[dim]No completed tasks yet.[/dim]")
            else:
                console.print("[dim]No completed tasks yet.[/dim]")
        elif action == "add":
            task = console.input("[yellow]New task: [/yellow]").strip()
            if task:
                todos.append(task)
                with open(TODO_FILE, "w") as f:
                    f.write("\n".join(todos))
                console.print("[green]✅ Task added.[/green]")
        elif action.startswith("done "):
            try:
                idx = int(action.split()[1]) - 1
                removed = todos.pop(idx)
                with open(TODO_FILE, "w") as f:
                    f.write("\n".join(todos))
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                with open(DONE_FILE, "a") as f:
                    f.write(f"[{timestamp}] {removed}\n")
                console.print(f"[green]✅ Completed: {removed}[/green]")
            except (IndexError, ValueError):
                console.print("[red]Invalid number.[/red]")
        elif action == "clear":
            todos = []
            with open(TODO_FILE, "w") as f:
                f.write("")
            console.print("[yellow]List cleared.[/yellow]")
        else:
            console.print("[red]Unknown command.[/red]")

def handle_timer():
    console.print("\n[bold cyan]Pomodoro Timer[/bold cyan]")
    console.print("[dim]Default: 25 min work, 5 min break. Press Enter to use defaults.[/dim]")

    try:
        work_input = console.input("[yellow]Work minutes (default 25): [/yellow]").strip()
        break_input = console.input("[yellow]Break minutes (default 5): [/yellow]").strip()
        work_mins = int(work_input) if work_input else 25
        break_mins = int(break_input) if break_input else 5
    except ValueError:
        console.print("[red]Invalid input, using defaults.[/red]")
        work_mins, break_mins = 25, 5

    for phase, mins in [("Work", work_mins), ("Break", break_mins)]:
        total_secs = mins * 60
        console.print(f"\n[bold cyan]{phase} session — {mins} minutes. Press Ctrl+C to stop.[/bold cyan]\n")
        try:
            for remaining in range(total_secs, 0, -1):
                m, s = divmod(remaining, 60)
                sys.stdout.write(f"\r  ⏱  {m:02d}:{s:02d} remaining   ")
                sys.stdout.flush()
                time.sleep(1)
            sys.stdout.write(f"\r  ✅ {phase} session done!              \n")
            sys.stdout.flush()
            if phase == "Work":
                os.system("say 'Work session done, take a break'")
                os.system('osascript -e \'display notification "Time to take a break!" with title "Work Session Done ✅" sound name "Glass"\'')
            else:
                os.system("say 'Break over, back to work'")
                os.system('osascript -e \'display notification "Back to work, Maadhav!" with title "Break Over 💪" sound name "Glass"\'')
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            console.print("[yellow]Timer stopped.[/yellow]")
            return



def get_all_notes():
    notes = []
    for f in sorted(os.listdir(NOTES_DIR)):
        if f.endswith(".md"):
            notes.append(f)
    return notes

def parse_note_header(filepath):
    title, subject, date = "Untitled", "general", "unknown"
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        in_front = False
        for line in lines:
            line = line.strip()
            if line == "---":
                in_front = not in_front
                continue
            if in_front:
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("subject:"):
                    subject = line.split(":", 1)[1].strip()
                elif line.startswith("date:"):
                    date = line.split(":", 1)[1].strip()
    except Exception:
        pass
    return title, subject, date

def handle_notes():
    while True:
        console.print("\n[bold cyan]\U0001f4d3 Notes[/bold cyan]")
        console.print("[dim]new / list / search / back[/dim]")
        action = console.input("[bold green]notes> [/bold green]").strip().lower()

        if action == "back":
            break

        elif action == "new":
            subject = console.input("[yellow]Subject tag (e.g. bio, history, cs): [/yellow]").strip().lower()
            if not subject:
                subject = "general"
            title = console.input("[yellow]Title: [/yellow]").strip()
            if not title:
                title = "Untitled"
            console.print("[yellow]Type your note. Enter END on a new line when done:[/yellow]")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            content = "\n".join(lines)
            date_str = datetime.now().strftime("%Y-%m-%d")
            safe_title = title.lower().replace(" ", "-").replace("/", "-")
            fname = f"{date_str}_{subject}_{safe_title}.md"
            fpath = os.path.join(NOTES_DIR, fname)
            md = f"---\ntitle: {title}\nsubject: {subject}\ndate: {date_str}\ntags: [{subject}, school]\n---\n\n# {title}\n\n{content}\n"
            with open(fpath, "w") as f:
                f.write(md)
            console.print(f"[green]\u2705 Note saved \u2192 {fname}[/green]")

        elif action == "list":
            notes = get_all_notes()
            if not notes:
                console.print("[dim]No notes yet.[/dim]")
                continue
            grouped = {}
            for i, fname in enumerate(notes):
                fpath = os.path.join(NOTES_DIR, fname)
                title, subject, date = parse_note_header(fpath)
                grouped.setdefault(subject, []).append((i + 1, fname, title, date))
            for subject, entries in sorted(grouped.items()):
                console.print(f"\n  [bold cyan]{subject.upper()}[/bold cyan]")
                for num, fname, title, date in entries:
                    console.print(f"    [cyan]{num}.[/cyan] {title}  [dim]{date}[/dim]")
            console.print()
            choice = console.input("[yellow]Open note number (or Enter to go back): [/yellow]").strip()
            if not choice:
                continue
            try:
                idx = int(choice) - 1
                fpath = os.path.join(NOTES_DIR, notes[idx])
                title, subject, date = parse_note_header(fpath)
                with open(fpath, "r") as f:
                    raw = f.read()
                body = re.sub(r"^---.*?---\n", "", raw, flags=re.DOTALL).strip()
                console.print(Panel(body, title=f"[bold cyan]{title}[/bold cyan]  [dim]{date} \u00b7 {subject}[/dim]", border_style="cyan", padding=(1, 2)))
                while True:
                    sub = console.input("[dim]append / summarize / back: [/dim]").strip().lower()
                    if sub == "back":
                        break
                    elif sub == "append":
                        console.print("[yellow]Type lines to append. END to finish:[/yellow]")
                        new_lines = []
                        while True:
                            line = input()
                            if line.strip() == "END":
                                break
                            new_lines.append(line)
                        with open(fpath, "a") as f:
                            f.write("\n" + "\n".join(new_lines) + "\n")
                        console.print("[green]\u2705 Note updated.[/green]")
                        break
                    elif sub == "summarize":
                        with console.status("[bold cyan]Summarizing...[/bold cyan]", spinner="dots"):
                            try:
                                response = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=[
                                        {"role": "system", "content": "You are a helpful study assistant. Summarize the following notes concisely and clearly, using markdown formatting when useful for readability."},
                                        {"role": "user", "content": f"Summarize these notes:\n\n{body}"}
                                    ],
                                )
                                summary = response.choices[0].message.content
                            except Exception as e:
                                console.print(f"[red]\u274c Error: {e}[/red]")
                                continue
                        console.print(Panel(summary, title="[bold cyan]Summary[/bold cyan]", border_style="cyan", padding=(1, 2)))
                    else:
                        console.print("[red]Unknown command.[/red]")
            except (IndexError, ValueError):
                console.print("[red]Invalid number.[/red]")

        elif action == "search":
            keyword = console.input("[yellow]Search keyword: [/yellow]").strip().lower()
            if not keyword:
                continue
            notes = get_all_notes()
            found = False
            for i, fname in enumerate(notes):
                fpath = os.path.join(NOTES_DIR, fname)
                title, subject, date = parse_note_header(fpath)
                with open(fpath, "r") as f:
                    lines = f.readlines()
                matches = [(j + 1, l.strip()) for j, l in enumerate(lines) if keyword in l.lower()]
                if matches:
                    found = True
                    console.print(f"\n  [cyan]{i+1}. {title}[/cyan]  [dim]{date} \u00b7 {subject}[/dim]")
                    for lineno, text in matches[:3]:
                        console.print(f"    [dim]line {lineno}:[/dim] {text}")
            if not found:
                console.print(f"[dim]No notes found containing \'{keyword}\'.[/dim]")

        else:
            console.print("[red]Unknown command.[/red]")

UNLOCK_SEQUENCE = "unlock"

def handle_lock():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    typed = ""
    try:
        tty.setraw(fd)
        sys.stdout.write("\r🔒 Locked — type 'unlock' to resume: ")
        sys.stdout.flush()
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x03":
                raise KeyboardInterrupt
            typed += ch
            typed = typed[-len(UNLOCK_SEQUENCE):]
            if typed == UNLOCK_SEQUENCE:
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

def handle_medical():
    MEDICAL_SYSTEM_PROMPT = (
        "You are an expert in medical terminology with deep knowledge of Greek and Latin word roots, prefixes, and suffixes used in medicine. "
        "You draw on reputable medical sources such as Stedman's Medical Dictionary, Taber's Cyclopedic Medical Dictionary, and established anatomy and physiology textbooks. "
        "When given a medical term, you must: "
        "1. State the full definition clearly on the first line. "
        "2. Break the word into its component parts (prefix, root/combining form, suffix) and define each part separately. "
        "3. Explain how the parts combine to form the full meaning. "
        "4. If applicable, give one or two related terms that share the same word parts. "
        "Use clear structure and formatting, including markdown, when it improves readability."
    )
    console.print("\n[bold cyan]Medical Terminology[/bold cyan]")
    console.print("[dim]Enter a medical term to break it down, or 'back' to return.[/dim]\n")

    while True:
        term = console.input("[bold green]term> [/bold green]").strip()
        if term.lower() == "back":
            break
        if not term:
            continue
        with console.status("[bold cyan]Looking up...[/bold cyan]", spinner="dots"):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Break down and explain this medical term: {term}"}
                    ],
                )
                reply = response.choices[0].message.content
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]\n")
                continue
        console.print(Panel(reply, title=f"[bold cyan]{term}[/bold cyan]", border_style="cyan", padding=(1, 2)))
        # Only write to file if not in private mode
        if not private_mode:
            with open(filename, "a") as f:
                f.write(f"You: medical - {term}\nGroq: {reply}\n\n")

GREETINGS = [
    "Welcome back, Maadhav. Let's get to work. 💪",
    "Hey Maadhav! Ready to be productive today?",
    "Good to see you, Maadhav. Let's make today count.",
    "What's up, Maadhav? Let's crush it today. 🔥",
    "Maadhav is in the building. Time to get things done.",
    "Hey Maadhav! Another day, another opportunity. 🚀",
    "Back again, Maadhav? Let's get after it.",
    "Maadhav. Focus mode: ON. 🧠",
]

BANNER = r"""
  __  __                 _ _
 |  \/  |               | | |
 | \  / | __ _  __ _  __| | |__   __ ___   __
 | |\/| |/ _` |/ _` |/ _` | '_ \ / _` \ \ / /
 | |  | | (_| | (_| | (_| | | | | (_| |\ V /
 |_|  |_|\__,_|\__,_|\__,_|_| |_|\__,_| \_/
"""

def show_welcome():
    console.clear()

    # Print ASCII banner
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")

    # Random greeting
    greeting = random.choice(GREETINGS)
    console.print(f"  [bold white]{greeting}[/bold white]")
    console.print(f"  [dim]{datetime.now().strftime('%A, %B %d, %Y  •  %I:%M %p')}[/dim]")
    console.print()
    console.print(Rule(style="cyan"))
    console.print()

    # Daily tasks status
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r") as f:
            remaining = [l for l in f.read().splitlines() if l.strip() and l in DAILY_TASKS]
    else:
        remaining = DAILY_TASKS[:]

    total = len(DAILY_TASKS)
    done = total - len(remaining)

    if remaining:
        task_lines = f"[bold yellow]  Daily Tasks  [{done}/{total} done][/bold yellow]\n\n"
        for task in remaining:
            task_lines += f"  [yellow]◦[/yellow] {task}\n"
    else:
        task_lines = f"  [bold green]Daily Tasks — All done! [{done}/{total}] 🎉[/bold green]\n"

    console.print(task_lines)
    console.print(Rule(style="cyan"))
    console.print()

    # Commands in two columns
    console.print("  [bold white]Commands[/bold white]\n")
    col1 = (
        "[cyan]load[/cyan]     load a txt or PDF file\n"
        "[cyan]essay[/cyan]    get feedback on your essay\n"
        "[cyan]image[/cyan]    generate an image\n"
        "[cyan]math[/cyan]     solve a math problem\n"
    )

    col2 = (
        "[cyan]todo[/cyan]     manage your to-do list\n"
        "[cyan]timer[/cyan]    pomodoro focus timer\n"
        "[cyan]medical[/cyan]  break down medical terms\n"
        "[cyan]deca[/cyan]     DECA PBM prep + ICDC quizzes\n"
        "[cyan]note[/cyan]     create and manage notes\n"
        "[cyan]lock[/cyan]     lock the terminal  [dim](unlock: type 'unlock')[/dim]\n"
        "[cyan]private[/cyan]  private mode  [dim](no logs saved)[/dim]\n"
        "[red]exit[/red]     quit\n"
    )

    console.print(Columns([
        Panel(col1, border_style="dim cyan", padding=(0, 2)),
        Panel(col2, border_style="dim cyan", padding=(0, 2)),
    ]))
    console.print()

with open(filename, "w") as f:
    f.write(f"Chat started: {datetime.now()}\n\n")

seed_daily_tasks()
show_welcome()
console.print(f"[dim]💾 Saving to {filename}[/dim]\n")

loaded_file_content = None

while True:
    try:
        # Show private mode indicator in prompt
        if private_mode:
            user_input = console.input("[bold magenta]🔒 Private | You: [/bold magenta]")
        else:
            user_input = console.input("[bold green]You: [/bold green]")

        # paste mode: type prompt first, then paste content, then END
        if user_input.strip().lower() == "paste":
            prompt_line = console.input("[yellow]Your prompt/question: [/yellow]").strip()
            console.print("[dim]Now paste your content, then type END on a new line:[/dim]")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            pasted = "\n".join(lines)
            if prompt_line:
                user_input = f"{prompt_line}\n\n{pasted}"
            else:
                user_input = pasted
    except KeyboardInterrupt:
        console.print()
        console.print(Rule(style="cyan"))
        console.print(f"\n  [bold cyan]See you later, Maadhav. Keep grinding. 👋[/bold cyan]\n")
        break

    if user_input.lower() == "exit":
        console.print()
        console.print(Rule(style="cyan"))
        console.print(f"\n  [bold cyan]See you later, Maadhav. Keep grinding. 👋[/bold cyan]\n")
        break

    if not user_input.strip():
        continue

    # Toggle private mode
    if user_input.strip().lower() == "private":
        private_mode = not private_mode
        if private_mode:
            console.print()
            console.print(Panel(
                "Private mode ON.\nNothing you type or receive will be saved to disk.\nConversation history is also cleared — no context carries over between messages.",
                title="[bold magenta]🔒 Private Mode[/bold magenta]",
                border_style="magenta",
                padding=(1, 2)
            ))
            console.print()
        else:
            console.clear()
            console.print(Panel(
                "Private mode OFF. Terminal cleared. Logging resumed.",
                title="[bold cyan]🔓 Private Mode Disabled[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            ))
            console.print()
        continue

    # Lock terminal (also triggered by Ctrl+L which sends \x0c)
    if user_input.lower() == "lock" or user_input == "\x0c":
        handle_lock()
        continue

    # Load file
    if user_input.lower() == "load":
        filepath = console.input("[yellow]Drag your file here and press Enter: [/yellow]")
        content, error = read_file(filepath)
        if error:
            console.print(f"[red]❌ {error}[/red]\n")
        else:
            loaded_file_content = content
            console.print("[green]✅ File loaded! Now ask me anything about it.[/green]\n")
        continue

    # Essay helper
    if user_input.lower() == "essay":
        choice = console.input("[yellow]Drag your essay file here, or type 'paste': [/yellow]")
        if choice.lower() == "paste":
            console.print("[yellow]Paste your essay below, then type END on a new line:[/yellow]")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            essay_content = "\n".join(lines)
        else:
            essay_content, error = read_file(choice)
            if error:
                console.print(f"[red]❌ {error}[/red]\n")
                continue
        try:
            reply = ask_groq(f"Please review this essay and provide detailed feedback on: structure and flow, argument strength, grammar and clarity, and specific suggestions for improvement. Be constructive and specific.\n\nEssay:\n{essay_content}")
            console.print(Panel(reply, title="[bold cyan]Essay Feedback[/bold cyan]", border_style="cyan", padding=(1, 2)))
            if not private_mode:
                with open(filename, "a") as f:
                    f.write(f"You: essay feedback request\nGroq: {reply}\n\n")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]\n")
        continue

    # Image generation
    if user_input.lower() == "image":
        prompt = console.input("[yellow]Describe the image you want: [/yellow]")
        try:
            from huggingface_hub import InferenceClient
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            HF_TOKEN = "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"

            console.print("[dim]🎨 Generating image... this may take 20-30 seconds[/dim]")
            hf_client = InferenceClient(token=HF_TOKEN)
            image = hf_client.text_to_image(
                prompt,
                model="stabilityai/stable-diffusion-xl-base-1.0"
            )
            image_path = f"{IMAGE_DIR}/image_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            image.save(image_path)
            os.system(f"open '{image_path}'")
            console.print(f"[green]✅ Image generated and opened![/green]")
            console.print(f"[dim]💾 Saved to {image_path}[/dim]\n")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]\n")
        continue

    # Math solver
    if user_input.lower() == "math":
        problem = console.input("[yellow]Enter your math problem: [/yellow]")
        math_prompt = (
            f"Solve this math problem. Follow this exact format:\n"
            f"1. State the answer clearly on the first line (e.g. 'x = 2' or 'Answer: 42').\n"
            f"2. Then show your full step-by-step work, one step per line.\n"
            f"Use markdown formatting if it improves clarity.\n\n"
            f"Problem: {problem}"
        )
        try:
            reply = ask_groq(math_prompt)
            console.print(Panel(reply, title="[bold cyan]Math Solution[/bold cyan]", border_style="cyan", padding=(1, 2)))
            if not private_mode:
                with open(filename, "a") as f:
                    f.write(f"You: math - {problem}\nGroq: {reply}\n\n")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]\n")
        continue

    # To-do list
    if user_input.lower() == "todo":
        handle_todo()
        continue

    # Pomodoro timer
    if user_input.lower() == "timer":
        handle_timer()
        continue
    
    # DECA PBM prep
    if user_input.lower() == "deca":
        handle_deca()
        continue

    # Notes
    if user_input.lower() == "note":
        handle_notes()
        continue

    # Medical terminology
    if user_input.lower() == "medical":
        handle_medical()
        continue

    # Paste multi-line message
    if user_input.lower() == "paste":
        console.print("[yellow]Paste your message below, then type END on a new line:[/yellow]")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        user_input = "\n".join(lines)
        if not user_input.strip():
            continue

    # Regular chat with optional loaded file
    if loaded_file_content:
        full_message = f"Here is a file I want you to help me with:\n\n{loaded_file_content}\n\nMy question: {user_input}"
        loaded_file_content = None
    else:
        full_message = user_input

    try:
        reply = ask_groq(full_message)
        console.print()
        console.print(Panel(
            reply,
            title="[bold magenta]🔒 Groq (Private)[/bold magenta]" if private_mode else "[bold cyan]Groq[/bold cyan]",
            border_style="magenta" if private_mode else "cyan",
            padding=(1, 2)
        ))
        console.print()
        # Only write to file if not in private mode
        if not private_mode:
            with open(filename, "a") as f:
                f.write(f"You: {user_input}\nGroq: {reply}\n\n")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]\n")