#!/home/jic823/miniforge3/bin/python
"""Extract factual fields from the specified 1922 directory OCR."""
import argparse
from collections import Counter
import csv
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
OCR_ROOTS = (Path('/home/jic823/ceylon/ocr_chandra/out_chandra2'),
             Path('/mnt/data/jic823/ocr_chandra/out_chandra2'))
OCR_LAYOUT = Path(
    '1922-fergusons-ceylon-directory_4e422995/'
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
    root = os.environ.get('CEYLON_OCR_ROOT')
    if root is None:
        root = next((path for path in OCR_ROOTS if (path / OCR_LAYOUT).is_file()), OCR_ROOTS[0])
    with (Path(root) / OCR_LAYOUT).open(encoding='utf-8') as source:
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
    value = re.sub(r',?\s*(?:\betc\.?|&c\.?)$', '', value, flags=re.I).strip(' ,;')
    terms = re.split(r'[,;]|\s+and\s+(?=(?:[A-Z]|[a-z]+(?:ers|ors)\b))', value)
    return [term.strip(' .()') for term in terms if term.strip(' .()')]


BODY = re.compile(r'\b(?:Co\b|Ltd\b|Ld\b|Limited\b|Bros\b|Brothers\b|Sons\b|Stores?\b|'
                  r'Warehouse\b|Works\b|Company\b|Bank\b|Society\b|Hotel\b|Suisse\b|'
                  r'Hall\b|Pharmacy\b|Dispensary\b|Emporium\b|Establishment\b|Depôt\b|Press\b|Seminary\b)', re.I)
OCR_DAMAGE = re.compile(r"\b(?:Colom' o|Bunga'ow|P\. rad-niya|Mata'e|Katuke'e|Ho'el|Laid'aw|"
                        r"Mil on|B\. at\b|[A-Z]ad-r|Cul-r|Ba'oha|M-rikar|A'ttygalle|Sarna is|"
                        r"\w+ z Bhai|San's|Ampitiya \[|Wharf\s*\?\?|Dispensary, Tho|Oilmanatores|Whitcaway|Molchanoff, P\. ch atnoff)")


def damage(*values):
    return ['ocr_doubtful'] if any(v and (OCR_DAMAGE.search(v) or '�' in v) for v in values) else []


def kind_of(name):
    if re.search(r'\bBank\b', name, re.I):
        return 'bank'
    if re.search(r'\b(?:Society|Seminary)\b', name, re.I):
        return 'association'
    return 'firm' if BODY.search(name) or '&' in name else 'sole trader'


HONORIFIC = re.compile(r'^(?:The\s+)?(?:Hon\.?|M(?:rs|r|iss)\.?|Madame|Dr\.?|Sir|Lady|'
                       r'Lieut\.?[- ]?Col\.?|Col\.?|Capt\.?|Rev\.?|Mlle\.?|Major)\s+', re.I)
POST_INITIALISMS = (
    'JPMMC', 'JP', 'MMC', 'ACA', 'FCA', 'CA', 'ASAA', 'AMIEE', 'AMIES', 'AMICE',
    'BA', 'MA', 'MPS', 'UPM', 'GBVC', 'CCS',
)
POST_TITLE = r'(?:' + '|'.join(
    (r'\.\s*' if len(title) == 2 else r'\.?\s*').join(title) + r'\.?' for title in POST_INITIALISMS
) + (
    r'|Esq\.?|Gate Muhandiram)'
)
POST = re.compile(r'(?:\s*,\s*|\s+&\s+|\s+)(' + POST_TITLE + r')$', re.I)
DOUBTFUL_INITIALS = r'(?:[A-Z]\.\s*|[A-Z] ){2,}[A-Z]\.?'
DOUBTFUL_POST = re.compile(r', ' + DOUBTFUL_INITIALS + r'$')
SUFFIX_ABBREVIATION = re.compile(
    r"(?:^|[\s,(])(?:[A-Z]|Ltd|Ld|Co|Cos|Bros|Jr|Junr|Sr|St|Ste|Inc|Cie|"
    r"Ests|Ges|Dept|Assn|Corp|etc|[A-Za-z](?:\.\s*[A-Za-z])+|Esq)\.$", re.I
)
PER_PRO = re.compile(r'\bper\s+pro\b\.?', re.I)


def trim_full_stop(value):
    if value is None:
        return None
    value = value.rstrip()
    if value.endswith('.') and not SUFFIX_ABBREVIATION.search(value):
        return value[:-1].rstrip()
    return value


def signatory(value):
    value, count = PER_PRO.subn('', value)
    value = re.sub(r'\s*\(\s*\)', '', value)
    return clean(value).strip(' ,;'), bool(count)
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
PERSON_START = r'(?:Mr\.? |Mrs\.? |Miss |Dr\.? |Madame |[A-Z]\. |[A-Z][a-z]+ [A-Z]\.)'


def person_parts(value):
    name = value
    titles = []
    while (match := HONORIFIC.match(name)):
        titles.append(match.group().strip())
        name = name[match.end():]
    trailing = []
    while (match := POST.search(name)):
        trailing.append(match[1])
        name = name[:match.start()].rstrip(' ,&')
    titles.extend(reversed(trailing))
    name = DOUBTFUL_POST.sub('', name)
    name = trim_full_stop(name)
    words = name.split()
    if not words:
        return None, None, titles
    start = len(words) - 1
    while start > 0 and words[start - 1].lower() in ('de', 'la', 'le', 'van', 'von', 'der', 'den', 'da'):
        start -= 1
    if words[-1].lower().rstrip('.') in ('saibo', 'chetty', 'rawther', 'hadjar', 'lebbe', 'effendi', 'sahib'):
        while start > 0 and not re.fullmatch(r'[A-Z]\.?', words[start - 1]):
            start -= 1
    return ' '.join(words[start:]).rstrip(','), ' '.join(words[:start]) or None, titles


def role_class(role):
    role = role.lower()
    if 'propriet' in role or role == 'owner':
        return 'owner'
    if 'partner' in role:
        return 'partner'
    if 'manager' in role or 'managing director' in role:
        return 'manager'
    if re.search(r'chairman|president|secretar|treasurer|director|committee|auditor|trustee|representative', role):
        return 'officer'
    if 'member' in role:
        return 'member'
    if 'licen' in role:
        return 'licensee'
    if role in ('listed', 'acting'):
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
        self.dropped_phrases = Counter()
        self.source_locator = None
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
                     printed_page=printed, name_as_printed=name, other_names_as_printed=[],
                     kind=kind or kind_of(name),
                     address_as_printed=address, town=town, trades=trades or [],
                     attested=attested, continues_from=None, continuation_pages=[],
                     flags=sorted(set(flags) | set(damage(name, address))))
        entry.update(self.override(key).get('listing', {}))
        entry['name_as_printed'] = trim_full_stop(entry['name_as_printed'])
        self.listings.append(entry)
        return entry

    def role(self, listing, page, name, role='listed', year=None, column=None, flags=(), per_pro=False):
        if not name:
            return
        name, signed = signatory(name)
        name = trim_full_stop(name)
        surname, given, titles = person_parts(name)
        if DOUBTFUL_POST.search(name) and not POST.search(name):
            flags = [*flags, 'ocr_doubtful']
        key = listing['listing_id']
        record = dict(role_id=f'{key}:role{len(self.roles_for(key)) + 1}',
                      listing_id=key, person_as_printed=name, surname=surname,
                      given_or_initials=given, honorifics=titles, role_as_printed=role,
                      role_class=role_class(role), per_pro=per_pro or signed, year=year, pdf_page=page,
                      source_column=column, source_locator=self.source_locator or key, flags=sorted(set(flags) | set(damage(name))))
        self.roles.append(record)

    def roles_for(self, key):
        return [row for row in self.roles if row['listing_id'] == key]

    def connection(self, listing, page, relation, relation_class, target,
                   target_kind='unknown', place=None, qualifier=None, flags=(), address=None):
        if not fact(target):
            return
        target, target_flags = overflow(target)
        place, place_flags = overflow(place)
        address, address_flags = overflow(address)
        key = listing['listing_id']
        number = 1 + sum(row['listing_id'] == key for row in self.connections)
        self.connections.append(dict(
            connection_id=f'{key}:conn{number}', listing_id=key,
            relation_as_printed=relation, relation_class=relation_class,
            target_as_printed=trim_full_stop(target), target_kind=target_kind,
            target_place_as_printed=trim_full_stop(place), target_address_as_printed=trim_full_stop(address),
            qualifier=qualifier,
            pdf_page=page, source_locator=self.source_locator or key,
            flags=sorted(set(flags) | set(target_flags + place_flags + address_flags + damage(target, place, address)))))

    def people(self, listing, page, value, column, entries=None):
        if entries is None:
            entries = role_entries(value)
        for name, role in entries:
            if BODY.search(name) or re.search(r'\b(?:Department|Dept|See Advt)\b', name):
                continue
            self.role(listing, page, name, role, column=column)

    def save(self):
        datasets = (('listings', self.listings, 'listing_id'),
                    ('roles', self.roles, 'role_id'),
                    ('connections', self.connections, 'connection_id'))
        ids = {row['listing_id'] for row in self.listings}
        all_ids = [row[key] for _, rows, key in datasets for row in rows]
        unique = len(all_ids) == len(set(all_ids))
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
        audit_long = []
        for audit_name in ('audit.tsv', 'audit_repair1.tsv', 'audit_reread.tsv'):
            audit_path = ROOT / audit_name
            if not audit_path.exists():
                continue
            with audit_path.open(encoding='utf-8', newline='') as audit:
                for row in csv.DictReader(audit, delimiter='\t'):
                    for key, value in row.items():
                        if len(value) > 200:
                            audit_long.append((row['listing_id'], key, len(value)))
        result = dict(unique_ids=unique, valid_references=not dangling, fields_at_most_200=not (long or audit_long),
                      dangling_references=dangling, overlong_fields=long, overlong_audit_fields=audit_long,
                      counts=counts, relation_class_counts=dict(sorted(Counter(
                          row['relation_class'] for row in self.connections).items())),
                      role_class_counts=dict(sorted(Counter(row['role_class'] for row in self.roles).items())),
                      honorific_values=sorted({value for row in self.roles for value in row['honorifics']},
                                               key=lambda value: (value.casefold(), value)),
                      dropped_phrases=dict(sorted(self.dropped_phrases.items())), skipped=self.skipped)
        (ROOT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False))
        if not all((unique, not dangling, not long, not audit_long)):
            raise SystemExit(1)
        for filename, rows, _ in datasets:
            target = ROOT / f'{filename}.jsonl'
            staged = target.with_suffix('.jsonl.tmp')
            with staged.open('w', encoding='utf-8') as output:
                for row in rows:
                    output.write(json.dumps(row, ensure_ascii=False) + '\n')
            staged.replace(target)


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
                elif override.get('self_role', listing['kind'] == 'sole trader' and (not has_header or page == 550)):
                    data.role(listing, page, listing['name_as_printed'], column=heading)
                for relation, cls, target, kind, place in override.get('connections', []):
                    data.connection(listing, page, relation, cls, target, kind, place)


