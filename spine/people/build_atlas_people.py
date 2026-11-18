#!/usr/bin/env python3
"""Export people for the atlas's People view and People layer (docs/data/people/).

Three kinds of record, kept apart:
  o  officials: one name group per Blue Book volume (bluebook/extracted/officer_matches.tsv, 1863-1917)
  d  directory people: one role in one listing (directories/ferguson_1922/roles.jsonl)
  b  people named in K. M. de Silva, A History of Sri Lanka (desilva_people.json), linked to the book's pages

A record is placed on the map when its office title, department or listing names a place the gazetteer knows.
The place is "named in the office", which is usually but not always where the person worked. Nothing here says
that two records are the same person: records are grouped under a *printed-name key* (surname and initials as
printed), and the viewer says so.

Run from anywhere:  python spine/people/build_atlas_people.py   (standard library only)
"""
import collections
import csv
import gzip
import json
import re
import shutil
import unicodedata
from pathlib import Path

SPINE = Path(__file__).resolve().parents[1]
ROOT = SPINE.parent
ATLAS = ROOT / "docs" / "data"
OUT = ATLAS / "people"
HERE = Path(__file__).resolve().parent
csv.field_size_limit(10 ** 9)

HOCT_1922 = ("https://www.historyofceylontea.com/ceylon-publications/fergusons-directory/"
             "1922-fergusons-ceylon-directory/quick-view/index.php")
SETTLEMENT = re.compile(r"\b(village|town|city|suburb|settlement|municipal|neighbou?rhood|capital|hill station|port)\b", re.I)
# Words that are also place names in the gazetteer but in an office title nearly always mean something else.
STOP = set("""fort park mount point hospital central north south east west northern southern eastern western
union church college station office court police prison jail gaol customs harbour harbor bridge junction mills
estate garden gardens hill hills lake island islands bank market road street school government house hall
victoria albert wellington hope providence welcome union eden rose pearl temple palace model pioneer star
head first second third fourth chief senior junior assistant acting native english class grade division
adam adams king queen queens kings prince princes george charles william henry mary anne elizabeth
ceylon india england london madras bombay calcutta""".split())


