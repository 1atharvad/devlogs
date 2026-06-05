---
title: "n8n Folder Assignment Doesn't Work via the API"
description: "The n8n REST API can move workflows between projects but not into folders within one. The same gap shows up in the CLI export. The fix for both was postgres."
pubDate: "Jun 02 2026"
primaryTag: "n8n"
tags: ["Python", "FastAPI", "PostgreSQL"]
---

Building a workflow management UI meant needing two things from n8n: which folder each workflow belongs to, and the ability to reassign it. Both turned out to be gaps in the REST API.

The workflows list endpoint returns workflow metadata but no folder data. The folders endpoint returns folders but not which workflows they contain. There's no join — you can't get a full picture in a single call, and there's no documented way to query "all workflows with their current folder."

The transfer endpoint exists but only moves workflows between projects. Moving a workflow into a folder within the same project isn't supported. The API accepts the request and returns 200, but nothing changes.

## Going Direct to Postgres

n8n stores everything in postgres. The schema has `workflow_entity`, `folder`, and an `n8n_workflow_folder` join table that holds the assignment. None of that is hidden — it's just not exposed usefully through the API.

The fix was a second SQLAlchemy session pointed at n8n's database and a direct query:

```python
rows = await session.execute(
    select(WorkflowEntity, Folder)
    .outerjoin(N8nWorkflowFolder, WorkflowEntity.id == N8nWorkflowFolder.workflow_id)
    .outerjoin(Folder, N8nWorkflowFolder.folder_id == Folder.id)
)
```

One query, full picture — workflow metadata and folder assignment together.

Reassignment is a postgres `UPDATE` on `n8n_workflow_folder`. If no row exists yet (workflow has never been assigned a folder), it's an insert. Removing a folder assignment is a delete on the same row. Folder creates, renames, and deletes still go through the REST API — those work fine. The workaround is only for the assignment relationship itself.

## The Same Gap in the CLI

The backup/restore scripts hit the same problem from a different angle.

n8n's CLI can export workflows to JSON, but the exported files don't include folder assignment — `parentFolder` and `parentFolderId` are absent from the output. A full backup that faithfully restores folder structure can't rely on the CLI export alone.

The fix was to inject the folder data before committing the backup. The export script reads the current folder assignments from postgres, then merges them into each exported JSON file before writing to disk. A `manifest.json` tracks which workflow IDs are archived so restore can skip them.

Restore is a wipe-then-rebuild: delete all workflows and folders via the REST API, import the saved JSONs via CLI, then re-run the folder assignments via postgres `UPDATE`. The import step gets workflows back into n8n; the postgres step puts them back in the right folders. Without that second step, every workflow lands in the unfiled list regardless of what the JSON says.

```bash
# after n8n import via CLI
psql "$N8N_DB_URL" <<SQL
  UPDATE n8n_workflow_folder wf
  SET folder_id = m.folder_id
  FROM workflow_folder_map m
  WHERE wf.workflow_id = m.workflow_id;
SQL
```

The `package.json` scripts use bash explicitly rather than sh — the export script uses process substitution (`<(...)`) which sh on macOS doesn't support.

## The Tradeoff

Reading from and writing to n8n's internal tables is a coupling risk. If n8n changes its schema, these queries break. In practice that's acceptable here — n8n is self-hosted, schema changes across minor versions have been rare, and the alternative (broken folder assignment in both the UI and backups) is worse.

The REST API handles what it can. Postgres handles what it can't.
