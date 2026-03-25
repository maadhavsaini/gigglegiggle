# Derei Assistant

A multifunction AI assistant project with two interfaces:

- **Web app** built with Flask + Groq (`app.py`)
- **Terminal app** built with Rich + Groq (`chatbot.py`)

This project combines chat, model selection, notes, to-do workflow, DECA prep, medical term breakdowns, web search + URL summarization, and global RSS news summarization.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Core Features](#core-features)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Run the Project](#run-the-project)
- [API Reference (Web)](#api-reference-web)
- [Terminal Commands](#terminal-commands)
- [Configuration Notes](#configuration-notes)
- [Security and Code Protection](#security-and-code-protection)
- [Deployment Notes](#deployment-notes)
- [Troubleshooting](#troubleshooting)
- [Roadmap Ideas](#roadmap-ideas)

---

## Project Overview

Derei Assistant is designed as a **student-focused productivity and learning assistant**.

It supports:

- General AI chat with history
- Dynamic Groq model catalog + model-specific routing
- Vision chat for image attachments
- File-aware Q&A with text/PDF ingestion
- Structured study modes (DECA, medical terminology, essay feedback, math helper)
- Productivity modules (to-do + pomodoro timer + notes)
- Lightweight web intelligence (search + URL summarize + global news summaries)

---

## Core Features

### 1) AI Chat (Web + Terminal)

- Uses Groq Chat Completions
- Supports conversation history
- Supports optional preloaded file context
- Supports private mode in terminal (no persistence when enabled)

### 2) Model Discovery and Selection

- Exposes `/api/groq-models`
- Maintains known model metadata (friendly names, modality support)
- Auto-falls back to safe defaults when model metadata is unavailable

### 3) Vision and Attachments

- Accepts image attachments with validation limits
- Routes image requests to a vision-capable model
- Supports text/PDF ingestion with chunking + retrieval context

### 4) Productivity Toolkit

- To-do list CRUD + completed-task history
- Pomodoro settings endpoint and terminal timer flow
- Markdown note management with YAML frontmatter

### 5) Learning Tools

- DECA PBM quiz generation and coaching
- Medical terminology decomposition
- Essay feedback
- Math step-by-step solving prompts

### 6) Web Intelligence

- DuckDuckGo HTML search parsing
- URL fetch + extraction + summarization
- Multi-continent RSS fetch + AI summary per article

---

## Tech Stack

- **Backend:** Python, Flask
- **LLM Provider:** Groq Python SDK
- **Terminal UI:** Rich
- **Document Parsing:** PyPDF2
- **Config/Secrets:** python-dotenv
- **Frontend:** HTML/CSS/JS (single-page style template)

---

## Repository Structure

```text
CHATBOT HOSTING FILES/
  app.py
  chatbot.py
  derei_constitution.md
  requirements.txt
  .env
  static/
    design-system.css
  templates/
    index.html
```

---

## Setup

### Prerequisites

- Python 3.10+
- pip
- A valid Groq API key

### Install dependencies

```bash
cd "CHATBOT HOSTING FILES"
pip install -r requirements.txt
```

> Note: `chatbot.py` uses packages like `rich` (and optionally `huggingface_hub` for image generation flow). If you use terminal-only advanced commands, install any missing optional dependencies.

---

## Environment Variables

Create or edit `.env` in `CHATBOT HOSTING FILES`:

```env
GROQ_API_KEY=your_real_groq_key_here
```

The code now reads `GROQ_API_KEY` from `.env` in both `app.py` and `chatbot.py`.

---

## Run the Project

### Run Web App

```bash
cd "CHATBOT HOSTING FILES"
python app.py
```

Default:

- Host: `0.0.0.0`
- Port: `5000`
- URL: `http://localhost:5000`

### Run Terminal App

```bash
cd "CHATBOT HOSTING FILES"
python chatbot.py
```

---

## API Reference (Web)

### `GET /`

Serves the main web interface.

### `GET /api/groq-models`

Returns available/known Groq models and defaults.

### `POST /api/chat`

Primary chat endpoint.

Expected JSON fields:

- `message` (string)
- `history` (array)
- `model` (optional string)
- `attachment` (optional object)

### `GET|POST|DELETE /api/todo`

Manage task list and completed task history.

### `POST /api/timer`

Returns timer defaults.

### `GET|POST /api/notes`

Read/create/update/delete note content via action payload.

### `POST /api/medical`

Medical term breakdown endpoint.

### `POST /api/deca`

Generates DECA PBM structured question JSON.

### `POST /api/load`

Loads text/PDF file content for assistant context.

### `POST /api/search`

Searches web results (DuckDuckGo HTML endpoint parsing).

### `POST /api/summarize`

Fetches and summarizes URL content.

### `GET|POST /api/news`

Aggregates RSS articles by continent and generates concise AI summaries.

---

## Terminal Commands

`chatbot.py` includes command-driven utilities such as:

- `load`
- `essay`
- `image`
- `math`
- `todo`
- `timer`
- `deca`
- `note`
- `medical`
- `private`
- `lock`
- `paste`
- `exit`

Behavior highlights:

- **Private mode** avoids saving messages to disk
- Chat logs persist when private mode is off
- Daily task seeding is supported

---

## Configuration Notes

Current code uses absolute local paths for some storage locations (chat logs, notes, todo files). If you run on a different machine, update these constants in `app.py` and `chatbot.py`.

Recommended improvement:

- Move all filesystem paths into environment variables for portability and safer deployment.

---

## Security and Code Protection

No method can guarantee that source code is impossible to copy once someone has access. What you can do is make copying **legally risky**, **operationally difficult**, and **technically inconvenient**.

### 1) Legal protections (highest impact)

- Add a **Proprietary License** (All Rights Reserved) **(implemented: see `LICENSE`)**
- Include explicit copyright notice in this repository
- Define commercial-use restrictions and enforcement policy

### 2) Access controls

- Keep repository private
- Enforce organization/team permissions
- Require branch protection + PR review
- Enable mandatory 2FA for collaborators

### 3) Secret hygiene (already started)

- Keep API keys in `.env` only
- Never commit `.env` with real secrets **(implemented: see `.gitignore`)**
- Rotate keys immediately if exposed
- Enable secret scanning in your Git host

### 4) Release strategy

- Do not distribute full source to untrusted parties
- If distributing software, ship compiled/packaged artifacts when possible
- Consider obfuscation for selected modules (deterrent only, not a true lock)

### 5) Runtime and infra controls

- Put sensitive logic server-side only
- Add auth and rate limits for public endpoints
- Monitor logs for abuse and unusual usage patterns

### 6) Team process controls

- Use signed commits/tags for provenance
- Keep dependency and security patch cadence
- Document ownership and contributor agreements

---

## Deployment Notes

Before production deployment:

- Set `debug=False`
- Run behind a production WSGI server (e.g., gunicorn)
- Terminate TLS at reverse proxy/load balancer
- Add request size limits and API rate limits
- Externalize all local absolute paths into env vars

---

## Troubleshooting

### Missing API key

If startup fails with a missing key error:

1. Confirm `.env` exists in `CHATBOT HOSTING FILES`
2. Confirm variable name is exactly `GROQ_API_KEY`
3. Restart the process after editing `.env`

### Package errors

Install requirements again:

```bash
pip install -r requirements.txt
```

If a terminal feature still fails, install missing optional dependency and re-run.

### Port already in use

Change the port in `app.py` or stop the conflicting process.

---

## Roadmap Ideas

- Add authentication and user profiles
- Move storage to database instead of plain files
- Add tests for API routes and utility functions
- Add CI checks (lint, test, security scan)
- Introduce structured logging + observability
- Extract config to dedicated settings module
