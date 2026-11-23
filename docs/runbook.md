# Monitoring and rollback runbook (PW#8, LC12)

Service: SpendSmart on Render. Health check: `GET /health` returns `200 {"status":"ok","db":"ok"}`, or `503 {"status":"degraded","db":"down"}` when the database is unreachable.

## 1. Monitoring

**Internal (Render Logs).** Render dashboard -> service -> **Logs**. Every request logs one line: `GET /expenses 200 12.3ms`. Look for `500` lines and Python tracebacks. Budget alerts log at WARNING.

**External (UptimeRobot).** Free account at uptimerobot.com, then:
1. **Add New Monitor** -> type **HTTP(s)**.
2. URL: `https://<service>.onrender.com/health`, interval **5 minutes**.
3. Alert contacts: the whole team's emails.

The 5 minute ping also keeps the free Render instance from sleeping.

## 2. Incident response

| Step | Action |
|---|---|
| 1. Detect | UptimeRobot email, or `/health` is not 200. Note the **time detected**. |
| 2. Diagnose | Render **Logs**: find the first error. Render **Events**: which deploy came just before it? |
| 3. Decide | If the latest deploy caused it, roll back (do not debug in production). |
| 4. Roll back | Render -> service -> **Events** -> pick the last good deploy -> **Rollback**. |
| 5. Verify | `curl https://<service>.onrender.com/health` returns 200 and `db: ok`; log in and add an expense. Note the **time recovered**. |
| 6. Fix forward | `git revert <bad-sha>` on a branch, open a PR, get a review, merge. Auto-deploy ships the fix. |
| 7. Record | Add a row to the table below. |

Render auto-deploys from `main`. Roll back first, then fix the code, because an open rollback is overwritten by the next merge.

## 3. Rollback drill (do once before the demo)

1. Branch `drill/break-health`, make `/health` raise (for example `raise RuntimeError("drill")`), open a PR, merge it. Render deploys the broken version.
2. UptimeRobot reports the monitor down. Note the time.
3. Roll back in Render (step 4 above). Note the time.
4. Revert the commit through a PR (step 6).
5. Fill in the table.

## 4. Incident log

MTTR = time recovered - time detected.

| Date | What broke | Detected | Recovered | MTTR | Fix |
|---|---|---|---|---|---|
| (drill) | | | | | |
