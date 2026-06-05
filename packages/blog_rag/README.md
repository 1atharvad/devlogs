# blog_rag

Reusable Django app that adds a RAG (retrieval-augmented generation) chat API to any Django project. Built with LangGraph, pgvector, Google Gemini embeddings, and OpenRouter.

## How it works

- Blog posts are fetched from an RSS feed, split into chunks, embedded with Gemini, and stored in PostgreSQL via pgvector.
- A LangGraph ReAct agent decides when to search the vector store and answers questions using only content from the blog.
- Conversation history is kept per session so follow-up questions work naturally.
- A GitHub Actions workflow triggers an automatic re-sync whenever Vercel reports a successful production deployment.

---

## Prerequisites

- Python 3.11+
- PostgreSQL with the pgvector extension
- A Google Gemini API key (for embeddings)
- An OpenRouter API key (for the chat model)

Enable pgvector in your database:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Installation

Install from the repo:
```bash
pip install git+https://github.com/your-username/devlogs.git#subdirectory=packages/blog_rag
```

Or editable from a local clone:
```bash
pip install -e /path/to/devlogs/packages/blog_rag
```

---

## Django setup

**1. Add to `INSTALLED_APPS` in `settings.py`:**
```python
INSTALLED_APPS = [
    ...
    "rest_framework",
    "blog_rag",
]
```

**2. Add the `BLOG_RAG` config block to `settings.py`:**
```python
BLOG_RAG = {
    # Required
    "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY"),
    "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY"),
    "SYNC_SECRET": os.environ.get("SYNC_SECRET"),  # shared with GitHub Actions

    # Optional — these are the defaults
    "RSS_URL": "https://blog.atharvadevasthali.com/rss.xml",
    "EMBEDDING_MODEL": "models/gemini-embedding-001",
    "EMBEDDING_DIMENSIONS": 3072,
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    "CHAT_MODEL": "openai/gpt-4o-mini",
    "TOP_K": 5,
    "CHUNK_SIZE": 500,
    "CHUNK_OVERLAP": 50,
    "SYNC_CRON_HOURS": None,  # e.g. "0,6,12,18" to sync at fixed times of day
}
```

**3. Mount the URLs in `urls.py`:**
```python
from django.urls import path, include

urlpatterns = [
    ...
    path("rag/", include("blog_rag.urls")),
]
```

**4. Run migrations:**
```bash
python manage.py migrate
```

**5. Do the initial content sync:**
```bash
python manage.py sync_from_rss https://blog.atharvadevasthali.com/rss.xml
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/rag/chat/` | Send a message, get an answer from the agent |
| `GET` | `/rag/search/` | Raw vector similarity search (no LLM) |
| `POST` | `/rag/sync/` | Trigger a content re-sync from RSS |

### POST /rag/chat/

```json
// Request
{
  "message": "How do you rate limit with Nginx?",
  "session_id": "abc123",
  "link": "https://yourblog.com/some-post"
}

// Response
{
  "answer": "...",
  "session_id": "abc123",
  "sources": [
    { "title": "Post title", "source": "https://..." }
  ]
}
```

`session_id` is optional — omit to start a new session, pass it back on follow-ups to maintain history. `link` is optional — the current page URL, used as context only when the question is about that page. `sources` is empty if the agent answered from history without searching.

### GET /rag/search/

```
GET /rag/search/?q=nginx+rate+limiting&k=5
```

```json
[
  { "title": "...", "source": "https://...", "content": "..." }
]
```

---

## Automatic sync after Vercel deploy

The GitHub Actions workflow at `.github/workflows/sync-rag.yml` listens for Vercel's `deployment_status` event and calls `/rag/sync/` after every successful production deployment. No Vercel paid plan needed — this uses GitHub's native deployment status events which Vercel writes automatically.

### Setup

**1. Generate a secret:**
```bash
openssl rand -hex 32
```

**2. Your server `.env`** — Django reads this to verify incoming requests:
```bash
SYNC_SECRET=your-generated-secret
```

**3. GitHub repo secrets** (Settings → Secrets → Actions) — GitHub Actions reads these to make the request:

| Secret | Value | Why |
|--------|-------|-----|
| `RAG_SYNC_URL` | `https://atharvadevasthali.com/api/blog/sync/` | the URL to POST to |
| `SYNC_SECRET` | same value as step 2 | sent as the Bearer token |

Vercel env vars are not involved — Vercel only builds the frontend. GitHub Actions is what calls your server after Vercel finishes.

That's it. Every time Vercel finishes a production deploy, GitHub Actions POSTs to `/rag/sync/` and the vector store re-syncs in the background.

---

## Periodic sync (optional)

If you want the vector store to stay fresh on a schedule regardless of deploys, set `SYNC_CRON_HOURS` in your `BLOG_RAG` config. The scheduler starts with Django and fires at the specified hours of the day:

```python
BLOG_RAG = {
    ...
    "SYNC_CRON_HOURS": "0,6,12,18",  # sync at midnight, 6am, noon, 6pm
}
```

The schedule is time-based, not interval-based — deploys don't reset the clock.

---

## Syncing content manually

```bash
# Sync new and updated posts only
python manage.py sync_from_rss https://blog.atharvadevasthali.com/rss.xml

# Force re-embed everything regardless of modified time
python manage.py sync_from_rss https://blog.atharvadevasthali.com/rss.xml --force
```

---

## Running tests

```bash
cd packages/blog_rag
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -v
```

Or via npm from the repo root:
```bash
npm run setup:rag
npm run test:rag
```