CO_SUFFIX = re.compile(r'(?i)\b(?:Co|Cos|Company|Corporation|Inc|Ltd|Ld|Limited|Bros|Brother[s]?|Sons|Cie|'
                       r'Association|Society|Syndicate|Insurance|Assurance|Bank|Works|Steamers|Line|Estates|'
                       r'Plantations|Factories|Factory|Railway|Mills|Kaisha)\b')
PLACES = re.compile(
    r'(?:London|New York(?: City)?|Glasgow|Manchester|Liverpool|Birmingham|Edinburgh|'
    r'Calcutta|Bombay|Madras|Cochin|Karachi|Karaobi|Rangoon|Colombo|Kandy|Galle|'
    r'Sydney|Melbourne|Adelaide|Perth|Brisbane|Wellington|Auckland|Dunedin|Christchurch|'
    r'Bale & Paris|Paris|Marseilles?|Hamburg|Bordeaux|Copenhagen|Amsterdam|Zurich|Berlin|Rotterdam|'
    r'Yokohama|Tokio|Tokyo|Osaka|Kobe|Japan|Penang|Singapore|Shanghai|Hankow|Foochow|'
    r'China|Havana|Canton|Hongkong|Montreal|Toronto|Vancouver|Boston|Chicago|Seattle|'
    r'San Francisco|Philadelphia|Antwerp|England|Europe|Australia|India|Ceylon|'
    r'Burma|Switzerland|Scotland|Ireland|Belfast|Beyrouth|Victoria|Belgium|Argentina|'
    r'New Zealand|Wellington|Henselo|The Hague|Helmond|Widnes|Northwich|Kallai|Genoa|'
    r'Delhi|Moscow|Petrograd|Riga|Manritus|Chungking|Johannesburg|Manila|Hobart|'
    r'Detroit|Akron|Utrecht|Dundee|Port Sunlight|Port Elizabeth|Mauritius|Sundaan|Jesselton|'
    r'F\.M\.S\.|U\.?\s*S\.?\s*A\.?|E\.?\s*C\.?\s*\d*|S\.?\s*E\.?|B\.C\.)'
)
POSTAL_DISTRICT = r'[NSEW](?:\.?\s*[WEC])?\.?(?:\s*\d+)?'
STREET_WORD = r'(?:Streets?|St\.|Roads?|Rd\.|Lanes?|Pavement|Avenue|Buildings?|House|Gate|Circle|Court|Place|Axe|Square)'
STREET_END = re.compile(r'\b' + STREET_WORD + r'(?=\W|$)', re.I)
HOUSE_NUMBER = r'\d+(?:[-/]\d+)*(?:[A-Za-z])?'
ADDRESS_START = re.compile(r'^(?:' + HOUSE_NUMBER + r'(?:\s*(?:,|&)\s*' + HOUSE_NUMBER +
                           r')*(?=[, ]|$)|[^,;]{2,65}\b' + STREET_WORD + r'(?=[, .]|$))', re.I)
