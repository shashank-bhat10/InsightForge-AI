# InsightForge AI

A student-built analytics application with a FastAPI backend, PostgreSQL persistence, and a React dashboard. Upload tabular data, inspect quality and statistics, compare machine learning models, generate a simple trend forecast, and optionally ask Gemini questions about a dataset.

## Problem and objectives

Exploring a spreadsheet often requires separate tools for quality checks, charts, modelling, and follow-up questions. InsightForge brings these activities into one learning project. Its objectives are to simplify initial exploration, demonstrate an authenticated Python API, and explain basic ML evaluation.

This repository is intended for local demonstrations and technical interviews. It does not claim production readiness or measured business impact.

## Implemented features

- Registration through the API; browser sign-in with bcrypt passwords and expiring JWTs.
- Per-user dataset metadata, conversations, and chat history in PostgreSQL.
- CSV, XLSX, and XLS upload, parsing checks, and a configurable 10 MiB default upload limit.
- Preview, missing-value counts, statistics, grouped totals/averages, duplicates, IQR outliers, correlations, and categorical distributions.
- Recharts grouped comparisons and downloadable HTML reports. Browser Print can save a report as PDF.
- Four candidate classifiers or regressors, an 80/20 split, and permutation feature importance.
- Linear trend forecasting after summing observations into regular periods.
- Optional Gemini chat using summaries, grouped analysis, a 20-row preview, and conversation context. Missing keys and provider failures return readable errors.

## Technologies

Python 3.14, FastAPI, Pydantic, SQLAlchemy, PostgreSQL, pandas, NumPy, scikit-learn, SciPy, Google Gen AI SDK, PyJWT, bcrypt, React, TypeScript, Vite, Recharts, pytest, Docker Compose, and nginx.

Runtime dependencies are in `backend/requirements.txt`; root `requirements.txt` includes that file. npm dependencies are locked in `frontend/package-lock.json`.

## Architecture

```mermaid
flowchart LR
    Browser[React dashboard] --> API[FastAPI routers and auth]
    API --> Services[pandas / scikit-learn services]
    API --> Repositories[SQLAlchemy repositories]
    Repositories --> DB[(PostgreSQL)]
    API --> Files[Local upload files]
    Services --> Gemini[Optional Gemini API]
```

SQL stores users, ownership, file paths, and chats. Dataset contents stay on disk. Models are trained during requests and are not saved as artifacts.

## Folder structure

```text
backend/
  app/
    auth/           Password hashing and JWTs
    config/         Environment settings
    database/       Engine, sessions, table initialization
    dependencies/   Current-user dependency
    models/         SQLAlchemy tables
    repositories/   Persistence queries
    routers/        HTTP endpoints
    schemas/        Pydantic contracts
    services/       Analytics, ML, forecasting, Gemini
  Dockerfile
  requirements.txt
frontend/           React / TypeScript application
examples/           Small synthetic demonstration CSV
tests/              API and service tests
docs/               API, architecture, database, review and verification
.env.example
requirements.txt
requirements-dev.txt
pytest.ini
docker-compose.yml
INTERVIEW_GUIDE.md
```

## Windows setup (PowerShell)

Install Python 3.14, Node.js 22.12+ (Node 24 was used for verification), Git, and PostgreSQL 16 or 17. Docker Desktop is optional. Run commands from the root unless stated otherwise.

