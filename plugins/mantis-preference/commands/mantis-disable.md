---
description: Permanently suppress a Mantis rule for the current developer. Writes plugins/mantis-preference/state/overrides.json with a 90-day re-prompt per the load-bearing M6 5% floor contract. Use when the user runs /mantis-disable <rule_id> and wants to opt a rule out beyond Bayesian accumulation.
argument-hint: <rule_id>
---

Permanently suppress the given Mantis rule for the current developer. Delegates to the `mantis-disable` skill (runbook at `plugins/mantis-preference/skills/mantis-disable/SKILL.md`).

Argument:
- `<rule_id>` — e.g. `PY-M1-001`, `mantis-python:unused-import`. Must be a known Mantis rule; unknown ids are rejected (no silent accept — F02 fabrication guard).

Invocation contract:

```
python plugins/mantis-preference/scripts/override.py \
  --dev "$MANTIS_DEV_ID" \
  --rule <rule_id> \
  disable
```

`MANTIS_DEV_ID` resolves per the skill's runbook: SHA256 of `git config user.email` (truncated to 12 hex chars) when inside a git repo, else `os.environ["USER"]`.

Contract this enforces (root `CLAUDE.md` § Behavioral contracts #4):
- One rejection signal does NOT kill a rule — M6's Thompson sampler has a 5% surfacing floor.
- Permanent suppression is the developer's *explicit* action — this command is the only path.
- The override expires after 90 days (quarterly re-prompt). Re-run the command to renew.

Output:
- `plugins/mantis-preference/state/overrides.json` gains one record: `{dev_id, rule_id, disabled_at, reprompt_at}`.
- Confirmation line with the rule id, dev id, and reprompt date.

Publishes `mantis.rule.disabled` on the enchanted-mcp event bus (Phase 2) with `{developer_id, rule_id, expiry_ts}`.
