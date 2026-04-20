# mantis-typescript

*TypeScript / JavaScript language adapter for Mantis. Maps biome rule IDs into M-engine outputs.*

## What it does

Activates on `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs` files. Invocation priority:

1. **biome** (if installed) → `biome check --json` → parse findings.
2. **tsc --noEmit** fallback (if TypeScript is in the project's devDeps) → parse diagnostic output.
3. **Regex fallback** (last resort, ~20 rules) → if neither biome nor tsc is available; flags `substrate: fallback-regex` honestly.

Maps each finding to an M-engine category via `config/biome-rule-map.json`:

| Biome category | Mantis M-engine route |
|----------------|----------------------|
| correctness/* | M1 runtime-failure candidate |
| style/* | M7 rubric — Idiom-fit axis |
| complexity/* | M7 rubric — Simplicity axis |
| a11y/* | M7 rubric — Clarity axis |
| suspicious/* (security-framed) | **Skip** — Reaper R3 owns |

## Non-duplication

- Never maps security rules (Reaper R3 overlap).
- Never runs with `biome check --apply` — Mantis is advisory.
- Never replaces biome — adapter pattern.

## Launch-to-full coverage

- Launch: ~80 of biome's ~423 rules mapped.
- Phase 2: coverage expands based on real review data.

## Install

```bash
/plugin install mantis-typescript@mantis
```

Requires mantis-core. Optional: `biome` or `typescript` installed in the developer's repo for richer output.

## State

| File | Purpose |
|------|---------|
| `config/biome-rule-map.json` | Biome rule ID → M-engine category mapping (ship-time, committed) |

## Source

- [biome (biomejs)](https://github.com/biomejs/biome) — Rust-rewritten JS/TS linter + formatter.
- [biome rules index](https://biomejs.dev/linter/rules/) — all ~423 rules with categories.
