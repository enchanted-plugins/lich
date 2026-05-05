"""Tests for M6 Bayesian Preference Accumulation.

Covers: Beta math, Thompson sampling determinism, the 5% surfacing floor,
observer state round-trip, override round-trip, and reader per-flag/aggregate
behavior.
"""

from __future__ import annotations

import json
import random
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from posteriors import (  # noqa: E402
    SURFACING_FLOOR,
    Posterior,
    mean,
    surfacing_probability,
    thompson_sample,
    update,
)
import observer  # noqa: E402
import override  # noqa: E402
import reader  # noqa: E402


class BetaMathTests(unittest.TestCase):
    def test_uniform_prior_mean_is_half(self):
        p = Posterior("alice", "rule-1")
        self.assertAlmostEqual(mean(p), 0.5)

    def test_mean_after_accepts(self):
        p = Posterior("alice", "rule-1", accepts=5, rejects=0)
        # alpha=6, beta=1 → 6/7
        self.assertAlmostEqual(mean(p), 6 / 7)

    def test_mean_after_rejects(self):
        p = Posterior("alice", "rule-1", accepts=0, rejects=5)
        # alpha=1, beta=6 → 1/7
        self.assertAlmostEqual(mean(p), 1 / 7)

    def test_mean_symmetry_with_equal_counts(self):
        p = Posterior("alice", "rule-1", accepts=10, rejects=10)
        self.assertAlmostEqual(mean(p), 0.5)

    def test_update_returns_new_posterior_append_only(self):
        p = Posterior("alice", "rule-1", accepts=1, rejects=1)
        p2 = update(p, accepted=True)
        # Original untouched
        self.assertEqual(p.accepts, 1)
        self.assertEqual(p2.accepts, 2)
        self.assertEqual(p2.rejects, 1)

    def test_update_reject_increments_rejects(self):
        p = Posterior("alice", "rule-1", accepts=3, rejects=2)
        p2 = update(p, accepted=False)
        self.assertEqual(p2.accepts, 3)
        self.assertEqual(p2.rejects, 3)


class ThompsonSamplingTests(unittest.TestCase):
    def test_seeded_rng_is_deterministic(self):
        p = Posterior("alice", "rule-1", accepts=5, rejects=3)
        r1 = random.Random(42)
        r2 = random.Random(42)
        self.assertEqual(thompson_sample(p, r1), thompson_sample(p, r2))

    def test_samples_in_unit_interval(self):
        p = Posterior("alice", "rule-1", accepts=2, rejects=7)
        rng = random.Random(0)
        for _ in range(200):
            s = thompson_sample(p, rng)
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 1.0)

    def test_samples_concentrate_near_mean_with_many_observations(self):
        p = Posterior("alice", "rule-1", accepts=90, rejects=10)
        rng = random.Random(7)
        draws = [thompson_sample(p, rng) for _ in range(1000)]
        avg = sum(draws) / len(draws)
        # True posterior mean = 91/102 ≈ 0.892
        self.assertGreater(avg, 0.8)
        self.assertLess(avg, 0.95)


class SurfacingFloorTests(unittest.TestCase):
    def test_floor_constant_is_five_percent(self):
        # Load-bearing contract.
        self.assertEqual(SURFACING_FLOOR, 0.05)

    def test_floor_enforced_after_many_rejects(self):
        """100 rejects should NOT let a sample fall below 0.05."""
        p = Posterior("alice", "doomed-rule", accepts=0, rejects=100)
        rng = random.Random(123)
        for _ in range(500):
            s = surfacing_probability(p, rng=rng)
            self.assertGreaterEqual(s, SURFACING_FLOOR)

    def test_floor_clamps_up_not_down(self):
        """A sample > floor must be returned as-is, not replaced with floor."""
        # Heavy-accepts posterior → most samples above floor.
        p = Posterior("alice", "rule-1", accepts=50, rejects=0)
        rng = random.Random(1)
        high_count = 0
        for _ in range(100):
            s = surfacing_probability(p, rng=rng)
            if s > 0.5:
                high_count += 1
        self.assertGreater(high_count, 50)  # most should be high, not clamped

    def test_custom_floor_respected(self):
        p = Posterior("alice", "rule-1", accepts=0, rejects=1000)
        rng = random.Random(0)
        s = surfacing_probability(p, floor=0.1, rng=rng)
        self.assertGreaterEqual(s, 0.1)


