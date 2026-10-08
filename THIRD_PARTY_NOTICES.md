# Third-Party Notices

## Healenium (Apache License 2.0, https://www.apache.org/licenses/LICENSE-2.0)

- Project: Healenium (https://github.com/healenium/healenium)
- Usage: attempt-1 locator matching behind `healing/matching/` interface; no source modified.
- Obligation: retain upstream copyright/license notices; see `NOTICE`.

### Components (pinned in infra/docker-compose.yml)

- hlm-backend `healenium/hlm-backend:3.5.1` — CRUD + reports (`/healenium/report/`, `/healenium/report/data`).
- hlm-proxy `healenium/hlm-proxy:2.2.1` — Selenium proxy, `RemoteWebDriver(http://localhost:8085)`.
- selector-imitator `healenium/hlm-selector-imitator:1.6` — healed-locator formatting.
- postgres `postgres:15.5-alpine` — reference selectors / healing / report storage.
- selenoid `aerokube/selenoid:latest-release` + `aerokube/selenoid-ui:latest-release` — Selenium server (upstream floating tag; repin on upgrade).