TOWN_END = re.compile(r'(?<!\w)(?P<town>' + PLACES.pattern +
                      r')(?:,\s*(?P<district>' + POSTAL_DISTRICT + r'))?(?=[.;, ]|$)')
def overflow(value):
    if value is None or '[' not in value and ']' not in value:
        return value, []
    value = re.sub(r'\bPetro-\s*\[grad\b', 'Petrograd', value)
    # OCR sometimes repeats a complete suffix alongside its overflow.
    value = re.sub(r'(\b(?:Co\.?,\s*)?(?:Ltd|Ld)\.?)\s+[\[(](?:(?:Co\.?,\s*)?(?:Ltd|Ld)\.?|Co\.?)'
                   r'(?=\s|$)', r'\1', value, flags=re.I)
    value = re.sub(r'(?<=,)\s*\[(?=(?:Co\.?(?:,\s*(?:Ltd|Ld)\.?)?|Ltd\.?|Ld\.?)'
                   r'(?:\s|$))', ' ', value, flags=re.I)
    if '[' in value or ']' in value:
        return clean(value.replace('[', '').replace(']', '')), ['ocr_doubtful']
    return value, []


def target_kind_of(value, relation=None):
    if re.search(r'\b(?:Assurance|Insurance|Underwriters|Lloyd.s)\b', value, re.I):
        return 'insurer'
    if re.search(r'\bBank\b|\bBanking Corporation\b', value, re.I):
        return 'bank'
    if re.search(r'Steamers?|Steamship|Shipping|Steam Navigation|\bS\.\s*S\.|\bB\.\s*I\.\s*S\.\s*N\.|\bLine\b|Kisen Kaisha|Fleet', value, re.I):
        return 'shipping line'
    if re.search(r'\b(?:Ests\.?|Estates?|Plantations?)\b|\b(?:Tea|Rubber|Coconut|Cocoanut) (?:Co\b|Company|Syndicate)', value, re.I):
        return 'estate company'
    if relation == 'shipping_agent':
        return 'shipping line'
    if CO_SUFFIX.search(value) or '&' in value and not re.match(PERSON_START, value):
        return 'company'
    if re.match(PERSON_START, value):
        return 'person'
    return 'unknown'


