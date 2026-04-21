"""Group and flatten iterables.

Pure, idiomatic, small-surface helpers with no I/O and no hidden state.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import chain
from typing import Iterable, TypeVar

K = TypeVar("K")
V = TypeVar("V")


def group_pairs(pairs: Iterable[tuple[K, V]]) -> dict[K, list[V]]:
    """Collect (key, value) pairs into lists keyed by key, preserving order."""
    groups: dict[K, list[V]] = defaultdict(list)
    for key, value in pairs:
        groups[key].append(value)
    return dict(groups)


def flatten(nested: Iterable[Iterable[V]]) -> list[V]:
    """Flatten one level of nesting via itertools.chain.from_iterable."""
    return list(chain.from_iterable(nested))
