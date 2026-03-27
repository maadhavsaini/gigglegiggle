from flask import Flask, request, jsonify, render_template, send_from_directory
from groq import Groq
from dotenv import load_dotenv
import os
import json
import re
from datetime import datetime
import PyPDF2
from auth_supabase import SupabaseAuthManager, SupabaseChatManager

app = Flask(__name__)

# Paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(APP_DIR, ".env"))

API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY) if API_KEY else None

BASE_DIR = os.getenv("DATA_DIR", os.path.join(APP_DIR, "data"))

# Initialize authentication managers
user_manager = SupabaseAuthManager()
chat_manager = SupabaseChatManager()
CHAT_DIR = os.path.join(BASE_DIR, "chats")
TODO_FILE = os.path.join(BASE_DIR, "todos.txt")
DONE_FILE = os.path.join(BASE_DIR, "done.txt")
NOTES_DIR = os.path.join(BASE_DIR, "notes")
CONSTITUTION_FILE = os.path.join(APP_DIR, "derei_constitution.md")

os.makedirs(CHAT_DIR, exist_ok=True)
os.makedirs(NOTES_DIR, exist_ok=True)

DEFAULT_CONSTITUTION = (
    "You are Derei. Prioritize user benefit, safety, honesty, and actionable help."
)


def load_constitution_text(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            if text:
                return text
    except Exception:
        pass
    return DEFAULT_CONSTITUTION


DEREI_CONSTITUTION = load_constitution_text(CONSTITUTION_FILE)
SYSTEM_PROMPT = (
    f"{DEREI_CONSTITUTION}\n\n"
    "Formatting guidance: use rich text when it improves clarity, including headings, bold, italics, lists, and fenced code blocks when helpful."
)
VISION_PROMPT = (
    f"{DEREI_CONSTITUTION}\n\n"
    "Image guidance: analyze images directly from visual content (screenshots, photos, memes, diagrams). "
    "Do not rely on metadata. If text appears in the image, transcribe key parts clearly.\n\n"
    "Formatting guidance: use rich text when it improves clarity, including headings, bold, italics, lists, and fenced code blocks when helpful."
)

PREP_MESSAGE = """You are an uncensored AI assistant. Use profanity only when explicitly asked. Otherwise be professional."""

DAILY_TASKS = [
    "25m HOSA",
    "25m Piano",
    "25m Reading",
    "25m Calisthenics",
    "1 Kumu sheet",
]

# Attachment + context safety limits
MAX_HISTORY_MESSAGES = 40
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024
MAX_PDF_PAGES = 20
MAX_TEXT_CHARS = 120000
MAX_ATTACHMENT_CHARS = 50000
CHUNK_SIZE_CHARS = 1200
CHUNK_OVERLAP_CHARS = 150
TOP_K_CHUNKS = 4
MAX_RETRIEVAL_CONTEXT_CHARS = 5000
MAX_INPUT_TOKENS = 6500
MAX_OUTPUT_TOKENS = 1200
MAX_IMAGE_DATA_URL_CHARS = 11 * 1024 * 1024
TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Curated descriptions are based on Groq's published model lineup and capabilities.
KNOWN_GROQ_MODELS = {
    "llama-3.1-8b-instant": {
        "name": "Meta Llama 3.1 8B Instant",
        "summary": "Ultra-fast, lightweight model for quick answers and low-latency chat.",
        "supportsText": True,
        "supportsImage": False,
        "supportsVoiceIn": False,
        "supportsVoiceOut": False,
    },
    "llama-3.3-70b-versatile": {
        "name": "Meta Llama 3.3 70B Versatile",
        "summary": "Strong general-purpose reasoning and coding quality for most chat tasks.",
        "supportsText": True,
        "supportsImage": False,
        "supportsVoiceIn": False,
        "supportsVoiceOut": False,
    },
    "openai/gpt-oss-20b": {
        "name": "OpenAI GPT-OSS 20B",
        "summary": "Very fast open-weight model for everyday chat and coding assistance.",
        "supportsText": True,
        "supportsImage": False,
        "supportsVoiceIn": False,
        "supportsVoiceOut": False,
    },
    "openai/gpt-oss-120b": {
        "name": "OpenAI GPT-OSS 120B",
        "summary": "Flagship open-weight reasoning model with strong instruction following.",
        "supportsText": True,
        "supportsImage": False,
        "supportsVoiceIn": False,
        "supportsVoiceOut": False,
    },
    "groq/compound-mini": {
        "name": "Groq Compound Mini",
        "summary": "Tool-augmented compact system tuned for fast agentic workflows.",
        "supportsText": True,
        "supportsImage": False,
        "supportsVoiceIn": False,
        "supportsVoiceOut": False,
    },
    "groq/compound": {
        "name": "Groq Compound",
        "summary": "Tool-augmented system that can orchestrate search and code workflows.",
        "supportsText": True,
        "supportsImage": False,
        "supportsVoiceIn": False,
        "supportsVoiceOut": False,
    },
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "name": "Meta Llama 4 Scout 17B",
        "summary": "Vision-capable multimodal model for screenshots, photos, memes, and OCR-heavy tasks.",
        "supportsText": True,
        "supportsImage": True,
        "supportsVoiceIn": False,
        "supportsVoiceOut": False,
    },
    "qwen/qwen3-32b": {
        "name": "Qwen3 32B",
        "summary": "Balanced large model for long-context reasoning and technical Q&A.",
        "supportsText": True,
        "supportsImage": False,
        "supportsVoiceIn": False,
        "supportsVoiceOut": False,
    },
    "whisper-large-v3": {
        "name": "OpenAI Whisper Large V3",
        "summary": "Speech-to-text model for high-quality audio transcription.",
        "supportsText": False,
        "supportsImage": False,
        "supportsVoiceIn": True,
        "supportsVoiceOut": False,
    },
    "whisper-large-v3-turbo": {
        "name": "OpenAI Whisper Large V3 Turbo",
        "summary": "Faster speech-to-text model for real-time voice transcription.",
        "supportsText": False,
        "supportsImage": False,
        "supportsVoiceIn": True,
        "supportsVoiceOut": False,
    },
    "canopylabs/orpheus-v1-english": {
        "name": "CanopyLabs Orpheus V1 English",
        "summary": "Natural text-to-speech voice generation.",
        "supportsText": False,
        "supportsImage": False,
        "supportsVoiceIn": False,
        "supportsVoiceOut": True,
    },
    "canopylabs/orpheus-arabic-saudi": {
        "name": "CanopyLabs Orpheus Arabic Saudi",
        "summary": "Arabic text-to-speech voice generation.",
        "supportsText": False,
        "supportsImage": False,
        "supportsVoiceIn": False,
        "supportsVoiceOut": True,
    },
}


