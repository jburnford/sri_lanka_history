#!/home/jic823/miniforge3/bin/python
"""Extract factual fields from the specified 1922 directory OCR."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SOURCE = Path(
    '/mnt/data/jic823/ocr_chandra/out_chandra2/1922-fergusons-ceylon-directory_4e422995/'
    '1922-fergusons-ceylon-directory/1922-fergusons-ceylon-directory_layout.jsonl'
)


def clean(value):
    return re.sub(r'\s+', ' ', value).strip()


class Layout(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.lines = ['']
        self.rows = []
        self.row = self.cell = None
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.row = []
        if tag in ('td', 'th'):
            self.cell = ['']
        if tag in ('br', 'p', 'li', 'div'):
            self.lines.append('')
            if self.cell is not None:
                self.cell.append('')

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None and self.row is not None:
            self.row.append([clean(line) for line in self.cell if clean(line)])
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag in ('p', 'li', 'div'):
            self.lines.append('')
            if self.cell is not None:
                self.cell.append('')

    def handle_data(self, value):
        if self.cell is not None:
            self.cell[-1] += value
        self.lines[-1] += value


def get_pages(wanted):
    with SOURCE.open(encoding='utf-8') as source:
        for line in source:
            page = json.loads(line)
            number = int(page['pdf_page'])
            if number in wanted:
                yield number, page['blocks']


def plain(block):
    return clean(' '.join(Layout(block['content']).lines))


def printed_page(blocks):
    for block in blocks:
        if block['label'] == 'Page-Header':
            header = plain(block)
            if header.isdecimal():
                return int(header)
    return None


def inspect(pages, indices=None):
    for page, blocks in get_pages(pages):
        print(f'\n=== {page} / {printed_page(blocks)} ===')
        for index, block in enumerate(blocks):
            if indices is not None and index not in indices:
                continue
            layout = Layout(block['content'])
            print(f"{index} {block['label']}", end=' ')
            if layout.rows:
                print()
                for row, cells in enumerate(layout.rows):
                    print(f'{row}:', ' | '.join(' / '.join(cell) for cell in cells))
            else:
                print(' / '.join(clean(line) for line in layout.lines if clean(line)))


def fact(value):
    value = clean(value)
    value = re.sub(r'\s*\.{2,}$', '', value).strip()
    return value if value and not re.fullmatch(r'[ .…—–-]+', value) else None


def joined(lines):
    return re.sub(r'(?<=\w)- (?=[a-z])', '', ' '.join(lines))


def address_ditto(value, previous):
    if not value or not previous:
        return value
    match = re.fullmatch(r'(.*?)(?:\bdo\.?|[„〃]+)', value, re.I)
    if not match:
        return value
    prefix = match[1]
    street = re.sub(r'^(?:[\dA-Za-z& ,.-]+, )(?=[A-Za-z])', '', previous, count=1)
    # Keep the street only when the previous prefix contains a house number.
    if not previous[0].isdigit():
        street = previous
    return prefix + street


def trade_terms(value):
    value = fact(value.strip(' ,.;()'))
    if not value:
        return []
    value = re.sub(r',?\s*\b(?:etc\.?|&c\.?)$', '', value, flags=re.I).strip(' ,;')
    terms = re.split(r'[,;]|\s+and\s+(?=(?:[A-Z]|[a-z]+(?:ers|ors)\b))', value)
    return [term.strip(' .()') for term in terms if term.strip(' .()')]


BODY = re.compile(r'\b(?:Co\b|Ltd\b|Ld\b|Limited\b|Bros\b|Brothers\b|Sons\b|Stores?\b|'
                  r'Warehouse\b|Works\b|Company\b|Bank\b|Society\b|Hotel\b|Suisse\b|'
                  r'Hall\b|Pharmacy\b|Dispensary\b|Emporium\b|Establishment\b|Depôt\b|Press\b|Seminary\b)', re.I)
OCR_DAMAGE = re.compile(r"\b(?:Colom' o|Bunga'ow|P\. rad-niya|Mata'e|Katuke'e|Ho'el|Laid'aw|"
                        r"Mil on|B\. at\b|[A-Z]ad-r|Cul-r|Ba'oha|M-rikar|A'ttygalle|Sarna is|"
                        r"\w+ z Bhai|San's|Ampitiya \[|Wharf\s*\?\?)")


def damage(*values):
    return ['ocr_doubtful'] if any(v and (OCR_DAMAGE.search(v) or '�' in v) for v in values) else []


def kind_of(name):
    if re.search(r'\bBank\b', name, re.I):
        return 'bank'
    if re.search(r'\b(?:Society|Seminary)\b', name, re.I):
        return 'association'
    return 'firm' if BODY.search(name) or '&' in name else 'sole trader'


HONORIFIC = re.compile(r'^(?:The\s+)?(?:Hon\.?|M(?:rs|r|iss)\.?|Madame|Dr\.?|Sir|Lady|'
                       r'Lieut\.?[- ]?Col\.?|Col\.?|Capt\.?|Rev\.?|Major|H\.? E\.?)\s+', re.I)
POST = re.compile(r'(?:,?\s+)((?:[A-Z]{1,5}\.){2,}[A-Z.]*|J\.P\.(?:M\.M\.C\.)?|A\.?M\.?I\.?E\.?E\.?)$')
ROLE_WORDS = (
    r'Managing Director|Managing Proprietress|Managing Proprietor|Managing Partner|'
    r'General Manager|Acting General Manager|Acting Manager|Assistant(?:s| Manager| Engineer| Secretary)?|'
    r'Asst\.? (?:Manager|Engineer|Secretary)|Chief Clerk|Chief Assistant|'
    r'Joint Managers?|Kandy Manager|Colombo Manager|Resident Engineer|'
    r'Manager(?:s| pro| in Kandy| Kandy| and Director| and Cutter)?|'
    r'Agent(?:s| and Manager)?|Sub-Agent|Propriet(?:or(?:s)?|ress)|'
    r'Partner(?:s)?|Director(?:s)?|Secretary|Treasurer|Chairman|Vice-Chairman|'
    r'President|Vice-President|Member(?:s)?|Accountant|Shroff|Cashier|Book-keeper|'
    r'Engineer|Foreman|Draper|Cutter|Chemist|Milliner|Dressmaker'
)
ROLE_RE = re.compile(r'^(?:' + ROLE_WORDS + r')\b', re.I)
PERSON_START = r'(?:Mr\.? |Mrs\.? |Miss |Dr\.? |Madame |[A-Z]\. |[A-Z][a-z]+ [A-Z]\.)'


def person_parts(value):
    name = value
    titles = []
    while (match := HONORIFIC.match(name)):
        titles.append(match.group().strip())
        name = name[match.end():]
    while (match := POST.search(name)):
        titles.append(match[1])
        name = name[:match.start()].rstrip(' ,')
    words = name.split()
    if not words:
        return None, None, titles
    start = len(words) - 1
    while start > 0 and words[start - 1].lower() in ('de', 'la', 'le', 'van', 'von', 'der', 'den', 'da'):
        start -= 1
    return ' '.join(words[start:]), ' '.join(words[:start]) or None, titles


def role_class(role):
    role = role.lower()
    if 'propriet' in role or role == 'owner':
        return 'owner'
    if 'partner' in role:
        return 'partner'
    if 'manager' in role or 'managing director' in role:
        return 'manager'
    if re.search(r'chairman|president|secretary|treasurer|director|committee|auditor|trustee', role):
        return 'officer'
    if 'member' in role:
        return 'member'
    if 'licen' in role:
        return 'licensee'
    if role == 'listed':
        return 'unknown'
    return 'staff'


def role_entries(value):
    value = re.sub(r'\[[^\]]*(?:See|see)[^\]]*\]', '', value)
    value = re.sub(r'\bKandy Staff:\s*[—–-]*', '', value)
    value = re.sub(r'(?<=\bAgent)\s+(?=Chief Clerk,)', '; ', value)
    parts = re.split(r';|\.\s+(?=' + PERSON_START + r')(?<=[a-z]\. )', value)
    pending = None
    for part in parts:
        part = part.strip(' .;') if not part.strip().endswith('.') else part.strip(' ;')
        if not fact(part):
            continue
        lead = re.match(r'^(' + ROLE_WORDS + r')[:,.]\s+(.+)', part, re.I)
        if lead:
            pending = lead[1]
            part = lead[2]
        items = re.split(r',\s+(?=' + PERSON_START + r')|\s+(?:and|&)\s+(?=' + PERSON_START + r')', part)
        named = []
        for item in items:
            if not fact(item):
                continue
            inline = list(re.finditer(r',?\s+(' + ROLE_WORDS + r')(?=[.,; ]|$)', item, re.I))
            if inline:
                match = inline[0]
                person = item[:match.start()].strip(' ,()')
                title = item[match.start(1):].strip(' ,.')
                if title.endswith(' Colombo') or title.endswith(', Colombo'):
                    title = title.removesuffix(' Colombo').rstrip(',')
                if person:
                    named.append((person, title))
            else:
                named.append((item.strip(' ,()'), pending or 'listed'))
        if len(named) > 1 and named[-1][1].lower() in ('partners', 'managers', 'proprietors', 'assistants'):
            named = [(name, named[-1][1]) for name, _ in named]
        yield from named
        pending = None


class Extraction:
    def __init__(self):
        self.listings = []
        self.roles = []
        self.connections = []
        self.skipped = {}
        self.overrides = {}
        override_file = ROOT / 'overrides.json'
        if override_file.exists():
            self.overrides = json.loads(override_file.read_text(encoding='utf-8'))

    def override(self, key):
        return self.overrides.get(key, {}).get('fields', {})

    def listing(self, sect, heading, page, printed, block, row, name, address=None,
                town=None, trades=None, kind=None, attested=None, flags=()):
        key = f'ferg1922:p{page}:b{block}:r{row}'
        entry = dict(listing_id=key, section=f'{sect}. {heading}', pdf_page=page,
                     printed_page=printed, name_as_printed=name, kind=kind or kind_of(name),
                     address_as_printed=address, town=town, trades=trades or [],
                     attested=attested, continues_from=None, continuation_pages=[],
                     flags=sorted(set(flags) | set(damage(name, address))))
        entry.update(self.override(key).get('listing', {}))
        self.listings.append(entry)
        return entry

    def role(self, listing, page, name, role='listed', year=None, column=None, flags=()):
        if not name:
            return
        surname, given, titles = person_parts(name)
        key = listing['listing_id']
        record = dict(role_id=f'{key}:role{len(self.roles_for(key)) + 1}',
                      listing_id=key, person_as_printed=name, surname=surname,
                      given_or_initials=given, honorifics=titles, role_as_printed=role,
                      role_class=role_class(role), year=year, pdf_page=page,
                      source_column=column, flags=sorted(set(flags) | set(damage(name))))
        self.roles.append(record)

    def roles_for(self, key):
        return [row for row in self.roles if row['listing_id'] == key]

    def connection(self, listing, page, relation, relation_class, target,
                   target_kind='unknown', place=None, qualifier=None, flags=()):
        if not fact(target):
            return
        key = listing['listing_id']
        number = 1 + sum(row['listing_id'] == key for row in self.connections)
        self.connections.append(dict(
            connection_id=f'{key}:conn{number}', listing_id=key,
            relation_as_printed=relation, relation_class=relation_class, target_as_printed=target,
            target_kind=target_kind, target_place_as_printed=place, qualifier=qualifier,
            pdf_page=page, flags=sorted(set(flags) | set(damage(target, place)))))

    def people(self, listing, page, value, column, entries=None):
        if entries is None:
            entries = role_entries(value)
        for name, role in entries:
            if BODY.search(name) or re.search(r'\b(?:Department|Dept|See Advt)\b', name):
                continue
            self.role(listing, page, name, role, column=column)

    def save(self):
        for filename, rows in (('listings', self.listings), ('roles', self.roles),
                               ('connections', self.connections)):
            with (ROOT / f'{filename}.jsonl').open('w', encoding='utf-8') as output:
                for row in rows:
                    output.write(json.dumps(row, ensure_ascii=False) + '\n')
        ids = {row['listing_id'] for row in self.listings}
        unique = all(len(rows) == len({row[key] for row in rows}) for rows, key in (
            (self.listings, 'listing_id'), (self.roles, 'role_id'), (self.connections, 'connection_id')))
        dangling = [row for row in self.roles + self.connections if row['listing_id'] not in ids]

        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for item in value.values():
                    yield from strings(item)
            elif isinstance(value, list):
                for item in value:
                    yield from strings(item)

        long = [(next(iter(row.values())), key, len(value)) for row in
                self.listings + self.roles + self.connections for key, item in row.items()
                for value in strings(item) if len(value) > 200]
        sections = {row['listing_id']: row['section'][0] for row in self.listings}
        counts = {s: {tag: sum(sections[row['listing_id']] == s for row in rows)
                      for tag, rows in (('listings', self.listings), ('roles', self.roles),
                                        ('connections', self.connections))}
                  for s in sorted(set(sections.values()))}
        result = dict(unique_ids=unique, valid_references=not dangling, fields_at_most_200=not long,
                      dangling_references=dangling, overlong_fields=long, counts=counts, skipped=self.skipped)
        (ROOT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False))
        if not all((unique, not dangling, not long)):
            raise SystemExit(1)


def short_name(value):
    value = re.sub(r'\s*[—–-]?\s*\(See Advt\.\)\.?', '', value, flags=re.I)
    return fact(value.rstrip(' ,;'))


A_TRADES = {
    'Bankers.': ['Bankers'], 'European Storekeepers.': ['Storekeepers'],
    'Engineers, &c.': ['Engineers'], 'Merchants.': ['Merchants'],
    'NATIVE SHOPKEEPERS, STOREKEEPERS, ETC.': ['Shopkeepers', 'Storekeepers'],
    'Hotels.': ['Hotels'], 'BOOK-SELLERS AND STATIONERS.': ['Book-sellers', 'Stationers'],
    'CHEMISTS AND DRUGGISTS.': ['Chemists', 'Druggists'],
    'COACH BUILDERS, FARRIERS, SADDLERS, &c': ['Coach builders', 'Farriers', 'Saddlers'],
    'MILLINERS AND DRESSMAKERS.': ['Milliners', 'Dressmakers'],
    'LIQUOR LICENSEES. / WHOLESALE.': ['Wholesale liquor licensees'],
    'LIQUOR LICENSEES. / RETAIL.': ['Retail liquor licensees'],
    'Tavern Licenses. / Foreign Liquor': ['Tavern licenses', 'Foreign liquor'],
    'TAILORING ESTABLISHMENTS, &c': ['Tailoring establishments'],
    'FLORISTS, &c.': ['Florists'],
}


def extract_a(data):
    for page, blocks in get_pages(range(548, 556)):
        printed = printed_page(blocks)
        heading = main = ''
        for block, raw in enumerate(blocks):
            label = raw['label']
            if label == 'Section-Header':
                heading = plain(raw)
                if block == 2:
                    main = heading
                elif page == 553 and block in (14, 16):
                    heading = 'LIQUOR LICENSEES. / ' + heading
                elif page == 553 and block == 20:
                    heading = 'Tavern Licenses. / ' + heading
                continue
            if label != 'Table' and (page, block) not in {(551, 6), (551, 7), (552, 12), (552, 14), (554, 8)}:
                continue
            layout = Layout(raw['content'])
            rows = layout.rows
            if not rows:
                value = plain(raw).replace('St., Kandy Cycle', 'St.; Kandy Cycle')
                parts = [value] if page == 551 else value.split(';')
                rows = []
                for part in parts:
                    match = re.split(r'\s+\.{2,}\s+|,\s+(?!Ltd\.|Ld\.)', part, maxsplit=1)
                    rows.append([[cell] for cell in match])
            has_header = page <= 550 or (page, block) == (551, 4)
            column = joined(rows[0][1]) if has_header else None
            previous_name = previous_address = previous_trade = previous_job = None
            for index, cells in enumerate(rows):
                if has_header and not index:
                    continue
                if heading == 'LICENSED SURVEYORS.':
                    for column_index, cell in enumerate(cells):
                        name = fact(joined(cell))
                        if name:
                            listing = data.listing('A', f'{main} / {heading}', page, printed, block,
                                                   index * len(cells) + column_index, name, town='Kandy',
                                                   trades=['Licensed surveyors'])
                            data.role(listing, page, name, 'Licensed Surveyor', column=heading)
                    continue
                key = f'ferg1922:p{page}:b{block}:r{index}'
                override = data.override(key)
                if override.get('skip'):
                    continue
                values = [fact(joined(cell)) for cell in cells]
                name = short_name(values[0] or '')
                if not name:
                    continue
                roles = values[1] if has_header else None
                address = values[-1] if len(values) > 1 else None
                if page == 549 and block == 6:
                    address = None
                if name == 'do':
                    name = previous_name
                address = address_ditto(address, previous_address)
                previous_name = name
                if address:
                    previous_address = address
                trades = A_TRADES.get(heading, [heading.rstrip('.').capitalize()])
                if page == 548 and block == 6 or page == 549 and block == 4:
                    name, *tail = re.split(r',\s+(?!Ltd\b|Sons\b|Laidlaw\b|Campbell\b)', name, maxsplit=1)
                    if tail:
                        description = re.split(r'\s+\(See Advt', tail[0])[0]
                        trades = trade_terms(description.replace('etc. (Distemper and Paints)', 'Distemper and Paints'))
                if roles and (roles.startswith('(') or roles == 'do'):
                    if roles != 'do':
                        previous_trade = trade_terms(roles)
                    trades = previous_trade or trades
                    roles = None
                elif page == 550:
                    previous_trade = None
                if page == 551 and block == 9:
                    job = previous_job if values[1] == 'do' else values[1]
                    previous_job = job
                    trades = trade_terms(job)
                    override = dict(override, roles=[[name, job]])
                if page in (552, 554) and (page, block) in {(552, 8), (554, 16)}:
                    roles = values[2]
                if '(Veda Arachchi)' in name:
                    name = name.split(' (', 1)[0]
                    override = dict(override, roles=[[name, 'Veda Arachchi']])
                flags = ['ocr_doubtful'] if page == 551 else []
                if name is None:
                    continue
                listing = data.listing('A', f'{main} / {heading}', page, printed, block, index, name,
                                       address, 'Kandy', trades, flags=flags)
                entries = override.get('roles')
                if roles or entries:
                    data.people(listing, page, roles or '', override.get('column', column or heading), entries)
                elif override.get('self_role', not has_header and kind_of(name) == 'sole trader'):
                    data.role(listing, page, listing['name_as_printed'], column=heading)
                for relation, cls, target, kind, place in override.get('connections', []):
                    data.connection(listing, page, relation, cls, target, kind, place)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', nargs='+', type=int)
    parser.add_argument('--blocks', nargs='+', type=int)
    parser.add_argument('--section', choices=['A'])
    args = parser.parse_args()
    if args.inspect:
        inspect(args.inspect, args.blocks)
        return
    data = Extraction()
    extract_a(data)
    data.save()


if __name__ == '__main__':
    main()
