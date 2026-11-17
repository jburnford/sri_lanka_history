"""Ceylon Blue Books: the article-by-country trade ledgers in the single-block layout of 1880-1906.

From 1907 the ledgers are read by jobs/trade_work/read_trade.py. Before that each page is one block:

    article | country | figures ...

with the article named once, countries below it under "Br. Col.—" and "For. Coun.—", and the article's total as a
row of figures with no label. Classes and groups are headings that span the table.

  1901-1906  quantities are single numbers; values are whole rupees
             imports: total quantity, quantity entered for home consumption, value
             exports: quantity and value, each as Ceylon produce / other produce / total
  1880-1900  quantities of weight are printed as hundredweights, quarters and pounds ("837 0 7"); values as
             rupees and cents in two columns; further columns give average price and duty. See LAYOUT below.

For 1901-1906, headings are learned from the six volumes' OCR; two reviewed
structural exceptions distinguish terminal Pearls and nested Seeds/Unenumerated.
Explicit heading/leaf pairs and first leaves anchor repeated, ordered sub-entry
runs. A heading stack retains every level, including across page continuations. Conflicting membership evidence leaves a bare printed
name with a heading-uncertain note. Article blocks are buffered so collapsed
blocks can be withheld and wrapped-country totals can be checked. Government
Stores are identified from page headings. Tea components retain their printed
figures and carry component notes; tea seed remains under Seeds.

Everything is kept as printed; `value` is the number where the cell is one, and for cwt-qr-lb the weight in cwt.
Each article is checked: its country rows should add to its total row. Rows that cannot be read safely go to the
skipped file with a reason, and are never guessed.

Output (same columns as trade.tsv.gz):
  extracted/trade_1880_1906.tsv.gz
  extracted/trade_1880_1906_checks.tsv     articles whose total does not equal the sum of their countries
  extracted/trade_1880_1906_skipped.tsv
Usage: read_trade_old.py [volume key ...]
"""
import collections, csv, gzip, io, json, re, sys
from decimal import Decimal
from pathlib import Path

BB = Path(__file__).parent
FIELDS = ("table_id year_volume pdf_page printed_page flow class_as_printed group_as_printed article_as_printed "
          "country_group_as_printed country_as_printed unit_as_printed measure value_as_printed value row_kind note").split()
IMPORT = ["quantity_total", "quantity_home_consumption", "value_total_rs"]
EXPORT = ["quantity_ceylon_produce", "quantity_other_produce", "quantity_total",
          "value_ceylon_produce_rs", "value_other_produce_rs", "value_total_rs"]
EMPTY = {"", ".", "..", "...", "—", "–", "-", "--", "―", "…", "— —", "Nil", "nil"}
DITTO = {'"', "''", ",,", "„", "”", "“", "〃", "»", "do.", "Do.", "do", "Do"}
GROUP = re.compile(r"^(Br(?:it(?:ish)?)?\.? ?Col(?:onies|\.)?|For(?:eign)?\.? ?Coun(?:tries|\.)?)\s*[—–\-.:]*\s*", re.I)
LEADERS = re.compile(r"\s*(?:\.{2,}|…+)[\s.…]*")
YEARS_NEW = [str(y) for y in range(1901, 1907)]


def clean(s): return LEADERS.sub(" ", s).strip(" .")


def num(c):
    """(value, ok). A dash or blank is ('', True); a number is (digits, True); anything else is ('', False)."""
    c = re.sub(r"^Rs\.?\s*", "", c.strip())
    if c in EMPTY: return "", True
    c2 = c.replace(",", "")          # a cell with a space holds two figures (two printed rows merged): not a number
    if re.fullmatch(r"\d+", c2): return c2, True
    return "", False


def flow_of(t):
    h = " ".join(t["rows"][0]).lower() if t["rows"] else ""
    first = t["rows"][0][0].strip().lower() if t["rows"] else ""
    if "countr" not in h: return None
    if first.startswith("imports") and t["n_cols"] == 5: return "import"
    if first.startswith("exports") and t["n_cols"] in (8, 9): return "export"
    return None