```powershell
git clone https://github.com/shashank-bhat10/InsightForge-AI.git
cd InsightForge-AI
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Using the environment executable directly avoids PowerShell activation-policy issues. If `.env` already exists, edit it instead of overwriting it.

### Database configuration

Start the PostgreSQL Windows service. In pgAdmin Query Tool or `psql`, connected as a user allowed to create databases, run once:

```sql
CREATE DATABASE insightforge_ai;
```

Edit root `.env`:

```dotenv
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/insightforge_ai
SECRET_KEY=replace-with-a-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash
MAX_UPLOAD_BYTES=10485760
```

Generate a secret with the following command and paste it into `.env` (at least 32 characters are required):

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

URL-encode special characters in database credentials. Never commit `.env` or paste real keys into issues or screenshots.

The backend reads legacy `backend/.env` first, then root `.env`; root values override duplicate legacy values. Process environment variables override both. Prefer one root file for a new installation. `DATABASE_URL` and `SECRET_KEY` are required; Gemini credentials are optional. Select a `GEMINI_MODEL` available to your account. Live provider availability was not verified during this review.

### Start the backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Open [API documentation](http://localhost:8000/docs) or [health](http://localhost:8000/health). Startup creates missing tables; it does not migrate existing definitions. A database connection failure prevents normal startup. Health reports API process state, not database readiness.

### Create an account

Use `POST /register` in Swagger UI with your own values:

```json
{"full_name":"Demo Student","email":"student@example.com","password":"ChooseYourOwn123!"}
```

Passwords require at least 8 characters and at most 72 UTF-8 bytes. The frontend currently has sign-in, not registration. Swagger's Authorize dialog uses your email as `username` and your password to obtain a bearer token.

### Start the frontend (second PowerShell window)

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open [the dashboard](http://localhost:5173) and sign in. `frontend/.env` defaults to `VITE_API_URL=http://localhost:8000`. Restart Vite after changing it; Vite embeds this value at build time. Never put secrets in Vite variables.

The backend permits localhost/127.0.0.1 frontend origins on port 5173 and the existing hosted frontend origin. Other origins require updating CORS in `backend/app/main.py`.

## Demonstrate the features

1. Register through Swagger, then sign in through the frontend.
2. Upload `examples/demo_sales.csv`: 60 synthetic daily rows, five columns. It is not a business dataset or benchmark.
3. Open Analytics. Check the 60-row summary, preview, grouped comparisons, and missing-value report. Export an HTML report.
4. In AutoML choose `Sales` and explicitly select regression. Compare MAE, RMSE, and R². Choose `Segment` and classification to compare weighted F1 and other metrics. Synthetic relationships do not demonstrate generalization to real data.
5. In Forecasting choose `Date`, `Sales`, daily frequency, and a horizon such as 7. The result is trend extrapolation.
6. Without a Gemini key, chat returns an unavailable message while local analytics and ML remain usable. With your own key/model, test ordinary chat and a dataset question. Use non-sensitive demonstration data.
7. Check that another account cannot access the first account's dataset IDs.

## API overview

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/`, `/health` | Process information |
| POST | `/register` | Register user (JSON) |
| POST | `/login` | OAuth2 form: email as `username`, plus `password` |
| GET | `/me` | Signed-in profile |
| POST / GET | `/api/v1/datasets/` | Multipart upload / list owned datasets |
| GET / DELETE | `/api/v1/datasets/{id}` | Metadata / delete dataset and upload |
| GET | `/api/v1/analytics/{id}/{operation}` | `preview`, `summary`, `statistics`, `insights`, `grouped-analysis`, `quality`, `advanced` |
| POST | `/api/v1/ml/{id}/train` | JSON `target_column`, `problem_type` |
| GET | `/api/v1/forecast/{id}/columns` | Detect date/numeric columns |
| POST | `/api/v1/forecast/{id}/predict` | Date/target columns, periods, frequency |
| POST | `/api/v1/ai/chat` | Prompt, optional dataset and conversation IDs |
| GET | `/api/v1/ai/test` | Authenticated provider connectivity request |
| GET / DELETE | `/api/v1/ai/history/{id}` | Get conversation messages / delete one chat |
| POST / GET | `/api/v1/conversations/` | Create / list conversations |
| PUT / DELETE | `/api/v1/conversations/{id}` | Rename / delete conversation and chats |

All data and AI routes require `Authorization: Bearer <token>`. See [API details](docs/API.md). Invalid schemas return 422; parsing/ML input errors return 400; oversized uploads return 413; unavailable chat returns 503.

## Machine learning workflow

Rows with missing targets are removed. Infinite numeric values become missing. Named date columns expand into year, month, day, weekday, day-of-year, and ordinal-day features. Constant columns and text columns with more than 90% unique values are removed. Categorical detection includes pandas 3 string dtypes.

A reproducible 80/20 split uses `random_state=42`. Classification requires enough examples for stratification. Numeric features use median imputation; categorical features use most-frequent imputation and one-hot encoding that ignores unseen categories. Each candidate has its own fitted preprocessing pipeline.

Classification compares logistic regression, decision tree, random forest, and gradient boosting using accuracy, weighted precision, weighted recall, and weighted F1; the highest rounded weighted F1 selects the winner. Regression compares linear regression and the same three tree families using MAE, MSE, RMSE, and R²; the highest rounded R² selects the winner. Permutation importance uses five repeats on the holdout.

Auto detection treats numeric targets with at most 10 distinct values as classification; choose the task manually when this heuristic is unsuitable. At least 10 usable rows are required. No accuracy or latency claim is made.

## Tests and checks

From the root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q backend/app
.\.venv\Scripts\python.exe -m pip check
cd frontend
npm run build
npm run lint
npm audit
```

