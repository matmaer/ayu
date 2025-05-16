from pathlib import Path
from dataclasses import dataclass


@dataclass
class Plugin:
    name: str
    version: str
    is_installed: bool
    options: list[str]


def build_command(is_tool: bool, plugins: dict[str, list[str]], test_path: Path) -> str:
    return ""
