"""Line up the 1834 Ceylon Gazetteer headwords with (a) names printed in the Tropical Agriculturist and
(b) Wikidata's Sri Lanka items. Exact normalised match first; then a spelling-tolerant match (1834 spellings
are archaic: Amblangodde = Ambalangoda), offered as candidates only, never as decisions.
Output analysis/casie_chitty_matches.tsv
"""
import csv, difflib, collections
from common import *

def skeleton(k):
    """Rough sound key for old romanisations: oo->u, ee->i, doubled letters single, final e/a/y dropped."""
    k = k.replace(" ", "")
    for a, b in (("oo", "u"), ("ee", "i"), ("ou", "u"), ("w", "v"), ("ck", "k"), ("c", "k"), ("y", "i"), ("ph", "p"), ("th", "t"), ("dh", "d"), ("aa", "a")):
        k = k.replace(a, b)
    k = re.sub(r"(.)\1", r"\1", k)
    return re.sub(r"[aeiou]+$", "", k)

def main():
    ents = read_jsonl(HERE / "gazetteer/casie_chitty_1834.jsonl")
    journal = {r["key"]: r for r in read_names("PLACE")}
    dec = {}
    for f in ("places_tier1", "places_tier1b", "places_tier2"):
        for d in read_jsonl(HERE / f"grounding/{f}.jsonl"): dec[d["key"]] = d
    wd_exact, wd_skel = collections.defaultdict(list), collections.defaultdict(list)
    for w in read_jsonl(HERE / "gazetteer/sri_lanka_wikidata.jsonl"):
        if w.get("missing"): continue
        for n in wd_names(w):
            wd_exact[n].append(w); wd_skel[skeleton(n)].append((n, w))
    jskel = collections.defaultdict(list)
    for k, r in journal.items(): jskel[skeleton(k)].append(k)
    rows, tally = [], collections.Counter()
    for e in ents:
        keys = [e["key"]] + [key(a) for a in e["alt_spellings"] if re.match(r"[A-Z]", a)]
        jx = [k for k in keys if k in journal]
        jf = sorted({k for kk in keys for k in jskel.get(skeleton(kk), []) if k not in jx}, key=lambda k: -journal[k]["articles"])[:3]
        wx = {w["qid"]: w for k in keys for w in wd_exact.get(k, [])}
        wf = {}
        if not wx:
            for kk in keys:
                for n, w in wd_skel.get(skeleton(kk), []):
                    if difflib.SequenceMatcher(None, kk, n).ratio() >= 0.75: wf[w["qid"]] = w
        d = dec.get(jx[0]) if jx else None
        cls = "wikidata_exact" if wx else "wikidata_spelling_candidate" if wf else "no_wikidata_candidate"
        tally[cls] += 1; tally["in_journal" if jx else "journal_spelling_candidate" if jf else "not_in_journal"] += 1
        fmt = lambda ws: " | ".join(f'{w["qid"]} {w.get("labels", {}).get("en", "")} ({(w.get("description") or "")[:40]})' for w in list(ws.values())[:4])
        rows.append((e["id"], e["headword"], "; ".join(e["alt_spellings"]), e["kind"] or "", "; ".join(f'{x["miles"]} mi {x["direction"]} of {x["from"]}' for x in e["distances"][:2]),
                     "; ".join(f'{k} ({journal[k]["articles"]})' for k in jx), "; ".join(f'{k} ({journal[k]["articles"]})' for k in jf),
                     (d or {}).get("status", ""), (d or {}).get("qid", ""), cls, fmt(wx), fmt(wf)))
    (HERE / "analysis").mkdir(exist_ok=True)
    with open(HERE / "analysis/casie_chitty_matches.tsv", "w", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t"); wr.writerow(["id", "headword", "alt_spellings", "kind", "distances", "journal_exact", "journal_spelling_candidates",
            "journal_decision", "journal_qid", "wikidata_class", "wikidata_exact", "wikidata_spelling_candidates"]); wr.writerows(rows)
    print(len(rows), dict(tally))

if __name__ == "__main__":
    main()
