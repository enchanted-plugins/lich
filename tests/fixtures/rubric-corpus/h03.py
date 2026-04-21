"""File-backed counter with an injectable storage boundary.

The storage protocol separates persistence from arithmetic, so the counter
is unit-testable with an in-memory fake.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class CounterStore(Protocol):
    def read(self) -> int: ...
    def write(self, value: int) -> None: ...


class FileStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> int:
        try:
            return int(self._path.read_text(encoding="utf-8").strip() or "0")
        except FileNotFoundError:
            return 0

    def write(self, value: int) -> None:
        self._path.write_text(str(value), encoding="utf-8")


class Counter:
    def __init__(self, store: CounterStore) -> None:
        self._store = store
        self._value = store.read()

    def inc(self) -> int:
        self._value += 1
        self._store.write(self._value)
        return self._value

    def reset(self) -> None:
        self._value = 0
        self._store.write(0)
