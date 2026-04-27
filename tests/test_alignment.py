"""Alignment tests for lich — cross-cutting brand contracts.

Verifies plugin.json shape, marketplace.json completeness, hook subagent guard,
and conduct module count consistency. Repo-aware via REPO_ROOT below.
"""
from __future__ import annotations
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestPluginJsonShape(unittest.TestCase):
    """Every plugin.json parses and has required keys; marketplace.json is complete."""

    REQUIRED_KEYS = {"name", "version", "description"}

    def _plugin_dirs(self) -> list[Path]:
        plugins_dir = REPO_ROOT / "plugins"
        if not plugins_dir.is_dir():
            return []
        return [p for p in plugins_dir.iterdir() if p.is_dir()]

    def _marketplace_names(self) -> set[str]:
        mp = REPO_ROOT / ".claude-plugin" / "marketplace.json"
        if not mp.exists():
            return set()
        data = json.loads(mp.read_text(encoding="utf-8"))
        return {p["name"] for p in data.get("plugins", [])}

    def test_every_plugin_json_parses_and_has_required_keys(self):
        plugin_dirs = self._plugin_dirs()
        if not plugin_dirs:
            self.skipTest("No plugins/ directory found — nothing to check.")
        for plugin_dir in plugin_dirs:
            with self.subTest(plugin=plugin_dir.name):
                path = plugin_dir / ".claude-plugin" / "plugin.json"
                self.assertTrue(path.exists(), f"{path} missing")
                data = json.loads(path.read_text(encoding="utf-8"))
                missing = self.REQUIRED_KEYS - data.keys()
                self.assertFalse(
                    missing, f"{plugin_dir.name}: missing keys {missing}"
                )
                for key in self.REQUIRED_KEYS:
                    self.assertTrue(
                        str(data[key]).strip(),
                        f"{plugin_dir.name}: key '{key}' is empty",
                    )

    def test_marketplace_json_lists_all_plugin_dirs(self):
        plugins_dir = REPO_ROOT / "plugins"
        mp = REPO_ROOT / ".claude-plugin" / "marketplace.json"
        if not plugins_dir.is_dir() or not mp.exists():
            self.skipTest("plugins/ dir or marketplace.json absent — skipping.")
        disk_names = {p.name for p in plugins_dir.iterdir() if p.is_dir()}
        listed_names = self._marketplace_names()
        self.assertEqual(
            listed_names,
            disk_names,
            f"marketplace.json mismatch: "
            f"unlisted={disk_names - listed_names} "
            f"phantom={listed_names - disk_names}",
        )


class TestHookSubagentGuard(unittest.TestCase):
    """Every hook .sh file contains the subagent-loop guard within its first 20 lines."""

    GUARD_PATTERNS = [
        re.compile(r'if \[\[ -n "\$CLAUDE_SUBAGENT" \]\]; then exit 0; fi'),
        re.compile(r'if \[\[ -n "\$\{CLAUDE_SUBAGENT:-\}" \]\]; then exit 0; fi'),
        re.compile(r'if \[\[ -n "\$CLAUDE_SUBAGENT" \]\]; then'),
        re.compile(r'if \[\[ -n "\$\{CLAUDE_SUBAGENT:-\}" \]\]; then'),
    ]

    def _hook_scripts(self) -> list[Path]:
        return list((REPO_ROOT / "plugins").rglob("hooks/*/*.sh"))

    def _has_guard_in_first_20_lines(self, text: str) -> bool:
        lines = text.splitlines()
        head = "\n".join(lines[:20])
        return any(pat.search(head) for pat in self.GUARD_PATTERNS)

    def test_every_hook_has_subagent_guard(self):
        hooks = self._hook_scripts()
        if not hooks:
            # No hooks present — pass trivially per spec.
            return
        for path in hooks:
            with self.subTest(hook=str(path.relative_to(REPO_ROOT))):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(
                    self._has_guard_in_first_20_lines(text),
                    f"{path.name}: subagent guard not found in first 20 lines",
                )


class TestConductModuleCount(unittest.TestCase):
    """Conduct module count on disk matches claims in CLAUDE.md and README.md."""

    def _count_conduct_mds(self) -> int:
        conduct_dir = REPO_ROOT / "shared" / "conduct"
        if not conduct_dir.is_dir():
            return 0
        return len(list(conduct_dir.glob("*.md")))

    def _check_count_in_text(self, text: str, actual: int, source: str) -> None:
        # Match patterns like "10 modules", "10-module", "10 conduct modules"
        pattern = re.compile(r'\b(\d+)[\s-]module', re.IGNORECASE)
        matches = pattern.findall(text)
        if not matches:
            # Soft assertion: no count phrase found — skip.
            return
        claimed_counts = {int(m) for m in matches}
        self.assertIn(
            actual,
            claimed_counts,
            f"{source}: conduct/*.md count is {actual} but text claims {claimed_counts}",
        )

    def test_claude_md_conduct_count(self):
        actual = self._count_conduct_mds()
        if actual == 0:
            self.skipTest("shared/conduct/ absent — nothing to check.")
        claude_md = REPO_ROOT / "CLAUDE.md"
        if not claude_md.exists():
            self.skipTest("CLAUDE.md absent — skipping.")
        self._check_count_in_text(
            claude_md.read_text(encoding="utf-8"), actual, "CLAUDE.md"
        )

    def test_readme_md_conduct_count(self):
        actual = self._count_conduct_mds()
        if actual == 0:
            self.skipTest("shared/conduct/ absent — nothing to check.")
        readme = REPO_ROOT / "README.md"
        if not readme.exists():
            self.skipTest("README.md absent — skipping.")
        self._check_count_in_text(
            readme.read_text(encoding="utf-8"), actual, "README.md"
        )


if __name__ == "__main__":
    unittest.main()
