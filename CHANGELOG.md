# Changelog

All notable changes to `mantis` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Mantis is Phase 3 #6 in the @enchanted-plugins ecosystem rollout and has not shipped a public release yet. This file captures the scaffolding and docs landing ahead of v0.1.0.

### Added
- Tier-1 governance docs: `SECURITY.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`.
- `.github/` scaffold: issue templates, PR template, CODEOWNERS, dependabot config.
- Tier-2 docs: `docs/getting-started.md`, `docs/installation.md`, `docs/troubleshooting.md`, `docs/adr/README.md`.

### Planned for [0.1.0]
- 6 sub-plugins covering code review for AI-assisted development: mantis-core, mantis-preference, mantis-python, mantis-rubric, mantis-sandbox, mantis-typescript, mantis-verdict (+ `full` meta-plugin).
- 5 named engines — M1 Cousot Interval Propagation, M2 Falleri Structural Diff, M5 Bounded Subprocess Dry-Run, M6 Bayesian Per-Developer Preference, M7 Zheng Pairwise Rubric — full derivations in [docs/science/README.md](docs/science/README.md).
- 3 agents across tiers; orchestrator on Opus, executors on Sonnet, validators on Haiku.
- `/mantis-review` slash command: static suspicion → sandboxed confirmation → Bayesian weighting → rubric judgment.
- Integration with Weaver's PR lifecycle: findings posted on the PR body when `/weaver:pr` is used.

Track progress in [ROADMAP.md](docs/ROADMAP.md) and the [ecosystem map](https://github.com/enchanted-plugins/flux/blob/main/docs/ecosystem.md).

[Unreleased]: https://github.com/enchanted-plugins/mantis/commits/main
