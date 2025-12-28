# Documentation

This folder collects reference material and onboarding templates for `sql_job_runner`.

## Env Architecture
- Base envs live in `envs/clients/<client>.env` (real credentials, export/report roots, logging level, etc.).
- Schedule wrappers live in `envs/schedules/<window>/<client>.env` referencing the base env via `BASE_ENV=clients/<client>.env` plus a `JOBS` list.
- Example cron for 5 a.m. daily runs:
  ```
  0 5 * * * /bin/bash -lc "cd /path/sql_job_runner && ./scripts/run_scheduled_jobs.sh envs/schedules/5am"
  ```

## Onboarding Kit
- Templates live in `documentation/onboarding-kit/`:
  - `client_profile_template.md`
  - `client_connection_checklist.md`
  - `client_setup.md`
  - `README.md` (workflow walkthrough)
- Client-specific documents live with their envs under `envs/clients/<client>/` (e.g., `envs/clients/nomadata/profile.md`).
