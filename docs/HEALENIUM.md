# Healenium services

Source: `github.com/healenium/healenium` master (`docker-compose.yaml`,
`docker-compose-selenoid.yaml`). No Healenium source modified; config +
public HTTP interfaces only. Python tests connect via
`webdriver.Remote("http://localhost:8085")` (hlm-proxy).

| Service | Image (pinned) | Ports | Purpose | Key env |
|---|---|---|---|---|
| postgres-db | `postgres:15.5-alpine` | 5432 | Stores reference selectors, healing results, reports | `POSTGRES_DB/USER/PASSWORD` (override via env; compose default is local-dev only) |
| healenium (hlm-backend) | `healenium/hlm-backend:3.5.1` | 7878 | CRUD service; report UI at `/healenium/report` (no trailing slash; with slash 404s), JSON at `/healenium/report/data` | `SPRING_POSTGRES_*`, `SCORE_CAP` n/a (proxy-side), `COLLECT_METRICS=true` |
| selector-imitator | `healenium/hlm-selector-imitator:1.6` | 8000 | Converts healed locator to convenient format | none |
| hlm-proxy | `healenium/hlm-proxy:2.2.1` | 8085 | Proxy between test runner and Selenium server; attempt-1 healer | `RECOVERY_TRIES=1 SCORE_CAP=.6 HEAL_ENABLED=true SELENIUM_SERVER_URL=http://selenium-hub:4444/wd/hub HEALENIUM_SERVICE=http://healenium:7878 IMITATE_SERVICE=http://selector-imitator:8000` |
| selenium-hub + chrome node | `selenium/hub:latest`, `selenium/node-chromium:latest` (official Healenium base compose; selenoid removed 2026-10-08 — its binary speaks Docker API 1.24, unusable on Docker Desktop 29 which requires >= 1.40) | 4444 | Selenium Grid server + Chrome node | `SE_EVENT_BUS_HOST=selenium-hub`, node session env; no `docker.sock` mount needed |
| demo | `python:3.12-slim` + pip-installed `fastapi/httpx/uvicorn` at start | 8001 | Demo app under test (`uvicorn demo_app.app:app`) | `DRIFT_MODE` / `API_DRIFT_MODE` (default `none`; set per-run for live benches) |

First-time setup (from repo root):

```sh
docker compose --project-directory infra -f infra/docker-compose.yml config
docker compose --project-directory infra -f infra/docker-compose.yml up -d
```

Verify: `docker ps` shows `postgres-db`, `healenium`, `selector-imitator`,
`hlm-proxy`, `selenium-hub`, `node-chrome`; open `http://localhost:7878/healenium/report`.

Live measurement (needs `pip install selenium` on the host):

```sh
python -m scripts.live_healenium_check   # services, proxy, one drifted heal, read-back
make bench-healenium-live                # full 24-case run -> benchmark/reports/healenium_live.md
```

The live bench warms Healenium with one green pass (the tool needs stored
reference selectors), then restarts demo per drift group and drives every
case through `RemoteWebDriver(http://localhost:8085)` loading
`http://demo:8001<page>` (in-compose DNS; localhost is unreachable from
inside browser containers).
