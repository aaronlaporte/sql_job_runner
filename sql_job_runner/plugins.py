from __future__ import annotations

import json
import itertools
import mimetypes
import smtplib
import subprocess
import urllib.error
import urllib.request
import zipfile
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

import pandas as pd
from sqlalchemy import create_engine


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


def sftp_upload(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    source = Path(params.get("source", ""))
    if not source.exists():
        raise ValueError("sftp_upload requires a valid 'source' file path.")
    host = params.get("host")
    username = params.get("username")
    remote_path = params.get("remote_path")
    if not all([host, username, remote_path]):
        raise ValueError("sftp_upload requires 'host', 'username', and 'remote_path'.")

    port = str(params.get("port", 22))
    identity_file = params.get("ssh_key")
    extra_opts = params.get("scp_options", [])
    if isinstance(extra_opts, str):
        extra_opts = [extra_opts]

    cmd = ["scp", "-P", port]
    if identity_file:
        cmd.extend(["-i", str(identity_file)])
    cmd.extend([str(opt) for opt in extra_opts])
    cmd.append(str(source))
    cmd.append(f"{username}@{host}:{remote_path}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"SCP upload failed: {result.stderr.strip()}")


def load_to_database(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    connection_string = params.get("connection_string")
    table_name = params.get("table")
    if not connection_string or not table_name:
        raise ValueError("load_to_database requires 'connection_string' and 'table'.")

    if_exists = params.get("if_exists", "append")
    schema = params.get("schema")
    include_index = bool(params.get("include_index", False))
    chunksize = params.get("chunksize")

    engine = create_engine(connection_string)
    with engine.begin() as conn:
        df.to_sql(
            table_name,
            conn,
            if_exists=if_exists,
            schema=schema,
            index=include_index,
            chunksize=chunksize,
            method=params.get("method"),
        )


def s3_upload(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    source = Path(params.get("source", ""))
    if not source.exists():
        raise ValueError("s3_upload requires a valid 'source' file path.")
    bucket = params.get("bucket")
    key = params.get("key")
    if not bucket or not key:
        raise ValueError("s3_upload requires 'bucket' and 'key'.")

    try:
        import boto3
    except ImportError as exc:
        raise ImportError("boto3 is required for s3_upload plugin.") from exc

    session_kwargs: Dict[str, Any] = {}
    profile = params.get("profile")
    if profile:
        session_kwargs["profile_name"] = profile
    session = boto3.session.Session(**session_kwargs)
    client = session.client("s3")

    extra_args = params.get("extra_args")
    upload_kwargs: Dict[str, Any] = {}
    if extra_args:
        upload_kwargs["ExtraArgs"] = extra_args
    client.upload_file(str(source), bucket, key, **upload_kwargs)


def gcs_upload(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    source = Path(params.get("source", ""))
    if not source.exists():
        raise ValueError("gcs_upload requires a valid 'source' file path.")
    bucket_name = params.get("bucket")
    blob_name = params.get("blob")
    if not bucket_name or not blob_name:
        raise ValueError("gcs_upload requires 'bucket' and 'blob'.")

    try:
        from google.cloud import storage
    except ImportError as exc:
        raise ImportError("google-cloud-storage is required for gcs_upload plugin.") from exc

    credentials_json = params.get("credentials_json")
    if credentials_json:
        client = storage.Client.from_service_account_json(credentials_json)
    else:
        client = storage.Client()

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    content_type = params.get("content_type")
    blob.upload_from_filename(str(source), content_type=content_type)


def email_report(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    smtp_host = params.get("smtp_host")
    smtp_port = int(params.get("smtp_port", 587))
    sender = params.get("sender")
    recipients = params.get("recipients")
    subject = params.get("subject", "SQL Job Report")
    body = params.get("body", f"Rows produced: {len(df)}")
    if not smtp_host or not sender or not recipients:
        raise ValueError("email_report requires 'smtp_host', 'sender', and 'recipients'.")

    username = params.get("username")
    password = params.get("password")
    use_tls = params.get("use_tls", True)

    if isinstance(recipients, str):
        recipients = [addr.strip() for addr in recipients.split(",") if addr.strip()]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    attachments = params.get("attachments", [])
    if isinstance(attachments, str):
        attachments = [attachments]
    for attachment in attachments:
        path = Path(attachment)
        if not path.exists():
            continue
        mime_type, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (mime_type.split("/", 1) if mime_type else ("application", "octet-stream"))
        with path.open("rb") as fh:
            msg.add_attachment(fh.read(), maintype=maintype, subtype=subtype, filename=path.name)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(msg)


def slack_notification(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    webhook_url = params.get("webhook_url")
    if not webhook_url:
        raise ValueError("slack_notification requires 'webhook_url'.")
    message = params.get("message", f"Job completed with {len(df)} rows.")
    payload = {"text": message}
    extra = params.get("extra_fields")
    if isinstance(extra, dict):
        payload.update(extra)

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Slack notification failed: {exc}") from exc


def zip_and_archive(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    destination = Path(params.get("destination", "exports/archive.zip"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    sources = params.get("files") or []
    if isinstance(sources, str):
        sources = [sources]
    if not sources:
        raise ValueError("zip_and_archive requires at least one file in 'files'.")

    mode = "w"
    if destination.exists() and params.get("append", False):
        mode = "a"

    with zipfile.ZipFile(destination, mode=mode) as zf:
        for file_path in sources:
            path = Path(file_path)
            if path.is_file():
                zf.write(path, arcname=path.name)


def data_quality_snapshot(df: pd.DataFrame, params: Dict[str, Any]) -> None:
    path = Path(params.get("path", "reports/data_quality_snapshot.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    compare = params.get("compare", True)
    thresholds = params.get("thresholds", {})
    numeric_cols = df.select_dtypes(include=["number"]).columns

    numeric_summary: Dict[str, Dict[str, float]] = {}
    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        numeric_summary[col] = {
            "min": float(series.min()),
            "max": float(series.max()),
            "avg": float(series.mean()),
        }

    snapshot = {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "numeric_summary": numeric_summary,
    }

    comparison: Dict[str, Any] = {}
    if path.exists() and compare:
        previous = json.loads(path.read_text())
        prev_rows = previous.get("row_count", 0) or 0
        diff = snapshot["row_count"] - prev_rows
        comparison["row_count_diff"] = diff
        comparison["row_count_pct_change"] = (diff / prev_rows * 100) if prev_rows else None

        threshold_pct = thresholds.get("row_count_pct") if isinstance(thresholds, dict) else None
        if threshold_pct is not None and prev_rows:
            pct = abs(diff) / prev_rows * 100
            if pct > threshold_pct:
                raise ValueError(
                    f"Row count changed by {pct:.2f}% which exceeds threshold {threshold_pct}%."
                )
    if comparison:
        snapshot["comparison"] = comparison

    path.write_text(json.dumps(snapshot, indent=2))


PLUGIN_REGISTRY: Dict[str, PluginFunc] = {
    "markdown_summary": markdown_summary,
    "top_dimension_measure_combinations": top_dimension_measure_combinations,
    "sftp_upload": sftp_upload,
    "load_to_database": load_to_database,
    "s3_upload": s3_upload,
    "gcs_upload": gcs_upload,
    "email_report": email_report,
    "slack_notification": slack_notification,
    "zip_and_archive": zip_and_archive,
    "data_quality_snapshot": data_quality_snapshot,
}
