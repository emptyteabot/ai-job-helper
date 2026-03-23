# AI Job Applier Web

A web MVP for assisted job application workflows.

## Current Product State (March 23, 2026)

- Stage: web MVP, not a fully autonomous product.
- Boss boundary: assisted only. Human intervention is required for QR login, captcha, and other verification checkpoints.
- Challenge Center: cloud Playwright challenge-center workflow is in progress. The current implementation works for guided sessions but is not yet fully hardened for large-scale production operations.

## What This Repository Is

- A single FastAPI service that can serve both API and built frontend assets.
- A React + Vite frontend for login, search, records, assisted apply, and challenge handling.
- An assisted automation surface with explicit human checkpoints.

## What This Repository Is Not

- Not a captcha bypass system.
- Not an unattended, always-on autonomous apply bot.
- Not a guarantee of interview rate or apply success.

## Implemented MVP Capabilities

- Authentication flows (`/api/auth/*`) with env-controlled provider modes.
- Resume upload and resume analysis APIs.
- Job search routes with fallback behavior.
- Apply progress streaming via WebSocket:
  - `/api/apply/ws`
  - `/api/apply/ws/apply`
- Boss assisted bridge endpoints:
  - `/api/boss/status`
  - `/api/boss/login`
  - `/api/boss/search`
  - `/api/boss/apply`
- Challenge session APIs:
  - `/api/challenges`
  - `/api/challenges/{id}/refresh`
  - `/api/challenges/{id}/submit`
  - `/api/challenges/{id}/screenshot`
  - `/api/boss/challenge/start`
  - `/api/boss/challenge/{id}/resume`

## In Progress

- Cloud Playwright Challenge Center reliability and operational hardening.
- Better session durability and multi-environment deployment robustness.
- UX and copy cleanup in challenge-related pages.

## Local Development

Prerequisites:

- Python 3.10+
- Node.js 20+
- npm

Install dependencies:

```bash
# backend
python -m pip install -r backend/requirements.txt

# frontend
cd frontend
npm install
cd ..
```

Run in split dev mode:

```bash
# terminal 1
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8765

# terminal 2
cd frontend
npm run dev
```

Run in single-service mode (build + serve):

```bash
bash start.sh --build
PORT=8765 bash start.sh
```

## Important Runtime Flags

- `APP_ENV`: `development` or `production`
- `SECRET_KEY`: must be replaced in production
- `AUTH_EXPOSE_DEBUG_CODE`: set `0` in production
- `AUTH_BYPASS_CODE`: keep empty in production
- `ALLOW_SIMULATED_APPLY`:
  - `1` (default) keeps MVP simulated apply behavior available
  - `0` forces strict mode where simulated success is disabled

## Deployment

See [DEPLOY.md](./DEPLOY.md) for current deployment guidance and limitations.
