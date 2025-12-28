# Env layout

- `envs/clients/<client>/<client>.env` – canonical base env per client (DATABASE_URL, EXPORT_ROOT, REPORT_ROOT, LOG_LEVEL, TZ).
- `envs/clients/<client>/profile.md` and `connection_checklist.md` – optional intake notes that mirror the onboarding kit templates.
- `envs/schedules/<window>/<client>.env` – schedule wrappers that set `BASE_ENV` plus a space-delimited `JOBS` list for that window.

## Quick start

1) Copy `envs/clients/client_template.env.example` to `envs/clients/<client>/<client>.env` and fill in real values.  
2) Create a schedule wrapper like `envs/schedules/5am/<client>.env`:
```
BASE_ENV=clients/<client>/<client>.env
JOBS="sample_orders another_job"
```
3) Cron example: `0 5 * * * /bin/bash -lc "cd /path/sql_job_runner && ./scripts/run_scheduled_jobs.sh envs/schedules/5am"`
