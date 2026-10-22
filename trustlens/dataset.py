import json
from dataclasses import dataclass, field


@dataclass
class Case:
    id: str
    question: str
    expected_doc_id: str = None
    expected_contains: str = None
    should_refuse: bool = False
    tags: list = field(default_factory=list)

    @staticmethod
    def from_dict(d):
        missing = [k for k in ("id", "question") if not d.get(k)]
        if missing:
            raise ValueError("case missing fields: %s" % ", ".join(missing))
        return Case(
            id=d["id"],
            question=d["question"],
            expected_doc_id=d.get("expected_doc_id"),
            expected_contains=d.get("expected_contains"),
            should_refuse=bool(d.get("should_refuse", False)),
            tags=list(d.get("tags", [])),
        )


def load_cases(path):
    cases = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(Case.from_dict(json.loads(line)))
    ids = [c.id for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case ids in dataset")
    return cases


def load_results(path):
    results = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                results[r["case_id"]] = r
    return results
