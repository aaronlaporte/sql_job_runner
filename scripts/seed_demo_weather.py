"""Seed a multi-decade weather dataset inside data/demo.sqlite.

Usage examples:
    python scripts/seed_demo_weather.py --wipe --start-year 1980 --end-year 2025
    python scripts/seed_demo_weather.py --regions "Pacific Northwest" "Gulf Coast"

The script adds daily records per region with synthetic temperatures/precipitation,
including seasonality, long-term warming, and stochastic volatility events.
"""
from __future__ import annotations

import argparse
import math
import random
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, List

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "demo.sqlite"

DEFAULT_REGIONS = [
    "Pacific Northwest",
    "Southwest Desert",
    "Gulf Coast",
    "Great Plains",
    "Midwest",
    "Northeast",
]


@dataclass
class WeatherParams:
    start_year: int
    end_year: int
    regions: List[str]
    warming_per_year: float = 0.02  # deg F per year
    volatility_chance: float = 0.02


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)


def ensure_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS weather_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observation_date DATE NOT NULL,
            region TEXT NOT NULL,
            avg_temp REAL NOT NULL,
            min_temp REAL NOT NULL,
            max_temp REAL NOT NULL,
            precipitation REAL NOT NULL,
            anomaly TEXT NOT NULL
        );
        """
    )


def wipe_table(cur) -> None:
    cur.execute("DELETE FROM weather_observations;")


def seasonal_base(day_of_year: int) -> float:
    # Rough sinusoidal pattern: avg national temps between ~30F (Jan) and ~85F (Jul)
    return 57 + 28 * math.sin(2 * math.pi * (day_of_year - 170) / 365)


def region_offset(region: str) -> float:
    offsets = {
        "Pacific Northwest": -5,
        "Southwest Desert": +10,
        "Gulf Coast": +8,
        "Great Plains": +2,
        "Midwest": -8,
        "Northeast": -6,
    }
    return offsets.get(region, 0.0)


def generate_rows(params: WeatherParams) -> Iterable[tuple]:
    start_date = date(params.start_year, 1, 1)
    end_date = date(params.end_year, 12, 31)
    span_years = params.end_year - params.start_year + 1
    warming_per_day = params.warming_per_year / 365

    current_date = start_date
    cumulative_trend = 0.0
    last_year = start_date.year

    while current_date <= end_date:
        if current_date.year != last_year:
            last_year = current_date.year
        doy = current_date.timetuple().tm_yday
        base_temp = seasonal_base(doy)
        cumulative_trend = (current_date - start_date).days * warming_per_day

        for region in params.regions:
            temp = base_temp + region_offset(region) + cumulative_trend
            noise = random.gauss(0, 5)
            anomaly = "normal"

            if random.random() < params.volatility_chance:
                # Trigger either heat wave or cold snap
                if random.random() < 0.5:
                    spike = random.uniform(10, 18)
                    temp += spike
                    noise += random.uniform(4, 8)
                    anomaly = "heat_wave"
                else:
                    dip = random.uniform(10, 18)
                    temp -= dip
                    noise -= random.uniform(4, 8)
                    anomaly = "cold_snap"

            avg_temp = temp + noise
            diurnal_range = random.uniform(8, 25)
            min_temp = avg_temp - diurnal_range / 2 - random.uniform(0, 4)
            max_temp = avg_temp + diurnal_range / 2 + random.uniform(0, 4)

            precip_base = 0.05 if anomaly == "heat_wave" else 0.12
            precip = max(0.0, random.gauss(precip_base, 0.08))
            if anomaly == "cold_snap" and random.random() < 0.3:
                precip += random.uniform(0.3, 1.2)
                anomaly = "winter_storm"

            yield (
                current_date.isoformat(),
                region,
                round(avg_temp, 2),
                round(min_temp, 2),
                round(max_temp, 2),
                round(precip, 3),
                anomaly,
            )

        current_date += timedelta(days=1)


def chunked(iterable: Iterable[tuple], size: int = 1000):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def insert_rows(cur, rows: Iterable[tuple]) -> int:
    total = 0
    for batch in chunked(rows):
        cur.executemany(
            """
            INSERT INTO weather_observations (
                observation_date,
                region,
                avg_temp,
                min_temp,
                max_temp,
                precipitation,
                anomaly
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            batch,
        )
        total += len(batch)
    return total


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed multi-decade weather observations.")
    parser.add_argument("--start-year", type=int, default=1980, help="First year to generate (inclusive)")
    parser.add_argument("--end-year", type=int, default=2025, help="Last year to generate (inclusive)")
    parser.add_argument("--regions", nargs="*", help="Optional list of regions; defaults to national presets")
    parser.add_argument("--warming", type=float, default=0.02, help="Degrees F warming per year")
    parser.add_argument("--volatility", type=float, default=0.02, help="Daily probability of extreme event")
    parser.add_argument("--wipe", action="store_true", help="Delete existing weather data before inserting")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    ensure_dirs()
    regions = args.regions if args.regions else DEFAULT_REGIONS
    params = WeatherParams(
        start_year=args.start_year,
        end_year=args.end_year,
        regions=regions,
        warming_per_year=args.warming,
        volatility_chance=args.volatility,
    )

    conn = sqlite3.connect(DB_PATH)
    with conn:
        cur = conn.cursor()
        ensure_table(cur)
        if args.wipe:
            wipe_table(cur)
        total = insert_rows(cur, generate_rows(params))
    conn.close()
    print(
        f"Inserted {total:,} weather rows spanning {args.start_year}-{args.end_year} across {len(regions)} region(s)."
    )


if __name__ == "__main__":
    main()
