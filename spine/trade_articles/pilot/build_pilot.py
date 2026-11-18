#!/usr/bin/env python3
"""Pilot: trade articles on two sides, grounded to Wikidata with the distinctions Wikidata does not hold.

Reads   concepts.tsv        trade concepts, each with a Wikidata item and the relation to it
        article_rules.tsv   printed heading -> concept and facets (first matching rule wins)
        ../../bluebook/extracted/trade*.tsv.gz        Ceylon Blue Book ledgers (exports)
        UK_TRADE_DB (default ~/uk_trade_db/db/uk_trade.duckdb)   UK imports, table country_year_final
Writes  articles.tsv        every printed article in the pilot families, with its concept, facets and years
        mirror.tsv          Ceylon exports to the UK against UK imports from Ceylon, 1880-1900, with the
                            evidence each side has for its own figure. Neither figure is corrected.

  python build_pilot.py        (needs the duckdb module for the UK side)
"""
import collections
import csv
import gzip
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXTRACTED = HERE.parents[1] / "bluebook" / "extracted"
UK_DB = Path(os.environ.get("UK_TRADE_DB", Path.home() / "uk_trade_db" / "db" / "uk_trade.duckdb"))
FAMILY = re.compile(r"\btea\b|coffee|cinchona|[io]nchona|\bbark\b|peruvian|cinnamon|coco-?a? ?nut|coprah?|poonac|"
                    r"desiccated|\bcoir|plumbago", re.I)
LB_PER = {"lb": 1, "lbs": 1, "cwt": 112, "cwts": 112, "owt": 112, "owts": 112, "ton": 2240, "tons": 2240}
# What the two sides can be compared on: concept(s) summed on the Ceylon side, concept on the UK side, the unit
# of comparison, the unit the UK statements print (assumed where the UK reading has none), and the Ceylon lines
# that are minor: a year in which only these were read is a partial reading, not a disagreement.
MIRROR = [
    ("tea", ["tea.made"], "tea.made", "lb", "lbs", None),
    ("coffee, raw (all kinds)", ["coffee.raw"], "coffee.raw", "cwt", "cwts", r"liberian|native"),
    ("cinchona bark", ["cinchona.bark"], "cinchona.bark", "cwt", "cwts", None),
    ("cinnamon", ["cinnamon.quills"], "cinnamon.quills", "lb", "lbs", r"wild"),
    ("coconut oil", ["coconut.oil"], "coconut.oil", "cwt", "cwts", None),
    ("plumbago", ["plumbago"], "plumbago", "cwt", "tons", None),
]


