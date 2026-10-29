# sql_job_runner

Modular SQL job runner that executes parameterized queries, exports the results, and chains them into Python-based post-processing/reporting steps.

## Features

- **YAML job definitions** describe which SQL file to execute, the parameters to inject, desired output format, and optional post-processing plugins.
- **Jinja2 templating** inside `queries/*.sql` enables dynamic filters (dates, ids, etc.).
- **SQLAlchemy-powered DB client** works with PostgreSQL, SQLite, and any engine supported by SQLAlchemy (install the appropriate driver, e.g., `psycopg2-binary`).
- **Plugin registry** lets you attach actions (like Markdown summaries) without editing the runner logic.
- **Demo SQLite dataset** (`scripts/seed_demo_data.py`) so you can test the engine end-to-end without hitting a production database.

## Repository layout

```
.
├── .env.example          # Template for DATABASE_URL (uses SQLite demo by default)
├── data/                 # SQLite files or other artifacts (.gitkeep present)
├── exports/              # CSV/Parquet/Excel outputs written here
├── jobs/                 # YAML job definitions
├── queries/              # SQL templates rendered via Jinja2
├── reports/              # Post-processing outputs such as Markdown summaries
├── runner.py             # CLI entry point that executes jobs
├── scripts/seed_demo_data.py  # Seeds demo SQLite DB
├── sql_job_runner/       # Python package (job loader, renderer, plugins, etc.)
└── requirements.txt
```

## Quick start

1. **Install dependencies** (ideally inside a virtual environment):

   ```bash
   pip install -r requirements.txt
   ```

2. **Create a `.env` file** using the example:

   ```bash
   cp .env.example .env
   ```

   - For the demo flow, keep the default `sqlite:///data/demo.sqlite` value.
   - For PostgreSQL or other engines, replace with a SQLAlchemy connection string (e.g., `postgresql+psycopg2://user:pass@host:5432/dbname`).

3. **Seed the demo database** (optional but recommended for a quick win):

   ```bash
   python scripts/seed_demo_data.py
   ```

   - Each run appends additional synthetic orders, continuing from the last stored date.
   - Adjust the volume with flags such as `--days 14 --min-per-day 2 --max-per-day 5`.
   - To wipe the demo table and start over: `python scripts/seed_demo_data.py --wipe`.
   - Need a different flavor of data? Run the weather generator for a multi-decade national temperature dataset:

     ```bash
     python scripts/seed_demo_weather.py --wipe --start-year 1980 --end-year 2025
     ```

     This creates a `weather_observations` table with daily records, seasonality, volatility, and a slight warming trend. Adjust regions, years, or volatility with the script flags.
   - Want a sports analytics sandbox? Populate an NFL-style star schema with:

     ```bash
     python scripts/seed_demo_nfl.py --wipe --start-season 2000 --end-season 2024
     ```

     That script builds `dim_team`, `dim_player`, `dim_season`, `fact_team_stats`, and `fact_player_stats` with realistic-yet-synthetic rosters and stats so you can practice dimensional modeling.

4. **Run the sample job**:

   ```bash
   python runner.py
   ```

   - Outputs land in `exports/sample_orders.csv`.
   - A Markdown summary is generated at `reports/sample_orders_summary.md`.

5. **Target specific jobs** (when multiple YAML files exist):

   ```bash
   python runner.py --only sample_orders another_job_id
   ```

6. **Generate narrative commentary** (optional but handy when you just want insights):

   ```bash
   python scripts/analyze_report.py sample_orders
   ```

   - Reads the latest export for that job, auto-detects dimension + measure columns, and writes a text summary to `reports/sample_orders_analysis.txt`.
   - Pass `--measure order_total` to override the metric column or adjust `--top-n` / `--combo-top-n` for deeper results.
   - Every run also produces `reports/<job_id>_validation.json`, which records pre/post row counts and column-level stats to catch data-loss issues.

## Quickstart for new jobs

