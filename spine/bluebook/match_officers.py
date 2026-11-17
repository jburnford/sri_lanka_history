"""Match people named in the Blue Book Civil Establishment to Colonial Office List persons and to journal profiles.

A Blue Book name is "Surname, initials" (index) or "initials Surname" (returns). A candidate must share the
surname and have forenames whose initials agree letter for letter with the printed initials.
  Colonial Office List: the person must have a Ceylon posting starting no later than the volume year and be
     born 16-75 years before it. One candidate -> matched (high when a printed appointment year equals the
     start year of one of the person's Ceylon postings and at least two initials agree, otherwise medium).
     Several -> review.
  Journal profile: same surname and initials, profile active within 20 years of the volume. One -> candidate
     only (never asserted: the journal's profiles are themselves proposed groupings).
Output: bluebook/extracted/officer_matches.tsv   one row per name group in a volume (surname + given names as printed).
        A group is a proposal that its entries are one person; it is not a count of people.
"""
import collections, csv, gzip, re, sys
from pathlib import Path
BB = Path(__file__).parent
sys.path.insert(0, str(BB.parent))
from common import *
csv.field_size_limit(sys.maxsize)

def inits(s):
    return "".join(w[0] for w in re.findall(r"[A-Za-z]+", s or "")).upper()

def tsv(p):
    op = gzip.open if str(p).endswith(".gz") else open
    with op(p, "rt", newline="") as fh: return list(csv.DictReader(fh, delimiter="\t"))

