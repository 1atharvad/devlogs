"""
Django AppConfig for the blog_rag package.

The host project activates this package by adding "blog_rag" to
INSTALLED_APPS. Django then picks up BlogRagConfig automatically via the
default_app_config convention (or the explicit apps.py entry point).
"""

from django.apps import AppConfig


class BlogRagConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog_rag"
    verbose_name = "Blog RAG"
