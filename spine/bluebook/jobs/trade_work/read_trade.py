#!/usr/bin/env python3
"""Read the article/country ledgers from the supplied OCR tables (stdlib only)."""
import argparse
import collections
import csv
import gzip
import json
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'extracted'
WORK = ROOT / 'jobs/trade_work'
FIELDS = ('table_id year_volume pdf_page printed_page flow class_as_printed '
          'group_as_printed article_as_printed country_group_as_printed '
          'country_as_printed unit_as_printed measure value_as_printed value row_kind note').split()
IMPORT = ['quantity_total', 'quantity_home_consumption', 'value_total_rs']
EXPORT = ['quantity_ceylon_produce', 'quantity_other_produce', 'quantity_total',
          'value_ceylon_produce_rs', 'value_other_produce_rs', 'value_total_rs']
DITTO = {'"', "''", ',,', '„', '”', '“', '〃', '»'}
EMPTY = {'', '.', '..', '...', '—', '–', '-', '--', '―', '…'}
NUMBER = re.compile(r'(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)$')
GROUP_MARK = re.compile(r'(British Possessions\s*[—–-]|Foreign Countries\s*[—–-])', re.I)
UNIT = re.compile(r'(?:\(?\{?\s*)?(?:doz\.?\s*(?:pairs|packs)|No\.?\s+of\s+doz\.?|'
                  r'No\.?|cwt\.?|owt\.?|lb\.?|lbs\.?|tons?|gals?\.?|gallons?|'
                  r'bots?\.?|bottles?|dozen|doz\.?|gross|value|yds?\.?|yards?|'
                  r'oz\.?\s*troy|oz\.?|sq\.?\s*(?:ft\.?|yds?\.?)|feet|ft\.?|'
                  r'pairs?|sets?|cases?|reams?|loads?|bushels?|barrels?|carats?|pkgs?\.?|'
                  r'lin\.?\s*ft\.?|coils?|troy\s*oz\.?)', re.I)


def clean(s):
    """Remove dot leaders while retaining spelling, punctuation and accents."""
    return re.sub(r'\s*\.{2,}\s*', ' ', s).strip()


