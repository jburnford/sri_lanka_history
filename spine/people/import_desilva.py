#!/usr/bin/env python3
"""Make desilva_people.json: the people in the timeline read from K. M. de Silva, A History of Sri Lanka (1981).

The full timeline (events, evidence phrases, relations) is kept outside this repository. This takes only what the
atlas shows: a person's name and aliases, the offices and dates the book gives, a one-line description in our own
words, the places the book ties them to, and the pages. No wording from the book is copied.

  python spine/people/import_desilva.py /path/to/timeline/desilva_timeline.json
"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def year(value):
    found = re.match(r"-?\d+", str(value or ""))
    return int(found.group()) if found else None


def main():
    timeline = json.loads(Path(sys.argv[1]).read_text())
    active = collections.defaultdict(list)
    for event in timeline["events"]:
        for person in event["people"]:
            if year(event["date_start"]) is not None:
                active[person["id"]].append(year(event["date_start"]))
    place_names = {place["id"]: place for place in timeline["places"]}
    places = collections.defaultdict(list)
    for relation in timeline["relations"]:
        if relation["object"] in place_names and relation["predicate"] in ("official_of", "governor_of", "ruler_of",
                                                                           "located_in", "headquartered_in"):
            place = place_names[relation["object"]]
            entry = dict(name=place["name"], modern=place.get("modern_name") or "", relation=relation["predicate"],
                         start=relation.get("start") or "", end=relation.get("end") or "",
                         note=(relation.get("note") or "")[:120])
            if entry not in places[relation["subject"]]:
                places[relation["subject"]].append(entry)
    people = []
    for person in timeline["people"]:
        years = list(active[person["id"]])
        for role in person.get("roles", []):
            years += [y for y in (year(role.get("start")), year(role.get("end"))) if y is not None]
        pages = sorted({(c["pdf_page"], str(c.get("printed_page") or "")) for c in person["citations"]})
        people.append(dict(
            id=person["id"], name=person["name"], aliases=person.get("aliases") or [],
            description=person.get("description") or "", community=person.get("community") or "",
            born=person.get("born") or "", died=person.get("died") or "",
            roles=[dict(title=r.get("title") or "", organization=r.get("organization") or "",
                        start=r.get("start") or "", end=r.get("end") or "") for r in person.get("roles", [])],
            first_year=min(years) if years else None, last_year=max(years) if years else None,
            places=places.get(person["id"], []), pages=[list(page) for page in pages]))
    source = timeline["source"]
    out = dict(source=dict(id=source["id"], author=source["author"], title=source["title"], year=source["year"],
                           publisher=source["publisher"],
                           pdf="https://archive.org/download/bub_gb_dByI_qil26YC/bub_gb_dByI_qil26YC.pdf",
                           item="https://archive.org/details/bub_gb_dByI_qil26YC"),
               note="Read chapter by chapter by Claude from the scan's OCR; years, figures and doubtful readings were "
                    "cross-checked against a second OCR. Descriptions are summaries, not quotations.",
               people=people)
    (HERE / "desilva_people.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(len(people), "people;", sum(1 for p in people if p["places"]), "with a place;",
          sum(1 for p in people if p["first_year"] is not None), "dated")


if __name__ == "__main__":
    main()
