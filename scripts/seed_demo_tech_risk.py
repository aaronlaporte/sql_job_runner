"""Seed a synthetic technology risk assessment dataset for financial services.

Usage examples:
    python scripts/seed_demo_tech_risk.py --days 30
    python scripts/seed_demo_tech_risk.py --start-date 2024-01-15 --days 10 --min-per-day 2 --max-per-day 6
    python scripts/seed_demo_tech_risk.py --wipe
"""
from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "tech_risk.sqlite"

BUSINESS_UNITS = [
    "Global Banking",
    "Wealth Management",
    "Retail Deposits",
    "Capital Markets",
    "Risk & Treasury",
    "Digital Lending",
]

SYSTEMS = [
    "Payments Core",
    "Client Onboarding Portal",
    "Trade Booking Engine",
    "Wealth CRM",
    "Fraud Analytics Platform",
    "Regulatory Reporting Hub",
]

CONTROL_DOMAINS = [
    "Identity & Access",
    "Change Management",
    "Cloud Governance",
    "Third-Party Oversight",
    "Business Continuity",
    "Data Protection",
]

RISK_FACTORS = [
    "Privileged access drift",
    "Vendor concentration",
    "Unpatched middleware",
    "Encryption gaps",
    "Inadequate monitoring",
    "Legacy batch dependencies",
]

REGULATORY_REFERENCES = [
    "SOX 404",
    "GLBA",
    "FFIEC CAT",
    "NYDFS 500",
    "Basel II Tech Risk",
    "EBA ICT Guidelines",
]

STATUSES = ["open", "in progress", "mitigation accepted", "closed"]
OWNERS = ["Tech Risk Ops", "Resilience PMO", "IAM Guild", "Cloud Center", "Vendor Risk Team"]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)


def ensure_table(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS technology_risk_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessed_on DATE NOT NULL,
            business_unit TEXT NOT NULL,
            system_name TEXT NOT NULL,
            control_domain TEXT NOT NULL,
            risk_factor TEXT NOT NULL,
            inherent_risk INTEGER NOT NULL,
            residual_risk INTEGER NOT NULL,
            severity TEXT NOT NULL,
            finding_summary TEXT NOT NULL,
            regulatory_reference TEXT NOT NULL,
            remediation_owner TEXT NOT NULL,
            target_remediation DATE NOT NULL,
            status TEXT NOT NULL
        );
        """
    )


def wipe_table(cur: sqlite3.Cursor) -> None:
    cur.execute("DELETE FROM technology_risk_assessments;")


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def severity_from_score(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 55:
        return "moderate"
    return "low"


def generate_rows(start: date, days: int, min_per_day: int, max_per_day: int):
    rows = []
    for offset in range(days):
        assessed_on = start + timedelta(days=offset)
        for _ in range(random.randint(min_per_day, max_per_day)):
            domain = random.choice(CONTROL_DOMAINS)
            system = random.choice(SYSTEMS)
            inherent = random.randint(55, 95)
            residual = max(10, inherent - random.randint(5, 35))
            severity = severity_from_score(residual)
            summary = f"{domain} gap on {system} due to {random.choice(RISK_FACTORS)}"
            rows.append(
                (
                    assessed_on.isoformat(),
                    random.choice(BUSINESS_UNITS),
                    system,
                    domain,
                    random.choice(RISK_FACTORS),
                    inherent,
                    residual,
                    severity,
                    summary,
                    random.choice(REGULATORY_REFERENCES),
                    random.choice(OWNERS),
                    (assessed_on + timedelta(days=random.randint(15, 120))).isoformat(),
                    random.choice(STATUSES),
                )
            )
    return rows


def append_rows(
    cur: sqlite3.Cursor,
    start_date: date,
    days: int,
    min_per_day: int,
    max_per_day: int,
) -> int:
    rows = generate_rows(start_date, days, min_per_day, max_per_day)
    if not rows:
        return 0
    cur.executemany(
        """
        INSERT INTO technology_risk_assessments (
            assessed_on,
            business_unit,
            system_name,
            control_domain,
            risk_factor,
            inherent_risk,
            residual_risk,
            severity,
            finding_summary,
            regulatory_reference,
            remediation_owner,
            target_remediation,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        rows,
    )
    return len(rows)


def next_start_date(cur: sqlite3.Cursor, explicit_start: str | None) -> date:
    if explicit_start:
        return parse_date(explicit_start)
    cur.execute("SELECT MAX(assessed_on) FROM technology_risk_assessments;")
    max_date = cur.fetchone()[0]
    if max_date:
        return parse_date(max_date) + timedelta(days=1)
    return date(2024, 1, 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed the tech risk assessment demo dataset for financial services scenarios."
    )
    parser.add_argument("--start-date", help="Optional YYYY-MM-DD date to begin inserting rows from.")
    parser.add_argument("--days", type=int, default=30, help="Number of sequential days to generate (default: 30).")
    parser.add_argument("--min-per-day", type=int, default=1, help="Minimum assessments per day (default: 1).")
    parser.add_argument("--max-per-day", type=int, default=4, help="Maximum assessments per day (default: 4).")
    parser.add_argument("--wipe", action="store_true", help="Delete all rows and exit.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    with conn:
        cur = conn.cursor()
        ensure_table(cur)

        if args.wipe:
            wipe_table(cur)
            print("All technology risk records removed.")
            return

        start_date = next_start_date(cur, args.start_date)
        inserted = append_rows(cur, start_date, args.days, args.min_per_day, args.max_per_day)
        print(
            f"Inserted {inserted} technology risk assessments spanning {args.days} day(s) starting {start_date} into {DB_PATH}"
        )


def run_cli() -> None:
    try:
        main()
    except sqlite3.Error as exc:
        raise SystemExit(f"SQLite error: {exc}")


if __name__ == "__main__":
    run_cli()
