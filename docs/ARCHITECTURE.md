# Architecture

React renders the dashboard and sends bearer-authenticated HTTP requests to FastAPI. Routers validate resource ownership, schemas validate payloads, services calculate results, and repositories access SQLAlchemy models.

`app/main.py` registers routers and CORS. Its lifespan initializes missing database tables; importing the app does not connect to PostgreSQL or initialize a Gemini client. `app/database/session.py` supplies the shared request session dependency. `app/auth` owns hashing and JWT functions; `services/auth_service.py` retains compatibility aliases to the same JWT implementation.

Dataset contents live in `backend/uploads`; PostgreSQL contains metadata and ownership. Upload names use UUIDs, bytes are bounded, files are parsed before metadata is saved, and failed uploads are removed. Analytics reload files using pandas. Non-finite values become missing and JSON responses use null where applicable.

ML uses independent preprocessing/estimator pipelines. Training is synchronous and models live only during the request. Forecasting is a linear trend over regular aggregate periods. Gemini context includes summaries, aggregates, preview values and bounded chat history. It is optional and has no vector store or arbitrary code execution.

The frontend API URL is configured with `VITE_API_URL`; it is a build-time value. Docker builds static frontend assets into nginx. Compose provides PostgreSQL readiness gating and persistent database/upload storage. Container execution remains unverified on the review host.

This architecture is appropriate for a small local demonstration. Background queues, model serving, distributed storage, migrations, refresh-token sessions and deployment hardening are outside the current implementation.
