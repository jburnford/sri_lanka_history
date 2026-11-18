"""Inventory locally held pages of Ceylon directories, using only layout JSONL."""
import argparse
import collections
import csv
import html
import json
import os
from pathlib import Path
import random
import re

HERE = Path(__file__).resolve().parent
ROOTS = (Path('/home/jic823/ceylon/ocr_chandra/out_chandra2'),
         Path('/mnt/data/jic823/ocr_chandra/out_chandra2'))
CLASSES = """mercantile_colombo mercantile_outstation trade_lists associations
banks_insurance clergy_religious education professions government_establishment
municipal_local military_volunteer consuls shipping_port estates_directory
planters_alphabetical residents_alphabetical companies_register press almanac_calendar
statistics_review gazetteer_places advertisements front_matter index reference_material unclassified""".split()
VOLUME_FIELDS = """ocr_folder title year repository pages_total pdf_pages_held pages_held
has_contents_or_index_page notes""".split()
SECTION_FIELDS = """ocr_folder year pdf_page_start pdf_page_end printed_page_start
printed_page_end heading_as_printed section_class town_or_area attested layout
ocr_condition confidence notes""".split()
OVERRIDE_FIELDS = """ocr_folder pdf_page_start pdf_page_end section_class heading_as_printed
town_or_area attested layout confidence reason""".split()
SEED = 19221920

TAGS = re.compile(r'<[^>]+>')
NUMBER = re.compile(r'(?i)(?:[0-9]{1,4}[a-z]?|[ivxlcdm]{1,9}|[a-h])\.?$')
CONT = re.compile(r'\b(?:cont(?:inued|d)?|concl(?:uded)?|cont[’\']d)\b', re.I)
CONTENTS = re.compile(r'\b(?:table of contents|principal contents|general contents|contents(?: of (?:part|volume|the))?)\b', re.I)
INDEX = re.compile(r'^(?:\W|[ivxlcdm0-9]+\s+)*(?:(?:general|alphabetical|classified|commercial|subject|advertisers?[’\']?)\s+)?ind(?:ex|ices|cx)\b', re.I)
CORRECTED = re.compile(r"\b(?:corrected|revised|compiled|brought up)\s+(?:up\s+)?to\s+(.{3,45})", re.I)
DATE = re.compile(r"(?i)(?:(?:\d{1,2}(?:st|nd|rd|th)?\s+)?(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?\s+(?:\d{1,2}(?:st|nd|rd|th)?[.,]?\s+)?(?:18|19|20)\d{2}|(?:18|19|20)\d{2}(?:\s*[-–—]\s*\d{2,4})?)")
YEARS = re.compile(r'\b(?:18|19|20)\d{2}\s*(?:[-–—]|to)\s*(?:\d{4}|\d{2})\b', re.I)
CELL_COUNT = re.compile(r'<t[dh]\b', re.I)
ROW = re.compile(r'<tr\b[^>]*>(.*?)</tr>', re.I | re.S)
AD = re.compile(r'\b(?:advertisements?|advertizements?|advertisers?[’\']?\.?|advt?s?\.?)\b', re.I)


def clean(value):
    return ' '.join(html.unescape(TAGS.sub(' ', value)).split())


def normalize(value):
    return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()


def ranges(numbers):
    result = []
    for number in sorted(set(numbers)):
        if result and result[-1][1] + 1 == number:
            result[-1][1] = number
        else:
            result.append([number, number])
    return result


def range_string(numbers):
    return ','.join(str(a) if a == b else f'{a}-{b}' for a, b in ranges(numbers))


def read_tsv(path):
    with path.open(encoding='utf-8', newline='') as source:
        return list(csv.DictReader(source, delimiter='\t'))


