I built a tool that tells you whether your AI change made things worse.

Everyone changes a prompt, flips on a reranker, tweaks a setting,
eyeballs three outputs, and ships. Then users find the regression.

So I built TrustLens. Pick two versions of a system, run both live
over the same golden questions, and get a verdict: ship, or do not
ship, with the exact cases that regressed named.

First thing I pointed it at: my own EvidenceRAG system. The
question every RAG engineer has an opinion about: does the
cross-encoder reranker actually help?

Live result over 10 golden questions:
- Retrieval was perfect in both versions. Hit@1 and citation
  precision: 1.000 with rerank off, 1.000 with it on.
- Pass rate: identical, 0.500 in both.
- Latency: reranking cost real time. p50 went from about 1.0s to
  2.5s, p95 from about 2.0s to 4.0s.
- And one case that passed without the reranker failed with it,
  because the answerer quoted a different sentence.

Verdict from TrustLens: DO NOT SHIP. Not because reranking is bad,
but because on this question set it bought no accuracy, cost 2 to
4x the latency, and silently flipped a case.

That is the job of an evaluation gate: not to confirm what you
hoped, but to catch what you would have shipped.

EvidenceRAG answers with citations. Forkwise traces what a run
did. TrustLens decides whether the change ships.

Code and live demo in the comments.
