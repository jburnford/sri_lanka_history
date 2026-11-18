"""Check source provenance, every block's arithmetic, and volume coverage."""
import csv
import gzip
import json
import re
from collections import defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[1]
VOLUMES = '1880 1881 1882 1883 1885 1886 1887 1889b 1890 1891 1892 1893 1894 1896 1897 1898 1899 1900'.split()
COMMODITIES = 'tea coffee cinchona cinnamon coconut_oil plumbago'.split()
FIELDS = {
    'figure': 'commodity year_volume table_id source_row pdf_page article_as_printed heading_above_as_printed country_as_printed row_kind measure unit_as_printed value_as_printed value reading agrees_with_rule_reader note'.split(),
    'measure': 'quantity_ceylon_produce quantity_other_produce quantity_total value_ceylon_produce_rs value_other_produce_rs value_total_rs'.split(),
}
BLOCK_FIELDS = 'commodity article_as_printed year_volume tables_and_rows status countries_read country_sum_quantity printed_total_quantity sum_agrees_quantity country_sum_value printed_total_value sum_agrees_value note'.split()
FRACTIONS = dict(zip('¼½¾⅓⅔⅛⅜⅝⅞', ('1/4', '1/2', '3/4', '1/3', '2/3', '1/8', '3/8', '5/8', '7/8')))
LABELS = re.compile(r'(?i)\b(?:lbs?|cwt|qrs?|rs|r|c|cts|cs|pkgs?|packages?|bags?|gallons?|gals?|no|plantation|chips|trunk|twig|br|and|bales)\.?\b\.?')
NUMBER = re.compile(r'\d+(?:\.\d+)?(?: \d+/\d+)?|\d+/\d+')

def scalar(raw):
    if re.fullmatch(r'(?:\d+ )?\d+/\d+', raw):
        return sum(map(Fraction, raw.split()))
    if not NUMBER.fullmatch(raw):
        raise ValueError(raw)
    return Fraction(raw)

def amount(raw, unit, measure):
    cleaned = LABELS.sub('', raw).replace(' | ', ' ')
    cleaned = re.sub(r'(?<=\d),(?=\d)', '', cleaned)
    cleaned = re.sub(r'\\frac\{(\d+)\}\{(\d+)\}', r' \1/\2', cleaned)
    cleaned = re.sub(r'\s*[†‡*§¶"„]+\s*', ' ', cleaned)
    for glyph, fraction in FRACTIONS.items():
        cleaned = cleaned.replace(glyph, ' ' + fraction)
    cleaned = ' '.join(cleaned.split())
    cells = cleaned.split()
    if measure.startswith('value'):
        if len(cells) != 2 or not all(c.isdigit() for c in cells) or len(cells[1]) > 2:
            raise ValueError('Rupee and cent components are incomplete or ambiguous')
        return Fraction(int(cells[0]) * 100 + int(cells[1]), 100)
    if unit.endswith('cwt qr lb'):
        if len(cells) < 3 or not cells[0].isdigit() or not cells[1].isdigit():
            raise ValueError('Cwt, quarter and pound components are incomplete or ambiguous')
        cwt, qr, lb = int(cells[0]), int(cells[1]), scalar(' '.join(cells[2:]))
        if qr >= 4 or lb >= 28:
            raise ValueError('Quarter or pound component exceeds the printed unit range')
        return cwt + Fraction(qr, 4) + lb / 112
    return scalar(cleaned)

def display(value, unit='', measure=''):
    with localcontext() as context:
        context.prec = 50
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
        if unit.endswith('cwt qr lb'):
            return f'{decimal:.4f}'
        if measure.startswith('value'):
            return f'{decimal:.2f}'
        return format(decimal.quantize(Decimal('0.000000000001')).normalize(), 'f')

