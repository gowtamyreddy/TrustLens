# TrustLens: build plan

## One line
TrustLens tells you whether a change to an AI system made it better or
worse, before you ship it.

## Goal
Give an AI engineer a repeatable way to run a golden dataset against two
versions of a system (prompt, retrieval settings, model, or config),
score both runs with the same metrics, and see exactly which cases
regressed.

## The gap it fills
EvidenceRAG answers questions and Forkwise shows what a run did.
Neither answers the release question: "is version B safe to ship?"
Teams usually eyeball a few outputs, ship, and find regressions from
users. TrustLens makes the comparison mechanical and auditable.

## V1 scope
- Golden dataset format (JSONL): question, expected document, expected
  phrase, should-refuse flag, tags.
- Scoring: pass/fail per case, hit@1 on the top citation, citation
  precision, refusal correctness, latency p50/p95.
- Compare: metric deltas between a base run and a candidate run, the
  list of cases that passed before and fail now (regressions), and the
  list that flipped the other way (improvements).
- Gates: a run fails the gate if pass rate or hit@1 drops beyond a
  threshold. The CLI exits non-zero, so it can sit in CI later.
- Recorded runner for demos and tests. A live EvidenceRAG adapter is
  the next step, behind the same runner interface.

## Not in V1
- No paid LLM judge. A judge interface can come later; V1 metrics are
  deterministic and free.
- No hosted multi-user service. Local first, like Forkwise.

## Role split
- Boone: engine, CLI, tests, dashboard, demo.
- Meganaa: the golden dataset judgment calls, threshold choices, README
  story, and the interview explanation.

## Interview story (draft)
"Prompt and retrieval changes are code changes, so I test them like
code. TrustLens runs the same golden set against the old and new
version, scores citations and refusals deterministically, and blocks
the release if a case that used to pass now fails."
