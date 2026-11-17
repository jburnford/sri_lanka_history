"""Parse the entries of Simon Casie Chitty, The Ceylon Gazetteer (Cotta Church Mission Press, 1834) from the
Internet Archive text of a later reprint (item in.ernet.dli.2015.94788), into one record per headword.
Kept: headword as printed, alternative spellings given in brackets, the kind of place from the first clause,
any "N miles <direction> of <place>" statements, the full entry text, and the line number in the source text.
This is the uncorrected archive OCR of the 1989 Navrang reprint. Ids are kept in gazetteer/casie_chitty_ids.tsv,
keyed on the source line, so an entry keeps its id when the parser changes.
Output gazetteer/casie_chitty_1834.jsonl
"""
import csv, json, re
from common import *
SRC = HERE / "sources/ceylon_gazetteer_ia/djvu.txt"
# A headword is one to four words (later words may be lower case: "Wallametty torre"); alternative spellings in
# brackets may come before or after the comma. HEAD2 is the other printed form, "Kandy. The name Kandy is ...".
HEAD = re.compile(r"^([A-Z][A-Za-z'’\-]+(?: [A-Za-z][A-Za-z'’\-]+){0,3})((?: ?\([^)]{2,80}\))*)\s*,-?\s*((?:\([^)]{2,80}\)\s*)?)(.*)$", re.S)
HEAD2 = re.compile(r"^([A-Z][A-Za-z'’\-]+(?: [A-Z][A-Za-z'’\-]+){0,2})((?: ?\([^)]{2,80}\))?)\.\s+((?:The|A|An|This) .*)$", re.S)
STRONG = r"(an? |the |one of |once |formerly |two |three )"
WEAK = r"-? ?(an? |the |one of |once |formerly |two |three |is |or |in the (?:province|district|parish|korle) |situated |so called )"
NOTHEAD = re.compile(r"^(Of|After|The|In|On|At|This|These|To|From|By|For|But|When|It|He|They|His|Their|Among|During|Besides|Except|Though|Although|While|Since|Here|There|Its|Some|Such|Both|Several|Many|Most|Every|Each|All|As|If|No|Not|One|With)( |$)|\b(of|the|this|and|in|to)\b")
KIND = re.compile(r"\b(village|town|city|river|district|province|korle|korale|pattoo|pattu|island|islet|fort|port|harbour|bay|lake|tank|"
                  r"gulf|mountain|hill|peak|point|cape|rock|station|post|parish|peninsula|canal|stream|ferry|pass|temple|hamlet|"
                  r"division|country|plain|forest|village|rest house|salt ?pans?|lagoon|promontory)\b", re.I)
DIST = re.compile(r"(\d+(?: \d)?(?:½|¼)?(?: and a half)?) miles? (?:to the )?((?:north|south|east|west)(?:[ -]?(?:north|south|east|west))?(?:[ -]?(?:north|south|east|west))?(?:ward)?(?: by (?:north|south|east|west))?) (?:of|from) (?:the )?(?:fort |town of |village of )?([A-Z][A-Za-z'\-]+(?: [A-Z][a-z]+)?)")
RUNHEAD = re.compile(r"^(\[?[A-Z]{3}\]?|\d+|The Ceylon Gazetteer|[A-Z]{3}\])$")

