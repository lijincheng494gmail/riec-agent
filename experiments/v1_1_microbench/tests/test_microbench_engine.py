from __future__ import annotations

import json
from pathlib import Path
import unittest

from microbench_engine import MUTANTS, evaluate_case, matches_expected


ROOT = Path(__file__).resolve().parents[1]


class MicrobenchEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads((ROOT / "02_TARGETED_CASES.json").read_text())
        cls.by_id = {case["case_id"]: case for case in cls.cases}

    def test_case_ids_are_unique(self) -> None:
        self.assertEqual(len(self.by_id), len(self.cases))

    def test_all_required_regimes_exist(self) -> None:
        observed = {case["risk_regime"] for case in self.cases}
        self.assertEqual(observed, {f"R{i}" for i in range(8)})

    def test_baseline_confirms(self) -> None:
        case = self.by_id["T00_BASELINE_VALID_CONFIRMATION"]
        self.assertTrue(matches_expected(evaluate_case(case), case["expected"]))

    def test_high_search_one_shot_confirms(self) -> None:
        case = self.by_id["T01_R0_HIGH_DEVELOPMENT_SEARCH"]
        self.assertTrue(matches_expected(evaluate_case(case), case["expected"]))

    def test_compound_risk_fails_closed(self) -> None:
        case = self.by_id["T19_R7_COMPOUND_RISK"]
        self.assertTrue(matches_expected(evaluate_case(case), case["expected"]))

    def test_declared_mutants_are_implemented(self) -> None:
        protocol = json.loads((ROOT / "01_MICROBENCH_PROTOCOL.json").read_text())
        self.assertEqual(set(protocol["mutants"]), MUTANTS)


if __name__ == "__main__":
    unittest.main()

