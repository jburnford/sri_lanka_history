#!/usr/bin/env python3
"""Export the parsed Blue Book tables for the atlas's Blue Book view (docs/data/bluebook/).

Reads only committed files in this folder; writes nothing here. Output, all gzip-compressed JSON except volumes.json:

  volumes.json             one entry per volume: key, year, archive.org item, table count per confidence level
  index.json.gz            one short row per table (page, section, headings, size, level, totals, counts of
                           extracted figures and officers), for searching by year, section and heading text
  labels.json.gz           row and column labels -> tables that print them (delta-encoded positions in the index)
  vol/<key>.json.gz        the tables of one volume in full: cells, headings, confidence details
  extracted/<key>.json.gz  figures (observations.tsv.gz) and officer names (extracted/officers_index.tsv,
                           extracted/civil_establishment.tsv) drawn from each table of one volume
  acreage.json             acreage by crop (observations of kind agriculture:acreage_by_crop) for the series chart

The browser decompresses the .gz files itself (DecompressionStream), so they are served as plain files.
Run:  python3 spine/bluebook/export_viewer.py
"""
import collections, csv, gzip, json, re, sys
from pathlib import Path

BB = Path(__file__).resolve().parent
OUT = BB.parents[1] / "docs" / "data" / "bluebook"
LEVELS = ["summed", "two_readings", "partly", "unconfirmed", "suspect"]
ID = re.compile(r"^bb(\w+):p(\d+):t(\d+)$")
NUMERIC = re.compile(r"^[\W\d½¼¾]*$")
csv.field_size_limit(sys.maxsize)


def dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def write(name, value, compress=True):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = dump(value).encode()
    path.write_bytes(gzip.compress(data, 9, mtime=0) if compress else data)
    return path.stat().st_size


def tsv(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh, delimiter="\t")


def clean_label(cell):
    """A printed label as it will be searched: leader dots and stray punctuation removed, case kept."""
    c = re.sub(r"(\s*\.\s*){2,}|…+", " ", cell).strip(" .,:;-—–\"'*")
    return re.sub(r"\s+", " ", c)


def intval(x):
    try: return int(x)
    except (TypeError, ValueError): return 0


