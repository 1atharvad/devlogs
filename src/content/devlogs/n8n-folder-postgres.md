---
title: "Git Pull and Push for Self-Hosted n8n"
description: "n8n's git integration is enterprise-only. Here's how to build a pull/push workflow for the community edition that actually preserves folder structure — which the CLI doesn't do on its own."
pubDate: "Jun 02 2026"
primaryTag: "n8n"
tags: ["PostgreSQL", "Docker", "Infrastructure"]
---

n8n has git integration — but it's an enterprise feature. On the self-hosted community edition, there's no export-and-commit built in, workflows live only in the database, and if something goes wrong there's no rollback. For a production setup running critical automation, that's a problem.

The solution was a pair of shell scripts — `pull_workflows.sh` and `push_workflows.sh` — wired up as `npm run pull-workflows` and `npm run push-workflows`. Pull snapshots the current state to JSON files in the repo. Push does a full wipe-and-restore from those files. The hard part was folder structure: n8n's CLI drops it silently on both ends.

## The Folder Problem

n8n's CLI export produces one JSON file per workflow. What it doesn't include is which folder the workflow belongs to — `parentFolder` and `parentFolderId` are absent from every exported file. Import those files back and every workflow lands in the unfiled list, folder structure gone.

The REST API has a transfer endpoint but it only moves workflows between projects, not into folders within the same project. It accepts the request, returns 200, and changes nothing.

Folder assignments live in n8n's postgres database in an `n8n_workflow_folder` join table. That's the only reliable place to read or write them.

## Pull: Inject Folder Data Before Committing

The pull script runs the CLI export first, then reads the current folder assignments directly from postgres and merges them into each JSON file before writing to disk:

```bash
# read assignments from postgres
psql "$N8N_DB_URL" -t -A -F',' \
  -c "SELECT wf.workflow_id, f.name, f.id
      FROM n8n_workflow_folder wf
      JOIN folder f ON f.id = wf.folder_id" \
| while IFS=',' read -r wf_id folder_name folder_id; do
    file="workflows/${wf_id}.json"
    tmp=$(jq --arg fn "$folder_name" --arg fi "$folder_id" \
      '.parentFolder = $fn | .parentFolderId = $fi' "$file")
    echo "$tmp" > "$file"
  done
```

The script also generates a `manifest.json` that tracks which workflow IDs are archived — restore uses this to skip them rather than reimporting workflows that were intentionally retired.

The `--commit` flag stages and commits the result automatically. `--force` overwrites local changes without prompting.

## Push: Wipe, Import, Reassign

Restore is three steps:

**1. Wipe.** Delete all existing workflows and folders via the REST API. This avoids ID conflicts and duplicate names on import.

**2. Import.** Run the n8n CLI import against the JSON files. This gets all workflows back into the database with their content and settings intact — but again, no folder assignments.

**3. Reassign.** Read `parentFolderId` from each imported JSON and run a postgres `UPDATE` to put everything back in the right folder:

```bash
for file in workflows/*.json; do
  wf_id=$(jq -r '.id' "$file")
  folder_id=$(jq -r '.parentFolderId // empty' "$file")
  [ -z "$folder_id" ] && continue

  psql "$N8N_DB_URL" -c \
    "INSERT INTO n8n_workflow_folder (workflow_id, folder_id)
     VALUES ('$wf_id', '$folder_id')
     ON CONFLICT (workflow_id) DO UPDATE SET folder_id = EXCLUDED.folder_id"
done
```

Without step 3, the import looks complete but every workflow is unfiled.

## One macOS Gotcha

The scripts use bash explicitly, not sh. The pull script uses process substitution (`<(...)`) for feeding psql output into the loop — sh on macOS doesn't support it. The `package.json` entries specify bash directly:

```json
"pull-workflows": "bash sh_files/pull_n8n_workflows.sh",
"push-workflows": "bash sh_files/push_n8n_workflows.sh"
```

## The Tradeoff

This reads from and writes to n8n's internal postgres tables directly. If n8n changes the `n8n_workflow_folder` schema across a version upgrade, the scripts break. In practice that's been stable across minor versions — and the alternative is losing folder structure entirely on every backup and restore, which isn't acceptable for a setup with 50+ workflows organized across a dozen folders.
