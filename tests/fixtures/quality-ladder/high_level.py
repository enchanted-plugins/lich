from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence


@dataclass(frozen=True)
class User:
    id: int
    name: str


def average(nums: Sequence[float]) -> Optional[float]:
    if not nums:
        return None
    return sum(nums) / len(nums)


def find_user(users: Sequence[User], uid: int) -> Optional[User]:
    return next((u for u in users if u.id == uid), None)


def parse_pair(s: str) -> Optional[tuple[int, int]]:
    parts = s.split(",", maxsplit=1)
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def read_config(path: Path) -> str:
    return path.read_text(encoding="utf-8")
