# Deploying to Render (PW#7, LC12)

Render builds the repo's `Dockerfile` and redeploys on every push to `main` (Auto-Deploy). The GHCR image from `cd.yml` is a separate delivery artifact; Render builds from source.

## One-time setup (Blueprint, fastest)

1. Sign in at render.com with GitHub and allow access to `Ferhadb/SoftwareFinalProject`.
2. **New +** -> **Blueprint** -> pick the repo -> branch `main`. Render reads `render.yaml` and creates:
   - Web service `spendsmart` (Docker, free plan, health check `/health`, auto-deploy on)
   - Postgres `spendsmart-db` (free plan)
3. Click **Apply**. The first build takes a few minutes.
4. Open `https://spendsmart.onrender.com/health`. Expect `{"status":"ok","db":"ok",...}`.

### Without the Blueprint (manual)

**New +** -> **Web Service** -> *Build and deploy from a Git repository* -> this repo -> **Runtime: Docker** -> branch `main` -> Auto-Deploy **Yes** -> Health Check Path `/health`. Create a Postgres (**New +** -> **PostgreSQL**) and add the environment variables below.

## Environment variables

| Key | Value | Notes |
|---|---|---|
| `APP_ENV` | `prod` | The app refuses to start in prod without a real `JWT_SECRET` |
| `JWT_SECRET` | random string | The Blueprint generates it. Never commit it |
| `DATABASE_URL` | Render Postgres connection string | `postgres://` is rewritten to the psycopg driver automatically |
| `CATEGORIZER` | `rules` (or `chain`) | `chain` also needs `LLM_API_KEY` |
| `LOG_LEVEL` | `INFO` | |

## Verify

```bash
curl -s https://spendsmart.onrender.com/health
```

Then open the site, register, add `Starbucks 6.50`, and check the **Logs** tab for the request lines.

## Free tier notes

- The service sleeps after about 15 minutes idle; the first request after that takes 30-60 s. The UptimeRobot monitor (see `runbook.md`) pings every 5 minutes. Open the app a few minutes before presenting.
- Free Postgres expires after about 30 days. If it is created too early it can vanish before the demo: create it around Nov 25 or later, or use an external free Postgres and set `DATABASE_URL`.
- The disk is not persistent, so never use SQLite in production.

## Rollback

See `runbook.md`.