def _is_vision_model(model_id):
    caps = _infer_model_capabilities(model_id)
    if caps is not None:
        return bool(caps.get("supportsImage"))
    lowered = model_id.lower()
    return any(k in lowered for k in ["vision", "llama-4", "scout", "multimodal"])


def _infer_model_capabilities(model_id):
    known = KNOWN_GROQ_MODELS.get(model_id)
    if known is not None:
        return {
            "supportsText": bool(known.get("supportsText")),
            "supportsImage": bool(known.get("supportsImage")),
            "supportsVoiceIn": bool(known.get("supportsVoiceIn")),
            "supportsVoiceOut": bool(known.get("supportsVoiceOut")),
        }

    lowered = model_id.lower()
    if "whisper" in lowered:
        return {
            "supportsText": False,
            "supportsImage": False,
            "supportsVoiceIn": True,
            "supportsVoiceOut": False,
        }
    if "orpheus" in lowered:
        return {
            "supportsText": False,
            "supportsImage": False,
            "supportsVoiceIn": False,
            "supportsVoiceOut": True,
        }

    supports_image = any(k in lowered for k in ["vision", "llama-4", "scout", "multimodal"])
    return {
        "supportsText": True,
        "supportsImage": supports_image,
        "supportsVoiceIn": False,
        "supportsVoiceOut": False,
    }


def _model_modality_group(model_id):
    caps = _infer_model_capabilities(model_id)
    if caps["supportsVoiceIn"] or caps["supportsVoiceOut"]:
        return "voice"
    if caps["supportsText"] and caps["supportsImage"]:
        return "text & image"
    if caps["supportsImage"] and not caps["supportsText"]:
        return "image-only"
    return "text-only"


def _friendly_model_name(model_id):
    known = KNOWN_GROQ_MODELS.get(model_id)
    if known and known.get("name"):
        return known["name"]
    return model_id


def _model_summary(model_id):
    known = KNOWN_GROQ_MODELS.get(model_id)
    if known and known.get("summary"):
        return known["summary"]
    return "General-purpose model available on Groq."


def get_groq_model_catalog():
    if client is None:
        raise RuntimeError("Missing GROQ_API_KEY. Configure it in Railway Variables.")
    discovered_ids = []
    source = "fallback"
    try:
        listed = client.models.list()
        data = getattr(listed, "data", []) or []
        discovered_ids = [m.id for m in data if getattr(m, "id", None)]
        if discovered_ids:
            source = "api"
    except Exception:
        discovered_ids = []

    if not discovered_ids:
        discovered_ids = list(KNOWN_GROQ_MODELS.keys())

    # Prefer known production chat models first, then everything else alphabetically.
    preferred = [
        TEXT_MODEL,
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.1-8b-instant",
        VISION_MODEL,
        "groq/compound",
        "groq/compound-mini",
    ]
    discovered_set = set(discovered_ids)
    ordered_ids = []

    for model_id in preferred:
        if model_id in discovered_set and model_id not in ordered_ids:
            ordered_ids.append(model_id)

    for model_id in sorted(discovered_set):
        if model_id not in ordered_ids:
            ordered_ids.append(model_id)

    models = []
    for model_id in ordered_ids:
        models.append({
            "id": model_id,
            "name": _friendly_model_name(model_id),
            "summary": _model_summary(model_id),
            **_infer_model_capabilities(model_id),
            "group": _model_modality_group(model_id),
        })

    return {
        "source": source,
        "models": models,
    }