def summarize(figures, found):
    if not found:
        return ('not_found', '0', '', '', 'no_total', '', '', 'no_total')
    readable = [f for f in figures if f['reading'] != 'unreadable']
    if not readable:
        status = 'unreadable'
    elif len(readable) < len(figures) or any(f['reading'] == 'doubtful' for f in figures):
        status = 'partly_read'
    else:
        status = 'read'
    countries = {f['country_as_printed'] for f in readable if f['row_kind'] == 'country'}
    country_rows = defaultdict(list)
    for figure in figures:
        if figure['row_kind'] == 'country':
            key = figure['table_id'], figure['source_row'], figure['country_as_printed']
            country_rows[key].append(figure)
    result = [status, str(len(countries))]
    for measure in ('quantity_total', 'value_total_rs'):
        totals = {}
        sums = defaultdict(Fraction)
        for f in readable:
            if f['row_kind'] == 'article_total' and f['measure'] == measure:
                unit = f['unit_as_printed']
                assert unit not in totals, f
                totals[unit] = amount(f['value_as_printed'], unit, measure)
        prefix = measure.split('_', 1)[0] + '_'
        for row in country_rows.values():
            components = [f for f in row if f['measure'].startswith(prefix)]
            printed_totals = [f for f in components if f['measure'] == measure]
            for f in printed_totals or components:
                if f['reading'] != 'unreadable':
                    unit = f['unit_as_printed']
                    sums[unit] += amount(f['value_as_printed'], unit, f['measure'])
        for unit in totals:
            sums.setdefault(unit, Fraction(0))
        def show(values):
            formatted = {unit: display(value, unit, measure) for unit, value in values.items()}
            if len(formatted) < 2:
                return next(iter(formatted.values()), '')
            return json.dumps(formatted, ensure_ascii=False, sort_keys=True)
        result.extend((show(sums), show(totals), ('yes' if sums == totals else 'no') if totals else 'no_total'))
    return tuple(result)

def read_tsv(name, fields):
    with (WORK / name).open(newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        assert reader.fieldnames == fields, (name, reader.fieldnames)
        return list(reader)

def load_sources():
    result = {}
    for volume in VOLUMES:
        with gzip.open(ROOT / 'tables' / f'{volume}.jsonl.gz', 'rt') as handle:
            for line in handle:
                t = json.loads(line)
                result[t['id']] = (volume, t)
    return result

def main():
    sources = load_sources()
    figures = read_tsv('main_exports.tsv', FIELDS['figure'])
    blocks = read_tsv('blocks.tsv', BLOCK_FIELDS)
    pairs = {(block['commodity'], block['year_volume']) for block in blocks}
    assert pairs == {(commodity, volume) for commodity in COMMODITIES for volume in VOLUMES}, pairs
    owners = {}
    grouped = defaultdict(list)
    for index, block in enumerate(blocks):
        for span in block['tables_and_rows'].split():
            table_id, _, indices = span.rpartition(':')
            first, _, last = indices.partition('-')
            volume, source = sources[table_id]
            assert volume == block['year_volume'], block
            assert 0 <= int(first) <= int(last or first) < len(source['rows']), span
            for row in range(int(first), int(last or first) + 1):
                key = block['commodity'], block['article_as_printed'], table_id, row
                assert key not in owners, key
                owners[key] = index
    seen = set()
    for figure in figures:
        table_id, index = figure['table_id'], int(figure['source_row'])
        volume, source = sources[table_id]
        assert volume == figure['year_volume'] and str(source['pdf_page']) == figure['pdf_page'], figure
        assert 0 <= index < len(source['rows']), figure
        cells = source['rows'][index]
        next_column = 0
        for piece in figure['value_as_printed'].split(' | '):
            pattern = r'(?<!\S)' + re.escape(piece) + r'(?!\S)'
            column = next((i for i in range(next_column, len(cells))
                           if re.search(pattern, cells[i])), None)
            assert piece and column is not None, (figure, cells)
            next_column = column + 1
        assert figure['measure'] in FIELDS['measure'], figure
        assert figure['reading'] in ('clear', 'doubtful', 'unreadable'), figure
        assert figure['agrees_with_rule_reader'] in ('yes', 'no', 'not_read_by_it'), figure
        assert figure['row_kind'] in ('country', 'article_total'), figure
        if figure['row_kind'] == 'article_total':
            assert not figure['country_as_printed'], figure
        elif figure['reading'] != 'unreadable':
            assert figure['country_as_printed'], figure
        if figure['reading'] == 'unreadable':
            assert not figure['value'] and figure['note'], figure
        else:
            unit, measure = figure['unit_as_printed'], figure['measure']
            assert figure['value'] == display(amount(figure['value_as_printed'], unit, measure), unit, measure), figure
        key = figure['commodity'], figure['article_as_printed'], table_id, index
        identity = (*key, figure['country_as_printed'], figure['row_kind'],
                    figure['measure'], figure['unit_as_printed'])
        assert identity not in seen, figure
        seen.add(identity)
        grouped[owners[key]].append(figure)
    for index, block in enumerate(blocks):
        actual = tuple(block[key] for key in BLOCK_FIELDS[4:-1])
        expected = summarize(grouped[index], bool(block['tables_and_rows']))
        assert expected == actual, (block, expected)
    print(f'Checked {len(figures)} figure records, {len(blocks)} blocks, and {len(pairs)} commodity-volume pairs.')

if __name__ == '__main__':
    main()