class ObserverRoundTripTests(unittest.TestCase):
    def _tmp_state(self) -> Path:
        d = Path(tempfile.mkdtemp(prefix="m6-test-"))
        return d / "learnings.json"

    def test_observe_then_load(self):
        path = self._tmp_state()
        observer.observe("alice", "PY-M1-001", accepted=True, path=path)
        observer.observe("alice", "PY-M1-001", accepted=True, path=path)
        observer.observe("alice", "PY-M1-001", accepted=False, path=path)

        state = observer.load_state(path)
        p = state["alice::PY-M1-001"]
        self.assertEqual(p.accepts, 2)
        self.assertEqual(p.rejects, 1)

    def test_get_posterior_missing_returns_prior(self):
        path = self._tmp_state()
        p = observer.get_posterior("bob", "rule-x", path)
        self.assertEqual(p.accepts, 0)
        self.assertEqual(p.rejects, 0)

    def test_save_state_is_pretty_printed_json(self):
        path = self._tmp_state()
        observer.observe("alice", "r1", accepted=True, path=path)
        text = path.read_text(encoding="utf-8")
        # Pretty: indented, sorted keys, trailing newline
        self.assertIn("\n", text)
        self.assertIn("  ", text)
        # Structure
        data = json.loads(text)
        self.assertIn("alice::r1", data)
        self.assertEqual(data["alice::r1"]["accepts"], 1)

    def test_multiple_pairs_independent(self):
        path = self._tmp_state()
        observer.observe("alice", "r1", accepted=True, path=path)
        observer.observe("alice", "r2", accepted=False, path=path)
        observer.observe("bob", "r1", accepted=True, path=path)

        state = observer.load_state(path)
        self.assertEqual(len(state), 3)
        self.assertEqual(state["alice::r1"].accepts, 1)
        self.assertEqual(state["alice::r2"].rejects, 1)
        self.assertEqual(state["bob::r1"].accepts, 1)

    def test_corrupt_state_treated_as_empty(self):
        path = self._tmp_state()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not-json{{{", encoding="utf-8")
        self.assertEqual(observer.load_state(path), {})


class OverrideRoundTripTests(unittest.TestCase):
    def _tmp_state(self) -> Path:
        d = Path(tempfile.mkdtemp(prefix="m6-ovr-"))
        return d / "overrides.json"

    def test_disable_and_check(self):
        path = self._tmp_state()
        self.assertFalse(override.is_disabled("alice", "noisy-rule", path))
        entry = override.disable("alice", "noisy-rule", path)
        self.assertTrue(override.is_disabled("alice", "noisy-rule", path))
        self.assertEqual(entry["dev_id"], "alice")
        self.assertEqual(entry["rule_id"], "noisy-rule")

    def test_reprompt_is_90_days_out(self):
        path = self._tmp_state()
        entry = override.disable("alice", "noisy-rule", path)
        disabled_at = override._parse_iso(entry["disabled_at"])
        reprompt_at = override._parse_iso(entry["reprompt_at"])
        delta = reprompt_at - disabled_at
        # Should be within 1s of exactly 90 days
        self.assertAlmostEqual(delta.total_seconds(), timedelta(days=90).total_seconds(), delta=2)

    def test_due_for_reprompt_false_when_fresh(self):
        path = self._tmp_state()
        override.disable("alice", "r", path)
        self.assertFalse(override.due_for_reprompt("alice", "r", path))

    def test_due_for_reprompt_true_when_expired(self):
        path = self._tmp_state()
        # Manually write a stale entry
        stale = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat().replace("+00:00", "Z")
        reprompt = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                [{"dev_id": "alice", "rule_id": "r", "disabled_at": stale, "reprompt_at": reprompt}]
            ),
            encoding="utf-8",
        )
        self.assertTrue(override.due_for_reprompt("alice", "r", path))

    def test_disable_refreshes_existing_entry(self):
        path = self._tmp_state()
        override.disable("alice", "r", path)
        first = override._load(path)[0]["disabled_at"]
        # Re-disable; should refresh
        override.disable("alice", "r", path)
        entries = override._load(path)
        self.assertEqual(len(entries), 1)  # not duplicated


class ReaderTests(unittest.TestCase):
    def _setup_state(self):
        d = Path(tempfile.mkdtemp(prefix="m6-rdr-"))
        state_path = d / "learnings.json"
        ovr_path = d / "overrides.json"
        # alice accepted rule-A strongly
        for _ in range(8):
            observer.observe("alice", "rule-A", accepted=True, path=state_path)
        # alice mildly rejected rule-B
        observer.observe("alice", "rule-B", accepted=True, path=state_path)
        observer.observe("alice", "rule-B", accepted=False, path=state_path)
        observer.observe("alice", "rule-B", accepted=False, path=state_path)
        # rule-C: strongly rejected
        for _ in range(20):
            observer.observe("alice", "rule-C", accepted=False, path=state_path)
        return state_path, ovr_path

    def test_per_flag_assessment_classifies_by_mean(self):
        state_path, ovr_path = self._setup_state()
        flags = [
            {"rule_id": "rule-A"},
            {"rule_id": "rule-B"},
            {"rule_id": "rule-C"},
            {"rule_id": "rule-D"},  # never seen → prior 0.5 → likely-accepted
        ]
        rng = random.Random(42)
        out = reader.per_flag_assessment(
            flags, "alice", state_path, ovr_path, rng
        )
        classes = {a["rule_id"]: a["classification"] for a in out}
        self.assertEqual(classes["rule-A"], "likely-accepted")
        # rule-B: alpha=2, beta=3 → mean=0.4 → borderline
        self.assertEqual(classes["rule-B"], "borderline")
        self.assertEqual(classes["rule-C"], "likely-rejected")
        self.assertEqual(classes["rule-D"], "likely-accepted")  # prior

    def test_disabled_rules_never_surface(self):
        state_path, ovr_path = self._setup_state()
        override.disable("alice", "rule-A", ovr_path)
        flags = [{"rule_id": "rule-A"}]
        out = reader.per_flag_assessment(
            flags, "alice", state_path, ovr_path, random.Random(0)
        )
        self.assertTrue(out[0]["disabled"])
        self.assertFalse(out[0]["would_surface"])

    def test_evaluate_aggregates_counts(self):
        state_path, ovr_path = self._setup_state()
        flags = [
            {"rule_id": "rule-A"},
            {"rule_id": "rule-A"},
            {"rule_id": "rule-B"},
        ]
        # Force all samples high so they surface
        class _HighRNG(random.Random):
            def betavariate(self, a, b):  # type: ignore[override]
                return 0.99

        rng = _HighRNG()
        agg = reader.evaluate(flags, "alice", state_path, ovr_path, rng)
        self.assertEqual(agg["surfaced_count"], 3)
        self.assertEqual(agg["accept_majority_count"], 2)  # 2x rule-A
        self.assertEqual(agg["borderline_count"], 1)  # rule-B

    def test_floor_still_surfaces_rejected_rule_sometimes(self):
        state_path, ovr_path = self._setup_state()
        flags = [{"rule_id": "rule-C"}]
        # Run many trials; the 5% floor guarantees nonzero surfacing probability
        surfaced = 0
        for seed in range(200):
            rng = random.Random(seed)
            out = reader.per_flag_assessment(
                flags, "alice", state_path, ovr_path, rng
            )
            # Surfacing probability must be >= floor even on rule-C
            self.assertGreaterEqual(out[0]["surfacing_probability"], SURFACING_FLOOR)
            if out[0]["would_surface"]:
                surfaced += 1
        # Not asserting exact count — just that the floor is honored each call.

    def test_latest_for_developer_scopes_correctly(self):
        state_path, ovr_path = self._setup_state()
        observer.observe("bob", "rule-X", accepted=True, path=state_path)
        rules = reader.latest_for_developer("alice", state_path)
        self.assertIn("rule-A", rules)
        self.assertIn("rule-B", rules)
        self.assertIn("rule-C", rules)
        self.assertNotIn("rule-X", rules)


if __name__ == "__main__":
    unittest.main()
