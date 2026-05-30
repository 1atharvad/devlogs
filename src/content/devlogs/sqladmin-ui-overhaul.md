---
title: "Hardening the Admin Panel: Auth, Security, and a Real Build Pipeline"
description: "sqladmin gives you a CRUD interface. It doesn't give you auth, a real dashboard, XSS protection, or a reproducible asset pipeline. Here's what it took to add all of that."
pubDate: "May 29 2026"
primaryTag: "python"
tags: ["UI", "CSS", "sqladmin", "Docker", "Security"]
---

sqladmin gets you a working CRUD interface fast. What it doesn't give you is any of the surrounding infrastructure a real admin panel needs — proper auth, a useful home page, security guarantees, or a frontend build you can reproduce. This is the work to add all of that.

## Auth

sqladmin has an `AuthenticationBackend` protocol. Implement it and you get login/logout wired into the panel's routing automatically.

The implementation is straightforward: credentials come from `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables, sessions are managed with `itsdangerous` signed cookies keyed to `ADMIN_SECRET_KEY`. On startup there's an assertion that fails fast if `ADMIN_SECRET_KEY` isn't set — better to crash immediately than to run with unsigned sessions.

One layout issue worth noting: sqladmin's `url_for('admin:logout')` inside the sub-app was resolving to the Docker container's internal hostname rather than the external URL. Fixed by registering a `admin_logout_url` Jinja2 global at startup, computed once as `root_url + "/db-admin/logout"`, and referencing that in the template instead.

## Custom Dashboard and Settings Page

The default sqladmin index is an empty page with a welcome message. Replaced it with a live stats view that queries row counts per model and renders them with icons — useful at a glance, takes about 30 lines.

Added a Settings view alongside it: environment name, database connection info (host, name, driver — not credentials), and installed dependency versions pulled from `importlib.metadata`. The kind of page that saves a lot of `ssh → cat .env` when something looks off in production.

## MultiValueFilter

sqladmin's built-in filters match on a single value. For the workflow log tables — where filtering by multiple dates or event types at once is common — that's not enough.

Built a `MultiValueFilter` that accepts comma-separated input and translates it to `column.in_([...])`. The implementation subclasses sqladmin's `FilterConverter` and overrides the clause generation for the relevant column types. Nothing clever, just the right SQLAlchemy clause.

## The XSS Fix

The detail view had formatters that used `Markup(f"<tag>{val}</tag>")` to render HTML in the admin. `Markup()` tells Jinja2 the string is safe to render unescaped — but when `val` comes from the database, wrapping it in `Markup()` directly means any stored HTML or script tags render as-is. Classic stored XSS.

The fix is `Markup.format(escape(val))` instead:

```python
# Before — val is injected unescaped
Markup(f'<span class="badge">{val}</span>')

# After — val is HTML-escaped before interpolation
Markup('<span class="badge">{}</span>').format(escape(val))
```

`Markup.format()` auto-escapes any argument that isn't already a `Markup` instance before substituting it — `val` never touches the template string raw. The fundamental problem with `Markup(f-string)` is that the f-string is evaluated before `Markup` ever sees it, so there's nothing left to escape.

## Frontend Build Pipeline

Admin assets (SCSS + TypeScript) were previously compiled locally and committed. That works until it doesn't — different machines, different versions of sass, stale compiled output that doesn't match the source.

Moved the build into Docker: a dedicated Node stage runs `npm ci` and `esbuild + sass` to produce minified CSS and JS, then the Python runtime stage copies only the compiled output. The final image never sees node_modules. `npm ci` instead of `npm install` means the lockfile is always respected and the build is reproducible across environments.

The three-stage layout — Node frontend → Python builder → runtime — keeps the final image lean. Each stage only carries what the next one actually needs.
