#!/home/jic823/miniforge3/bin/python
"""Extract factual fields from the specified 1922 directory OCR."""
import argparse
import csv
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
                       r'Lieut\.?[- ]?Col\.?|Col\.?|Capt\.?|Rev\.?|Mlle\.?|Major|H\.? E\.?)\s+', re.I)
POST = re.compile(r'(?:\s*,\s*|\s+&\s+|\s+)((?:[A-Za-z]{1,5}\.\s*){2,}|J\.P\.(?:M\.M\.C\.)?|'
                  r'A\.?M\.?I\.?E\.?E\.?|Esq\.?|Gate Muhandiram)$', re.I)
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
    while (match := POST.search(name)):
        titles.append(match[1])
        name = name[:match.start()].rstrip(' ,&')
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
                      source_column=column, source_locator=self.source_locator or key, flags=sorted(set(flags) | set(damage(name))))
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
            pdf_page=page, source_locator=self.source_locator or key,
            flags=sorted(set(flags) | set(damage(target, place)))))

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
        audit_path = ROOT / 'audit.tsv'
        audit_long = []
        if audit_path.exists():
            with audit_path.open(encoding='utf-8', newline='') as audit:
                for row in csv.DictReader(audit, delimiter='\t'):
                    for key, value in row.items():
                        if len(value) > 200:
                            audit_long.append((row['listing_id'], key, len(value)))
        result = dict(unique_ids=unique, valid_references=not dangling, fields_at_most_200=not (long or audit_long),
                      dangling_references=dangling, overlong_fields=long, overlong_audit_fields=audit_long, counts=counts, skipped=self.skipped)
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


B_HEADING = 'LIST OF COLOMBO MERCHANTS AND AGENTS.'
B_ROLES = (
    r'(?:Sole |Governing |Local |General |Acting |Assistant |Chief |Joint |Head |Visiting |Sub[ -]|Colombo |Ceylon |'
    r'London |Resident |Travelling |Fixing |Superintending |Managing |Asst\.? |As t\.? |Office |Branch |Honorary |Hon\.? )*'
    r'(?:Propriet(?:or|ress)s?|Partners?|Directors?|Managers?|Agents?|Engineers?|Secretar(?:y|ies)|'
    r'Attorneys?|Accountants?|Assistants?|Assts?\.?|Auditors?|Superintendents?|Inspectors?|'
    r'Chairman|Canvasser|Clerks?|Storekeeper|Book-?keeper|Electrician|Shroff|Treasurer|'
    r'Tea Buyers?|Milliner|Draper|Dressmaker|(?:Vice-)?Consul|Cashier|Trustee|Veterinary Surgeon|Staff)'
)
TITLE_PATTERN = (
    r'(?P<title>' + B_ROLES +
    r'(?: (?:and|&) (?:Manager|Accountant|Secretary|Treasurer|Director|Engineer))?'
    r'(?: (?:in|for) [A-Z][A-Za-z -]+?)?(?: \([^)]{2,32}\))?|'
    r'[A-Z][A-Za-z &’\'-]{2,45} (?:Dept\.?|Department|Branch)|'
    r'General Office|Office|Tramway|Forage|Silverware|Drapery|Rubber & Produce|Men.s Clothing)'
)
CREDENTIAL = r'(?:[A-Za-z]\.\s*){2,}[A-Za-z.]?|(?:A\.?M\.?I\.?E\.?E\.?|J\.?\s*P\.|C\.?\s*A\.|jr\.|junr\.)'
PERSON_HEADING = re.compile(
    r'(?<![\w-])' + TITLE_PATTERN +
    r'\s*[:—–]\s*[—–-]*\s*', re.I
)
PREFIX_ROLE = re.compile(r'^' + TITLE_PATTERN + r'(?:\s*[:,.—–-]\s*|\s+)(?=[(A-Z])')
SUFFIX_ROLE = re.compile(r'^(.+?)(?:,\s*|\s+)(?P<post>' + B_ROLES + r'(?: (?:in|for) .+)?)[.]?$')


