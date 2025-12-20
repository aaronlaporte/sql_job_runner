"""Generate a narrative analysis for a job's latest export."""
from __future__ import annotations

import argparse
import itertools
from pathlib import Path
import sys
from typing import Iterable, List

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from sql_job_runner.job_loader import load_job  # noqa: E402
JOBS_DIR = BASE_DIR / "jobs"
REPORTS_DIR = BASE_DIR / "reports"


def detect_dimensions(df: pd.DataFrame) -> List[str]:
    dims: List[str] = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
            dims.append(col)
    return dims


def detect_measures(df: pd.DataFrame) -> List[str]:
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    filtered = [c for c in numeric_cols if "id" not in c.lower()]
    return filtered or numeric_cols


def resolve_job_file(job_id: str) -> Path:
    candidates = [JOBS_DIR / f"{job_id}.yaml", JOBS_DIR / f"{job_id}.yml"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit(f"Could not find job file for id '{job_id}'. Looked for: {', '.join(str(c) for c in candidates)}")


def fmt_currency(value: float) -> str:
    return f"${value:,.2f}"


def fmt_value(value: float) -> str:
    return f"{value:,.2f}"


def summarize_dimension(df: pd.DataFrame, dim: str, measure: str, top_n: int) -> List[str]:
    if dim not in df.columns:
        return []
    grouped = (
        df.groupby(dim)[measure]
        .agg(["sum", "mean", "count"])
        .rename(columns={"sum": "sum_value", "mean": "avg_value", "count": "row_count"})
        .sort_values("sum_value", ascending=False)
        .head(top_n)
    )
    lines = [f"Top {top_n} by {dim}:"]
    for idx, row in grouped.iterrows():
        lines.append(
            f"  - {idx}: total {fmt_currency(row['sum_value'])} across {int(row['row_count'])} orders (avg {fmt_currency(row['avg_value'])})"
        )
    return lines


def summarize_combo(df: pd.DataFrame, dims: Iterable[str], measure: str, top_n: int) -> List[str]:
    dims = [d for d in dims if d in df.columns]
    if len(dims) < 2:
        return []
    lines: List[str] = []
    for combo in itertools.combinations(dims, 2):
        grouped = (
            df.groupby(list(combo))[measure]
            .agg(["sum", "mean", "count"])
            .rename(columns={"sum": "sum_value", "mean": "avg_value", "count": "row_count"})
            .sort_values("sum_value", ascending=False)
            .head(top_n)
        )
        if grouped.empty:
            continue
        combo_name = ", ".join(combo)
        lines.append(f"Top {top_n} combinations for {combo_name}:")
        for idx, row in grouped.iterrows():
            labels = ", ".join(str(value) for value in idx) if isinstance(idx, tuple) else str(idx)
            lines.append(
                f"  - {labels}: total {fmt_currency(row['sum_value'])} over {int(row['row_count'])} orders (avg {fmt_currency(row['avg_value'])})"
            )
    return lines


def read_output(job) -> pd.DataFrame:
    output_path = Path(job.output.path)
    if job.output.format == "csv":
        return pd.read_csv(output_path)
    if job.output.format == "parquet":
        return pd.read_parquet(output_path)
    if job.output.format == "excel":
        return pd.read_excel(output_path)
    raise SystemExit(f"Unsupported output format for analysis: {job.output.format}")


def build_analysis(job_id: str, measure: str | None, top_n: int, combo_top_n: int) -> tuple[str, Path]:
    job_file = resolve_job_file(job_id)
    job = load_job(job_file, base_dir=BASE_DIR)
    df = read_output(job)
    if df.empty:
        raise SystemExit("No rows available to analyze.")

    measures = detect_measures(df)
    target_measure = measure or (measures[0] if measures else None)
    if not target_measure or target_measure not in df.columns:
        raise SystemExit(
            f"Measure column '{measure}' not found. Available numeric columns: {', '.join(df.columns)}"
        )

    dims = detect_dimensions(df)

    lines: List[str] = []
    lines.append(f"Report analysis for job '{job.job_id}' ({job.name})")
    lines.append(f"Orders: {len(df)} | Measure: {target_measure} | Total: {fmt_currency(df[target_measure].sum())}")
    lines.append("")

    if dims:
        for dim in dims[:5]:
            lines.extend(summarize_dimension(df, dim, target_measure, top_n))
            lines.append("")
        lines.extend(summarize_combo(df, dims[:4], target_measure, combo_top_n))
    else:
        lines.append("No dimension columns detected for deeper analysis.")

    output_path = REPORTS_DIR / f"{job_id}_analysis.txt"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
    return "\n".join(lines), output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a text analysis based on a job's export.")
    parser.add_argument("job_id", help="Job ID (matches YAML filename without extension)")
    parser.add_argument("--measure", help="Numeric column to analyze; defaults to first numeric column found")
    parser.add_argument("--top-n", type=int, default=3, help="Number of top dimension values to list")
    parser.add_argument("--combo-top-n", type=int, default=3, help="Number of top combos per dimension pair")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    text, output_path = build_analysis(args.job_id, args.measure, args.top_n, args.combo_top_n)
    print(text)
    print(f"\nAnalysis written to {output_path}")


if __name__ == "__main__":
    main()
