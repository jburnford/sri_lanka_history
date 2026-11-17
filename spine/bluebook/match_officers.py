"""Match people named in the Blue Book Civil Establishment to Colonial Office List persons and to journal profiles.

A Blue Book name is "Surname, initials" (index) or "initials Surname" (returns). A candidate must share the
surname and have forenames whose initials agree letter for letter with the printed initials.
  Colonial Office List: the person must have a Ceylon posting starting no later than the volume year and be
     born 16-75 years before it. One candidate -> matched (high when a printed appointment year equals the
     start year of one of the person's Ceylon postings and at least two initials agree, otherwise medium).
     Several -> review.
  Journal profile: same surname and initials, profile active within 20 years of the volume. One -> candidate
     only (never asserted: the journal's profiles are themselves proposed groupings).
Output: bluebook/extracted/officer_matches.tsv   one row per Blue Book person-year
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
    # one Blue Book person per volume: merge index rows and establishment rows on (surname, initials)
    people = collections.OrderedDict()
    for r in tsv(BB / "extracted/officers_index.tsv"):
        k = (r["year_volume"], key(r["surname"]), inits(r["initials"]))
        p = people.setdefault(k, {"year": int(r["year_volume"]), "surname": r["surname"], "initials": r["initials"], "names": set(), "offices": [], "appt": set(), "tables": set()})
        p["names"].add(r["name_as_printed"]); p["offices"].append(r["office_as_printed"]); p["tables"].add(r["table_id"])
    for r in tsv(BB / "extracted/civil_establishment.tsv"):
        if not r["surname"]: continue
        k = (r["year_volume"], key(r["surname"]), inits(r["initials"]))
        p = people.setdefault(k, {"year": int(r["year_volume"]), "surname": r["surname"], "initials": r["initials"], "names": set(), "offices": [], "appt": set(), "tables": set()})
        p["names"].add(r["name_as_printed"]); p["tables"].add(r["table_id"])
        off = (r["department"] + ": " if r["department"] else "") + r["office_as_printed"]
        if not re.match(r"(do|ditto)\b", r["office_as_printed"], re.I): p["offices"].append(off)
        if r["appointment_year"]: p["appt"].add(int(r["appointment_year"]))
    rows, tally = [], collections.Counter()
    for (y, sk, ini), p in people.items():
        if not ini or len(sk) < 3: tally["no initials"] += 1; continue
        yr = p["year"]
        cands = []
        for c in col.get(sk, []):
            ci = inits(c["given_names"])
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
        tally["col:" + (status + ":" + conf if status else "none")] += 1
        if len(pc) == 1: tally["profile candidate"] += 1
        rows.append((f"bbp:{y}:{sk.replace(' ', '_')}:{ini}", y, p["surname"], p["initials"], " | ".join(sorted(p["names"]))[:200], " | ".join(dict.fromkeys(p["offices"]))[:400],
                     " ".join(map(str, sorted(p["appt"]))), status, conf, cid,
                     " | ".join(f'{c["id"]} {c["given_names"]} {c["surname"]} b.{c["birth_year"]}' for c, _, _ in cands)[:400],
                     pc[0]["id"] if len(pc) == 1 else "", " | ".join(f'{r["id"]} {r["name"]} ({r["articles"]})' for r in pc[:4]), " ".join(sorted(p["tables"]))[:300]))
    with open(BB / "extracted/officer_matches.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["bb_person", "year_volume", "surname", "initials", "names_as_printed", "offices_as_printed", "appointment_years",
            "col_status", "col_confidence", "col_person", "col_candidates", "journal_profile_candidate", "journal_profile_candidates", "tables"]); w.writerows(rows)
    print("blue book person-years:", len(rows), dict(tally))

if __name__ == "__main__":
    main()
