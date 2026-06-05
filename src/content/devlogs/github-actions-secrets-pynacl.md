---
title: "Managing Server Env Vars Without Touching the Server"
description: "A UI to add, reveal, and delete env vars — with a deploy button that syncs everything to GitHub Actions secrets so the next deployment picks them up automatically."
pubDate: "Jun 02 2026"
primaryTag: "python"
tags: ["Python", "GitHub", "Docker", "Infrastructure"]
---

The usual way to update a server's environment variables is to SSH in, edit `.env`, and restart the relevant containers. It works but it's manual, error-prone, and leaves no audit trail. Every change is someone typing on a server.

The alternative built here: a UI in the admin panel to manage env vars, and a deploy button that pushes them all to GitHub Actions as repository secrets. The next time the deployment workflow runs `docker compose up`, it injects those secrets as environment variables automatically. The server's env state is managed through the UI, not through SSH.

## The Flow

```
Admin UI  →  PUT /env/{key}       writes to server .env
Admin UI  →  POST /env/deploy     syncs all vars to GitHub Actions secrets
GitHub Actions  →  docker compose up  injects secrets as env vars on next deploy
```

Adding or updating a variable in the UI writes it to the `.env` file on the server immediately — so the running app can pick it up with a restart. The deploy step is separate: it takes the current state of `.env` and pushes every variable to GitHub Actions, so the next automated deployment starts with the correct environment from the start rather than relying on a file that might differ between servers.

## GitHub Requires Encrypted Values

GitHub's secrets API won't accept plaintext. Every value has to be encrypted with the repository's own public key using libsodium's sealed box before the request goes out. `PyNaCl` handles it:

```python
from base64 import b64decode, b64encode
from nacl.public import PublicKey, SealedBox

def _encrypt_secret(public_key_b64: str, secret: str) -> str:
    pub = PublicKey(b64decode(public_key_b64))
    box = SealedBox(pub)
    return b64encode(box.encrypt(secret.encode())).decode()
```

The deploy endpoint fetches the repo's public key once, then loops over every variable — encrypting each value and pushing it to `PUT /repos/{owner}/{repo}/actions/secrets/{key}`. Each PUT creates or overwrites idempotently.

## The UI

The environment tab in settings lists all variables with values masked by default. Each row has a reveal button that makes a separate authenticated request for the plaintext — so the list can load without exposing values, and reveals are individually logged.

Actions available per variable: reveal, edit, delete. The deploy button at the top syncs the full current state to GitHub Actions in one call.

Every action writes an audit event — `env_var_set`, `env_var_revealed`, `env_var_deleted`, `env_deployed` — with actor and timestamp. The value is never included in the audit record, only the key name.

## What This Replaces

No more SSHing to update `.env`. No more "did you remember to update the staging server too." The UI is the source of truth for what variables exist; GitHub Actions is the source of truth for what gets injected at deploy time. The two stay in sync through the deploy button.