def write_tsv(name, fields, rows):
    with (HERE / name).open('w', encoding='utf-8', newline='') as target:
        writer = csv.DictWriter(target, fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def directory_title(title):
    title = normalize(title)
    return bool(re.search(r'\b(?:ceylon (?:handbook and )?directory|ceylon handbook and directory)\b', title)
                and not re.search(r'\b(?:directory tea rubber and coconut estates|thackers|extract)\b', title))


def sources():
    root = Path(os.environ['CEYLON_OCR_ROOT']) if os.environ.get('CEYLON_OCR_ROOT') else next(
        (candidate for candidate in ROOTS if candidate.is_dir()), ROOTS[0])
    registry = {r['ocr_folder']: r for r in read_tsv(HERE.parent.parent / 'sources' / 'ocr_registry.tsv')}
    volumes = []
    for folder in sorted(root.iterdir()):
        base = re.sub(r'_p\d+$', '', folder.name)
        row = registry.get(folder.name) or registry.get(base)
        if not row or not directory_title(row['title']) or not folder.is_dir():
            continue
        candidates = sorted(set(folder.glob('*_layout.jsonl')) | set(folder.glob('*/*_layout.jsonl')))
        if not candidates:
            continue
        if len(candidates) != 1:
            raise ValueError(f'Ambiguous layout files in {folder}')
        year = row['date'] or re.search(r'(?:18|19|20)\d{2}', row['title']).group()
        volumes.append((folder.name, year, row, candidates[0]))
    return sorted(volumes, key=lambda v: (0 if v[0].startswith('1922-fergusons') else
                                         1 if v[0].startswith('FergusonsCeylonDirectory1920') else 2,
                                         v[1], v[0].lower()))


def page_info(data):
    blocks = data['blocks']
    max_y = max((b['bbox'][3] for b in blocks), default=1) or 1
    heads, titles, all_titles, numbers, widths = [], [], [], [], []
    counts = collections.Counter()
    list_columns = collections.Counter()
    toc_blocks = 0
    date = ''
    line_breaks = 0
    estate_table = False
    for block in blocks:
        label = block['label']
        counts[label] += 1
        raw = block['content'] or ''
        y = block['bbox'][1] / max_y
        if label in ('List-Group', 'Text'):
            line_breaks += len(re.findall(r'<(?:br|li)\b', raw, re.I))
        if label in ('Page-Header', 'Section-Header', 'Title'):
            value = clean(raw)
            if label == 'Page-Header':
                if NUMBER.fullmatch(value):
                    numbers.append(value)
                elif value:
                    number = re.match(r'^([0-9]{1,4}[a-z]?|[IVXLCDM]{2,9})\.?\s+(?=[A-Z])', value)
                    if not number:
                        number = re.search(r'\s+([0-9]{1,4}[a-z]?|[IVXLCDM]{2,9})\.?$', value)
                    if number:
                        numbers.append(number[1])
                        value = value[:number.start()] + value[number.end():]
                    heads.append(value)
            elif value and len(value) <= 200:
                all_titles.append(value)
                if y <= .26:
                    titles.append(value)
            mention = CORRECTED.search(value)
            if mention and (match := DATE.search(mention[1])):
                date = match[0]
        elif label == 'Table-Of-Contents':
            toc_blocks += 1
        elif label == 'Table' or '<table' in raw.lower():
            widths += [len(CELL_COUNT.findall(row)) for row in ROW.findall(raw)]
            if not estate_table:
                opening = normalize(clean(raw[:2500]))
                estate_table = ('proprietors or lessees' in opening and
                                ('district' in opening or 'acreage' in opening or 'agents' in opening))
        elif label == 'List-Group':
            list_columns[block['bbox'][0] // max(1, round(max_y * .07))] += 1
        elif label == 'Text' and y < .31 and not date and (mention := CORRECTED.search(clean(raw)[:400])):
            if match := DATE.search(mention[1]):
                date = match[0]

    widths = [width for width in widths if width >= 2]
    clues = heads + titles[:2]
    contents = any(CONTENTS.match(value.strip(' .:—')) for value in clues)
    index = any(INDEX.match(value) for value in clues)
    return {'n': int(data['pdf_page']), 'heads': heads, 'titles': titles,
            'all_titles': all_titles, 'printed': ' / '.join(dict.fromkeys(numbers)), 'counts': counts,
            'widths': widths, 'columns': len(list_columns), 'toc': toc_blocks, 'date': date,
            'contents': contents, 'index': index, 'line_breaks': line_breaks,
            'estate_table': estate_table}


def load_pages(path):
    pages = {}
    with path.open(encoding='utf-8') as source:
        for line in source:
            if not line.strip():
                continue
            page = page_info(json.loads(line))
            number = page['n']
            if number in pages:
                raise ValueError(f'Duplicate PDF page {number} in {path}')
            pages[number] = page
    return dict(sorted(pages.items()))


def inspect(pages, begin, end, step, all_titles=False):
    for number, page in pages.items():
        if not begin <= number <= end or (number - begin) % step:
            continue
        counts = page['counts']
        signature = ' '.join(f'{key[0]}{value}' for key, value in counts.items() if key != 'Page-Header')
        widths = collections.Counter(page['widths']).most_common(2)
        shape = '/'.join(str(w) for w, _ in widths)
        titles = page['all_titles'] if all_titles else page['titles'][:3]
        print(f'{number:4} {page["printed"]:>9} {signature:19} {shape:5} '
              f'{" | ".join(page["heads"])[:100]} || {" | ".join(titles)[:160]}')


# Order matters when a heading has terms from several types.
RULES = [
    ('reference_material', r'\bnative titles and names\b'),
    ('index', r'^(?:(?:alphabetical|classified|general|subject) )?index(?: |$)|\bindex (?:to|of) advertisements?\b'),
    ('front_matter', r'^(?:principal |general |table of )?contents\b|^preface\b|^errata\b|^addenda|^abbreviations\b'),
    ('advertisements', r'^(?:adverti[sz]ements?|advertisers?|advt?s?)$'),
    ('estates_directory', r'\b(?:estates? director(?:y|ies)|individual estates? owners?|individual owners? of|(?:tea|rubber|coconut|coco nut|cinnamon|citronella|cacao) (?:cultivation and )?(?:estates|plantations)|low ?country plantations|(?:tamil|english|native|sinhalese) names of (?:the )?(?:ceylon |tea |rubber )?estates|estates tamil names|proprietors or lessees|acres under cultivation)\b'),
    ('planters_alphabetical', r'\b(?:alphabetical (?:directory|list|index) of (?:ceylon )?(?:tea |rubber )?planters|(?:tea |rubber )?planters (?:alphabetical|alphabetically|directory)|list of (?:ceylon )?planters)\b'),
    ('residents_alphabetical', r'\b(?:general directory|address(?:es| directory)|box holders)\b|\balphabetical (?:list|directory) of (?:the )?(?:inhabitants|residents|persons|addresses|names)\b'),
    ('companies_register', r'\b(?:mercantile and planting companies|joint stock companies|registered companies|planting companies|public companies|companies registered|limited liability companies|company register|joint stock and planting companies)\b'),
    ('mercantile_colombo', r'\bcolombo (?:merchants|mercantile list)\b|^merchants and agents in colombo\b'),
    ('mercantile_outstation', r'^(?!colombo)\b(?:[a-z]+ ){1,3}(?:mercantile (?:and trade )?list|merchants (?:and )?agents|merchants c)\b|\b(?:mercantile firms.{0,40}outstations|outstations and villages)\b'),
    ('associations', r'\b(?:chamber of commerce|traders? association|insurance agents? association|fire insurance association|public institutions|co operative societies|clubs and societies|planters association|growers association|trade unions|trade associations|professional associations|sports clubs|rotary clubs|institutions and associations|learned societies)\b'),
    ('banks_insurance', r'^(?:banks?|banking|insurance companies|life insurance|fire insurance|marine insurance)\b|\bbanking (?:agencies|and insurance)\b'),
    ('military_volunteer', r'\b(?:military establishments?|army list|ceylon army|royal (?:navy|air force)|east indies station|ceylon defence force|ceylon volunteer|volunteer force|ceylon garrison artillery|ceylon light infantry|naval establishment)\b'),
    ('consuls', r'\b(?:consuls?|consular (?:corps|officers|representatives|agents)|foreign representatives|diplomatic corps|diplomatic missions)\b'),
    ('municipal_local', r'\b(?:municipalit(?:y|ies)|municipal council|local boards?|local government|urban councils?|town councils?|village committees?|district road committees?|provincial road committees?)\b'),
    ('government_establishment', r'\b(?:public service|civil service|civil establishments?|public offices|government of (?:ceylon|sri lanka)|government departments|house of representatives|executive council|legislative council|state council|governor general|ceylon cabinet|the cabinet|government establishment|postal and telegraphic information|stamp duties|customs tariff|crown land sales|court of requests|supreme court|police magistrates|district courts|civil list|parliament of ceylon|government apothecaries)\b'),
    ('clergy_religious', r'\b(?:ecclesiastical|clergy|christian missions?|churches and missions|places of worship|buddhist temples|buddhist priests|hindu temples|muslim mosques|roman catholic church|anglican church|religious denominations|religious bodies)\b'),
    ('education', r'\b(?:educational institutions|educational establishments?|colleges and schools|schools and colleges|government schools|registered schools|assisted schools|education in ceylon|university of ceylon|university college|teachers training|education department)\b'),
    ('professions', r'\b(?:licensed (?:surveyors|notaries|medical)|surveyors and levellers|visiting agents|medical practitioners|medical register|legal practitioners|maternity and other nurses|list of hospitals|hospitals in ceylon|advocates and proctors|notaries public|registered medical|government hospitals|principal hospitals)\b'),
    ('press', r'\b(?:newspapers(?: and periodicals)?|periodicals published|ceylon press|the press of ceylon)\b'),
    ('shipping_port', r'\b(?:steam (?:navigation|boat|ship)|shipping (?:agents|companies|services|directory)|port of colombo|marine surveyors|harbour (?:regulations|dues|master)|boat companies|flagstaff signals|light ?houses)\b'),
    ('almanac_calendar', r'\b(?:ephemeris|calendar|almanac|historical events|chronological table|table of events|chronological and historical|eclipses and planets|festivals and holidays)\b'),
    ('gazetteer_places', r'\b(?:gazetteer|postal (?:towns|directory)|post offices|post stations|roads in ceylon|minor roads and bridle paths|principal roads|list of resthouses|trigonometrical altitudes|table of distances|rivers lakes and tanks|coach and motor mail)\b'),
    ('trade_lists', r'\b(?:professional and trade list|mercantile and trade list|licensed (?:pawnbrokers|rubber|cacao)|principal chetty firms|general trades|trade directory|classified trades|trade lists?|factories mills|manufactories and machine offices|telegraphic addresses)\b'),
    ('statistics_review', r'\b(?:agricultural review|statistical|statistics|population of ceylon|census of ceylon|imports and exports|exports of ceylon|planting industry|ceylon tea industry|year in review|revenue and expenditure|ceylon imports|ceylon exports|trade and commerce|meteorological)\b'),
]
RULES = [(section_class, re.compile(pattern)) for section_class, pattern in RULES]
TOWN = re.compile(r'^(Colombo|Kandy|Galle|Jaffna|Matara|Negombo|Nuwara Eliya|Badulla|Batticaloa|Trincomalee|Kurunegala|Ratnapura|Hambantota|Kalutara|Gampola|Hatton|Tuticorin)\b', re.I)


def classify_heading(value):
    for section_class, pattern in RULES:
        if pattern.search(normalize(value)):
            return section_class
    return ''


def clues(page):
    if page['index']:
        return 'index', next(value for value in page['heads'] + page['all_titles'] if INDEX.match(value))
    if page['contents']:
        return 'front_matter', next(value for value in page['heads'] + page['all_titles'] if CONTENTS.match(value.strip(' .:—')))
    if any(AD.fullmatch(value.strip(' .:—')) for value in page['heads']):
        return 'advertisements', ''
    for value in page['heads'] + page['titles'][:2]:
        if (section_class := classify_heading(value)):
            town = TOWN.match(value)
            if section_class == 'mercantile_outstation' and not (town or 'outstation' in value.lower()):
                continue
            return section_class, value
    return '', ''


DEFAULT_LAYOUT = {
    'mercantile_colombo': '3-column table: firm | staff | agencies',
    'mercantile_outstation': 'firm, staff and address tables; trade lists',
    'trade_lists': 'trade headings over grouped names',
    'associations': 'institutional profiles and rosters',
    'banks_insurance': 'bank and agency lists',
    'clergy_religious': 'religious rosters and profiles',
    'education': 'school and staff profiles',
    'professions': 'professional rosters',
    'government_establishment': 'department and staff lists',
    'municipal_local': 'local staff and committee lists',
    'military_volunteer': 'unit and officer lists',
    'consuls': 'country and consul table',
    'shipping_port': 'company and agency tables',
    'estates_directory': 'estate, owner, agent, acreage and crop tables',
    'planters_alphabetical': 'alphabetical names and estate locations',
    'residents_alphabetical': 'alphabetical names, occupations and addresses',
    'companies_register': 'company profiles and property tables',
    'press': 'publication lists',
    'almanac_calendar': 'calendar and reference tables',
    'statistics_review': 'running prose and statistical tables',
    'gazetteer_places': 'location and distance tables',
    'advertisements': 'advertisements',
    'front_matter': 'title and reference leaves',
    'index': 'alphabetical subject index',
    'reference_material': 'reference table',
    'unclassified': 'unclear',
}
DUPLICATE_1883 = '1883-84_FERGUSON_S_CEYLON_DIRECTORY_PART_TWO_f639fd7f'
PART_1883 = '1883-84-the-ceylon-handbook-and-directory-calendar-part-2_897cc272'
SOURCE_NOTES = {
    '1871-72': 'The supplied PDF interleaves and duplicates some printed pages.',
    '1883-84-the-ceylon-handbook-and-directory-calendar-part-1': 'Part 1 ends in Civil Establishments, which continue in Part 2.',
    '1883-84-the-ceylon-handbook-and-directory-calendar-part-2': 'Part 2 begins mid-Civil Establishments. A second scan of Part 2 has its own registry record.',
    '1883-84_FERGUSON': 'Alternate OCR of 1883–84 Part 2. Page sequence matches the other Part 2 folder.',
    '1890-91-the-ceylon-handbook-and-directory-part-1': 'Part 1 ends within trade statistics. Part 2 continues the printed sequence.',
    '1890-91-the-ceylon-handbook-and-directory-part-2': 'Part 2 begins within trade tables continued from Part 1.',
    '1898-99': 'Supplied PDF skips printed pages within the estate directory; some held pages are repeated or out of order.',
    'CeylonHandbook1906': 'All registry PDF pages held. Registry warns of over 100 pages missing from the source edition; opening goes from ads to stamp duties.',
    '1922-fergusons': 'All registry PDF pages held. Printed pagination has gaps and repeats, including printed 419–423 before PDF 462.',
    '1940-fergusons': 'Held pages are in the address directory. Recurring school advertisements are printed on the same pages.',
    '1941-fergusons': 'Final held PDF page is an isolated index leaf after men’s addresses.',
    '1942-fergusons': 'Final index material contains repeated or reordered leaves.',
    '1946-fergusons': 'Index sequence interleaves displaced estate and address pages.',
    '1950-fergusons': 'Address pagination repeats or restarts inside the supplied PDF.',
    '1951-fergusons': 'Supplied PDF starts mid-reference and ends among hill estates. Mercantile sequences overlap.',
    '1955-fergusons': 'Supplied PDF starts with ads and a mid-calendar leaf and ends within the Colombo industrial tables.',
    '1959-fergusons': 'Large printed-page jumps before trade lists and within the estate index and address directory.',
    '1960-61': 'Supplied PDF ends within women’s addresses.',
    '1964-fergusons': 'Supplied PDF ends within foreign addresses.',
    '1967-68': 'Supplied PDF ends within district estate tables.',
}
SOURCE_INCOMPLETE = {
    'CeylonHandbook1906': {'front_matter', 'almanac_calendar', 'planters_alphabetical'},
    '1951-fergusons': {'almanac_calendar', 'estates_directory', 'front_matter', 'index', 'planters_alphabetical'},
    '1955-fergusons': {'front_matter', 'index', 'estates_directory', 'planters_alphabetical',
                      'residents_alphabetical', 'clergy_religious', 'associations', 'professions',
                      'mercantile_outstation', 'press', 'military_volunteer'},
    '1959-fergusons': {'mercantile_colombo', 'mercantile_outstation', 'companies_register',
                      'shipping_port', 'press', 'consuls', 'banks_insurance'},
}
# Catalogue contents name their own publications rather than the volume's sections.
CATALOGUE_CONTENTS = {'ceylonhandbook1904': 1489, '1905-06-fergusons': 1466,
                      'CeylonHandbook1905': 1627, 'CeylonHandbook1906': 1353,
                      'CeylonHandbook1907': 1651, '1909-fergusons': 1561}
CONFIRMED_CONTENTS = {'1922-fergusons': {35}, 'FergusonsCeylonDirectory1920': {52},
                      '1944-fergusons': {8}, '1946-fergusons': {6}}


def rows_by_volume(rows):
    result = collections.defaultdict(list)
    for row in rows:
        result[row['ocr_folder']].append(row)
    return result


def for_prefix(name, values, default):
    return next((value for prefix, value in values.items() if name.startswith(prefix)), default)


def automatic_pages(pages):
    """Fill short losses of headings using adjoining pages with matching evidence."""
    signals = {number: clues(page) for number, page in pages.items()}
    for number, (section_class, title) in signals.items():
        if section_class:
            yield number, (section_class, title, 'medium', '')
            continue
        before = next((signals[n] for n in range(number - 1, number - 5, -1)
                       if n in signals and signals[n][0]), ('', ''))
        after = next((signals[n] for n in range(number + 1, number + 5)
                      if n in signals and signals[n][0]), ('', ''))
        if before[0] and before[0] == after[0]:
            yield number, (*before, 'medium', '')
        else:
            yield number, ('unclassified', '', 'low', 'No consistent heading or structure identified.')


def make_groups(name, pages, overrides):
    decisions = dict(automatic_pages(pages))
    for id_, row in enumerate(overrides):
        start, end = (int(row[key]) for key in ('pdf_page_start', 'pdf_page_end'))
        if start > end or any(n not in pages for n in range(start, end + 1)):
            raise ValueError(f'Override outside held pages for {name}: {start}-{end}')
        for number in range(start, end + 1):
            decisions[number] = id_
    for number, page in pages.items():
        choice = decisions[number]
        if isinstance(choice, int) and overrides[choice]['section_class'] in {'index', 'advertisements'}:
            continue
        if clues(page)[0] == 'advertisements' and not page['estate_table']:
            decisions[number] = ('advertisements', '', 'high', 'Advertising running head and commercial content.')
    current = []
    previous = None
    for number, value in decisions.items():
        key = value if isinstance(value, int) else value[0]
        if current and (key != previous or current[-1] + 1 != number):
            yield current, overrides[previous] if isinstance(previous, int) else None
            current = []
        current.append(number)
        previous = key
    if current:
        yield current, overrides[previous] if isinstance(previous, int) else None


def suitable_heading(pages, section_class):
    for page in pages:
        for title in page['titles'] + page['heads']:
            if classify_heading(title) == section_class and len(title) <= 160:
                return title
    for page in pages[:4]:
        for title in page['heads']:
            if normalize(title) in {'directories', 'advertisements', 'index'}:
                return title
    return ''


def expected_structure(page, layout, section_class):
    counts = page['counts']
    width_counts = collections.Counter(page['widths'])
    whole_columns = sum(count for width, count in width_counts.items() if width >= 5)
    text = counts['Text']
    lists = counts['List-Group']
    if section_class == 'unclassified':
        return False
    if section_class == 'advertisements':
        return bool(text or counts['Section-Header'] or counts['Picture'] or counts['Image'])
    if layout.startswith('3-column table: firm | staff |'):
        return width_counts[3] >= 2
    if 'acreage and crop' in layout:
        return whole_columns >= 2
    if 'titles' in layout or 'title' in layout or 'divider' in layout:
        return bool(text or counts['Section-Header'] or counts['Title'] or counts['Image'] or page['toc'])
    if 'prose' in layout or 'ordinance' in layout or 'profiles' in layout or 'regulations' in layout:
        return bool(text or lists or page['widths'])
    if 'index' in layout or 'table' in layout:
        return bool(len(page['widths']) >= 2 or page['toc'] or lists)
    if section_class == 'residents_alphabetical':
        return bool(lists or len(page['widths']) >= 2 or text >= 8 or page['line_breaks'] >= 8)
    return bool(lists or len(page['widths']) >= 2 or text >= 4 or page['line_breaks'] >= 4)


def section_rows(volume, pages, overrides):
    name, year, _, _ = volume
    results = []
    for numbers, correction in make_groups(name, pages, overrides):
        entries = [pages[n] for n in numbers]
        first, last = entries[0], entries[-1]
        if correction:
            section_class = correction['section_class']
            heading = correction['heading_as_printed']
            layout = correction['layout']
            confidence = correction['confidence']
            note = correction['reason']
            town = correction['town_or_area']
            attested = correction['attested']
        else:
            votes = [clues(page)[0] for page in entries]
            section_class = next((vote for vote in votes if vote), 'unclassified')
            heading = layout = note = town = attested = ''
            confidence = 'medium' if section_class != 'unclassified' else 'low'
            if section_class == 'advertisements':
                confidence = 'high'
                note = 'Advertising running head and commercial content.'
        heading = heading or suitable_heading(entries, section_class)
        layout = layout or DEFAULT_LAYOUT[section_class]
        attested = attested or next((page['date'] for page in entries if page['date']), '')
        if not attested and (match := YEARS.search(heading)):
            attested = match[0]
        if not town and section_class in {'mercantile_colombo', 'mercantile_outstation'}:
            if section_class == 'mercantile_colombo':
                town = 'Colombo'
            elif match := TOWN.match(heading):
                town = match[0].title()
        if not results and numbers[0] > 1 and not re.search(r'\b(?:begins|starts|mid)\b', note, re.I):
            note = 'Held OCR starts at this section or its continuation. ' + note
        preserve = sum(expected_structure(page, layout, section_class) for page in entries) / len(entries)
        condition = 'good' if preserve >= .85 else 'mixed' if preserve >= .5 else 'poor'
        values = [name, year, numbers[0], numbers[-1], first['printed'], last['printed'],
                  heading, section_class, town, attested, layout, condition, confidence, note]
        results.append(dict(zip(SECTION_FIELDS, values, strict=True)))
    return results


def volume_rows(volume, pages, sections):
    name, year, row, _ = volume
    total = int(row['pages'])
    missing = set(range(1, total + 1)) - pages.keys()
    indexing = {n for section in sections if section['section_class'] == 'index'
                for n in range(section['pdf_page_start'], section['pdf_page_end'] + 1)}
    indexing |= for_prefix(name, CONFIRMED_CONTENTS, set())
    catalogue_page = for_prefix(name, CATALOGUE_CONTENTS, None)
    if catalogue_page in pages:
        indexing.add(catalogue_page)
    note = for_prefix(name, SOURCE_NOTES, '')
    if missing:
        first = sections[0]
        prefix = 'OCR missing PDF ' + range_string(missing) + '. '
        if not note:
            prefix += ('First held class is ' + str(first['section_class']) + '.')
        note = (prefix + note).strip()
    values = [name, row['title'], year, row['repository'], total, range_string(pages),
              len(pages), range_string(indexing), note]
    return dict(zip(VOLUME_FIELDS, values, strict=True))


def coverage_rows(volumes, all_sections):
    duplicate_years = collections.Counter(row['year'] for row in volumes)
    labels = {}
    for row in volumes:
        name, year = row['ocr_folder'], row['year']
        label = year
        if duplicate_years[year] > 1:
            if 'part-1' in name:
                label += ' (part 1)'
            elif 'part-2' in name:
                label += ' (part 2)'
            elif name == DUPLICATE_1883:
                label += ' (part 2 alternate)'
            else:
                label += ' (' + ('IA' if row['repository'] == 'archive.org' else 'HoCT') + ')'
        labels[name] = label
    if len(set(labels.values())) != len(labels):
        labels = {name: f'{label} [{name}]' for name, label in labels.items()}
    counts = collections.defaultdict(collections.Counter)
    for row in all_sections:
        counts[row['ocr_folder']][row['section_class']] += row['pdf_page_end'] - row['pdf_page_start'] + 1
    matrix = []
    for section_class in CLASSES:
        matrix_row = {'section_class': section_class}
        for row in volumes:
            name = row['ocr_folder']
            count = counts[name][section_class]
            incomplete_pdf = row['pages_held'] < row['pages_total']
            missing_in_source = section_class in for_prefix(name, SOURCE_INCOMPLETE, set())
            matrix_row[labels[name]] = count if count else '?' if incomplete_pdf or missing_in_source else 0
        matrix.append(matrix_row)
    return ['section_class', *labels.values()], matrix


def validation_for(pages, sections):
    assigned = collections.Counter(n for row in sections
                                   for n in range(row['pdf_page_start'], row['pdf_page_end'] + 1))
    problems = {n for n, count in assigned.items() if count != 1} | (assigned.keys() ^ pages.keys())
    failures = set(row['section_class'] for row in sections) - set(CLASSES)
    return {'pages_held': len(pages), 'sections': len(sections),
            'exactly_once': not problems, 'page_assignment_errors': range_string(problems),
            'classes_valid': not failures, 'unknown_classes': sorted(failures)}


def sample_sections(sections, rng):
    return sorted(rng.sample(sections, min(8, len(sections))), key=lambda row: row['pdf_page_start'])


def build(volumes, review=False, start_index=0, end_index=999, review_starts=()):
    overrides = rows_by_volume(read_tsv(HERE / 'boundaries_overrides.tsv'))
    volume_table, section_table = [], []
    by_volume = {}
    rng = random.Random(SEED)
    for index, volume in enumerate(volumes):
        name, _, registration, path = volume
        pages = load_pages(path)
        if not pages or min(pages) < 1 or max(pages) > int(registration['pages']):
            raise ValueError(f'Invalid PDF page numbers for {name}')
        if name == DUPLICATE_1883:
            companion = next(v for v in volumes if v[0] == PART_1883)
            comparable = load_pages(companion[3])
            # Compare the shared page numbers, layout and running-head families.
            if comparable.keys() != pages.keys():
                raise ValueError('1883 alternate scan no longer has the same page sequence')
            agreement = sum((left['printed'], list(left['counts'])) ==
                            (right['printed'], list(right['counts']))
                            for left, right in zip(comparable.values(), pages.values(), strict=True))
            if agreement < .90 * len(pages):
                raise ValueError('1883 alternate scan needs its own reviewed boundaries')
            decisions = overrides[PART_1883] + overrides[name]
        else:
            decisions = overrides[name]
        sections = section_rows(volume, pages, decisions)
        samples = sample_sections(sections, rng)
        if review and start_index <= index <= end_index:
            if review_starts:
                samples = [row for row in sections if row['pdf_page_start'] in review_starts]
            review_display(index, name, path, pages, samples)
        volume_row = volume_rows(volume, pages, sections)
        volume_table.append(volume_row)
        section_table.extend(sections)
        result = validation_for(pages, sections)
        result['fields_at_most_200'] = all(len(str(value)) <= 200
                                           for row in [volume_row, *sections] for value in row.values())
        by_volume[name] = result
    if review:
        return
    coverage_fields, coverage = coverage_rows(sorted(volume_table, key=lambda row: row['year']), section_table)
    fields = [*volume_table, *section_table, *coverage, *(r for group in overrides.values() for r in group)]
    if (HERE / 'audit.tsv').exists():
        fields += read_tsv(HERE / 'audit.tsv')
    failures = [{'folder': row.get('ocr_folder', ''), 'field': field, 'length': len(str(value))}
                for row in fields for field, value in row.items() if len(str(value)) > 200]
    pilot = {f'{start}-{end}': all(any(
        row['ocr_folder'].startswith('1922-fergusons') and row['section_class'] in allowed
        and row['pdf_page_start'] <= n <= row['pdf_page_end']
        for row in section_table) for n in range(start, end + 1))
        for start, end, allowed in [(462, 467, {'associations', 'banks_insurance'}),
                                    (468, 500, {'mercantile_colombo'}),
                                    (548, 555, {'mercantile_outstation'})]}
    validation = {'volume_count': len(volumes), 'section_count': len(section_table),
                  'fields_at_most_200': not failures, 'oversize_fields': failures,
                  'all_classes_valid': all(row['classes_valid'] for row in by_volume.values()),
                  'all_held_pages_exactly_once': all(row['exactly_once'] for row in by_volume.values()),
                  'pilot_1922_ranges_match': pilot, 'volumes': by_volume}
    write_tsv('volumes.tsv', VOLUME_FIELDS, volume_table)
    write_tsv('sections.tsv', SECTION_FIELDS, section_table)
    write_tsv('coverage.tsv', coverage_fields, coverage)
    (HERE / 'validation.json').write_text(json.dumps(validation, indent=2, ensure_ascii=False) + '\n',
                                         encoding='utf-8')
    if failures or not all(pilot.values()) or not validation['all_held_pages_exactly_once'] or not validation['all_classes_valid']:
        raise SystemExit('Validation failed. See validation.json.')
    print(f'{len(volumes)} volumes, {sum(row["pages_held"] for row in volume_table):,} PDF pages, '
          f'{len(section_table)} sections')


REVIEW_WORDS = re.compile(r'(?i)\b(?:rate|rules|licen[cs]e|capital|director|partner|staff|manager|agency|agents?|'
                          r'newspapers?|periodicals?|estates?|acres?|acreage|proprietors?|post office|post town|'
                          r'address(?:es)?|secretary|committee|hospitals?|surgeons?|doctors?|church|mission|'
                          r'commission|railway|calendar|income tax|page|contents|preface|limited|telephone|'
                          r'supplier|manufactur\w+|district|province|register|members?|exports?|imports?|'
                          r'revenue|expenditure|quantity|pounds|rs|price|house|banking|colombo|kandy|galle)\b')


def review_display(index, name, path, pages, samples):
    """Display transient structural evidence from the four pages of each audit check."""
    positions = {n for row in samples for n in (
        row['pdf_page_start'] - 1, row['pdf_page_start'],
        row['pdf_page_end'], row['pdf_page_end'] + 1) if n in pages}
    snippets = {}
    with path.open(encoding='utf-8') as source:
        for line in source:
            data = json.loads(line)
            number = data['pdf_page']
            if number not in positions:
                continue
            content = ' '.join(clean(block['content'] or '') for block in data['blocks']
                               if block['label'] in {'Text', 'Table', 'List-Group', 'Table-Of-Contents'})
            keywords = collections.Counter(word.lower() for word in REVIEW_WORDS.findall(content))
            ranking = sorted(keywords.items(), key=lambda item: (-item[1], item[0]))
            snippets[number] = '/'.join(word for word, _ in ranking[:4])
    print(f'\n{index} {name}')
    for row in samples:
        start, end = row['pdf_page_start'], row['pdf_page_end']
        checks = []
        for number in dict.fromkeys([start - 1, start, end, end + 1]):
            if number not in pages:
                checks.append(f'{number}:∅')
                continue
            page = pages[number]
            heading = (page['all_titles'] or page['heads'] or [''])[0]
            widths = collections.Counter(page['widths']).most_common(1)
            structure = (f'{widths[0][0]}c' if widths else 'L' if page['counts']['List-Group']
                         else 'C' if page['toc'] else 'P' if page['counts']['Text'] else '–')
            checks.append(f'{number}:{structure} {heading[:32]} [{snippets[number]}]')
        print(f'{start}-{end} {row["section_class"]} | ' + ' ; '.join(checks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', metavar='FOLDER_PREFIX')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=10000)
    parser.add_argument('--step', type=int, default=1)
    parser.add_argument('--all-titles', action='store_true')
    parser.add_argument('--review-audit', action='store_true')
    parser.add_argument('--volume-from', type=int, default=0)
    parser.add_argument('--volume-to', type=int, default=999)
    parser.add_argument('--review-starts', type=int, nargs='+', default=())
    args = parser.parse_args()
    volumes = sources()
    if args.inspect:
        for name, _, _, path in volumes:
            if name.lower().startswith(args.inspect.lower()):
                print(name)
                inspect(load_pages(path), args.start, args.end, args.step, args.all_titles)
        return
    build(volumes, args.review_audit, args.volume_from, args.volume_to, args.review_starts)


if __name__ == '__main__':
    main()
