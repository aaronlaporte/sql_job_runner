"""Seed a synthetic NFL-style star schema in data/demo.sqlite.

Creates dimension tables (teams, players, seasons) and fact tables for team- and
player-level stats across a configurable range of seasons.
"""
from __future__ import annotations

import argparse
import random
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "demo.sqlite"
GAMES_PER_SEASON = 17

TEAM_INFO = [
    ("ARI", "Arizona Cardinals", "Phoenix", "NFC", "West"),
    ("ATL", "Atlanta Falcons", "Atlanta", "NFC", "South"),
    ("BAL", "Baltimore Ravens", "Baltimore", "AFC", "North"),
    ("BUF", "Buffalo Bills", "Buffalo", "AFC", "East"),
    ("CAR", "Carolina Panthers", "Charlotte", "NFC", "South"),
    ("CHI", "Chicago Bears", "Chicago", "NFC", "North"),
    ("CIN", "Cincinnati Bengals", "Cincinnati", "AFC", "North"),
    ("CLE", "Cleveland Browns", "Cleveland", "AFC", "North"),
    ("DAL", "Dallas Cowboys", "Dallas", "NFC", "East"),
    ("DEN", "Denver Broncos", "Denver", "AFC", "West"),
    ("DET", "Detroit Lions", "Detroit", "NFC", "North"),
    ("GB", "Green Bay Packers", "Green Bay", "NFC", "North"),
    ("HOU", "Houston Texans", "Houston", "AFC", "South"),
    ("IND", "Indianapolis Colts", "Indianapolis", "AFC", "South"),
    ("JAX", "Jacksonville Jaguars", "Jacksonville", "AFC", "South"),
    ("KC", "Kansas City Chiefs", "Kansas City", "AFC", "West"),
    ("LV", "Las Vegas Raiders", "Las Vegas", "AFC", "West"),
    ("LAC", "Los Angeles Chargers", "Los Angeles", "AFC", "West"),
    ("LAR", "Los Angeles Rams", "Los Angeles", "NFC", "West"),
    ("MIA", "Miami Dolphins", "Miami", "AFC", "East"),
    ("MIN", "Minnesota Vikings", "Minneapolis", "NFC", "North"),
    ("NE", "New England Patriots", "Boston", "AFC", "East"),
    ("NO", "New Orleans Saints", "New Orleans", "NFC", "South"),
    ("NYG", "New York Giants", "New York", "NFC", "East"),
    ("NYJ", "New York Jets", "New York", "AFC", "East"),
    ("PHI", "Philadelphia Eagles", "Philadelphia", "NFC", "East"),
    ("PIT", "Pittsburgh Steelers", "Pittsburgh", "AFC", "North"),
    ("SEA", "Seattle Seahawks", "Seattle", "NFC", "West"),
    ("SF", "San Francisco 49ers", "San Francisco", "NFC", "West"),
    ("TB", "Tampa Bay Buccaneers", "Tampa", "NFC", "South"),
    ("TEN", "Tennessee Titans", "Nashville", "AFC", "South"),
    ("WAS", "Washington Commanders", "Washington", "NFC", "East"),
]

POSITIONS = [
    "QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S", "K"
]

FIRST_NAMES = [
    "James", "Robert", "Michael", "William", "David", "Joseph", "Thomas",
    "Christopher", "Daniel", "Matthew", "Anthony", "Andrew", "Joshua",
    "Ryan", "Brandon", "Justin", "Austin", "Tyler", "Kyle", "Dylan",
    "Aaron", "Ethan", "Noah", "Liam", "Mason", "Logan", "Elijah",
    "Aiden", "Jayden", "Carter"
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson",
    "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez",
    "Clark", "Ramirez", "Lewis", "Robinson"
]


@dataclass
class Player:
    player_id: int
    player_code: str
    full_name: str
    position: str
    birth_year: int
    home_team: str


def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)


