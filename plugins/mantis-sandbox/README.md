# mantis-sandbox

*M5 Bounded Subprocess Dry-Run. The sandboxed-confirmation layer of Mantis's static→dynamic review pipeline.*

## What it does

For each runtime-failure candidate flagged by M1 Cousot Interval Propagation (in `mantis-core`), `mantis-sandbox` synthesizes a concrete witness input (boundary values: `0`, `None`, `""`, `sys.maxsize`, etc.) and executes the containing function in a stdlib-only sandbox. The sandbox enforces five resource caps and a wall-clock alarm:

| Cap | Value | Why |
|-----|-------|-----|
| `RLIMIT_CPU` | 5 seconds | Infinite-loop defense |
| `RLIMIT_AS` | 512 MB | Address-space cap |
| `RLIMIT_NOFILE` | 16 | File-descriptor cap |
| `RLIMIT_FSIZE` | 10 MB | Per-file write cap |
| `signal.alarm` | 10 seconds | Wall-clock kill |

Plus: scrubbed environment (no `HTTP_PROXY`, `no_proxy=*`), per-run `tempfile.mkdtemp()` write-target deleted on exit.

Confirmed bugs are *facts*, not probabilities. A confirmed `ZeroDivisionError` with a concrete witness input is a hard FAIL trigger in Mantis's verdict composition, not a soft-weighted score.

## Platform support

**Unix only at launch.** Python's `resource` module is absent on Windows. On non-POSIX platforms, `mantis-sandbox` emits `{status: "platform-unsupported"}` and skips execution — never silently pretends M5 ran. Windows support via Job Objects backend is tracked for Phase 2.

## Non-duplication

- Does not re-scan for CWEs (Reaper R3's lane).
- Does not check change classification (Hornet V1/V2's lane).
- Does not emit verdicts (mantis-verdict's lane).
- Does not persist witness outputs — the temp-dir is ephemeral.

## Install

```bash
/plugin install mantis-sandbox@mantis
```

Requires `mantis-core` to emit flags. Install both or use `full`:

```bash
/plugin install full@mantis
```

## Skills

| Skill | Purpose |
|-------|---------|
| `mantis-sandbox` | Confirms mantis-core's flags by executing witness inputs in the bounded sandbox. Chained, not user-invoked. |

## State

| File | Purpose |
|------|---------|
| `state/run-log.jsonl` | Append-only record of every sandbox run — confirmed / timeout / sandbox-error / no-bug outcomes |

## Outcome classes

`mantis-sandbox` never collapses to binary success/failure. Every run records one of:

- `confirmed-bug` — witness reproduced a runtime failure. Hard FAIL trigger.
- `timeout-without-confirmation` — alarm fired before bug surfaced. HOLD trigger; could be unreachable after a hang or a separate infinite-loop bug.
- `sandbox-error` — infrastructure failure (cap enforcement, subprocess spawn). Infra bug, not a review finding.
- `input-synthesis-failed` — couldn't construct a type-valid witness. Reported honestly; not a pass.
- `no-bug-found` — all witnesses ran clean. Static flag still stands (M1 is sound-approximate), but no dynamic confirmation.

## Security

This plugin executes developer code. The five resource caps are the ACE-risk mitigation. Any relaxation requires a documented security review. See `../../CLAUDE.md` § Behavioral contract 2.

## Source

- Python stdlib `resource` + `signal` + `subprocess` + `tempfile`. No external deps.
- Novel composition for code review: static-suspicion → sandboxed-confirmation pipeline. No existing reviewer ships this at zero-dep plugin weight.
