---
name: mantis-review
description: >
  Runs M1 Cousot Interval Propagation and M2 Falleri Structural Diff on a
  code scope, flags runtime-failure candidates (div-zero, null deref, OOB,
  overflow, resource leak), and hands the flagged sites to mantis-sandbox
  for M5 confirmation. Use when: the user runs /mantis-review on a hunk /
  file / PR, or the PostToolUse hook fires on Write/Edit/MultiEdit. Do not
  use for: security-taint review (Reaper R3 owns that), change
  classification (Hornet V1/V2 owns that), or rubric-style judgment
  (mantis-rubric skill owns that).
model: sonnet
tools: [Read, Grep, Glob]
---

# mantis-review

## Preconditions

- A `mantis-core` sub-plugin state dir exists at `plugins/mantis-core/state/`.
- Target code parses under the detected language's substrate (Python `ast`, TypeScript `tsc --generateTrace`). If parsing fails, emit `substrate-parse-failed` and skip — do not fabricate flags.
- Hornet's `change-tracker/state/audit.jsonl` is optionally present. If absent, Mantis runs on the full file instead of Hornet-flagged hunks.

## Inputs

- **Slash command**: `/mantis-review <scope>` where scope is `hunk` (current file + line range), `file` (full file path), or `pr` (all changes in the PR).
- **Hook payload**: PostToolUse event with `tool`, `file_path`, `old_string`, `new_string`.

## Steps

1. **Parse the target.** Use `ast.parse` for Python, subprocess `tsc --noEmit --generateTrace` for TypeScript. On parse failure, emit `substrate-parse-failed` and return empty flags.
2. **Run M1 Cousot Interval Propagation.** Walk the AST applying interval + nullability + container-shape abstract domains. Threshold-widen at N=3 iterations with language-aware bounds (`{0, 1, -1, sys.maxsize}` for Python ints). Emit per-site flags: `{file, line, variable, abstract_value, failure_class, severity}`.
3. **Run M2 Falleri Structural Diff** *if comparing two versions*. Use conservative GumTree parameters (`min_height=3`, `min_dice=0.6`, `min_similarity=0.7`). Time budget 2 seconds per file; on timeout, fall back to unified diff and flag `structural-diff-timeout`.
4. **Read Reaper's vuln-detector audit.jsonl.** If a CRITICAL or HIGH CWE finding exists on the target file, boost the review-attention weight for M6's prioritization and annotate M7's rubric input with "Security context: Reaper flagged {cwe} {severity}". Never re-scan for the CWE itself.
5. **Emit flagged sites.** Write to `plugins/mantis-core/state/review-flags.jsonl` for mantis-sandbox to pick up. Fields: `{ts, file, line, failure_class, severity, M1_confidence, needs_M5_confirmation}`.

## Outputs

- `plugins/mantis-core/state/review-flags.jsonl` — append-only flag records.
- stderr: short summary of M1 findings count, M2 edits detected, Reaper context applied.
- Return value to parent: a JSON block `{flags: [...], M2_edits: N, duration_ms: X}`.

## Handoff

Next skill in the chain: **mantis-sandbox** (SKILL at `plugins/mantis-sandbox/skills/mantis-sandbox/SKILL.md`) — confirms each flagged site via bounded subprocess dry-run.

After both skills run, **mantis-verdict** composes the final DEPLOY/HOLD/FAIL verdict.

## Failure modes

When this skill fails, log to `state/learnings.json` with one of the codes from `@shared/conduct/failure-modes.md`:

- **F02 fabrication** — if M1 reports a flag the AST walk doesn't actually produce (never do this; soundness is the brand)
- **F04 task drift** — if the skill strays into security-taint detection (Reaper's lane)
- **F13 distractor pollution** — if M2 emits > 20 edits on a small diff; revert to conservative parameters
- **F14 version drift** — if the TypeScript substrate uses an unsupported `tsc` version; emit a compatibility warning
