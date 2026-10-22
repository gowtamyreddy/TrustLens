"""TrustLens dynamic demo.

Pick two EvidenceRAG versions (rerank on/off, top_k), run both LIVE
over the same golden questions, and get a release verdict: metric
deltas, the cases that regressed, and a gate decision. Nothing here
is recorded; every run executes the real pipeline.

Run:  EVIDENCERAG_HOME=../evidencerag python app.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr

from trustlens.dataset import load_cases
from trustlens.metrics import build_report
from trustlens.compare import compare_reports, gate
from trustlens.runner import run_cases
from trustlens.evidencerag_adapter import EvidenceRAGRunner

EVR_HOME = os.environ.get(
    "EVIDENCERAG_HOME",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "evidencerag"))
CASES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "data", "evidencerag_cases.jsonl")
CASES = load_cases(CASES_PATH)
_runners = {}


def _runner(rerank, top_k):
    key = (bool(rerank), int(top_k))
    if key not in _runners:
        _runners[key] = EvidenceRAGRunner(EVR_HOME, rerank=rerank,
                                          top_k=top_k)
    return _runners[key]


def _top_doc(results, cid):
    r = results.get(cid)
    if not r or not r.get("citations"):
        return "(refused)"
    return r["citations"][0].get("doc_id", "?")


def run_compare(a_rerank, a_topk, b_rerank, b_topk):
    if not os.path.isdir(EVR_HOME):
        return ("EvidenceRAG was not found at %s, so the live run "
                "cannot start." % EVR_HOME, [], [], "")
    res_a = run_cases(_runner(a_rerank, a_topk), CASES)
    res_b = run_cases(_runner(b_rerank, b_topk), CASES)
    rep_a = build_report(CASES, res_a)
    rep_b = build_report(CASES, res_b)
    diff = compare_reports(rep_a, rep_b)
    ok, reasons = gate(diff["deltas"], diff["regressions"])
    sa, sb = rep_a["summary"], rep_b["summary"]

    def cfg(rerank, topk):
        return "rerank %s, top_k %d" % ("on" if rerank else "off", topk)

    verdict = ["## Verdict: %s" % ("SHIP IT" if ok else "DO NOT SHIP"),
               "",
               "Version A (%s) against version B (%s), over %d live "
               "questions." % (cfg(a_rerank, a_topk),
                               cfg(b_rerank, b_topk), len(CASES))]
    if reasons:
        verdict.append("")
        verdict.append("Gate reasons: " + "; ".join(reasons))
    if diff["regressions"]:
        verdict.append("Regressed cases: " + ", ".join(diff["regressions"]))
    if diff["improvements"]:
        verdict.append("Improved cases: " + ", ".join(diff["improvements"]))
    if not diff["regressions"] and not diff["improvements"]:
        verdict.append("No case changed its pass/fail outcome.")

    rows = []
    for key, label, fmt in (
            ("pass_rate", "Pass rate", "%.3f"),
            ("hit_at_1", "Hit@1 (top citation)", "%.3f"),
            ("citation_precision", "Citation precision", "%.3f"),
            ("contains_rate", "Expected phrase found", "%.3f"),
            ("latency_p50_ms", "Latency p50 (ms)", "%.0f"),
            ("latency_p95_ms", "Latency p95 (ms)", "%.0f")):
        va, vb = sa.get(key, 0.0), sb.get(key, 0.0)
        rows.append([label, fmt % va, fmt % vb,
                     ("%+.3f" % (vb - va)) if fmt == "%.3f"
                     else ("%+.0f" % (vb - va))])

    by_id_a = {c["case_id"]: c for c in rep_a["cases"]}
    by_id_b = {c["case_id"]: c for c in rep_b["cases"]}
    case_rows = []
    for case in CASES:
        pa = "PASS" if by_id_a[case.id]["passed"] else "FAIL"
        pb = "PASS" if by_id_b[case.id]["passed"] else "FAIL"
        mark = ""
        if pa == "PASS" and pb == "FAIL":
            mark = "REGRESSED"
        elif pa == "FAIL" and pb == "PASS":
            mark = "IMPROVED"
        case_rows.append([case.id, pa, pb, _top_doc(res_a, case.id),
                          _top_doc(res_b, case.id), mark])
    note = ("Every number above came from running the real EvidenceRAG "
            "pipeline just now, on this machine, over the questions "
            "listed below. First run loads the models and takes about "
            "a minute; later runs are faster.")
    return "\n".join(verdict), rows, case_rows, note


HEADER = """# TrustLens: did the change make it better?

Two versions of the same AI system, one set of golden questions,
run live. TrustLens scores both, names the cases that regressed,
and gives a ship or do-not-ship verdict.

**Try the classic question:** version A with reranking off, version
B with reranking on. Engineers assume the reranker helps. Run it
and see what it actually does to accuracy and latency."""

with gr.Blocks(title="TrustLens: Live Regression Check",
               theme=gr.themes.Soft(primary_hue="indigo",
                                    neutral_hue="slate"),
               css=".footer {display: none !important}") as demo:
    gr.Markdown(HEADER)
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Version A (current)")
            a_rerank = gr.Checkbox(label="Cross-encoder rerank", value=False)
            a_topk = gr.Slider(1, 10, value=5, step=1, label="top_k")
        with gr.Column():
            gr.Markdown("### Version B (candidate)")
            b_rerank = gr.Checkbox(label="Cross-encoder rerank", value=True)
            b_topk = gr.Slider(1, 10, value=5, step=1, label="top_k")
    run_btn = gr.Button("Run both versions live", variant="primary")
    verdict_md = gr.Markdown("_Your verdict will appear here._")
    metrics = gr.Dataframe(
        headers=["Metric", "Version A", "Version B", "Change"],
        datatype=["str", "str", "str", "str"],
        label="Scores", interactive=False)
    case_tbl = gr.Dataframe(
        headers=["Case", "A", "B", "A top source", "B top source",
                 "Change"],
        datatype=["str", "str", "str", "str", "str", "str"],
        label="Case by case", interactive=False)
    note_md = gr.Markdown("")
    with gr.Accordion("The golden questions used for every run",
                      open=False):
        gr.Dataframe(
            value=[[c.id, c.question,
                    c.expected_doc_id or "(must refuse)"]
                   for c in CASES],
            headers=["Case", "Question", "Expected source"],
            datatype=["str", "str", "str"], interactive=False)
    gr.Markdown(
        "<small>Local and free: open-weight models on CPU, no paid "
        "APIs, no recorded results. Code: "
        "[TrustLens](https://github.com/gowtamyreddy) (repo on "
        "request) \u00b7 System under test: EvidenceRAG</small>")
    run_btn.click(run_compare,
                  inputs=[a_rerank, a_topk, b_rerank, b_topk],
                  outputs=[verdict_md, metrics, case_tbl, note_md],
                  api_name="run_compare")

if __name__ == "__main__":
    demo.queue()
    demo.launch()
