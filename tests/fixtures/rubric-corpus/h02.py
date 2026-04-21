"""Read and write key=value config files.

Missing files are a distinct result from malformed lines; caller sees both.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParseResult:
    values: dict[str, str]
    skipped_lines: tuple[int, ...]


def read_config(path: Path) -> ParseResult:
    """Parse key=value lines; record the line numbers of malformed entries."""
    values: dict[str, str] = {}
    skipped: list[int] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            skipped.append(lineno)
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return ParseResult(values=values, skipped_lines=tuple(skipped))


def write_config(path: Path, cfg: dict[str, str]) -> None:
    path.write_text("".join(f"{k}={v}\n" for k, v in cfg.items()), encoding="utf-8")