class Reader:
    def __init__(self, year):
        self.year = year
        self.rows, self.skipped, self.articles = [], [], []
        self.flow = None
        self.reset()

    def reset(self):
        self.cl = self.gr = self.parent = self.article = self.cg = self.unit = ""
        self.cur = None
        self.leaf = None            # the article cell last seen (the OCR repeats it on every row of the article)
        self.last_sub = None
        self.pending = ""           # a group heading that may itself be the article ("(a) Apparel, made up")

    def skip(self, t, i, r, why): self.skipped.append((t["id"], i, json.dumps(r, ensure_ascii=False), why))

    def start(self, name, t, i, continued=False):
        # Sub-entries sit under a heading ending in a dash ("Coffee—": Mixed, Unmixed). Nothing in the table marks
        # where they end. Articles and sub-entries are each in alphabetical order, so the heading is dropped when a
        # name sorts before the previous sub-entry but after the heading itself ("Confectionery" after "Unmixed").
        if self.parent and name and not continued:
            k, pk, prev = name.lower(), self.parent.rstrip("—–- ").lower(), (self.last_sub or "").lower()
            if prev and k < prev and k > pk: self.parent = ""
            self.last_sub = name if self.parent else None
        full = (self.parent + " " + name).strip() if self.parent and name else (name or self.parent)
        if continued and self.cur and self.cur["article"] == full: return
        self.pending = ""
        self.article, self.cg, self.unit = full, "", ""
        self.cur = {"article": full, "flow": self.flow, "start": t["id"], "row": i, "sum": collections.defaultdict(Decimal),
                    "totals": [], "countries": 0, "skips": 0, "continued": continued}
        self.articles.append(self.cur)

    def heading(self, s, t, i):
        s = s.strip()
        parts = [x for x in re.split(r"(?<=contd\.)\s+|\s+(?=\(\d+\)\s|\([a-z]\)\s)", s) if x]      # "II.—Raw Materials—contd. (2) Metal—contd. Copper, sheathing"
        if len(parts) > 1:
            for x in parts[:-1]: self.heading(x, t, i)
            last = parts[-1]
            if re.match(r"^(?:[IVX]+\.\s*[—–-]|\(\w+\))", last) or last.rstrip().endswith(("—", "–")) or re.search(r"contd\.?$", last): self.heading(last, t, i)
            else: self.start(clean(last), t, i)           # the article's own name, merged into the heading cell
            return
        g = GROUP.match(s)
        if g and g.end() == len(s):
            self.cg = "British Colonies" if g[1].lower().startswith("br") else "Foreign Countries"; return
        contd = bool(re.search(r"cont(?:inue)?d\.?\s*$", s, re.I))
        base = re.sub(r"\s*[—–-]?\s*cont(?:inue)?d\.?\s*$", "", s, flags=re.I).strip()
        if re.match(r"^[IVXL]+\.\s*[—–-]", base): self.cl, self.gr, self.parent = base, "", ""
        elif re.match(r"^\(\d+\)", base): self.gr, self.parent, self.pending = base, "", base
        elif re.match(r"^\([a-z]\)", base): self.gr = re.sub(r"\s*\([a-z]\).*$", "", self.gr).strip() + " " + base; self.parent = ""; self.pending = base
        else:
            p = base.rstrip("—–- ").strip() + "—"
            if not (contd and self.parent == p): self.parent = p; self.last_sub = None
            return
        # a class or group heading does not end the article in hand: its total row does (see read)

    def read(self, tables):
        for t in tables:
            flow = flow_of(t)
            if not flow: continue
            if flow != self.flow: self.flow = flow; self.reset()
            measures = IMPORT if flow == "import" else EXPORT
            for i, r in enumerate(t["rows"]):
                r = [c.strip() for c in r]
                if r[0].lower().rstrip(".,:") in ("imports", "exports"): continue
                body = [c for c in r if c and c not in ("Rs.", "Rs")]
                if not body: continue
                if len(set(body)) == 1 and (len(body) >= 3 or not any(re.search(r"\d", c) for c in r[2:])) and not re.search(r"\d{2,}", body[0]):
                    self.heading(body[0], t, i); continue
                # two ways the OCR misplaces the label cells of a country row:
                #   the country in the article column, its leaders and unit in the country column
                #   the whole row one column to the left (country in the article column, figures from the second)
                def unitish(x):
                    x = LEADERS.sub("", x).strip(" .")
                    return x == "" or x in DITTO or re.fullmatch(r"[A-Za-z]{1,6}\.?", x) is not None
                if r[0] and r[1] and re.match(r"^(?:\.{2,}|…)", r[1]) and unitish(r[1]) and any(re.search(r"\d", x) or x in ("—", "–", "-") for x in r[2:]):
                    r = ["", r[0] + " " + r[1]] + r[2:]
                elif r[0] and LEADERS.search(r[0]) and not r[-1] and (num(r[1])[1] and (re.search(r"\d", r[1]) or r[1] in EMPTY - {""})):
                    r = [""] + r[:-1]
                r[1] = re.sub(r"^(?:\.{2,}|…)[\s.…]*", "", r[1])
                a, c, figs = r[0], r[1], r[2:2 + len(measures)]
                if any(x.strip() and x.strip() not in ("Rs.", "Rs") for x in r[2 + len(measures):]):
                    self.skip(t, i, r, "figures in a column beyond the layout"); continue
                hasfig = any(re.search(r"\d", x) for x in figs)
                contd = False
                if re.fullmatch(r"[—–-]?\s*cont(?:inue)?d\.?", c, re.I): contd, c = True, ""
                if a and re.match(r"^(?:[IVXL]+\.\s*[—–-]|\((?:\d+|[a-z])\)\s)", a) and (t["id"], a) != self.leaf:
                    # class and group headings merged into the article cell: peel them off, keep the article's own name
                    self.leaf = (t["id"], a)
                    rest = a
                    while True:
                        m = re.match(r"^((?:[IVXL]+\.\s*[—–-]\s*)?(?:\((?:\d+|[a-z])\)\s*)?[^—–:(]*[—–:]+(?:\s*contd\.)?)\s*(.*)$", rest)
                        if not m or not re.match(r"^(?:[IVXL]+\.\s*[—–-]|\((?:\d+|[a-z])\))", rest): break
                        self.heading(m[1].rstrip("—–: ") if not re.search(r"contd\.$", m[1]) else m[1], t, i); rest = m[2].strip()
                    if re.match(r"^\((?:\d+|[a-z])\)\s", rest):                 # "(a) Apparel, made up": the group is the article
                        self.heading(rest, t, i); rest = re.sub(r"^\(\w+\)\s*", "", rest)
                    rest = re.sub(r"^[IVXL]+\.\s*[—–-]\s*", "", rest)       # a class numeral left without its text
                    a = rest
                if a and (t["id"], a) == self.leaf and not contd: a = ""          # the same article cell, repeated
                elif a: self.leaf = (t["id"], a)
                if a:
                    if re.search(r"cont(?:inue)?d\.?\s*$", a, re.I): contd = True; a = re.sub(r"\s*[—–-]?\s*cont(?:inue)?d\.?\s*$", "", a, flags=re.I)
                    if a.rstrip().endswith(("—", "–")) and not c and not hasfig:
                        self.heading(a + ("—contd." if contd else ""), t, i); continue
                    self.start(clean(a), t, i, continued=contd)
                if not c and not hasfig: continue
                if (self.cur is None or self.cur.get("closed")) and not a and self.pending and (c or hasfig):
                    name = re.sub(r"^\(\w+\)\s*", "", self.pending).rstrip("—–- ")
                    self.parent = ""; self.start(clean(name), t, i); self.cur["named_by_heading"] = True
                if self.cur is None or (self.cur.get("closed") and not a):
                    self.skip(t, i, r, "figures with no article heading above them (after an article's total, or at the start of a run of pages)"); continue
                m = GROUP.match(c)
                if m and (m.end() == len(c) or c[m.end():].strip()):
                    self.cg = "British Colonies" if m[1].lower().startswith("br") else "Foreign Countries"
                    c = c[m.end():].strip()
                    if not c and not hasfig: continue
                note = [f"source row {i}"] + (["article named by its group heading"] if self.cur.get("named_by_heading") else [])
                if not c:
                    kind, country, unit = "article_total", "", self.unit
                    note.append("unlabelled row of figures read as the article total")
                elif re.match(r"^total\b", c, re.I):
                    kind, country, unit = "article_total", clean(c), self.unit
                else:
                    kind = "country"
                    parts = LEADERS.split(c, maxsplit=1)
                    country, tail = parts[0].strip(" ."), (parts[1].strip() if len(parts) > 1 else "")
                    if tail in DITTO or not tail: unit = self.unit; note += ["unit from ditto"] if tail in DITTO and self.unit else []
                    else: unit = tail; self.unit = unit
                    if not country or re.search(r"\d", country):
                        self.cur["skips"] += 1; self.skip(t, i, r, "country label not readable"); continue
                vals = [num(x) for x in figs]
                if not all(ok for _, ok in vals):
                    self.cur["skips"] += 1; self.skip(t, i, r, "a figure cell is not a plain number"); continue
                if kind == "country": self.cur["countries"] += 1
                else: self.cur["closed"] = True
                for mname, raw, (v, _) in zip(measures, figs, vals):
                    self.rows.append([t["id"], self.year, t["pdf_page"], t.get("printed_page") or "", flow, self.cl, self.gr, self.article,
                                      self.cg if kind == "country" else "", country, unit if mname.startswith("quantity") else "", mname,
                                      re.sub(r"^Rs\.?\s*", "", raw), v, kind, "; ".join(note)])
                    if kind == "country" and v: self.cur["sum"][mname] += Decimal(v)
                    elif kind == "article_total" and v: self.cur["totals"].append((mname, Decimal(v), t["id"], i, self.cur["sum"][mname]))
        return self



