# Verification report

Review date: 24 October 2026. Host: Windows, Python 3.14.0, Node 24.19.0, npm 11.17.0, local PostgreSQL 17. Results describe the reviewed local code, not a production deployment.

| Check | Observed result |
| --- | --- |
| `python -m pytest -q` | 19 passed using isolated SQLite API fixtures |
| PostgreSQL mode with `INSIGHTFORGE_TEST_POSTGRES=1` | 19 passed; API fixtures used temporary PostgreSQL schemas and removed them afterward |
| Python compilation and application module imports | Passed |
| `python -m pip check` | No broken requirements |
| Runtime/dev requirements resolution | Existing environment satisfies documented pins; not a separate clean-machine installation |
| `npm ci` | Completed; dependency lock refreshed after compatible audit fixes |
| `npm run build` | Passed; approximately 599 kB JavaScript bundle produces Vite's size advisory |
| `npm run lint` | Passed |
| `npm audit` | Zero known vulnerabilities reported after updates |
| `pip-audit -r backend/requirements.txt` | No known vulnerabilities reported after replacing the JWT dependency |
| Uvicorn startup and `/health` | Startup completed against local PostgreSQL; HTTP 200 |
| Vite startup | Started successfully |
| Browser integration | Signed in through React against local FastAPI, listed the uploaded synthetic dataset, and rendered its analytics/statistics/charts |
| Docker Compose | YAML parsed and database volume/dependency structure checked; Docker executable absent, so images/containers not run |
| Secret/generated-file checks | Working and staged project files checked for common key patterns and matches to local environment secrets; no matches. Environment files, venvs, caches, node_modules and uploads excluded |
| Git diff | Reviewed for intended project changes and whitespace errors |

## Test coverage

Authentication success/failure, duplicate registration, invalid email/password input, invalid tokens, JWT expiry/signature, dataset ownership, upload types/content/size, failure cleanup, all seven analytics routes, conversation CRUD, missing Gemini key, sanitized provider failure, mocked successful/empty responses, mixed numeric/string/date ML classification and regression, independent preprocessors, usable-row counts, invalid targets/tasks, JSON-safe missing/infinite values, XLSX loading, numeric date false positives, Unix millisecond timestamps and monthly forecast compatibility.

API tests run the model comparison and forecast endpoints. Real Gemini output is not asserted: fake responses or a missing key isolate the tests from credentials, quota and network behaviour.

## Explicit limits

- Live Gemini response quality, quota, model access and real provider outages were not tested.
- Legacy XLS has its required reader dependency but no actual XLS fixture was exercised; XLSX was tested.
- Docker execution and a fresh Windows/Linux installation were not tested.
- GitHub Actions configuration was added; local results do not imply a completed hosted CI run.
- Browser smoke coverage is login/dataset listing/analytics; upload and ML/forecast behaviour are covered by API tests rather than a full automated browser suite. HTML export is implemented but was not exercised as a downloaded file in the browser smoke check.
- Two upstream deprecation warnings remain: Starlette's httpx TestClient path and Google SDK typing internals on Python 3.14. Tests pass with these warnings.
- Audit and secret scans are point-in-time checks, not guarantees that all possible vulnerabilities or historical exposures are absent. Git history was preserved.

See [REVIEW.md](REVIEW.md) for issue details and the root README for reproducible commands and modelling limitations. No benchmark accuracy, latency, scalability or business-outcome claims were produced.
