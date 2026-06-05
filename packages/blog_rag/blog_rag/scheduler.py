"""
Periodic sync scheduler for blog_rag.

Started from BlogRagConfig.ready() when SYNC_CRON_HOURS is set.
Uses APScheduler's cron trigger so syncs fire at fixed times of day
regardless of when the server started or was last deployed.

The RUN_MAIN guard prevents the scheduler from starting twice under
manage.py runserver, which forks a child process for the auto-reloader.
"""

import os

from apscheduler.schedulers.background import BackgroundScheduler


def _sync_job():
    from django.core.management import call_command
    from .conf import get as rag_setting

    rss_url = rag_setting("RSS_URL")
    if rss_url:
        call_command("sync_from_rss", rss_url)


def start(cron_hours: str):
    if _is_reloader():
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(_sync_job, "cron", hour=cron_hours, id="blog_rag_sync")
    scheduler.start()


def _is_reloader() -> bool:
    """Return True if this is the reloader parent process under runserver."""
    import sys
    return "runserver" in sys.argv and os.environ.get("RUN_MAIN") is None
