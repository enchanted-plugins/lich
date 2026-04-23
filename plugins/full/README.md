# full

*Meta-plugin. One install pulls in all 7 Lich sub-plugins via dependency resolution.*

## Install

```bash
/plugin marketplace add enchanted-plugins/lich
/plugin install full@lich
```

Installs the complete Lich review pipeline:

| Sub-plugin | Engines | Role |
|-----------|---------|------|
| `lich-core` | M1, M2 | Static analysis substrate (Cousot Interval Propagation + Falleri Structural Diff) |
| `lich-sandbox` | M5 | Bounded Subprocess Dry-Run — confirms M1 flags with witness inputs (Unix-only) |
| `lich-preference` | M6 | Bayesian Preference Accumulation — per-developer Beta posteriors with Thompson sampling |
| `lich-rubric` | M7 | Zheng Pairwise Rubric Judgment — 5-axis LLM-as-judge with Kappa reliability |
| `lich-python` | — | Language adapter mapping ruff rules into M-engine outputs |
| `lich-typescript` | — | Language adapter mapping biome rules into M-engine outputs |
| `lich-verdict` | — | DEPLOY/HOLD/FAIL synthesizer, event emitter |

## Cherry-pick individual sub-plugins

If you only want a subset:

```bash
/plugin install lich-core@lich lich-sandbox@lich lich-verdict@lich
```

Minimum viable Lich install (no preference learning, no rubric judgment): `lich-core + lich-sandbox + lich-verdict`. This gives you the static→sandbox pipeline without personalization.

## Verify

```bash
/plugin list
```

Expected output: all 7 sub-plugins + `full` listed under the `lich` marketplace.

## Phase 2 additions (future)

The `full` meta will expand to include Phase 2 sub-plugins when they ship:
- `lich-property-graph` (M3 Yamaguchi Property-Graph Traversal)
- `lich-synthesis` (M4 Type-Reflected Invariant Synthesis)
- `lich-rust`, `lich-go`, `lich-java`, `lich-kotlin` (language adapters)
- `lich-clone-detect` (Schleimer Winnowing)
- `lich-separation-logic` (O'Hearn Bi-Abduction for JVM)