def street_and_place(value, default_place=None, office=False):
    """Return a street and locality when the printed boundary is recognizable."""
    value = value.strip(' ,;')
    for location in TOWN_END.finditer(value):
        street = value[:location.start()].rstrip(' ,')
        if not street or not (ADDRESS_START.match(street) or STREET_END.search(street)):
            continue
        tail = value[location.end():].strip(' .,')
        if tail and not (office and PLACES.fullmatch(tail)):
            continue
        place = location['town'] if office else value[location.start():]
        if default_place and re.fullmatch(POSTAL_DISTRICT, place):
            place = default_place if office else default_place + ', ' + place
        return street, place
    if ADDRESS_START.match(value) or STREET_END.search(value):
        postal = re.search(r',?\s+(' + POSTAL_DISTRICT + r')\.?$', value)
        if postal and default_place:
            return value[:postal.start()].rstrip(' ,'), (
                default_place if office else default_place + ', ' + postal[1])
        if postal and office:
            return value[:postal.start()].rstrip(' ,'), None
        return value, default_place
    return None, value or default_place


def company_chunks(line):
    """Separate runs of names while keeping business suffixes and printed places."""
    for part in re.split(r';|\s+and for\s+|\s+[—–]\s+', line):
        if not (part := fact(part.strip(' ,;'))):
            continue
        fragments = re.split(r'(?i)(?<=\bLtd\.) (?=[A-Z])|(?<=\bLd\.) (?=[A-Z])|(?<=\bInc\.) (?=[A-Z])', part)
        if len(fragments) > 1:
            combined = []
            for current in fragments:
                if combined and re.match(PLACES.pattern + r'(?:[ ,.]|$)', current) and (',' not in current or not CO_SUFFIX.search(current)):
                    combined[-1] += ' ' + current
                else:
                    combined.append(current)
            fragments = combined
        for fragment in fragments:
            start = 0
            for m in re.finditer(r',\s+(?:and\s+)?', fragment):
                head = fragment[start:m.start()]
                tail = fragment[m.end():]
                if head.count('(') > head.count(')') or ADDRESS_START.match(tail) or re.match(
                    r'&\s+' + HOUSE_NUMBER + r'[, ]', tail
                ):
                    continue
                if re.match(r'(?:of|for|from)\s', tail, re.I):
                    continue
                if not CO_SUFFIX.search(head) or re.match(r'^(?:Ltd\b|Ld\b|Limited\b|Inc\b|Prptry\b|\(|\[)', tail, re.I):
                    continue
                begins_place = re.match(PLACES.pattern + r'(?:[ ,.]|$)', tail)
                if begins_place and not CO_SUFFIX.search(tail.split(',', 1)[0]) or re.fullmatch(
                    POSTAL_DISTRICT + r'\.?', tail
                ):
                    continue
                if re.search(r'[A-Z](?:[A-Za-z]|\.)', tail) and (CO_SUFFIX.search(tail) or
                        re.search(r'(?:,|\s)' + PLACES.pattern + r'\.?$', head)):
                    if head.strip():
                        yield head.strip(' ,')
                    start = m.end()
            if fragment[start:].strip(' ,'):
                yield fragment[start:].strip(' ,')


