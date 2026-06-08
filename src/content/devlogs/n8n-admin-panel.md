---
title: "Admin Panel: Env Manager, Audit Log, and Workflows UI"
description: "Three new admin panel features built on top of a module refactor: encrypted env var management with live GitHub secret sync, a write audit log, and a workflows UI that bypasses the n8n API for read queries."
pubDate: "Jun 02 2026"
primaryTag: "n8n"
tags: ["FastAPI", "React", "SQLite", "Infrastructure"]
---

The admin panel started as a deployment log viewer. It grew into a [GitHub config UI and deployment logs drawer](/devlogs/n8n-deploy-infra#github-config-ui-and-deployment-logs), then an env var manager, an audit log, and a workflows dashboard — at which point the original single-file FastAPI setup stopped being workable. All three features landed alongside a full module refactor.

## Env Manager

The env vars this panel manages are the deployment secrets: database passwords, API keys, service URLs. They live in SQLite (`env_vars` table) encrypted at rest with Fernet, and the canonical destination is GitHub Actions environment secrets. Anything saved here needs to be there before the next deploy runs.

Saves go through two paths depending on environment. In production, saving a var writes it to SQLite and immediately syncs to GitHub via the secrets API — the encryption mechanism (libsodium `SealedBox`, per-key PUT) is covered in [Managing Server Env Vars Without Touching the Server](/devlogs/github-actions-secrets-pynacl). What changed here: the original design batched syncs into a manual deploy step; this iteration syncs on every individual save, so GitHub always reflects the current state without a separate deploy trigger. In dev, writes go to SQLite and a local `.env` file instead of hitting the GitHub API.

The list endpoint returns only keys and timestamps. Reading a value requires a separate `GET /env/{key}` call, which also writes an audit log entry. There's no bulk reveal.

One design issue worth noting: the Fernet key is derived as `sha256(JWT_SECRET)`. That makes the encryption key dependent on the auth secret. Rotating `JWT_SECRET` — which you'd do if it were ever compromised — silently makes every stored env var unreadable. The decrypt function currently returns the raw ciphertext on failure rather than raising, so there's no visible error. Rotating the auth secret without a migration step would silently break the env manager.

`github_token` and `github_repo` are stored in a separate `app_config` table and explicitly filtered out of GitHub secret syncs. They live in a different table precisely so they don't get pushed as GitHub secrets — the token that manages secrets shouldn't be stored as one.

## Audit Log

Every write operation that touches sensitive data calls `create_audit_log(session, action, actor_id, actor_name, target_name, detail, ip_address)`. The currently instrumented actions are env var reads, creates, updates, deletes, deploys, GitHub config updates, and workflow folder changes. User management operations aren't logged yet.

Storage is SQLite, `audit_log` table. The `ip_address` column wasn't in the original schema — it was added as a live `ALTER TABLE` during app startup via a lifespan handler, with a guard that catches the `duplicate column` error if it already exists:

```python
try:
    await conn.execute("ALTER TABLE audit_log ADD COLUMN ip_address TEXT")
except Exception:
    pass
```

Functional, but it's a bolted-on migration rather than a tracked one. The right fix is a migration file; what's there works until the schema needs to change again.

The read endpoint is `GET /audit` with a `limit` param (default 100, max 500). It returns total count, 24-hour event count, and the log entries. No server-side filtering by action type, actor, or date range — that's left to the frontend.

## n8n Workflows UI

The workflows list shows per-workflow stats: name, folder, active state, all-time run counts, success/error breakdown, last run status and duration, and 24-hour run and error counts. There's also a per-workflow execution history view and a chart of daily/hourly execution counts.

All of this comes from querying n8n's Postgres database directly with asyncpg, not from the n8n REST API. The API doesn't expose aggregate stats per workflow in a single call — getting the same data through it would require N+1 requests. The backend runs one query with four CTEs instead.

One join that doesn't work without an explicit cast: `workflow_entity.id` is a UUID column, but `execution_entity.workflowId` is a VARCHAR. Postgres won't match them without `w.id::text`:

```sql
JOIN workflow_entity w ON w.id::text = e."workflowId"
```

Without the cast, the join silently returns no rows. No error, no warning — the query succeeds with an empty result set.

Write operations — specifically folder assignment — go through the n8n REST API rather than direct `UPDATE` statements. The reason is that n8n's folder membership is entangled with project ownership in its data model. A direct write to `workflow_entity.parentFolderId` doesn't update the project association, which leaves the workflow in an inconsistent state. The `/workflows/{id}/transfer` endpoint handles both, so that's what gets called.

This is different from the [workflow backup/restore scripts](/devlogs/n8n-folder-postgres), which do write folder assignments directly to the `n8n_workflow_folder` table. That's safe there because the restore sequence does a full wipe and re-import first, resetting project associations entirely before reassigning folders. On a live workflow that's already owned by a project, a direct write would skip the ownership step and corrupt the state.

Folder transfers also require the personal project ID, which isn't predictable — n8n creates it automatically but doesn't expose it as a config value. A helper runs `SELECT id FROM project WHERE type = 'personal' LIMIT 1` before each transfer call to look it up.

## The Refactor

Before this feature drop, all endpoints lived in a single `routes.py`. The n8n module needed two distinct data access patterns in the same domain — REST API for writes, direct Postgres for reads — which made sense to isolate together rather than scatter. Separating `db/crud.py` from the routers meant any router could import DB operations without creating circular dependencies. The `auth/security.py` and `auth/router.py` split kept the `require_admin` FastAPI dependency importable by other routers without pulling in the auth endpoints alongside it.

The result:

```
admin-api/
  main.py
  db/         — models, session factory, all CRUD
  auth/       — JWT logic, password hashing, user endpoints
  env/        — env var CRUD, GitHub sync, deploy trigger
  n8n/        — workflow stats, folder management, execution history
  logs/       — container log streaming, audit read endpoint
```

The split was driven by what needed to be imported where, not by any upfront design. It ended up clean, but it got there reactively.
