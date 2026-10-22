"""Live EvidenceRAG adapter for TrustLens.

Implements the TrustLens runner interface against the real EvidenceRAG
pipeline (hybrid retrieval, optional cross-encoder rerank, extractive
answer). The config knobs are the ones a real engineer would change:
rerank on/off and top_k. Everything is local and free.
"""
import sys
import time

_cache = {}


def _load(home):
    if home in _cache:
        return _cache[home]
    if home not in sys.path:
        sys.path.insert(0, home)
    from src import embed, index as vector_index, ingest
    from src import rerank as rerank_module
    from src import answer as answer_module
    from src.retrieve import Retriever
    import pathlib
    artifacts = pathlib.Path(home) / "data" / "artifacts"
    chunks = ingest.load_chunks(artifacts / "chunks.jsonl")
    faiss_index = vector_index.load_index(artifacts / "index.faiss")
    embedder = embed.Embedder()
    retriever = Retriever(chunks, embedder, faiss_index)
    _cache[home] = (retriever, rerank_module, answer_module)
    return _cache[home]


class EvidenceRAGRunner:
    """One runner instance = one system version (a config)."""

    def __init__(self, home, rerank=True, top_k=5):
        self.home = str(home)
        self.use_rerank = bool(rerank)
        self.top_k = int(top_k)
        self._reranker = None

    def _get_reranker(self, rerank_module):
        if self._reranker is None:
            self._reranker = rerank_module.Reranker()
        return self._reranker

    def __call__(self, case):
        retriever, rerank_module, answer_module = _load(self.home)
        t0 = time.perf_counter()
        fused = retriever.hybrid_search(case.question, top_k=20)
        if self.use_rerank:
            ranked = rerank_module.rerank(
                case.question, fused, self._get_reranker(rerank_module),
                self.top_k)
        else:
            ranked = fused[: self.top_k]
        result = answer_module.extractive_answer(
            case.question, ranked, retriever.embedder)
        latency = round((time.perf_counter() - t0) * 1000, 1)
        spans = result.get("spans") or []
        return {
            "case_id": case.id,
            "status": result.get("status"),
            "spans": spans,
            "citations": [s["citation"] for s in spans],
            "answer_text": " ".join(s["text"] for s in spans),
            "latency_ms": latency,
            "cost_usd": 0.0,
        }