def split_target(value, default_place=None, ditto_place=None):
    value, flags = overflow(value)
    value = re.sub(r'\s*\((?:See Adv[st]?\.?|which see)\)', '', value, flags=re.I)
    value = re.sub(r'\s*[—–-]+\s*See Adv.*$', '', value, flags=re.I).strip(' ,;')
    suffix = re.search(r',?\s+([„〃"]+)$', value)
    if suffix:
        return value[:suffix.start()].rstrip(' ,'), ditto_place, None, flags if ditto_place else ['ocr_doubtful']
    if re.search(r'\?\?+|\betc\.', value, re.I):
        flags.append('ocr_doubtful')
    for comma in re.finditer(r',\s*', value):
        prefix, suffix = value[:comma.start()], value[comma.end():]
        if prefix and ADDRESS_START.match(suffix) and (
            STREET_END.search(suffix) or re.match(HOUSE_NUMBER + r'[, ]', suffix)
        ):
            offices = re.split(r',\s*&\s+(?=' + HOUSE_NUMBER + r'[, ])', suffix)
            if len(offices) > 1:
                pairs = [street_and_place(office, default_place) for office in offices]
                if all(address and place for address, place in pairs):
                    return prefix, '; '.join(place for _, place in pairs), (
                        '; '.join(address for address, _ in pairs)), flags
            address, place = street_and_place(suffix, default_place)
            if address:
                return prefix, place, address, flags
    location = re.search(r'(?:[,.;]\s+|\s+of\s+|\s+)(?=' + PLACES.pattern + r'(?:[, .]|$))', value)
    if location and location.start() > 1:
        tail = value[location.end():].strip(' ,')
        if not any((location[0].strip(), re.match(r'\s*,', value[location.end() + len(tail):]))) and re.search(
            r'^(?:Ceylon|India|China|England|Scotland|Australia)\b', tail
        ) and ',' not in tail:
            return value, default_place, None, flags
        prefix = value[:location.start()].strip(' ,')
        if location[0].strip() == 'of' and (re.search(r'\bBank$', prefix) or re.fullmatch(
                r'(?:Ceylon|India|China|England|Scotland|Australia)\.?', tail)):
            return value, default_place, None, flags
        if not re.match(r'^(?:The|of)\s+', tail) and not CO_SUFFIX.search(tail) and not re.match(r'^(?:Co\.|Ltd)', tail):
            if ' of ' not in location[0] or not CO_SUFFIX.search(tail):
                return prefix, tail, None, flags
    return value, default_place, None, flags


