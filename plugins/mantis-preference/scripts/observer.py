"""Observer: persists (dev_id, rule_id) -> Posterior to learnings.json.

The state file is a single JSON object keyed on "dev_id::rule_id". Chosen over
JSONL for M6 because the posterior for a pair is a running total, not an
event stream — the entire state fits in memory and is small enough to
rewrite atomically on every update.

For audit history of individual accept/reject events, see the PostToolUse
hook's dispatch logs (out of scope for this module).

CLI:
    python observer.py --dev DEV --rule RULE --accept
    python observer.py --dev DEV --rule RULE --reject
    python observer.py --dev DEV --rule RULE --show
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .posteriors import Posterior, mean, update
except ImportError:  # CLI / direct invocation
    from posteriors import Posterior, mean, update  # type: ignore

# Repo-root sys.path shim for shared/learnings.py (advisory Gauss log).
_SHARED = Path(__file__).resolve().parents[3] / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
try:
    import learnings as _learnings  # type: ignore
except Exception:  # pragma: no cover — advisory
    _learnings = None


_LOW_THRESHOLD = 0.2
_HIGH_THRESHOLD = 0.8


def _crossed_threshold(old_mean: float, new_mean: float) -> str | None:
    """Return a short label if new_mean crossed a threshold relative to old.

    Thresholds: 0.2 and 0.8. Ties break toward the "crossed" side so a
    single equal observation still surfaces the event.
    """
    if old_mean < _HIGH_THRESHOLD <= new_mean:
        return "above-0.8"
    if old_mean >= _HIGH_THRESHOLD > new_mean:
        return "below-0.8"
    if old_mean > _LOW_THRESHOLD >= new_mean:
        return "below-0.2"
    if old_mean <= _LOW_THRESHOLD < new_mean:
        return "above-0.2"
    return None


_HERE = Path(__file__).resolve().parent
# scripts/ -> mantis-preference/ -> plugins/ -> repo root = parents[2].
# (Matches sandbox.py / compose.py / override.py idiom; parents[3] overshoots.)
_REPO_ROOT = _HERE.parents[2]
_DEFAULT_STATE = (
    _REPO_ROOT / "plugins" / "mantis-preference" / "state" / "learnings.json"
)
_DEFAULT_FLAGS = (
    _REPO_ROOT / "plugins" / "mantis-core" / "state" / "review-flags.jsonl"
)
_DEFAULT_OVERRIDES = (
    _REPO_ROOT / "plugins" / "mantis-preference" / "state" / "overrides.json"
)
_DEFAULT_SURFACED = (
    _REPO_ROOT / "plugins" / "mantis-preference" / "state" / "surfaced.jsonl"
)


def _key(dev_id: str, rule_id: str) -> str:
    return f"{dev_id}::{rule_id}"


def _posterior_to_dict(p: Posterior) -> dict:
    return {
        "dev_id": p.dev_id,
        "rule_id": p.rule_id,
        "accepts": p.accepts,
        "rejects": p.rejects,
    }


def _dict_to_posterior(d: dict) -> Posterior:
    return Posterior(
        dev_id=d["dev_id"],
        rule_id=d["rule_id"],
        accepts=int(d.get("accepts", 0)),
        rejects=int(d.get("rejects", 0)),
    )


def load_state(path: Path | None = None) -> dict[str, Posterior]:
    """Read learnings.json into {key -> Posterior}. Missing file → {}."""
    path = path or _DEFAULT_STATE
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Corrupt state: treat as empty. Re-running observations will rebuild.
        return {}
    out: dict[str, Posterior] = {}
    for k, v in raw.items():
        try:
            out[k] = _dict_to_posterior(v)
        except (KeyError, TypeError, ValueError):
            continue
    return out


def save_state(path: Path | None, state: dict[str, Posterior]) -> None:
    """Pretty-print JSON for human review. Creates parent dirs if needed."""
    path = path or _DEFAULT_STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = {k: _posterior_to_dict(p) for k, p in state.items()}
    path.write_text(
        json.dumps(serializable, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def get_posterior(
    dev_id: str, rule_id: str, path: Path | None = None
) -> Posterior:
    """Return existing posterior or fresh Beta(1,1)."""
    state = load_state(path)
    return state.get(_key(dev_id, rule_id), Posterior(dev_id, rule_id))


def observe(
    dev_id: str,
    rule_id: str,
    accepted: bool,
    path: Path | None = None,
) -> Posterior:
    """Update the posterior for (dev_id, rule_id) and persist."""
    state = load_state(path)
    key = _key(dev_id, rule_id)
    existing = state.get(key, Posterior(dev_id, rule_id))
    new = update(existing, accepted)
    state[key] = new
    save_state(path, state)

    # Gauss Accumulation — note only when a posterior crosses a threshold.
    if _learnings is not None:
        try:
            crossed = _crossed_threshold(mean(existing), mean(new))
            if crossed is not None:
                _learnings.safe_emit(
                    plugin="mantis-preference",
                    code="F05",
                    axis=rule_id,
                    hypothesis=f"rule {rule_id} posterior crossed {crossed}",
                    outcome=f"dev={dev_id} mean={round(mean(new), 4)} "
                            f"accepts={new.accepts} rejects={new.rejects}",
                    counter="monitor for drift",
                )
        except Exception:
            pass

    return new


def scan_flags(
    dev_id: str,
    flags_path: Path | None = None,
    overrides_path: Path | None = None,
    state_path: Path | None = None,
    surfaced_path: Path | None = None,
) -> dict:
    """Consume review-flags.jsonl, decide per-rule surfacing via Thompson
    sampling (respecting the 5% floor and explicit overrides), and append
    one snapshot line to surfaced.jsonl.

    Called from the PostToolUse hook after M1/M5 have written their state.
    Zero external deps; fail-open on missing inputs.
    """
    flags_path = flags_path or _DEFAULT_FLAGS
    overrides_path = overrides_path or _DEFAULT_OVERRIDES
    surfaced_path = surfaced_path or _DEFAULT_SURFACED

    # reader.per_flag_assessment lives alongside observer; import lazily to
    # avoid a circular-import surprise when observer is imported as a module
    # by reader (which imports get_posterior + load_state from us).
    try:
        from .reader import per_flag_assessment
    except ImportError:  # direct invocation
        from reader import per_flag_assessment  # type: ignore

    flags: list[dict] = []
    if flags_path.exists():
        with flags_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    flags.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    assessments = per_flag_assessment(
        flags, dev_id, state_path=state_path, overrides_path=overrides_path
    )

    surfaced = [a for a in assessments if a.get("would_surface")]
    suppressed = [a for a in assessments if not a.get("would_surface")]

    from datetime import datetime, timezone
    snapshot = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dev_id": dev_id,
        "flags_in": len(flags),
        "surfaced_count": len(surfaced),
        "suppressed_count": len(suppressed),
        "surfaced_rule_ids": sorted({a["rule_id"] for a in surfaced}),
        "suppressed_rule_ids": sorted({a["rule_id"] for a in suppressed}),
    }

    surfaced_path.parent.mkdir(parents=True, exist_ok=True)
    with surfaced_path.open("a", encoding="utf-8") as w:
        w.write(json.dumps(snapshot) + "\n")

    return snapshot


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingest a developer accept/reject signal into the M6 posterior."
    )
    parser.add_argument("--dev", default=None, help="Developer id")
    parser.add_argument("--rule", default=None, help="Rule id")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--accept", action="store_true")
    group.add_argument("--reject", action="store_true")
    group.add_argument("--show", action="store_true", help="Just print the posterior")
    group.add_argument(
        "--scan-flags",
        action="store_true",
        help="Scan review-flags.jsonl and append a surfacing snapshot.",
    )
    parser.add_argument("--state", default=None, help="Override state path")
    parser.add_argument("--flags", default=None, help="Override flags path (scan only)")
    parser.add_argument(
        "--overrides", default=None, help="Override overrides.json path (scan only)"
    )
    parser.add_argument(
        "--surfaced", default=None, help="Override surfaced.jsonl path (scan only)"
    )

    args = parser.parse_args(argv)
    state_path = Path(args.state) if args.state else None

    if args.scan_flags:
        # Hook-mode: dev is optional (default = os login); --rule is ignored.
        import os
        dev_id = args.dev or os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
        flags_path = Path(args.flags) if args.flags else None
        overrides_path = Path(args.overrides) if args.overrides else None
        surfaced_path = Path(args.surfaced) if args.surfaced else None
        snap = scan_flags(
            dev_id,
            flags_path=flags_path,
            overrides_path=overrides_path,
            state_path=state_path,
            surfaced_path=surfaced_path,
        )
        print(json.dumps(snap))
        return 0

    if not args.dev or not args.rule:
        parser.error("--dev and --rule are required for --accept/--reject/--show")

    if args.show:
        p = get_posterior(args.dev, args.rule, state_path)
        print(json.dumps({**_posterior_to_dict(p), "mean": round(mean(p), 4)}, indent=2))
        return 0

    accepted = args.accept
    p = observe(args.dev, args.rule, accepted, state_path)
    print(json.dumps({**_posterior_to_dict(p), "mean": round(mean(p), 4)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
