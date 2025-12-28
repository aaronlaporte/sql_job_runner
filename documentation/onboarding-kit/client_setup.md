# Client Onboarding & Scheduled Jobs

This guide explains how to add a new client to the SQL job runner and set up their initial scheduled job run using the `envs/clients` + `envs/schedules` layout.

## 1. New Client Setup

1. **Create the base env file**
   ```bash
   cp envs/clients/client_template.env.example envs/clients/<client>.env
   ```
   This file is the canonical definition for the client regardless of schedules.
2. **Populate credentials and paths**
   - Edit `envs/clients/<client>.env` with the real `DATABASE_URL`, `EXPORT_ROOT`, `REPORT_ROOT`, `LOG_LEVEL`, and `TZ`.
   - Leave it in `envs/clients/` even if the client has no scheduled jobs yet.
3. **Ensure output directories exist**
   ```bash
   mkdir -p exports/<client> reports/<client>
   ```
   (Skip if the env reuses shared folders such as `exports`/`reports`.)
4. **Test manually**
   ```bash
   dotenv run --dotenv-path envs/clients/<client>.env python runner.py --only sample_orders
   ```
   Replace `sample_orders` with any smoke-test job to validate credentials/permissions.
5. **Optional: add to a schedule**
   - When the client needs an automated window (e.g., 5 a.m.), create a wrapper under `envs/schedules/5am/<client>.env`:
     ```
     BASE_ENV=clients/<client>.env
     JOBS="job_a job_b"
     ```
   - The wrapper references the base env and lists the job IDs to run during that window.

## 2. First Scheduled Job for a Client

1. **Author the SQL template** under `queries/<job_id>.sql` (use Jinja placeholders for parameters).
2. **Add the job definition** `jobs/<job_id>.yaml` describing outputs, parameters, plugins, and validation paths.
3. **Dry run with the client env**
   ```bash
   dotenv run --dotenv-path envs/clients/<client>.env python runner.py --only <job_id>
   ```
   Verify exports/reports/validations land in the expected client directories.
4. **Register the job in the schedule wrapper**
   - Update the `JOBS` list inside `envs/schedules/<window>/<client>.env` to include the new `job_id`.
5. **Scheduled execution**
   - Cron (or any scheduler) continues to call `./scripts/run_scheduled_jobs.sh envs/schedules/<window>`; the script loads each wrapper, pulls in the referenced base env, and runs the specified jobs.
    - Any `post_process` step can be temporarily disabled by adding `enabled: false` inside its `params` block (the runner skips those steps automatically).

## Notes

- Create additional schedule folders (e.g., `envs/schedules/noon/`, `envs/schedules/mondays/`) as needed.
- Keep template envs up to date so onboarding new clients remains copy-paste simple.
- Test/staging clients (e.g., Nomadata) can point `DATABASE_URL` to `sqlite:///data/demo.sqlite` while still using the same scheduling mechanism.
