from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class SQLRenderer:
    """Render SQL templates with Jinja2."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.env = Environment(
            loader=FileSystemLoader(str(base_dir)),
            autoescape=select_autoescape([]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_path: Path, parameters: Dict[str, Any]) -> str:
        rel = template_path.resolve().relative_to(self.base_dir.resolve())
        template = self.env.get_template(str(rel))
        return template.render(**parameters)
