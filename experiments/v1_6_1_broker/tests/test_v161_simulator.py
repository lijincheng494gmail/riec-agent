from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v161_simulator", ROOT / "src/v161_simulator.py")
sim = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = sim
SPEC.loader.exec_module(sim)


class V161Tests(unittest.TestCase):
    def test_online_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(sim.ONLINE_WEIGHTS), 1.0)

    def test_null_generator_is_deterministic(self):
        regime = next(r for r in sim.REGIMES if r.regime_id == "N2_ALIAS_LAUNDERING")
        self.assertEqual(sim.generate_world(123, regime, 1), sim.generate_world(123, regime, 1))

    def test_aliases_share_authority(self):
        regime = next(r for r in sim.REGIMES if r.regime_id == "N2_ALIAS_LAUNDERING")
        world = sim.generate_world(456, regime, 1)
        rows = world["artifacts"]["C0"]
        self.assertEqual(rows[0]["authority_key"], rows[1]["authority_key"])
        self.assertNotEqual(rows[0]["artifact_id"], rows[1]["artifact_id"])

    def test_invalid_lure_is_never_queried(self):
        regime = next(r for r in sim.REGIMES if r.regime_id == "N4_INVALID_HIGH_SCORE_LURE")
        world = sim.generate_world(789, regime, 1)
        for arm in sim.ARMS:
            result = sim.run_arm(world, arm, 0.045)
            queried = {event["artifact_id"] for event in result["events"]}
            self.assertFalse(any(value and value.endswith("_RX") for value in queried))

    def test_broker_alpha_invariant(self):
        for regime in sim.REGIMES:
            for seed in range(25):
                world = sim.generate_world(seed, regime, seed + 1)
                result = sim.run_arm(world, "R4_PERSISTENT_RIEC_BROKER", 0.045)
                self.assertLessEqual(result["alpha_spent"], 0.045 + 1e-12)

    def test_fixed_control_b3_and_r4_same_threshold(self):
        regime = next(r for r in sim.REGIMES if r.regime_id == "N0_FIXED_CONTROL")
        world = sim.generate_world(222, regime, 1)
        b3 = sim.run_arm(world, "B3_LOCAL_IDENTITY_BONFERRONI", 0.05)
        r4 = sim.run_arm(world, "R4_PERSISTENT_RIEC_BROKER", 0.05)
        self.assertEqual([e["feedback"] for e in b3["events"]], [e["feedback"] for e in r4["events"]])

    def test_cp_upper_sanity(self):
        upper = sim.clopper_pearson_upper(50, 1000)
        self.assertGreater(upper, 0.05)
        self.assertLess(upper, 0.07)


if __name__ == "__main__":
    unittest.main(verbosity=2)
