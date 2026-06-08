---
title: "Replacing Bash Deploys with Ansible and CI Gates"
description: "Migrating from ad-hoc SSH scripts to a proper Ansible-based deploy pipeline with lint gates, dynamic topology inference, and targeted container restarts."
pubDate: "Jun 08 2026"
primaryTag: "n8n"
tags: ["Ansible", "CI/CD", "Infrastructure", "Docker"]
---

The previous deploy approach was SSH over a Bitbucket pipeline running shell scripts. It worked until it didn't. No lint enforcement, no structured playbooks, environment config scattered across hardcoded docker-compose values, and every deploy restarting everything regardless of what actually changed. The autoscaler from the [previous entry](/devlogs/n8n-autoscaler) added enough moving parts that the existing approach started becoming a liability.

This covers the full pipeline rewrite: CI gates, Ansible migration, compose cleanup, and some admin panel fixes that landed alongside.

## Lint Gates Before Any Deploy

The CI workflow now has a lint stage that must pass before any deploy step runs. Frontend uses ESLint, the admin API uses black / isort / ruff. Both are pinned — Node 20 via `actions/setup-node`, Python 3.11 via `actions/setup-python` — so the environment the linter runs in matches the environment the code runs in.

Adding the gates caught a batch of existing violations: import ordering across the API, unused React imports in the frontend, a handful of ruff B904 and N811 rule violations. None of these were bugs, but they would have accumulated quietly without enforcement.

## Dynamic Topology Inference

The infrastructure supports two topologies: a single server running everything, or a main server plus separate worker servers. The CI workflow shouldn't need to be edited when adding a worker server — it should detect the topology and act accordingly.

The inference is straightforward: if the `CONTABO_WORKER_IP` secret is set, this is a multi-server deploy. If it's absent, it's single-server.

Single topology runs `deploy_main.yml` only. Multi topology also invokes a shell script (`gen_workers_inventory.sh`) that builds an Ansible inventory file from the IP secret at runtime, then runs `deploy_workers.yml` against it. The CI workflow never has a hardcoded assumption about which topology is active.

## Splitting the Playbooks

Originally one `deploy.yml` playbook covered both main and worker hosts. On a single-topology run — where the `workers` host group doesn't exist in inventory — Ansible emitted a warning on every task that referenced the workers group:

```
[WARNING]: Could not match supplied host pattern, ignoring: workers
```

Not fatal, but noisy and misleading. The fix was obvious once it was annoying enough: split into `deploy_main.yml` and `deploy_workers.yml`, each referencing only its own host group. The warning went away. Each playbook now runs cleanly against its inventory without producing output about things it doesn't manage.

## Targeted Container Restarts

Every deploy previously did a full `docker compose restart`, which meant restarting the n8n main instance even if only a frontend file changed, and restarting workers even if nothing worker-related was touched.

The CI workflow now checks which paths changed and restarts only the affected services. A change to frontend or API files restarts only `admin-api`. A change to `.env`, compose files, or core n8n config triggers a full restart. Worker services restart only when worker-specific config changes.

The logic is path matching against `git diff --name-only` output. Not elegant, but it's explicit about what triggers what, which matters more than elegance in deploy pipelines.

## Ansible Migration

The Bash-over-SSH approach had no idempotency guarantees and no structured inventory. Replacing it with Ansible brought the expected benefits — idempotent tasks, proper host grouping, readable playbooks — plus one specific structural benefit: `group_vars`.

The layout after migration:

```
ansible/
  inventory/
  playbooks/
    deploy_main.yml
    deploy_workers.yml
    tasks/
      common_setup.yml
    group_vars/
      all.yml
```

All non-secret environment variables — ports, hostnames, execution tuning, feature flags — live in `group_vars/all.yml`. The `common_setup.yml` task uses `blockinfile` to append them to `.env` on every deploy. Nothing environment-related is hardcoded in docker-compose files anymore.

Two operational details worth noting: all inventories now set `ansible_python_interpreter: /usr/bin/python3` explicitly, which silences Ansible's auto-discovery warnings on remote hosts. Long-running deploy tasks were converted to `async / poll` after deploys started timing out mid-run due to SSH idle disconnect — combined with `ServerAliveInterval` and `ServerAliveCountMax` in SSH config, the long tasks no longer drop the connection.

## The group_vars Path Bug

After creating `group_vars/all.yml`, the blockinfile task failed with `'N8N_PORT' is undefined`. The file existed, Ansible wasn't reading it.

Ansible's `group_vars` auto-loading only looks relative to the playbook file or the inventory file — not arbitrary sibling directories in the project tree. The file was created at `ansible/group_vars/all.yml`, but the playbooks live at `ansible/playbooks/`. Ansible looked for `ansible/playbooks/group_vars/`, found nothing, and silently continued without the variables.

Moving the file to `ansible/playbooks/group_vars/all.yml` fixed it. The variable loading rules aren't documented prominently — this one gets people.

## Docker Compose Cleanup

Across all four compose files (`docker-compose.prod.yml`, `prod-main.yml`, `prod-worker.yml`, `dev.yml`), hardcoded values were replaced with `${VAR}` interpolation sourced from `.env`. Port numbers, hostnames, `NODE_OPTIONS` — anything that was duplicated between Ansible config and compose config was removed from compose and made authoritative in `group_vars/all.yml`.

`sh_files/start-n8n-worker.sh` was a startup wrapper that did one thing: `exec n8n worker`. It existed because at some point someone needed a script there, and it stayed. Replaced it with `command: worker` directly in the compose service definition. Nothing depends on the script file existing.

## Modal Backdrop Bug (createPortal)

All modals in the admin panel — `AddVarModal`, `DeleteConfirmModal`, `ImportModal`, `UserManagement` — were rendering their backdrops with `position: fixed; inset: 0` inside parent containers that use `overflow-hidden` and `h-screen` flex layout.

In certain browser stacking contexts, a fixed-position element inside an `overflow-hidden` ancestor doesn't behave like it's fixed to the viewport — it behaves fixed to the nearest containing block that establishes a stacking context. The visible result: backdrops appearing with a top offset equal to the parent container's position, instead of covering the full viewport.

The fix is `createPortal(..., document.body)` in every modal's render. This moves the modal DOM entirely outside the ancestor tree, so no ancestor's CSS can affect its stacking or position. The modal renders as a direct child of `<body>` regardless of where in the component tree it's instantiated.

## GitHub Config UI and Deployment Logs

The GitHub token and repo name were previously configured via docker-compose environment variables, which meant changing them required a redeploy. Moved both into SQLite (`app_config` table) so they can be updated at runtime through the admin UI.

The deployment logs drawer pulls the GitHub Actions API for the configured repo and renders a paginated runs list with polling. The API route prefix was renamed from `/api/logs` to `/api/admin` across nginx, FastAPI, and the frontend client — the original name was accurate to what was there at the time and wrong for what it grew into.

The broader admin panel expansion — env var manager, audit log, and workflows UI — that landed shortly after is covered in [Admin Panel: Env Manager, Audit Log, and Workflows UI](/devlogs/n8n-admin-panel).
