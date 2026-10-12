# AI Job Helper

A public legacy prototype of an AI-assisted job-search workflow. It parses resumes, runs staged analysis, matches candidate evidence to job requirements, prepares interview material and contains experiments for browser-assisted application workflows.

> The current product is [AgentHelpJob](https://agenthelpjob.com). This repository is kept as an earlier implementation snapshot; the current product source is private.

## What is in this repository

- Resume ingestion for PDF, Word, image and plain text.
- Multi-stage AI analysis for resume evidence, job matching and interview preparation.
- FastAPI and Streamlit application paths.
- WebSocket progress updates and structured job/application records.
- Browser-automation experiments for selected recruiting platforms.
- Tests, deployment configuration and implementation notes.

## Main entry points

- `streamlit_app.py` — Streamlit interface.
- `web_app.py` — web application entry point.
- `app/` — application modules and services.
- `frontend/` and `static/` — user interface assets.
- `tests/` — automated checks.
- `docs/` — technical and product documentation.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run streamlit_app.py
```

Configure `DEEPSEEK_API_KEY` in `.env` to enable model-backed analysis.

## Project status

This codebase records several iterations in one repository, including backup entry points and deployment experiments. For a review, start with `streamlit_app.py`, `web_app.py`, `app/`, `tests/` and `PROJECT_OVERVIEW.md`.

## License

MIT.
