# RFC 0001 — Rule-Map Schema v1.1

- **Status:** Draft
- **Authors:** enchanted-plugins
- **Date:** 2026-04-21
- **Targets:** `shared/rules/_schema.json`

## Summary

Rule-map schema v1.1 adds one optional top-level field — `cross_references` — so a rule-map can declare that a slice of its rule-ID surface delegates routing to another rule-map's adapter pipeline. The change is strictly additive: every v1.0 file continues to parse. We deliberately **do not** add a seventh `posture_defer_to_hydra` bucket.

## Motivation

The `lich-registry-research` cron agent's 2026-04-21 report (`shared/rules/proposed/REPORT.md` § Schema gaps) surfaced two concrete cases the v1.0 schema handles only in prose:

1. **Pass-through linters.** `hadolint` embeds ShellCheck and emits `SC*` IDs alongside its own `DL*` IDs; `actionlint` embeds `pyflakes` + `shellcheck`. Today the rule-map has no machine-readable way to say *"rules matching `SC*` route via `languages/shell.json`"* — it lives in a free-text `note`, invisible to the M1 adapter.
2. **Posture vs. security.** `hadolint` DL3002 (final user is root) and DL3004 (sudo use) are adjacent to CWE-250/269 but are *posture* signals, not concrete CWE claims. The v1.0 schema has one defer bucket (`security_defer_to_hydra`), and that is where they land.

## Proposal

### Add `cross_references` (optional, top-level)

```jsonc
"cross_references": [
  { "pattern": "SC*", "delegate_to": "languages/shell" }
]
```

Semantics: a rule_id matching `pattern` (glob syntax, compiled by the adapter) routes its M1 flag through `delegate_to`'s adapter pipeline instead of the owning rule-map's. Missing `delegate_to` targets are a load-time error.

- **Non-breaking:** absent field means "no cross-routing" — identical to v1.0 behavior.
- **Minimal scope:** `cross_references` is a routing hint, not a merge. The delegating map still owns `coverage_stats` and the `categories` scaffold.

### Do NOT add `posture_defer_to_hydra`

The cron report floated a seventh bucket for posture-only signals. After review, **we are rejecting it for v1.1**:

- Hydra R3 owns the security/posture lane end-to-end. Splitting posture out of `security_defer_to_hydra` fragments the single-source-of-truth contract Lich has with Hydra (`CLAUDE.md § behavioral contracts 1`).
- The current routing (posture → `security_defer_to_hydra` with `never_mapped: true`) loses no information: Hydra decides whether to surface or ignore.
- Revisit only if Hydra grows a **distinct** posture surface with its own SLA/severity vocabulary. Until then, one defer bucket is the honest contract.

## Migration

- v1.0 rule-maps parse unchanged under v1.1 (additive field).
- `_schema.json` gains a descriptive note near `schema_version`. The `enum` remains `["1.0"]` until v1.1 ships with a validator; no existing files are renamed or bumped.
- Future PR will add `"1.1"` to the `enum`, add the `cross_references` property definition, and bump one language map as the reference implementation.

## Non-goals

- No rename of existing buckets (`correctness_m1`, `idiom_m7`, `complexity_m7`, `naming_m7`, `testability_m7`, `security_defer_to_hydra`).
- No change to the Hydra non-duplication contract — security-framed rules still route to `security_defer_to_hydra` with `never_mapped: true`.
- No new top-level required fields.
- No style sub-bucket (cron report gap #3 deferred to a future RFC).

## References

- Cron research report: [`shared/rules/proposed/REPORT.md`](../../shared/rules/proposed/REPORT.md) § Schema gaps
- Behavioral contract: [`CLAUDE.md`](../../CLAUDE.md) § behavioral contracts 1 (Hydra non-duplication)
- Current schema: [`shared/rules/_schema.json`](../../shared/rules/_schema.json)
- Reference rule-map: [`shared/rules/languages/python.json`](../../shared/rules/languages/python.json)
