# Mantis — Code review for AI-assisted development

*An @enchanted-plugins product — algorithm-driven, agent-managed, self-learning.*

Answers *"Is this code good?"* via a five-engine pipeline: static suspicion (M1 Cousot Interval Propagation), structural change comprehension (M2 Falleri Structural Diff), sandboxed confirmation (M5 Bounded Subprocess Dry-Run), Bayesian preference accumulation (M6), and LLM rubric judgment (M7 Zheng Pairwise Rubric). Catches runtime failures that pass compile time; defers security-lane findings to Reaper and change-classification to Hornet.

## Origin

Mantis, after the **Mantis Lords of Hollow Knight** — gate-reviewers who judge worthiness through trial before letting you pass. Every PR is a supplicant at the gate; every engine is a test the code must survive. Joins Hornet (change comprehension) and Weaver (git flow) in the Hollow Knight cluster — three HK entities for three related dev-surface plugins is intentional brand signal.

The question this plugin answers: *Is this code good?*

## Problem

AI-assisted development ships bugs humans wouldn't. The two dominant failure modes in 2026:
1. **Runtime failures that pass compile time.** `x / n` type-checks in every language; `n = 0` crashes at runtime. Static type systems don't catch it; neither does `cargo check` / `tsc`. Humans catch it on review, LLMs miss it.
2. **Reviewer fatigue on noisy signals.** GitHub Copilot, Cursor, and Qodo ship thousands of style suggestions, all at equal weight. Developers accept/reject without the tool learning. Over time, the signal-to-noise collapses and the reviewer disables the tool.

Mantis addresses both: a static→sandboxed pipeline (M1 flags, M5 confirms) catches the first; per-developer Bayesian preference accumulation (M6) addresses the second. No existing reviewer ships either at zero-external-dep weight; both together is genuinely novel.

## Architecture

```
                  ┌─────────────────────────────────┐
                  │           Mantis                │
                  │    Phase 3 · Plugin #6          │
                  │   "Is this code good?"          │
                  └──────────────┬──────────────────┘
                                 │
    ┌────────┬────────┬──────────┼──────────┬────────┬────────┐
    │        │        │          │          │        │        │
┌───▼────┐ ┌─▼──────┐ ┌▼─────────▼┐ ┌───────▼┐ ┌─────▼──┐ ┌───▼────┐
│mantis- │ │mantis- │ │  mantis-  │ │mantis- │ │mantis- │ │mantis- │
│ core   │ │sandbox │ │preference │ │rubric  │ │python  │ │type-   │
│(M1+M2) │ │ (M5)   │ │  (M6)     │ │ (M7)   │ │(adapt) │ │script  │
└────────┘ └────────┘ └───────────┘ └────────┘ └────────┘ └────────┘
                                 │
                         ┌───────▼────────┐
                         │ mantis-verdict │
                         │ (DEPLOY/HOLD/  │
                         │  FAIL router)  │
                         └────────────────┘
```

Architecture diagrams in [docs/architecture/](docs/architecture/) are auto-generated from source-of-truth (`plugin.json`, `hooks.json`, `SKILL.md` frontmatter) by `docs/architecture/generate.py`. Never hand-edited. The full synthesized architecture is at [docs/architecture/mantis-architecture.md](docs/architecture/mantis-architecture.md).

## Named algorithms

Every engine is backed by a formal algorithm. Full derivations in [docs/science/README.md](docs/science/README.md).

$$\text{M1: } \text{Int}_v = [\text{lo}, \text{hi}] \sqcup \text{Null}(v) \sqcup \text{Shape}(v), \quad \text{widen after } N=3 \text{ iterations}$$

$$\text{M6: } P(\text{surface rule } r \mid \text{dev } d) = \max\left(0.05,\ \theta \sim \text{Beta}(\alpha_{d,r},\ \beta_{d,r})\right)$$

| ID | Name | Plugin | Algorithm |
|----|------|--------|-----------|
| M1 | Cousot Interval Propagation | mantis-core | Abstract interpretation over interval + nullability + container-shape lattices with threshold widening |
| M2 | Falleri Structural Diff | mantis-core | GumTree two-phase AST matching (top-down hash + bottom-up Dice) |
| M5 | Bounded Subprocess Dry-Run | mantis-sandbox | Stdlib `resource.setrlimit` + `signal.alarm` + subprocess sandbox (Unix-only) |
| M6 | Bayesian Preference Accumulation | mantis-preference | Beta-Binomial Thompson sampling per (developer, rule) with 5% minimum floor |
| M7 | Zheng Pairwise Rubric Judgment | mantis-rubric | 5-axis rubric + position-swap debiasing + Cohen's Kappa reliability |

**Defining engine:** M5 Bounded Subprocess Dry-Run — the static-suspicion → sandboxed-confirmation pipeline is the novel moat no existing reviewer ships at zero-external-dep weight.

Phase 2 adds M3 Yamaguchi Property-Graph Traversal, M4 Type-Reflected Invariant Synthesis, Schleimer Winnowing Clone Detection, O'Hearn Separation-Logic Bi-Abduction, and Cohort Similarity Borrowing.

## Install

```bash
/plugin marketplace add enchanted-plugins/mantis
/plugin install full@mantis
```

To cherry-pick a single sub-plugin:

```bash
/plugin install mantis-core@mantis
```

Verify with `/plugin list`.

## Plugins

| Command | Function | Agent tier |
|---------|----------|------------|
| `/mantis-review <scope>` | On-demand deep review aggregating M1-M7 | Sonnet |
| `/mantis-explain <finding_id>` | Walk through why M1/M5/M7 flagged a specific finding | Sonnet |
| `/mantis-disable <rule_id>` | Permanent rule suppression with quarterly auto-reprompt | Haiku |

## Comparison

Honest comparison against adjacent tools. Marks `✓` only where the feature is present and production-ready.

| Feature | Mantis | GitHub Copilot | Cursor | Qodo Merge |
|---------|--------|----------------|--------|------------|
| Catches runtime-only bugs via sandboxed confirmation | ✓ | — | — | — |
| Per-developer Bayesian preference posterior | ✓ | — | — | — |
| Inter-judge reliability (Cohen's Kappa) reported | ✓ | — | — | — |
| Zero external runtime deps | ✓ | — | — | — |
| Markdown-file rule customization | ✓ | ✓ | ✓ | ✓ |
| Auto-generated PR comments | via Weaver | ✓ | ✓ | ✓ |
| Cross-plugin signal routing (Reaper, Hornet, Nook) | ✓ | — | — | — |

## Lifecycle

```
Session Start
     │
     ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Reaper  │─▶│  Hornet  │─▶│  Mantis  │
│ security │  │ changes  │  │  quality │
└──────────┘  └──────────┘  └────┬─────┘
                                 │
                            ┌────▼──────┐
                            │  Weaver   │
                            │ git flow  │
                            └───────────┘
                                 │
                            ┌────▼──────┐
                            │   Nook    │
                            │  cost     │
                            └───────────┘

Five Questions Answered:
  "What did I say?"     → Flux    (prompts)
  "What did I spend?"   → Allay   (tokens)
  "What just happened?" → Hornet  (changes)
  "Is it safe?"         → Reaper  (security)
  "What did it cost?"   → Nook    (spend)
  "Is it good?"         → Mantis  (quality)     ← you are here
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

---

Repo: https://github.com/enchanted-plugins/mantis
