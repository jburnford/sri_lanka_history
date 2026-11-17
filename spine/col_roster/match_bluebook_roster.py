"""Match Blue Book official name groups to the Colonial Office List's Ceylon establishment entries of about the same year.

Both sources list office holders by name. A Blue Book volume for year Y is compared with the nearest Colonial Office
List edition dated Y-1 to Y+2 (an edition describes the establishment of roughly the year before it). A pair must
share the surname and have initials that agree letter for letter (or one a prefix of the other, with two or more
letters), and no full forename may disagree. A match is "unique" when one Blue Book group and one roster name
fit each other and nothing else; anything else is "ambiguous" and lists the alternatives.

These are name matches within one colony and about one year: good evidence, not proof, and unreviewed.

Output: col_roster/bluebook_roster_matches.tsv   one row per Blue Book group that has a candidate
        col_roster/roster_coverage.tsv           per edition: roster names, how many are found in the Blue Book
"""
import collections, csv, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from common import key
csv.field_size_limit(sys.maxsize)
NOT_NAME = re.compile(r"\d|\b(Inst|Sc|Edin|Lond|Cantab|Oxon|Hospital|Department|Office)\b|[()]", re.I)

def given(s):
    """Forename tokens, lower case; degrees and other non-name tokens (A.M.Inst.C.E., B.Sc., (Edin.)) dropped."""
    out = []
    for tok in re.split(r"\s+", (s or "").strip()):
        if NOT_NAME.search(tok) or tok.count(".") > 1: continue
        out += [w.lower() for w in re.findall(r"[A-Za-z]+", tok)]
    return out
def ini(g): return "".join(w[0] for w in g)
def fits(a, b):
    ia, ib = ini(a), ini(b)
    if not ia or not ib: return False
    if not (ia == ib or (len(ia) >= 2 and ib.startswith(ia)) or (len(ib) >= 2 and ia.startswith(ib))): return False
    return not any(len(x) >= 4 and len(y) >= 4 and not (x.startswith(y) or y.startswith(x)) for x, y in zip(a, b))

def main():
    ros = collections.defaultdict(lambda: collections.defaultdict(list))        # edition -> surname key -> entries
    for r in csv.DictReader(open(HERE / "ceylon_roster.tsv"), delimiter="\t"):
        sk, g = key(r["surname"]), given(r["given_names"])
        if len(sk) < 3 or not g or len(r["name_raw"]) > 45: continue
        ros[int(r["edition_year"])][sk].append((g, r))
    editions = sorted(ros)
    bb = collections.defaultdict(lambda: collections.defaultdict(list))         # volume year -> surname key -> groups
    for r in csv.DictReader(open(HERE.parent / "bluebook/extracted/officer_matches.tsv"), delimiter="\t"):
        g = r["bb_person"].split(":")[3].split("_")
        bb[int(r["year_volume"])][key(r["surname"])].append((g, r))
    rows, cover, tally = [], [], collections.Counter()
    for y in sorted(bb):
        near = sorted((e for e in editions if y - 1 <= e <= y + 2), key=lambda e: (abs(e - (y + 1)), e))
        if not near: tally["volumes with no edition near"] += 1; continue
        e = near[0]; found = set(); names = set()
        for sk, entries in ros[e].items():
            people = collections.defaultdict(list)                                # distinct roster names (an officer can hold two posts)
            for g, r in entries: people[" ".join(g)].append(r)
            names |= {(sk, n) for n in people}
            for g, r in bb[y].get(sk, []):
                cands = [n for n in people if fits(g, n.split())]
                if not cands: continue
                rivals = {n: [r2["bb_person"] for g2, r2 in bb[y][sk] if fits(g2, n.split())] for n in cands}
                unique = len(cands) == 1 and len(rivals[cands[0]]) == 1
                tally["unique" if unique else "ambiguous"] += 1
                for n in cands: found.add((sk, n))
                best = people[cands[0]]
                rows.append((r["bb_person"], y, r["names_as_printed"], r["offices_as_printed"][:200], e, "unique" if unique else "ambiguous",
                             " | ".join(f"{n} {sk}" for n in cands), " | ".join(x["record_id"] for n in cands for x in people[n])[:300],
                             " | ".join(dict.fromkeys((x["position"] or x["department"] or "") for x in best))[:200], best[0]["salary"],
                             r["col_status"], r["col_person"]))
        cover.append((y, e, len(names), len(found), f"{len(found) / max(len(names), 1):.0%}", sum(len(v) for v in bb[y].values())))
    with open(HERE / "bluebook_roster_matches.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["bb_person", "year_volume", "bb_names_as_printed", "bb_offices_as_printed", "col_edition", "match", "roster_names", "roster_record_ids",
                    "roster_office", "roster_salary", "biography_match_status", "biography_person"]); w.writerows(rows)
    with open(HERE / "roster_coverage.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["bluebook_year", "col_edition", "roster_names", "found_in_bluebook", "share", "bluebook_groups"]); w.writerows(cover)
    print(dict(tally)); print("roster names", sum(c[2] for c in cover), "found", sum(c[3] for c in cover))
    for c in cover: print(*c)
    both = sum(1 for r in rows if r[5] == "unique" and r[10] == "matched"); print("unique roster matches that also have a biography match:", both, "; unique without:", sum(1 for r in rows if r[5] == "unique" and r[10] != "matched"))

if __name__ == "__main__":
    main()