def ensure_tables(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_team (
            team_key INTEGER PRIMARY KEY AUTOINCREMENT,
            team_code TEXT UNIQUE,
            team_name TEXT,
            city TEXT,
            conference TEXT,
            division TEXT,
            founded_year INT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_player (
            player_key INTEGER PRIMARY KEY AUTOINCREMENT,
            player_code TEXT UNIQUE,
            full_name TEXT,
            position TEXT,
            birth_year INT,
            home_team_code TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_season (
            season_key INTEGER PRIMARY KEY AUTOINCREMENT,
            season_year INT UNIQUE,
            start_date DATE,
            end_date DATE
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS fact_team_stats (
            season_key INT,
            team_key INT,
            games_played INT,
            wins INT,
            losses INT,
            points_for INT,
            points_against INT,
            yards_for INT,
            yards_against INT,
            turnovers INT,
            takeaways INT,
            playoff_flag INT,
            PRIMARY KEY (season_key, team_key)
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS fact_player_stats (
            season_key INT,
            team_key INT,
            player_key INT,
            position TEXT,
            games_played INT,
            snaps INT,
            yards REAL,
            touchdowns INT,
            tackles REAL,
            sacks REAL,
            interceptions INT,
            PRIMARY KEY (season_key, team_key, player_key)
        );
        """
    )


def wipe_tables(cur) -> None:
    cur.execute("DELETE FROM fact_player_stats;")
    cur.execute("DELETE FROM fact_team_stats;")
    cur.execute("DELETE FROM dim_player;")
    cur.execute("DELETE FROM dim_team;")
    cur.execute("DELETE FROM dim_season;")


def insert_teams(cur) -> Dict[str, int]:
    mapping = {}
    for code, name, city, conf, div in TEAM_INFO:
        cur.execute(
            """
            INSERT INTO dim_team (team_code, team_name, city, conference, division, founded_year)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(team_code) DO UPDATE SET
                team_name=excluded.team_name,
                city=excluded.city,
                conference=excluded.conference,
                division=excluded.division;
            """,
            (code, name, city, conf, div, 1970),
        )
        cur.execute("SELECT team_key FROM dim_team WHERE team_code = ?;", (code,))
        mapping[code] = cur.fetchone()[0]
    return mapping


def insert_seasons(cur, start_year: int, end_year: int) -> Dict[int, int]:
    mapping = {}
    for year in range(start_year, end_year + 1):
        start = date(year, 9, 1)
        end = date(year + 1, 2, 20)
        cur.execute(
            """
            INSERT INTO dim_season (season_year, start_date, end_date)
            VALUES (?, ?, ?)
            ON CONFLICT(season_year) DO UPDATE SET
                start_date=excluded.start_date,
                end_date=excluded.end_date;
            """,
            (year, start.isoformat(), end.isoformat()),
        )
        cur.execute("SELECT season_key FROM dim_season WHERE season_year = ?;", (year,))
        mapping[year] = cur.fetchone()[0]
    return mapping


def generate_players(num_per_team: int = 65) -> List[Player]:
    players: List[Player] = []
    player_id = 1
    for team_code, *_ in TEAM_INFO:
        for _ in range(num_per_team):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"
            position = random.choice(POSITIONS)
            birth_year = random.randint(1975, 2003)
            code = f"{team_code}-{player_id:05d}"
            players.append(Player(player_id, code, name, position, birth_year, team_code))
            player_id += 1
    return players


def insert_players(cur, players: List[Player]) -> Dict[str, int]:
    mapping = {}
    for player in players:
        cur.execute(
            """
            INSERT INTO dim_player (player_code, full_name, position, birth_year, home_team_code)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(player_code) DO UPDATE SET
                full_name=excluded.full_name,
                position=excluded.position,
                birth_year=excluded.birth_year,
                home_team_code=excluded.home_team_code;
            """,
            (player.player_code, player.full_name, player.position, player.birth_year, player.home_team),
        )
        cur.execute("SELECT player_key FROM dim_player WHERE player_code = ?;", (player.player_code,))
        mapping[player.player_code] = cur.fetchone()[0]
    return mapping


def roster_for_team(players: List[Player], team_code: str, roster_size: int = 48) -> List[Player]:
    pool = [p for p in players if p.home_team == team_code]
    return random.sample(pool, min(roster_size, len(pool)))


def team_stats(strength: float) -> Tuple[int, int, int, int, int, int, int, int, int]:
    wins = max(2, min(GAMES_PER_SEASON, int(random.gauss(8 * strength, 3))))
    wins = max(0, min(GAMES_PER_SEASON, wins))
    losses = GAMES_PER_SEASON - wins
    points_for = int(random.gauss(24 * GAMES_PER_SEASON / 2, 80) * strength)
    points_against = int(points_for * random.uniform(0.75, 1.25))
    yards_for = int(random.gauss(360 * GAMES_PER_SEASON, 500) * strength)
    yards_against = int(yards_for * random.uniform(0.8, 1.2))
    turnovers = int(random.uniform(10, 28))
    takeaways = int(random.uniform(10, 30))
    playoff = 1 if wins >= 10 else 0
    return wins, losses, points_for, points_against, yards_for, yards_against, turnovers, takeaways, playoff


def player_stat_line(player: Player, team_strength: float) -> Tuple[int, int, float, int, float, float, int]:
    games = random.randint(8, GAMES_PER_SEASON)
    snaps = random.randint(200, 800)
    yards = touchdowns = tackles = sacks = interceptions = 0
    if player.position == "QB":
        yards = random.gauss(3200, 900) * team_strength
        touchdowns = int(random.gauss(24, 8) * team_strength)
    elif player.position == "RB":
        yards = random.gauss(900, 300) * team_strength
        touchdowns = int(random.gauss(8, 3) * team_strength)
    elif player.position == "WR":
        yards = random.gauss(1000, 350) * team_strength
        touchdowns = int(random.gauss(7, 4) * team_strength)
    elif player.position == "TE":
        yards = random.gauss(600, 150) * team_strength
        touchdowns = int(random.gauss(5, 2) * team_strength)
    elif player.position == "OL":
        yards = 0
    elif player.position in {"DL", "LB"}:
        tackles = random.gauss(80, 20) * team_strength
        sacks = max(0, random.gauss(5, 3) * team_strength)
    elif player.position in {"CB", "S"}:
        tackles = random.gauss(60, 15) * team_strength
        interceptions = max(0, int(random.gauss(2, 2) * team_strength))
    elif player.position == "K":
        yards = 0
        touchdowns = 0
    return (
        games,
        snaps,
        max(0.0, yards),
        max(0, touchdowns),
        max(0.0, tackles),
        max(0.0, sacks),
        max(0, interceptions),
    )


def seed(params) -> None:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    with conn:
        cur = conn.cursor()
        ensure_tables(cur)
        if params.wipe:
            wipe_tables(cur)
        team_mapping = insert_teams(cur)
        season_mapping = insert_seasons(cur, params.start_season, params.end_season)
        players = generate_players(params.player_pool)
        player_mapping = insert_players(cur, players)

        for year in range(params.start_season, params.end_season + 1):
            season_key = season_mapping[year]
            for code, *_ in TEAM_INFO:
                team_key = team_mapping[code]
                strength = random.uniform(0.6, 1.2)
                wins, losses, pf, pa, yf, ya, to, take, playoff = team_stats(strength)
                cur.execute(
                    """
                    INSERT INTO fact_team_stats (
                        season_key, team_key, games_played, wins, losses,
                        points_for, points_against, yards_for, yards_against,
                        turnovers, takeaways, playoff_flag
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        season_key,
                        team_key,
                        GAMES_PER_SEASON,
                        wins,
                        losses,
                        pf,
                        pa,
                        yf,
                        ya,
                        to,
                        take,
                        playoff,
                    ),
                )

                roster = roster_for_team(players, code, params.roster_size)
                for player in roster:
                    stat_line = player_stat_line(player, strength)
                    cur.execute(
                        """
                        INSERT INTO fact_player_stats (
                            season_key, team_key, player_key, position,
                            games_played, snaps, yards, touchdowns,
                            tackles, sacks, interceptions
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            season_key,
                            team_key,
                            player_mapping[player.player_code],
                            player.position,
                            *stat_line,
                        ),
                    )
    conn.close()


@dataclass
class Params:
    start_season: int
    end_season: int
    roster_size: int
    player_pool: int
    wipe: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed NFL-style star schema data.")
    parser.add_argument("--start-season", type=int, default=2000)
    parser.add_argument("--end-season", type=int, default=2024)
    parser.add_argument("--roster-size", type=int, default=48)
    parser.add_argument("--player-pool", type=int, default=65, help="Players generated per team")
    parser.add_argument("--wipe", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    params = Params(
        start_season=args.start_season,
        end_season=args.end_season,
        roster_size=args.roster_size,
        player_pool=args.player_pool,
        wipe=args.wipe,
    )
    seed(params)
    print(
        f"Seeded NFL data for seasons {params.start_season}-{params.end_season} "
        f"with roster size {params.roster_size}."
    )


if __name__ == "__main__":
    main()
