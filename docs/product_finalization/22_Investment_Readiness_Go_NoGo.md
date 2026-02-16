# Investment Readiness Go/No-Go Gate

## 1) Gate Objective
- Decide if the product is ready to enter active financing pitch + growth acceleration.

## 2) Go/No-Go Criteria
| Dimension | Go Threshold | Current Check Method |
|---|---|---|
| Product Completeness | Core flow stable (upload -> analysis -> real links -> export) | `/app` manual + API contracts |
| Data Authenticity | No synthetic fallback in default production path | provider tests + recommendation output audit |
| Reliability | `/api/ping`, `/api/version`, `/api/ready`, `/api/health` all green | smoke script |
| Quality | test suite green, no P0/P1 defects | `pytest -q` + QA report |
| UX Consistency | Home/App/Investor use one minimal design language | visual review checklist |
| Security Baseline | keys via env, no secrets in code, access path documented | security checklist |
| GTM Proof | measurable leads + early pilot conversion | business metrics + weekly report |

## 3) Required Evidence Pack
- Engineering:
  - CI test pass snapshot.
  - Deployment smoke JSON.
  - readiness and health API output.
- Product:
  - before/after UX screenshots for key pages.
  - recorded full user flow demo (2-3 min).
- Business:
  - weekly growth report.
  - investor summary with readiness score and targets.

## 4) Stop Conditions (No-Go)
- Recommender returns demo/synthetic jobs in production mode.
- Core APIs unstable or high timeout rate.
- Critical security misconfiguration (public key leakage, open admin paths).
- No measurable growth signal after 2 experiment cycles.

## 5) Go Decision Protocol
- Meeting attendees:
  - Product, Tech Lead, QA, SRE, GTM owner, Founder.
- Decision outputs:
  - `GO`: enter active marketing + pilot acceleration.
  - `CONDITIONAL GO`: launch with blocker list and 72h deadline.
  - `NO-GO`: rollback to stabilization sprint.