def b_people(lines):
    title = 'listed'
    buffer = ''
    for line in lines:
        if re.fullmatch(r'(?:COLOMBO|KANDY|WALKERS) STAFF(?: AT [A-Z &,.]+)?[:.]?', line, re.I):
            continue
        if not buffer:
            buffer = line
            continue
        if re.search(r'\w-$', buffer) and re.match(r'[a-z]', line):
            buffer = buffer[:-1] + line
            continue
        preceding = buffer.rsplit('\n', 1)[-1]
        if re.match(r'(?:and |& |per pro|signs |\()', line, re.I) or re.search(
            r'[:,;]$|\b(?:and|for|of|in|Mr\.?|Mrs\.?|Miss|Hon\.?|Sir|Dr\.?|Geo\.?|Chas\.?|'
            r'[A-Z]\.?)$', preceding
        ):
            sep = ' '
        elif PREFIX_ROLE.match(line) or PERSON_HEADING.match(line) or re.fullmatch(TITLE_PATTERN, line):
            sep = '\n'
        elif re.fullmatch(TITLE_PATTERN + r'[.:—–]*', preceding) or re.match(
            r'^(?:[A-Z][a-zÀ-ž-]+[.,;]?(?:$| [a-z]))', line
        ):
            sep = ' '
        elif line.startswith(('and ', 'of ')):
            sep = ' '
        else:
            sep = '\n'
        buffer += sep + line
    buffer = re.sub(r'\(Contd\.?\)', '', buffer, flags=re.I)
    # Headings printed with punctuation can start a new role within the same line.
    buffer = PERSON_HEADING.sub(lambda m: '\n' + m['title'] + ': ', buffer)
    for line in buffer.splitlines():
        line = clean(line).strip(' ;—–')
        if not fact(line) or line.startswith(('[See', '(In Private')):
            continue
        if only_role := re.fullmatch(TITLE_PATTERN + r'[.:—–]*', line):
            title = only_role['title']
            continue
        prefix = PREFIX_ROLE.match(line)
        if prefix:
            title = prefix['title']
            line = line[prefix.end():]
        if not line:
            continue
        yield title, line


PERSON_SPLIT = re.compile(r';\s*|,\s+(?:and\s+)?|\s+(?:and|&)\s+|(?<=[a-z])\. +(?=(?:Mr\.? |Mrs\.? |Miss |Dr\.? |Sir |[A-Z]\.))')
SIGNATORY = re.compile(r'\b(?:per pro\.?|signs? (?:the|&) firm)\b', re.I)


def split_people(value, title):
    value = re.sub(r'\s*\([^)]*(?:See |on leave|which see)[^)]*\)', '', value, flags=re.I)
    value = re.sub(r'\s*\(\s*\)', '', SIGNATORY.sub('', value)).strip(' ,;')
    if BODY.search(value) and len(value) < 120:
        corporate = re.search(r'\b(?:Co\.|Ltd\.?|Limited|Brothers|Bros\.?|Sons)\b[.,]?', value, re.I)
        if corporate and not re.search(r',\s*sign', value, re.I):
            yield value.strip(' ;'), title, True, []
            return
    names = []
    value = re.sub(r'\b(Mr|Mrs|Mlle|Dr|Geo|Chas|Thos|Robt|Hon|Rev|Capt)\. ', r'\1. ', value)
    for item in PERSON_SPLIT.split(value):
        item = item.replace(' ', ' ')
        item = item.strip(' ,;—–')
        if not fact(item):
            continue
        if names and (re.fullmatch(CREDENTIAL, item) or re.fullmatch(r'(?:[A-Z]\.\s*)+[A-Z]\.?', item)
                      and not re.search(r'[a-z]{2}', item)):
            names[-1][0] += ', ' + item
        elif names and re.fullmatch(B_ROLES, item.strip('.'), re.I):
            names[-1][1] = item.strip('.')
        else:
            names.append([item, title])
    for name, role in names:
        if suffix := SUFFIX_ROLE.fullmatch(name):
            name, role = suffix[1], suffix['post']
        if post := re.search(r'\((Chairman|Managing|Manager|Works Manager|acting)\)', name, re.I):
            name = (name[:post.start()] + name[post.end():]).strip()
            if post[1].lower() == 'managing':
                role = 'Managing Director'
            elif post[1].lower() == 'acting' and role == 'listed':
                role = post[1]
            elif post[1].lower() != 'acting':
                role = post[1]
        if not re.search(r'[A-Za-zÀ-ž]{2}', name) or len(name) > 100:
            continue
        if name[0] in '([' and not name.endswith((')', ']')):
            name = name[1:]
        is_uncertain = len(name.split()) == 1 and role == 'listed'
        yield name.strip(' ,;'), role, False, ['ocr_doubtful'] if is_uncertain else []


