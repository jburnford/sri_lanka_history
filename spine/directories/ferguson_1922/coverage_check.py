#!/home/jic823/miniforge3/bin/python
"""Measure OCR token coverage in the Colombo readings."""
from collections import Counter
import csv
import json
import re

from extract import ROOT, Layout, colombo_coordinates, get_pages


TRADE_HEADINGS = ('Import', 'Export', 'Importers of')
STAFF_HEADINGS = ('Assistants per pro', 'COLOMBO STAFF', 'KANDY STAFF',
                  'TALAWAKELLE STAFF', 'RATNAPURA BRANCH')
AGENCY_HEADINGS = ('Principal Correspondents and Agencies', 'Wine & Spirits Agencies',
                   'Life, Fire and Marine')
COLUMN_HEADINGS = ('Firms and Addresses', 'Partners and Assistants',
                   'Principal Correspondents and Agencies')
TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def read_jsonl(path):
    with path.open(encoding='utf-8') as source:
        return [json.loads(line) for line in source]


def source_cells(pages, locator):
    page, block, row = colombo_coordinates(locator)
    layout = Layout(pages[page][block]['content'])
    if not layout.rows:
        return [' '.join(filter(None, layout.lines))]
    return [re.sub(r'(?<=\w)-\n(?=[a-z])', '', '\n'.join(lines))
            for lines in layout.rows[row]]


def field_text(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for part in value:
            yield from field_text(part)


def output_tokens(listing):
    excluded = {'listing_id', 'source_rows', 'source_column', 'source_locator',
                'flags', 'reading_notes', 'role_class', 'relation_class', 'target_kind'}
    rows = [listing, *listing['roles'], *listing['connections']]
    return {word for row in rows for field, value in row.items() if field not in excluded
            for item in field_text(value) for word in words(item)}


def words(text):
    text = re.sub(r'(?<!\w)do\.(?!\w)|[„〃]', '', text, flags=re.IGNORECASE)
    return TOKEN.findall(text.casefold())


def headings_for(listing):
    staff = {row['role_as_printed'] for row in listing['roles']}
    staff.update(row['department_as_printed'] for row in listing['roles'])
    agencies = {row['relation_as_printed'] for row in listing['connections']}
    agencies.update(row['group_heading_as_printed'] for row in listing['connections'])
    labels = staff | agencies | set(TRADE_HEADINGS + STAFF_HEADINGS + AGENCY_HEADINGS + COLUMN_HEADINGS)
    return sorted({tuple(words(label)) for label in labels if label and label != 'listed'},
                  key=lambda label: (-len(label), label))


def without_headings(cell, headings):
    # Match headings at the beginning of a line or before heading punctuation.
    # Count the same words when they occur in names or other facts.
    for label in headings:
        phrase = r'[\W_]+'.join(map(re.escape, label))
        pattern = rf'(?:^[ \t]*{phrase}(?!\w)|(?<!\w){phrase}\s*(?=[:—–]))'
        cell = re.sub(pattern, '', cell, flags=re.IGNORECASE | re.MULTILINE)
    return cell


def measure(listing, pages):
    headings = headings_for(listing)
    source = Counter(word for locator in listing['source_rows']
                     for cell in source_cells(pages, locator)
                     for word in words(without_headings(cell, headings)))
    output = output_tokens(listing)
    matched = sum(count for word, count in source.items() if word in output)
    uncovered = Counter({word: count for word, count in source.items() if word not in output})
    total = source.total()
    return total, matched, matched / total if total else 1, uncovered


def main():
    readings = read_jsonl(ROOT / 'colombo_readings.jsonl')
    pages = dict(get_pages(range(468, 501)))
    with (ROOT / 'coverage_b.tsv').open('w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target, delimiter='\t', lineterminator='\n')
        writer.writerow(('listing_id', 'ocr_words', 'covered_words', 'share', 'uncovered_tokens'))
        for listing in readings:
            total, matched, share, uncovered = measure(listing, pages)
            pointers = ' '.join(sorted(uncovered, key=lambda word: (-uncovered[word], word))[:5])
            writer.writerow((listing['listing_id'], total, matched, f'{share:.6f}', pointers))


if __name__ == '__main__':
    main()
