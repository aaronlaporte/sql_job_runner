from __future__ import annotations

import json
from datetime import datetime
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .job_config import ValidationConfig, TableauValidationConfig

# Make tabl/ importable when running locally alongside sql_job_runner
TABL_ROOT = Path(__file__).resolve().parents[2] / "tabl"
if TABL_ROOT.exists() and str(TABL_ROOT) not in sys.path:
    sys.path.append(str(TABL_ROOT))

try:  # pragma: no cover - optional dependency
    from tabl.validation.dashboards import fetch_view_data
    from tabl.validation.comparator import compare_metrics as compare_tableau_metrics
    from tabl.validation.alerts import notify_email, notify_slack
except Exception as exc:  # pragma: no cover
    fetch_view_data = None
    compare_tableau_metrics = None
    notify_email = None
    notify_slack = None
    TABL_IMPORT_ERROR = exc
else:
    TABL_IMPORT_ERROR = None

def _read_output(path: Path, fmt: str) -> pd.DataFrame:
    if fmt == "csv":
        return pd.read_csv(path)
    if fmt == "parquet":
        return pd.read_parquet(path)
    if fmt == "excel":
        return pd.read_excel(path)
    raise ValueError(f"Unsupported format for validation: {fmt}")


def _numeric_stats(series: pd.Series) -> Dict[str, float]:
    stats: Dict[str, float] = {}
    if pd.api.types.is_numeric_dtype(series):
        stats["sum"] = float(series.sum(skipna=True))
        stats["min"] = float(series.min(skipna=True))
        stats["max"] = float(series.max(skipna=True))
    return stats


def compute_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": {},
    }
    for col in df.columns:
        series = df[col]
        detail: Dict[str, Any] = {
            "non_null": int(series.notna().sum()),
            "nulls": int(series.isna().sum()),
            "unique": int(series.nunique(dropna=True)),
        }
        detail.update(_numeric_stats(series))
        metrics["columns"][col] = detail
    return metrics


def compare_export_metrics(pre: Dict[str, Any], post: Dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if pre["row_count"] != post["row_count"]:
        issues.append(f"Row count mismatch pre={pre['row_count']} post={post['row_count']}")
    if pre["column_count"] != post["column_count"]:
        issues.append(f"Column count mismatch pre={pre['column_count']} post={post['column_count']}")

    for col, detail in pre["columns"].items():
        post_detail = post["columns"].get(col)
        if not post_detail:
            issues.append(f"Column '{col}' missing post-export")
            continue
        for key in ("non_null", "nulls", "unique"):
            if detail.get(key) != post_detail.get(key):
                issues.append(
                    f"Column '{col}' {key} mismatch pre={detail.get(key)} post={post_detail.get(key)}"
                )
        for key in ("sum", "min", "max"):
            if key in detail or key in post_detail:
                if round(detail.get(key, 0.0), 5) != round(post_detail.get(key, 0.0), 5):
                    issues.append(
                        f"Column '{col}' {key} mismatch pre={detail.get(key)} post={post_detail.get(key)}"
                    )
    return issues


def validate_export(
    job_id: str,
    df: pd.DataFrame,
    output_path: Path,
    fmt: str,
    validation_cfg: ValidationConfig | None,
) -> None:
    cfg = validation_cfg or ValidationConfig()
    if not cfg.enabled:
        return

    report_path = (cfg.path or Path("reports") / f"{job_id}_validation.json").resolve()
    export_result = _run_export_validation(df, output_path, fmt)

    payload: Dict[str, Any] = {
        "job_id": job_id,
        "output": str(output_path),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "pre_metrics": export_result["pre_metrics"],
        "post_metrics": export_result["post_metrics"],
        "issues": export_result["issues"],
        "passed": export_result["passed"],
    }

    tableau_result: Optional[Dict[str, Any]] = None
    if cfg.tableau:
        tableau_result = _run_tableau_validation(cfg.tableau, df)
        payload["tableau_validation"] = tableau_result
        payload["passed"] = payload["passed"] and tableau_result["passed"]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2))

    errors: List[str] = []
    if export_result["issues"]:
        errors.append(f"Export mismatch: {'; '.join(export_result['issues'])}")
    if tableau_result and not tableau_result["passed"]:
        errors.append(
            "Tableau discrepancy: Δ="
            f"{tableau_result['difference']} ({tableau_result['difference_pct']:.2f}%)"
        )
    if errors:
        raise ValueError(f"Validation failed for job '{job_id}': {' | '.join(errors)}")


def _run_export_validation(df: pd.DataFrame, output_path: Path, fmt: str) -> Dict[str, Any]:
    pre_metrics = compute_metrics(df)
    post_df = _read_output(output_path, fmt)
    post_metrics = compute_metrics(post_df)
    issues = compare_export_metrics(pre_metrics, post_metrics)
    return {
        "pre_metrics": pre_metrics,
        "post_metrics": post_metrics,
        "issues": issues,
        "passed": len(issues) == 0,
    }


def _run_tableau_validation(tableau_cfg: TableauValidationConfig, reference_df: pd.DataFrame) -> Dict[str, Any]:
    if TABL_IMPORT_ERROR is not None or fetch_view_data is None or compare_tableau_metrics is None:
        raise RuntimeError(
            "tabl validation utilities are unavailable. Ensure the ../tabl package "
            "exists and is importable."
        ) from TABL_IMPORT_ERROR

    tableau_df = fetch_view_data(tableau_cfg.view_id)
    result = compare_tableau_metrics(tableau_df, reference_df, metric=tableau_cfg.metric)

    alert_sent = False
    if tableau_cfg.alert and not result.within_threshold:
        message = (
            f"[sql_job_runner] Tableau validation failed for view {tableau_cfg.view_id} "
            f"metric {result.metric}: Tableau={result.tableau_value} "
            f"Reference={result.reference_value} Δ={result.difference} "
            f"({result.difference_pct:.2f}%)"
        )
        if notify_slack:
            try:
                notify_slack(message)
                alert_sent = True
            except Exception:
                pass
        if notify_email:
            try:
                notify_email(
                    subject="Tableau validation discrepancy",
                    body=message,
                )
                alert_sent = True
            except Exception:
                pass

    return {
        "view_id": tableau_cfg.view_id,
        "metric": result.metric,
        "tableau_value": result.tableau_value,
        "reference_value": result.reference_value,
        "difference": result.difference,
        "difference_pct": result.difference_pct,
        "passed": result.within_threshold,
        "alert_sent": alert_sent,
    }
