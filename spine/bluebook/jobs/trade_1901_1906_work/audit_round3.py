"""Recheck all three samples and count the changes on the full 1901–1906 run."""
import collections
import csv
import gzip
import json
import re
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[1]
sys.path.insert(0, str(ROOT))
from read_trade_old import GROUP, REVIEWED_CHILDREN, flow_of, name_key

FIELDS = ('article_as_printed', 'class_as_printed', 'group_as_printed',
          'country_as_printed', 'country_group_as_printed', 'unit_as_printed',
          'measure', 'value_as_printed', 'component')
REVISED = {
    10: dict(unit_as_printed='cwt.'), 11: dict(unit_as_printed='cwt.'),
    13: dict(article_as_printed='Arms— Guns, double'),
    14: dict(article_as_printed='Arms— Guns, double'),
    22: dict(article_as_printed='Printing Materials'),
    37: dict(article_as_printed='Arms— Guns, double'),
    45: dict(article_as_printed='Fruit, fresh— Grapes'),
    46: dict(article_as_printed='Meat, frozen— Poultry and Game'),
    51: dict(article_as_printed='Yellow Metal', country_as_printed='Mauritius'),
    54: dict(country_as_printed='British India', value_as_printed='68688'),
    72: dict(measure='quantity_ceylon_produce', component='chips'),
    76: dict(group_as_printed='(3) Other (b) Miscellaneous'),
    80: dict(group_as_printed='(3) Other'), 81: dict(group_as_printed='(3) Other'),
    84: dict(article_as_printed='Fruit, fresh— Grapes'),
    90: dict(value_as_printed='—'),
    100: dict(unit_as_printed='reams'),
    101: dict(unit_as_printed='cases'), 102: dict(unit_as_printed='cases'),
    103: dict(unit_as_printed='cases'),
    121: dict(value_as_printed=''),
    124: dict(value_as_printed='42', component=''),
    125: dict(component=''),
    131: dict(class_as_printed='IV.—Bullion and Coin', group_as_printed=''),
    132: dict(class_as_printed='IV.—Bullion and Coin', group_as_printed=''),
    148: dict(unit_as_printed='Bars'),
    151: dict(unit_as_printed='cwt.', country_group_as_printed='British Colonies'),
    165: dict(group_as_printed='(3) Other (b) Miscellaneous'),
    166: dict(group_as_printed='(3) Other (b) Miscellaneous'),
    167: dict(group_as_printed='(3) Other (c) Timber, unworked'),
    168: dict(group_as_printed='(3) Other (c) Timber, unworked'),
    170: dict(country_group_as_printed='British Colonies'),
    184: dict(article_as_printed='Meat, frozen— Mutton'),
    238: dict(country_group_as_printed='British Colonies'),
    274: dict(group_as_printed='(3) Other (b) Miscellaneous'),
}