B_RELATION = re.compile(
    r"(?<![\w-])(?P<label>"
    r'Principal Correspondents and Agencies|Agents and Correspondents|Correspondents and Agents|'
    r'Insurance Agencies|Wine (?:&|and) Spirits Agencies|Drug Agencies|General Agencies|Other Agencies|'
    r'W\. S\. & Co\x27s AGENCIES|'
    r'(?:(?:Sole|Chief|Local|General|Managing|Buying|Colombo|London|Visiting) )?'
    r"Agen(?:t|ts|['’]s)(?: (?:&|and) Secretaries)?" r'(?: for(?: (?:Shipping|Insurance|Bankers))?| in| at)|Agents?(?=\s*[:—–])|'
    r'(?:Local )?Representatives? (?:of|in)|Agency at|Agencies (?:at|in)|Agencies|Correspondents(?: in| at)?|'
    r'Bankers|Branches and Agencies in|Branches(?: at| in)?|Branch Office|Branch Depôt|Depôts at|Also at|Head Office(?: and Sale Rooms)?|'
    r'Registered Offices?|London (?:Buying )?Office|London Agent[s]?|London Correspondent|'
    r'Central Offices|Colonial and Foreign Depots|Engineering Workshops and Stores at|Mills at|Works at|Saw Mills at|Coaling Contractors to|Successors to|Proprietors? of|'
    r'Sterling Companies|Rupee Companies)'
    r'(?:(?:\s*[:—–-]\s*)|(?:\.\s*)|(?=\s+(?:the\b|[A-Z0-9"(“]))|$)', re.I
)
QUALIFIER = re.compile(r'^\(?\s*(?P<qual>(?:Sterling|Rupee|Rupen)\s+(?:Companies|Co\.?[’\']?s\.?)|'
                       r'Shipping|Insurance|Estates|General)\s*\)?[.:—– -]*', re.I)
TRADE_PATTERN = re.compile(
    r'\b(?:merchants?|brokers?|dealers?|manufacturers?|importers?|exporters?|engineers?|'
    r'contractors?|builders?|veterinarians?|undertakers?|livery stable keepers?|booksellers?|seed(s)?men|printers?|publishers?|drapers?|milliners?|'
    r'stationers?|outfitters?|packers?|purveyors?|ship repairers?|planters?|'
    r'accountants?|mine owners?|mining|min(er|ers)|valuer[s]?|valuators?|agents|attorneys)\b', re.I
)
CO_SUFFIX = re.compile(r'(?i)\b(?:Co|Cos|Company|Corporation|Inc|Ltd|Ld|Limited|Bros|Brother[s]?|Sons|Cie|'
                       r'Association|Society|Syndicate|Insurance|Assurance|Bank|Works|Steamers|Line|Estates|'
                       r'Plantations|Factories|Factory|Railway|Mills|Kaisha)\b')