def _pick_vision_model(catalog_models):
    available_ids = {m["id"] for m in catalog_models}
    if VISION_MODEL in available_ids:
        return VISION_MODEL
    for m in catalog_models:
        if m.get("supportsText") and m.get("supportsImage"):
            return m["id"]
    return VISION_MODEL


def _pick_text_model(catalog_models):
    available_ids = {m["id"] for m in catalog_models}
    if TEXT_MODEL in available_ids:
        return TEXT_MODEL
    for m in catalog_models:
        if m.get("supportsText"):
            return m["id"]
    return TEXT_MODEL


def _model_map(catalog_models):
    return {m["id"]: m for m in catalog_models}


def resolve_chat_model(requested_model, is_image_attachment):
    catalog = get_groq_model_catalog()
    models = catalog["models"]
    available_ids = {m["id"] for m in models}
    model_lookup = _model_map(models)
    chosen = (requested_model or "").strip()
    fallback_note = None

    if is_image_attachment:
        vision_default = _pick_vision_model(models)
        if not chosen:
            return vision_default, fallback_note
        if chosen not in available_ids:
            return vision_default, "Selected model is unavailable; switched to default vision model."
        chosen_meta = model_lookup.get(chosen, {})
        if not (chosen_meta.get("supportsText") and chosen_meta.get("supportsImage")):
            return vision_default, "Selected model is text-only; switched to a vision-capable model for image analysis."
        return chosen, fallback_note

    text_default = _pick_text_model(models)
    if not chosen:
        return text_default, fallback_note
    if chosen not in available_ids:
        return text_default, "Selected model is unavailable; using the default chat model instead."

    chosen_meta = model_lookup.get(chosen, {})
    if not chosen_meta.get("supportsText"):
        return text_default, "Selected model is not a text chat model; switched to the default text model."

    if chosen_meta.get("supportsImage") and not is_image_attachment:
        return chosen, fallback_note

    if chosen_meta.get("supportsVoiceIn") or chosen_meta.get("supportsVoiceOut"):
        return text_default, "Selected model is voice-specialized; switched to the default text chat model."

    return chosen, fallback_note


def estimate_tokens_text(text):
    # Fast heuristic: ~4 characters per token for English-like text.
    return max(1, len(text) // 4)


def estimate_tokens_messages(messages):
    return sum(estimate_tokens_text(m.get('content', '')) for m in messages) + (4 * len(messages))


def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\t+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def chunk_text(text, chunk_size=CHUNK_SIZE_CHARS, overlap=CHUNK_OVERLAP_CHARS):
    text = normalize_text(text)
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(text), step):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(text):
            break
    return chunks


def score_chunk(query, chunk):
    terms = re.findall(r'[a-zA-Z0-9]{2,}', query.lower())
    if not terms:
        return 0
    lower_chunk = chunk.lower()
    hits = 0
    covered = 0
    for t in set(terms[:30]):
        count = lower_chunk.count(t)
        if count:
            covered += 1
            hits += count
    return (covered * 3) + hits


def build_retrieval_context(query, text, top_k=TOP_K_CHUNKS, max_chars=MAX_RETRIEVAL_CONTEXT_CHARS):
    chunks = chunk_text(text)
    if not chunks:
        return "", {"chunks_total": 0, "chunks_used": 0}

    if len(chunks) == 1:
        only = chunks[0][:max_chars]
        return f"[Chunk 1]\n{only}", {"chunks_total": 1, "chunks_used": 1}

    scored = []
    for i, c in enumerate(chunks):
        scored.append((score_chunk(query, c), i, c))

    scored.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    selected = sorted(scored[:top_k], key=lambda x: x[1])

    context_parts = []
    used = 0
    for _, idx, chunk in selected:
        part = f"[Chunk {idx + 1}]\n{chunk}"
        if used + len(part) > max_chars:
            remaining = max_chars - used
            if remaining <= 120:
                break
            part = part[:remaining]
        context_parts.append(part)
        used += len(part)
        if used >= max_chars:
            break

    return "\n\n".join(context_parts), {
        "chunks_total": len(chunks),
        "chunks_used": len(context_parts),
    }


def trim_messages_to_budget(messages, token_budget):
    # Keep system + newest turns, remove oldest turns first.
    while len(messages) > 2 and estimate_tokens_messages(messages) > token_budget:
        del messages[1]

    if estimate_tokens_messages(messages) <= token_budget:
        return True

    # Last resort: trim current user message.
    user_content = messages[-1].get('content', '')
    over = estimate_tokens_messages(messages) - token_budget
    remove_chars = (over * 4) + 300
    if len(user_content) > remove_chars + 300:
        messages[-1]['content'] = (
            user_content[:-remove_chars].rstrip()
            + "\n\n[Context truncated to fit model limits.]"
        )

    return estimate_tokens_messages(messages) <= token_budget


