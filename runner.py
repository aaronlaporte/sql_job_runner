from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path
from typing import Iterable, List

from dotenv import load_dotenv

from sql_job_runner.database import DatabaseClient
from sql_job_runner.job_loader import load_job
from sql_job_runner.job_config import ValidationConfig
from sql_job_runner.plugins import PLUGIN_REGISTRY
from sql_job_runner.sql_renderer import SQLRenderer
from sql_job_runner.validation import validate_export


def collect_job_files(patterns: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    for pattern in patterns:
        for match in glob.glob(pattern):
            files.append(Path(match).resolve())
    return sorted(files)


def run_job(job_file: Path, renderer: SQLRenderer, db: DatabaseClient, only: set[str] | None) -> None:
    job = load_job(job_file)
    if only and job.job_id not in only:
        return
    if not job.enabled:
        print(f"Skipping {job.job_id} (disabled)")
        return

    print(f"Running job {job.job_id} → {job.output.path}")
    sql = renderer.render(job.sql_file, job.parameters)
    df = db.run_query(sql)
    output_path = job.output.path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if job.output.format == "csv":
        df.to_csv(output_path, index=False)
    elif job.output.format == "parquet":
        df.to_parquet(output_path, index=False)
    elif job.output.format == "excel":
        df.to_excel(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {job.output.format}")

    for step in job.post_process:
        plugin = PLUGIN_REGISTRY.get(step.plugin)
        if not plugin:
            raise ValueError(f"Unknown plugin: {step.plugin}")
        params = step.params or {}
        if params.get("enabled") is False:
            print(f"  Post-process step '{step.plugin}' skipped (disabled)")
            continue
        plugin(df.copy(), params)
        print(f"  Post-process step '{step.plugin}' completed")

    validation_cfg = job.validation or ValidationConfig()
    if validation_cfg.enabled:
        validate_export(job.job_id, df, output_path, job.output.format, validation_cfg)
        report_path = validation_cfg.path if validation_cfg.path else Path("reports") / f"{job.job_id}_validation.json"
        print(f"  Validation recorded at {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run configured SQL jobs")
    parser.add_argument(
        "--jobs",
        nargs="*",
        default=["jobs/*.yaml"],
        help="Glob(s) of job definition files to load",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Optional list of job_ids to run",
    )
    args = parser.parse_args()

    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit("DATABASE_URL is not set. Copy .env.example to .env and update it.")

    db = DatabaseClient(db_url)
    renderer = SQLRenderer(base_dir=Path(__file__).parent)
    job_files = collect_job_files(args.jobs)
    if not job_files:
        raise SystemExit("No job files found.")

    only_set = set(args.only) if args.only else None

    for job_file in job_files:
        run_job(job_file, renderer, db, only_set)


if __name__ == "__main__":
    main()