PLACES = re.compile(
    r'(?:London|New York(?: City)?|Glasgow|Manchester|Liverpool|Birmingham|Edinburgh|'
    r'Calcutta|Bombay|Madras|Cochin|Karachi|Karaobi|Rangoon|Colombo|Kandy|Galle|'
    r'Sydney|Melbourne|Adelaide|Perth|Brisbane|Wellington|Auckland|Dunedin|Christchurch|'
    r'Paris|Marseilles?|Hamburg|Bordeaux|Copenhagen|Amsterdam|Zurich|Berlin|Rotterdam|'
    r'Yokohama|Tokio|Tokyo|Osaka|Kobe|Japan|Penang|Singapore|Shanghai|Hankow|Foochow|'
    r'China|Havana|Canton|Hongkong|Montreal|Toronto|Vancouver|Boston|Chicago|Seattle|'
    r'San Francisco|Philadelphia|Antwerp|England|Europe|Australia|India|Ceylon|'
    r'Burma|Switzerland|Scotland|Ireland|Belfast|Beyrouth|Victoria|Belgium|Argentina|'
    r'New Zealand|Wellington|Henselo|The Hague|Helmond|Widnes|Northwich|Kallai|Genoa|'
    r'F\.M\.S\.|U\.?\s*S\.?\s*A\.?|E\.?\s*C\.?\s*\d*|S\.?\s*E\.?|B\.C\.)'
)


def relation_class_of(label, qualifier):
    key = label.lower()
    if key.startswith(('branch', 'also at', 'depôts', 'works at', 'saw mills at', 'mills at',
                       'colonial and foreign depots', 'engineering workshops and stores at')):
        return 'branch_at'
    if 'secretaries' in key or 'secretar' in key:
        return 'secretary_for'
    if 'correspondent' in key:
        return 'correspondent'
    if 'representative' in key:
        return 'represents'
    if 'insurance' in key or qualifier and qualifier.lower() == 'insurance':
        return 'insurer_agent'
    if 'shipping' in key or qualifier and qualifier.lower() == 'shipping':
        return 'shipping_agent'
    if 'agencies' in key or key.startswith(('agenc', "agen's", 'agent', 'sole agent', 'managing agent', 'chief agent', 'local agent',
                       'london agent', 'buying agent',
                       'sterling companies', 'rupee companies')):
        return 'agent_for'
    return 'other'


def target_kind_of(value, relation=None):
    if re.search(r'\b(?:Assurance|Insurance|Underwriters|Lloyd.s)\b', value, re.I):
        return 'insurer'
    if re.search(r'\bBank\b|\bBanking Corporation\b', value, re.I):
        return 'bank'
    if re.search(r'Steamers?|Steamship|Shipping|Steam Navigation|\bS\.\s*S\.|\bLine\b|Kisen Kaisha|Fleet', value, re.I):
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


def place_list(value):
    value = re.split(r'\b(?:and )?(?:at |in )?all (?:other |the |chief |principal |foreign )*'
                     r'(?:parts|ports|towns|cities|directions)\b', value, maxsplit=1, flags=re.I)[0]
    return [item.strip(' ,.;&') for item in re.split(r'[,;]|\s+(?:and|&)\s+', value)
            if item.strip(' ,.;&') and item.strip(' ,.;&').lower() not in ('etc', 'c', 'etc etc')]


