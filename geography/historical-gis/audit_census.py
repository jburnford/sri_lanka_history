#!/usr/bin/env python3
"""Reconcile transcribed census totals without editing input data.

Run: python3 audit_census.py
Use --output FILE to save a TSV with formula inputs, differences and citations.
Use --review-only to emit only checks needing interpretation.
"""
import argparse
import csv
from fractions import Fraction
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
METRICS = {
    '': 'population', '_male': 'population_male', '_female': 'population_female',
    '_houses': 'occupied_houses', '_buildings': 'habitable_buildings',
    '_literate_male': 'literates_male', '_literate_female': 'literates_female',
}
COLS = (
    'check_id', 'source_id', 'year', 'metric', 'unit', 'total_row', 'printed_total',
    'component_sum', 'difference', 'rounding_allowance', 'status', 'note',
    'total_locator', 'source_url', 'components',
)


def read(name):
    with (HERE / f'{name}.tsv').open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


SOURCES = {r['source_id']: r['url'] for r in read('sources')}


def number(text):
    if text in (None, '', '..'):
        return None
    return sum((Fraction(x) for x in text.replace(',', '').removeprefix('W').split()), Fraction())


def display(value):
    return '' if value is None else str(value)


def key(label):
    name = label.lower().removeprefix('province of ').removesuffix(' province')
    return re.sub(r'[^a-z0-9]+', '-', name).strip('-')


def location(row, fallback=''):
    return row.get('locator') or row.get('page') or fallback


def entry(row, column, fallback='', multiplier=1):
    value = number(row.get(column))
    return row['name'], value * multiplier if value is not None else None, location(row, fallback)


def check(identifier, source, year, metric, total, components, *, url='', allow=0, note='',
          unit='persons'):
    """Use total minus sum. Blanks remain missing, even in partial subtotals."""
    label, reported, locator = total
    values = [x[1] for x in components]
    missing = reported is None or not values or any(x is None for x in values)
    subtotal = sum(x for x in values if x is not None)
    difference = None if missing else reported - subtotal
    if missing:
        status = 'missing input'
    elif difference == 0:
        status = 'exact'
    elif abs(difference) <= allow:
        status = 'rounding compatible'
    else:
        status = 'human review'
    link = url or SOURCES[source]
    p = re.search(r'PDF p\. (\d+)', locator)
    if p and '.pdf' in link.lower() and '#page=' not in link:
        link += '#page=' + p[1]
    return dict(zip(COLS, (
        f'{source}:{year}:{identifier}:{metric}', source, year, metric, unit, label,
        display(reported), display(subtotal) if values else '', display(difference),
        display(allow), status, note, locator, link,
        json.dumps([{'row': n, 'value': display(v), 'locator': l} for n, v, l in components],
                   ensure_ascii=False),
    )))


def numeric_unit(metric):
    return {'occupied_houses': 'houses', 'habitable_buildings': 'buildings',
            'area': 'square miles'}.get(metric, 'persons')


def sex_checks(source, rows, years, fallback=''):
    for r in rows:
        for y in years:
            col = str(y)
            label, total, loc = entry(r, col, fallback)
            parts = [(label + ' — ' + k, number(r.get(col + '_' + k)), loc)
                     for k in ('male', 'female')]
            if total is None and all(x[1] is None for x in parts):
                continue  # These intentionally unassigned grouped cells are documented in the scan audits.
            yield check(r.get('feature_id') or key(label), source, y, 'population',
                        (label, total, loc), parts, url=r.get('source_url') or '')


def area_hierarchy(source, rows, year, columns, fallback='', rounding=None):
    country = next(r for r in rows if r['kind'] == 'country')
    provinces = [r for r in rows if r['kind'] == 'province']
    children = [r for r in rows if r['kind'] == 'district' or r.get('feature_id') == 'urban:colombo']
    for column, metric in columns:
        for total in [country, *provinces]:
            parts = provinces if total is country else [
                r for r in children if key(r['parent']) == key(total.get('unit_name') or total['name'])
            ]
            assert parts, (source, total['name'])
            allow = rounding(total, parts) if rounding else 0
            note = ('Colombo Municipality is separate from the Colombo District remainder in this table.'
                    if any(r.get('feature_id') == 'urban:colombo' for r in parts) else '')
            if rounding:
                note = (note + ' Area is printed at mixed precision. Allow up to half of each last displayed unit.').strip()
            if source == 'census-1891' and metric == 'area' and key(total['name']) == 'north-western':
                note += (' The printed Chilaw area is obscured. The remainder is 262 square miles; '
                         'this is an inference and was not entered as a printed value.')
            if source == 'gazette-9533' and year == 1931 and total is country:
                note = ('The printed Ceylon total is eight above the listed provinces. '
                        'The final report repeats the discrepancy. Retain both totals as printed.')
            yield check('subtotals:' + key(total['name']), source, year, metric,
                        entry(total, column, fallback), [entry(r, column, fallback) for r in parts],
                        url=total.get('source_url') or '', allow=allow, note=note, unit=numeric_unit(metric))


