# Polyglot fixture — control case (Markdown).

This file is the routing control: the dispatcher sees `.md` and must not
produce a runtime flag. There's nothing here to analyze; the assertion is
that the state log is not mutated.

If Mantis ever ships a Markdown adapter, this fixture is expected to still
produce zero correctness flags — the prose is deliberately plain.