def trade_chunks(value):
    if not TRADE_PATTERN.search(value):
        return []
    broker = re.fullmatch(r'(.+?) Brokers?\.?', value, re.I)
    if broker and ',' in broker[1]:
        return [term + ' Brokers' for term in re.split(r',\s*|\s+(?:and|&)\s+', broker[1])]
    terms = trade_terms(value)
    return [item for item in terms if len(item) <= 75 and not re.match(r'^(?:The|See|Established)\s', item)
            and not CO_SUFFIX.search(item) and not re.search(r'\b(?:is |are |has |will |which |where |being )\b', item)]


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
                if re.match(r'(?:of|for|from)\s', tail, re.I):
                    continue
                if not CO_SUFFIX.search(head) or re.match(r'^(?:Ltd\b|Ld\b|Limited\b|Inc\b|Prptry\b|\(|\[)', tail, re.I):
                    continue
                if re.match(PLACES.pattern + r'(?:[ ,.]|$)', tail):
                    continue
                if re.search(r'[A-Z](?:[A-Za-z]|\.)', tail) and (CO_SUFFIX.search(tail) or
                        re.search(r'(?:,|\s)' + PLACES.pattern + r'\.?$', head)):
                    if head.strip():
                        yield head.strip(' ,')
                    start = m.end()
            if fragment[start:].strip(' ,'):
                yield fragment[start:].strip(' ,')


def split_target(value, default_place=None, ditto_place=None):
    flags = []
    value = re.sub(r'\s*\((?:See Adv[st]?\.?|which see)\)', '', value, flags=re.I)
    value = re.sub(r'\s*[—–-]+\s*See Adv.*$', '', value, flags=re.I).strip(' ,;')
    suffix = re.search(r',?\s+([„〃"]+)$', value)
    if suffix:
        return value[:suffix.start()].rstrip(' ,'), ditto_place, flags if ditto_place else ['ocr_doubtful']
    if re.search(r'\[[^]]*|\b(?:\?\?+|etc\.)', value, re.I):
        flags.append('ocr_doubtful')
    location = re.search(r'(?:[,.;]\s+|\s+of\s+|\s+)(?=' + PLACES.pattern + r'(?:[, .]|$))', value)
    if location and location.start() > 1:
        tail = value[location.end():].strip(' ,')
        if not any((location[0].strip(), re.match(r'\s*,', value[location.end() + len(tail):]))) and re.search(
            r'^(?:Ceylon|India|China|England|Scotland|Australia)\b', tail
        ) and ',' not in tail:
            return value, default_place, flags
        prefix = value[:location.start()].strip(' ,')
        if not re.match(r'^(?:The|of)\s+', tail) and not CO_SUFFIX.search(tail) and not re.match(r'^(?:Co\.|Ltd)', tail):
            if ' of ' not in location[0] or not CO_SUFFIX.search(tail):
                return prefix, tail, flags
    return value, default_place, flags