def read_tsv(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def tidy(label):
    label = re.sub(r"\s+", " ", label or "").strip()
    label = re.sub(r"^(?:\(?\d\)? ?[A-Z][A-Za-z ,.]*\. |[IVX]+\.—[A-Za-z ()0-9.]*\. )", "", label)   # class prefixes
    return re.sub(r"[\s.…]+$", "", label).strip()


def classify(rules, side, label):
    for rule in rules:
        if rule["side"] == side and re.search(rule["pattern"], label, re.I):
            return rule
    return None


def number(text):
    text = re.sub(r"[¼½¾]|\s+\d+/\d+$", "", str(text or "")).replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def main():
    concepts = {row["concept_id"]: row for row in read_tsv(HERE / "concepts.tsv")}
    rules = read_tsv(HERE / "article_rules.tsv")
    for rule in rules:
        assert rule["concept_id"] == "-" or rule["concept_id"] in concepts, rule

    # ---- Ceylon side ----
    articles = collections.OrderedDict()
    ceylon_rows = []
    for name in ("trade_1880_1900.tsv.gz", "trade_1880_1906.tsv.gz", "trade.tsv.gz"):
        for row in read_tsv(EXTRACTED / name):
            if row.get("flow") != "export" or not FAMILY.search(row["article_as_printed"]):
                continue
            label = tidy(row["article_as_printed"])
            rule = classify(rules, "ceylon", label)
            entry = articles.setdefault(("ceylon", label), dict(rule=rule, years=set(), figures=0, units=collections.Counter()))
            entry["years"].add(row["year_volume"][:4])
            entry["figures"] += 1
            if row["measure"].startswith("quantity"):
                entry["units"][row["unit_as_printed"].strip(". ").lower()] += 1
            if rule and rule["concept_id"] != "-" and name == "trade_1880_1900.tsv.gz":
                ceylon_rows.append((rule["concept_id"], row))

    # ---- UK side ----
    import duckdb
    uk = duckdb.connect(str(UK_DB), read_only=True)
    uk_rows = uk.execute("select article_group, article, country, unit, year, quantity, value, q_rank, v_rank, source "
                         "from country_year_final where flow = 'import'").fetchall()
    uk_ceylon = []
    for group, article, country, unit, year, quantity, value, q_rank, v_rank, source in uk_rows:
        label = " / ".join(v for v in (re.sub(r"\s+", " ", group or "").strip(), re.sub(r"\s+", " ", article or "").strip()) if v)
        if not FAMILY.search(label):
            continue
        rule = classify(rules, "uk", label.lower())
        entry = articles.setdefault(("uk", label), dict(rule=rule, years=set(), figures=0, units=collections.Counter()))
        entry["years"].add(str(year))
        entry["figures"] += 1
        entry["units"][(unit or "").strip(". ").lower()] += 1
        if rule and rule["concept_id"] != "-" and "ceylon" in (country or "").lower():
            uk_ceylon.append((rule["concept_id"], year, unit, quantity, value, q_rank, label))

    with (HERE / "articles.tsv").open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle, delimiter="\t", lineterminator="\n")
        out.writerow(["side", "article_as_printed", "concept_id", "concept_label", "qid", "relation_to_item", "facets",
                      "status", "first_year", "last_year", "volumes_or_years", "figures", "units", "rule_note"])
        for (side, label), entry in sorted(articles.items(), key=lambda kv: (kv[0][0], (kv[1]["rule"] or {}).get("concept_id", "~"), kv[0][1])):
            rule = entry["rule"]
            concept = concepts.get(rule["concept_id"]) if rule else None
            status = "assigned" if concept else "set_aside" if rule else "unassigned"
            years = sorted(entry["years"])
            out.writerow([side, label, concept["concept_id"] if concept else "", concept["label"] if concept else "",
                          concept["qid"] if concept else "", concept["relation"] if concept else "",
                          rule["facets"] if rule else "", status, years[0], years[-1], len(years), entry["figures"],
                          "; ".join(f"{u or '(none)'} {n}" for u, n in entry["units"].most_common(3)),
                          rule["note"] if rule else ""])

    # ---- mirror, 1880-1900 ----
    cey = collections.defaultdict(lambda: dict(uk_q=0.0, uk_v=0.0, total_q=None, total_v=None, parts=set(), tables=set(), n=0))
    for concept_id, row in ceylon_rows:
        year = int(row["year_volume"][:4])
        key = (concept_id, year)
        value = number(row["value"])
        if value is None:
            continue
        unit = row["unit_as_printed"].strip(". ").lower()
        if row["row_kind"] == "country" and re.search(r"united kingdom|great britain", row["country_as_printed"], re.I):
            if row["measure"] == "quantity_total" and unit in LB_PER:
                cey[key]["uk_q"] += value * LB_PER[unit]
                cey[key]["parts"].add(tidy(row["article_as_printed"]))
                cey[key]["tables"].add(row["table_id"])
                cey[key]["n"] += 1
            elif row["measure"] == "value_total_rs":
                cey[key]["uk_v"] += value
        elif row["row_kind"] == "article_total":
            if row["measure"] == "quantity_total" and unit in LB_PER:
                cey[key]["total_q"] = (cey[key]["total_q"] or 0) + value * LB_PER[unit]
            elif row["measure"] == "value_total_rs":
                cey[key]["total_v"] = (cey[key]["total_v"] or 0) + value
    ukq = collections.defaultdict(list)
    for concept_id, year, unit, quantity, value, q_rank, label in uk_ceylon:
        unit = (unit or "").strip(". ").lower()
        if quantity:
            ukq[(concept_id, year)].append((quantity, unit, q_rank, label))

    with (HERE / "mirror.tsv").open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle, delimiter="\t", lineterminator="\n")
        out.writerow(["commodity", "year", "unit", "ceylon_exports_to_uk", "uk_imports_from_ceylon", "ratio_ceylon_to_uk",
                      "status", "ceylon_articles_summed", "ceylon_share_of_quantity", "ceylon_share_of_value",
                      "ceylon_internal_check", "uk_rank", "uk_readings", "uk_unit", "uk_vs_neighbours",
                      "ceylon_vs_uk_neighbours", "points_to", "ceylon_tables"])
        for title, ceylon_concepts, uk_concept, unit, uk_unit, minor in MIRROR:
            per = LB_PER[unit]
            series = {}
            for year in range(1880, 1901):
                readings = ukq.get((uk_concept, year), [])
                usable = [(q * LB_PER[u or uk_unit] / per, r, u or uk_unit + " (assumed)") for q, u, r, _ in readings
                          if u in LB_PER or not u]
                # more than one UK reading for a year: prefer the best rank, then the larger (a sub-line may repeat)
                series[year] = min(usable, key=lambda item: (item[1], -item[0])) if usable else None
            for year in range(1880, 1901):
                c = dict(uk_q=0.0, uk_v=0.0, total_q=0.0, total_v=0.0, parts=set(), tables=set(), n=0, have_total=False)
                for concept_id in ceylon_concepts:
                    item = cey.get((concept_id, year))
                    if not item:
                        continue
                    c["uk_q"] += item["uk_q"]
                    c["uk_v"] += item["uk_v"]
                    c["parts"] |= item["parts"]
                    c["tables"] |= item["tables"]
                    c["n"] += item["n"]
                    if item["total_q"]:
                        c["total_q"] += item["total_q"]
                        c["total_v"] += item["total_v"] or 0
                        c["have_total"] = True
                ceylon_value = c["uk_q"] / per if c["n"] else None
                uk_value = series[year][0] if series[year] else None
                share_q = c["uk_q"] / c["total_q"] if c["n"] and c["have_total"] and c["total_q"] else None
                share_v = c["uk_v"] / c["total_v"] if c["n"] and c["have_total"] and c["total_v"] else None
                internal = ""
                if share_q is not None and share_v is not None and (share_q > 1.05 or share_v > 1.05 or share_v == 0):
                    internal = "printed totals not usable"   # a total was read for only some of the lines summed
                    share_q = share_v = None
                elif share_q is not None and share_v is not None:
                    internal = "consistent" if abs(share_q - share_v) <= 0.12 else "inconsistent"
                elif c["n"]:
                    internal = "no printed total read"
                neighbours = fits = ""
                before, after = series.get(year - 1), series.get(year + 1)
                if uk_value and before and after:
                    expected = (before[0] * after[0]) ** 0.5
                    neighbours = f"{uk_value / expected:.2f}"
                    if ceylon_value:
                        fits = f"{ceylon_value / expected:.2f}"
                ratio = ceylon_value / uk_value if ceylon_value and uk_value else None
                partial = bool(minor and c["parts"] and all(re.search(minor, part, re.I) for part in c["parts"]))
                if ratio is not None and partial:
                    status = "ceylon partial: main line not read"
                elif ratio is None:
                    status = "ceylon missing" if uk_value and not ceylon_value else "uk missing" if ceylon_value else "both missing"
                elif 0.95 <= ratio <= 1.05:
                    status = "agree within 5%"
                elif 0.85 <= ratio <= 1.15:
                    status = "differ 5-15%"
                else:
                    status = "differ more than 15%"
                points = ""
                if ratio is not None and status.startswith("differ"):
                    # The UK figure is only called doubtful when the Ceylon figure fits the UK's own neighbouring
                    # years better than the UK figure does. A jump in a fast-moving series is not evidence by itself.
                    uk_odd = bool(neighbours) and not 0.93 <= float(neighbours) <= 1.07 and 0.95 <= float(fits) <= 1.05
                    if internal == "inconsistent" and not uk_odd:
                        points = "ceylon reading: its share of quantity and its share of value disagree"
                    elif uk_odd and internal == "consistent":
                        points = "uk reading: the ceylon figure fits the uk's neighbouring years and is self-consistent"
                    elif internal == "inconsistent" and uk_odd:
                        points = "both doubtful"
                    else:
                        points = "undecided: needs the pages"
                out.writerow([title, year, unit, f"{ceylon_value:.0f}" if ceylon_value else "", f"{uk_value:.0f}" if uk_value else "",
                              f"{ratio:.3f}" if ratio else "", status, " + ".join(sorted(c["parts"])),
                              f"{share_q:.3f}" if share_q is not None else "", f"{share_v:.3f}" if share_v is not None else "",
                              internal, series[year][1] if series[year] else "", len(ukq.get((uk_concept, year), [])),
                              series[year][2] if series[year] else "", neighbours, fits, points,
                              " ".join(sorted(c["tables"]))])


if __name__ == "__main__":
    main()