def checks():
    # Compare within each volume and reporting geography. Do not combine different vintages by name alone.
    for source, table, years, suffixes in (
        ('census-1891', 'census_1891_comparison', (1881, 1891), ('', '_male', '_female')),
        ('census-1901-table-iv', 'census_1901_comparison', (1871, 1881, 1891, 1901),
         ('', '_male', '_female', '_houses')),
    ):
        rows = read(table)
        yield from sex_checks(source, rows, years)
        for y in years:
            yield from area_hierarchy(source, rows, y, [(f'{y}{s}', METRICS[s]) for s in suffixes])

    yield from area_hierarchy(
        'census-1891', read('census_1891_area_density'), 1891, [('1891_area_sq_mi', 'area')],
        rounding=lambda total, parts: sum(
            Fraction(1, 2 * (number(r['1891_area_sq_mi']) or Fraction()).denominator)
            for r in [total, *parts]
        ),
    )

    # 1891 Chilaw house subtotal on the 1901 scan. Other three component rows are not imported
    # as observations; their original values are included explicitly for reproducibility.
    source = 'census-1901-table-iv'
    rows = {r['feature_id']: r for r in read('census_1901_comparison')}
    p28 = 'Table IV, p. 28, CRL scan 026'
    yield check('subtotals:chilaw-district-detail', source, 1891, 'occupied_houses',
                entry(rows['district:chilaw'], '1891_houses'),
                [entry(rows['urban:chilaw'], '1891_houses'),
                 ('Pitigal Korale North', 2218, p28), ('Pitigal Korale Central', 4934, p28),
                 ('Pitigal Korale South', 4539, p28)],
                url=rows['urban:chilaw']['source_url'], unit='houses',
                note='District summary on p. 25 (CRL scan 024); Local Board and other components on p. 28.')

    yield from sex_checks('census-1911-towns', read('census_1911_towns'), (1901, 1911))
    source = 'census-1921'
    p13 = 'PDF p. 13'
    rows = read('census_1921')
    yield from sex_checks(source, rows, (1911, 1921), p13)
    # These two enumerations appear separately after the province totals. Dots for the Basses
    # female and both buildings fields represent no contribution, not imputed district data.
    outside_provinces_1921 = {
        '': (743, 8), '_male': (653, 8), '_female': (90, 0), '_buildings': (0, 0),
        '_literate_male': (594, 7), '_literate_female': (45, 0),
    }
    for y in (1911, 1921):
        for suffix, values in outside_provinces_1921.items():
            col, metric = f'{y}{suffix}', METRICS[suffix]
            parts = [entry(r, col, p13) for r in rows if r['kind'] == 'province']
            note = '1911 provincial figures adjusted as necessary for area changes.'
            if y == 1921:
                parts += [(label, value, p13) for label, value in zip(('Train', 'Basses'), values)]
                note = 'Includes printed Train and Basses rows outside the provincial subtotal.'
            yield check('subtotals:ceylon', source, y, metric, entry(rows[0], col, p13), parts,
                        note=note, unit=numeric_unit(metric))

    source = 'gazette-9533'
    gazette = read('census_gazette')
    for r in gazette:
        r['locator'] = f"p. {r['page']}, PDF p. {int(r['page']) - 488}"
    for y in (1931, 1946):
        yield from area_hierarchy(source, gazette, y, [(str(y), 'population')])

    source = 'census-1946-final'
    final = {int(r['year']): {**r, 'name': 'Ceylon', 'locator': 'Table 3, p. 57, PDF p. 87'}
             for r in read('census_dates')}
    provinces = [r for r in read('census_1946_final') if r['kind'] == 'province']
    districts = read('census_1946_districts')
    for y in (1931, 1946):
        yield check('subtotals:ceylon', source, y, 'population', entry(final[y], 'population'),
                    [entry(r, str(y)) for r in provinces],
                    note=('The printed Ceylon total is eight above the listed provinces. '
                          'The provisional Gazette repeats the discrepancy. Retain both totals as printed.'
                          if y == 1931 else ''))
    for y in (1921, 1946):
        district_page = '1946 final Table 97, p. 147, PDF p. 195'
        for province in provinces:
            parts = []
            for r in districts:
                if key(r['parent']) == key(province['name']):
                    parts.extend((r['name'] + ' — ' + sex, number(r[f'{y}_{sex}']), district_page)
                                 for sex in ('male', 'female'))
            total_source = source if y == 1946 else 'census-1921'
            reference = province if y == 1946 else next(
                r for r in rows if r['kind'] == 'province' and key(r['name']) == key(province['name']))
            yield check('subtotals:district-counts:' + key(province['name']), total_source, y, 'population',
                        entry(reference, str(y), p13), parts,
                        note='District sex counts in 1946 final Table 97, PDF p. 195. '
                             '1921 cross-publication comparisons are informational.')

    source = 'dcs-table-2.1'
    dcs = read('census_dcs')
    for y in (1871, 1881, 1891, 1901, 1911, 1921, 1931, 1946):
        loc = 'Table 2.1, PDF p. 1'
        included = [r for r in dcs[1:] if r[str(y)] not in ('..', '')]
        yield check('subtotals:sri-lanka', source, y, 'population',
                    entry(dcs[0], str(y), loc, 1000),
                    [entry(r, str(y), loc, 1000) for r in included], allow=50 * (len(included) + 1),
                    note=('Thousands display to 0.1; compare in persons with ±50 per independently rounded cell. '
                          'The table groups historical districts as published; all-dot rows do not contribute. '
                          '1931 Mannar carries an unexplained W marker in print.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Write TSV to FILE instead of stdout')
    parser.add_argument('--review-only', action='store_true', help='Exclude exact and rounding-compatible checks')
    args = parser.parse_args()
    data = list(checks())
    assert len({r['check_id'] for r in data}) == len(data), 'non-unique check identifiers'
    matched = [r for r in data if not args.review_only or r['status'] in ('human review', 'missing input')]
    if args.output:
        with args.output.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, COLS, delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(matched)
    else:
        writer = csv.DictWriter(sys.stdout, COLS, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(matched)


if __name__ == '__main__':
    main()