def b_connections(data, listing, page, lines, column, initial=None, flags=()):
    state = initial or (column, 'correspondent', None, None)
    previous_the = ''
    previous_place = None
    buffer = []
    for line in lines:
        if buffer and page in (470, 478, 490, 491, 492, 493, 500) and (
            re.match(r'^(?:Ltd|Ld|Limited|Inc|Co\.|of |and |& |Sons[,.])', line) or
            re.search(r'\b(?:The|of|and|in|for|\d+)\s*$', buffer[-1])
        ):
            buffer[-1] += ' ' + line
        elif buffer and re.search(r'\w-$', buffer[-1]) and re.match(r'[a-z]', line):
            buffer[-1] = buffer[-1][:-1] + line
        elif buffer and line[:1].islower() and len(buffer[-1]) > 5:
            buffer[-1] += ' ' + line
        else:
            buffer.append(line)
    for line in buffer:
        line = re.sub(r'\(Cont(?:inue)?d\.?[^)]*\)|\(See Adv[^)]*\)', '', line, flags=re.I).strip(' ;—–')
        if not fact(line) or line.startswith(('On ', 'Member ', 'Established ', 'Danish Royal ')):
            continue
        if state[1] == 'other' and re.search(r'Office', state[0], re.I) and not (
            re.match(r'^' + PLACES.pattern, line) or not CO_SUFFIX.search(line)
        ):
            state = (column, 'correspondent', None, None)
        matches = list(B_RELATION.finditer(line))
        pieces = []
        if not matches or matches[0].start():
            pieces.append((None, line[:matches[0].start()].strip(' ;,') if matches else line))
        pieces.extend((m['label'], line[m.end():matches[i+1].start() if i+1 < len(matches) else len(line)])
                      for i, m in enumerate(matches))
        for label, value in pieces:
            value = re.sub(r'^\s*(?:and\s+|for\s+|&\s+)', '', value.strip(' ;:—–,'), flags=re.I)
            if label:
                qualifier = None
                if match := QUALIFIER.match(value):
                    qualifier = match['qual'].rstrip('.')
                    value = value[match.end():]
                if label.lower().startswith(('sterling', 'rupee')):
                    qualifier = label
                place = 'London' if label.startswith('London ') else None
                state = (label, relation_class_of(label, qualifier), qualifier, place)
                previous_the = ''
                previous_place = None
            relation, cls, qualifier, region = state
            if not fact(value):
                continue
            if re.fullmatch(r'\((?:LIFE|FIRE|MARINE|ACCIDENT)[^)]*\)[.]?', value, re.I):
                continue
            if not label and (cls == 'correspondent' and relation == column or
                              relation.lower().endswith('office')) and trade_chunks(value) and not re.search(
                                  r'\b(?:Co\.|Company|Ltd\.?|Inc\.)\b', value):
                listing['trades'] = list(dict.fromkeys(listing['trades'] + trade_chunks(value)))
                continue
            if re.match(r'^(?:[„〃"]\s+)', value):
                value = previous_the + re.sub(r'^[„〃"]\s+', '', value)
            else:
                previous_the = 'The ' if value.startswith('The ') else ''
            geographical = bool(re.search(r'\b(?:Branches|Also at|Depôts at|Mills at|Correspondents in|Agencies (?:at|in)|'
                                          r'Agency at|Colonial and Foreign Depots)\b',
                                          relation, re.I))
            office = bool(re.search(r'\b(?:Office[s]?|Works at|Depôt)\b', relation, re.I))
            if geographical and (not CO_SUFFIX.search(value) or relation.lower() in ('correspondents in', 'agencies in')):
                targets = place_list(value)
            elif office and not relation.lower().startswith(('branches', 'depôts')):
                targets = [value]
            elif qualifier == 'Estates' and not CO_SUFFIX.search(value):
                targets = place_list(value)
            else:
                targets = company_chunks(value)
            for target in targets:
                target = re.sub(r'^(?:(?:and|at|for)\s+)+', '', target, flags=re.I).strip()
                if not target or len(target) > 165 or re.search(
                    r'\b(?:various parts|the world|following lines|all chief ports|all other|and other lines)\b', target, re.I
                ) or re.fullmatch(r'(?:&c|etc|General|Insurance|Shipping|and|for|Co\.?|Ltd\.?)[ .,]*', target, re.I
                ) or re.fullmatch(r'\([^)]*\)[, .]*', target):
                    continue
                if geographical and not CO_SUFFIX.search(target):
                    name, place, local_flags = target.rstrip(' .'), None, []
                    kind = 'place'
                elif office:
                    name, place, local_flags = target.rstrip(' ,'), region, []
                    location = list(PLACES.finditer(target))
                    if location and not region:
                        place = location[0][0]
                    kind = 'place'
                else:
                    name, place, local_flags = split_target(target, region, previous_place)
                    kind = target_kind_of(name, cls)
                    if kind == 'unknown' and PLACES.fullmatch(name.strip(' .')):
                        kind = 'place'
                if len(name) < 3 or re.search(r'\b(?:which see|see advert|continued over)\b', name, re.I):
                    continue
                if place:
                    previous_place = place
                target_cls = cls
                if cls == 'agent_for' and kind in ('insurer', 'shipping line'):
                    target_cls = 'insurer_agent' if kind == 'insurer' else 'shipping_agent'
                data.connection(listing, page, relation, target_cls, name, kind, place, qualifier,
                                list(flags) + local_flags)
    return state