Default tests use isolated in-memory SQLite and mocked/missing AI responses. They do not use your database or call Gemini. For PostgreSQL tests using existing `.env` credentials, run from the root:

```powershell
$env:INSIGHTFORGE_TEST_POSTGRES = '1'
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:INSIGHTFORGE_TEST_POSTGRES
```

The database user needs permission to create schemas. Each API test creates a random schema and removes it afterward; existing application tables are not used. `TEST_DATABASE_URL` can override this optional test database. See [verification results](docs/VERIFICATION.md) for actual outcomes and untested areas.

## Docker (optional)

Set `POSTGRES_PASSWORD` and `SECRET_KEY` in root `.env`. Use a URL-safe password for this Compose example. If local PostgreSQL uses port 5432, stop it or change the Compose host port.

```powershell
docker compose up --build
```

Frontend: port 5173; API: port 8000. Containers use a named PostgreSQL volume and `backend/uploads` bind mount. PostgreSQL must become healthy before the backend starts. For remote access, set `VITE_API_URL` to the browser-reachable API URL before building and update CORS. Docker was unavailable on the review machine; image builds and container startup remain unverified.

## Screenshots

The screenshot below is a real local demonstration using the bundled synthetic dataset. Its quality score describes that sample, not application performance.

![Analytics on the synthetic sample](docs/screenshots/analytics.png)

## Known limitations

- Synchronous, in-request analysis is intended for small datasets. A byte limit does not cap expanded Excel size, feature count, CPU time, or concurrent work.
- Feature-type/cardinality decisions use data before splitting. There is no cross-validation or separate final test set. Selecting the best model on the same holdout creates selection bias; scores are exploratory.
- Forecasting sums regular periods and fills missing periods with zero through resampling. It has no seasonality or backtested accuracy. Bounds use constant residual spread and are not calibrated prediction intervals; negative forecasts are possible.
- Gemini sees summaries, category values, and preview rows. Answers can be incorrect. Grouped output contains at most 20 groups for categorical columns with at most 50 values. Context uses at most 50 stored messages.
- Browser JWTs use localStorage. There is no refresh/revocation flow, rate limiting, password reset, RBAC, or deployment hardening.
- Tables use `create_all`; migrations and backup/restore workflows are not implemented. Upload storage is local to the backend.
- Quality scores are rule-based heuristics, not a validated standard. Statistical insights are computed locally rather than generated by Gemini.
- Browser smoke checks do not replace an automated browser suite. Live Gemini responses, legacy XLS samples, and Docker execution remain unverified.

## Future improvements

Cross-validation with separate final evaluation, fitted feature-selection transformers, forecasting backtests, background job limits, schema migrations, model persistence, broader browser tests, and deployment-specific authentication hardening are plans, not implemented features.

Read [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md) for explanations and defensible resume statements, and [review notes](docs/REVIEW.md) for fixed problems and remaining constraints.