def main():
    col = collections.defaultdict(list)
    posts = collections.defaultdict(list)
    for r in tsv(HERE / "graph/postings.tsv.gz"):
        if r["start"]: posts[r["person"]].append((int(r["start"]), r["colony_label"], r["position"]))
    for r in tsv(HERE / "graph/col_persons.tsv.gz"):
        col[key(r["surname"])].append(r)
    prof = collections.defaultdict(list)
    for r in tsv(HERE / "graph/profiles.tsv.gz"):
        if r["kind"] != "named": continue
        w = r["name"].replace(",", " ").split()
        if len(w) < 2: continue
        prof[key(w[-1])].append((inits(" ".join(w[:-1])), r))
    # Entries are grouped within a volume on surname and the given names exactly as printed ("John", "J", "J W"), never on
    # initials alone: John, Joseph and Jerome Perera are three groups. An initials-only form ("Perera, J.") is joined to
    # a fuller form only when exactly one fuller form in that volume and surname has those initials; otherwise it stays
    # apart and is flagged. The grouping is a proposal, recorded in the "grouping" column; the entries themselves are
    # the rows of officers_index.tsv and civil_establishment.tsv.
    def given(s): return " ".join(w.lower() for w in re.findall(r"[A-Za-z]+", s or ""))
    def blank(r): return {"year": int(r["year_volume"]), "surname": r["surname"], "initials": r["initials"], "names": set(), "offices": [], "appt": set(), "tables": set(), "entries": 0}
    people = collections.OrderedDict()
    for r in tsv(BB / "extracted/officers_index.tsv"):
        k = (r["year_volume"], key(r["surname"]), given(r["initials"]))
        p = people.setdefault(k, blank(r)); p["entries"] += 1
        p["names"].add(r["name_as_printed"]); p["offices"].append(r["office_as_printed"]); p["tables"].add(r["table_id"])
    for r in tsv(BB / "extracted/civil_establishment.tsv"):
        if not r["surname"]: continue
        k = (r["year_volume"], key(r["surname"]), given(r["initials"]))
        p = people.setdefault(k, blank(r)); p["entries"] += 1
        p["names"].add(r["name_as_printed"]); p["tables"].add(r["table_id"])
        off = (r["department"] + ": " if r["department"] else "") + r["office_as_printed"]
        if not re.match(r"(do|ditto)\b", r["office_as_printed"], re.I): p["offices"].append(off)
        if r["appointment_year"]: p["appt"].add(int(r["appointment_year"]))
    fam = collections.defaultdict(list)
    for (y, sk, g) in people: fam[(y, sk)].append(g)
    for (y, sk), gs in fam.items():
        full = [g for g in gs if any(len(w) > 1 for w in g.split())]
        for g in gs:
            p = people.get((y, sk, g))
            if p is None: continue
            p.setdefault("grouping", "one printed form")
            if not g or any(len(w) > 1 for w in g.split()): continue
            same = [f for f in full if "".join(w[0] for w in f.split()) == g.replace(" ", "")]
            if len(same) == 1:
                q = people[(y, sk, same[0])]
                for f_ in ("names", "appt", "tables"): q[f_] |= p[f_]
                q["offices"] += p["offices"]; q["entries"] += p["entries"]
                q["grouping"] = "initials joined to the only fuller name with them in this volume"
                del people[(y, sk, g)]
            elif len(same) > 1:
                p["grouping"] = f"initials shared by {len(same)} fuller names in this volume: not joined to any"
    for (y, sk, g), p in people.items():
        if len(p["names"]) > 1 and p["grouping"] == "one printed form": p["grouping"] = "same given names in index and returns"
    def clash(printed, col_given):
        """A printed full forename that disagrees with the candidate's forename in the same position (John v. James)."""
        a, b = printed.split(), given(col_given).split()
        for x, y_ in zip(a, b):
            if len(x) >= 4 and len(y_) >= 4 and not (x.startswith(y_) or y_.startswith(x)): return True
        return False
    rows, tally = [], collections.Counter()
    for (y, sk, g), p in people.items():
        ini = "".join(w[0] for w in g.split()).upper()
        if not ini or len(sk) < 3: tally["no initials"] += 1; continue
        yr = p["year"]
        cands = []
        for c in col.get(sk, []):
            ci = inits(c["given_names"])
            if clash(g, c["given_names"]): continue
            if not (ci == ini or (len(ini) >= 2 and ci.startswith(ini)) or (len(ci) >= 2 and ini.startswith(ci))): continue
            ps = [x for x in posts.get(c["id"], []) if x[1] == "Ceylon" and x[0] <= yr]
            by = int(c["birth_year"]) if c["birth_year"].isdigit() else None
            if not ps or (by and not 16 <= yr - by <= 75): continue
            # the printed appointment year must equal the start of a Ceylon posting, not a posting anywhere
            cands.append((c, ci == ini, bool(p["appt"] & {x[0] for x in posts[c["id"]] if x[1] == "Ceylon"})))
        pc = [r for i, r in prof.get(sk, []) if i == ini and r["first"] and int(r["first"]) - 20 <= yr <= int(r["last"]) + 20]
        status, conf, cid = "", "", ""
        if len(cands) == 1:
            c, exact, appt = cands[0]; status = "matched"; conf = "high" if appt and exact else "medium" if exact or appt else "low"; cid = c["id"]
            if conf == "high" and len(ini) < 2: conf = "medium"          # surname + one initial is too thin for "high"
        elif len(cands) > 1:
            best = [c for c in cands if c[1] and c[2]]
            if len(best) == 1: status, conf, cid = "matched", "medium", best[0][0]["id"]
            else: status = "review"
        if len(pc) == 1: tally["profile candidate"] += 1
        if p["grouping"].startswith("initials shared") and status == "matched": conf = "low"      # the printed form does not say which of several men
        tally["col:" + (status + ":" + conf if status else "none")] += 1
        rows.append((f"bbp:{y}:{sk.replace(' ', '_')}:{g.replace(' ', '_')}", y, p["surname"], p["initials"], " | ".join(sorted(p["names"]))[:200], " | ".join(dict.fromkeys(p["offices"]))[:400],
                     " ".join(map(str, sorted(p["appt"]))), status, conf, cid,
                     " | ".join(f'{c["id"]} {c["given_names"]} {c["surname"]} b.{c["birth_year"]}' for c, _, _ in cands)[:400],
                     pc[0]["id"] if len(pc) == 1 else "", " | ".join(f'{r["id"]} {r["name"]} ({r["articles"]})' for r in pc[:4]), " ".join(sorted(p["tables"]))[:300], p["entries"], p["grouping"]))
    with open(BB / "extracted/officer_matches.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["bb_person", "year_volume", "surname", "initials", "names_as_printed", "offices_as_printed", "appointment_years",
            "col_status", "col_confidence", "col_person", "col_candidates", "journal_profile_candidate", "journal_profile_candidates", "tables", "entries", "grouping"]); w.writerows(rows)
    print("blue book name groups (volume, surname, given names as printed):", len(rows), dict(tally))

if __name__ == "__main__":
    main()