def norm(text):
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def plain(text):
    """Accents removed, case and punctuation kept."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in text if not unicodedata.combining(c))


def slug(text):
    return norm(text).replace(" ", "-")


def read_tsv(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


# ---- gazetteer ------------------------------------------------------------------------------------------------

def build_gazetteer():
    """name (normalised) -> list of candidate places; each place: id, name, lat, lon, qid, basis."""
    places = {}       # id -> place
    names = collections.defaultdict(list)

    def add(place_id, name, lat, lon, qid, basis, rank, extra_names=()):
        if not (5.7 < lat < 10.0 and 79.3 < lon < 82.1):
            return
        place = places.setdefault(place_id, dict(id=place_id, name=name, lat=round(lat, 5), lon=round(lon, 5),
                                                 qid=qid or "", basis=basis, rank=rank))
        for value in (name, *extra_names):
            key = norm(value)
            if key and place not in names[key]:
                names[key].append(place)

    def layer(identifier):
        return json.loads((ATLAS / f"{identifier}.json").read_text())["features"]

    def point(feature):
        lon, lat = feature["geometry"]["coordinates"][:2]
        return lat, lon

    by_qid = {}

    def atlas_place(qid, name, lat, lon, basis, rank, extra=()):
        # One place per Wikidata item across the atlas layers; places with no item are keyed by name.
        place_id = by_qid.get(qid) if qid else None
        if not place_id:
            place_id = (qid or "n:" + slug(name))
            if qid:
                by_qid[qid] = place_id
        add(place_id, name, lat, lon, qid, basis, rank, extra)
        if place_id in places and places[place_id]["rank"] > rank:
            places[place_id].update(rank=rank, basis=basis)
        for value in (name, *extra):
            key = norm(value)
            if key and place_id in places and places[place_id] not in names[key]:
                names[key].append(places[place_id])

    for f in layer("urban_census"):
        p = f["properties"]
        name = p.get("anchor_name") or re.sub(r"\s+(Town|Municipality|Urban.*|Local Board.*)$", "", p["name"])
        atlas_place(p.get("qid"), name, *point(f), "census town", 0, [p["name"]])
    for f in layer("ferguson_towns_1893"):
        p = f["properties"]
        atlas_place(p.get("qid"), p["name"], *point(f), "town on Ferguson's 1893 map", 1)
    for f in layer("motor_amenity_places_1936"):
        p = f["properties"]
        atlas_place(p.get("qid"), p["place_as_printed"], *point(f), "place on the 1936 Motor Map lists", 2)
    for f in layer("gazetteer_1834_points"):
        p = f["properties"]
        if SETTLEMENT.search(p.get("category", "") + " " + p.get("location_scope", "")) or \
                p.get("category", "").lower() in ("town", "village", "fort", "district", "seaport", "port"):
            extra = [p["modern_name"]] if p.get("modern_name") else []
            atlas_place(p.get("qid"), p["historical_name"], *point(f), "entry in the 1834 Gazetteer", 3, extra)

    # Wikidata's Sri Lanka items, settlements only (chosen by their description, not by a list of class ids).
    for line in (SPINE / "gazetteer" / "sri_lanka_wikidata.jsonl").open(encoding="utf-8"):
        item = json.loads(line)
        if item.get("lat") is None or not SETTLEMENT.search(item.get("description") or ""):
            continue
        label = item.get("labels", {}).get("en")
        if not label:
            continue
        qid = item["qid"]
        aliases = item.get("aliases", {}).get("en", [])
        if qid in by_qid:
            atlas_place(qid, places[by_qid[qid]]["name"], places[by_qid[qid]]["lat"], places[by_qid[qid]]["lon"],
                        places[by_qid[qid]]["basis"], places[by_qid[qid]]["rank"], [label, *aliases])
            continue
        add(qid, label, float(item["lat"]), float(item["lon"]), qid, "Wikidata settlement", 5, aliases)
        if qid in places:
            places[qid]["sitelinks"] = item.get("sitelinks", 0)

    # Historical spellings: printed form -> a name the gazetteer already has. Reviewed by hand; see the file.
    aliases = []
    path = HERE / "place_spellings.tsv"
    if path.exists():
        for row in read_tsv(path):
            target = names.get(norm(row["gazetteer_name"]))
            if target:
                best = min(target, key=lambda p: (p["rank"], -p.get("sitelinks", 0)))
                names[norm(row["printed"])] = [best]
                aliases.append(row["printed"])
            else:
                print("place_spellings.tsv: no gazetteer place called", row["gazetteer_name"])
    return places, names


def make_matcher(names):
    longest = max(len(key.split()) for key in names)
    longest = min(longest, 3)

    def match(text):
        """Places named in a piece of office text: list of (place, how)."""
        words = norm(text).split()
        found, used = [], set()
        for size in range(longest, 0, -1):
            for start in range(0, len(words) - size + 1):
                if any(i in used for i in range(start, start + size)):
                    continue
                key = " ".join(words[start:start + size])
                if size == 1 and (key in STOP or len(key) < 4):
                    continue
                candidates = names.get(key)
                if not candidates:
                    continue
                best = min(candidates, key=lambda p: (p["rank"], -p.get("sitelinks", 0)))
                if best["rank"] >= 5 and len(candidates) > 1:
                    how = "one of %d Wikidata places of this name" % len(candidates)
                elif best["rank"] >= 5:
                    how = "Wikidata name"
                else:
                    how = best["basis"]
                found.append((best, how))
                used.update(range(start, start + size))
        seen, unique = set(), []
        for place, how in found:
            if place["id"] not in seen:
                seen.add(place["id"])
                unique.append((place, how))
        return unique
    return match


# ---- records --------------------------------------------------------------------------------------------------

TITLES = set("""the hon honble honourable sir mr mrs miss dr rev revd capt captain major col colonel lieut lt
his her excellency honor honour lady madame mlle esq kt knt bart governor lord earl viscount bishop monsignor
professor justice general admiral father fr ven venerable king queen prince""".split())


def name_key(surname, initials):
    """Printed-name key: surname, then the first letter of each given name or initial. Titles before the name
    and anything after a comma (post-nominals, ranks, notes) are left out, so "Stewart, The Hon. C. H., C.M.G."
    and "C. H. Stewart" share a key. Two people with the same initials share one too: it is not an identity."""
    given = str(initials or "").replace("'", "").split(",")[0]
    given = re.sub(r"\(.*?\)", " ", given)
    words = [w for w in re.sub(r"[^a-z ]", " ", norm(given)).split() if w not in TITLES]
    letters = "_".join(word[0] for word in words if word not in ("de", "van", "der", "la"))
    family = " ".join(w for w in norm(str(surname or "").replace("'", "")).split() if w not in TITLES)
    return (family.replace(" ", "-") or "unknown") + (":" + letters if letters else "")


COMPOUND = set()   # surnames of two or more words seen in "Surname, given" form, e.g. "casie chitty"


def split_printed(printed):
    """(surname, given) from one printed form, or None. Handles "Surname, Hon. Sir Given" and
    "The Hon. Sir Given Surname, K.C.M.G." alike; the upstream columns read the second form wrongly."""
    text = re.sub(r"\(.*?\)", " ", plain(printed)).replace("'", "")
    parts = [part.strip() for part in text.split(",")]
    head = [w for w in re.sub(r"[^A-Za-z ]", " ", parts[0]).split() if w.lower() not in TITLES]
    if not head:
        return None
    rest = parts[1] if len(parts) > 1 else ""
    lowered = [w.lower() for w in head]
    if len(head) == 1:
        return lowered[0], rest
    # Two or more words before the comma: a compound surname ("Casie Chitty, A") or given names followed by
    # post-nominals ("Hugh Clifford, K.C.M.G."). Only a surname already seen with several sets of initials counts.
    if len(parts) > 1 and (" ".join(lowered) in COMPOUND or (len(head) == 2 and lowered[0] in ("de", "van", "la"))):
        return " ".join(lowered), rest
    # given names first: leading initials, then either a known compound surname or the last word
    for size in (3, 2):
        if len(head) > size and " ".join(lowered[-size:]) in COMPOUND:
            return " ".join(lowered[-size:]), " ".join(head[:-size])
    if len(head) >= 3 and lowered[-2] in ("de", "van", "la"):
        return " ".join(lowered[-2:]), " ".join(head[:-2])
    return lowered[-1], " ".join(head[:-1])


def printed_key(printed_forms, surname, initials):
    keys = collections.Counter()
    for form in printed_forms:
        parsed = split_printed(form)
        if parsed and parsed[0]:
            keys[name_key(parsed[0], parsed[1])] += 1
    if keys:
        # prefer the fullest reading when the forms disagree (an index line often has fewer initials)
        return max(keys, key=lambda k: (keys[k], len(k)))
    return name_key(surname, initials)


def learn_compounds(rows):
    """Two- and three-word surnames. Evidence: printed before a comma with at least three different sets of
    initials, and also printed after bare initials ("C. N. M. Abdul Cader"). The second test keeps out given names
    followed by degrees ("Aldo Castellani, M.D.")."""
    before_comma, after_initials = collections.defaultdict(set), set()
    for row in rows:
        for form in row["names_as_printed"].split(" | "):
            parts = plain(form).replace("'", "").split(",")
            raw = re.sub(r"[^A-Za-z ]", " ", parts[0]).split()
            words = [w.lower() for w in raw if w.lower() not in TITLES]
            if len(parts) > 1 and 2 <= len(words) <= 3 and all(len(w) > 1 for w in words):
                before_comma[" ".join(words)].add(norm(parts[1]))
            lead = 0
            while lead < len(words) and len(words[lead]) == 1:
                lead += 1
            if lead and 2 <= len(words) - lead <= 3 and all(len(w) > 2 for w in words[lead:]):
                after_initials.add(" ".join(words[lead:]))
    COMPOUND.update(name for name, rests in before_comma.items()
                    if len(rests) >= 3 and (name in after_initials or len(rests) >= 8))


def officials(match, col_people):
    rows = read_tsv(SPINE / "bluebook" / "extracted" / "officer_matches.tsv")
    roster = {}
    path = SPINE / "col_roster" / "bluebook_roster_matches.tsv"
    if path.exists():
        for row in read_tsv(path):
            if row["match"] == "unique":
                roster[row["bb_person"]] = (row["col_edition"], row["roster_office"])
    learn_compounds(rows)
    for row in rows:
        printed = [value.strip() for value in row["names_as_printed"].split(" | ") if value.strip()]
        key = printed_key(printed, row["surname"], row["initials"])   # the same key as directory people
        display = min(printed, key=len) if printed else row["surname"]
        offices = [value.strip(" -") for value in row["offices_as_printed"].split(" | ") if value.strip(" -")]
        places = match(" ; ".join(offices))
        record = dict(k="o", key=key, name=display[:90], y=int(row["year_volume"][:4]),
                      office=" · ".join(offices)[:260], tables=row["tables"].split()[:3],
                      places=[(p["id"], how) for p, how in places])
        if row["col_person"]:
            person = col_people.get(row["col_person"], {})
            record["col"] = dict(id=row["col_person"], conf=row["col_confidence"],
                                 name=(person.get("given_names", "") + " " + person.get("surname", "")).strip(),
                                 born=person.get("birth_year", ""), qid=person.get("wikidata_qid", ""))
        if row["bb_person"] in roster:
            record["roster"] = dict(edition=roster[row["bb_person"]][0], office=roster[row["bb_person"]][1][:120])
        yield record


def directory(match):
    base = SPINE / "directories" / "ferguson_1922"
    listings = {}
    for line in (base / "listings.jsonl").open(encoding="utf-8"):
        item = json.loads(line)
        listings[item["listing_id"]] = item
    for line in (base / "roles.jsonl").open(encoding="utf-8"):
        role = json.loads(line)
        listing = listings[role["listing_id"]]
        section = listing["section"][:1]
        town = listing.get("town") or ""
        places = match(town)
        role_text = role.get("role_as_printed") or ""
        if role_text == "listed":
            role_text = ""
        year = role.get("year") or (listing.get("attested") if isinstance(listing.get("attested"), int) else None)
        flags = sorted(set(role.get("flags") or []) | set(listing.get("flags") or []))
        yield dict(k="d", key=printed_key([role["person_as_printed"]], role.get("surname") or "", role.get("given_or_initials") or ""),
                   name=role["person_as_printed"][:90], y=int(year) if year else 1921,
                   dated="year printed in the list" if year else "list corrected to December 1921" if section == "B"
                   else "1922 volume",
                   office=role_text[:120], firm=listing["name_as_printed"][:120],
                   address=(listing.get("address_as_printed") or "")[:160], town=town,
                   trades=", ".join((listing.get("trades") or [])[:4])[:120],
                   section=listing["section"][3:90], page=role["pdf_page"], ref=role["role_id"],
                   doubt="; ".join(v for v in ("OCR doubtful" if "ocr_doubtful" in flags else "",
                                               "page layout lost in OCR" if "structure_lost" in flags else "") if v),
                   places=[(p["id"], how) for p, how in places])


def book(match):
    """People in the timeline read from de Silva's History (desilva_people.json, made by import_desilva.py)."""
    path = HERE / "desilva_people.json"
    if not path.exists():
        return
    data = json.loads(path.read_text())
    for person in data["people"]:
        forms = [person["name"]] + [a for a in person["aliases"] if "(" not in a]
        key = printed_key(forms[:1], "", "")
        if ":" not in key:   # the main name is a bare surname or a title: an alias may carry the given names
            fuller = [printed_key([form], "", "") for form in forms[1:]]
            fuller = [k for k in fuller if ":" in k and k.split(":")[0] == key]
            if fuller:
                key = max(fuller, key=len)
        roles = []
        for role in person["roles"]:
            span = "–".join(v[:4] for v in (role["start"], role["end"]) if v)
            roles.append(", ".join(v for v in (role["title"], role["organization"]) if v) + (f" ({span})" if span else ""))
        text = " ; ".join([r["title"] for r in person["roles"]] + [pl["name"] + " ; " + pl["modern"] for pl in person["places"]])
        yield dict(k="b", key=key, name=person["name"][:90], y=person["first_year"], y2=person["last_year"],
                   office="; ".join(dict.fromkeys(roles))[:260], desc=person["description"][:320],
                   community=person["community"], born=str(person["born"])[:12], died=str(person["died"])[:12],
                   pages=person["pages"][:14], ref=person["id"],
                   places=[(p["id"], how) for p, how in match(text)])