B_HEADING = 'LIST OF COLOMBO MERCHANTS AND AGENTS.'
B_LOCATOR = re.compile(r'ferg1922:p(\d+):b(\d+):r(\d+)$')
B_RECORD_TYPES = (
    ('roles', 'role_id', 'role', (
        'person_as_printed', 'surname', 'given_or_initials', 'honorifics', 'role_as_printed',
        'role_class', 'per_pro', 'department_as_printed', 'location_as_printed', 'source_column', 'flags',
    )),
    ('connections', 'connection_id', 'conn', (
        'relation_as_printed', 'relation_class', 'target_as_printed', 'target_kind',
        'target_place_as_printed', 'target_address_as_printed', 'group_heading_as_printed', 'qualifier', 'flags',
    )),
)
B_LISTING_FIELDS = (
    'name_as_printed', 'other_names_as_printed', 'kind', 'address_as_printed',
    'town', 'trades', 'flags', 'reading_notes',
)
B_DROPPED_PHRASES = {'ferg1922:p481:b2:r2': 1}


def colombo_coordinates(locator):
    match = B_LOCATOR.fullmatch(locator)
    if not match or not 468 <= int(match[1]) <= 500:
        raise ValueError(f'Invalid Colombo source locator: {locator}')
    return tuple(map(int, match.groups()))


def extract_b(data):
    with (ROOT / 'colombo_readings.jsonl').open(encoding='utf-8') as source:
        readings = [json.loads(line) for line in source]
    listing_ids = [row['listing_id'] for row in readings]
    if len(listing_ids) != 153 or sorted(set(listing_ids), key=colombo_coordinates) != listing_ids:
        raise ValueError('Expected 153 unique Colombo readings in PDF order')

    printed = {page: printed_page(blocks) for page, blocks in get_pages(range(468, 501))}
    for reading in readings:
        key = reading['listing_id']
        page, _, _ = colombo_coordinates(key)
        sources = reading['source_rows']
        if not sources or len(sources) != len(set(sources)):
            raise ValueError(f'Expected unique source rows for {key}')
        source_pages = {locator: colombo_coordinates(locator)[0] for locator in sources}
        continuation_sources = [locator for locator, p in source_pages.items() if p > page]
        entry = dict(listing_id=key, section=f'B. {B_HEADING}', pdf_page=page,
                     printed_page=printed[page], attested='corrected to December 1921',
                     continues_from=None, source_rows=sources,
                     continuation_pages=sorted({source_pages[locator] for locator in continuation_sources}))
        if continuation_sources:
            entry['continuation_sources'] = continuation_sources
        entry.update({field: reading[field] for field in B_LISTING_FIELDS})
        data.listings.append(entry)
        for stem, id_field, suffix, fields in B_RECORD_TYPES:
            output = getattr(data, stem)
            for number, row in enumerate(reading[stem], 1):
                locator = row['source_locator']
                record = {id_field: f'{key}:{suffix}{number}', 'listing_id': key,
                          'pdf_page': source_pages[locator], 'source_locator': locator}
                if stem == 'roles':
                    record['year'] = None
                elif row['qualifier'] != row['group_heading_as_printed']:
                    raise ValueError(f'Mismatched Colombo agency group in {key} at record {number}')
                record.update({field: row[field] for field in fields})
                output.append(record)
    data.dropped_phrases.update(B_DROPPED_PHRASES)


CHAMBER = 'CEYLON CHAMBER OF COMMERCE'
FIRE = 'Ceylon Fire Insurance Association.'
MARINE = "Colombo Marine Insurance Agents' Association."


def c_chamber(data, page, printed, blocks):
    for block, heading_index in ((3, 2), (5, 4), (7, 6)):
        heading = plain(blocks[heading_index])
        rows = Layout(blocks[block]['content']).rows
        previous = []
        listing = None
        for row, cells in enumerate(rows):
            values = [joined(cell) for cell in cells]
            source = f'ferg1922:p{page}:b{block}:r{row}'
            data.source_locator = source
            override = data.override(source)
            if block == 3 and row and len(values) == 1 and listing:
                data.role(listing, page, values[0], 'Chairman', year=listing['attested'], column='Chairman.')
                continue
            if len(values) < 2 or not values[0].isdigit():
                continue
            year = int(values[0])
            names = values[1:]
            if block != 3:
                names = [part.strip() for part in re.split(r'\s*[—–]\s*', values[1]) if part.strip()]
                if re.fullmatch(r'(?:J\. )?(?:do\s*)+|[„〃]+', values[1], re.I):
                    names = previous
                else:
                    previous = names
            flags = ['ocr_doubtful'] if block == 3 or override.get('ocr_doubtful') else []
            listing = data.listing('C', heading, page, printed, block, row, CHAMBER, town='Colombo',
                                   kind='association', attested=year, flags=flags)
            for column, name in enumerate(names):
                if not fact(name) or name == '(Vacant)':
                    continue
                role = ('Chairman', 'Vice Chairman', 'Secretary')[column] if block == 3 else heading.rstrip('.')
                name, _, acting = name.partition(', acting')
                if acting or ', acting' in names[column]:
                    role += ', acting'
                data.role(listing, page, name, role, year=year,
                          column=rows[0][column + 1][0] if block == 3 else heading,
                          flags=flags)