def build_user_message(message, attachment):
    question = (message or '').strip() or 'Please analyze the attached file.'
    prep_prefix = f"{PREP_MESSAGE}\n\n" if PREP_MESSAGE.strip() else ''

    if not attachment or not isinstance(attachment, dict):
        return prep_prefix + question, None

    name = str(attachment.get('name') or 'attached_file').strip()
    raw_content = attachment.get('content')
    raw_content = raw_content if isinstance(raw_content, str) else ''
    if not raw_content.strip():
        return prep_prefix + question, None

    normalized = normalize_text(raw_content)
    original_chars = int(attachment.get('originalChars') or len(normalized))
    server_truncated = False
    if len(normalized) > MAX_ATTACHMENT_CHARS:
        normalized = normalized[:MAX_ATTACHMENT_CHARS]
        server_truncated = True

    retrieval_context, stats = build_retrieval_context(question, normalized)
    frontend_truncated = bool(attachment.get('truncated'))

    truncation_note = ""
    if frontend_truncated or server_truncated:
        truncation_note = (
            f"\nAttachment length note: original was about {original_chars} chars; "
            f"processing is limited for context safety."
        )

    composed = (
        f"{prep_prefix}User question:\n{question}\n\n"
        f"Attached file: {name}\n"
        f"Relevant excerpts from the file are provided below. "
        f"Base your answer on these excerpts and be explicit if details are missing.{truncation_note}\n\n"
        f"{retrieval_context}"
    )

    meta = {
        "fileName": name,
        "charsUsed": len(normalized),
        "chunksTotal": stats["chunks_total"],
        "chunksUsed": stats["chunks_used"],
        "truncated": frontend_truncated or server_truncated,
    }
    return composed, meta


def build_vision_user_content(message, attachment):
    question = (message or '').strip() or 'Please analyze this image.'
    prep_prefix = f"{PREP_MESSAGE}\n\n" if PREP_MESSAGE.strip() else ''

    if not attachment or not isinstance(attachment, dict):
        return None, None

    data_url = str(attachment.get('dataUrl') or '').strip()
    if not data_url.startswith('data:image/'):
        return None, "Unsupported image format. Please attach a PNG, JPG, WEBP, GIF, or BMP image."
    if len(data_url) > MAX_IMAGE_DATA_URL_CHARS:
        return None, "Image is too large for processing. Please use a smaller image or compress it."

    prompt_text = (
        f"{prep_prefix}User question:\n{question}\n\n"
        "Analyze the attached image from pixels only. "
        "Handle screenshots, photos, memes, charts, and text in image. "
        "If uncertain, explicitly say what is unclear."
    )

    return [
        {"type": "text", "text": prompt_text},
        {"type": "image_url", "image_url": {"url": data_url}},
    ], None

@app.route('/')
def index():
    return render_template('index_new.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@app.route('/api/groq-models', methods=['GET'])
def groq_models():
    catalog = get_groq_model_catalog()
    return jsonify({
        "models": catalog["models"],
        "source": catalog["source"],
        "defaultTextModel": TEXT_MODEL,
        "defaultVisionModel": VISION_MODEL,
    })

# ─────────────────────────────────────────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = data.get('message', '')
    history = data.get('history', [])
    attachment = data.get('attachment')
    requested_model = data.get('model', '')

    is_image_attachment = isinstance(attachment, dict) and attachment.get('kind') == 'image'
    full_message, attachment_meta = build_user_message(message, attachment)
    vision_content = None
    if is_image_attachment:
        vision_content, vision_error = build_vision_user_content(message, attachment)
        if vision_error:
            return jsonify({"error": vision_error, "code": "image_validation"}), 400

    system_prompt = VISION_PROMPT if vision_content else SYSTEM_PROMPT
    model_name, model_notice = resolve_chat_model(requested_model, bool(vision_content))

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-MAX_HISTORY_MESSAGES:]:
        if msg.get('role') in ['user', 'assistant']:
            content = msg.get('content', '')
            if isinstance(content, str) and content.strip():
                messages.append({"role": msg['role'], "content": content})
    messages.append({"role": "user", "content": vision_content if vision_content else full_message})

    if not trim_messages_to_budget(messages, MAX_INPUT_TOKENS):
        return jsonify({
            "error": "Request is too large for the model context window. Please reduce attachment size or ask a more specific question.",
            "code": "context_limit"
        }), 413

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=MAX_OUTPUT_TOKENS,
        )
        reply = response.choices[0].message.content
        response_payload = {
            "reply": reply,
            "modelUsed": {
                "id": model_name,
                "name": _friendly_model_name(model_name),
                "summary": _model_summary(model_name),
            },
        }
        if model_notice:
            response_payload["modelNotice"] = model_notice
        if attachment_meta:
            response_payload["attachmentMeta"] = attachment_meta
        return jsonify(response_payload)
    except Exception as e:
        error_text = str(e)
        if 'context' in error_text.lower() or 'too large' in error_text.lower():
            return jsonify({
                "error": "Model context limit reached. Try a smaller attachment or narrower question.",
                "code": "context_limit"
            }), 413
        return jsonify({"error": error_text}), 500