def cross_references(by_key):
    """Printed names that could be a person in de Silva: same surname, compatible initials, dates within reach.
    Proposals for a reader to judge; nothing is merged on the strength of them."""
    by_surname = collections.defaultdict(list)
    for key in by_key:
        by_surname[key.split(":")[0]].append(key)
    proposals = []
    for key, items in by_key.items():
        for record in items:
            if record["k"] != "b" or ":" not in key or record["y2"] < 1850 or record["y"] > 1930:
                continue
            surname, initials = key.split(":")
            mine = initials.split("_")
            for other in by_surname[surname]:
                if other == key or ":" not in other:
                    continue
                theirs = other.split(":")[1].split("_")
                records = [r for r in by_key[other] if r["k"] in "od"]
                if not records:
                    continue
                short, long = sorted((mine, theirs), key=len)
                if long[:len(short)] != short:
                    continue
                first, last = min(r["y"] for r in records), max(r["y"] for r in records)
                if last < record["y"] - 25 or first > record["y2"] + 25:
                    continue
                proposals.append(dict(book_key=key, book=record, other=other, first=first, last=last, n=len(records),
                                      display=collections.Counter(r["name"] for r in records).most_common(1)[0][0],
                                      offices=[r["office"] for r in records if r["office"]][:3],
                                      grade="surname and first initials agree; the other name has more initials"))
    return proposals


