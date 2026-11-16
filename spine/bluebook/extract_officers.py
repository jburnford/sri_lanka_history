"""Ceylon Blue Books: the people named in the Civil Establishment.

Two printed sources per volume (1869, 1889, 1902, 1904 so far; later volumes do not print them):
  LIST OF OFFICERS        alphabetical index: name, office, page          -> extracted/officers_index.tsv
  the establishment returns: office, name, date of appointment, by whom
                             appointed, salary ..., under department heads -> extracted/civil_establishment.tsv
Everything is kept as printed; `surname`/`initials` are parsed helpers for matching, not corrections.
"""
import csv, glob, gzip, json, re, sys, collections
from pathlib import Path
BB = Path(__file__).parent
sys.path.insert(0, str(BB.parent))
from common import key
DOTS = re.compile(r"[\s.…·\-–—]*$")
clean = lambda s: DOTS.sub("", re.sub(r"\s*\.\s*\.[ .]*", " ", s or "")).strip()

def split_name(n):
    """'Abayaratna, D. J., Mudaliyar' or 'W. J. Stork' -> (surname, initials/forenames, rest)."""
    n = clean(n)
    n = re.sub(r"^(Hon\.|The Hon\.|Hon'ble|Sir|Dr\.|Rev\.|Mr\.|Capt\.|Major|Lieut\.|Col\.|His Excellency)\s+", "", n)
    if "," in n:
        p = [x.strip() for x in n.split(",")]
        return p[0], p[1] if len(p) > 1 else "", ", ".join(p[2:])
    m = re.match(r"^((?:[A-Z]\.\s*)+|(?:[A-Z][a-z]+\s+)+?)((?:de |van |von |d')?[A-Z][A-Za-z'\-]+(?: [A-Z][a-z]+)?)(?:,?\s*(.*))?$", n)
    if m: return m.group(2).strip(), m.group(1).strip(), (m.group(3) or "").strip()
    return n, "", ""

def main():
    idx, est = [], []
    for f in sorted(glob.glob(str(BB / "tables/*.jsonl.gz"))):
        dept = sub = None
        for line in gzip.open(f, "rt"):
            t = json.loads(line)
            if not t["rows"]: continue
            h = [c.lower() for c in t["rows"][0]]
            hs = " ".join(h)
            # ---- index: Name | Office | Page
            if t["n_cols"] in (3, 4) and re.search(r"names? of officers?|^name", h[0]) and "office" in hs and "page" in hs:
                for ri, r in enumerate(t["rows"][1:], 1):
                    name, office, page = clean(r[0]), clean(r[1]), clean(r[-1])
                    if not name or name.lower().startswith("name") or not re.match(r"[A-Z]", name): continue
                    s, i, rest = split_name(name)
                    idx.append((t["id"], t["year"], t["pdf_page"], ri, name, office, page, s, i, rest))
            # ---- establishment: Office | Name | Date of Appointment | By whom ... | Salary ...
            elif t["n_cols"] >= 5 and h[0].startswith("office") and h[1].startswith("name") and "appointment" in h[2]:
                sal = next((i for i, c in enumerate(h) if "salary" in c), None)
                for ri, r in enumerate(t["rows"][1:], 1):
                    if len(set(r)) == 1 and r[0]:                    # a heading that spans the table
                        txt = re.sub(r"[\s.—\-]*(contd|continued|cont)\.?$", "", clean(r[0]), flags=re.I).strip(" .—-")
                        if txt.isupper() or dept is None: 
                            if re.search(r"PROVINCE", txt) and dept: sub = txt
                            else: dept, sub = txt, None
                        else: sub = txt
                        continue
                    office, name, date = clean(r[0]), clean(r[1]), clean(r[2])
                    if office.lower().startswith("office") or not (office or name): continue
                    if not re.search(r"[A-Za-z]{2}", name): name = ""
                    s, i, rest = split_name(name) if name else ("", "", "")
                    ym = re.search(r"(1[789]\d\d|190\d)", date)
                    est.append((t["id"], t["year"], t["pdf_page"], t["printed_page"] or "", ri, dept or "", sub or "", office, name, date, ym.group(1) if ym else "",
                                clean(r[3]) if len(r) > 3 else "", " ".join(clean(c) for c in r[sal:sal + 3]) if sal is not None else "", s, i))
    (BB / "extracted").mkdir(exist_ok=True)
    with open(BB / "extracted/officers_index.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["table_id", "year_volume", "pdf_page", "row", "name_as_printed", "office_as_printed", "page_ref", "surname", "initials", "rest"]); w.writerows(idx)
    with open(BB / "extracted/civil_establishment.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["table_id", "year_volume", "pdf_page", "printed_page", "row", "department", "subdivision", "office_as_printed", "name_as_printed",
                    "date_of_appointment_as_printed", "appointment_year", "appointed_by_as_printed", "salary_cells_as_printed", "surname", "initials"]); w.writerows(est)
    for nm, rows, yi in (("officers_index", idx, 1), ("civil_establishment", est, 1)):
        print(nm, len(rows), dict(sorted(collections.Counter(r[yi] for r in rows).items())))
    print("establishment rows with a name:", sum(1 for r in est if r[8]), "| departments:", len({r[5] for r in est}))
    print(collections.Counter(r[5] for r in est).most_common(25))

if __name__ == "__main__":
    main()