# The modern ledgers use plain numbers. Keep the older reader above for the
# compound weights and currency of the nineteenth-century tables.
CONT = r'(?:[—–-]+\s*)?cont(?:inue)?d\.?'
CLASS_PREFIX = re.compile(r'^((?:[IVXL]+|1|11|111)\.\s*[—–-]*\s*)(Manufactured(?:\s+Articles)?|Raw [Mm]aterials|Bullion and Coin|Live Animals)?', re.I)
GROUP_TEXT = re.compile(r'^\((\d+|[a-z])\)\.?\s*(Chemical,? Dyeing,? and Tanning(?: Materials)?|Apparel, made up|Food and Drink|Animals, Living|Live Animals|Of Metal \(other than Machinery\.?\)|Metal \(other than Machinery\)|Of Metal other than Machinery|Metal other than Machinery|Of Metal other|Of Metal \(other|Other Mixed Materials|Of Mixed Materials|Silk and Satin|Timber[,;] [un-]*worked|Miscellaneous|Narcotics|Spirits|Textile|Cotton|Linen|Lineh|Woollen|Metal|Other)', re.I)
UNIT_END = re.compile(r'(?:^|\s)(\{?\s*(?:No\. of Bunches\.?|reams\.?|oz\.?|pwt\.?|gross|val\.?|wt\.?|bots\.?|Bot\.?|pcs\.?|Bars|b\.?|4 doz\.?(?: cases)?|cwt\.?|cwts\.?|tons?\.?|lb\.?|lbs\.?|gals?\.?|yds\.?|doz\.?|pkgs\.?|pieces\.?|cases\.?|No\.?|pairs\.?|bundles\.?|heads?\.?|feet\.?|ft\.?|sq\. ft\.?|' + '|'.join(re.escape(x) for x in sorted(DITTO, key=len, reverse=True)) + r'))\s*$', re.I)
GENERIC = {'other', 'tinned', 'fresh', 'dried', 'dyed', 'gray', 'grey', 'free', 'dutiable', 'in wood', 'in bottle', 'in bottles', 'bottled', 'unmixed', 'mixed', 'bleached', 'printed', 'single', 'double', 'magazine', 'scientific', 'agricultural', 'locomotive', 'unrefined', 'refined or candied'}


