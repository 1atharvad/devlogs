---
title: "Building the blog_rag Django Package"
description: "A full build log of the blog_rag reusable Django app — pgvector embeddings, LangGraph chat agent, GitHub Actions post-deploy sync, APScheduler cron, and SSE log streaming."
pubDate: "Jun 04 2026"
primaryTag: "AI"
tags: ["Python", "Django", "RAG", "LangGraph", "PostgreSQL", "GitHub Actions"]
---

The blog already had a working RAG pipeline — an n8n workflow syncing posts into Supabase, a Gemini agent answering questions. The [previous devlog](/devlogs/building-ai-agent-for-devlogs) covers that version. This is the rewrite: a proper Django app package that can be dropped into any Django project with two lines of config.

## The Settings Bridge

The package ships with defaults for everything except API keys. The host project only sets what it needs:

```python
INSTALLED_APPS = [..., "blog_rag"]

BLOG_RAG = {
    "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY"),
    "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY"),
    "SYNC_SECRET": os.environ.get("SYNC_SECRET"),
}
```

`conf.py` is a single `get(key)` function that reads from `settings.BLOG_RAG` first, falls back to `DEFAULTS`. Every configurable value goes through it — one place to see what the package can be configured with, and the defaults are always explicit.

## Vector Store

`DocumentChunk` is the only model. A post gets split into overlapping text chunks, each chunk gets a 3072-dimensional Gemini embedding, and everything lives in the same postgres database as the rest of the app. No separate vector service. `pgvector`'s `CosineDistance` handles similarity search directly in postgres.

This works because the corpus is small — a personal blog with a few hundred chunks. At scale (tens of thousands of documents), postgres isn't the right tool for vector workloads. Self-hosting pgvector at that point means managing indexing, memory pressure, and query performance yourself. A managed service like Pinecone or Supabase's hosted pgvector handles all that.

## Content Sync

`sync_from_rss` is a management command that reads the blog's RSS feed, fetches each post's full body via an `apiUrl` field in the feed, splits it into chunks, embeds them with Gemini, and upserts into `DocumentChunk`. Posts are skipped unless their `modified_time` has changed. `--force` re-embeds everything. Gemini's embedding API rate-limits at per-minute quotas — the command retries on 429 with a 60-second wait.

## The Chat Agent

A LangGraph ReAct agent with a single `search_blog` tool. The agent decides when to search based on the conversation. Session memory via `MemorySaver` — in-process, not shared across workers, gone on restart. For a single-worker setup that's fine; swap to `PostgresSaver` for multi-process deployments.

The prompt has a specific rule for the `[User is currently viewing: ...]` tag that the frontend injects into messages. The tag is metadata from the frontend — not something the user typed — so the agent only uses it when the question is clearly about the current page.

## Post-Deploy Sync via GitHub Actions

Keeping the vector store current after publishing a new post required a trigger after Vercel deploys. The obvious choice — Vercel webhooks — is a paid feature. The free alternative: GitHub Actions `deployment_status` events.

Vercel writes deployment statuses to GitHub automatically. A workflow listens for those events and calls `/rag/sync/` after every production success:

```yaml
on:
  deployment_status:

jobs:
  sync:
    if: |
      github.event_name == 'workflow_dispatch' ||
      (github.event.deployment_status.state == 'success' &&
      github.event.deployment_status.environment == 'Production')
    environment: production
```

`workflow_dispatch` is also enabled so the sync can be triggered manually from GitHub Actions without needing a deploy.

Auth is a Bearer token — `SYNC_SECRET` stored in GitHub's production environment secrets and read from the Django server's `.env`. Same value, both sides.

## Scheduled Sync (Optional)

Disabled by default — no scheduler runs unless you opt in. If deploys don't correlate with content changes, set `SYNC_CRON_HOURS` in `BLOG_RAG` and the scheduler starts automatically with Django:

```python
"SYNC_CRON_HOURS": "0,6,12,18",  # midnight, 6am, noon, 6pm
```

Uses a cron trigger rather than an interval so deploys don't reset the clock. A `RUN_MAIN` guard prevents it firing twice under `manage.py runserver` — Django's dev server spawns two processes (a watcher and the main process), so without the guard the scheduler starts in both. Checking `os.environ.get("RUN_MAIN")` skips the reloader process and only starts in the main one.

## SSE Log Streaming

The sync endpoint runs in a background thread and returns immediately — which is what GitHub Actions needs to avoid timing out. But that made it hard to see what actually happened.

POST to `/rag/sync/` now returns a `job_id`. GET to `/rag/sync/?job_id=...` streams the management command's output as SSE until done:

```
data: Fetching RSS: https://blog.atharvadevasthali.com/rss.xml
data: Found 13 posts
data:   skip    abc123
data:   new     def456
data: Done — new: 1  updated: 0  skipped: 12
data: [done]
```

The background thread writes to a `queue.Queue` via a custom `_Writer`. The SSE stream reads from that queue with a 30-second timeout, yielding `: keepalive` pings during the gaps (Gemini embedding calls can take a while). The queue entry is cleaned up after the stream closes.

The GitHub Actions workflow POSTs to get the `job_id`, then streams the GET response and prints each line until `[done]`.