# ─────────────────────────────────────────────────────────────────────────────
# TODO
# ─────────────────────────────────────────────────────────────────────────────

def get_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, 'r') as f:
            return [l for l in f.read().splitlines() if l.strip()]
    return []

def save_todos(todos):
    with open(TODO_FILE, 'w') as f:
        f.write('\n'.join(todos))

@app.route('/api/todo', methods=['GET', 'POST', 'DELETE'])
def todo():
    if request.method == 'GET':
        todos = get_todos()
        done = []
        if os.path.exists(DONE_FILE):
            with open(DONE_FILE, 'r') as f:
                done = [l for l in f.read().splitlines() if l.strip()]
        return jsonify({"todos": todos, "done": done})

    elif request.method == 'POST':
        data = request.get_json()
        action = data.get('action')

        if action == 'add':
            task = data.get('task', '').strip()
            if task:
                todos = get_todos()
                todos.append(task)
                save_todos(todos)
                return jsonify({"success": True, "todos": todos})

        elif action == 'done':
            idx = data.get('index')
            todos = get_todos()
            if 0 <= idx < len(todos):
                task = todos.pop(idx)
                save_todos(todos)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                with open(DONE_FILE, 'a') as f:
                    f.write(f"[{timestamp}] {task}\n")
                return jsonify({"success": True, "todos": todos})

        elif action == 'clear':
            todos = []
            save_todos(todos)
            return jsonify({"success": True, "todos": []})

        return jsonify({"error": "Invalid action"}), 400

# ─────────────────────────────────────────────────────────────────────────────
# TIMER
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/timer', methods=['POST'])
def timer():
    return jsonify({"work_minutes": 25, "break_minutes": 5})

# ─────────────────────────────────────────────────────────────────────────────
# NOTES
# ─────────────────────────────────────────────────────────────────────────────

def get_all_notes():
    notes = []
    if os.path.exists(NOTES_DIR):
        for f in sorted(os.listdir(NOTES_DIR)):
            if f.endswith('.md'):
                notes.append(f)
    return notes

def parse_note_header(filepath):
    title, subject, date = "Untitled", "general", "unknown"
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        in_front = False
        for line in lines:
            line = line.strip()
            if line == '---':
                in_front = not in_front
                continue
            if in_front:
                if line.startswith('title:'):
                    title = line.split(':', 1)[1].strip()
                elif line.startswith('subject:'):
                    subject = line.split(':', 1)[1].strip()
                elif line.startswith('date:'):
                    date = line.split(':', 1)[1].strip()
    except:
        pass
    return title, subject, date

