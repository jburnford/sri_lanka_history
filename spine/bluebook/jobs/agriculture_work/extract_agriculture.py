#!/home/jic823/miniforge3/bin/python
"""Rebuild the agricultural extract from local OCR JSONL files (stdlib only).

Deliberately uses reviewed layouts. Source coordinates in every note are zero-based.
No OCR spelling or suspect numeric character is repaired.
"""
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'extracted'
WORK = ROOT / 'jobs/agriculture_work'
YEARS = [1869,1889,1890,1902,1904,1912,1924,1925,1926,1928,1930,1933,1934]
# Second pass: volumes from which only the opening "Agricultural Statistics" tables are taken (file keys).
MORE_VOLUMES = ['1863','1866','1868','1871','1877','1880','1881','1882','1883','1885','1886','1887','1889b',
                '1891','1892','1893','1894','1896','1897','1898','1899','1900','1901','1903','1905','1906','1907',
                '1908','1910','1911','1913','1914','1915','1916','1917','1918','1919','1920','1921','1922','1923']
FIELDS = 'table_id year_volume year_data pdf_page printed_page table_kind area_level area_as_printed parent_area_as_printed measure_as_printed unit_as_printed value_as_printed value note'.split()
TABLES = {}
PAGES = {}
for key in [str(y) for y in YEARS] + MORE_VOLUMES:
    with gzip.open(ROOT / f'tables/{key}.jsonl.gz', 'rt') as f:
        for line in f:
            t = json.loads(line)
            TABLES[t['id']] = t
    with gzip.open(ROOT / f'pages/{key}.jsonl.gz', 'rt') as f:
        for line in f:
            p = json.loads(line)
            PAGES[key,p['pdf_page']] = p


def trim(s):
    # Only whitespace and trailing sequences of dot leaders; retain single punctuation dots.
    return re.sub(r'(?:\s*\.\s*){2,}$', '', s.strip()).rstrip()


def missing(s):
    return not s.strip() or bool(re.fullmatch(r'[.\s—–−-]+', s.strip())) or s.strip().lower() == 'nil'

FRACTIONS = {'¼':Decimal('.25'),'½':Decimal('.5'),'¾':Decimal('.75'),
             '⅛':Decimal('.125'),'⅜':Decimal('.375'),'⅝':Decimal('.625'),'⅞':Decimal('.875'),
             '⅓':Decimal(1)/3,'⅔':Decimal(2)/3}


def decimal_string(x):
    return format(x, 'f').rstrip('0').rstrip('.') if '.' in format(x, 'f') else str(x)


def number(s):
    if missing(s):
        return '', ''
    q = s.strip()
    marks = []
    # Explicit typographical footnote markers, never letters which could be OCR errors.
    q2 = re.sub(r'\\(?:dagger|ddagger|ast)\b|[*†‡§]+', '', q).strip()
    if q2 != q:
        marks.append('footnote marker retained in value_as_printed; omitted in value')
    q = q2
    # Only syntactically valid thousands separators are removed.
    if ',' in q:
        if not re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?:[¼½¾⅛⅜⅝⅞]|\\frac\{\d+\}\{\d+\}|\s+\d+/\d+)?', q):
            return '', 'unreadable or ambiguous numeric string; not corrected'
        q = q.replace(',', '')
    try:
        if re.fullmatch(r'[+-]?\d+(?:\.\d+)?', q):
            return decimal_string(Decimal(q)), '; '.join(marks)
        m = re.fullmatch(r'(\d*)\s*([¼½¾⅛⅜⅝⅞])', q)
        if m:
            return decimal_string(Decimal(m[1] or 0)+FRACTIONS[m[2]]), '; '.join(marks)
        m = re.fullmatch(r'(\d*)\\frac\{(\d+)\}\{(\d+)\}', q)
        if not m:
            m = re.fullmatch(r'(\d+)\s+(\d+)/(\d+)', q)
        if m and int(m[3]):
            den = int(m[3])
            # Decimal requirement: do not approximate recurring fractions silently.
            d = den
            while d % 2 == 0: d //= 2
            while d % 5 == 0: d //= 5
            if d == 1:
                return decimal_string(Decimal(m[1] or 0)+Decimal(m[2])/Decimal(den)), '; '.join(marks)
    except (InvalidOperation, ValueError):
        pass
    return '', 'unreadable or nonnumeric return; not corrected'

UNIT_PATTERN = r'(?:bushels?|lb\.?|lbs\.|cwt\.|nuts|leaves|fruits|tons?|bunches|oz\.|Rs\.)'


def split_unit(s):
    """Split only explicit unit text, without supplying units from neighbouring crops."""
    m = re.fullmatch(r'(' + UNIT_PATTERN + r')\s+(.+)', s.strip(), re.I)
    if m: return m[2], m[1]
    m = re.fullmatch(r'(.+?)\s+(' + UNIT_PATTERN + r')', s.strip(), re.I)
    if m: return m[1], m[2]
    return s, ''

DATA = []
# Parallel source-cell coordinates: used to validate provenance, no guessed cells.
PROVENANCE = []
USED = {}
SKIPPED = {}
AUDIT = []
CELL_CHECKS = defaultdict(list)   # DATA index -> statuses of the acreage totals checks it takes part in


def register(t, kind, dating):
    USED[t['id']] = {'kind':kind, 'dating':dating}


# Page-image readings (page_readings/acreage/): the opening acreage tables for 1879-1891 read by eye from the
# archive.org page images, because the OCR of these pages misreads many figures. Each file is the table's grid in
# the parsed table's own row and column order (crop row, then province rows, then the printed total row); a line
# starting "!" is a note on one cell. A reading replaces the OCR string in value_as_printed; the OCR string stays
# in source_cells.tsv and is quoted in note wherever it differs.
READINGS = ROOT / 'page_readings/acreage'
PAGE_READING = {}   # (table, row, column) -> (reading, [notes])
TABLE_READING_CELLS = {}   # the part of PAGE_READING that comes from whole-table readings


