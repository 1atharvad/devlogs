# blog_rag

Reusable Django app that adds a RAG (retrieval-augmented generation) chat API to any Django project. Built with LangGraph, pgvector, Google Gemini embeddings, and OpenRouter.

## How it works

- Blog posts are fetched from an RSS feed, split into chunks, embedded with Gemini, and stored in PostgreSQL via pgvector.
- A LangGraph ReAct agent decides when to search the vector store and answers questions using only content from the blog.
- Conversation history is kept per session so follow-up questions work naturally.
- A Vercel deploy webhook triggers an automatic re-sync whenever new content is published.

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
    "GOOGLE_API_KEY": "your-gemini-api-key",
    "OPENROUTER_API_KEY": "your-openrouter-key",
    "RSS_URL": "https://blog.atharvadevasthali.com/rss.xml",  # default, can override
    "SYNC_SECRET": "long-random-string-from-vercel-webhook",  # see Vercel setup below

    # Optional — these are the defaults
    "EMBEDDING_MODEL": "models/gemini-embedding-001",
    "EMBEDDING_DIMENSIONS": 3072,
    "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    "CHAT_MODEL": "openai/gpt-4o-mini",
    "TOP_K": 5,
    "CHUNK_SIZE": 500,
    "CHUNK_OVERLAP": 50,
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
| `POST` | `/rag/sync/` | Webhook — re-syncs content from RSS |

### POST /rag/chat/

```json
// Request
{
  "message": "How do you rate limit with Nginx?",
  "session_id": "abc123",        // optional — omit to start a new session
  "link": "https://yourblog.com/some-post"  // optional — current page context
}

// Response
{
  "answer": "You can use Nginx's `limit_req_zone` directive to rate limit by IP.",
  "session_id": "abc123",
  "sources": [
    { "title": "Rate Limiting with Nginx", "source": "https://blog.atharvadevasthali.com/rate-limiting-nginx" }
  ]
}
```

`sources` contains every blog post the agent retrieved, deduplicated by URL. It will be an empty array if the agent answered from conversation history without searching.

```json
```

Pass the returned `session_id` back on follow-up messages to maintain conversation history.

### GET /rag/search/

```
GET /rag/search/?q=nginx+rate+limiting&k=5
```

```json
[
  { "title": "Rate Limiting with Nginx", "source": "https://...", "content": "..." },
  ...
]
```

---

## Automatic sync via Vercel webhook

Every time you publish new content and Vercel finishes deploying, it automatically triggers a re-sync so the vector store stays up to date.

### 1. Create the webhook in Vercel

- Go to **vercel.com → Team Settings → Webhooks**
- Click **Add Webhook**
- URL: `https://your-contabo-domain.com/rag/sync/`
- Events: check **Deployment Succeeded**
- Click **Create** — Vercel shows you a **signing secret** once. Copy it now.

### 2. Store the secret as an environment variable on your server

Never hardcode secrets in the repo. On your Contabo server, add it to your environment (`.env` file or shell profile):

```bash
export BLOG_RAG_SYNC_SECRET="paste-the-vercel-signing-secret-here"
```

To generate your own secret instead (e.g. if you need to rotate it):
```bash
openssl rand -hex 32
```
Then update both the Vercel webhook secret field and this env var to match.

### 3. Read it in Django `settings.py`

```python
import os

BLOG_RAG = {
    "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY"),
    "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY"),
    "SYNC_SECRET": os.environ.get("BLOG_RAG_SYNC_SECRET"),
}
```

That's it. Vercel will POST to `/rag/sync/` after every production deploy. Preview deploys are ignored automatically. The sync runs in a background thread so the webhook response returns immediately.

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
