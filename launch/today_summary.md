# TrustLens: today (2026-10-22)

Done:
- Core engine: dataset, scoring, compare, gates, CLI. 4/4 tests.
- Live EvidenceRAG adapter: rerank on/off, top_k. run-live CLI.
- Dynamic UI (app.py): pick two versions, run both live, verdict.
- UI verified end to end through its own API: verdict DO NOT SHIP
  for rerank on vs off; regressed 2401_18059_1, improved
  gsad-sdee-2022_2; latency p50 978 ms to 2515 ms.
- LinkedIn draft: launch/linkedin_post.md.

Remaining (needs Meganaa):
- Create the public GitHub repo (TrustLens) and say go for push.
- Optional: Hugging Face demo deploy (same recipe as Forkwise).
- Her 60-second whiteboard story for interviews.
