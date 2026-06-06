---
title: "Free Post-Deploy Vector Store Sync with GitHub Actions"
description: "Vercel webhooks are a paid feature. GitHub Actions deployment_status events are free — and Vercel writes them automatically. How I wired up post-deploy RAG sync without touching a paid plan."
pubDate: "Jun 06 2026"
primaryTag: "GitHub Actions"
tags: ["Python", "Django", "RAG", "Vercel"]
---

Any RAG system has a sync problem: the vector store needs to stay current with the actual content. New post published, vector store should update. The question is what triggers that update.

The setup here: a Django backend serving a RAG chat widget, content published via Vercel, vector store on the same postgres instance. The [full package build](/devlogs/blog-rag-django-package-build) covers the whole system. This is just the sync trigger.

## The Obvious Approach Doesn't Work

Vercel has a webhooks feature — configure an endpoint, and Vercel POSTs to it on deployment events. That's exactly what's needed. It's also a paid feature, not available on the free plan.

The sync endpoint was already built. The problem was getting it called automatically after a successful production deploy.

## GitHub Actions deployment_status Events

Vercel writes deployment status updates to GitHub automatically on every deploy — no configuration, no paid plan, this happens by default. GitHub Actions can listen for those events:

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
    runs-on: ubuntu-latest
```

The condition filters for production deploys that succeeded. `workflow_dispatch` is also enabled so the sync can be triggered manually from GitHub Actions without needing a deploy — useful for testing or forcing a full re-sync.

Auth is a Bearer token — `SYNC_SECRET` stored in GitHub's production environment secrets and read from the Django server's `.env`. Same value, both sides.

## Streaming the Sync Log

The sync endpoint runs the management command in a background thread and returns immediately with a `job_id` — so the GitHub Actions request doesn't time out waiting for all the embedding calls to finish. A second GET request streams the command's output as SSE until the job is done:

```
data: Fetching RSS: https://blog.atharvadevasthali.com/rss.xml
data: Found 13 posts
data:   skip    abc123
data:   new     def456
data: Done — new: 1  updated: 0  skipped: 12
data: [done]
```

The workflow POSTs to get the `job_id`, then streams the GET response and prints each line until `[done]`. The full sync log shows up inside the GitHub Actions run — no guessing whether the sync worked.

The net result: every time a production deploy succeeds on Vercel, the vector store syncs automatically, the log is visible in GitHub Actions, and the whole thing runs on the free tier.
