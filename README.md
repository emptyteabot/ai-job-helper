# AI Job Helper — public legacy prototype

> Preserved public prototype from the early AgentHelpJob iterations.  
> **Current product:** `emptyteabot/-job` (private canonical repository)  
> **Interactive demo:** [agenthelpjob.lunarnewt3.chatgpt.site](https://agenthelpjob.lunarnewt3.chatgpt.site)

AI Job Helper parses resumes, runs staged analysis, matches candidate evidence to job requirements, prepares interview material and records early browser-assisted application experiments. It is useful as historical context, but it is not the source of truth for the current product.

## What is in this repository

- Resume ingestion for PDF, Word, image and plain text.
- Multi-stage AI analysis for resume evidence, job matching and interview preparation.
- FastAPI and Streamlit application paths.
- WebSocket progress updates and structured job/application records.
- Early browser-automation experiments for selected recruiting platforms.
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
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run streamlit_app.py
```

Configure `DEEPSEEK_API_KEY` in `.env` to enable model-backed analysis.

## Status and lineage

| Repository | Role |
| --- | --- |
| `emptyteabot/-job` | Canonical May 2026 product |
| `emptyteabot/agenthelpjob` | March 2026 implementation snapshot |
| `emptyteabot/ai-job-helper` | This public legacy prototype |

This repository deliberately keeps historical experiments and backup entry points. For a review, start with `streamlit_app.py`, `web_app.py`, `app/`, `tests/` and `PROJECT_OVERVIEW.md`.

## License

MIT.
