"""Validate review proposals against the local input; makes no decisions."""

import json
from collections import Counter
from pathlib import Path


def validate():
    folder = Path(__file__).resolve().parent
    records = [json.loads(line) for line in (folder / "names_review_input.jsonl").read_text().splitlines()]
    proposals = [json.loads(line) for line in (folder / "names_review_proposals.jsonl").read_text().splitlines()]
    assert len(proposals) == len(records), "Missing or extra proposals"
    fields = {"type", "key", "outcome", "qid", "also_possible", "confidence", "reason"}
    references = 0
    for number, (record, proposal) in enumerate(zip(records, proposals), 1):
        prefix = f"Line {number}: "
        assert set(proposal) == fields, prefix + "Incorrect fields"
        assert (proposal["type"], proposal["key"]) == (record["type"], record["key"]), prefix + "Order or identity mismatch"
        assert proposal["outcome"] in {"match", "none", "ambiguous", "not_a_thing"}, prefix + "Invalid outcome"
        assert proposal["confidence"] in {"high", "medium", "low"}, prefix + "Invalid confidence"
        assert isinstance(proposal["reason"], str) and proposal["reason"].strip(), prefix + "Missing reason"
        assert isinstance(proposal["also_possible"], list), prefix + "Invalid alternatives"
        assert len(set(proposal["also_possible"])) == len(proposal["also_possible"]), prefix + "Duplicate alternatives"
        if proposal["outcome"] == "match":
            assert isinstance(proposal["qid"], str), prefix + "Match needs QID"
            assert proposal["also_possible"] == [], prefix + "Match has alternatives"
        else:
            assert proposal["qid"] is None, prefix + "Nonmatch has QID"
        if proposal["outcome"] == "ambiguous":
            assert len(proposal["also_possible"]) >= 2, prefix + "Ambiguity needs alternatives"
        else:
            assert proposal["also_possible"] == [], prefix + "Unexpected alternatives"
        eligible = {candidate["qid"] for candidate in record["candidates"]}
        rejected = set(record.get("rejected", []))
        chosen = ([proposal["qid"]] if proposal["qid"] is not None else []) + proposal["also_possible"]
        for qid in chosen:
            assert qid in eligible, prefix + f"{qid} not among candidates"
            assert qid not in rejected, prefix + f"{qid} was rejected"
            references += 1
    print(f"PASS: {len(proposals)}/{len(records)} records, in input order.")
    print(f"PASS: all {references} QID references occur in their own record's candidates; zero rejected selections.")
    print("Outcomes:", dict(Counter(p["outcome"] for p in proposals)))
    print("Confidence:", dict(Counter(p["confidence"] for p in proposals)))
    print("PASS: schema, outcome/QID consistency, alternatives, confidence and reasons.")


if __name__ == "__main__":
    validate()
