DEFAULT_GATES = {
    "max_pass_rate_drop": 0.0,
    "max_hit_at_1_drop": 0.05,
}


def compare_reports(base, candidate):
    b = {c["case_id"]: c for c in base["cases"]}
    c = {x["case_id"]: x for x in candidate["cases"]}
    regressions = sorted(cid for cid in b
                         if b[cid]["passed"] and cid in c
                         and not c[cid]["passed"])
    improvements = sorted(cid for cid in b
                          if not b[cid]["passed"] and cid in c
                          and c[cid]["passed"])
    bs, cs = base["summary"], candidate["summary"]
    keys = ["pass_rate", "hit_at_1", "citation_precision",
            "contains_rate", "latency_p50_ms", "latency_p95_ms"]
    deltas = {k: round(cs.get(k, 0.0) - bs.get(k, 0.0), 4) for k in keys}
    return {"deltas": deltas, "regressions": regressions,
            "improvements": improvements}


def gate(candidate_ok_deltas, regressions, gates=None):
    g = dict(DEFAULT_GATES)
    if gates:
        g.update(gates)
    reasons = []
    if candidate_ok_deltas.get("pass_rate", 0.0) < -g["max_pass_rate_drop"]:
        reasons.append("pass rate dropped by %.3f (allowed %.3f)"
                       % (-candidate_ok_deltas["pass_rate"],
                          g["max_pass_rate_drop"]))
    if candidate_ok_deltas.get("hit_at_1", 0.0) < -g["max_hit_at_1_drop"]:
        reasons.append("hit@1 dropped by %.3f (allowed %.3f)"
                       % (-candidate_ok_deltas["hit_at_1"],
                          g["max_hit_at_1_drop"]))
    if regressions and g["max_pass_rate_drop"] <= 0.0:
        reasons.append("regressed cases: %s" % ", ".join(regressions))
    return (len(reasons) == 0), reasons