def b_address(lines):
    full = joined(lines)
    full = re.sub(r'\s*[—–-]?\s*\(See Adv[^)]*\)', '', full, flags=re.I)
    full = re.split(r'\s+(?:Telegraphic Address|Tel\.? (?:Address|Addresses)|G\.P\.O\.|Phone No|Telephone No)', full,
                    maxsplit=1, flags=re.I)[0]
    match = re.search(r'\s*\[\s*', full)
    if not match:
        match = re.search(r'\s*\((?=(?:No\.? |Fort\b|Columb[oa]\b|Hatton\b|York\b|Kollupitiya\b|'
                          r'Office\b|Gregory|Chamber of Commerce))', full, re.I)
    if match and match.start():
        name, addr = full[:match.start()], full[match.end():]
    elif len(lines) > 1 and re.search(r'\b(?:Street|St\.|Road|Building|Place|House|Fort)\b', lines[1], re.I):
        name, addr = lines[0], joined(lines[1:])
    else:
        name, addr = full, ''
    addr = addr.split(']', 1)[0].rstrip('),; ').removesuffix(')').rstrip()
    addr = re.split(r'\b(?:Tel\.? Address|Telegraphic Address|Telephone|Codes|Phone No\.?|P\.?\s*O\.?\s*Box)\b', addr,
                    flags=re.I, maxsplit=1)[0].strip(' ;,')
    name = re.sub(r'\s*[—–-]*\s*(?:Estd\.?|Estab\.?|Established)\s*\d{4}\.?\s*\.*$', '', name, flags=re.I)
    name = re.sub(r'\s+[-—–.]{2,}$', '', name)
    return short_name(name), fact(addr)


def b_page_rows(data, page, blocks):
    if page == 489:
        col = plain(blocks[2])
        agency = plain(blocks[3])
        for left in (4, 6, 8, 10):
            first, last = data.override(f'ferg1922:p{page}:b{left}:r0')['right_blocks']
            yield left, 0, [Layout(blocks[left]['content']).lines,
                            Layout(blocks[left + 1]['content']).lines,
                            [plain(blocks[i]) for i in range(first, last + 1)]], col, agency
        return
    for block, raw in enumerate(blocks):
        rows = Layout(raw['content']).rows
        if not rows:
            continue
        columns = rows[0]
        for index, cells in enumerate(rows[1:], 1):
            yield block, index, cells, joined(columns[1]), joined(columns[2])