def write(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if name.endswith(".gz"):
        with path.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as handle:
            handle.write(data)   # mtime=0: the same input gives the same bytes
    else:
        path.write_bytes(data)


def main():
    places, names = build_gazetteer()
    match = make_matcher(names)
    col_people = {row["id"]: row for row in read_tsv(SPINE / "graph" / "col_persons.tsv.gz")}
    records = list(officials(match, col_people)) + list(directory(match)) + list(book(match))

    shutil.rmtree(OUT, ignore_errors=True)
    by_place = collections.defaultdict(list)
    by_key = collections.defaultdict(list)
    how_used = collections.Counter()
    for record in records:
        by_key[record["key"]].append(record)
        for place_id, how in record["places"]:
            by_place[place_id].append(record)
            how_used[(place_id, how)] += 1

    # places with people
    place_rows = []
    for place_id, items in by_place.items():
        place = places[place_id]
        years = collections.Counter()
        for record in items:
            years[(record["k"], record["y"])] += 1
        hows = sorted({how for (pid, how) in how_used if pid == place_id})
        if not (years := years):
            continue
        file_id = slug(place_id)
        place_rows.append(dict(id=file_id, name=place["name"], lat=place["lat"], lon=place["lon"], qid=place["qid"],
                               basis="; ".join(hows), o=sum(1 for r in items if r["k"] == "o"),
                               d=sum(1 for r in items if r["k"] == "d"), b=sum(1 for r in items if r["k"] == "b"),
                               oy=sorted({y for (k, y) in years if k == "o"}),
                               years=[[k, y, n] for (k, y), n in sorted(years.items())]))
        rows = []
        for record in sorted(items, key=lambda r: (r["y"], norm(r["name"]))):
            if record["k"] == "o":
                rows.append(["o", record["y"], record["key"], record["name"], record["office"], record["tables"][:1]])
            elif record["k"] == "b":
                rows.append(["b", record["y"], record["key"], record["name"], record["office"] or record["desc"],
                             record["pages"][0] if record["pages"] else None])
            else:
                rows.append(["d", record["y"], record["key"], record["name"],
                             " — ".join(v for v in (record["office"], record["firm"], record["address"]) if v),
                             record["page"]])
        write(f"place/{file_id}.json.gz", rows)
    place_rows.sort(key=lambda r: -(r["o"] + r["d"]))
    write("places.json", place_rows)
    slug_of = {place_id: slug(place_id) for place_id in by_place}
    name_of = {slug(place_id): places[place_id]["name"] for place_id in by_place}

    # names: a light index for search, and the full entries in shards by the first two letters of the key
    proposals = cross_references(by_key)
    see_also = collections.defaultdict(list)
    per_person = collections.Counter(item["book_key"] for item in proposals)
    for item in proposals:
        if per_person[item["book_key"]] > 3:   # a common name: too many candidates to be worth showing; see the TSV
            continue
        book_record = item["book"]
        see_also[item["book_key"]].append(dict(k="x", key=item["other"], name=item["display"], y=item["first"],
                                               y2=item["last"], n=item["n"], note=item["grade"]))
        see_also[item["other"]].append(dict(k="x", key=item["book_key"], name=book_record["name"], y=book_record["y"],
                                            y2=book_record["y2"], n=1, book=True, note=item["grade"]))
    with (HERE / "desilva_match_proposals.tsv").open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle, delimiter="\t", lineterminator="\n")
        out.writerow(["desilva_id", "desilva_name", "desilva_years", "desilva_description", "printed_name_key",
                      "printed_name", "record_years", "records", "sample_offices", "basis", "decision"])
        for item in sorted(proposals, key=lambda i: (i["book"]["name"], i["other"])):
            b = item["book"]
            out.writerow([b["ref"], b["name"], f'{b["y"]}-{b["y2"]}', b["desc"], item["other"], item["display"],
                          f'{item["first"]}-{item["last"]}', item["n"], " | ".join(item["offices"])[:400], item["grade"], ""])
    index, shards = [], collections.defaultdict(dict)
    for key, items in by_key.items():
        items.sort(key=lambda r: (r["y"], r["k"]))
        display = collections.Counter(r["name"] for r in items).most_common(1)[0][0]
        kinds = "".join(sorted({r["k"] for r in items}))
        index.append([key, display, items[0]["y"], max(r.get("y2") or r["y"] for r in items), len(items), kinds])
        entries = []
        for record in items:
            entry = {k: v for k, v in record.items() if k not in ("key", "places") and v not in ("", None, [])}
            entry["places"] = [[slug_of[p], name_of[slug_of[p]], how] for p, how in record["places"]]
            entries.append(entry)
        entries.extend(see_also.get(key, []))
        shard = (re.sub(r"[^a-z]", "", key)[:2] or "zz").ljust(2, "_")
        shards[shard][key] = entries
    index.sort(key=lambda row: row[0])
    write("names.json.gz", index)
    for shard, entries in shards.items():
        write(f"names/{shard}.json.gz", entries)

    placed = collections.Counter(r["k"] for r in records if r["places"])
    total = collections.Counter(r["k"] for r in records)
    summary = dict(officials=total["o"], officials_placed=placed["o"], directory=total["d"],
                   directory_placed=placed["d"], book=total["b"], book_placed=placed["b"],
                   book_source=json.loads((HERE / "desilva_people.json").read_text())["source"] if total["b"] else None,
                   places=len(place_rows), names=len(index),
                   official_years=sorted({r["y"] for r in records if r["k"] == "o"}),
                   directory_source=HOCT_1922)
    write("summary.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "official_years"}, indent=1))

    # for review: which printed names carried the matches, and what place-like words found no place
    used = collections.Counter()
    for (place_id, how), n in how_used.items():
        used[(places[place_id]["name"], how)] += n
    with (HERE / "place_matches_review.tsv").open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle, delimiter="\t", lineterminator="\n")
        out.writerow(["place", "how_matched", "records"])
        for (name, how), n in used.most_common():
            out.writerow([name, how, n])
    tail = collections.Counter()
    for record in records:
        if record["k"] == "o" and not record["places"]:
            for found in re.findall(r"(?:,| at| of) ([A-Z][a-z]{3,}(?: [A-Z][a-z]{3,})?)\s*(?:$|[·|;])", record["office"]):
                tail[found] += 1
    with (HERE / "unplaced_office_endings.tsv").open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle, delimiter="\t", lineterminator="\n")
        out.writerow(["office_ending", "records_without_a_place"])
        for name, n in tail.most_common(600):
            out.writerow([name, n])


if __name__ == "__main__":
    main()
