#!/usr/bin/env python3
"""Check output provenance and regressions in the ledger's normal entry points."""
import csv
import gzip
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ('table_id year_volume pdf_page printed_page flow class_as_printed '
          'group_as_printed article_as_printed country_group_as_printed '
          'country_as_printed unit_as_printed measure value_as_printed value row_kind note').split()
with (ROOT/'extracted/trade.tsv').open() as f:
    reader = csv.DictReader(f, delimiter='\t')
    assert reader.fieldnames == FIELDS
    rows = list(reader)
source = {}
for year in sorted({r['year_volume'] for r in rows}):
    with gzip.open(ROOT/f'tables/{year}.jsonl.gz', 'rt') as f:
        source.update((t['id'], t) for t in map(json.loads, f))
for row in rows:
    assert row['flow'] in {'import', 'export'}
    assert row['row_kind'] in {'country', 'subtotal', 'article_total'}
    assert not re.match(r'^(Brought|Carried)\b', row['country_as_printed'])
    assert not re.search(r'\d|[{}]', row['country_as_printed'])
    assert row['unit_as_printed'] not in {'"', ',,', '„'}
    index = int(re.search(r'\bsource row (\d+)', row['note'])[1])
    cells = source[row['table_id']]['rows'][index]
    raw = row['value_as_printed']
    if row['value']:
        assert row['value'] == raw.replace(',', ''), row
        pattern = r'(?<![\d.])'+re.escape(raw)+r'(?!\d)'
        assert any(re.search(pattern, cell) for cell in cells), (row, cells)


def select(table, article, country, measure):
    return [r for r in rows if r['table_id']==table and r['article_as_printed']==article
            and r['country_as_printed']==country and r['measure']==measure]

barley = select('bb1925:p175:t1', 'Grain, barley—', 'British India', 'quantity_total')
assert len(barley)==1 and barley[0]['value']=='2693'
assert barley[0]['unit_as_printed']=='cwt.' and 'unit from ditto' in barley[0]['note']
pulses = select('bb1925:p175:t1', 'Grain, pulses, peas—', 'Belgium', 'quantity_total')
assert len(pulses)==1 and pulses[0]['value']=='13'
assert pulses[0]['country_group_as_printed']=='Foreign Countries—'
assert select('bb1925:p232:t1','Aerated and mineral waters—','Maldivé Islands','quantity_total')[0]['value']=='4380'
assert select('bb1925:p249:t1','Oil, citronella—','Maldiv Islands','value_total_rs')[0]['value']=='289'
assert select('bb1925:p202:t1','Typewriters, parts—','United Kingdom','quantity_total')[0]['unit_as_printed']=='No.'
with (ROOT/'extracted/trade_checks.tsv').open() as f:
    checks = list(csv.DictReader(f, delimiter='\t'))
assert any(r['total_table_id']=='bb1925:p232:t1' and r['measure']=='quantity_total'
           and r['difference_sum_minus_total']=='-70000000' for r in checks)
print('Verified header, source-number provenance, country labels, units, block continuity, paired quantities, and checks.')
print('Measure rows',len(rows))
print('Volumes',dict(Counter(r['year_volume'] for r in rows)))
