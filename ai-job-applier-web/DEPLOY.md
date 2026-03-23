# Deployment Notes (MVP)

This project is currently a web MVP. Deployment guidance below is intentionally conservative and avoids claims that are not production-proven.

## Reality Check

- The product supports assisted automation, not unattended autonomous execution.
- Boss workflows require human completion for QR/captcha/security challenges.
- Cloud Playwright Challenge Center is in progress; current challenge sessions are usable but not fully scaled/hardened.

## Deployment Model

- Single service: `FastAPI` serves API and `frontend/dist` assets.
- Canonical entrypoint: `start.sh`.
- Supported targets: Railway, Render, or a single Linux/WSL host.

## Build and Start

Build step:

```bash
bash start.sh --build
```

Start step:

```bash
PORT=8765 bash start.sh
```

Notes:

- `start.sh` installs backend requirements once (marker file: `.backend-deps-installed`).
- If `frontend/dist/index.html` is missing, `start.sh` triggers frontend build automatically.
- Railway/Render can run `bash start.sh --build` in build phase and `bash start.sh` in run phase.

## Minimum Production Environment

| Variable | Recommended value | Why it matters |
| --- | --- | --- |
| `APP_ENV` | `production` | Enables production safety behavior |
| `SECRET_KEY` | random strong secret | Required for secure auth/session signing |
| `AUTH_EXPOSE_DEBUG_CODE` | `0` | Prevents debug verification code exposure |
| `AUTH_BYPASS_CODE` | empty | Avoids bypass login in production |
| `PORT` | platform-provided or fixed | Uvicorn listen port |

## Optional but Common Environment

| Variable | Typical value | Notes |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | provider key | Only needed when AI generation path is enabled |
| `ALLOW_SIMULATED_APPLY` | `1` or `0` | `1` keeps MVP simulated apply path; `0` for strict no-sim mode |
| `AUTH_LOCAL_ACCOUNT_ENABLED` | `1` | Enables local email/password auth |
| `AUTH_EMAIL_DIRECT_ENABLED` | `1` | Enables direct email login flow |
| `AUTH_SMS_PROVIDER` | `tencentcloud` or `twilio` | Needed for real SMS delivery |

## Health and Readiness Checks

Use these endpoints after deploy:

- `GET /health` (or `GET /api/health`)
- `GET /api/system/readiness`

Also verify:

- Frontend loads from the same host/domain.
- WebSocket upgrade works for `/api/apply/ws`.
- Boss status endpoint returns expected assisted mode details: `GET /api/boss/status`.

## Assisted Boundary Verification

Before calling a deployment done, confirm these behaviors explicitly:

1. Boss login/apply still requires human action at challenge checkpoints.
2. Challenge Center can create, refresh, screenshot, submit code, and close sessions.
3. No background unattended loop is running without a user-triggered session.

## Known MVP Limitations

- Challenge session state is currently file/runtime centric; not yet built for multi-node distributed coordination.
- Browser anti-bot changes upstream can affect challenge/session stability.
- Some challenge-center UI copy is still being cleaned up.

## Rollback (Simple)

1. Checkout previous known-good commit.
2. Rebuild assets and dependencies: `bash start.sh --build`.
3. Restart service with same env set.
4. Re-run health/readiness checks above.
