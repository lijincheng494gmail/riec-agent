from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("qwen_protocol", ROOT / "src/qwen_protocol.py")
protocol = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = protocol
SPEC.loader.exec_module(protocol)


class ProtocolTests(unittest.TestCase):
    def test_response_validation(self):
        valid = {"A", "B", "C", "D"}
        self.assertEqual(protocol.validate_response({"ranked_candidate_ids": ["A", "B", "C"]}, valid), (True, "PASS"))
        self.assertFalse(protocol.validate_response({"ranked_candidate_ids": ["A", "A", "C"]}, valid)[0])
        self.assertEqual(protocol.validate_response({"ranked_candidate_ids": ["A", "B"]}, {"A", "B"}), (True, "PASS"))
        self.assertFalse(protocol.validate_response({"ranked_candidate_ids": ["A", "B", "C"]}, {"A", "B"})[0])

    def test_holm(self):
        rows = protocol.holm([("H1", 0.01), ("H2", 0.03)])
        self.assertTrue(rows[0]["reject"])
        self.assertTrue(rows[1]["reject"])

    def test_sign_test(self):
        self.assertEqual(protocol.exact_sign_p(5, 0), 0.03125)
        self.assertEqual(protocol.exact_sign_p(0, 0), 1.0)

    def test_alpha_invariant_shape(self):
        self.assertEqual(protocol.BROKER_ALPHA, 0.05)
        self.assertEqual(protocol.AGENTS_PER_WORLD, 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