def extract_b(data):
    listings = {}
    states = {}
    for page, blocks in get_pages(range(468, 501)):
        printed = printed_page(blocks)
        printed_doubt = page in (469, 473, 476, 477, 481, 489, 490)
        for block, row, cells, people_col, agencies in b_page_rows(data, page, blocks):
            key = f'ferg1922:p{page}:b{block}:r{row}'
            opts = data.override(key)
            if opts.get('skip'):
                continue
            coord = (page, block if page == 489 else row)
            data.source_locator = key
            flags = ['structure_lost'] if page in (480, 484, 489) or opts.get('structure_lost') else []
            if printed_doubt or opts.get('ocr_doubtful'):
                flags.append('ocr_doubtful')
            targets = opts.get('attach')
            first, middle, right = ([clean(s) for s in cell if clean(s)] for cell in (
                [[], cells[0], cells[1]] if len(cells) == 2 else cells))
            if page == 484 and row >= 2:
                targets = [(484, 1)]
                middle = first + middle
            if not targets:
                name, address = b_address(first)
                if not name:
                    continue
                town = 'Colombo'
                if address and re.search(r'\bJaffna\b', address):
                    town = 'Jaffna'
                if name == 'Hatton Bank and Agency Co.':
                    town = 'Hatton'
                if page == 468 and row == 5:
                    town = 'Galle'
                fields = opts.get('listing', {})
                listing = data.listing('B', B_HEADING, page, printed, block, row,
                                       name, address, town, kind=fields.get('kind'),
                                       attested='corrected to December 1921', flags=flags)
                listings[coord] = listing
                targets = [coord]
                if coord == (468, 5):
                    other = data.listing('B', B_HEADING, page, printed, block, 7,
                                         'Walkers & Clark Spence', None, 'Galle',
                                         attested='corrected to December 1921', flags=['shared_entry'])
                    listings[(page, 7)] = other
                    targets.append((page, 7))
            for target in targets:
                target = tuple(target)
                listing = listings[target]
                if listing['pdf_page'] != page:
                    if page not in listing['continuation_pages']:
                        listing['continuation_pages'].append(page)
                    listing.setdefault('continuation_sources', []).append(key)
                    listing['flags'] = sorted(set(listing['flags'] + flags))
                if 'structure_lost' in flags and 'structure_lost' not in listing['flags']:
                    listing['flags'].append('structure_lost')
                if len(targets) > 1:
                    flags = sorted(set(flags + ['shared_entry']))
                if 'roles' in opts:
                    for person, role in opts['roles']:
                        data.role(listing, page, person, role, column=people_col, flags=flags)
                else:
                    for title, names in b_people(middle):
                        for name, role, is_body, local_flags in split_people(names, title):
                            if is_body:
                                data.connection(listing, page, role if role != 'listed' else people_col,
                                                'other', name, target_kind_of(name), flags=flags)
                            else:
                                data.role(listing, page, name, role, column=people_col, flags=flags + local_flags)
                for source, person, role in opts.get('additional_roles', []):
                    data.source_locator = source
                    data.role(listing, page, person, role, column=people_col, flags=flags)
                data.source_locator = key
                all_flags = flags + (['ocr_doubtful'] if opts.get('uncertain_connections') else [])
                if opts.get('skip_right'):
                    right = []
                if cutoff := opts.get('skip_right_from'):
                    right = right[:next(index for index, line in enumerate(right) if line.startswith(cutoff))]
                state = b_connections(data, listing, page, right, agencies, states.get(target), all_flags)
                states[target] = state
                for source, relation, cls, target_name, kind, place in opts.get('additional_connections', []):
                    data.source_locator = source
                    data.connection(listing, page, relation, cls, target_name, kind, place, flags=all_flags)
                data.source_locator = key
                for group in opts.get('agency_groups', []):
                    for name in group['targets']:
                        data.connection(listing, page, group['relation'], 'agent_for', name,
                                        target_kind_of(name), flags=all_flags + ['structure_lost'])
                if 'trades' in opts.get('listing', {}):
                    listing['trades'] = opts['listing']['trades']
                for connection in opts.get('connections', []):
                    data.connection(listing, page, *connection, flags=all_flags)
                if target == coord:
                    extra = re.search(r'\b(?:Also )?(?:Branches at|Branch Office:)\s*(.+)',
                                      b_address(first)[1] or '', re.I)
                    if extra:
                        for place in place_list(extra[1]):
                            data.connection(listing, page, extra[0][:-len(extra[1])].strip(' :'),
                                            'branch_at', place, 'place', flags=flags)
        data.source_locator = None


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
                name, place, flags = split_target(target)
                if name and not re.fullmatch(r'(?:Co|Ltd|Ld)\.?', name, re.I):
                    kind = 'insurer' if acquired else target_kind_of(name)
                    if kind == 'unknown' and re.fullmatch(r"[A-Z][A-Za-z. '-]+", name):
                        kind = 'person'
                    entries.append([name, place, kind])
        for name, place, kind in entries:
            data.connection(listing, page, key, 'other', name, kind, place, flags=listing['flags'])
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
        data.connection(listing, page, 'Agents', 'other', agent.strip(),
                        'bank' if 'Bank' in agent else 'company', place='Colombo')


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
