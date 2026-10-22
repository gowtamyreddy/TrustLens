"""Runner interface.

A runner takes a Case and returns a result dict:
  {"case_id", "status": "answered"|"insufficient_evidence",
   "answer_text" or "spans", "citations": [{"doc_id", ...}],
   "latency_ms", "cost_usd"}

V1 ships a RecordedRunner (replays saved results, for demos and tests).
The live EvidenceRAG adapter implements the same interface next.
"""
import time
from .dataset import load_results


class RecordedRunner:
    def __init__(self, results_path):
        self.results = load_results(results_path)

    def __call__(self, case):
        return self.results.get(case.id)


def run_cases(runner, cases):
    out = {}
    for case in cases:
        t0 = time.perf_counter()
        result = runner(case)
        if result is not None and not result.get("latency_ms"):
            result = dict(result)
            result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        if result is not None:
            out[case.id] = result
    return out