def c_assoc(data, page, printed, blocks, block):
    heading = plain(blocks[block])
    key = f'ferg1922:p{page}:b{block}:r0'
    options = data.override(key)
    listing = data.listing('C', heading, page, printed, block, 0, heading,
                           town='Colombo', kind='association',
                           flags=['structure_lost', 'ocr_doubtful'] if options.get('structure_lost') else [])
    for index, person, role in options.get('officers', []):
        data.source_locator = f'ferg1922:p{page}:b{index}:r0'
        data.role(listing, page, person, role, flags=listing['flags'])
    for index, relation, target, kind in options.get('membership', []):
        data.source_locator = f'ferg1922:p{page}:b{index}:r0'
        data.connection(listing, page, relation, 'other', target, kind, flags=listing['flags'])
    return listing


def c_member_list(data, page, printed, block, raw, association, heading, acquired=False):
    previous_company = None
    key = 'ACQUIRED BY.' if acquired else 'AGENTS.'
    rows = Layout(raw['content']).rows
    if not acquired:
        key = joined(rows[0][1])
    for row, cells in enumerate(rows[1:], 1):
        locator = f'ferg1922:p{page}:b{block}:r{row}'
        options = data.override(locator)
        data.source_locator = locator
        companies, agents = cells
        name = fact(joined(companies))
        company_ditto = bool(re.fullmatch(r'(?:do[ .]*)+|[„〃]+', name or '', re.I))
        if company_ditto and previous_company:
            listing = previous_company
            name = listing['name_as_printed']
        else:
            town = 'London' if re.search(r', of London\.?$', name) else 'Colombo'
            listing = data.listing('C', heading, page, printed, block, row, name, town=town, kind='firm',
                                   trades=['Insurance'])
            previous_company = listing
            if not acquired:
                data.connection(association, page, 'MEMBERS.', 'other', name, 'insurer')
        entries = options.get('agents')
        if entries is None:
            value = re.sub(r'^\s*\.{2,}\s*', '', joined(agents)).rstrip(' ,')
            entries = []
            for target in company_chunks(value):
                name, place, address, flags = split_target(target)
                if name and not re.fullmatch(r'(?:Co|Ltd|Ld)\.?', name, re.I):
                    kind = 'insurer' if acquired else target_kind_of(name)
                    if kind == 'unknown' and re.fullmatch(r"[A-Z][A-Za-z. '-]+", name):
                        kind = 'person'
                    entries.append([name, place, kind, address, flags])
        for name, place, kind, *details in entries:
            address, flags = details or (None, [])
            data.connection(listing, page, key, 'other' if acquired else 'has_agent', name, kind, place,
                            flags=listing['flags'] + flags, address=address)
            if not acquired and kind == 'person':
                data.role(listing, page, name, 'Agents', column=key, flags=listing['flags'])


def c_banks(data, page, printed, blocks):
    heading = f'{plain(blocks[2])} / {plain(blocks[3])}'
    for block, raw in enumerate(blocks[4:], 4):
        if raw['label'] != 'Section-Header':
            continue
        name = plain(raw).removesuffix('.')
        address = re.sub(r'^Offices?\s*:?\s*', '', plain(blocks[block+1]))
        if block == 30:
            address = None
        listing = data.listing('C', heading, page, printed, block, 0, name,
                               address, 'Colombo', ['Banking'], 'bank')
        opts = data.override(listing['listing_id'])
        data.source_locator = f'ferg1922:p{page}:b{block + (1 if block == 30 else 2)}:r0'
        for person, role in opts.get('roles', []):
            data.role(listing, page, person, role)
        for relation, cls, target, kind in opts.get('connections', []):
            data.connection(listing, page, relation, cls, target, kind)


