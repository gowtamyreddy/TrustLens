# TrustLens

Did this change make the AI system better, or worse?

TrustLens is an evaluation regression workbench for LLM and RAG
systems. Run a golden dataset against two versions of your system,
score both with the same deterministic metrics, and see exactly which
cases regressed before you ship.

## Why
Prompt tweaks, chunking changes, and reranker settings all change
answers silently. Teams eyeball a few outputs and ship. TrustLens
replaces the eyeball with a repeatable comparison and a release gate.

## Metrics (V1, deterministic, free)
- Pass rate per case and overall
- Hit@1: the top citation is the expected document
- Citation precision: share of citations from the expected document
- Refusal correctness: unanswerable questions are refused, not answered
- Latency p50 and p95

## Quickstart
Score a recorded run against the sample dataset:

    python -m trustlens.cli score --dataset data/sample_cases.jsonl --results data/sample_results_a.jsonl --out report_a.json
    python -m trustlens.cli score --dataset data/sample_cases.jsonl --results data/sample_results_b.jsonl --out report_b.json
    python -m trustlens.cli compare --base report_a.json --candidate report_b.json

The compare command prints metric deltas, regressions, improvements,
and a gate verdict. It exits non-zero when the gate fails.

## Status
V1 core: dataset loading, scoring, comparison, gates, CLI, tests.
Dynamic layer DONE and VERIFIED end to end (2026-10-22): a live
EvidenceRAG adapter (rerank on/off, top_k) and a demo UI (app.py)
that runs two versions live over the golden questions and returns
a ship / do-not-ship verdict. Nothing recorded. The full run
(A off, B on) completed through the UI in about a minute.

## First live case study (2026-10-21, local 20-paper corpus, 10 cases)
Question: does turning the cross-encoder reranker on help?
- Retrieval: hit@1 and citation precision were 1.000 in BOTH versions.
- Pass rate: 0.500 in both. Most failures are phrase matching: the
  answerer quoted a different sentence from the right paper than the
  golden phrase, plus one refusal case the system answered anyway.
- Latency: rerank on cost p50 619 ms to 2406 ms, p95 1193 to 5389.
- Verdict: gate FAILED the reranked version, because one case
  regressed (RAPTOR phrase match) even at equal pass rate.
Honest reading: on this set, reranking bought no accuracy and cost
about 4x latency. That is the kind of finding TrustLens exists for.
