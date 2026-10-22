import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from trustlens.dataset import load_cases, load_results
from trustlens.metrics import build_report, score_case
from trustlens.compare import compare_reports, gate

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


class TrustLensTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases(os.path.join(DATA, "sample_cases.jsonl"))
        self.a = load_results(os.path.join(DATA, "sample_results_a.jsonl"))
        self.b = load_results(os.path.join(DATA, "sample_results_b.jsonl"))

    def test_dataset_loads(self):
        self.assertEqual(len(self.cases), 6)
        self.assertTrue(self.cases[-1].should_refuse)

    def test_base_run_all_pass(self):
        rep = build_report(self.cases, self.a)
        self.assertEqual(rep["summary"]["pass_rate"], 1.0)
        self.assertEqual(rep["summary"]["hit_at_1"], 1.0)

    def test_refusal_scored(self):
        case = self.cases[-1]
        self.assertTrue(score_case(case, self.a[case.id]).passed)
        bad = {"case_id": case.id, "status": "answered",
               "answer_text": "About 11 m/s.", "citations": []}
        self.assertFalse(score_case(case, bad).passed)

    def test_compare_finds_regression_and_gate_fails(self):
        ra = build_report(self.cases, self.a)
        rb = build_report(self.cases, self.b)
        diff = compare_reports(ra, rb)
        self.assertEqual(diff["regressions"], ["selfrag_tokens"])
        ok, reasons = gate(diff["deltas"], diff["regressions"])
        self.assertFalse(ok)
        self.assertTrue(reasons)


if __name__ == "__main__":
    unittest.main()