def name_key(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def strip_cont(s):
    return re.sub(CONT + r'\s*$', '', s, flags=re.I).strip(' .—–-:')


def peel_structure(s):
    """Return literal OCR class/group prefixes separately from the article tail."""
    s = s.strip(); parts = []
    m = CLASS_PREFIX.match(s)
    if m:
        # A bare numeral is structural too; its following word is the article.
        end = m.end()
        parts.append(('class', s[:end].strip()))
        s = s[end:].lstrip(' .—–-:')
        s = re.sub(r'^' + CONT + r'\s*', '', s, flags=re.I).strip()
    while s:
        m = GROUP_TEXT.match(s)
        if not m: break
        parts.append(('group', m[0].strip()))
        s = s[m.end():].lstrip(' .—–-:')
        s = re.sub(r'^' + CONT + r'\s*', '', s, flags=re.I).strip()
    return parts, s


def table_measures(t, flow):
    """Read the printed column titles on this table, including reversed imports."""
    if flow == 'import':
        result = []
        for title in t['rows'][0][2:]:
            k = name_key(title)
            if not k: continue
            if 'homeconsumption' in k: result.append('quantity_home_consumption')
            elif 'quantit' in k and 'import' in k: result.append('quantity_total')
            elif 'value' in k and 'import' in k: result.append('value_total_rs')
            else: return None
        return result if sorted(result) == sorted(IMPORT) else None
    result = []; category = ''
    for j, title in enumerate(t['rows'][1][2:], 2):
        top = name_key(t['rows'][0][j])
        if 'quantity' in top: category = 'quantity'
        elif 'value' in top: category = 'value'
        k = name_key(title)
        if not k: continue
        if k.startswith('total'): suffix = 'total'
        elif k.startswith('british'): suffix = 'other_produce'
        elif k.startswith(('produce', 'product')): suffix = 'ceylon_produce'
        else: return None
        if not category: return None
        result.append(category + '_' + suffix + ('_rs' if category == 'value' else ''))
    return result if sorted(result) == sorted(EXPORT) else None


class HeadingEvidence:
    """Learn literal heading/leaf relationships from repeated OCR ledgers.

    Trust an explicit inline pair and the first leaf after a dashed heading.
    Subsequent ordered leaves form a candidate run; a descending non-generic
    leaf ends it. Require recurrence in two volumes/flows before learning an
    implicit pair, and reject names independently attested as top-level in the
    same major class. This distinguishes Tea (food) from Seeds— Tea (materials).
    """
    def __init__(self, tables):
        tables=list(tables)
        self.children=collections.defaultdict(set); self.heads=set()
        self.top=collections.Counter(); self.names=set(); self.possible_children=collections.defaultdict(set); sequences=[]
        # Continuation suffixes do not establish headings by themselves:
        # Tea—contd. and Dyed—contd. are article continuations.
        for ts in tables:
            for t in ts:
                if not flow_of(t): continue
                for r in t['rows'][1:]:
                    _,s=peel_structure(r[0])
                    s=re.sub(CONT,'',s,flags=re.I).strip()
                    for h in re.findall(r'(?:^|(?<=\.))\s*([^—–]+?)[—–](?!\s*contd)',s):
                        h=clean(h)
                        if h: self.heads.add(name_key(h))
        for ts in tables:
            seq=[]; last=None; context=''; flow=None; group=''
            for t in ts:
                f=flow_of(t)
                if not f: continue
                if f!=flow:
                    sequences.append(seq); seq=[]; context=''; group=''; last=None; flow=f
                for ri, r in enumerate(t['rows'][1:], 1):
                    a=r[0].strip()
                    if ri > 1:
                        prev=t['rows'][ri-1]
                        if prev[0].endswith('-') and not prev[0].endswith('--') and a and not prev[1]: a=prev[0][:-1]+a
                    if a.endswith('-') and not a.endswith('--') and ri+1<len(t['rows']) and t['rows'][ri+1][0] and not r[1]: continue
                    if not a or a==last or not re.search('[A-Za-z]',a) or a in ('Rs.','Rs'): continue
                    last=a
                    parts,a=peel_structure(a)
                    for typ,text in parts:
                        if typ=='class':
                            ctx=re.sub(r'^(?:[IVXL]+|1|11|111)\.\s*[—–-]*\s*','',text).lower().replace(' articles','')
                            if 'live animals' in ctx or (not ctx and re.match(r'^(?:I|L|1)\.', text)): ctx='consumption'
                            if ctx and ctx!=context:
                                context=ctx; group=''; seq.append(('boundary','',context))
                        else:
                            g=name_key(text)
                            if re.search('Food and Drink|Live Animals|Animals, Living|Narcotics',text,re.I): context='consumption'
                            if g!=group and 'contd' not in r[0].lower(): seq.append(('boundary','',context))
                            group=g
                    chunks=re.split(CONT+r'\s*',a,flags=re.I)
                    for j,ch in enumerate(chunks):
                        ch=clean(ch).strip(' .—–-:')
                        if not ch or ch.lower()=='articles': continue
                        self.names.add(ch)
                        if j<len(chunks)-1:
                            seq.append(('head' if name_key(ch) in self.heads else 'leaf',ch,context)); continue
                        raw=a.rstrip()
                        if re.search(r'[—–]|--',ch):
                            h,leaf=re.split(r'[—–]|--',ch,maxsplit=1); h,leaf=clean(h),clean(leaf)
                            if h and leaf:
                                self.children[name_key(h)].add(name_key(leaf));self.heads.add(name_key(h))
                                seq.extend([('head',h,context),('leaf',leaf,context)]); continue
                        seq.append(('head' if raw.endswith(('—','–','--')) else 'leaf',ch,context))
            sequences.append(seq)
        candidates=collections.defaultdict(set); tops=collections.Counter()
        for run, seq in enumerate(sequences):
            parent='';prev='';first=False
            for typ,s,ctx in seq:
                k=name_key(s)
                if typ=='boundary': parent='';prev='';continue
                if typ=='head' and not (parent and k in self.children[parent]): parent=k;prev='';first=True;continue
                if parent:
                    if first:
                        self.children[parent].add(k);first=False;prev=k;continue
                    if s.lower() in GENERIC or k in self.children[parent] or (k>=prev and prev!='other' and (k<parent or k[:1]!=parent[:1])):
                        candidates[parent,k,ctx].add(run);prev=k;continue
                    parent='';prev=''
                tops[k,ctx]+=1;self.top[k]+=1
        for (p,k,ctx),runs in candidates.items():
            n=len(runs)
            if n>=2: self.possible_children[p].add(k)
            if n>=2 and not tops[k,ctx]: self.children[p].add(k)

        # Retain every literal level of inline chains, and adjacent dashed
        # headings (Paper / Other, Coffee / Arabian), across all six volumes.
        self.branches = set()
        self.aliases = collections.defaultdict(dict)
        for ts in tables:
            prior = ''; previous_flow = None
            for t in ts:
                f = flow_of(t)
                if not f: continue
                if f != previous_flow: prior = ''; previous_flow = f
                last = None
                for r in t['rows'][1:]:
                    if not r[0] or r[0] == last: continue
                    last = r[0]
                    parts, text = peel_structure(r[0])
                    if parts and not re.search('contd', r[0], re.I): prior = ''
                    if not text or not re.search('[A-Za-z]', text): continue
                    text = re.sub(CONT, '', text, flags=re.I).strip()
                    chunks = [clean(x).strip(' .:') for x in re.split('[—–]+|--', text) if clean(x)]
                    if not chunks: continue
                    for a, b in zip(chunks, chunks[1:]):
                        self.children[name_key(a)].add(name_key(b))
                        self.branches.add(name_key(a))
                    dashed = text.endswith(('—', '–', '--')) or (bool(re.search(CONT, r[0], re.I)) and name_key(text) in self.branches)
                    only_heading = not r[1] or len(set(x for x in r if x)) == 1
                    if dashed and only_heading and not re.search(CONT, r[0], re.I):
                        self.branches.add(name_key(chunks[-1]))
                    # A continuation alone cannot turn a known leaf into a branch.
                    if dashed and only_heading:
                        if prior and name_key(chunks[0]) != prior:
                            self.children[prior].add(name_key(chunks[0]))
                        prior = name_key(chunks[-1])
                    else: prior = ''
        runs = collections.defaultdict(set)
        for run, ts in enumerate(tables):
            stack=[]; prev={}; flow=None; last=None
            for t in ts:
                f=flow_of(t)
                if not f: continue
                if f!=flow: stack=[]; prev={}; flow=f; last=None
                for r in t['rows'][1:]:
                    if not r[0] or r[0]==last: continue
                    last=r[0]
                    parts,text=peel_structure(r[0])
                    if parts and not re.search(CONT,r[0],re.I): stack=[]; prev={}
                    if not text: continue
                    text=re.sub(CONT,'',text,flags=re.I).strip()
                    chunks=[clean(x).strip(' .:') for x in re.split('[—–]+|--',text) if clean(x)]
                    for j, literal in enumerate(chunks):
                        k=name_key(literal)
                        if not k or k in {'imports','exports','rs','articles'}: continue
                        head=j<len(chunks)-1 or (k in self.branches and (text.endswith(('—','–','--')) or re.search(CONT,r[0],re.I)))
                        if head:
                            if k in stack: stack=stack[:stack.index(k)+1]
                            elif stack and k in self.children[stack[-1]]: prev[stack[-1]]=k;stack.append(k)
                            elif len(stack)>1 and len(self.children[k] & self.children[stack[-1]])>=2:
                                self.children[stack[-2]].add(k)
                                stack=stack[:-1]+[k]
                            else: stack=[k]
                            continue
                        if k=='pearlsandpreciousstones': stack=[]
                        # A descent within a nested branch can return to its
                        # outer ordered run (Arabian / Plantation -> Liberian).
                        while len(stack)>1 and k not in self.children[stack[-1]] and k not in GENERIC and k<prev.get(stack[-1],''):
                            stack.pop()
                        if not stack: continue
                        p=stack[-1]; old=prev.get(p,'')
                        known=k in self.children[p]
                        generic=literal.lower() in GENERIC
                        same_stem=any(re.sub(r'\(.*','',literal).strip().lower()==re.sub(r'\(.*','',n).strip().lower() and name_key(n) in self.children[p] for n in self.names) if '(' in literal else False
                        ordered=(not old or k>=old) and old!='other' and (k<p or k[:1]!=p[:1])
                        if p in GENERIC and not known and not generic: stack=[]; continue
                        if known or generic or same_stem or ordered:
                            runs[p,k].add((run,flow)); prev[p]=k
                        else: stack=[]
        for (p,k), appearances in runs.items():
            if len(appearances)>=2 and (not self.top[k] or p in {'spices','oil','cocoanut','coffee','arms'} or k in GENERIC): self.children[p].add(k)
        # Ordered runs recur in both flows. These families have independent
        # top-level homonyms in other classes, which must not veto membership.
        for p in ('spices', 'oil', 'cocoanut', 'coffee', 'arms'):
            self.children[p].update(self.possible_children[p] - {'imports', 'exports'})
        # The reviewed government-store layout explicitly nests this heading.
        # Both labels are literal OCR; no spelling is supplied or corrected.
        self.children[name_key('Seeds, excluding Food Stuffs')].add('unenumerated')
        # A terminal top-level article after the bullion/coin entries, as
        # printed; the alphabetical heuristic alone cannot distinguish it.
        self.top_level = {name_key('Pearls and Precious Stones')}
        for children in self.children.values(): children.difference_update(self.top_level)
        # Elliptical comma leaves: learn Cinnamon, Wild from the full forms
        # in other volumes, without changing the current row's word Wild.
        for p, children in self.children.items():
            for literal in sorted(self.names):
                if ',' in literal and name_key(literal) in children:
                    prefix, leaf = literal.rsplit(',', 1)
                    self.aliases[p][name_key(leaf)] = prefix.strip() + ', '


class ModernReader(Reader):
    @property
    def parent(self):
        return ' '.join(self.heading_stack)

    @parent.setter
    def parent(self, value):
        self.heading_stack = [value] if value else []

    def __init__(self, year, evidence):
        self.evidence = evidence
        self.gov = False
        self.block = []
        super().__init__(year)
        self.government_pages = set()
        # Page headings, rather than hard-coded page intervals, identify the
        # second ledger. Only selected import tables are affected.
        active = False
        path = BB / f'pages/{year}.jsonl.gz'
        if path.exists():
            for line in gzip.open(path, 'rt'):
                p = json.loads(line)
                h = ' '.join(p.get('headings') or [])
                if re.search(r'GENERAL IMPORTS.*Government Stores', h, re.I): active = True
                elif re.search(r'GENERAL (?:EXPORTS|IMPORTS)', h, re.I): active = False
                if active: self.government_pages.add(p['pdf_page'])

    def reset(self):
        super().reset()
        self.top_name = ''
        self.pending_cg = ''
        self.heading_context = []
        self.article_note = []
        self.block = []
        self.last_country = ''
        self.last_cg = ''
        self.total_units = []

    def start(self, name, t, i, continued=False):
        name = clean(name).strip()
        uncertainty = []
        k = name_key(name)
        matched = False
        if k in self.evidence.top_level:
            self.parent = ''
            self.heading_context = []
        if not self.parent:
            for depth in range(len(self.heading_context)-1,-1,-1):
                p=name_key(self.heading_context[depth])
                if k in self.evidence.children[p]:
                    self.heading_stack=self.heading_context[:depth+1]
                    break
        for depth in range(len(self.heading_stack)-1, -1, -1):
            p = name_key(self.heading_stack[depth])
            known = k in self.evidence.children[p]
            if not known and len(k) >= 7:
                known = any(k + ending == child or child + ending == k
                            for child in self.evidence.children[p] for ending in ('h', 's'))
            alias = self.evidence.aliases[p].get(k)
            if alias and name_key(alias) not in name_key(self.article): alias = None
            if known or alias:
                self.heading_stack = self.heading_stack[:depth+1]
                if alias: name = alias + name
                matched = True
                break
        if self.parent and not matched:
            p = name_key(self.heading_stack[-1])
            if name.lower() not in GENERIC and not (k < p and (not self.last_sub or k >= name_key(self.last_sub))):
                uncertainty = [f'heading uncertain: may belong under "{self.parent}"'] if k in self.evidence.possible_children[p] else []
                self.parent = ''
        if self.parent: self.last_sub = name
        else: self.last_sub = None
        full = (self.parent + ' ' + name).strip() if self.parent else name
        if continued and self.cur and self.article == full and not self.cur.get('closed'):
            if not self.cur['unsafe'] or self.cur['start']==t['id']: return
            # A readable continuation is a new segment after a collapsed page.
            # Do not let the rejected page suppress its legible continuation.
        self.finish()
        self.pending = ''
        self.article, self.cg, self.unit = full, self.pending_cg, ''
        self.pending_cg = ''
        self.article_note = uncertainty
        if not self.parent: self.top_name = name
        self.last_country = ''; self.last_cg = ''; self.total_units = []
        self.quantity_components = []
        self.cur = {'article': full, 'flow': self.flow, 'start': t['id'], 'row': i,
                    'sum': collections.defaultdict(Decimal), 'totals': [], 'countries': 0,
                    'skips': 0, 'continued': continued, 'unsafe': ''}
        self.articles.append(self.cur)

    def set_parent(self, s):
        p = strip_cont(s).rstrip('—–- ') + '—'
        k = name_key(p)
        for depth, old in enumerate(self.heading_stack):
            if name_key(old) == k:
                self.heading_stack = self.heading_stack[:depth] + [p]
                self.heading_context = self.heading_stack[:]
                return
        for depth in range(len(self.heading_stack)-1, -1, -1):
            old = name_key(self.heading_stack[depth])
            if k in self.evidence.children[old]:
                self.heading_stack = self.heading_stack[:depth+1] + [p]
                self.heading_context = self.heading_stack[:]
                self.last_sub = None
                return
        self.parent = p
        self.heading_context = self.heading_stack[:]
        self.last_sub = None

    def label(self, s, t, i, has_data=False):
        parts, rest = peel_structure(s)
        for typ, text in parts:
            if typ == 'class':
                # Repeated continuation headings must not discard a live parent.
                old = name_key(re.sub(r'^(?:[IVXL]+|1|11|111)\.', '', self.cl))
                new = name_key(re.sub(r'^(?:[IVXL]+|1|11|111)\.', '', text))
                if old and new and not (old.startswith(new) or new.startswith(old)):
                    self.gr = ''; self.parent = ''; self.top_name = ''; self.heading_context=[]
                self.cl = text
            else:
                if re.match(r'^\(\d+\)', text):
                    old = re.sub(r'\s*\([a-z]\).*', '', self.gr)
                    same = name_key(old) == name_key(text)
                    if not same: self.parent = ''; self.top_name = ''; self.heading_context=[]
                    self.gr = (text + self.gr[len(old):]) if same else text
                else:
                    old = re.search(r'\([a-z]\).*', self.gr)
                    same = old and name_key(old[0]) == name_key(text)
                    if not same: self.parent = ''; self.top_name = ''; self.heading_context=[]
                    self.gr = re.sub(r'\s*\([a-z]\).*', '', self.gr).strip() + ' ' + text
                if not same and re.match(r'^\([a-z]\)', text) and not re.search('contd', s, re.I): self.pending = text
        if not rest or not re.search('[A-Za-z]', rest) or rest in ('Rs.', 'Rs'): return
        # An isolated tail of Manufactured Articles is never a parent.
        rest = re.sub(r'^Articles\.?\s*[—–-]*\s*contd\.?\s*', '', rest, flags=re.I).strip()
        if not rest: return
        country_group = GROUP.match(rest)
        if country_group and country_group.end() == len(rest):
            self.cg = 'British Colonies' if country_group[1].lower().startswith('br') else 'Foreign Countries'
            self.pending_cg = self.cg
            return
        # Distinguish continuation leaves from headings before stripping contd.
        chunks = re.split(r'\s*' + CONT + r'\s*', rest, flags=re.I)
        for chunk in chunks[:-1]:
            chunk = chunk.strip(' .—–-:')
            if not chunk: continue
            inline = re.match(r'^(.*?)[—–]+\s*(.+)$', chunk)
            if inline:
                chain = re.split(r'[—–]+', chunk)
                for h in chain[:-1]: self.set_parent(h)
                self.start(chain[-1], t, i, continued=True)
            elif name_key(chunk) in self.evidence.branches:
                self.set_parent(chunk)
            else: self.start(chunk, t, i, continued=True)
        tail = chunks[-1].strip()
        if not tail: return
        chain = [x.strip() for x in re.split(r'[—–]+|--', tail)]
        if len(chain)>1:
            for h in chain[:-1]:
                if not h: continue
                # A dash attached to a data-bearing known leaf is continuation furniture.
                leaf = any(name_key(h) in self.evidence.children[name_key(p)] for p in self.heading_stack)
                if has_data and leaf and name_key(h) not in self.evidence.branches and not chain[-1]:
                    self.start(h,t,i,continued=True); return
                self.set_parent(h)
            tail=chain[-1]
            if not tail: return
        if re.search('[A-Za-z]', clean(tail)): self.start(clean(tail), t, i)

    def finish(self):
        if not self.cur or not self.block: return
        a = self.cur
        if a['unsafe']:
            for rec in self.block: self.skip(rec['t'], rec['i'], rec['raw'], a['unsafe'])
            a['skips'] += len(self.block)
            a['countries'] = 0
            a['totals'] = []
            self.block = []; return
        sums = collections.defaultdict(Decimal)
        for rec in self.block:
            if rec['kind'] == 'country':
                for m, raw, extra in rec['values']:
                    v, ok = num(raw)
                    if v: sums[(m, rec['unit'] if m.startswith('quantity') else '')] += Decimal(v)
        disagree = False
        for rec in self.block:
            if rec['kind'] != 'article_total': continue
            printed = collections.defaultdict(Decimal)
            for m, raw, extra in rec['values']:
                v, ok = num(raw)
                if v: printed[m] += Decimal(v)
            for m, v in printed.items():
                total = sums[(m, rec['unit'] if m.startswith('quantity') else '')]
                a['totals'].append((m, v, rec['t']['id'], rec['i'], total, rec['unit'] if m.startswith('quantity') else ''))
                if v != total: disagree = True
        wrapped = any('wrapped country' in '; '.join(rec['notes']) for rec in self.block)
        for rec in self.block:
            note = [f"source row {rec['i']}"] + rec['notes'] + self.article_note
            if self.gov: note.append('government stores imports')
            if wrapped and (disagree or not a['totals']) and rec['kind'] == 'country':
                note.append('possible row shift after a wrapped country name')
            for m, raw, extra in rec['values']:
                v, ok = num(raw)
                t = rec['t']
                self.rows.append([t['id'], self.year, t['pdf_page'], t.get('printed_page') or '', a['flow'],
                    rec['cl'], rec['gr'], a['article'], rec['cg'] if rec['kind']=='country' else '', rec['country'],
                    rec['unit'] if m.startswith('quantity') else '', m, re.sub(r'^Rs\.?\s*', '', raw), v,
                    rec['kind'], '; '.join(note + ([extra] if extra else []))])
        self.block = []

    def table_rows(self, t):
        """Join wrapped names; preserve the row of the figures as provenance.

        A wrap with figures on both label lines can shift the rest of a country
        group. Reassociate only when the label/vector counts agree, a trailing
        country has no figures, and the only discarded vector is all dashes.
        Totals are checked after the article is buffered.
        """
        rows = []
        for i, raw in enumerate(t['rows']):
            r = [x.strip() for x in raw]
            body = [x for x in r if x]
            if body and len(set(body)) == 1 and len(body)>2:
                r = [body[0], ''] + ['']*(len(r)-2)
            rows.append({'i':i, 'r':r, 'raw':raw, 'notes':[]})
        # Two independent names can occupy one OCR cell. Split only when
        # their following country runs have an explicit change of printed unit.
        for j, item in enumerate(rows):
            a=clean(item['r'][0])
            if not a: continue
            for cut in [m.start() for m in re.finditer(' ',a)]:
                left,right=a[:cut],a[cut+1:]
                if left not in self.evidence.names or right not in self.evidence.names: continue
                if ' ' in left or not GROUP.match(item['r'][1]) or any(re.search(r'\d',x) for x in item['r'][2:]): continue
                first_unit=None
                for following in rows[j+1:]:
                    rr=following['r']
                    if rr[0]: break
                    u=UNIT_END.search(rr[1])
                    if not u or u[1] in DITTO: continue
                    if first_unit is None: first_unit=u[1]; continue
                    if u[1]!=first_unit:
                        item['r'][0]=left
                        rr[0]=right
                        following['notes'].append('article name separated from preceding one-line article at printed unit change')
                    break
                break
        j = 0
        while j < len(rows)-1:
            x, y = rows[j], rows[j+1]; r, s = x['r'], y['r']
            # A heading may share the first continued country's figures,
            # with its leaf displaced onto the next country row.
            if r[0].endswith(('—','–')) and any(re.search(r'\d',v) for v in r[2:]) and re.search(CONT+r'$',s[0],re.I):
                leaf=strip_cont(s[0])
                if name_key(leaf) in self.evidence.children[name_key(r[0])]:
                    r[0] += ' '+s[0]
                    s[0]=''
            # Wrapped article names without data (Refined or / Candied).
            if r[0] and r[0] not in ('Rs.', 'Rs') and re.search('[A-Za-z]', r[0]) and not r[1] and (r[0].endswith('-') or clean(r[0]+' '+s[0]) in self.evidence.names) and s[0] and not re.match(r'^[IVXL]+\.|^\(', r[0]) and not r[0].endswith(('—','–','--')) and not re.search('contd',r[0],re.I):
                s[0] = r[0].rstrip('-') + ('' if r[0].endswith('-') else ' ') + s[0]
                if any(re.search(r'\d', z) for z in r[2:]): r[0]=''
                else: x['r'] = ['']*len(r)
            # Country continuation can be a hyphenated word or parenthesis.
            if not r[0] and r[1] and (r[1].endswith('-') or r[1].count('(')>r[1].count(')')) and not s[0] and s[1] and not GROUP.match(s[1]):
                label = r[1].rstrip('-') + ('' if r[1].endswith('-') else ' ') + s[1]
                x['notes'].append('joined wrapped country name')
                if not any(re.search(r'\d', z) for z in r[2:]):
                    s[1] = label; y['notes'].append('joined wrapped country name'); x['r']=['']*len(r)
                elif not any(re.search(r'\d', z) for z in s[2:]):
                    r[1] = label; y['r']=['']*len(s)
                else:
                    # There are figures on both halves. Collect the remainder
                    # of this country group, then align its complete labels and
                    # numeric vectors if there is a trailing empty label slot.
                    end=j+2
                    while end<len(rows) and not rows[end]['r'][0] and rows[end]['r'][1] and not GROUP.match(rows[end]['r'][1]): end+=1
                    seg=rows[j:end]; labels=[]; vectors=[]; q=0
                    while q<len(seg):
                        z=seg[q]; rr=z['r']; lab=rr[1]
                        if lab.endswith('-') and q+1<len(seg):
                            lab=lab[:-1]+seg[q+1]['r'][1]; q+=1
                        labels.append(lab); q+=1
                    for z in seg:
                        if any(re.search(r'\d', v) for v in z['r'][2:]): vectors.append(z)
                    if len(labels)==len(vectors) and not any(re.search(r'\d',z) for z in seg[-1]['r'][2:]):
                        for z in seg: z['r'][1]=''
                        for lab,z in zip(labels,vectors):
                            z['r'][1]=lab; z['notes'].append('reassociated figures after a wrapped country name')
                        for z in seg:
                            if z not in vectors: z['r']=['']*len(z['r'])
                        j=end-1
                    else:
                        # The suffix is a label, not another country. Keep the
                        # first vector and skip the ambiguous second one.
                        r[1]=label
                        self.skip(t,y['i'],y['raw'],'ambiguous extra figures on wrapped country suffix')
                        y['r']=['']*len(s)
                        x['notes'].append('possible row shift after a wrapped country name')
            j+=1
        return rows

    def tea_values(self, figs):
        figs = list(figs)
        while len(figs)>6 and not figs[-1]: figs.pop()
        # OCR occasionally merges Black and Green into one cell.
        if len(figs)==6 and len(figs[0].split())==2:
            figs = figs[0].split()+figs[1:]
        def n(s):
            v,ok=num(s); return int(v or 0) if ok else None
        ns=[n(x) for x in figs]
        if None in ns: return None
        if len(figs)==7 and sum(ns[:3])==ns[3] and ns[4]+ns[5]==ns[6]:
            names=[EXPORT[0], EXPORT[0]]+EXPORT[1:]
            return [(m,r,'component black' if j==0 else 'component green' if j==1 else '') for j,(m,r) in enumerate(zip(names,figs))]
        if len(figs)==6 and ns[0]+ns[1]==ns[2] and ns[3]+ns[4]==ns[5]:
            names=[EXPORT[0], EXPORT[0]]+EXPORT[2:]
            return [(m,r,'component black' if j==0 else 'component green' if j==1 else '') for j,(m,r) in enumerate(zip(names,figs))]
        return None

    def read(self, tables):
        for t in tables:
            flow=flow_of(t)
            if not flow: continue
            gov=flow=='import' and t['pdf_page'] in self.government_pages
            if flow!=self.flow or gov!=self.gov:
                self.finish(); self.flow=flow; self.reset(); self.gov=gov
            measures=table_measures(t,flow)
            if measures is None:
                for i,r in enumerate(t['rows'][1:],1): self.skip(t,i,r,'unrecognized table measure headers')
                continue
            raw_leaf=None
            for item in self.table_rows(t):
                i,r,original=item['i'],item['r'],item['raw']
                if not any(r): continue
                if r[0].lower().rstrip('.,:') in ('imports','exports'): continue
                # Repair the two displaced label layouts also handled by the
                # legacy reader, without touching any numeric cell.
                if r[0] and r[1] and re.match(r'^(?:\.{2,}|…)',r[1]) and not re.search(r'[A-Za-z]{7}',r[1]) and any(re.search(r'\d',x) for x in r[2:]):
                    r=['',r[0]+' '+r[1]]+r[2:]
                elif r[0] and LEADERS.search(r[0]) and not r[-1] and num(r[1])[1] and (re.search(r'\d',r[1]) or r[1] in EMPTY- {''}): r=['']+r[:-1]
                a,c=r[:2]; figs=r[2:]
                after_label=''
                if a and c and any(re.search(r'\d', x) for x in figs):
                    for cut in [m.start() for m in re.finditer(' ', a)]:
                        left,right=a[:cut],a[cut+1:]
                        h=re.split('[—–]',right,maxsplit=1)[0].strip()
                        if ' ' not in left and left in self.evidence.names and (right.strip(' .') in self.evidence.names or name_key(h) in self.evidence.heads):
                            a,after_label=left,right
                            break
                notes=item['notes'][:]
                if not re.search('[A-Za-z]', a) or a in ('Rs.', 'Rs'): a=''
                if a==raw_leaf: a=''
                elif a: raw_leaf=a
                # The tail of the class heading can precede a country label.
                class_tail = bool(re.match(r'^Articles\.?\s*[—–-]*\s*contd\.?',c,re.I))
                group_tail = ''
                if class_tail:
                    if 'Articles' not in self.cl and 'Manufactured' in self.cl: self.cl += ' Articles'
                    c=re.sub(r'^Articles\.?\s*[—–-]*\s*contd\.?\s*','',c,flags=re.I)
                # Class/group continuation tails can share the country cell
                # with a real country; consume the furniture only.
                tail_match=re.match(r'^(than Machinery\)?)[.—– -]*contd\.?\s*', c, re.I)
                if tail_match:
                    group_tail=tail_match[1]
                    c=c[tail_match.end():]
                c=re.sub(r'^(?:[—–-]*\s*contd\.?\s*)+', '', c, flags=re.I).strip()
                c=re.sub(r'^(?:\.{2,}|…)[\s.…]*','',c)
                hasfig=any(re.search(r'\d',x) for x in figs)
                if a and any(re.search(r'gal\.?\s+cases|gals?\.?\s*&\s*cases',x,re.I) for x in figs):
                    self.label(a,t,i,True)
                    self.cur['unsafe']='quantity sub-columns gal. / cases: OCR row alignment ambiguous'
                    self.skip(t,i,original,self.cur['unsafe'])
                    continue
                if not hasfig and all(x in EMPTY or x in ('Rs.','Rs','Black','Green') for x in figs):
                    if a: self.label(a + (' contd.' if re.fullmatch(r'[—–-]*\s*contd\.?',r[1],re.I) else ''),t,i)
                    if class_tail and 'Manufactured' in self.cl and 'Articles' not in self.cl: self.cl += ' Articles'
                    if group_tail and group_tail not in self.gr: self.gr += ' ' + group_tail
                    g=GROUP.match(c)
                    if g:
                        self.cg='British Colonies' if g[1].lower().startswith('br') else 'Foreign Countries'
                        if not c[g.end():].strip(): self.pending_cg=self.cg
                        c=c[g.end():].strip()
                    if not c or re.fullmatch(r'(?:[—–-]*\s*contd\.?\s*)+',c,re.I): continue
                # A new heading sharing an old total must take effect AFTER it.
                g=GROUP.match(c)
                total_before=bool(a and hasfig and self.cur and not self.cur.get('closed') and (not c or (g and not c[g.end():].strip())))
                if total_before and g:
                    accumulated=collections.defaultdict(Decimal)
                    for rec in self.block:
                        if rec['kind']=='country':
                            for m,raw,extra in rec['values']:
                                v,ok=num(raw)
                                if v: accumulated[m]+=Decimal(v)
                    total_before = len(figs)>=len(measures) and all(num(raw)[1] and Decimal(num(raw)[0] or '0')==accumulated[m] for m,raw in zip(measures,figs))
                deferred=a if total_before else ''
                if a and not total_before: self.label(a,t,i,True)
                if class_tail and 'Manufactured' in self.cl and 'Articles' not in self.cl: self.cl += ' Articles'
                if group_tail and group_tail not in self.gr: self.gr += ' ' + group_tail
                if g:
                    self.cg='British Colonies' if g[1].lower().startswith('br') else 'Foreign Countries'
                    c=c[g.end():].strip()
                    if not c and hasfig and not total_before:
                        self.skip(t,i,original,'country name lost: unlabelled figures on a country-group heading')
                        if self.cur: self.cur['skips']+=1
                        continue
                    if not c and not hasfig: continue
                if re.search(r'carried\s+(?:over|forward)|brought\s+forward',c,re.I):
                    self.skip(t,i,original,'carried over / brought forward, not data'); continue
                if c and re.fullmatch(r'(?:Articles\s*)?(?:[—–-]*\s*contd\.?\s*)+',c,re.I):
                    self.skip(t,i,original,'page-top continuation text, not data'); continue
                if self.pending:
                    self.start(re.sub(r'^\(\w+\)\s*','',self.pending).strip('—–- '),t,i)
                    notes.append('article named by its group heading')
                if not self.cur or (self.cur.get('closed') and not a and (c or not any('braced unit line' in z['notes'] for z in self.block))):
                    if self.pending:
                        self.start(re.sub(r'^\(\w+\)\s*','',self.pending).strip('—–- '),t,i)
                        notes.append('article named by its group heading')
                    else:
                        if hasfig: self.skip(t,i,original,'figures with no article heading above them')
                        continue
                if not hasfig and not c: continue
                if self.cur['unsafe'].startswith('quantity sub-columns'):
                    self.skip(t,i,original,self.cur['unsafe']); self.cur['skips']+=1
                    continue
                kind='article_total' if not c or re.match(r'^total\b',c,re.I) else 'country'
                country=''; unit=self.unit
                if kind=='country':
                    parts=LEADERS.split(c,maxsplit=1)
                    country=parts[0].strip(); tail=parts[1].strip() if len(parts)>1 else ''
                    if not tail:
                        m=UNIT_END.search(country)
                        if m:
                            tail=m[1].strip(); country=country[:m.start()].strip(' .')
                    if not country and tail.startswith('{') and self.last_country:
                        country=self.last_country; self.cg=self.last_cg
                        notes.append('second unit line of the same country')
                    if tail in DITTO or not tail:
                        unit=self.unit
                        if tail in DITTO: notes.append('unit from ditto')
                    else:
                        unit=tail.lstrip('{').strip()
                        if '{' in tail: notes.append('braced unit line')
                        # Reject a collapsed country list before it can poison
                        # every subsequent total's unit.
                        if not UNIT_END.fullmatch(unit) or LEADERS.search(unit) or re.search(r'["{}]|Br\.? Col|For\.? Coun',unit,re.I):
                            self.cur['unsafe']='collapsed article block or ambiguous units: unit contains country list, fragment, or unreadable brace'
                        self.unit=unit
                    if not country or re.search(r'\d|[{}]',country):
                        if '{' in c or '}' in c: self.cur['unsafe']='ambiguous braced units: country cannot be assigned'
                        self.skip(t,i,original,'country label not readable'); self.cur['skips']+=1; continue
                    # The separately printed United Kingdom line precedes the
                    # colony/foreign groups, and ends any pending group marker.
                    if country.strip(' .')=='United Kingdom': self.cg=''
                    self.last_country=country; self.last_cg=self.cg
                    self.pending_cg=''
                    if unit and unit not in self.total_units: self.total_units.append(unit)
                else:
                    country=clean(c) if c else ''
                    notes.append('unlabelled row of figures read as the article total' if not c else 'printed total')
                    if len(self.total_units)>1 and any('braced unit line' in z['notes'] for z in self.block):
                        n=sum(z['kind']=='article_total' for z in self.block)
                        if n<len(self.total_units): unit=self.total_units[n]
                    self.cur['closed']=True
                while len(figs)>len(measures) and not figs[-1]: figs=figs[:-1]
                component_header = [re.match(r'^(Kapok or Tree Cotton|Cotton for Spinning),\s*(.*)$', x) for x in figs[:2]]
                if len(component_header)==2 and all(component_header):
                    self.quantity_components=[m[1] for m in component_header]
                    figs=[m[2] for m in component_header]+figs[2:]
                if flow=='export' and name_key(self.article)=='tea':
                    values=self.tea_values(figs)
                    if values is None:
                        self.skip(t,i,original,'tea row fits no Black + Green + other = total reading'); self.cur['skips']+=1; continue
                else:
                    if len(figs)!=len(measures) or not all(num(x)[1] for x in figs):
                        self.skip(t,i,original,'figures beyond layout or a figure cell is not a plain number'); self.cur['skips']+=1
                        if deferred: self.label(deferred,t,i)
                        continue
                    values=[(measures[0] if self.quantity_components and j<2 else m,x,
                             'component '+self.quantity_components[j] if self.quantity_components and j<2 else '')
                            for j,(m,x) in enumerate(zip(measures,figs))]
                if kind=='country': self.cur['countries']+=1
                self.block.append(dict(t=t,i=i,raw=original,kind=kind,country=country,unit=unit,cg=self.cg,
                                       cl=self.cl,gr=self.gr,notes=notes,values=values))
                if deferred: self.label(deferred,t,i)
                if after_label: self.label(after_label,t,i)
        self.finish()
        return self


def write(path, fields, rows):
    if path.suffix == ".gz":
        with gzip.GzipFile(filename="", mode="wb", fileobj=path.open("wb"), mtime=0) as g, io.TextIOWrapper(g, encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(fields); w.writerows(rows)
    else:
        with path.open("w", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(fields); w.writerows(rows)


def main():
    years = sys.argv[1:] or YEARS_NEW
    readers = []
    corpus = {y: [json.loads(l) for l in gzip.open(BB / f"tables/{y}.jsonl.gz", "rt")] for y in YEARS_NEW}
    evidence = HeadingEvidence(corpus.values())
    for y in years:
        tables = [json.loads(l) for l in gzip.open(BB / f"tables/{y}.jsonl.gz", "rt")]
        readers.append((ModernReader(y, evidence) if y in YEARS_NEW else Reader(y)).read(tables))
    out = BB / "extracted"
    write(out / "trade_1880_1906.tsv.gz", FIELDS, (r for rd in readers for r in rd.rows))
    write(out / "trade_1880_1906_skipped.tsv", ["table_id", "row_index", "cells", "reason"], (r for rd in readers for r in rd.skipped))
    checks = []
    print("volume flow   figures  articles  with_total  all_agree")
    for rd in readers:
        for flow in ("import", "export"):
            arts = [a for a in rd.articles if a["flow"] == flow and a["countries"]]
            wt = [a for a in arts if a["totals"]]
            good = 0
            for a in wt:
                last = {}
                for entry in a["totals"]:
                    mname, v, tid, i, s = entry[:5]
                    unit = entry[5] if len(entry) > 5 else ""
                    last[mname, unit] = (v, tid, i, s)
                bad = [(mname, unit, v, tid, i, s) for (mname, unit), (v, tid, i, s) in last.items() if v != s]
                good += not bad
                for mname, unit, v, tid, i, s in bad:
                    checks.append((rd.year, flow, a["article"], a["start"], tid, i, mname, v, s, s - v, a["skips"], "; ".join(x for x in ["continued from an earlier page" if a["continued"] else "", "unit " + unit if unit else ""] if x)))
            n = sum(1 for r in rd.rows if r[4] == flow)
            if n: print(f"{rd.year:6} {flow:6} {n:8,} {len(arts):9,} {len(wt):10,} {good:9,}  {good / max(len(wt), 1):.1%}   skipped rows {sum(1 for s in rd.skipped)}")
    write(out / "trade_1880_1906_checks.tsv", ["year_volume", "flow", "article_as_printed", "article_start_table", "total_table_id", "total_row_index",
                                               "measure", "printed_total", "country_sum", "difference", "skipped_rows_in_article", "note"], checks)


if __name__ == "__main__":
    main()
