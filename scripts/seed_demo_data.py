"""Seed or reset the demo SQLite database.

Usage examples:
    python scripts/seed_demo_data.py                 # append data
    python scripts/seed_demo_data.py --wipe         # delete all demo rows
    python scripts/seed_demo_data.py --days 14       # add two weeks of synthetic orders
    python scripts/seed_demo_data.py --start-date 2025-03-01 --days 10
"""
from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "demo.sqlite"

CUSTOMERS = [
    "Fiona Apple",
    "Marcus Allen",
    "Priya Patel",
    "Nadia Khan",
    "Liam Chen",
    "Sebastian Gomez",
]
STATUSES = ["pending", "shipped", "delivered", "refunded"]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)


def ensure_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            status TEXT NOT NULL,
            order_total REAL NOT NULL,
            order_date DATE NOT NULL
        );
        """
    )


def wipe_orders(cur) -> None:
    cur.execute("DELETE FROM orders;")


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def next_start_date(cur, explicit_start: Optional[str]) -> date:
    if explicit_start:
        return parse_date(explicit_start)
    cur.execute("SELECT MAX(order_date) FROM orders;")
    max_date = cur.fetchone()[0]
    if max_date:
        last = parse_date(max_date)
        return last + timedelta(days=1)
    return date(2025, 1, 1)


def generate_rows(start: date, days: int, min_per_day: int, max_per_day: int):
    rows = []
    for offset in range(days):
        current = start + timedelta(days=offset)
        for _ in range(random.randint(min_per_day, max_per_day)):
            rows.append(
                (
                    random.choice(CUSTOMERS),
                    random.choice(STATUSES),
                    round(random.uniform(25, 250), 2),
                    current.isoformat(),
                )
            )
    return rows


def append_orders(cur, start_date: date, days: int, min_per_day: int, max_per_day: int) -> int:
    rows = generate_rows(start_date, days, min_per_day, max_per_day)
    if not rows:
        return 0
    cur.executemany(
        "INSERT INTO orders (customer_name, status, order_total, order_date) VALUES (?, ?, ?, ?);",
        rows,
    )
    return len(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed the demo SQLite database with synthetic orders.")
    parser.add_argument("--start-date", help="Optional YYYY-MM-DD date to begin inserting rows from.")
    parser.add_argument("--days", type=int, default=30, help="Number of sequential days to generate (default: 30).")
    parser.add_argument("--min-per-day", type=int, default=1, help="Minimum rows per day (default: 1).")
    parser.add_argument("--max-per-day", type=int, default=4, help="Maximum rows per day (default: 4).")
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
            wipe_orders(cur)
            print("All demo data removed.")
            return

        start_date = next_start_date(cur, args.start_date)
        inserted = append_orders(cur, start_date, args.days, args.min_per_day, args.max_per_day)
        print(
            f"Inserted {inserted} rows spanning {args.days} day(s) starting {start_date} into {DB_PATH}"
        )


def run_cli():
    try:
        main()
    except sqlite3.Error as exc:
        raise SystemExit(f"SQLite error: {exc}")


if __name__ == "__main__":
    run_cli()