def load_page_readings():
    def short(s): return re.sub(r'[^a-z]', '', s.lower())
    for path in sorted(READINGS.glob('*.tsv')):
        tid = re.sub(r'^bb(\w+?)_p(\d+)_t(\d+)$', r'bb\1:p\2:t\3', path.stem)
        lines = [l.rstrip('\n').split('\t') for l in path.open(encoding='utf-8') if l.strip()]
        grid = [l for l in lines if not l[0].startswith('!')]
        notes = {(l[0][1:].strip(), l[1]): l[2] for l in lines if l[0].startswith('!')}
        t = TABLES[tid]
        cr = next(i for i, r in enumerate(t['rows']) if any(c.startswith('Paddy') for c in r))
        head = grid[0]
        assert len(head) == len(t['rows'][cr]) and len(grid) - 1 == len(t['rows']) - cr - 2, (tid, 'grid shape')
        assert all(short(a)[:3] == short(b)[:3] for a, b in zip(head[1:], t['rows'][cr][1:])), (tid, 'crop headings')
        used = set()
        for i, row in enumerate(grid[1:]):
            ri = cr + 2 + i
            label = t['rows'][ri][0]
            if row[0] == 'TOTAL': assert total_label(label) or not label.strip(), (tid, ri, label)
            else: assert short(row[0])[:4] == short(label)[:4], (tid, ri, row[0], label)
            for ci in range(1, len(head)):
                ns = [f'read from the page image (page_readings/acreage/{path.name})']
                if (row[0], head[ci]) in notes:
                    ns.append('page reading: ' + notes[row[0], head[ci]]); used.add((row[0], head[ci]))
                PAGE_READING[tid, ri, ci] = (row[ci], ns)
        assert used == set(notes), (tid, set(notes) - used)
    TABLE_READING_CELLS.update(PAGE_READING)
    # Single cells read from the page image after the outlier check (page_readings/acreage_cells.tsv), by source
    # row and column (zero-based).
    with (ROOT / 'page_readings/acreage_cells.tsv').open(encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            key = (r['table_id'], int(r['source_row']), int(r['source_column']))
            assert key not in PAGE_READING and key[0] in TABLES, key
            PAGE_READING[key] = (r['reading'], ['read from the page image (page_readings/acreage_cells.tsv)', 'page reading: ' + r['note']])


# Printed figures judged to be misprints in the Blue Book itself (page_readings/acreage_suspect.tsv): checked on the
# page image, kept as printed, and marked in note with the reason (what the totals, the other printing or the
# neighbouring years show).
SUSPECT = {}
with (ROOT / 'page_readings/acreage_suspect.tsv').open(encoding='utf-8', newline='') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        SUSPECT[r['table_id'], int(r['source_row']), int(r['source_column'])] = r


def emit(t, ri, ci, kind, level, area, parent, measure, unit='', yd='', notes=(), split=False):
    cell = t['rows'][ri][ci]
    v = cell.strip()  # Do not remove dots from missing values.
    ns = list(notes)
    if (t['id'], ri, ci) in PAGE_READING:
        v, page_notes = PAGE_READING[t['id'], ri, ci]
        ns += page_notes
        if v != cell.strip(): ns.append(f"the OCR reads '{cell.strip()}'")
    if split:
        v, cell_unit = split_unit(v)
        if cell_unit:
            unit = cell_unit
            ns.append('source cell: ' + cell)
    value, n = number(v)
    if n: ns.append(n)
    if (t['id'], ri, ci) in SUSPECT:
        sus = SUSPECT.pop((t['id'], ri, ci))
        assert sus['value_as_printed'] == v and sus['year_data'] == str(yd), (t['id'], ri, ci, v)
        ns.append('probable misprint (page_readings/acreage_suspect.tsv): ' + sus['reason'])
    if not yd: ns.append('year_data not established explicitly')
    ns.append(f'source row {ri}, column {ci}')
    DATA.append(dict(zip(FIELDS, [t['id'],t['year'],yd,t['pdf_page'],t.get('printed_page') or '',kind,level,trim(area),trim(parent),trim(measure),trim(unit),v,value,'; '.join(x for x in ns if x)])))
    PROVENANCE.append((t['id'], ri, ci, cell, v, unit))
    return len(DATA)-1


def total_label(a):
    return bool(re.search(r'\btotal\b|^ceylon[.\s]*$',a,re.I))


def add_check(t, label, total_index, part_indices):
    tr = DATA[total_index]
    parts = [DATA[i] for i in part_indices]
    invalid = [p for p in parts if not p['value'] and not missing(p['value_as_printed'])]
    pval = tr['value']
    usable = [Decimal(p['value']) for p in parts if p['value']]
    nulls = sum(missing(p['value_as_printed']) for p in parts)
    status = ''
    computed = difference = ''
    if invalid or (not pval and not missing(tr['value_as_printed'])):
        status = 'uncheckable: unreadable numeric string'
    elif not pval:
        status = 'uncheckable: no printed numeric total'
    elif not parts or not usable:
        status = 'uncheckable: no numeric parts'
    else:
        computed = decimal_string(sum(usable, Decimal(0)))
        difference = decimal_string(Decimal(pval)-Decimal(computed))
        status = 'agree' if Decimal(difference) == 0 else 'mismatch'
    AUDIT.append([t['id'],label,tr['value_as_printed'],computed,difference,status,len(parts),nulls,len(invalid)])
    for i in [total_index]+list(part_indices): CELL_CHECKS[i].append(status)
    if status == 'mismatch':
        DATA[total_index]['note'] += '; printed total does not add up (printed minus sum = ' + difference + ')'
    elif status.startswith('uncheckable'):
        DATA[total_index]['note'] += '; total not fully checkable: ' + status.split(': ',1)[1]
    if nulls:
        DATA[total_index]['note'] += '; total check sums available numeric parts; ' + str(nulls) + ' no-figure parts'
    if invalid:
        for i in part_indices:
            if not DATA[i]['value'] and not missing(DATA[i]['value_as_printed']):
                DATA[i]['note'] += '; this cell prevents a complete total check'


def simple_acreage(tid, yd, crop_ri=0, end=None, label='', dating=None, col_years=None, col_notes=None, cell_notes=None):
    """One province-by-crop block: crop names in row crop_ri, units in the row below, provinces down to `end`.
    col_years / col_notes override the year or add notes for one column; cell_notes for one (row, column)."""
    t=TABLES[tid]; dating=dating or f'Explicit page year {yd}; paired tables follow page text year order.'
    if tid in USED: USED[tid]['dating'] += ' ' + dating
    else: register(t,'acreage_by_crop',dating)
    head=t['rows'][crop_ri]; units=t['rows'][crop_ri+1]
    first=crop_ri+2; end=len(t['rows']) if end is None else end
    col_years=col_years or {}; col_notes=col_notes or {}; cell_notes=cell_notes or {}
    grid={}; totals=[]; ordinary=[]
    for ri in range(first,end):
        r=t['rows'][ri]
        total = total_label(r[0]) or not r[0].strip()
        if total: totals.append(ri)
        else: ordinary.append(ri)
        for ci in range(1,len(r)):
            ns=(['printed total'] if total else [])+col_notes.get(ci,[])+cell_notes.get((ri,ci),[])
            grid[ri,ci]=emit(t,ri,ci,'acreage_by_crop','colony_total' if total else 'province',r[0],'',head[ci],units[ci],col_years.get(ci,yd),ns)
    ncols=len(head)
    totalcols=[ci for ci in range(1,ncols) if total_label(head[ci])]
    for ri in range(first,end):
        for ci in totalcols:
            add_check(t,'area: '+(trim(t['rows'][ri][0]) or '(unlabelled colony total)')+label,grid[ri,ci],[grid[ri,c] for c in range(1,ncols) if c not in totalcols])
    for ri in totals:
        for ci in range(1,ncols):
            add_check(t,'measure: '+trim(head[ci])+label,grid[ri,ci],[grid[r,ci] for r in ordinary])


load_page_readings()

for tid,yd in [('bb1869:p11:t2',1868),('bb1869:p11:t3',1869),('bb1902:p16:t1',1901),('bb1902:p16:t2',1902),('bb1904:p18:t1',1903),('bb1904:p18:t2',1904),('bb1912:p16:t4',1911),('bb1912:p17:t1',1912)]:
    simple_acreage(tid,yd)

# Second pass: the opening "Agricultural Statistics" of the other volumes. Each page prints the previous year's
# table and then the volume year's, with the years as captions between them (read from the page text and checked
# against the page images for 1885, 1910, 1911, 1921 and 1922). Where two volumes print the same year, the figures
# agree (for example 1905 in the 1905 and 1906 volumes).
FOOTNOTE_SKIP = re.compile(r'Spinning|[Cc]itronella|Cloth is manufactured|Figures not available|nearest (?:hundred|thousand)')


def footnote_notes(tid):
    """A note for each cell carrying a footnote mark, quoting the page footnote with that mark when there is exactly one."""
    t=TABLES[tid]; key=tid[2:].split(':')[0]
    lines=[x.strip() for x in PAGES[key,t['pdf_page']]['text'] if x.strip()[:1] in '*†‡§' and not FOOTNOTE_SKIP.search(x)]
    out={}
    for ri,r in enumerate(t['rows']):
        for ci,c in enumerate(r):
            m=re.search(r'[*†‡§]',c)
            if not m or ci==0: continue
            found=[x for x in lines if x.startswith(m[0])]
            out[ri,ci]=['page footnote: '+found[0]] if len(found)==1 else ['footnote mark '+m[0]+'; no matching footnote found in the page text']
    return out


def column_footnotes(tid, crop_ri):
    """A footnote mark in a crop or unit heading applies to the whole column."""
    t=TABLES[tid]; cells=footnote_notes(tid); out={}
    for (ri,ci),ns in cells.items():
        if ri in (crop_ri,crop_ri+1): out.setdefault(ci,[]).extend(ns)
    return out, {k:v for k,v in cells.items() if k[0] not in (crop_ri,crop_ri+1)}


PERIOD_1910 = 'period printed as January 1, 1910, to June 30, 1911 (the Blue Book year changed); year_data gives the first year'
CENSUS_1921 = 'from the Census of Production, 1921 (page footnote)'
SECOND_PASS = [
    # (table, data year, crop row, end row, notes for every cell)
    ('bb1863:p10:t2',1862,0,9,[]), ('bb1863:p10:t2',1863,10,None,[]),
    ('bb1866:p11:t2',1865,0,None,[]), ('bb1866:p11:t3',1866,0,None,[]),
    ('bb1868:p11:t2',1867,0,None,[]), ('bb1868:p11:t3',1868,0,None,[]),
    ('bb1871:p13:t2',1870,0,None,[]), ('bb1871:p13:t3',1871,0,None,[]),
    ('bb1880:p8:t4',1879,0,None,[]), ('bb1880:p8:t5',1880,0,None,[]),
    ('bb1881:p10:t5',1880,0,None,[]), ('bb1881:p10:t6',1881,0,None,[]),
    ('bb1882:p10:t6',1881,1,None,[]), ('bb1882:p11:t1',1882,0,None,[]),
    ('bb1883:p10:t4',1882,0,None,[]), ('bb1883:p11:t1',1883,0,None,[]),
    ('bb1885:p13:t1',1884,0,None,[]), ('bb1885:p13:t2',1885,0,None,[]),
    ('bb1886:p13:t1',1885,0,None,[]), ('bb1886:p13:t2',1886,0,None,[]),
    ('bb1887:p14:t2',1886,0,None,[]), ('bb1887:p14:t3',1887,0,None,[]),
    ('bb1889b:p14:t2',1888,0,None,[]), ('bb1889b:p14:t3',1889,0,None,[]),
    ('bb1890:p295:t1',1889,0,None,[]), ('bb1890:p295:t2',1890,0,None,[]),
    ('bb1891:p297:t1',1890,0,None,[]), ('bb1891:p297:t2',1891,0,None,[]),
    ('bb1892:p310:t1',1891,0,None,[]), ('bb1892:p310:t2',1892,0,None,[]),
    ('bb1893:p18:t1',1892,0,None,[]), ('bb1893:p18:t2',1893,0,None,[]),
    ('bb1894:p14:t1',1893,0,None,[]), ('bb1894:p14:t2',1894,0,None,[]),
    ('bb1896:p15:t1',1895,0,None,[]), ('bb1896:p15:t2',1896,0,None,[]),
    ('bb1897:p17:t1',1896,0,None,[]), ('bb1897:p17:t2',1897,0,None,[]),
    ('bb1898:p15:t1',1897,0,None,[]), ('bb1898:p15:t2',1898,0,None,[]),
    ('bb1899:p15:t1',1898,0,None,[]), ('bb1899:p15:t2',1899,0,None,[]),
    ('bb1900:p18:t1',1899,0,None,[]), ('bb1900:p18:t2',1900,0,None,[]),
    ('bb1901:p16:t1',1900,0,None,[]), ('bb1901:p16:t2',1901,0,None,[]),
    ('bb1903:p18:t1',1902,0,None,[]), ('bb1903:p18:t2',1903,0,None,[]),
    ('bb1905:p15:t1',1904,0,None,[]), ('bb1905:p15:t2',1905,0,None,[]),
    ('bb1906:p16:t1',1905,0,None,[]), ('bb1906:p16:t2',1906,0,None,[]),
    ('bb1907:p17:t1',1906,0,None,[]), ('bb1907:p17:t2',1907,0,None,[]),
    ('bb1908:p14:t2',1907,0,None,[]), ('bb1908:p14:t3',1908,0,None,[]),
    ('bb1910:p14:t2',1909,0,None,[]), ('bb1910:p14:t3',1910,0,None,[PERIOD_1910]),
    ('bb1911:p14:t2',1910,0,None,[PERIOD_1910]), ('bb1911:p14:t3',1911,0,None,[]),
    ('bb1913:p15:t2',1912,0,None,[]), ('bb1913:p15:t3',1913,0,None,[]),
    ('bb1914:p15:t2',1913,0,None,[]), ('bb1914:p15:t3',1914,0,None,[]),
    ('bb1915:p14:t3',1914,1,None,[]), ('bb1915:p14:t4',1915,1,None,[]),
    ('bb1916:p16:t3',1915,1,None,[]), ('bb1916:p16:t4',1916,1,None,[]),
    ('bb1917:p15:t2',1916,0,None,[]), ('bb1917:p15:t3',1917,0,None,[]),
    ('bb1918:p15:t2',1917,0,None,[]), ('bb1918:p15:t3',1918,0,None,[]),
    ('bb1919:p14:t2',1918,0,None,[]), ('bb1919:p14:t3',1919,0,None,[]),
    ('bb1920:p15:t2',1919,0,None,[]), ('bb1920:p15:t3',1920,0,None,[]),
    ('bb1921:p15:t2',1920,0,None,['from the Blue Book for 1920 (page footnote)']),
    ('bb1921:p15:t3',1921,0,None,[CENSUS_1921]),
    ('bb1922:p15:t2',1921,0,None,[CENSUS_1921]),
    ('bb1922:p15:t3',1922,0,None,'census'), ('bb1923:p15:t2',1922,0,None,'census'), ('bb1923:p15:t3',1923,0,None,'census'),
]
for tid,yd,crop_ri,end,notes in SECOND_PASS:
    head=TABLES[tid]['rows'][crop_ri]
    col_notes,cell_notes=column_footnotes(tid,crop_ri)
    col_years={}
    if notes=='census':
        # Page footnote: figures other than paddy, other grains and cotton (which are for the year) are from the 1921 census.
        for ci in range(1,len(head)):
            if not re.match(r'Paddy|Other Grain|Cotton',head[ci]):
                col_years[ci]=1921
                col_notes.setdefault(ci,[]).append(f'printed in the {yd} table but {CENSUS_1921}; only paddy, other grains and cotton are for {yd}')
        notes=[]
    for ci in range(1,len(head)): col_notes[ci]=notes+col_notes.get(ci,[])
    two_blocks=sum(1 for x in SECOND_PASS if x[0]==tid)>1
    simple_acreage(tid,yd,crop_ri,end,f' [{yd}]' if two_blocks else '',
                   dating=f'{yd}: year caption printed above the table; previous-year table first.' if not two_blocks else f'{yd}: block captioned {yd}.',
                   col_years=col_years,col_notes=col_notes,cell_notes=cell_notes)

# Colony-wide livestock summaries, each header supplies its own year.
for tid in ['bb1869:p11:t4','bb1902:p16:t3','bb1904:p18:t3','bb1912:p17:t2']:
    t=TABLES[tid]; register(t,'live_stock','Year printed in each numeric column header.')
    blocks=[0] if t['year']==1869 else [0,3]
    for ri,r in enumerate(t['rows'][1:],1):
        for base in blocks:
            if base and not r[base]: continue
            for ci in [base+1,base+2]:
                if not r[base] and not r[ci]:continue
                emit(t,ri,ci,'live_stock','colony_total','','',r[base],'',int(t['rows'][0][ci].rstrip('.')),['colony-wide summary; area label not printed']+(['printed total'] if not r[base] else []))


def province_row(r):
    return bool(r and re.search(r'province',r[0],re.I) and (r[0]==r[1] or all(not c.strip() for c in r[1:])))


def heading_row(r):
    # The first three columns repeat an expanded heading; extra OCR columns may differ.
    return bool(r[0].strip() and len(r)>2 and r[0]==r[1]==r[2])

# District returns with crop / animal names down the rows. Only primary acreage,
# gross produce and current stock counts are in scope; prices, yields and changes are excluded.
for y,cp,sp in [(1902,range(680,687),range(687,690)),(1904,range(726,733),range(733,736)),(1912,range(253,261),range(261,264))]:
    for pages,stock in [(cp,False),(sp,True)]:
        parent=area=''
        for page in pages:
            t=TABLES[f'bb{y}:p{page}:t1']
            register(t,'land_produce_stock','No explicit reporting year in table or page text; year_data left empty.')
            for ri,r in enumerate(t['rows'][t['header_rows']:],t['header_rows']):
                if heading_row(r):
                    if 'PROVINCE' in r[0].upper():
                        parent=trim(r[0]);area=''
                    else:
                        area=trim(r[0])
                    continue
                if not r[0].strip():
                    # Standalone units/narrative spacer rows, not observations.
                    continue
                assert area and parent, (t['id'],ri,'missing district context')
                # An inherited district continuation label is preserved as printed.
                ns=[]
                if 'contd' in area:ns.append('district continuation heading retained as printed')
                for ci in ([1] if stock else [1,2]):
                    stat=t['rows'][0][ci]
                    unit=''
                    if not stock and ci==1:
                        unit='Acres'  # exact word in the column header
                    notes=ns+['statistic: '+stat]
                    if ci==2 and (r[ci].startswith('Rs.') or (ri>0 and t['rows'][ri-1][ci]=='Rs. c.')):
                        notes.append('gross produce reported as monetary value; no currency conversion')
                    if t['id']=='bb1904:p727:t1' and ri==2 and ci==2:
                        notes.append('suspect OCR magnitude or unit (10,168,000 cwt.); retained without correction')
                    # Units standing alone immediately above a row apply to that row only.
                    if ri>0 and not t['rows'][ri-1][0].strip() and re.fullmatch(UNIT_PATTERN,t['rows'][ri-1][ci].strip(),re.I):
                        unit=t['rows'][ri-1][ci].strip()
                        notes.append('unit from source row '+str(ri-1))
                    emit(t,ri,ci,'land_produce_stock','district',area,parent,r[0],unit,'',notes,split=(ci==2))

# Land / acreage returns with districts across rows.
for tid in ['bb1869:p530:t1','bb1902:p690:t1','bb1904:p736:t1','bb1912:p264:t1','bb1924:p397:t1']:
    t=TABLES[tid]
    yd=1923 if t['year']==1924 else ''
    dating='Page footnote explicitly says figures are for 1923.' if yd else 'No explicit reporting year in table/page text; year_data left empty.'
    register(t,'land_produce_stock',dating)
    parent=''
    for ri,r in enumerate(t['rows'][t['header_rows']:],t['header_rows']):
        if province_row(r):
            parent=trim(r[0]);continue
        a=r[0]
        total=total_label(a) or not a.strip()
        if total:
            colony=bool(re.search(r'grand total|^ceylon',a,re.I)) or (t['year']==1869 and bool(a.strip()))
            level='colony_total' if colony else 'province'
        elif 'province' in a.lower():
            parent=trim(a);level='province'
        else:level='district'
        for ci in range(1,len(r)):
            if t['header_rows']==1:
                measure=t['rows'][0][ci]
            else:measure=t['rows'][1][ci]
            stat=t['rows'][0][ci]
            # Keep complete printed header in measure and the upper header in note.
            unit='Acres' if 'Acres' in stat else ''
            ns=(['printed total'] if total else [])+(['column group: '+stat] if stat!=measure else [])
            emit(t,ri,ci,'land_produce_stock',level,a,'' if level=='colony_total' else parent,measure,unit,yd,ns)

# One unambiguous 1869 crop/stock block (other blocks are rejected below).
t=TABLES['bb1869:p535:t1'];register(t,'land_produce_stock','Facing page 536 heading explicitly says STOCK, &c, 1869.; Western Province block.')
for ri,r in enumerate(t['rows'][3:],3):
    for ci in range(1,len(r)):
        total=total_label(r[0])
        unit='Acres' if ci<=13 else ''
        if ci==11:unit='acres' # printed lower-case in this column
        emit(t,ri,ci,'land_produce_stock','province' if total else 'district',r[0],'WESTERN PROVINCE.',t['rows'][2][ci],unit,1869,['statistic: '+t['rows'][1][ci]]+(['printed total'] if total else []))

# Later stock summaries: retain provincial and colony totals as well as districts;
# price columns are explicitly outside the requested count measures.
for tid in ['bb1924:p400:t1','bb1926:p318:t1','bb1928:p330:t1']:
    t=TABLES[tid];register(t,'live_stock','No explicit year for the count table in page text; year_data left empty.')
    parent='';fragment=''
    for ri,r in enumerate(t['rows'][t['header_rows']:],t['header_rows']):
        if r[0]=='Province of' and all(not c for c in r[1:]):
            fragment=r[0];continue
        a=r[0];ns=[]
        if fragment:
            # Do not manufacture an area string by joining source cells.
            ns.append('province heading prefix in preceding source row: '+fragment)
            fragment=''
            isprov=True
        else:isprov='province' in a.lower()
        if isprov:
            parent=trim(a)
            if all(not c.strip() for c in r[1:]):continue
            level='province'
        elif re.fullmatch(r'CEYLON\.?',a,re.I):level='colony_total'
        else:level='district'
        for ci in range(1,len(r),2):
            emit(t,ri,ci,'live_stock',level,a,'' if level=='colony_total' else parent,t['rows'][0][ci],'','',ns+['statistic: '+t['rows'][1][ci]]+(['printed total'] if level=='colony_total' else []))

# 1928 prints the province summaries together followed by all revenue districts.
t=TABLES['bb1928:p327:t1'];register(t,'acreage_by_crop','Rubber: July 1928 census, explicitly stated in page text. Other crops: mixed census-based estimates (1921/1924), no unique data year.')
grid={}; area_levels={}; province_indices=[]; district_indices=[]
# Parents are taken verbatim from this table's explicit province summary labels.
parents={
 13:4,14:4,15:5,16:5,17:5,18:6,19:6,20:6,21:7,22:7,23:7,24:8,25:8,
 26:9,27:9,28:9,29:10,30:11,31:12,32:12}
for ri,r in enumerate(t['rows'][3:],3):
    level='colony_total' if ri==3 else ('province' if ri<=12 else 'district')
    area_levels[ri]=level
    if level=='province':province_indices.append(ri)
    if level=='district':district_indices.append(ri)
    for ci in range(1,len(r)):
        yd=1928 if ci==12 else ''
        ns=['census of rubber in July 1928'] if yd else ['estimate based on Censuses of Production, 1921 and 1924; single year cannot be assigned']
        if level=='colony_total':ns.append('printed total')
        grid[ri,ci]=emit(t,ri,ci,'acreage_by_crop',level,r[0],t['rows'][parents[ri]][0] if ri in parents else '',t['rows'][2][ci],'Acres',yd,ns)
for ci in range(1,len(t['rows'][0])):
    add_check(t,'measure: '+trim(t['rows'][2][ci])+'; Ceylon vs provinces',grid[3,ci],[grid[r,ci] for r in province_indices])
    for pri in province_indices:
        parts=[r for r in district_indices if parents[r]==pri]
        add_check(t,'measure: '+trim(t['rows'][2][ci])+'; '+t['rows'][pri][0]+' vs districts',grid[pri,ci],[grid[r,ci] for r in parts])

# Second printings. Each volume reprints the previous year's acreage table, so most figures are printed twice, set in
# type and read by OCR separately. Match them on data year, area and crop (printed spellings joined, nothing else
# changed), note the other printing on each figure, and say which printing the totals checks favour where they differ.
CROP_SPELLINGS = {'cocoanuts':'coconuts','coconutts':'coconuts','coconnuts':'coconuts','cinna mon':'cinnamon','cinamon':'cinnamon',
                  'other grains':'other grain','pasturage':'pasture','cocoa':'cacao'}


def match_key(r):
    def norm(s):
        s=re.sub(r'(\w)[-‐]\s*(\w)',r'\1\2',s.lower()); s=re.sub(r'[^a-z ]',' ',s); return re.sub(r'\s+',' ',s).strip()
    area=norm(r['area_as_printed']); area='total' if area in ('','total','ceylon') else area
    crop=norm(r['measure_as_printed']); crop=CROP_SPELLINGS.get(crop,crop)
    return r['year_data'],area,crop


def totals_verdict(i):
    st=[x for x in CELL_CHECKS.get(i,[]) if not x.startswith('uncheckable')]
    return '' if not st else ('adds up' if all(x=='agree' for x in st) else 'does not add up')


def volume_of(tid): return tid[2:].split(':')[0]


PRINTINGS=defaultdict(list)
for i,r in enumerate(DATA):
    if r['table_kind']=='acreage_by_crop' and r['year_data']: PRINTINGS[match_key(r)].append(i)
REPRINTS=[]
for key,idx in PRINTINGS.items():
    if len({volume_of(DATA[i]['table_id']) for i in idx})<2: continue
    for i in idx:
        r=DATA[i]; mine=totals_verdict(i)
        for j in idx:
            o=DATA[j]
            if volume_of(o['table_id'])==volume_of(r['table_id']): continue
            where=f"the {volume_of(o['table_id'])} volume ({o['table_id']})"
            theirs=totals_verdict(j)
            both_blank=missing(r['value_as_printed']) and missing(o['value_as_printed'])
            if (r['value'] and r['value']==o['value']) or both_blank or (not r['value'] and r['value_as_printed']==o['value_as_printed']):
                status='agree'; r['note']+=f'; second printing: same figure in {where}'
            else:
                status='differ' if r['value'] and o['value'] else 'one missing or unreadable'
                verdict={('adds up','does not add up'):'the totals favour this printing',('does not add up','adds up'):'the totals favour the other printing',
                         ('adds up','adds up'):'both printings add up (a revision, or errors that cancel)',('does not add up','does not add up'):'neither printing adds up'}.get((mine,theirs),'the totals cannot decide')
                shown=o['value_as_printed'] if o['value_as_printed'].strip() else '(blank)'
                r['note']+=f'; second printing: {where} prints {shown}; {verdict}'
            if i<j: REPRINTS.append([*key,r['table_id'],r['value_as_printed'],r['value'],mine,o['table_id'],o['value_as_printed'],o['value'],theirs,status])

# Extra diagnostics on non-acreage_by_crop tables. They annotate suspect printed
# totals too, without mixing these comparisons into the requested acreage report.
ACREAGE_AUDIT = list(AUDIT)
CELL_INDEX = {(tid,ri,ci):i for i,(tid,ri,ci,*_) in enumerate(PROVENANCE)}

def check_cells(t, label, target, parts):
    if (t['id'],*target) not in CELL_INDEX:return
    ids=[CELL_INDEX[t['id'],*p] for p in parts if (t['id'],*p) in CELL_INDEX]
    add_check(t,label,CELL_INDEX[t['id'],*target],ids)

for tid in ['bb1869:p530:t1','bb1902:p690:t1','bb1904:p736:t1','bb1912:p264:t1']:
    t=TABLES[tid]; groups=[]; district_rows=[]; subtotal=None
    for ri,r in enumerate(t['rows'][t['header_rows']:],t['header_rows']):
        if province_row(r):
            if district_rows:groups.append((list(district_rows),subtotal))
            district_rows=[];subtotal=None
            continue
        if total_label(r[0]) or not r[0].strip():
            if ri==len(t['rows'])-1:
                # Final colony total: use each province subtotal, or its district
                # observations when that province has no printed subtotal.
                if district_rows:groups.append((list(district_rows),subtotal))
                agg=[sub for ds,sub in groups if sub is not None]
                agg += [d for ds,sub in groups if sub is None for d in ds]
                for ci in range(1,len(r)):
                    check_cells(t,'colony total: '+DATA[CELL_INDEX[tid,ri,ci]]['measure_as_printed'],(ri,ci),[(d,ci) for d in agg])
            else:
                subtotal=ri
                for ci in range(1,len(r)):
                    check_cells(t,'province subtotal: '+DATA[CELL_INDEX[tid,ri,ci]]['parent_area_as_printed']+'; '+DATA[CELL_INDEX[tid,ri,ci]]['measure_as_printed'],(ri,ci),[(d,ci) for d in district_rows])
        else:district_rows.append(ri)
        tc=3 if t['year']==1869 else 4
        check_cells(t,'area: '+(trim(r[0]) or '(unlabelled subtotal)'),(ri,tc),[(ri,ci) for ci in range(1,tc)])

t=TABLES['bb1869:p535:t1']
for ci in range(1,18):
    check_cells(t,'Western Province total; '+t['rows'][2][ci],(6,ci),[(r,ci) for r in [3,4,5]])
# Crop total columns may include/exclude pasture or selected crops, so the district
# return's acreage total is not presumed to equal every adjacent crop column.

for tid in ['bb1924:p397:t1','bb1924:p400:t1','bb1926:p318:t1','bb1928:p330:t1']:
    t=TABLES[tid];cis=list(range(1,len(t['rows'][0]))) if tid.endswith('397:t1') else list(range(1,len(t['rows'][0]),2))
    by_row=defaultdict(dict)
    for (table,ri,ci),idx in CELL_INDEX.items():
        if table==tid:by_row[ri][ci]=idx
    provinces=[];districts=defaultdict(list);colony=None;parent_ri=None
    for ri,cols in sorted(by_row.items()):
        row=DATA[next(iter(cols.values()))]
        if row['area_level']=='colony_total':colony=ri
        elif row['area_level']=='province':provinces.append(ri);parent_ri=ri
        else:
            # Some single-district province headings have no numeric row.
            # Do not attach those districts to the preceding numeric province.
            if parent_ri is not None and row['parent_area_as_printed']==DATA[by_row[parent_ri][cis[0]]]['area_as_printed']:
                districts[parent_ri].append(ri)
            else:provinces.append(ri);parent_ri=None
        if tid.endswith('397:t1'):
            check_cells(t,'cultivated total: '+row['area_as_printed'],(ri,4),[(ri,c) for c in [1,2,3]])
    for pri,ds in districts.items():
        for ci in cis:
            check_cells(t,'province total: '+DATA[by_row[pri][ci]]['area_as_printed']+'; '+DATA[by_row[pri][ci]]['measure_as_printed'],(pri,ci),[(r,ci) for r in ds])
    if colony is not None:
        for ci in cis:
            check_cells(t,'colony total: '+DATA[by_row[colony][ci]]['measure_as_printed'],(colony,ci),[(r,ci) for r in provinces])
OTHER_AUDIT = AUDIT[len(ACREAGE_AUDIT):]
AUDIT = ACREAGE_AUDIT

# Explicit review decisions for the remaining candidate tables.
for t in TABLES.values():
    tid=t['id'];y=t['year'];p=t['pdf_page']
    if tid in USED:continue
    if y==1869 and 535<=p<=542:
        SKIPPED[tid]='Complex crop/produce block: shifted or absent area/column labels, subdistrict hierarchy or unlabelled continuation; not safely aligned.'
    if tid=='bb1869:p541:t1':
        SKIPPED[tid]='Price-only table; outside the requested acreage, produce quantities and stock counts.'
    if tid=='bb1869:p540:t2':
        SKIPPED[tid]='Monetary values of produce in pounds/shillings/pence, rather than produce quantities; outside requested measures.'
    if (y,p) in [(1902,691),(1904,737),(1912,265)]:
        SKIPPED[tid]='Unlabelled continuation of uncultivated-land return; district/province row alignment cannot be established safely.'
    if (y,p) in [(1924,395),(1924,396)]:
        SKIPPED[tid]='Crop headers are shifted against data columns (and some row labels/figures also shift); no safe crop-to-number mapping.'
    if (y,p) in [(1925,305),(1926,315),(1925,308)]:
        SKIPPED[tid]='Province totals occur beside district labels, followed by an unlabelled numeric row; refusing to reassign printed area labels.'
    if (y,p) in [(1933,219),(1934,221)]:
        SKIPPED[tid]='Collapsed side-by-side crops/livestock layout: livestock figures appear beside crop names; crop figures/animal labels missing.'

# Candidate discovery independently scans all table headers, including continuations
# with no section/headings; broad historical progress tables and prices/wages are out of scope.
CANDIDATES={}
for tid,t in TABLES.items():
    meta=' '.join([t.get('section') or '']+t.get('headings',[]))
    top=' '.join(c for r in t['rows'][:max(t['header_rows'],1)] for c in r)
    first=t['rows'][0] if t['rows'] else []
    reasons=[]
    if re.search(r'Nature of Crop\.|Nature of Live Stock\.',top,re.I):reasons.append('district return header')
    if first and re.fullmatch(r'Province\.?',first[0],re.I) and re.search(r'Paddy',top,re.I):reasons.append('province crop summary')
    if re.search(r'Cultivated.*Uncultivated|Cultivated.*Pasture.*Waste',meta,re.I):reasons.append('land return heading')
    if re.fullmatch(r'(?:CULTIVATED AND|UNCULTIVATED LANDS, &c\.)',meta,re.I):reasons.append('land return continuation')
    if re.search(r'Nature of Crops|Acreages under Crops|Crops and Live Stock',meta,re.I):reasons.append('crop/stock section')
    if re.fullmatch(r'Live Stock',t.get('section') or '',re.I):reasons.append('stock section')
    if re.search(r'Number of Live Stock',meta,re.I) and any(re.fullmatch(r'18\d\d\.|19\d\d\.',c) for c in first) and len(first) in [3,6]:reasons.append('colony livestock summary')
    if tid=='bb1869:p11:t4' or (t['year']==1869 and 535<=t['pdf_page']<=542):reasons.append('reviewed early produce block')
    if reasons or tid in USED or tid in SKIPPED:
        CANDIDATES[tid]='; '.join(reasons) or 'reviewed target'
        if tid not in USED and tid not in SKIPPED:
            SKIPPED[tid]=('Not reviewed: the second pass took only the opening Agricultural Statistics tables from this volume.'
                          if tid[2:].split(':')[0] in MORE_VOLUMES else 'Candidate layout not reviewed sufficiently for safe extraction.')


def write_tsv(path, header, rows):
    with path.open('w',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(header);w.writerows(rows)


assert not SUSPECT, ('suspect cells not emitted', list(SUSPECT))
OUT.mkdir(exist_ok=True)
write_tsv(OUT/'agriculture.tsv',FIELDS,([r[k] for k in FIELDS] for r in DATA))
write_tsv(OUT/'agriculture_skipped.tsv',['table_id','reason'],sorted(SKIPPED.items(),key=lambda x:(TABLES[x[0]]['year'],TABLES[x[0]]['pdf_page'],x[0])))
write_tsv(OUT/'agriculture_second_printing.tsv',['year_data','area','crop','table_id','value_as_printed','value','totals','other_table_id','other_value_as_printed','other_value','other_totals','status'],sorted(REPRINTS))
write_tsv(OUT/'agriculture_checks.tsv',['table_id','area_or_measure','printed_total','computed_sum','difference'],(r[:5] for r in AUDIT if r[5]!='agree'))
write_tsv(WORK/'totals_audit.tsv',['table_id','area_or_measure','printed_total','computed_sum','difference','status','part_count','missing_part_count','unreadable_part_count'],AUDIT)
write_tsv(WORK/'other_totals_audit.tsv',['table_id','area_or_measure','printed_total','computed_sum','difference','status','part_count','missing_part_count','unreadable_part_count'],OTHER_AUDIT)
write_tsv(WORK/'source_cells.tsv',['table_id','source_row','source_column','source_cell','value_as_printed','unit_as_printed'],PROVENANCE)
counts=Counter(r['table_id'] for r in DATA)
write_tsv(WORK/'candidate_inventory.tsv',['table_id','year_volume','kind','decision','row_count','discovery','dating_or_reason'],([tid,TABLES[tid]['year'],USED.get(tid,{}).get('kind',''),'used' if tid in USED else 'skipped',counts[tid],reason,USED[tid]['dating'] if tid in USED else SKIPPED[tid]] for tid,reason in sorted(CANDIDATES.items(),key=lambda x:(TABLES[x[0]]['year'],TABLES[x[0]]['pdf_page'],x[0]))))

agreements=sum(r[5]=='agree' for r in AUDIT);mismatches=sum(r[5]=='mismatch' for r in AUDIT);uncheckable=len(AUDIT)-agreements-mismatches
numeric=sum(bool(r['value']) for r in DATA)
lines=['# Agriculture extract','',
 f'{len(DATA):,} observation rows from {len(USED)} tables; {numeric:,} numeric values. Missing-value cells are retained as rows. {len(SKIPPED)} candidate tables were skipped. The first pass searched 13 volumes for all three kinds of table; a second pass (below) took the opening Agricultural Statistics tables from {len(MORE_VOLUMES)} more. This is a selective extraction, not complete coverage of every volume.','',
 'Rebuild from this folder using the standard library only:','',
 '```sh','/home/jic823/miniforge3/bin/python jobs/agriculture_work/extract_agriculture.py','/home/jic823/miniforge3/bin/python jobs/agriculture_work/validate_agriculture.py','```','',
 '## Coverage','',
 '| Volume | Kind | Tables used (observation rows) |','| --- | --- | --- |']
for y in sorted([str(y) for y in YEARS]+MORE_VOLUMES):
    found=False
    for kind in ['acreage_by_crop','land_produce_stock','live_stock']:
        ids=[tid for tid,u in USED.items() if tid[2:].split(':')[0]==y and u['kind']==kind]
        if ids:
            found=True;lines.append(f'| {y} | {kind} | '+', '.join(f'{tid} ({counts[tid]})' for tid in ids)+' |')
    if not found:lines.append(f'| {y} | — | No tables extracted |')
lines += ['', 'The complete reviewed candidate inventory, including per-table dating decisions and counts, is in `jobs/agriculture_work/candidate_inventory.tsv`. Each excluded candidate has a reason in `agriculture_skipped.tsv`.', '',
 '## Second pass: opening Agricultural Statistics, 1862–1923','',
 'Almost every volume opens with a summary "Agricultural Statistics": acres under each crop by province, printed twice, for the previous year and for the volume year. The first pass took these from 1869, 1902, 1904, 1912 and 1928 only. The second pass (`SECOND_PASS` in the script) adds the pair from every other volume that prints one, read with the same rules as the first pass (`simple_acreage`), so every printed total is checked the same way.','',
 '- Years: the year captions printed between the two tables, read from the page text; the order (previous year first) was checked against the page images for 1885, 1910, 1911, 1921 and 1922. Where two volumes print the same year the figures agree, apart from OCR digit slips.',
 '- 1863 prints both years (1862, 1863) as two blocks of one parsed table; checks are labelled with the year in brackets.',
 '- 1877 prints no table: the page says the agricultural returns for 1877 were found so defective that they were not given.',
 '- 1910 and 1911: the Blue Book year changed, and one table covers January 1, 1910, to June 30, 1911. Its figures carry year_data 1910 and a note giving the period. It is printed in both volumes.',
 '- 1921–1923: the 1921 table is from the Census of Production, 1921. In the 1922 and 1923 volumes only paddy, other grains and cotton are for the year printed; the other crops repeat the 1921 census figures (page footnote), so those figures carry year_data 1921 and a note.',
 '- Footnote marks in a figure or heading (for example the tea totals 1901–1911, which a footnote compares with Ferguson\'s Directory, or rubber 1914–1921, interplanted or excluding small holdings) carry the footnote text in note.',
 '- Crop names are as printed: Cocoanuts, Coconuts, Cocoa-nuts; Cocoa and Cacao; Pasture and Pasturage. Units as printed (Acres, Acre, OCR "Aeres", "Acrea").',
 '- Not taken in this pass: the district returns that follow later in each volume, and livestock.','',
 '## Second printings','',
 f'Each volume reprints the previous year\'s table, so most acreage figures are printed twice, set in type and read by OCR separately. `agriculture_second_printing.tsv` pairs every figure with its other printings (same data year, area and crop; printed crop spellings such as Cocoanuts/Coconuts joined): {len(REPRINTS):,} pairs, {sum(x[-1]=="agree" for x in REPRINTS):,} the same, {sum(x[-1]=="differ" for x in REPRINTS)} different, {sum(x[-1]!="agree" and x[-1]!="differ" for x in REPRINTS)} with one side blank or unreadable. Each figure\'s note names its other printing; where they differ it gives the other figure and which printing the totals checks favour. The 1921 census figures repeated in 1922 and 1923 are paired too.','',
 f'Where two printings differ, `totals` / `other_totals` say whether the totals each takes part in add up. One adds up and the other does not in {sum(x[-1]=="differ" and {x[6],x[10]}=={"adds up","does not add up"} for x in REPRINTS)} pairs: the one that adds up is most likely the right reading. Neither adds up in {sum(x[-1]=="differ" and x[6]==x[10]=="does not add up" for x in REPRINTS)}; both add up in {sum(x[-1]=="differ" and x[6]==x[10]=="adds up" for x in REPRINTS)}, which suggests a revision between editions or two errors that cancel. No figure is changed on this evidence.','',
 '## Page-image readings, 1879–1891','',
 f'The OCR of the opening tables for 1879–1891 misreads many figures: it drops or merges digits (the 1881 volume gives coffee as 34,460 and 36,183 acres for 341,460½ and 361,838½) and confuses 3 with 8 and 5 with 6. These {len({k[0] for k in TABLE_READING_CELLS})} tables (the data years 1879–1891, each printed in its own volume and again in the next where that survives) were read by eye from the archive.org page images. `page_readings/acreage/` holds one file per table, the grid in the parsed table\'s row and column order with notes on single cells. The readings replace the OCR string in value_as_printed for {len(TABLE_READING_CELLS):,} cells; {sum(v!=TABLES[k[0]]["rows"][k[1]][k[2]].strip() for k,(v,_) in TABLE_READING_CELLS.items())} of them differ from the OCR, and those quote the OCR string in note. source_cells.tsv keeps the OCR string. Labels (provinces and crops) are still the OCR\'s.','',
 '- A reading is what the page shows, not a corrected figure. Where the print is faint, broken or blotted, or a 3 prints like an 8, the reading takes the digit the totals and the other printing require, and a note says so. Where a figure is clearly printed but does not add up, it is kept and the note gives what the totals imply: for example 1880 Eastern coconuts (57786, the totals imply 37786), the 1880 tobacco total misprinted 99957, the 1883 coffee total (292779; the provinces add to 292679) and the 1891 cinchona total (12127; Central and Uva add to 12172).',
 '- 1888: the Uva figure for coffee and cacao is printed once (56073) across both columns, and the coffee, cacao and tea totals exclude Uva (page footnote). The reading puts 56073 in the Coffee column, with a note, and leaves Cacao blank.',
 '- Cinchona: the summary table has no cinchona column in 1880 or 1882–1885; this is the printed table, not a reading gap. From 1886 to 1891 the provinces reporting cinchona change from year to year (1886 Central only; 1887 Uva only; 1888 Central only; 1890 Sabaragamuwa 27000).','',
 f'Misprints in the Blue Book itself stay as printed. {len(open(ROOT/"page_readings/acreage_suspect.tsv").readlines())-1} printed figures that the page images, the totals, the other printing or the neighbouring years show to be wrong (for example 1885 Western cinnamon 112021, 1863 Southern cotton 105806, 1890 Sabaragamuwa cinchona 27000) are listed in `page_readings/acreage_suspect.tsv` and marked in note with "probable misprint" and the reason. The viewer chart draws them as hollow points.','',
 'An outlier check of every acreage series (see `page_readings/README.md`) found five more OCR misreadings outside these tables, read from the page images and applied the same way: `page_readings/acreage_cells.tsv` (1921 Eastern paddy 103380 in the 1922 volume, 1904 Sabaragamuwa paddy 89469 in the 1905 volume, 1895 Northern paddy 52887, 1894 Sabaragamuwa cacao 1111 and North-Western coffee 876). Its other findings (`page_readings/acreage_outliers.tsv`) are figures the page prints, including misprints in one volume that the other volume prints correctly; those are left as printed, and their second-printing notes give the other figure.','',
 '## Reading the fields','',
 '- The source is OCR, except for the page-image readings above. “As printed” means the supplied OCR string, with whitespace at the edges and trailing dot leaders removed from labels. Single punctuation dots, accents, hyphenation, spelling and OCR errors are retained. Missing-value strings such as `...` are preserved unchanged in value_as_printed.',
 '- Each row corresponds to one selected source measurement cell, including blank and no-figure cells. Zero-based source row and column are recorded in note; the unaltered cell is also recorded in `jobs/agriculture_work/source_cells.tsv`. Repeated expanded province/district heading cells produce no observations.',
 '- Crop and animal names are measure_as_printed. For row-oriented district returns, note gives the exact statistic header (acreage, Gross Produce., or Number.) so acreage and produce for the same crop remain distinguishable. For cultivated-land returns, the lower printed header is the measure and the upper header is retained in note. No synthetic combined measure label is introduced.',
 '- Units are copied from explicit headers or the same source cell. An explicit unit immediately above an observation is used for that observation only. Units are not guessed from a neighbouring crop or a previous district. Numeric portions of cells containing explicit units are separated, with the complete source cell preserved in note. Blank unit means no safe explicit unit was available. Acre/Acres retain their printed forms; no unit conversions are performed. A heading saying only Acreage has no separate unit, so unit_as_printed is blank.',
 '- Decimal parsing accepts ordinary decimals, properly grouped thousands separators, Unicode quarter/eighth fractions and terminating fractions encoded with LaTeX or a spaced numerator/denominator. Explicit typographic footnote markers are retained in value_as_printed and noted when ignored for parsing. Letters are never changed into digits. Narrative returns, mixed/ambiguous numbers and letter-marked numbers remain unparsed with a note.',
 '- Province headings set the parent for district rows. Unlabelled provincial subtotal rows retain an empty area label and are marked printed total. Colony totals retain their printed label (or blank if unlabelled). The 1924 stock table has a split “Province of” / “Sabaragamuwa ..” label: area and parent retain the latter cell, and note preserves the prefix. No area spelling is repaired.',
 '- Scope includes primary crop acreage, gross produce quantities, land acreages, estate counts and current livestock counts. Wage rates, prices, production per acre, seed rates, historical increases, manufactures, mines, dairies and multi-year general progress tables are outside this extract. The district livestock returns of 1902/1904/1912 belong to land_produce_stock; the later combined province/district summary tables belong to live_stock. The small opening colony livestock summaries are also included as live_stock.', '',
 '## Data years','',
 '- Opening Agricultural Statistics: 1869 page 11 lists 1868 then 1869; 1902 page 16 lists 1901 then 1902; 1904 page 18 lists 1903 then 1904. The two acreage tables follow that order. In 1912 the acreage tables lie on separate pages: page 16 explicitly says 1911, page 17 says 1912. Opening stock summaries date each numeric column explicitly.',
 '- The 1869 Western Province produce/stock block (page 535) is dated 1869 by its facing continuation heading on page 536. The cultivated-land table on page 530 has no explicit year; its year_data is left empty.',
 '- The 1902, 1904 and 1912 detailed district crop, stock and cultivated-land returns do not establish a reporting year explicitly in their table/page headings or text. year_data is left empty rather than equated automatically with year_volume.',
 '- The 1924 cultivated/pasture/waste return explicitly reports 1923 (page 397 footnote). For the 1924, 1926 and 1928 livestock summary tables no explicit count year appears on the page: year_data remains empty.',
 '- The 1928 acreage note dates rubber to a July 1928 census. Other crops are estimates based on the 1921 and 1924 censuses: there is no single data year, so year_data is empty with a note.', '',
 '## Totals checks','',
 f'{len(AUDIT)} acreage total comparisons were attempted: {agreements} agree, {mismatches} differ, {uncheckable} cannot be checked. Agreement is {agreements}/{agreements+mismatches} ({100*agreements/(agreements+mismatches):.1f}%) of computable comparisons, or {agreements}/{len(AUDIT)} ({100*agreements/len(AUDIT):.1f}%) of all attempted comparisons.', '',
 'Every printed TOTAL row/column in the eight opening acreage tables is checked, including the 1869 corner grand totals in both directions. The 1928 CEYLON row is compared with provinces, and each numeric province summary with its districts; districts are never added again to province totals. Row totals and column totals are separate comparisons, so they may overlap in the cells they assess.', '',
 'Sums use Decimal with no rounding tolerance. A dash, blank, Nil or dots remains missing in the data; for checking, a sum is the sum of available numeric parts, not an assertion that missing parts are zero. An unreadable nonmissing part makes the comparison uncheckable. No numeric total or no numeric parts is also uncheckable. `agriculture_checks.tsv` contains mismatches and uncheckable comparisons (empty computed sum/difference for uncheckable). Difference is printed total minus computed sum. `jobs/agriculture_work/totals_audit.tsv` includes every comparison, status and missing/unreadable-part counts. Mismatching total cells are flagged in agriculture.tsv; figures are never corrected to make a total agree. Additional land and livestock total comparisons are in `jobs/agriculture_work/other_totals_audit.tsv`; these also flag suspect total cells in agriculture.tsv but are excluded from the acreage agreement percentage.', '',
 '## Validation','', 'The independent validator checks every output observation against a unique source cell, confirms literal label/unit provenance, independently parses each numeric value using rational arithmetic, reconciles the candidate/skip lists, and independently recomputes the opening crop totals from the source. Results are saved in `jobs/agriculture_work/validation_report.json`.','', '## Gaps and cautions','',
 '- 1889 inputs cover pages 1–282 (tables 9–279), and 1890 inputs cover pages 301–340 (tables 301–339). No target table was found in those supplied fragments; this does not establish absence in the complete historical volumes.',
 '- Most 1869 detailed blocks have unlabelled facing-page continuations, shifted crop/stock columns or subdistrict hierarchies requiring more layout evidence. Only the clear Western Province block and the initial cultivated-land return are used. Subdistrict blocks were not reassigned to district aggregates.',
 '- The uncultivated-land continuation pages in 1902, 1904 and 1912 have no area column and their row alignment with the preceding page is not secure; all are skipped.',
 '- The 1924 Nature of Crops tables have misaligned crop headings/data. Page 395 has 18 columns with 16 numbered positions and Cacao headings over empty columns; page 396 loses the tobacco produce slot and subsequent headings shift. They are skipped in full, including their otherwise clear early columns.',
 '- The 1925 acreage and livestock tables and 1926 acreage table show a province aggregate beside the first district label, followed by shifted district data and an unlabelled last row. They are skipped in full. The 1926 acreage headers also misplace Vegetables. No area labels are reassigned from arithmetic alone.',
 '- The 1928 acreage table has a missing Northern Province Coconuts total despite numeric district acreages; retained as printed and marked uncheckable. Other arithmetic discrepancies are reported, not repaired.',
 '- 1930 page 215 has no parsed table (n_tables=0), though page text contains colony crop/stock summaries and says provincial/district figures were omitted as unreliable. It is not reconstructed as a fictitious table. The 1933 and 1934 crop/stock tables collapse the two adjacent layouts: livestock numbers align with crop names and most crop numbers are absent. Both candidate tables are skipped.',
 '- OCR-looking geographic names and crop spellings remain literal. Dates not explicitly established are deliberately blank. A few Gross Produce cells report money rather than a physical quantity; these are retained in that statistic with their explicit currency text, without conversion. The 1904 Kandy tobacco return reports 10,168,000 cwt.; the suspect magnitude/unit is flagged without changing the source number. No network or external references were used; page images were used only for the 1879–1891 readings.', '']
(OUT/'agriculture_README.md').write_text('\n'.join(lines))
print(json.dumps({'rows':len(DATA),'numeric_values':numeric,'used_tables':len(USED),'skipped_tables':len(SKIPPED),'checks':len(AUDIT),'agree':agreements,'mismatch':mismatches,'uncheckable':uncheckable},indent=2))