def main():
    lines = SRC.read_text().split("\n")
    # paragraphs with their starting line; running heads and page numbers dropped, pages joined
    paras, cur, start = [], [], None
    for i, l in enumerate(lines, 1):
        s = l.strip()
        if RUNHEAD.match(s): continue
        if not s:
            if cur: paras.append((start, " ".join(cur))); cur = []
            continue
        if not cur: start = i
        cur.append(s)
    if cur: paras.append((start, " ".join(cur)))
    end = next(i for i, (ln, p) in enumerate(paras) if p.startswith("A CORRECT OUTLINE"))   # appendices follow Yattinuwera
    begin = next(i for i, (ln, p) in enumerate(paras) if p.startswith("Adam's Berg,"))
    # candidates: (headword, alternative spellings, rest of the first clause, strong?)
    cand, ocr = {}, {}
    for i in range(begin, end):
        # "Maderegamuwe. a village" and "Allipoot (Allupotta.) a military post": a stop or nothing where the comma belongs
        raw = paras[i][1]; w = re.match(r"\S+", raw).group(0)
        fixed = re.sub(r"^ll", "Il", w.replace("//", "ll").replace("/", "l"))        # OCR: "Ga//e", "Ha/pe", "llpekadawe"
        raw = (fixed + raw[len(w):]).replace(" {", " (", 1) if fixed != w or re.match(r"\S+ \{[^)]{2,80}\)", raw) else raw
        if fixed != w: ocr[i] = w
        p = re.sub(r"^([A-Z][A-Za-z'’\-]+(?: [A-Z][a-z]+)?(?: \([^)]{2,80}\))?)(?:\. (?=[a-z])| (?=an? ))", r"\1, ", raw); m = HEAD.match(p)
        if m and len(m.group(1)) >= 3 and not NOTHEAD.search(m.group(1)):
            first = m.group(4)[:140]
            if not re.match(WEAK, first, re.I): continue
            strong = bool(KIND.search(first) and re.match(STRONG, first, re.I))
            cand[i] = (m.group(1), re.findall(r"\(([^)]+)\)", m.group(2) + m.group(3)), m.group(4), strong, "comma")
            continue
        m = HEAD2.match(p)
        if m and len(m.group(1)) >= 3 and not NOTHEAD.search(m.group(1)):
            head, alts = m.group(1), re.findall(r"\(([^)]+)\)", m.group(2))
            if alts and re.search(r" of$", alts[0]): head, alts = f"{head} ({alts[0]})", []        # "Calpentyn (Gulf of). This is ..."
            cand[i] = (head, alts, m.group(3), False, "stop")
    # the backbone: the longest run of strong candidates whose first letters never go backwards. One misread first
    # letter ("Resale" for Pesale) is then an outlier, and cannot pull the alphabet forward for the entries after it.
    strong = [i for i in sorted(cand) if cand[i][3]]
    best, prev = [1] * len(strong), [-1] * len(strong)
    for a in range(len(strong)):
        for b in range(a):
            if key(cand[strong[b]][0])[:1] <= key(cand[strong[a]][0])[:1] and best[b] + 1 > best[a]: best[a], prev[a] = best[b] + 1, b
    a = max(range(len(strong)), key=lambda x: best[x]); backbone = []
    while a >= 0: backbone.append(strong[a]); a = prev[a]
    backbone.sort(); bset = set(backbone); accept, notes = set(backbone), {}
    import bisect
    def neighbours(i):
        x = bisect.bisect_left(backbone, i)
        lo = backbone[x - 1] if x else None; hi = next((b for b in backbone[x:] if b != i), None)
        return (key(cand[lo][0]) if lo is not None else "a"), (key(cand[hi][0]) if hi is not None else "zz")
    for i, c in cand.items():
        if i in bset: continue
        lo, hi = neighbours(i); k = key(c[0])
        if c[3]:                                         # reads as an entry, but out of alphabetical order
            accept.add(i)
            notes[i] = f"out of alphabetical order (between {lo} and {hi}): the first letter is probably misread in this text"
        elif c[4] == "comma" and (lo[:2] <= k[:2] <= hi[:2] or                     # the book's order is not strict within a letter
                                  (lo[:1] == k[:1] == hi[:1] and not re.match(r"(is|or) ", c[2]))): accept.add(i)
        elif c[4] == "stop" and lo[:1] <= k[:1] <= hi[:1] and (c[0].isupper() or lo[:3] <= k[:3] <= hi[:3] or lo[:2] == k[:2]):
            accept.add(i)
    ids = {int(r["source_line"]): r["id"] for r in csv.DictReader(open(HERE / "gazetteer/casie_chitty_ids.tsv"), delimiter="\t")}   # ids stay with their entry
    nxt = max((int(v.split(":")[1]) for v in ids.values() if v.split(":")[1].isdigit()), default=0)
    ents = []
    for i in range(begin, end):
        ln, p = paras[i]
        if i in accept:
            head, alts, rest, st, form = cand[i]
            if ln not in ids: nxt += 1; ids[ln] = f"cc1834:{nxt:04d}"
            k = KIND.search(rest[:200])
            e = {"id": ids[ln], "headword": head, "key": key(head), "alt_spellings": alts,
                 "kind": k.group(1).lower() if k else None, "anchor": i in bset, "text": p, "source_line": ln}
            if i in notes: e["note"] = notes[i]
            if i in ocr: e["note"] = f"headword printed in this text as {ocr[i].rstrip(',')}"
            ents.append(e)
        elif ents:
            ents[-1]["text"] += "\n" + p               # continuation paragraph of the entry above
    with open(HERE / "gazetteer/casie_chitty_ids.tsv", "w") as fh:
        fh.write("source_line\tid\theadword\n")
        hw = {e["source_line"]: e["headword"] for e in ents}
        for ln in sorted(ids): fh.write(f"{ln}\t{ids[ln]}\t{hw.get(ln, '')}\n")
    for e in ents:
        e["distances"] = [{"miles": a, "direction": b.lower(), "from": c} for a, b, c in DIST.findall(e["text"][:1500])][:6]
        e["chars"] = len(e["text"])
        if e["chars"] > 15000 and e["key"] not in ("ceylon", "kandy", "kandyan provinces", "colombo"):
            e["note"] = (e.get("note", "") + "; " if e.get("note") else "") + "very long: may swallow an entry whose opening was not recognised"
    with open(HERE / "gazetteer/casie_chitty_1834.jsonl", "w") as fh:
        for e in ents: fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    import collections
    print("entries", len(ents), "with distances", sum(1 for e in ents if e["distances"]), "with alt spellings", sum(1 for e in ents if e["alt_spellings"]))
    print(collections.Counter(e["kind"] for e in ents).most_common(12))
    print(collections.Counter(e["headword"][0] for e in ents))

if __name__ == "__main__":
    main()
