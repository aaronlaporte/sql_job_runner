from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class OutputConfig:
    format: str
    path: Path


@dataclass
class PostProcessConfig:
    plugin: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableauValidationConfig:
    view_id: str
    metric: Optional[str] = None
    alert: bool = True


@dataclass
class ValidationConfig:
    enabled: bool = True
    path: Path | None = None
    tableau: TableauValidationConfig | None = None


@dataclass
class JobConfig:
    job_id: str
    name: str
    description: str
    enabled: bool
    sql_file: Path
    parameters: Dict[str, Any] = field(default_factory=dict)
    output: OutputConfig | None = None
    post_process: List[PostProcessConfig] = field(default_factory=list)
    validation: ValidationConfig | None = None