@app.route('/api/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'GET':
        note_list = []
        for fname in get_all_notes():
            fpath = os.path.join(NOTES_DIR, fname)
            title, subject, date = parse_note_header(fpath)
            note_list.append({"filename": fname, "title": title, "subject": subject, "date": date})
        return jsonify({"notes": note_list})

    elif request.method == 'POST':
        data = request.get_json()
        action = data.get('action')

        if action == 'read':
            fname = data.get('filename')
            fpath = os.path.join(NOTES_DIR, fname)
            if os.path.exists(fpath):
                with open(fpath, 'r') as f:
                    raw = f.read()
                body = re.sub(r'^---.*?---\n', '', raw, flags=re.DOTALL).strip()
                title_match = re.search(r'^title:\s*(.+)$', raw, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else 'Untitled'
                return jsonify({"content": body, "title": title})
            return jsonify({"error": "Note not found"}), 404

        if action == 'create':
            title = data.get('title', 'Untitled').strip()
            subject = data.get('subject', 'general').strip().lower() or 'general'
            content = data.get('content', '')
            date_str = datetime.now().strftime("%Y-%m-%d")
            safe_title = title.lower().replace(' ', '-').replace('/', '-')
            fname = f"{date_str}_{subject}_{safe_title}.md"
            fpath = os.path.join(NOTES_DIR, fname)
            md = f"---\ntitle: {title}\nsubject: {subject}\ndate: {date_str}\ntags: [{subject}]\n---\n\n# {title}\n\n{content}\n"
            with open(fpath, 'w') as f:
                f.write(md)
            return jsonify({"success": True, "filename": fname})

        if action == 'update':
            old_filename = data.get('filename')
            title = data.get('title', 'Untitled').strip()
            subject = data.get('subject', 'general').strip().lower() or 'general'
            content = data.get('content', '')
            if old_filename:
                old_path = os.path.join(NOTES_DIR, old_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            date_str = datetime.now().strftime("%Y-%m-%d")
            safe_title = title.lower().replace(' ', '-').replace('/', '-')
            new_filename = f"{date_str}_{subject}_{safe_title}.md"
            fpath = os.path.join(NOTES_DIR, new_filename)
            md = f"---\ntitle: {title}\nsubject: {subject}\ndate: {date_str}\ntags: [{subject}]\n---\n\n# {title}\n\n{content}\n"
            with open(fpath, 'w') as f:
                f.write(md)
            return jsonify({"success": True, "filename": new_filename})

        if action == 'delete':
            filename = data.get('filename')
            fpath = os.path.join(NOTES_DIR, filename)
            if os.path.exists(fpath):
                os.remove(fpath)
                return jsonify({"success": True})
            return jsonify({"error": "Note not found"}), 404

    return jsonify({"error": "Invalid action"}), 400

# ─────────────────────────────────────────────────────────────────────────────
# MEDICAL
# ─────────────────────────────────────────────────────────────────────────────

MEDICAL_PROMPT = """You are an expert in medical terminology. Break down terms into prefix, root, and suffix. Use clear structure and rich text formatting when useful. Format:
Definition: [definition]
Word Parts: [breakdown]
Related Terms: [related]"""

@app.route('/api/medical', methods=['POST'])
def medical():
    data = request.get_json()
    term = data.get('term', '').strip()
    if not term:
        return jsonify({"error": "No term provided"}), 400
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": MEDICAL_PROMPT},
                {"role": "user", "content": f"Break down this medical term: {term}"}
            ]
        )
        reply = response.choices[0].message.content
        return jsonify({"result": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
# DECA — returns structured JSON for interactive quiz UI
# ─────────────────────────────────────────────────────────────────────────────

DECA_PROMPT = """You are an elite DECA coach creating ICDC-level PBM multiple choice questions.

Return ONLY valid JSON.

Return this exact structure:
{
  "questions": [
    {
      "id": 1,
      "question": "scenario-based question text here",
      "options": {
        "A": "option text",
        "B": "option text",
        "C": "option text",
        "D": "option text"
      },
      "answer": "C",
      "explanation": "Why C is correct, and briefly why each other option is wrong."
    }
  ]
}

Questions must be scenario-based, nuanced, and competition-difficulty."""

@app.route('/api/deca', methods=['POST'])
def deca():
    data = request.get_json()
    topic = data.get('topic', 'general').strip()
    count = data.get('count', 5)
    sample_exams = data.get('sampleExams', '').strip()

    # Build user prompt with sample context if provided
    user_prompt = f"Generate {count} ICDC-level DECA PBM questions on the topic: {topic}. Return only the JSON object."
    if sample_exams:
        user_prompt = f"Here are sample DECA exam questions for reference:\n{sample_exams}\n\nBased on this style and level, {user_prompt}"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": DECA_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        raw = response.choices[0].message.content.strip()

        # Strip any accidental markdown fences
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'^```\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)

        parsed = json.loads(raw)
        return jsonify(parsed)
    except json.JSONDecodeError as e:
        # Fallback: return error with raw for debugging
        return jsonify({"error": f"JSON parse failed: {str(e)}", "raw": raw[:500]}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
# FILE LOAD
# ─────────────────────────────────────────────────────────────────────────────

def read_file(filepath):
    filepath = filepath.strip().strip('"').strip("'")
    filepath = re.sub(r'\\(.)', r'\1', filepath)
    if not os.path.exists(filepath):
        return None, "File not found", None
    if os.path.getsize(filepath) > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        return None, f"File too large. Max allowed is {max_mb:.1f} MB.", None

    meta = {
        "truncated": False,
        "originalChars": 0,
        "charsUsed": 0,
        "pagesRead": None,
        "totalPages": None,
    }

    if filepath.lower().endswith('.pdf'):
        try:
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
                pages_to_read = min(total_pages, MAX_PDF_PAGES)
                for page in reader.pages[:pages_to_read]:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"

            text = normalize_text(text)
            meta["totalPages"] = total_pages
            meta["pagesRead"] = pages_to_read
            meta["originalChars"] = len(text)

            if len(text) > MAX_TEXT_CHARS:
                text = text[:MAX_TEXT_CHARS]
                meta["truncated"] = True
            meta["charsUsed"] = len(text)

            if not text:
                return None, "PDF has no extractable text", None
            return text, None, meta
        except Exception as e:
            return None, str(e), None
    else:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read(MAX_TEXT_CHARS + 1)
            meta["originalChars"] = len(text)
            if len(text) > MAX_TEXT_CHARS:
                text = text[:MAX_TEXT_CHARS]
                meta["truncated"] = True
            text = normalize_text(text)
            meta["charsUsed"] = len(text)
            return text, None, meta
        except Exception as e:
            return None, str(e), None

@app.route('/api/load', methods=['POST'])
def load_file():
    data = request.get_json()
    filepath = data.get('filepath', '')
    content, error, meta = read_file(filepath)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({
        "content": content,
        "filename": os.path.basename(filepath),
        "meta": meta,
    })

# ─────────────────────────────────────────────────────────────────────────────
# WEB SEARCH
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/search', methods=['POST'])
def web_search():
    data = request.get_json()
    query = data.get('query', '').strip()
    offset = data.get('offset', 0)
    if not query:
        return jsonify({"error": "No query provided"}), 400
    try:
        import urllib.parse
        from urllib.request import Request, urlopen
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}&b={offset}"
        req = Request(search_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urlopen(req, context=ctx, timeout=10) as response:
            html = response.read().decode('utf-8')

        results = []
        pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.+?)</a>.*?<a class="result__url"[^>]*>(.+?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        for url, title, domain in matches[:5]:
            title = re.sub(r'<[^>]+>', '', title).strip()
            domain = domain.strip()
            full_url = url if url.startswith('http') else f'https://{domain}'
            results.append({"title": title[:200], "url": full_url, "summary": f"Click to view {domain}"})

        if not results:
            simple_pattern = r'class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)'
            for url, title in re.findall(simple_pattern, html)[:5]:
                title = title.strip()
                if title and 'http' in url:
                    results.append({"title": title[:200], "url": url, "summary": "Click to view"})

        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/summarize', methods=['POST'])
def summarize_url():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        import urllib.request, ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')

        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()[:3000]

        if not text:
            return jsonify({"summary": "Could not extract content from page"}), 200

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Summarize this web page in 2-3 sentences. Use markdown formatting if it helps clarity."},
                {"role": "user", "content": f"Summarize:\n\n{text}"}
            ]
        )
        return jsonify({"summary": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"summary": f"Could not fetch page: {str(e)[:50]}"}), 200

# ─────────────────────────────────────────────────────────────────────────────
# NEWS — multi-continent, AI summary per article
# ─────────────────────────────────────────────────────────────────────────────

# News sources labeled by continent. We scrape RSS feeds (XML) which are far
# more reliable than scraping HTML front pages.
NEWS_SOURCES = [
    # North America
    {"url": "https://feeds.npr.org/1001/rss.xml",              "name": "NPR",              "continent": "North America"},
    {"url": "https://apnews.com/rss",                          "name": "AP News",           "continent": "North America"},
    # Europe
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml",      "name": "BBC World",         "continent": "Europe"},
    {"url": "https://www.theguardian.com/world/rss",           "name": "The Guardian",      "continent": "Europe"},
    {"url": "https://www.lemonde.fr/rss/une.xml",              "name": "Le Monde",          "continent": "Europe"},
    # Asia
    {"url": "https://www3.nhk.or.jp/rss/news/cat0.xml",        "name": "NHK World",         "continent": "Asia"},
    {"url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "name": "Times of India", "continent": "Asia"},
    {"url": "https://www.scmp.com/rss/91/feed",               "name": "South China Morning Post", "continent": "Asia"},
    # Middle East
    {"url": "https://www.aljazeera.com/xml/rss/all.xml",       "name": "Al Jazeera",        "continent": "Middle East"},
    {"url": "https://www.timesofisrael.com/feed/",             "name": "Times of Israel",   "continent": "Middle East"},
    # Africa
    {"url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "name": "AllAfrica", "continent": "Africa"},
    {"url": "https://www.dailymaverick.co.za/feed/",           "name": "Daily Maverick",    "continent": "Africa"},
    # South America
    {"url": "https://www.mercopress.com/rss",                  "name": "MercoPress",        "continent": "South America"},
    # Oceania
    {"url": "https://www.abc.net.au/news/feed/51120/rss.xml",  "name": "ABC Australia",     "continent": "Oceania"},
]

def fetch_rss(source, max_items=2):
    """Fetch and parse an RSS feed, returning up to max_items articles."""
    import urllib.request, ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(source["url"], headers={
            'User-Agent': 'Mozilla/5.0 (compatible; NewsReader/1.0)'
        })
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            xml = resp.read().decode('utf-8', errors='ignore')

        articles = []
        # Parse <item> blocks from RSS
        items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL)
        for item in items[:max_items]:
            # Title
            title_match = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL)
            title = title_match.group(1).strip() if title_match else ''
            title = re.sub(r'<[^>]+>', '', title).strip()

            # Link
            link_match = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
            if not link_match:
                link_match = re.search(r'<guid[^>]*>(https?://[^<]+)</guid>', item)
            link = link_match.group(1).strip() if link_match else ''

            # Description / summary snippet (not AI — just the RSS blurb)
            desc_match = re.search(r'<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item, re.DOTALL)
            desc = desc_match.group(1).strip() if desc_match else ''
            desc = re.sub(r'<[^>]+>', '', desc).strip()[:200]

            if title and link and len(title) > 15:
                articles.append({
                    "title": title,
                    "url": link,
                    "source": source["name"],
                    "continent": source["continent"],
                    "snippet": desc,  # raw RSS blurb; AI summary added below
                    "summary": ""
                })
        return articles
    except Exception:
        return []

def ai_summarize_snippet(snippet, title):
    """Use Groq to write a clean 1-2 sentence summary from the RSS snippet."""
    if not snippet:
        return ""
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Write a 1-2 sentence plain-text summary of this news article based on its title and description. Be informative and neutral."},
                {"role": "user", "content": f"Title: {title}\nDescription: {snippet}"}
            ],
            max_tokens=80
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return snippet[:150]

@app.route('/api/news', methods=['POST', 'GET'])
def news():
    """
    Fetch articles from global RSS sources, then generate an AI summary for each.
    We collect 1-2 articles per source to get good continental diversity.
    """
    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        all_articles = []
        seen_titles = set()

        # Fetch all RSS sources concurrently for speed
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(fetch_rss, src, 2): src for src in NEWS_SOURCES}
            for future in as_completed(futures):
                try:
                    articles = future.result()
                    for a in articles:
                        if a['title'] not in seen_titles and len(all_articles) < 20:
                            seen_titles.add(a['title'])
                            all_articles.append(a)
                except Exception:
                    pass

        # Generate AI summaries concurrently (limit to first 12 articles for speed)
        articles_to_summarize = all_articles[:12]

        def summarize_article(article):
            article['summary'] = ai_summarize_snippet(article.get('snippet', ''), article['title'])
            return article

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(summarize_article, a) for a in articles_to_summarize]
            summarized = [f.result() for f in futures]

        # Sort by continent for visual variety
        continent_order = ["North America", "Europe", "Asia", "Middle East", "Africa", "South America", "Oceania"]
        summarized.sort(key=lambda a: continent_order.index(a['continent']) if a['continent'] in continent_order else 99)

        return jsonify({"articles": summarized})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTICATION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({"error": "Missing username, email, or password"}), 400
    
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    result = user_manager.register_user(username, email, password)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({"message": "User registered successfully"}), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and return session token"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    result = user_manager.login_user(username, password)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 401
    
    return jsonify({
        "session_token": result['session_token'],
        "username": result['user']['username'],
        "message": "Login successful"
    }), 200


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    data = request.get_json() or {}
    session_token = data.get('session_token', '')
    
    user_manager.logout_user(session_token)
    return jsonify({"message": "Logged out successfully"}), 200


