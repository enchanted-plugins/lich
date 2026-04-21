from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Optional, Protocol, Sequence, TypeVar


class HasId(Protocol):
    id: int


T = TypeVar("T", bound=HasId)


@dataclass(frozen=True, slots=True)
class Average:
    mean: Decimal
    count: int

    @classmethod
    def of(cls, nums: Sequence[Decimal]) -> Optional["Average"]:
        if not nums:
            return None
        total = sum(nums, start=Decimal(0))
        return cls(mean=total / Decimal(len(nums)), count=len(nums))


def find_by_id(items: Sequence[T], target_id: int) -> Optional[T]:
    return next((it for it in items if it.id == target_id), None)


def parse_int_pair(s: str) -> Optional[tuple[int, int]]:
    parts = s.split(",", maxsplit=1)
    if len(parts) != 2:
        return None
    try:
        return int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        return None


def read_config(path: Path, max_bytes: int = 1 << 20) -> Optional[str]:
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > max_bytes:
        return None
    return path.read_text(encoding="utf-8")
