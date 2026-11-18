"""Select independent listing samples and write the recorded manual review."""
import argparse
import csv
import json
import random

from extract import Layout, ROOT, get_pages, plain  # Shared CEYLON_OCR_ROOT lookup.

SEEDS = {1: 1922, 2: 1923}
REPAIR_DRAWS = ((4711, (('B', 30), ('C', 10))), (4712, (('B', 20),)))
REPAIR_EXAMPLES = {
    'ferg1922:p468:b6:r5', 'ferg1922:p470:b2:r3',
    'ferg1922:p481:b2:r2', 'ferg1922:p481:b2:r5',
    'ferg1922:p497:b2:r1', 'ferg1922:p499:b2:r2',
    'ferg1922:p467:b3:r0', 'ferg1922:p464:b3:r25',
}


def repair_samples():
    with (ROOT / 'listings.jsonl').open(encoding='utf-8') as src:
        listings = [json.loads(line) for line in src]
    with (ROOT / 'audit.tsv').open(encoding='utf-8', newline='') as src:
        reserved = REPAIR_EXAMPLES | {row['listing_id'] for row in csv.DictReader(src, delimiter='\t')}
    for seed, sections in REPAIR_DRAWS:
        rng = random.Random(seed)
        sample = [row['listing_id'] for section, count in sections for row in rng.sample([
            row for row in listings if row['section'][0] == section and row['listing_id'] not in reserved
        ], count)]
        reserved.update(sample)
        yield sorted(sample, key=lambda key: tuple(int(part[1:]) for part in key.split(':')[1:]))


def read_sample(round_number, manual):
    with (ROOT / 'listings.jsonl').open(encoding='utf-8') as src:
        listings = [json.loads(line) for line in src]
    reserved = set()
    if round_number == 2:
        reserved = set(manual['1'])
    rng = random.Random(SEEDS[round_number])
    count = 20 if round_number == 1 else 10
    return [row for section in 'ABC' for row in sorted(rng.sample([
        row for row in listings if row['section'].startswith(section + '.')
        and row['listing_id'] not in reserved
    ], count), key=lambda row: row['listing_id'])]


def show(sample):
    pages = dict(get_pages({row['pdf_page'] for row in sample}))
    for row in sample:
        locator = row['listing_id']
        page = row['pdf_page']
        block, index = [int(part[1:]) for part in locator.split(':')[-2:]]
        blocks = pages[page]
        raw = blocks[block]
        rows = Layout(raw['content']).rows
        print(locator, row['printed_page'], row['section'], '\n  DATA',
              row['name_as_printed'], row['kind'], row['address_as_printed'], row['town'],
              row['trades'], row['attested'], row['continuation_pages'], row['flags'])
        if rows:
            if row['section'].endswith('LICENSED SURVEYORS.'):
                index, _ = divmod(index, len(rows[0]))
            start = max(0, index - 2) if row['section'][0] != 'B' else index
            end = min(len(rows), index + 1)
            for n in range(start, end):
                parts = [' / '.join(cell) for cell in rows[n]]
                if row['section'][0] == 'B':
                    parts[1] = parts[1][:180]
                    parts[2] = parts[2][:460]
                print('  OCR', n, ' | '.join(parts))
        else:
            print('  OCR', plain(raw))
            if page in (463, 465, 466, 467) and block + 1 < len(blocks):
                print('  NEXT', plain(blocks[block + 1])[:275])


def write_review(manual):
    columns = ('listing_id', 'field', 'extracted', 'agrees', 'comment')
    path = ROOT / 'audit.tsv'
    with path.open('w', encoding='utf-8', newline='') as dst:
        writer = csv.DictWriter(dst, columns, delimiter='\t', lineterminator='\n')
        writer.writeheader()

        def write(locator, field, value, agrees, comment):
            writer.writerow(dict(listing_id=locator, field=field, extracted=value,
                                 agrees='yes' if agrees else 'no', comment=comment))

        for phase, sample in manual.items():
            observations = mismatches = 0
            for locator, review in sample.items():
                errors = review.get('errors', {})
                item_errors = review.get('item_errors', {})
                for field, extracted in review['extracted'].items():
                    observations += 1
                    mismatches += field in errors
                    comment = errors.get(field, review.get('notes', {}).get(field, ''))
                    if field == 'listing_id':
                        comment = f'Round {phase}. ' + review['source']
                    value = json.dumps(extracted, ensure_ascii=False, separators=(',', ':'))
                    if isinstance(extracted, list) and len(value) > 200:
                        write(locator, field, f'[{len(extracted)} items shown in the following rows]',
                              field not in errors, comment)
                        for index, item in enumerate(extracted):
                            detail = f'{field}[{index}]'
                            write(locator, detail, json.dumps(item, ensure_ascii=False),
                                  detail not in item_errors, item_errors.get(detail, ''))
                    else:
                        write(locator, field, value, field not in errors, comment)
            print(f'Round {phase}: {len(sample)} listings, {observations} fields, {mismatches} mismatches')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('round', nargs='?', type=int, choices=[1, 2])
    parser.add_argument('--section', choices='ABC')
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--draw', action='store_true', help='Draw a candidate sample from the current output.')
    parser.add_argument('--repair-sample', type=int, choices=[1, 2],
                        help='Print the listing IDs for the specified repair audit.')
    args = parser.parse_args()
    with (ROOT / 'audit_notes.json').open(encoding='utf-8') as src:
        manual = json.load(src)
    if args.repair_sample:
        print(*list(repair_samples())[args.repair_sample - 1], sep='\n')
    elif args.rebuild:
        write_review(manual)
    elif args.round:
        sample = (read_sample(args.round, manual) if args.draw else
                  [review['extracted'] for review in manual[str(args.round)].values()])
        show([row for row in sample if not args.section or row['section'][0] == args.section])
    else:
        parser.error('supply a round, --rebuild, or --repair-sample')
