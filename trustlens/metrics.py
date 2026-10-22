import math
from dataclasses import dataclass


@dataclass
class CaseScore:
    case_id: str
    passed: bool
    refused: bool
    hit_at_1: float
    citation_precision: float
    contains_expected: float
    latency_ms: float
    reason: str
    category: str = ""


def _answer_text(result):
    if result.get("answer_text"):
        return result["answer_text"]
    spans = result.get("spans") or []
    return " ".join(s.get("text", "") for s in spans)


def _citation_docs(result):
    docs = []
    for c in result.get("citations") or []:
        docs.append(c.get("doc_id"))
    for s in result.get("spans") or []:
        cit = s.get("citation") or {}
        if cit.get("doc_id"):
            docs.append(cit["doc_id"])
    return docs


def score_case(case, result):
    if result is None:
        return CaseScore(case.id, False, False, 0.0, 0.0, 0.0, 0.0,
                         "no result recorded")
    refused = result.get("status") != "answered"
    docs = _citation_docs(result)
    text = _answer_text(result)
    hit1 = 1.0 if (case.expected_doc_id and docs and
                   docs[0] == case.expected_doc_id) else 0.0
    if case.expected_doc_id and docs:
        prec = sum(1 for d in docs if d == case.expected_doc_id) / len(docs)
    else:
        prec = 0.0
    targets = case.expected_contains
    if isinstance(targets, str):
        targets = [targets]
    contains = 1.0 if (targets and any(t.lower() in text.lower()
                                       for t in targets)) else 0.0
    latency = float(result.get("latency_ms") or 0.0)

    if case.should_refuse:
        passed = refused
        reason = "refused as expected" if refused else "answered but should refuse"
        category = "correct_refusal" if refused else "answered_should_refuse"
        return CaseScore(case.id, passed, refused, 0.0, 0.0, 0.0, latency,
                         reason, category)

    problems = []
    if refused:
        problems.append("refused but an answer was expected")
    if case.expected_doc_id and not hit1:
        problems.append("top citation is not the expected document")
    if case.expected_contains and not contains:
        problems.append("answer does not contain the expected phrase")
    passed = not problems
    reason = "pass" if passed else "; ".join(problems)
    if refused:
        category = "refused_should_answer"
    elif passed:
        category = "pass"
    elif hit1:
        category = "right_source_wrong_sentence"
    else:
        category = "wrong_source"
    return CaseScore(case.id, passed, refused, hit1, prec, contains,
                     latency, reason, category)


def _pct(values, q):
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, max(0, math.ceil(q * len(s)) - 1))
    return s[idx]


def summarize(scores):
    n = len(scores)
    if n == 0:
        return {"cases": 0}
    answerable = [s for s in scores if s.reason != "refused as expected"
                  and s.reason != "answered but should refuse"]
    return {
        "cases": n,
        "pass_rate": sum(1 for s in scores if s.passed) / n,
        "hit_at_1": (sum(s.hit_at_1 for s in answerable) / len(answerable)
                     if answerable else 0.0),
        "citation_precision": (sum(s.citation_precision for s in answerable)
                               / len(answerable) if answerable else 0.0),
        "contains_rate": (sum(s.contains_expected for s in answerable)
                          / len(answerable) if answerable else 0.0),
        "refusal_cases": sum(1 for s in scores
                             if s.reason in ("refused as expected",
                                             "answered but should refuse")),
        "latency_p50_ms": _pct([s.latency_ms for s in scores], 0.50),
        "latency_p95_ms": _pct([s.latency_ms for s in scores], 0.95),
    }


def build_report(cases, results):
    scores = [score_case(c, results.get(c.id)) for c in cases]
    return {
        "summary": summarize(scores),
        "cases": [vars(s) for s in scores],
    }
