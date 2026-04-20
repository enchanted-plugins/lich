---
description: Run Mantis's M1 + M2 static analysis on a hunk, file, or PR. Flags runtime-failure candidates for mantis-sandbox confirmation.
argument-hint: <hunk|file|pr> [path]
---

Run Mantis's static-analysis review on the specified scope. Delegates to the `mantis-review` skill.

Scope options:
- `hunk` — current file + cursor line range (interactive mode)
- `file <path>` — full file analysis
- `pr` — all changes in the current PR (via Hornet's change-classification data)

The review pipeline:
1. M1 Cousot Interval Propagation flags runtime-failure candidates (div-zero, null deref, OOB, overflow).
2. M2 Falleri Structural Diff isolates semantic edits from formatting churn.
3. Flagged sites queue for `mantis-sandbox` M5 confirmation.
4. `mantis-rubric` adds M7 judgment.
5. `mantis-verdict` composes the final DEPLOY/HOLD/FAIL.

Non-duplication: security-tagged findings (any CWE in Reaper's `vuln-detector/state/audit.jsonl`) are *not* re-scanned here. Mantis boosts attention weight on Reaper-flagged files but leaves CWE classification to Reaper.
