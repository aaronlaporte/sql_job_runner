# Environment grouping

- `envs/clients/` stores base environment files per client. These contain real credentials, export/report roots, etc., and can exist even if the client has no scheduled jobs yet.
- `envs/schedules/<window>/` holds schedule-specific wrappers. Each file references a base env via `BASE_ENV=clients/<client>.env` and lists the `JOBS` that should run in that window.
- To onboard a client without scheduling them, create their base env under `envs/clients/` only. When ready to schedule, add a wrapper file under the appropriate `envs/schedules/<window>/` folder pointing to the base env.
- Cron example (5 a.m. daily):
  ```
  0 5 * * * /bin/bash -lc "cd /path/sql_job_runner && ./scripts/run_scheduled_jobs.sh envs/schedules/5am"
  ```
