from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd
from sqlalchemy import create_engine, text


@dataclass
class DatabaseClient:
    url: str

    def __post_init__(self) -> None:
        self.engine = create_engine(self.url, future=True)

    def run_query(self, sql: str, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        with self.engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)

