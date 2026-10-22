import argparse
import json
import sys

from .dataset import load_cases, load_results
from .metrics import build_report
from .compare import compare_reports, gate
from .runner import run_cases


def _write(obj, path):
    text = json.dumps(obj, indent=2)
    if path:
        with open(path, "w") as f:
            f.write(text)
    return text


def cmd_score(args):
    cases = load_cases(args.dataset)
    results = load_results(args.results)
    report = build_report(cases, results)
    _write(report, args.out)
    s = report["summary"]
    print("cases=%d pass_rate=%.3f hit@1=%.3f citation_precision=%.3f "
          "p50=%.0fms p95=%.0fms" % (s["cases"], s["pass_rate"],
          s["hit_at_1"], s["citation_precision"], s["latency_p50_ms"],
          s["latency_p95_ms"]))
    return 0


def cmd_run_live(args):
    from .evidencerag_adapter import EvidenceRAGRunner
    cases = load_cases(args.dataset)
    runner = EvidenceRAGRunner(args.evidencerag_home,
                               rerank=not args.no_rerank,
                               top_k=args.top_k)
    results = run_cases(runner, cases)
    report = build_report(cases, results)
    report["config"] = {"rerank": not args.no_rerank, "top_k": args.top_k,
                        "system": "evidencerag-live"}
    _write(report, args.out)
    if args.results_out:
        with open(args.results_out, "w") as f:
            for cid in sorted(results):
                f.write(json.dumps(results[cid]) + "\n")
    s = report["summary"]
    print("LIVE run: cases=%d pass_rate=%.3f hit@1=%.3f "
          "citation_precision=%.3f p50=%.0fms p95=%.0fms"
          % (s["cases"], s["pass_rate"], s["hit_at_1"],
             s["citation_precision"], s["latency_p50_ms"],
             s["latency_p95_ms"]))
    return 0


def cmd_compare(args):
    with open(args.base) as f:
        base = json.load(f)
    with open(args.candidate) as f:
        cand = json.load(f)
    diff = compare_reports(base, cand)
    ok, reasons = gate(diff["deltas"], diff["regressions"])
    diff["gate_passed"] = ok
    diff["gate_reasons"] = reasons
    print(_write(diff, args.out))
    print("GATE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None):
    p = argparse.ArgumentParser(prog="trustlens")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score")
    s.add_argument("--dataset", required=True)
    s.add_argument("--results", required=True)
    s.add_argument("--out")
    s.set_defaults(fn=cmd_score)
    r = sub.add_parser("run-live")
    r.add_argument("--dataset", required=True)
    r.add_argument("--evidencerag-home", required=True)
    r.add_argument("--top-k", type=int, default=5)
    r.add_argument("--no-rerank", action="store_true")
    r.add_argument("--out")
    r.add_argument("--results-out")
    r.set_defaults(fn=cmd_run_live)
    c = sub.add_parser("compare")
    c.add_argument("--base", required=True)
    c.add_argument("--candidate", required=True)
    c.add_argument("--out")
    c.set_defaults(fn=cmd_compare)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