1. **Configure the database**  
   - Copy `.env.example` to `.env` and set `DATABASE_URL` to your actual connection string (e.g., `postgresql+psycopg2://user:pass@host:5432/dbname`).
   - Install the matching driver (`psycopg2-binary`, `pyodbc`, etc.) if it isn’t already in `requirements.txt`.

2. **Write the SQL template**  
   - Create `queries/<job_id>.sql`. Use Jinja placeholders like `{{ start_date }}` if you need parameters, or wrap optional clauses in `{% if %}` blocks.

3. **Define the job**  
   - Add `jobs/<job_id>.yaml` with fields:
     ```yaml
     job_id: my_job
     sql_file: queries/my_job.sql
     output:
       format: csv
       path: exports/my_job.csv
     post_process:
  - plugin: markdown_summary
    params:
      destination: reports/my_job_summary.md
validation:
  enabled: true
  path: reports/my_job_validation.json
  tableau:
    view_id: 12ab34cd-...
    metric: revenue
    alert: true
```
   - Include `parameters:` only if your SQL references them.

4. **Test the job**  
   ```bash
   python runner.py --only my_job
   ```
   - Inspect the output file and any plugin artifacts (CSV, Markdown, etc.).

5. **Optional: analyze the export**  
   ```bash
   python scripts/analyze_report.py my_job
   ```
   - Produces `reports/my_job_analysis.txt` with top dimensions/combos.

6. **Schedule or chain jobs**  
   - Use cron/Task Scheduler to run `python runner.py --only my_job` at the desired cadence.
   - Or omit `--only` to run every enabled job in `jobs/`.

That’s it—new reports only require a SQL template plus a YAML definition.

## Job definition schema (`jobs/*.yaml`)

```yaml
job_id: unique_identifier
name: Friendly job name
description: Optional context for humans
enabled: true            # allows you to ship but temporarily disable a job
sql_file: queries/my_query.sql
parameters:              # rendered via Jinja2
  start_date: 2025-01-01
  end_date: 2025-01-31
output:
  format: csv            # csv | parquet | excel
  path: exports/my_job.csv
post_process:
  - plugin: markdown_summary
    params:
      destination: reports/my_job_summary.md
      group_by: status
```

### Adding a new job

1. Create the SQL under `queries/`. Use `{{ parameter_name }}` placeholders anywhere you need dynamic values.
2. Write a YAML file under `jobs/` that references the SQL file, output format, and any post-processing plugins.
3. Update `.env` if the job needs a different database (e.g., point to staging vs prod).
4. Run `python runner.py --only your_job_id` to test.

## Plugin system

Plugins live in `sql_job_runner/plugins.py` and receive a copy of the Pandas DataFrame plus a params dict. Example: `markdown_summary` writes row counts and optional group-by stats to Markdown. To add your own plugin:

1. Write a new function that matches `PluginFunc` (signature `(df, params) -> None`).
2. Register it inside `PLUGIN_REGISTRY`.
3. Reference it by name from any job's `post_process` section.

Built-in plugins:

- `markdown_summary` – quick dataset meta info + optional group-by counts.
- `top_dimension_measure_combinations` – scans categorical dimensions vs numeric measures (auto-skipping columns that look like IDs) and lists the top-N aggregate outcomes for each pair in Markdown.
- `zip_and_archive` – bundles one or more output files into a zip so you can archive the run artifacts. Parameters: `files`, `destination`, optional `append`.
- `data_quality_snapshot` – records row counts/numeric stats to JSON and optionally enforces thresholds compared to the prior run. Parameters: `path`, optional `thresholds.row_count_pct`.
- `sftp_upload` – shells out to `scp` to push a generated file to `username@host:/remote/path`. Parameters: `source`, `host`, `username`, `remote_path`, optional `port`, `ssh_key`, `scp_options`.
- `load_to_database` – writes the DataFrame into another database table via SQLAlchemy. Parameters: `connection_string`, `table`, optional `schema`, `if_exists`, `chunksize`, `include_index`, `method`.
- `s3_upload` / `gcs_upload` – push the export to cloud object storage buckets using boto3 / google-cloud-storage (installed separately). Parameters: `source`, `bucket`, and destination keys (`key` or `blob`).
- `email_report` – send an SMTP email with optional attachments once the job finishes. Parameters: `smtp_host`, `sender`, `recipients`, optional `subject`, `body`, `attachments`, credentials.
- `slack_notification` – POST to a Slack webhook (or similar) with a templated message once the job completes. Parameters: `webhook_url`, `message`.

