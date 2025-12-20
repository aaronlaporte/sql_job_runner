from __future__ import annotations

import yaml
from pathlib import Path
from typing import Iterable, List

from .job_config import (
    JobConfig,
    OutputConfig,
    PostProcessConfig,
    ValidationConfig,
    TableauValidationConfig,
)


def load_job(path: Path, base_dir: Path | None = None) -> JobConfig:
    data = yaml.safe_load(path.read_text())
    root = base_dir or path.parent.parent

    sql_path = (root / data["sql_file"]).resolve()
    output_cfg = data.get("output", {})
    output = OutputConfig(
        format=output_cfg.get("format", "csv"),
        path=(root / output_cfg.get("path", f"exports/{data['job_id']}.csv")).resolve(),
    )
    post_process = [
        PostProcessConfig(plugin=step["plugin"], params=step.get("params", {}))
        for step in data.get("post_process", [])
    ]
    validation_cfg = data.get("validation")
    validation = None
    if validation_cfg is not None:
        tableau_cfg = None
        if validation_cfg.get("tableau"):
            tableau_cfg = TableauValidationConfig(
                view_id=validation_cfg["tableau"]["view_id"],
                metric=validation_cfg["tableau"].get("metric"),
                alert=validation_cfg["tableau"].get("alert", True),
            )
        validation = ValidationConfig(
            enabled=validation_cfg.get("enabled", True),
            path=(root / validation_cfg["path"]).resolve() if validation_cfg.get("path") else None,
            tableau=tableau_cfg,
        )
    if validation is None:
        validation = ValidationConfig()
    return JobConfig(
        job_id=data["job_id"],
        name=data.get("name", data["job_id"]),
        description=data.get("description", ""),
        enabled=data.get("enabled", True),
        sql_file=sql_path,
        parameters=data.get("parameters", {}),
        output=output,
        post_process=post_process,
        validation=validation,
    )


def load_jobs(paths: Iterable[Path], base_dir: Path | None = None) -> List[JobConfig]:
    jobs: List[JobConfig] = []
    for path in paths:
        jobs.append(load_job(path, base_dir=base_dir))
    return jobs
