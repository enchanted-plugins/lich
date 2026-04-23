"""Override: permanent rule suppression via explicit `/lich-disable`.

Per CLAUDE.md §4, accumulated rejections CANNOT silently zero out a rule.
The developer's explicit action goes here, and it auto-expires after 90 days
(quarterly re-prompt) so a one-off context isn't enshrined forever.

State shape (overrides.json):
    [
        {
            "dev_id": "...",
            "rule_id": "...",
            "disabled_at": "2026-04-20T...Z",
            "reprompt_at": "2026-07-19T...Z"
        }
    ]

CLI: handler for the `/lich-disable` skill invocation.
    python override.py --dev DEV --rule RULE disable
    python override.py --dev DEV --rule RULE check
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


_HERE = Path(__file__).resolve().parent
# plugins/lich-preference/scripts/ -> repo root via parents[2].
# Matches sandbox.py / compose.py idiom (parents[3] would overshoot).
_REPO_ROOT = _HERE.parents[2]
_DEFAULT_STATE = (
    _REPO_ROOT / "plugins" / "lich-preference" / "state" / "overrides.json"
)

# Quarterly re-prompt per CLAUDE.md §4.
REPROMPT_DAYS = 90


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _parse_iso(s: str) -> datetime:
    # Accept trailing Z or offset
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _load(path: Path | None = None) -> list[dict]:
    path = path or _DEFAULT_STATE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []


def _save(path: Path | None, entries: list[dict]) -> None:
    path = path or _DEFAULT_STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _find(entries: list[dict], dev_id: str, rule_id: str) -> dict | None:
    for e in entries:
        if e.get("dev_id") == dev_id and e.get("rule_id") == rule_id:
            return e
    return None


def disable(dev_id: str, rule_id: str, path: Path | None = None) -> dict:
    """Add or refresh an override entry. Returns the stored entry."""
    entries = _load(path)
    now = _now()
    reprompt = now + timedelta(days=REPROMPT_DAYS)
    entry = _find(entries, dev_id, rule_id)
    if entry is None:
        entry = {"dev_id": dev_id, "rule_id": rule_id}
        entries.append(entry)
    entry["disabled_at"] = _iso(now)
    entry["reprompt_at"] = _iso(reprompt)
    _save(path, entries)

    # Advisory event-bus publish. Brand invariant #7 — observability,
    # never load-bearing; any failure is swallowed silently. We walk up
    # looking for CLAUDE.md rather than relying on `parents[N]` arithmetic
    # so the shim is robust against path-depth surprises.
    try:
        import sys as _sys
        _p = Path(__file__).resolve()
        for _parent in _p.parents:
            if (_parent / "CLAUDE.md").exists() and \
               (_parent / "shared").is_dir():
                _shared = _parent / "shared"
                if str(_shared) not in _sys.path:
                    _sys.path.insert(0, str(_shared))
                break
        from events.bus import publish as _publish  # type: ignore
        _publish("lich.rule.disabled", {
            "dev_id": dev_id,
            "rule_id": rule_id,
            "disabled_at": entry["disabled_at"],
            "reprompt_at": entry["reprompt_at"],
        }, source="lich-preference")
    except Exception:
        pass

    return entry


def is_disabled(dev_id: str, rule_id: str, path: Path | None = None) -> bool:
    entry = _find(_load(path), dev_id, rule_id)
    return entry is not None


def due_for_reprompt(
    dev_id: str, rule_id: str, path: Path | None = None
) -> bool:
    """True if the override exists and reprompt_at has passed."""
    entry = _find(_load(path), dev_id, rule_id)
    if entry is None:
        return False
    try:
        return _parse_iso(entry["reprompt_at"]) < _now()
    except (KeyError, ValueError):
        return False


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Permanent rule override handler (/lich-disable)."
    )
    parser.add_argument("--dev", required=True)
    parser.add_argument("--rule", required=True)
    parser.add_argument("action", choices=["disable", "check"])
    parser.add_argument("--state", default=None)
    args = parser.parse_args(argv)

    state_path = Path(args.state) if args.state else None
    if args.action == "disable":
        entry = disable(args.dev, args.rule, state_path)
        print(json.dumps(entry, indent=2))
        return 0
    print(
        json.dumps(
            {
                "dev_id": args.dev,
                "rule_id": args.rule,
                "disabled": is_disabled(args.dev, args.rule, state_path),
                "due_for_reprompt": due_for_reprompt(
                    args.dev, args.rule, state_path
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(_main())