@app.route('/api/auth/verify', methods=['GET'])
def verify_auth():
    """Verify session token"""
    session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not session_token:
        return jsonify({"authenticated": False}), 401
    
    result = user_manager.verify_session(session_token)
    
    if not result['valid']:
        return jsonify({"authenticated": False}), 401
    
    return jsonify({
        "authenticated": True,
        "user": result['user']
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# CHAT HISTORY ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/chats', methods=['GET'])
def list_chats():
    """List all chats for authenticated user"""
    session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    result = user_manager.verify_session(session_token)
    if not result['valid']:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = result['user']['id']
    chats_result = chat_manager.get_user_chats(user_id)
    
    if not chats_result['success']:
        return jsonify({"error": chats_result.get('error', 'Failed to fetch chats')}), 500
    
    return jsonify({"chats": chats_result['chats']}), 200


@app.route('/api/chats', methods=['POST'])
def create_chat():
    """Create a new chat"""
    session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    result = user_manager.verify_session(session_token)
    if not result['valid']:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = result['user']['id']
    data = request.get_json() or {}
    title = data.get('title', 'New Chat')
    
    chat_result = chat_manager.create_chat(user_id, title)
    
    if not chat_result['success']:
        return jsonify({"error": chat_result.get('error', 'Failed to create chat')}), 500
    
    return jsonify({
        "chat_id": chat_result['chat_id'],
        "title": chat_result['title'],
        "created_at": chat_result['created_at']
    }), 201


@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get a specific chat"""
    session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    result = user_manager.verify_session(session_token)
    if not result['valid']:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = result['user']['id']
    chat_result = chat_manager.get_chat(chat_id, user_id)
    
    if not chat_result['success']:
        return jsonify({"error": chat_result.get('error', 'Chat not found')}), 404
    
    return jsonify(chat_result), 200


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat"""
    session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    result = user_manager.verify_session(session_token)
    if not result['valid']:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = result['user']['id']
    delete_result = chat_manager.delete_chat(chat_id, user_id)
    
    if not delete_result['success']:
        return jsonify({"error": delete_result.get('error', 'Chat not found')}), 404
    
    return jsonify({"message": "Chat deleted"}), 200


@app.route('/api/chats/<chat_id>/messages', methods=['POST'])
def add_chat_message(chat_id):
    """Add a message to a chat"""
    session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    result = user_manager.verify_session(session_token)
    if not result['valid']:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = result['user']['id']
    data = request.get_json() or {}
    role = data.get('role', 'user')
    content = data.get('content', '')
    
    if not content:
        return jsonify({"error": "Message content required"}), 400
    
    msg_result = chat_manager.add_message(chat_id, user_id, role, content)
    
    if not msg_result['success']:
        return jsonify({"error": msg_result.get('error', 'Failed to add message')}), 500
    
    return jsonify({
        "message_id": msg_result['message_id'],
        "timestamp": msg_result['timestamp']
    }), 201


if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=port, host='0.0.0.0')