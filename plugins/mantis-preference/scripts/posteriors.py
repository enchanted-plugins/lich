"""Beta-Binomial posteriors per (developer, rule).

Pseudocount prior Beta(1,1) encodes ignorance. 5% floor per CLAUDE.md contract §4.

The conjugacy is the load-bearing math: with Beta(1,1) prior and Bernoulli
observations (accept=success, reject=failure), the posterior after `a` accepts
and `r` rejects is Beta(1+a, 1+r). Thompson sampling draws one value from this
posterior per decision, giving exploration at high variance and exploitation at
low variance — no hand-tuned epsilon.

The 5% floor lives in `surfacing_probability`: any draw below 0.05 is clamped
UP (never silently floored to 0). A rule surviving 100 rejections still has a
5% chance of being surfaced. Permanent suppression requires an explicit
`/mantis-disable` — see override.py.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace


# Minimum surfacing probability per CLAUDE.md §4. Load-bearing constant; do
# NOT drop below 0.05 without a documented contract change.
SURFACING_FLOOR = 0.05


@dataclass(frozen=True)
class Posterior:
    """Beta-Binomial posterior for a (developer, rule) pair.

    alpha = accepts + 1, beta = rejects + 1 (Beta(1,1) uniform prior).
    """

    dev_id: str
    rule_id: str
    accepts: int = 0
    rejects: int = 0

    @property
    def alpha(self) -> float:
        return self.accepts + 1.0

    @property
    def beta(self) -> float:
        return self.rejects + 1.0


def mean(p: Posterior) -> float:
    """Posterior mean: alpha / (alpha + beta).

    Beta(1,1) → 0.5. One accept → 2/3. One reject → 1/3.
    """
    return p.alpha / (p.alpha + p.beta)


def thompson_sample(p: Posterior, rng: random.Random | None = None) -> float:
    """Draw one sample from Beta(alpha, beta).

    With no observations, Beta(1,1) is uniform on [0,1]. With many accepts,
    samples concentrate near 1. With many rejects, samples concentrate near 0.
    Variance shrinks with observations — the exploration-exploitation tradeoff
    is automatic.
    """
    rng = rng or random.Random()
    return rng.betavariate(p.alpha, p.beta)


def surfacing_probability(
    p: Posterior,
    floor: float = SURFACING_FLOOR,
    rng: random.Random | None = None,
) -> float:
    """Thompson-sampled surfacing probability, clamped to [floor, 1.0].

    The clamp is UP only: a raw sample of 0.01 returns `floor` (0.05), not 0.
    This enforces CLAUDE.md §4 — no rule dies by accumulated rejection alone.
    A raw sample of 0.9 is returned as 0.9. A raw sample of 1.01 (impossible
    from betavariate but defensive) returns 1.0.
    """
    raw = thompson_sample(p, rng=rng)
    if raw < floor:
        return floor
    if raw > 1.0:
        return 1.0
    return raw


def update(p: Posterior, accepted: bool) -> Posterior:
    """Return a new posterior with the observation applied.

    Posteriors are append-only — the old record is not mutated so call sites
    that hold a reference observe the pre-update state.
    """
    if accepted:
        return replace(p, accepts=p.accepts + 1)
    return replace(p, rejects=p.rejects + 1)