def main():
    volumes = [v for v in tsv(BB / "volumes.tsv") if v.get("key") != "skip"]
    for v in volumes: v["key"] = v.get("key") or v["year"]
    vindex = {v["key"]: i for i, v in enumerate(volumes)}

    conf = {r["table_id"]: r for r in tsv(BB / "table_confidence.tsv.gz")}

    obs = collections.defaultdict(list)
    kinds = []
    for r in tsv(BB / "observations.tsv.gz"):
        if r["kind"] not in kinds: kinds.append(r["kind"])
        m = re.search(r"source row (\d+)(?:, column (\d+))?", r["note"] or "")
        obs[r["table"]].append([kinds.index(r["kind"]), r["year_data"], r["area_as_printed"], r["parent_as_printed"],
                                r["measure_as_printed"], r["unit_as_printed"], r["value_as_printed"], r["value"],
                                int(m.group(1)) if m else -1, int(m.group(2)) if m and m.group(2) else -1,
                                r["note"], r["area_key"], r["measure_key"]])
    index_people = collections.defaultdict(list)
    for r in tsv(BB / "extracted/officers_index.tsv"):
        index_people[r["table_id"]].append([intval(r["row"]), r["name_as_printed"], r["office_as_printed"], r["page_ref"]])
    establishment = collections.defaultdict(list)
    for r in tsv(BB / "extracted/civil_establishment.tsv"):
        establishment[r["table_id"]].append([intval(r["row"]), r["name_as_printed"], r["office_as_printed"], r["department"],
                                             r["subdivision"], r["date_of_appointment_as_printed"], r["salary_cells_as_printed"]])

    sections, section_ids = [], {}
    index, labels = [], {"r": collections.defaultdict(list), "c": collections.defaultdict(list)}
    sizes = collections.Counter()
    meta = []
    for v in volumes:
        key = v["key"]
        counts = collections.Counter()
        vol, extracted = {}, {"kinds": kinds, "obs": {}, "officers": {}, "establishment": {}}
        n_pages = sum(1 for _ in gzip.open(BB / "pages" / f"{key}.jsonl.gz", "rt"))
        for line in gzip.open(BB / "tables" / f"{key}.jsonl.gz", "rt"):
            t = json.loads(line)
            m = ID.match(t["id"])
            assert m and m.group(1) == key and int(m.group(2)) == t["pdf_page"], t["id"]
            short = f"p{m.group(2)}:t{m.group(3)}"
            c = conf.get(t["id"], {})
            level = c.get("level") or "unconfirmed"
            counts[level] += 1
            section = (t.get("section") or "").strip()
            if section and section not in section_ids:
                section_ids[section] = len(sections); sections.append(section)
            n_obs, n_off = len(obs.get(t["id"], [])), len(index_people.get(t["id"], [])) + len(establishment.get(t["id"], []))
            pos = len(index)
            index.append([vindex[key], t["pdf_page"], int(m.group(3)), t.get("printed_page") or "",
                          section_ids.get(section, -1), " | ".join(h.strip() for h in t.get("headings") or []),
                          t["n_rows"], t["n_cols"], LEVELS.index(level), intval(c.get("totals_checked")),
                          intval(c.get("totals_agree")), n_obs, n_off])
            vol[short] = {
                "headings": t.get("headings") or [], "header_rows": t.get("header_rows") or 0, "rows": t["rows"],
                "confidence": {k: c.get(k, "") for k in ("level", "totals_checked", "totals_agree", "off_by_one_digit", "differ",
                               "numbers_confirmed_by_totals", "numbers_3plus_digits", "also_in_second_reading",
                               "share_in_second_reading", "flags", "disagreements", "nontrivial_totals_agree",
                               "running_subtotals_agree", "distinct_numbers_3plus")},
            }
            if t["id"] in obs: extracted["obs"][short] = obs[t["id"]]
            if t["id"] in index_people: extracted["officers"][short] = index_people[t["id"]]
            if t["id"] in establishment: extracted["establishment"][short] = establishment[t["id"]]
            # labels: every text cell in the header rows (column labels) and in the first column below them (row labels)
            hr = max(t.get("header_rows") or 0, 1)
            seen = {"r": set(), "c": set()}
            for i, row in enumerate(t["rows"]):
                for j, cell in enumerate(row if i < hr else row[:1]):
                    lab = clean_label(cell)
                    if len(lab) < 2 or len(lab) > 80 or NUMERIC.match(lab): continue
                    kind = "c" if i < hr else "r"
                    low = lab.lower()
                    if low in seen[kind]: continue
                    seen[kind].add(low)
                    labels[kind][low].append(pos)
        sizes["vol"] += write(f"vol/{key}.json.gz", {"key": key, "year": int(v["year"]), "tables": vol})
        if extracted["obs"] or extracted["officers"] or extracted["establishment"]:
            sizes["extracted"] += write(f"extracted/{key}.json.gz", extracted)
        meta.append({"key": key, "year": int(v["year"]), "note": v.get("note") or "", "ia": v["archive_org_identifier"],
                     "pages": n_pages, "tables": sum(counts.values()), "levels": [counts[l] for l in LEVELS],
                     "extracted": bool(extracted["obs"] or extracted["officers"] or extracted["establishment"])})
        print(key, sum(counts.values()), "tables", flush=True)

    def deltas(ids):
        out, prev = [], 0
        for x in ids: out.append(x - prev); prev = x
        return out
    sizes["labels"] = write("labels.json.gz", {k: {lab: deltas(ids) for lab, ids in sorted(d.items())} for k, d in labels.items()})
    sizes["index"] = write("index.json.gz", {
        "fields": ["volume", "pdf_page", "t", "printed_page", "section", "headings", "n_rows", "n_cols", "level",
                   "totals_checked", "totals_agree", "n_observations", "n_officers"],
        "sections": sections, "tables": index})

    # acreage by crop, for the series chart: one point per printed figure, with the level of the table it came from
    # printed figures judged to be misprints (page_readings/acreage_suspect.tsv): kept as printed, drawn hollow
    misprints = {(r["table_id"], int(r["source_row"]), int(r["source_column"])): r["reason"] for r in tsv(BB / "page_readings/acreage_suspect.tsv")}
    acreage = []
    for r in tsv(BB / "observations.tsv.gz"):
        if r["kind"] != "agriculture:acreage_by_crop" or not r["value"]: continue
        crop = r["measure_key"] or re.sub(r"(\w)[-‐]\s*(\w)", r"\1\2", r["measure_as_printed"]).strip(" .").lower()
        crop = re.sub(r"\s+", " ", crop)
        # printed spellings of one crop: "Cocoa" (1882) is the column later printed "Cacao"; OCR "Cinna mon", "Coconutts"
        crop = {"cocoanuts": "coconuts", "coconnuts": "coconuts", "coconutts": "coconuts", "cinna mon": "cinnamon",
                "cinamon": "cinnamon", "other grains": "other grain", "pasturage": "pasture", "cocoa": "cacao"}.get(crop, crop)
        area = r["area_key"] or re.sub(r"\s+", " ", r["area_as_printed"]).strip(" .").lower()
        area = re.sub(r"^province of (.+)$", r"\1 province", area)
        # the island total is printed "CEYLON" (1928), "Total" (1902-1912) or as an unlabelled total row (1869)
        if area in ("ceylon", "total") or (not area and "printed total" in r["note"]): area = "ceylon (island total)"
        acreage.append([crop, area, r["area_as_printed"], intval(r["year_volume"]), intval(r["year_data"]),
                        float(r["value"]), r["value_as_printed"], r["table"],
                        # figures read by eye from the page image (page_readings/) get their own level in the chart
                        "page_image" if "read from the page image" in r["note"] else conf.get(r["table"], {}).get("level", "unconfirmed"),
                        r["note"], misprints.get((r["table"], *map(int, re.search(r"source row (\d+), column (\d+)", r["note"]).groups())), "")])
    sizes["acreage"] = write("acreage.json", {"fields": ["crop", "area", "area_as_printed", "year_volume", "year_data", "value",
                                                         "value_as_printed", "table", "level", "note", "probable_misprint"], "rows": acreage}, compress=False)
    sizes["volumes"] = write("volumes.json", {"levels": LEVELS, "volumes": meta}, compress=False)

    total = sum(sizes.values())
    for k, n in sizes.items(): print(f"{k:10s} {n / 1e6:7.2f} MB")
    print(f"{'total':10s} {total / 1e6:7.2f} MB  ({len(index)} tables, {len(labels['r'])} row labels, {len(labels['c'])} column labels)")


if __name__ == "__main__":
    main()
