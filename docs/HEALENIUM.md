# Healenium services

Source: `github.com/healenium/healenium` master (`docker-compose.yaml`,
`docker-compose-selenoid.yaml`). No Healenium source modified; config +
public HTTP interfaces only. Python tests connect via
`webdriver.Remote("http://localhost:8085")` (hlm-proxy).

| Service | Image (pinned) | Ports | Purpose | Key env |
|---|---|---|---|---|
| postgres-db | `postgres:15.5-alpine` | 5432 | Stores reference selectors, healing results, reports | `POSTGRES_DB/USER/PASSWORD` (override via env; compose default is local-dev only) |
| healenium (hlm-backend) | `healenium/hlm-backend:3.5.1` | 7878 | CRUD service; report UI at `/healenium/report/`, JSON at `/healenium/report/data` | `SPRING_POSTGRES_*`, `SCORE_CAP` n/a (proxy-side), `COLLECT_METRICS=true` |
| selector-imitator | `healenium/hlm-selector-imitator:1.6` | 8000 | Converts healed locator to convenient format | none |
| hlm-proxy | `healenium/hlm-proxy:2.2.1` | 8085 | Proxy between test runner and Selenium server; attempt-1 healer | `RECOVERY_TRIES=1 SCORE_CAP=.6 HEAL_ENABLED=true SELENIUM_SERVER_URL=http://selenoid:4444/wd/hub HEALENIUM_SERVICE=http://healenium:7878 IMITATE_SERVICE=http://selector-imitator:8000` |
| selenoid | `aerokube/selenoid:latest-release` | 4444 | Selenium server (upstream floating tag; repin on upgrade) | `browsers.json` mount at `./selenoid-config/browsers.json` |
| selenoid-ui | `aerokube/selenoid-ui:latest-release` | 8080 | Selenoid UI | `--selenoid-uri http://selenoid:4444` |
| demo | `python:3.12-slim` | 8001 | Demo app under test (`uvicorn demo_app.app:app`) | none |

First-time setup (from repo root):

```sh
mkdir -p infra/db/sql infra/selenoid-config
curl https://raw.githubusercontent.com/healenium/healenium/master/db/sql/init.sql \
  -o infra/db/sql/init.sql
# minimal browsers.json, e.g. {"chrome": {"default": "latest", "versions": {"latest": {"image": "selenoid/chrome:latest", "port": "4444"}}}}
docker compose --project-directory infra -f infra/docker-compose.yml config
docker compose --project-directory infra -f infra/docker-compose.yml up -d
```

Verify: `docker ps` shows `postgres-db`, `healenium`, `selector-imitator`,
`hlm-proxy`, `selenoid`; open `http://localhost:7878/healenium/report/`.
