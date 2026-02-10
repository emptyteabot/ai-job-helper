"""
Zeabur (and some PaaS autodetectors) default to running `uvicorn main:app`.

This shim keeps that working while the real app entrypoint remains `web_app.py`.
"""

from web_app import app  # noqa: F401

