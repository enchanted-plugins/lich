"""Reader: per-flag M6 assessment + aggregate evaluate() for the verdict bar.

Consumers (lich-verdict.rules.evaluate_m6) pass in a list of M1 flags plus
the developer id; we look up each (dev, rule) posterior, Thompson-sample, and
classify. Overrides (explicit `/lich-disable`) suppress surfacing entirely —
distinct from posterior-driven de-prioritization, which always keeps the 5%
floor.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

try:
    from .observer import get_posterior, load_state
    from .override import is_disabled
    from .posteriors import mean, surfacing_probability
except ImportError:  # direct invocation / sys.path insertion from rules.py
    from observer import get_posterior, load_state  # type: ignore
    from override import is_disabled  # type: ignore
    from posteriors import mean, surfacing_probability  # type: ignore


# Classification thresholds — from CLAUDE.md Verdict bar M6 columns.
ACCEPT_MEAN = 0.5
BORDERLINE_MEAN = 0.3
SURFACE_SAMPLE = 0.5  # Thompson sample >= this → surface this round


def _rule_id(flag: dict) -> str:
    """Extract a rule id from a flag, tolerating several common shapes."""
    return (
        flag.get("rule_id")
        or flag.get("rule")
        or flag.get("id")
        or "unknown-rule"
    )


def per_flag_assessment(
    flags: list[dict],
    dev_id: str,
    state_path: Optional[Path] = None,
    overrides_path: Optional[Path] = None,
    rng: Optional[random.Random] = None,
) -> list[dict]:
    """For each flag, classify its preference-adjusted surfacing decision.

    Returns one dict per flag with:
        rule_id, posterior_mean, sample, surfacing_probability,
        would_surface, classification, disabled.
    """
    rng = rng or random.Random()
    out: list[dict] = []
    for flag in flags:
        rule_id = _rule_id(flag)
        disabled = is_disabled(dev_id, rule_id, overrides_path)
        p = get_posterior(dev_id, rule_id, state_path)
        m = mean(p)
        surf = surfacing_probability(p, rng=rng)
        would_surface = (not disabled) and (surf >= SURFACE_SAMPLE)
        if m >= ACCEPT_MEAN:
            classification = "likely-accepted"
        elif m >= BORDERLINE_MEAN:
            classification = "borderline"
        else:
            classification = "likely-rejected"
        out.append(
            {
                "rule_id": rule_id,
                "posterior_mean": m,
                "sample": surf,
                "surfacing_probability": surf,
                "would_surface": would_surface,
                "classification": classification,
                "disabled": disabled,
            }
        )
    return out


def evaluate(
    flags: list[dict],
    dev_id: str,
    state_path: Optional[Path] = None,
    overrides_path: Optional[Path] = None,
    rng: Optional[random.Random] = None,
) -> dict:
    """Aggregate assessment for verdict-bar consumption.

    Returns:
        {
            "surfaced_count": N,
            "accept_majority_count": N (mean >= 0.5),
            "borderline_count": N (0.3 <= mean < 0.5),
            "reject_majority_count": N (mean < 0.3),
            "disabled_count": N,
            "assessments": [...],  # full per-flag detail
        }
    """
    assessments = per_flag_assessment(
        flags, dev_id, state_path, overrides_path, rng
    )
    surfaced = [a for a in assessments if a["would_surface"]]
    accept_majority = sum(1 for a in surfaced if a["classification"] == "likely-accepted")
    borderline = sum(1 for a in surfaced if a["classification"] == "borderline")
    reject_majority = sum(1 for a in surfaced if a["classification"] == "likely-rejected")
    disabled = sum(1 for a in assessments if a["disabled"])
    return {
        "surfaced_count": len(surfaced),
        "accept_majority_count": accept_majority,
        "borderline_count": borderline,
        "reject_majority_count": reject_majority,
        "disabled_count": disabled,
        "assessments": assessments,
    }


def latest_for_developer(
    dev_id: str, state_path: Optional[Path] = None
) -> dict[str, dict]:
    """Return {rule_id -> {accepts, rejects, mean}} for this developer."""
    state = load_state(state_path)
    out: dict[str, dict] = {}
    prefix = f"{dev_id}::"
    for key, p in state.items():
        if not key.startswith(prefix):
            continue
        out[p.rule_id] = {
            "accepts": p.accepts,
            "rejects": p.rejects,
            "mean": mean(p),
        }
    return out
