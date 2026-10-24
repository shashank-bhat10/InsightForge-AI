# InsightForge frontend

React, TypeScript, Vite, and Recharts. Follow the [root setup guide](../README.md) to start PostgreSQL and FastAPI and register an account.

From this directory:

```powershell
npm ci
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Set `VITE_API_URL` in `.env` if the API is not at `http://localhost:8000`. Restart Vite after changing it; it is embedded at build time. Never put secrets in Vite variables.

Checks: `npm run build`, `npm run lint`, `npm audit`. To serve a build locally: `npm run preview -- --port 5173`. Registration currently uses backend Swagger UI.