## Validation checks

Each job can (optionally) run built-in validation after the export is written. The runner re-opens the output file and compares row counts, null counts, unique counts, and numeric aggregates to the in-memory DataFrame. Results are written to the JSON file specified by the `validation.path` (defaults to `reports/<job>_validation.json`). If any metric differs, the job fails fast with a descriptive error so you know something transformed or was lost between pre/post steps.

Need to verify Tableau dashboards as well? Add a `validation.tableau` block with `view_id` (and optional `metric`/`alert`). When present, the runner imports the Tableau ops toolkit, fetches the Tableau view data via `tableau-api-lib`, compares it to the DataFrame generated by the job, and (optionally) fires Slack/email alerts wired up in the validation helpers. Make sure:

- [tableau-admin-toolkit](https://github.com/aaronlaporte/tableau-admin-toolkit) is cloned next to this repo (or pip-installed) so `import admin` / `import validation` work.
- To use a local checkout, clone it alongside this repo (`git clone https://github.com/aaronlaporte/tableau-admin-toolkit.git ../tableau-admin-toolkit`) and install its requirements, or package it and pin a version so deployments pull the same admin/validation code.
- Tableau PAT credentials (`TABLEAU_SERVER`, `TABLEAU_SITE`, `TABLEAU_PAT_NAME`, `TABLEAU_PAT_SECRET`, etc.) are available in your environment or `.env`.
- `config/settings.yaml` in the Tableau toolkit has been copied from its example template so metadata such as the default metric and alerts are defined.

With that wiring, running `python runner.py` both exports datasets **and** confirms the Tableau dashboards fed by those datasets stay in sync.

## Demo datasets available

| Script | Tables created | Notes |
| --- | --- | --- |
| `scripts/seed_demo_data.py` | `orders` | Classic order-export scenario used by `sample_orders` job. |
| `scripts/seed_demo_weather.py` | `weather_observations` | Daily temps/precip across multiple regions with seasonality + warming trend. |
| `scripts/seed_demo_nfl.py` | `dim_team`, `dim_player`, `dim_season`, `fact_team_stats`, `fact_player_stats` | NFL-style star schema with realistic team/roster names and synthetic stats per season. |

Each script accepts `--wipe` plus knobs for the time window/scale. Mix and match them to prototype ETL pipelines or dimensional models before hitting a real database.

## Extending the engine

- **Scheduling** – Hook the `runner.py` command into Windows Task Scheduler, cron, or any orchestrator. The runner is pure CLI, so any scheduler works.
- **Notifications** – Add a plugin that emails the CSV, posts to Slack, or logs to your monitoring system.
- **Chained jobs** – Keep job outputs predictable (e.g., `exports/<job>.csv`), then add downstream jobs/plugins that consume those files to build dashboards or PDFs.
- **Automated commentary** – Run `python scripts/analyze_report.py <job_id>` post-export to produce `.txt` narratives you can email, archive, or paste into tickets.

## Troubleshooting

- `DATABASE_URL is not set` – Ensure you created `.env` or exported the variable in your shell.
- `sqlalchemy.exc.OperationalError` – Connection details are wrong or the DB is unreachable.
- `Unknown plugin` – Typo in the YAML `post_process` block or the plugin wasn't registered in `plugins.py`.
- Need to inspect generated SQL? Enable `print(sql)` in `runner.py` temporarily or log it inside a plugin before execution.

Happy job running!