def c_banking_agencies(data, page, printed, blocks):
    heading = plain(blocks[2])
    lines = Layout(blocks[3]['content']).lines
    items = []
    for line in map(clean, lines):
        if '—Agents,' in line:
            items.append(line)
        elif line and items:
            items[-1] += ' ' + line
    for row, item in enumerate(items):
        name, _, agent = item.partition('—Agents,')
        name = name.strip()
        place = None
        if match := re.search(r', (LONDON|BELFAST)\.?$', name):
            place = match[1]
            name = name[:match.start()]
        data.source_locator = f'ferg1922:p{page}:b3:r{row}'
        listing = data.listing('C', heading, page, printed, 3, row, name, town=place or 'Colombo',
                               trades=['Banking'], kind='bank')
        target, agent_place, address, flags = split_target(agent.strip())
        data.connection(listing, page, 'Agents', 'has_agent', target,
                        'bank' if 'Bank' in target else 'company', agent_place, flags=flags, address=address)


def c_outstations(data, page, printed, blocks, banks):
    heading = plain(blocks[4])
    town = None
    for block, raw in enumerate(blocks[5:], 5):
        label = raw['label']
        value = plain(raw)
        if label == 'Section-Header' and value.startswith('AT '):
            printed_town = value[3:].rstrip('.')
            town = 'Kandy' if printed_town == 'KANDY' else printed_town
            continue
        if block == 10:
            continue
        layout = Layout(raw['content'])
        lines = [clean(line) for line in layout.lines if clean(line)]
        name = lines[0].rstrip('.')
        address = '22, Ward Street.' if block == 7 else None
        listing = data.listing('C', heading, page, printed, block, 0, name,
                               address, town, ['Banking'], 'bank')
        opts = data.override(listing['listing_id'])
        data.source_locator = listing['listing_id']
        local_branches = opts.get('branches', [])
        for target, place in local_branches:
            data.source_locator = f'ferg1922:p{page}:b{block + 1}:r0'
            data.connection(listing, page, 'BRANCHES', 'branch_at', target, 'place', place)
        for base in banks:
            if name.replace(' AND ', ' & ') == base['name_as_printed'].replace(' AND ', ' & '):
                data.connection(base, page, heading, 'branch_at', town, 'place')
        if block == 9:
            data.source_locator = f'ferg1922:p{page}:b10:r0'
        for person, role in opts.get('roles', []):
            data.role(listing, page, person, role)
        for relation, cls, target, kind in opts.get('connections', []):
            data.connection(listing, page, relation, cls, target, kind)


def extract_c(data):
    fire = None
    banks = []
    for page, blocks in get_pages(range(461, 468)):
        printed = printed_page(blocks)
        if page == 461:
            data.skipped['461'] = 'Military directories only. No Chamber heading or roster is present.'
        elif page == 462:
            c_chamber(data, page, printed, blocks)
            c_assoc(data, page, printed, blocks, 8)
        elif page == 463:
            c_assoc(data, page, printed, blocks, 2)
            c_assoc(data, page, printed, blocks, 5)
            fire = c_assoc(data, page, printed, blocks, 9)
            c_member_list(data, page, printed, 13, blocks[13], fire, FIRE + ' / MEMBERS.')
        elif page == 464:
            fire['continuation_pages'].append(page)
            fire['continuation_sources'] = [f'ferg1922:p{page}:b2:r0']
            c_member_list(data, page, printed, 3, blocks[3], fire, plain(blocks[2]))
            c_member_list(data, page, printed, 5, blocks[5], fire, plain(blocks[4]), acquired=True)
        elif page == 465:
            marine = c_assoc(data, page, printed, blocks, 2)
            c_member_list(data, page, printed, 6, blocks[6], marine, MARINE + ' / MEMBERS.')
        elif page == 466:
            start = len(data.listings)
            c_banks(data, page, printed, blocks)
            banks = data.listings[start:]
        elif page == 467:
            c_banking_agencies(data, page, printed, blocks)
            c_outstations(data, page, printed, blocks, banks)
    data.source_locator = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', nargs='+', type=int)
    parser.add_argument('--blocks', nargs='+', type=int)
    parser.add_argument('--section', choices=['A', 'B', 'C'])
    args = parser.parse_args()
    if args.inspect:
        inspect(args.inspect, args.blocks)
        return
    data = Extraction()
    extract_a(data)
    if args.section != 'A':
        extract_b(data)
    if args.section not in ('A', 'B'):
        extract_c(data)
    data.save()


if __name__ == '__main__':
    main()
