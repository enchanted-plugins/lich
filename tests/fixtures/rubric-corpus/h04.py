"""Parity classification — tight pure functions.

Trivial arithmetic expressed as trivial code; type hints + one-line bodies.
"""

from __future__ import annotations

from typing import Iterable, Literal

Parity = Literal["even", "odd"]


def is_even(n: int) -> bool:
    return n % 2 == 0


def classify_number(n: int) -> Parity:
    return "even" if is_even(n) else "odd"


def classify_sequence(nums: Iterable[int]) -> list[Parity]:
    return [classify_number(n) for n in nums]
