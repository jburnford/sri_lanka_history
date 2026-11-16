"""Parse the entries of Simon Casie Chitty, The Ceylon Gazetteer (Cotta Church Mission Press, 1834) from the
Internet Archive text of a later reprint (item in.ernet.dli.2015.94788), into one record per headword.
Kept: headword as printed, alternative spellings given in brackets, the kind of place from the first clause,
any "N miles <direction> of <place>" statements, the full entry text, and the line number in the source text.
This is the uncorrected archive OCR; a fresh OCR run is in progress and should replace it.
Output gazetteer/casie_chitty_1834.jsonl
"""
import json, re
from common import *
SRC = HERE / "sources/ceylon_gazetteer_ia/djvu.txt"
HEAD = re.compile(r"^([A-Z][A-Za-z'’\-]+(?: [A-Z][A-Za-z'’\-]+){0,3})((?: ?\([^)]{2,80}\))*)\s*,\s+(.*)$", re.S)
KIND = re.compile(r"\b(village|town|city|river|district|province|korle|korale|pattoo|pattu|island|islet|fort|port|harbour|bay|lake|tank|"
                  r"mountain|hill|peak|point|cape|rock|station|post|parish|peninsula|canal|stream|ferry|pass|temple|hamlet|"
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
    # pass 1: anchors, entries that open by naming a kind of place and keep alphabetical order
    cand, anchors, last = {}, [], None
    for i, (ln, p) in enumerate(paras):
        m = HEAD.match(p)
        if not m or len(m.group(1)) < 3: continue
        first = m.group(3)[:140]
        if not re.match(r"(an? |the |one of |once |formerly |is |or )", first, re.I): continue
        cand[i] = m
        c = key(m.group(1))[:1]
        if KIND.search(first) and re.match(r"(an? |the |one of |once |formerly )", first, re.I) and (last is None or 0 <= ord(c) - ord(last[:1]) <= 3):
            anchors.append(i); last = key(m.group(1))
    # pass 2: other candidates ("Kandy, the capital of ...") count when they sit in order between two anchors
    aset, accept = set(anchors), set(anchors)
    for i, m in cand.items():
        if i in aset: continue
        prev = max((a for a in anchors if a < i), default=None); nxt = min((a for a in anchors if a > i), default=None)
        if prev is None or nxt is None: continue
        k2, lo, hi = key(m.group(1))[:2], key(cand[prev].group(1))[:2], key(cand[nxt].group(1))[:2]
        if lo <= k2 <= hi: accept.add(i)
    ents = []
    for i, (ln, p) in enumerate(paras):
        if p.startswith("A CORRECT OUTLINE"): break     # the appendices follow the last entry (Yattinuwera)
        if i in accept:
            m = cand[i]; head = m.group(1); alts = re.findall(r"\(([^)]+)\)", m.group(2) or "")
            k = KIND.search(m.group(3)[:200])
            ents.append({"id": f"cc1834:{len(ents)+1:04d}", "headword": head, "key": key(head), "alt_spellings": alts,
                         "kind": k.group(1).lower() if k else None, "anchor": i in aset, "text": p, "source_line": ln})
        elif ents:
            ents[-1]["text"] += "\n" + p               # continuation paragraph of the entry above
    for e in ents:
        e["distances"] = [{"miles": a, "direction": b.lower(), "from": c} for a, b, c in DIST.findall(e["text"][:1500])][:6]
        e["chars"] = len(e["text"])
        if e["chars"] > 10000: e["note"] = "very long: probably swallows a major entry (Ceylon, Kandy, Trincomalee...) whose opening was not recognised"
    with open(HERE / "gazetteer/casie_chitty_1834.jsonl", "w") as fh:
        for e in ents: fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    import collections
    print("entries", len(ents), "with distances", sum(1 for e in ents if e["distances"]), "with alt spellings", sum(1 for e in ents if e["alt_spellings"]))
    print(collections.Counter(e["kind"] for e in ents).most_common(12))
    print(collections.Counter(e["headword"][0] for e in ents))

if __name__ == "__main__":
    main()