def key(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def number(s):
    s = s.strip()
    if s in EMPTY:
        return ''
    if not NUMBER.fullmatch(s):
        raise ValueError('ambiguous numerical cell ' + repr(s))
    return s.replace(',', '')


def ledger_flow(t):
    h = ' '.join(c for r in t['rows'][:3] for c in r).lower()
    if 'articles' not in h:
        return None
    if 'quantities imported' in h:
        return 'import'
    if 'quantity' in h and 'produce' in h and 'value' in h:
        return 'export'
    return None


class Reader:
    def __init__(self, year):
        self.year = year
        self.records = []
        self.skipped = []
        self.events = []
        self.articles = []
        self.flow = None
        self.scope = ''
        self.cl = self.gr = self.article = self.cg = self.unit = ''
        self.current = None
        self.continuation = ''
        self.special_columns = False
        self.previous_country = ''
        self.previous_kind = 'country'
        self.pending_country = ''

    def skip(self, t, i, cells, reason, block=''):
        self.skipped.append([t['id'], i, json.dumps(cells, ensure_ascii=False), reason + ('; '+block if block else '')])
        if self.current is not None:
            self.current['skips'] += 1
            if cells and re.match(r'^Total(?:\s*\.{1,}|\s*[({]|\s*$)', cells[0], re.I):
                self.current['unreadable_totals'].append((t['id'], i, reason))

    def event(self, t, i, label, kind):
        self.events.append([t['id'], i, self.flow, kind, label])

    def start_article(self, label, t, i):
        label = clean(label)
        if self.current is not None and key(label) == key(self.article):
            self.event(t, i, label, 'repeated article heading')
            return
        cont = bool(re.search(r'cont(?:inued|d)?\.?\)?\s*[—–-]?\s*$', label, re.I))
        suffix = re.split(r'[—–]', label)[-1]
        cont = cont or key(suffix) in {'cntd','ontd','contimued'}
        if cont and self.current is not None:
            self.continuation = label
            self.event(t, i, label, 'continuation heading')
            return
        self.article = label
        self.cg = ''
        self.continuation = ''
        self.previous_country = ''
        self.current = {'year': self.year, 'flow': self.flow, 'scope': self.scope,
                        'article': label, 'start': t['id'], 'start_row': i,
                        'countries': collections.defaultdict(Decimal),
                        'units': {},
                        'totals': [], 'skips': 0, 'country_rows': 0, 'unreadable_totals': [],
                        'ambiguous_quantity_layout': False}
        self.articles.append(self.current)

    def heading(self, label, t, i):
        s = clean(label)
        if not s:
            return
        # Some OCR cells combine a repeated class/group line and a leaf heading.
        if re.match(r'^(CLASS|GROUP)\b', s, re.I):
            m = re.match(r'^((?:CLASS|GROUP)\s+[^—–]+[—–].*?\.)\s+([A-Z][a-z].*)$', s)
            if m:
                self.heading(m[1], t, i)
                self.heading(m[2], t, i)
                return
        if re.match(r'^CLASS\b', s, re.I):
            old = re.match(r'^CLASS\s+([IVX]+)', self.cl, re.I)
            new = re.match(r'^CLASS\s+([IVX]+)', s, re.I)
            if old and new and old[1] != new[1]:
                self.gr = ''
                self.article = ''
                self.current = None
            self.cl = s
            return
        if re.match(r'^GROUP\b', s, re.I):
            if key(s) != key(self.gr):
                self.article = ''
                self.current = None
            self.gr = s
            return
        if GROUP_MARK.fullmatch(s):
            self.cg = s
            return
        if re.match(r'^(?:Total\b|British Possessions\b|Foreign Countries\b)', s, re.I):
            self.event(t, i, s, 'unreadable data label retained without changing article')
            return
        if s.startswith('Other Foreign Countries'):
            self.pending_country = s
            return
        if re.match(r'^(?:ARTICLES\b|Rs\.?$|QUANTITY\b|VALUE\b|Produce and Manufactures|British, Foreign)', s, re.I):
            return
        # Subheadings without a country row are retained in the audit, and the
        # immediately following leaf heading becomes the article.
        self.start_article(s, t, i)

    def split_label(self, label, explicit_unit=''):
        """Separate a country label, unit, and explicit embedded quantities."""
        s = label.strip()
        tail = explicit_unit.strip()
        embedded = []
        m = re.search(r'\s*[({]\s*(?=(?:No\.?|cwt\.?|gals?\.?|tons?|cases?|lin\.?\s*ft)\b)', s, re.I)
        leader = re.search(r'\s*\.{2,}\s*', s)
        if m:
            tail = s[m.end():].strip()
            s = s[:m.start()].strip()
        elif leader and not explicit_unit:
            tail = clean(s[leader.end():])
            s = s[:leader.start()].strip()
        elif not explicit_unit:
            for pos in [m.start() for m in re.finditer(r'\s+', s)]:
                candidate = s[pos:].strip()
                if UNIT.fullmatch(candidate) or candidate in DITTO:
                    tail = candidate
                    s = s[:pos].rstrip(' .')
                    break
        tail = tail.strip(' {}()')
        if tail in {'†','‡','*'}:
            s += ' '+tail
            tail = ''
        if tail.startswith('\\') and tail[1:] in DITTO:
            tail = tail[1:]
        if tail and (re.search(r'\d', tail) or re.search(r'\s[—–-]', tail)):
            pair_pattern = r'(No\.?|cwt\.?|yds?\.?|gals?\.?|tons?|cases?|lin\.?\s*ft\.?)\s+([\d,]+|—|–|-)'
            pairs = re.findall(pair_pattern, tail, re.I)
            remainder = re.sub(pair_pattern, '', tail, flags=re.I).strip(' ,{}()')
            if pairs and not remainder:
                tail = ' '.join(p[0] for p in pairs)
                embedded = [p[1] for p in pairs]
        s = clean(s)
        if re.fullmatch(r'Total\s+\.', s, re.I):
            s = s.rstrip(' .')
        return s, tail, embedded

    def read_row(self, t, i, cells, unit_column=False, block='', partial=False):
        cells = list(cells)
        label = cells[0].strip() if cells else ''
        # Recover a complete row collapsed into the label cell. Each captured
        # number is present literally in that cell, including two-unit pairs.
        if self.flow == 'import' and not unit_column and not any(c.strip() for c in cells[1:]):
            m = re.match(r'^(.*?)\s+([\d,]+|—|–|-)\s+([\d,]+|—|–|-)\s+([\d,]+|—|–|-)\s*$', label)
            if m and ('..' in m[1] or m[1].lower().startswith('total')):
                cells = [m[1], m[2], m[3], m[4]]
                label = m[1]
            else:
                m = re.match(r'^(.*?)\(No\.\s*([\d,]+|—),\s*cwt\.\s*([\d,]+|—)\)\s*\(([\d,]+|—),\s*([\d,]+|—)\)\s*([\d,]+|—)$', label)
                if m:
                    cells = [m[1]+' (No. cwt.)', m[2]+' '+m[3], m[4]+' '+m[5], m[6]]
                    label = cells[0]
        explicit_unit = cells[1] if unit_column else ''
        vals = cells[2:] if unit_column else cells[1:]
        if self.flow == 'import' and not unit_column and len(vals)==3:
            m = re.match(r'^(.*?)\s+([\d,]+|—|–|-)\s*$', label)
            if m and '..' in m[1] and vals[0].strip()==m[2]:
                label = m[1]
                if not vals[2].strip() and vals[1].strip():
                    vals = [m[2], vals[0], vals[1]]
        if not label and not any(c.strip() and c.strip() not in {'Rs.', 'Rs'} for c in vals):
            return
        if re.match(r'^(?:Brought|Carried)\b', label, re.I):
            self.event(t, i, label, 'running total skipped')
            return
        if re.match(r'^(?:No\.?\s+of\s+doz\.?|cwt\.?|yds\.?|gals\.?|cases|tons)\s+[\d—–-]', label, re.I):
            self.skip(t, i, cells, 'unattached unit continuation row', block)
            return
        # Heading-only rows can contain placeholder dashes or displaced figures.
        if re.fullmatch(r'British Possessions|Foreign Countries', label, re.I):
            self.cg = clean(label)
            if any(re.search(r'\d', c) for c in vals):
                self.skip(t, i, cells, 'figures displaced onto a country-group heading', block)
            return
        if GROUP_MARK.fullmatch(label) or (label.endswith(('—','–')) and '..' not in label and not re.search(r'[({]', label) and not label.startswith('Other Foreign Countries')):
            self.heading(label, t, i)
            if any(re.search(r'\d', c) for c in vals):
                self.skip(t, i, cells, 'figures displaced onto a heading row', block)
            return
        # Repeated text in expanded spanning headings is not numerical data.
        has_data = any(re.search(r'\d', c) or c.strip() in EMPTY - {''} for c in vals)
        if not has_data and not re.match(r'^Total\b', label, re.I) and '..' not in label and not re.search(r'[({]\s*(No|cwt)',label):
            if label:
                self.heading(label, t, i)
            return
        if not label:
            self.skip(t, i, cells, 'figures without a row label', block)
            return
        # A country-group or article heading can share the OCR cell with data.
        # Establish the leaf article before processing an inline country group.
        unit_brace = re.search(r'[({]\s*(?:No\.?|cwt\.?|yds?\.?|gals?\.?|tons?|cases?|lin\.?\s*ft|pkgs?\.?|doz\.?)\b', label, re.I)
        heading_portion = label[:unit_brace.start()] if unit_brace else label
        first_dash = re.search(r'[—–]\s*(?=[A-Za-z])', heading_portion)
        group_match = GROUP_MARK.search(label)
        if first_dash and group_match and first_dash.start() >= group_match.start():
            first_dash = None
        if first_dash and not re.match(r'^(British Possessions|Foreign Countries)', label, re.I):
            self.start_article(label[:first_dash.start()+1], t, i)
            label = label[first_dash.end():]
        # Recover stacked country rows only when every numerical column has
        # exactly one explicitly separated figure per country.
        merged_pattern = re.compile(r'(.+?)\s+(\(?gals\.\s*cwt\.\)?|No\.\s*cwt\.|cwt\.|tons?|lb\.|yds\.|gals\.|doz\.\s*pairs|doz\.|value|"|„|,,)(?=\s|$)', re.I)
        merged = list(merged_pattern.finditer(label))
        if len(merged) > 1 and not label[merged[-1].end():].strip():
            split_values = [v.split() for v in vals]
            if all(len(v) == len(merged) for v in split_values):
                self.event(t, i, label, 'split merged country rows')
                for j, m in enumerate(merged):
                    subcells = [m[1]+' .. '+m[2]] + [v[j] for v in split_values]
                    self.read_row(t, i, subcells, False, block+'; split merged source row')
                return
        chunks = GROUP_MARK.split(label)
        label = chunks[-1].strip()
        for part in chunks[:-1]:
            if part.strip():
                if GROUP_MARK.fullmatch(part.strip()):
                    self.cg = clean(part)
                else:
                    if '..' in part or UNIT.search(part.strip().split()[-1]):
                        self.skip(t, i, cells, 'multiple country rows merged into one OCR row', block)
                        return
                    self.heading(part.strip(), t, i)
        # The final em dash separates a merged article heading from a country.
        unit_brace = re.search(r'[({]\s*(?:No\.?|cwt\.?|yds?\.?|gals?\.?|tons?|cases?|lin\.?\s*ft|pkgs?\.?|doz\.?)\b', label, re.I)
        heading_portion = label[:unit_brace.start()] if unit_brace else label
        if re.search(r'[—–]\s*[A-Za-z]', heading_portion):
            prefix, label = re.split(r'[—–]\s*(?=[A-Za-z])', label, maxsplit=1)
            self.start_article(prefix + '—', t, i)
        country, unit, embedded = self.split_label(label, explicit_unit)
        if not country and self.pending_country:
            country = self.pending_country
            self.pending_country = ''
        elif not country and self.previous_country and re.search(r'[({]', label):
            country = self.previous_country
        if not country:
            self.skip(t, i, cells, 'missing country label', block)
            return
        if re.search(r'\d|[{}]', country) or not re.search(r'[A-Za-zÀ-ž]', country) or UNIT.fullmatch(country.rstrip(' .')):
            self.skip(t, i, cells, 'unreadable country or unattached continuation unit '+repr(country), block)
            return
        if re.match(r'^Total\s+(?:British|Foreign|Br)(?:\b|\.)', country, re.I):
            kind = 'subtotal'
        elif re.fullmatch(r'Total\.?', country, re.I):
            kind = 'article_total'
        else:
            kind = 'country'
        if country == self.previous_country and re.search(r'^\s*\.{2,}\s*[({]', label):
            kind = self.previous_kind
        note = [self.scope, block, 'source row '+str(i)]
        if self.continuation:
            note.append('continued under '+self.continuation)
        if unit in DITTO:
            if not self.unit:
                self.skip(t, i, cells, 'unit ditto without antecedent', block)
                return
            unit = self.unit
            note.append('unit from ditto')
        elif unit in EMPTY:
            unit = self.unit
            if unit:
                note.append('unit carried forward')
        if self.current is None:
            if not self.gr:
                self.skip(t, i, cells, 'country row without an article or group', block)
                return
            saved_group = self.cg
            self.start_article('', t, i)
            self.cg = saved_group
            note.append('article heading absent; commodity identified only by group')
        if unit and not UNIT.fullmatch(unit) and re.sub(UNIT, '', unit).strip(' .'):
            self.skip(t, i, cells, 'unreadable or merged unit field '+repr(unit), block)
            return
        self.unit = unit
        # Resolve two explicitly printed units into separate quantity records.
        units = [m[0].strip(' {}()') for m in UNIT.finditer(unit)]
        dual = len(units) == 2 and key(unit) == key(' '.join(units))
        if kind == 'article_total' and self.current['ambiguous_quantity_layout']:
            self.skip(t, i, cells, 'article total in unresolved multiple-quantity layout', block)
            return
        measures = IMPORT if self.flow == 'import' else EXPORT
        components = [''] * len(measures)
        if self.special_columns:
            measures = ['quantity_ceylon_produce', 'quantity_ceylon_produce', 'quantity_total',
                        'value_ceylon_produce_rs', 'value_ceylon_produce_rs', 'value_total_rs']
            components = ['quills', 'chips', '', 'quills', 'chips', '']
        if len(vals) != len(measures):
            if not partial:
                self.skip(t, i, cells, 'unsupported column count', block)
                return
            measures = measures[:len(vals)]
            note.append('source table omits '+('value column' if len(vals)==2 else 'home-consumption and value columns'))
        expanded = []
        try:
            for j, (measure, raw) in enumerate(zip(measures, vals)):
                raw = raw.strip()
                if raw.startswith(('No.', 'No ', 'cwt.')):
                    raw = re.sub(r'\b(?:No\.?|cwt\.?)\s*', '', raw).strip()
                if measure.startswith('quantity') and dual:
                    parts = raw.split()
                    if not raw and embedded and self.flow == 'import' and j == 0:
                        parts = embedded
                        note.append('quantity printed in label cell')
                    if len(parts) != 2:
                        if raw in EMPTY:
                            parts = [raw, raw]
                        else:
                            raise ValueError('two-unit quantity cannot be separated')
                    for u, p in zip(units, parts):
                        expanded.append((u, measure, p, number(p), components[j]))
                else:
                    expanded.append((unit, measure, raw, number(raw), components[j]))
        except ValueError as e:
            if not dual and unit.lower().startswith('gal') and any(len(v.split()) > 1 for v in vals[:2 if self.flow=='import' else 3]):
                self.current['ambiguous_quantity_layout'] = True
            self.skip(t, i, cells, str(e), block)
            return
        note = '; '.join(dict.fromkeys(n for n in note if n))
        for u, measure, raw, val, component in expanded:
            row = [t['id'], self.year, t['pdf_page'], t.get('printed_page') or '', self.flow,
                   self.cl, self.gr, self.article, self.cg, country, u, measure, raw, val, kind, note + ('; Ceylon produce component '+component if component else '')]
            self.records.append(row)
            k = (key(u) if measure.startswith('quantity') else '', measure, component)
            self.current['units'][k] = u if measure.startswith('quantity') else ''
            if kind == 'country' and val:
                self.current['countries'][k] += Decimal(val)
            if kind == 'article_total':
                self.current['totals'].append((k, val, t['id'], i, raw, self.current['countries'][k]))
        if kind == 'country':
            self.current['country_rows'] += 1
        self.previous_country = country
        self.previous_kind = kind

    def read(self, tables):
        for t in tables:
            flow = ledger_flow(t)
            if not flow:
                continue
            government = any('GOVERNMENT STORES' in h.upper() for h in t.get('headings', []))
            if flow != self.flow or government:
                self.cl = self.gr = self.article = self.cg = self.unit = ''
                self.current = None
                self.flow = flow
                self.scope = 'government stores imports' if government else ''
            self.special_columns = any(re.search(r'\bQuills\b|\bChips\b', c, re.I) for r in t['rows'][:6] for c in r)
            if flow == 'import':
                if t['id'] == 'bb1925:p200:t1':
                    # This OCR table has a five-column left block and a truncated
                    # three-column right block. Heading spans use four columns.
                    for left in [True, False]:
                        for i, r in enumerate(t['rows'][2:], 2):
                            if i in [5,18,27,36]:
                                cells = [r[0 if left else 4], '', '', '']
                                self.heading(cells[0], t, i)
                                continue
                            cells = r[:5] if left else r[5:]
                            self.read_row(t, i, cells, True, 'left block' if left else 'right block', partial=not left)
                elif t['n_cols'] in [8,9,10] or t['id']=='bb1924:p288:t1':
                    width = 4 if t['n_cols']==9 else t['n_cols']//2
                    for a in [0,width]:
                        for i, r in enumerate(t['rows']):
                            if any('quantities imported' in c.lower() or c.upper().startswith('ARTICLES') for c in r[a:a+width]):
                                continue
                            if a and i>3 and len(set(r))==1 and r[0] and not re.match(r'^(CLASS|GROUP|British Possessions|Foreign Countries|Total)\b',r[0],re.I) and self.current and not self.current['totals']:
                                self.event(t,i,r[0],'full-width repeated heading suppressed in continuing right block')
                                continue
                            if t['n_cols']==9 and a==4 and any(r[8:]):
                                self.read_row(t, i, r[4:], True, 'right block')
                            else:
                                self.read_row(t, i, r[a:a+width], width==5, 'left block' if a==0 else 'right block', partial=width==3)
                else:
                    width = t['n_cols']//2
                    for a in [0,width]:
                        for i,r in enumerate(t['rows']):
                            cells = r[a:a+width]
                            label = cells[0].strip()
                            if label.upper().startswith('ARTICLES') or any('quantities imported' in c.lower() for c in cells):
                                continue
                            if re.match(r'^(CLASS|GROUP)\b', label, re.I) or (label.endswith('—') and not re.search(r'[({]',label)):
                                self.heading(label,t,i)
                            elif label or any(c.strip() for c in cells):
                                self.skip(t,i,cells,'unsupported import table layout; column meanings ambiguous','left block' if a==0 else 'right block')
            elif t['n_cols'] >= 7:
                for i,r in enumerate(t['rows']):
                    if r[0].upper().startswith('ARTICLES'):
                        continue
                    if any(c.strip() and c.strip() not in {'Rs.','Rs'} for c in r[7:]):
                        self.skip(t,i,r,'extra export columns contain unmapped data')
                    else:
                        self.read_row(t,i,r[:7])
            else:
                for i,r in enumerate(t['rows']):
                    self.skip(t,i,r,'unsupported export table layout')
        return self


def write_tsv(path, fields, rows):
    with path.open('w', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(fields)
        w.writerows(rows)


def build(years):
    readers=[]
    coverage=[]
    for year in years:
        with gzip.open(ROOT / f'tables/{year}.jsonl.gz','rt') as f:
            tables=[json.loads(l) for l in f]
        r=Reader(year).read(tables)
        readers.append(r)
        ledgers=[t for t in tables if ledger_flow(t)]
        coverage.append((year, len(ledgers)))
    OUT.mkdir(exist_ok=True)
    write_tsv(OUT/'trade.tsv',FIELDS,(row for r in readers for row in r.records))
    write_tsv(OUT/'trade_skipped.tsv',['table_id','row index','cells','reason'],(row for r in readers for row in r.skipped))
    write_tsv(WORK/'running_totals_and_continuations.tsv',['table_id','row_index','flow','event','label'],(row for r in readers for row in r.events))
    checks=[]
    stats=collections.defaultdict(lambda: [0,0,0])
    article_results=[]
    article_audit=[]
    unknown_counts=collections.Counter()
    for r in readers:
        for a in r.articles:
            if not a['totals'] and not a['unreadable_totals']:
                continue
            bad=[]
            for k, val, tid, idx, raw, actual in a['totals']:
                if not val:
                    continue
                total=Decimal(val or 0)
                if actual != total:
                    difference=actual-total
                    bad.append((abs(difference),k,tid,idx,val,str(actual),str(difference)))
                    checks.append([a['year'],a['flow'],a['scope'],a['article'],a['start'],tid,idx,a['units'].get(k,k[0]),k[1],k[2],raw,str(actual),str(difference),a['skips'],'mismatch'])
            unknown = list(dict.fromkeys(a['unreadable_totals']))
            if not any(v for _,v,*rest in a['totals']) and not unknown:
                unknown = [(a['start'],a['start_row'],'Total row has no readable printed figure')]
            for tid,idx,reason in unknown:
                checks.append([a['year'],a['flow'],a['scope'],a['article'],a['start'],tid,idx,'','','','','','',a['skips'],'uncheckable total; '+reason])
            st=stats[(a['year'],a['flow'])]
            st[0]+=1
            st[1]+=not bad and not unknown
            st[2]+=a['skips']>0
            unknown_counts[(a['year'],a['flow'])] += bool(unknown)
            article_audit.append([a['year'],a['flow'],a['scope'],a['start'],a['start_row'],a['article'],a['country_rows'],a['skips'],len(a['totals']),len(bad),len(unknown),'agree' if not bad and not unknown else 'uncheckable' if unknown else 'mismatch'])
            article_results.append((a,bad))
    write_tsv(OUT/'trade_checks.tsv',['year_volume','flow','scope','article_as_printed','article_start_table','total_table_id','total_row_index','unit_as_printed','measure','component','total_as_printed','country_sum','difference_sum_minus_total','skipped_rows_in_article','status'],checks)
    write_tsv(WORK/'article_audit.tsv',['year_volume','flow','scope','start_table','start_row','article_as_printed','country_rows','skipped_source_rows','total_measure_cells','mismatching_measures','uncheckable_total_rows','status'],article_audit)
    rows_count=collections.Counter((r.year,row[4]) for r in readers for row in r.records)
    country_count=collections.Counter((r.year,row[4]) for r in readers for row in r.records if row[14]=='country')
    lines=['# Ceylon Blue Books trade ledgers','',
           'Built from the supplied OCR table JSONL files with standard-library Python. Printed spellings and numerical cells are preserved. No source images or outside sources were used.','',
           'Completed the extraction and checks for 1925 first, followed by 1924, 1926 and 1928. Each of these four volumes has 111 article-ledger tables. These are completed reader passes with the unresolved rows and discrepancies listed below.', '',
           '1930, 1933 and 1934 were inspected. Their supplied tables contain trade summaries, but searches across every cell found neither the import quantity/home-consumption headers nor the export produce/manufactures headers. Article-country extraction for those volumes could not be completed from these inputs.', '',
           '## Coverage','',
           '| Volume | Flow | Output measure rows | Country measure rows | Articles with Total | All measures agree | Agreement |',
           '|---|---|---:|---:|---:|---:|---:|']
    for year,n in coverage:
        if not n:
            lines.append(f'| {year} | No article/country ledgers present in supplied tables | 0 | 0 | 0 | 0 | n/a |')
        for flow in ['import','export']:
            if not rows_count[(year,flow)]:continue
            total,good,skips=stats[(year,flow)]
            lines.append(f'| {year} | {flow} | {rows_count[(year,flow)]:,} | {country_count[(year,flow)]:,} | {total} | {good} | {good/total:.1%} |')
    lines += ['', '## Method and limitations','',
              '- Import blocks are read down the left side, then down the right side. Class, group, article, country group and unit state carry across blocks and pages. Government Stores imports restart state and carry a scope note.',
              '- Source row indexes in the ledger notes, skipped file and checks file are zero-based. Import block locations are recorded in notes and skip reasons. The audit of running totals, reconstructed rows and continuation headings is in `jobs/trade_work/running_totals_and_continuations.tsv`. Article-level check results are in `jobs/trade_work/article_audit.tsv`.',
              '- Every supported printed measure cell is emitted, including blank and dash cells with an empty normalized value. Ditto units are resolved and noted. Omitted units inherit the previous unit and carry a note.',
              '- Article checks sum country rows only. Subtotals and running totals are excluded. A Total is checked against the cumulative country rows above it in its article. Thus an intermediate bare Total uses the countries preceding that row. Later Totals use the larger cumulative sum. Empty country figures contribute zero to arithmetic and retain empty normalized values in the ledger. Empty total cells have no numerical assertion to compare.',
              '- An article agrees only when every readable Total figure agrees exactly and every Total row is interpretable. Unreadable Total rows and Total rows with no figures count as failures in the agreement denominator. The checks file contains numerical mismatches and explicit uncheckable-total entries.',
              '- Explicit paired units become separate quantity rows with their respective units. Unit punctuation is ignored for arithmetic grouping while the ledger retains each printed spelling. Cinnamon quills and chips both use the Ceylon-produce measures, with a component note and separate component checks.',
              '- Repeated continuation headings retain the initial printed article label. The continuation label is retained in notes and the audit. A missing leaf article heading leaves the article field empty and records the printed group. Footnote symbols next to a country are retained in the country field.',
              '- A complete row collapsed into its label cell, a shifted figure duplicated in that label, or stacked country rows are reconstructed only when literal tokens identify the figures. A full-width repeated leaf heading in a continuing right-hand import article is treated as an expanded OCR span and logged in the audit.',
              '- Ambiguous figures, shifted figures without an attributable country, unresolved two-unit rows, and unsupported layouts go to the skipped file. The 1925 machinery table bb1925:p200:t1 has a truncated right block. Its readable total quantities are retained with an omitted-column note. The 1924 machinery table bb1924:p288:t1 similarly retains the two explicit quantity columns. Column meanings in bb1926:p212:t1 remain ambiguous and its data are skipped.',
              '- Figures such as the 1925 cacao Total of 77704253 and the 1926 rubber United Kingdom Ceylon-produce quantity of 4080664 are retained literally. They cause large arithmetic discrepancies in the supplied OCR. These discrepancies remain unresolved. Other failures reflect skipped rows, misplaced headings or figures, intermediate Totals, or source arithmetic. No numerical OCR corrections are made.',
              '', '## Skipped rows and uncheckable articles', '',
              '| Volume | Skipped source block rows | Import articles with uncheckable Totals | Export articles with uncheckable Totals |',
              '|---|---:|---:|---:|']
    for r in readers:
        if any(y==r.year and n for y,n in coverage):
            lines.append(f'| {r.year} | {len(r.skipped)} | {unknown_counts[(r.year,"import")]} | {unknown_counts[(r.year,"export")]} |')
    lines += [
              '', '## Ten largest unexplained article differences','',
              'Articles are ranked by their largest absolute measure discrepancy. Quantities and rupees have different units, so this ranking is a numerical diagnostic.', '',
              '| Volume | Flow | Article | Total table | Measure | Unit | Printed total | Country sum | Difference |',
              '|---|---|---|---|---|---|---:|---:|---:|']
    ranked=sorted(((max(bad),a) for a,bad in article_results if bad),key=lambda x:x[0][0],reverse=True)[:10]
    for b,a in ranked:
        _,k,tid,idx,val,actual,diff=b
        text=a['article'].replace('|','\\|')
        lines.append(f'| {a["year"]} | {a["flow"]} | {text} | {tid}, row {idx} | {k[1]} | {a["units"].get(k,k[0])} | {val or "(blank)"} | {actual} | {diff} |')
    lines += ['', '## Rebuild and verify','', '```sh', '/home/jic823/miniforge3/bin/python jobs/trade_work/read_trade.py '+ ' '.join(map(str,years)), '/home/jic823/miniforge3/bin/python jobs/trade_work/verify_trade.py', '```','',
              'Verification checks the requested header, literal source-number provenance for every normalized figure, country labels, resolved units, block continuity and selected 1925 regressions. Arithmetic verification remains limited to the supplied OCR.']
    (OUT/'trade_README.md').write_text('\n'.join(lines))
    print(json.dumps({'coverage':coverage,'rows':{str(k):v for k,v in rows_count.items()},'agreement':{str(k):v for k,v in stats.items()},'skips':{r.year:len(r.skipped) for r in readers}},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('years',type=int,nargs='*',default=[1925,1924,1926,1928,1930,1933,1934])
    build(p.parse_args().years)
