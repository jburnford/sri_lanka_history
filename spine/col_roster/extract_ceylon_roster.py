"""Ceylon's establishment lists in every Colonial Office List edition held in col_matching, as named entries.

The Colonial Office List prints, under each colony, its "Civil Establishment": office, holder, salary. col_matching
parsed those rosters for three pilot editions only; its biographies ("Record of Services") cover far fewer people.
This runs col_matching's own rules parser (col_match.volume.roster) over every edition up to 1948 and keeps the
entries it files under Ceylon. Nothing in col_matching is changed.

An entry is what the rules parser made of the OCR: it has not been corrected, and some entries are not people
(a sentence about railways can be read as a name). Each keeps its page, block and outline so it can be checked.

Output: col_roster/ceylon_roster.tsv        one row per entry
        col_roster/ceylon_roster_editions.tsv   entries per edition
"""
import csv, dataclasses, os, sys
from pathlib import Path
HERE = Path(__file__).parent
COLM = HERE.parent.parent / "col_matching"
sys.path.insert(0, str(COLM)); os.chdir(COLM)
from col_match.volume import bios as bios_mod, reader, roster

def main():
    rows, per = [], []
    for year in reader.available_years("col"):
        if year > 1948: continue
        try:
            blocks = reader.load_volume(year, "col")
            sec = bios_mod.find_services_section(blocks)
            records, stats = roster.extract_records(blocks, stop_at=sec[0] if sec else None)
        except Exception as e:
            per.append((year, "", "", f"failed: {type(e).__name__}: {e}"[:200])); print(year, "failed", e); continue
        cey = [r for r in records if "CEYLON" in (r.colony or "").upper()]
        per.append((year, len(records), len(cey), ""))
        print(year, len(records), len(cey), flush=True)
        for r in cey:
            d = r.to_json() if hasattr(r, "to_json") else dataclasses.asdict(r)
            pv = d.get("provenance") or {}
            rows.append((d.get("record_id"), year, d.get("colony"), d.get("department"), d.get("position"), d.get("name_raw"), d.get("surname"),
                         d.get("given_names"), " ".join(d.get("honours") or []), d.get("salary"), pv.get("page"), pv.get("block"),
                         " ".join(map(str, pv.get("bbox") or [])), (d.get("snippet") or "")[:300]))
    with open(HERE / "ceylon_roster.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["record_id", "edition_year", "colony_as_filed", "department", "position", "name_raw", "surname", "given_names", "honours", "salary", "page", "block", "bbox", "snippet"])
        w.writerows(rows)
    with open(HERE / "ceylon_roster_editions.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n"); w.writerow(["edition_year", "roster_entries_all_colonies", "ceylon_entries", "note"]); w.writerows(per)
    print(len(rows), "Ceylon entries")

if __name__ == "__main__":
    main()
