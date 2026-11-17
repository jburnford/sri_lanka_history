"""Serialize manually reviewed decisions and validate their candidate references.

The TSV contains individually authored decisions; this script makes no place decisions.
"""
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
records = [json.loads(line) for line in (root / 'places_review_input.jsonl').read_text().splitlines()]
proposals = []
for expected, line in enumerate((root / 'places_review_decisions.tsv').read_text().splitlines(), 1):
    index, outcome, choices, confidence, reason = line.split('\t', 4)
    assert int(index) == expected, (index, expected)
    record = records[expected - 1]
    selected = [] if choices == '-' else [record['candidates'][int(n) - 1]['qid'] for n in choices.split(',')]
    assert outcome in {'match', 'none', 'ambiguous', 'not_a_place'}
    assert confidence in {'high', 'medium', 'low'}
    assert len(selected) == len(set(selected))
    assert (outcome == 'match' and len(selected) == 1) or outcome != 'match'
    assert outcome not in {'none', 'not_a_place'} or not selected
    rejected = record.get('rejected')
    assert not rejected or rejected not in selected, (record['key'], rejected)
    proposal = dict(key=record['key'], outcome=outcome,
                    qid=selected[0] if outcome == 'match' else None,
                    also_possible=selected if outcome == 'ambiguous' else [],
                    confidence=confidence, reason=reason)
    proposals.append(proposal)

out = root / 'places_review_proposals.jsonl'
out.write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in proposals))
# Independently reread the requested artifact and check membership and order.
written = [json.loads(line) for line in out.read_text().splitlines()]
references = 0
for index, proposal in enumerate(written):
    record = records[index]
    assert proposal['key'] == record['key'], index + 1
    valid = {c['qid'] for c in record['candidates']}
    used = ([proposal['qid']] if proposal['qid'] is not None else []) + proposal['also_possible']
    assert all(qid in valid for qid in used), (index + 1, proposal)
    assert record.get('rejected') not in used, (index + 1, 'rejected candidate')
    references += len(used)
print(json.dumps({'reviewed': len(written), 'input': len(records),
                  'outcomes': dict(Counter(p['outcome'] for p in written)),
                  'confidence': dict(Counter(p['confidence'] for p in written)),
                  'candidate_references_checked': references,
                  'candidate_membership_errors': 0, 'rejected_references': 0,
                  'input_order': 'passed'}, indent=2))
