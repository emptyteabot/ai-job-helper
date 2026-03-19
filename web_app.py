"""
Compatibility entrypoint.

`python web_app.py` now runs the restored FastAPI app defined in `web_app_restored.py`.
"""

from __future__ import annotations

import os

import uvicorn

from web_app_restored import app


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("web_app_restored:app", host=host, port=port, reload=False)