def read(path):
    open_table = gzip.open if path.suffix == '.gz' else open
    with open_table(path, 'rt', encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def write(name, rows, fields=None):
    with (WORK / name).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fields or list(rows[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def source(row):
    return row['table_id'], int(re.search(r'source row (\d+)', row['note'])[1])


def component(row):
    return next((part.removeprefix('component ') for part in row['note'].split('; ')
                 if part.startswith('component ')), '')


def index(rows, key):
    result = collections.defaultdict(list)
    for row in rows:
        result[key(row)].append(row)
    return result


def comparable(value):
    return ' '.join(re.sub(r'\s*[—–]\s*', '— ', value).strip(' .').lower().split())


before = read(WORK / 'round3_before_trade_1880_1906.tsv.gz')
after = read(ROOT / 'extracted/trade_1880_1906.tsv.gz')
skipped_before = read(WORK / 'round3_before_trade_1880_1906_skipped.tsv')
skipped_after = read(ROOT / 'extracted/trade_1880_1906_skipped.tsv')
old_sources, new_sources = index(before, source), index(after, source)
skip_sources = index(skipped_after, lambda row: (row['table_id'], int(row['row_index'])))
skip_reasons = {key: sorted({row['reason'] for row in rows}) for key, rows in skip_sources.items()}
old_measures = index(before, lambda row: (*source(row), row['measure']))
new_measures = index(after, lambda row: (*source(row), row['measure']))
verdicts = {r['sample_number']: r for suffix in ('a', 'b')
            for r in read(WORK / f'scan_check3_results_{suffix}.tsv')}
results = []
for sample in read(WORK / 'scan_check3_sample.tsv'):
    number = sample['sample_number']
    checked = verdicts[number]
    key = source(sample)
    assert checked['table_id'] == key[0]
    old_key = (*key, sample['measure'])
    assert any(all(r[f] == sample[f] for f in FIELDS[:-1]) and component(r) == component(sample)
               for r in old_measures[old_key]), (number, key)
    expected = {f: sample[f] for f in FIELDS[:-1]}
    expected['component'] = component(sample)
    expected.update(REVISED.get(int(number), {}))
    measure_matches = new_measures[(*key, expected['measure'])]
    matches = [r for r in measure_matches if component(r) == expected['component']]
    result = dict(sample, source_row=key[1], old_verdict=checked['verdict'],
                  what_the_page_shows=checked['what_the_page_shows'],
                  original_measure_matches=len(new_measures[old_key]), matched_measure_count=len(matches))
    assert len(matches) < 2, (number, key, matches)
    actual = {}
    if matches:
        row = matches[0]
        actual = {f: row[f] for f in FIELDS[:-1]}
        actual['component'] = component(row)
        result['new_value'] = row['value']
        result['new_note'] = row['note']
    else:
        result['new_value'] = result['new_note'] = ''
    diffs = [f'{f}: expected {expected[f]!r}, got {actual[f]!r}' for f in actual
             if comparable(expected[f]) != comparable(actual[f])]
    reasons = skip_reasons.get(key, [])
    if not actual:
        assert reasons, (number, key, 'withholding needs a skip record')
        judgement, explanation = 'withheld', ' | '.join(reasons)
    elif checked['verdict'] == 'cannot_tell':
        judgement, explanation = 'cannot tell', 'The scan leaves the figure ambiguous.'
    elif diffs:
        judgement, explanation = 'disagrees', ' | '.join(diffs)
    else:
        judgement, explanation = 'agrees', 'The relocated figure and reviewed labels agree.'
    result.update({f'new_{field}': actual.get(field, '') for field in FIELDS})
    result.update({f'expected_{field}': expected[field] for field in FIELDS})
    result.update(judgement=judgement, judgement_reason=explanation)
    results.append(result)
assert len(results) == len(verdicts) == len({r['sample_number'] for r in results}) == 279
write('recheck3.tsv', results)

# Compare the older audits with the actual round-two results, keeping their
# original expectations and listing earlier disagreements now withheld too.
worse = []
earlier_counts = {}
ranking = {'yes': 2, 'no': 1, 'cannot tell': 1, 'removed from output': 0}
for label, old_name, new_name in (
        ('first', 'round3_before_recheck.tsv', 'recheck.tsv'),
        ('second', 'round3_before_recheck2.tsv', 'recheck2.tsv')):
    previous, current = read(WORK / old_name), read(WORK / new_name)
    assert len(previous) == len(current)
    earlier_counts[label] = [collections.Counter(r['judgement'] for r in rows)
                             for rows in (previous, current)]
    for old, new in zip(previous, current):
        assert old['sample_number'] == new['sample_number']
        if ranking[new['judgement']] >= ranking[old['judgement']]:
            continue
        key = new['table_id'], int(new['source_row'])
        worse.append(dict(audit=label, sample_number=new['sample_number'], table_id=key[0],
                          source_row=key[1], before=old['judgement'], after=new['judgement'],
                          old_article=old['new_article'], new_article=new['new_article'],
                          reason=' | '.join(skip_reasons.get(key, [])) or new['judgement_reason']))
write('recheck_round3_earlier_regressions.tsv', worse,
      ('audit', 'sample_number', 'table_id', 'source_row', 'before', 'after',
       'old_article', 'new_article', 'reason'))

tables = {}
for year in range(1901, 1907):
    with gzip.open(ROOT / f'tables/{year}.jsonl.gz', 'rt') as f:
        tables.update((table['id'], table) for table in map(json.loads, f)
                      if flow_of(table, wide_exports=True))

for row in after:
    tid, i = source(row)
    cells = tables[tid]['rows'][i]
    raw = row['value_as_printed']
    tokens = {re.sub(r'^Rs\.?\s*', '', cell).strip() for cell in cells}
    tokens.update(token for cell in cells for token in cell.split())
    assert not raw or raw in tokens, (tid, i, raw, cells)
    assert not row['value'] or row['value'] == raw.replace(',', ''), row
assert list(before[0]) == list(after[0])
assert list(skipped_before[0]) == list(skipped_after[0])

# Enumerate every country-group marker with figures, including markers that
# share a braced second line or actually share the previous article's total.
markers = []
for tid, table in tables.items():
    for i, (_, country, *figures) in enumerate(table['rows']):
        country = re.sub(r'^(?:\.{2,}|…)[\s.…]*', '', country)
        group = GROUP.match(country)
        if not group or not any(re.search(r'\d', raw) for raw in figures):
            continue
        tail = re.sub(r'^(?:\.{2,}|…)[\s.…]*', '', country[group.end():].strip())
        if tail and not tail.startswith('{'):
            continue
        key = tid, i
        rows = new_sources[key]
        if rows:
            disposition = next((text for phrase, text in (
                ('alignment verified against the page', 'reassociated'),
                ('verified as the previous article total', 'verified total'),
                ('second unit line of the same country', 'braced second line'),
            ) if any(phrase in row['note'] for row in rows)), 'unclassified output')
        else:
            disposition = 'withheld'
        markers.append(dict(table_id=tid, source_row=i, country_cell=country,
                            figures=json.dumps(figures, ensure_ascii=False), disposition=disposition,
                            skip_reason=' | '.join(skip_reasons.get(key, []))))
write('round3_country_markers.tsv', markers)
assert all(m['disposition'] != 'unclassified output' and
           (m['disposition'] != 'withheld' or m['skip_reason']) for m in markers), markers

def scoped_skips(prefix):
    return {key for key, reasons in skip_reasons.items() if any(r.startswith(prefix) for r in reasons)}


def measures_at(keys, sources):
    return sum(len(sources[key]) for key in keys)


def counts(test):
    return [sum(test(row) for row in rows) for rows in (before, after)]


affected = scoped_skips('country alignment uncertain')
group_affected = scoped_skips(('group number disagrees', 'subgroup letter disagrees'))
cinnamon = lambda row: name_key(row['article_as_printed']).endswith('cinnamonplantation')
tea = lambda row: row['flow'] == 'export' and row['article_as_printed'] == 'Tea'
blank_unit = lambda row: row['measure'].startswith('quantity') and not row['unit_as_printed']
tea_1902 = lambda row: tea(row) and row['year_volume'] == '1902'
tea_plain = lambda row: row['table_id'] == 'bb1903:p687:t1' and tea(row)
recovered_units = [r for r in after if r['measure'].startswith('quantity') and r['unit_as_printed']
                   and any(blank_unit(old) and old['value_as_printed'] == r['value_as_printed']
                           for old in old_measures[(*source(r), r['measure'])])]
subset = lambda tid, i, m: [r['value_as_printed'] for r in new_measures[(tid, i, m)]]
assert subset('bb1902:p607:t1', 17, 'value_total_rs') == ['900']
assert subset('bb1902:p607:t1', 18, 'value_total_rs') == ['87']
assert subset('bb1903:p635:t1', 25, 'value_total_rs') == ['1']
assert all(r['unit_as_printed'] == 'lb.' for r in after if tea_1902(r) and r['measure'].startswith('quantity'))
assert all(r['measure'] == 'quantity_ceylon_produce' for r in after if component(r))
assert not any(component(r) and tea_plain(r) for r in after)
assert all(not new_sources[key] for key in group_affected)

metrics = {
    'output_measure_rows': [len(before), len(after)],
    'A_marker_candidates': collections.Counter(m['disposition'] for m in markers),
    'A_markers_by_volume': collections.Counter(m['table_id'][2:6] for m in markers),
    'A_marker_tables': len({m['table_id'] for m in markers}),
    'A_takeouts_source_rows': len(affected),
    'A_braced_takeouts_source_rows': len(scoped_skips('country alignment uncertain: displaced braced')),
    'A_takeouts_measure_rows': [measures_at(affected, rows) for rows in (old_sources, new_sources)],
    'A_Yellow_Metal_reviewed_shift_measure_rows': [measures_at({('bb1902:p607:t1', i) for i in (17,18,19)}, rows)
                                                  for rows in (old_sources, new_sources)],
    'B_Cinnamon_components': counts(lambda r: cinnamon(r) and bool(component(r))),
    'B_Cinnamon_other_quantity': counts(lambda r: cinnamon(r) and r['measure'] == 'quantity_other_produce'),
    'B_Cinnamon_cropped_value_totals': len(scoped_skips('Cinnamon value_total_rs missing')),
    'B_Cinnamon_unreadable_source_rows': len(scoped_skips('Cinnamon component columns')),
    'B_Tea_components': counts(lambda r: tea(r) and bool(component(r))),
    'B_p687_plain_Tea_components': counts(lambda r: tea_plain(r) and bool(component(r))),
    'B_Port_China_quantity_cells': [sum(r['measure'].startswith('quantity')
                                       for r in rows[('bb1903:p635:t1',25)])
                                    for rows in (old_sources, new_sources)],
    'C_bare_named_leaves_in_reviewed_groups': {},
    'C_full_names_in_reviewed_groups': {},
    'C_Printing_Materials': counts(lambda r: r['article_as_printed'] == 'Printing Materials'),
    'C_Printing_Materials_relocated_from_split': sum(
        r['article_as_printed'] == 'Printing Materials'
        and any(o['article_as_printed'] in ('Printing', 'Materials')
                for o in old_measures[(*source(r), r['measure'])]) for r in after),
    'D_blank_quantity_units': counts(blank_unit),
    'D_retained_quantities_new_unit': len(recovered_units),
    'D_units_by_evidence': collections.Counter(
        'ditto' if 'ditto' in r['note'] else 'carried or explicit'
        for r in recovered_units),
    'D_units_extracted_with_first_quantity_source_rows': len({
        source(r) for r in after if 'unit printed beside the first quantity' in r['note']}),
    'E_reviewed_conflict_source_rows': len(group_affected),
    'E_reviewed_conflict_measure_rows': [measures_at(group_affected, rows) for rows in (old_sources, new_sources)],
    'E_literal_number_as_nested_subgroup': counts(lambda r: bool(re.search(
        r'\(3\) Other\s+\(\d+\) (?:Miscellaneous|Timber)', r['group_as_printed']))),
    'E_Pearls_group_leak': counts(lambda r: r['article_as_printed'] == 'Pearls and Precious Stones'
                                 and bool(r['group_as_printed'])),
    'F_Gibraltar_Green_dash': counts(lambda r: source(r) == ('bb1903:p682:t1',37)
                                   and component(r) == 'green' and r['value_as_printed'] == '—'),
    'G_1902_Tea': counts(tea_1902),
    'G_1902_Tea_by_page': collections.Counter(r['table_id'] for r in after if tea_1902(r)),
    'G_1902_Tea_source_rows': len({source(r) for r in after if tea_1902(r)}),
    'G_1902_Tea_lost_value_totals': sum(tid == 'bb1902:p650:t1' for tid, _ in scoped_skips('tea value_total_rs missing')),
    'G_1902_Tea_unreadable_source_rows': sum(tid in ('bb1902:p650:t1','bb1902:p651:t1')
                                          for tid, _ in scoped_skips('tea component columns')),
    'new_recheck': collections.Counter(r['judgement'] for r in results),
    'new_recheck_by_old_verdict': {v: collections.Counter(r['judgement'] for r in results if r['old_verdict'] == v)
                                  for v in sorted({r['old_verdict'] for r in results})},
    'earlier_rechecks': earlier_counts,
    'numeric_provenance_errors': 0,
}
for parent, children in REVIEWED_CHILDREN.items():
    group = 'Other' if parent == 'Arms' else 'Food and Drink'
    # Homonyms such as fresh Fish outside the specific heading can remain bare.
    leaves = ('Guns, double',) if parent == 'Arms' else ('Grapes',) if parent == 'Fruit, fresh' else ('Mutton','Poultry and Game')
    metrics['C_bare_named_leaves_in_reviewed_groups'][parent] = counts(
        lambda r: group in r['group_as_printed'] and r['article_as_printed'] in leaves)
    metrics['C_full_names_in_reviewed_groups'][parent] = counts(
        lambda r: r['article_as_printed'] in {parent + '— ' + leaf for leaf in children})
(WORK / 'round3_audit_summary.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(metrics, ensure_ascii=False, indent=2))
