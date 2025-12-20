from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Any, Iterable
import itertools

import pandas as pd


PluginFunc = Callable[[pd.DataFrame, Dict[str, Any]], None]


def markdown_summary(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    destination = Path(params.get("destination", "reports/summary.md"))
    destination.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Dataset Summary",
        f"- Rows: {len(df)}",
        f"- Columns: {len(df.columns)}",
        "",
    ]

    group_by = params.get("group_by")
    if group_by and group_by in df.columns:
        lines.append(f"## Counts by `{group_by}`")
        summary = df.groupby(group_by).size().reset_index(name="count")
        lines.append("```")
        lines.append(summary.to_string(index=False))
        lines.append("```")
    else:
        lines.append("## Column Preview")
        lines.append("```")
        lines.append(df.head().to_string(index=False))
        lines.append("```")

    destination.write_text("\n".join(lines))


def _resolve_columns(existing: pd.DataFrame, requested: Iterable[str] | None) -> list[str]:
    if not requested:
        return []
    cols = [c for c in requested if c in existing.columns]
    missing = set(requested) - set(cols)
    if missing:
        raise ValueError(f"Columns not found: {missing}")
    return cols


def _detect_dimensions(df: pd.DataFrame) -> list[str]:
    dims = []
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(df[col]):
            dims.append(col)
    return dims


def _detect_measures(df: pd.DataFrame) -> list[str]:
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    filtered = [c for c in numeric_cols if "id" not in c.lower()]
    return filtered or numeric_cols


def top_dimension_measure_combinations(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    destination = Path(params.get("destination", "reports/top_combinations.md"))
    destination.parent.mkdir(parents=True, exist_ok=True)

    top_n = int(params.get("top_n", 5))
    min_combo = int(params.get("min_combination", 1))
    max_combo = int(params.get("max_combination", 2))

    dims = params.get("dimensions")
    measures = params.get("measures")

    if dims:
        dims = _resolve_columns(df, dims)
    else:
        dims = _detect_dimensions(df)

    if measures:
        measures = _resolve_columns(df, measures)
    else:
        measures = _detect_measures(df)

    if not dims:
        raise ValueError("No dimension columns available for top_dimension_measure_combinations plugin.")
    if not measures:
        raise ValueError("No numeric measure columns available for top_dimension_measure_combinations plugin.")

    lines = [f"# Top Dimension/Measure Outcomes", ""]

    total_sections = 0
    for r in range(min_combo, min(len(dims), max_combo) + 1):
        for combo in itertools.combinations(dims, r):
            combo_cols = list(combo)
            combo_name = ", ".join(combo_cols)
            lines.append(f"## Dimensions: {combo_name}")
            for measure in measures:
                agg = (
                    df.groupby(combo_cols)[measure]
                    .agg(["sum", "mean", "count"])
                    .reset_index()
                    .rename(columns={"sum": "sum_value", "mean": "avg_value", "count": "row_count"})
                )
                agg = agg.sort_values("sum_value", ascending=False).head(top_n)
                lines.append(f"### Measure: {measure}")
                if agg.empty:
                    lines.append("_No rows_")
                else:
                    lines.append("```")
                    lines.append(agg.to_string(index=False))
                    lines.append("```")
                lines.append("")
            total_sections += 1

    if total_sections == 0:
        lines.append("No valid dimension/measure combinations found.")

    destination.write_text("\n".join(lines))


PLUGIN_REGISTRY: Dict[str, PluginFunc] = {
    "markdown_summary": markdown_summary,
    "top_dimension_measure_combinations": top_dimension_measure_combinations,
}
