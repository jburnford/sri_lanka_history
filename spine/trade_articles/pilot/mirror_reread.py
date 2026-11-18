#!/usr/bin/env python3
"""Mirror comparison, second pass: the guided re-read of Ceylon's main export lines against the UK side.

Reads   ../../bluebook/jobs/main_exports_1880_1900_work/main_exports.tsv   (entry-by-entry re-read, made without
        the UK figures) and mirror.tsv (for the UK figures and the first-pass Ceylon figures).
Writes  mirror_reread.tsv, one row per commodity and Blue Book volume.

Neither side is treated as right. The Ceylon figure for a year is the United Kingdom row of each block of the
commodity: its total quantity cells (summed where the ledger prints the total in parts, e.g. cinnamon and chips),
or the sum of its component cells where no total cell was read. Standard library only.
"""
import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REREAD = HERE.parents[1] / "bluebook" / "jobs" / "main_exports_1880_1900_work" / "main_exports.tsv"
NAME = {"tea": "tea", "coffee": "coffee, raw (all kinds)", "cinchona": "cinchona bark", "cinnamon": "cinnamon",
        "coconut_oil": "coconut oil", "plumbago": "plumbago"}
MIRROR_UNIT = {"tea": "lb", "coffee": "cwt", "cinchona": "cwt", "cinnamon": "lb", "coconut_oil": "cwt",
               "plumbago": "cwt"}
RANK = {"clear": 0, "doubtful": 1, "unreadable": 2}


def unit_of(printed):
    """Weight unit a figure is in, or None for counts of packages, bales, drums."""
    text = printed.lower()
    if "cwt" in text:
        return "cwt"
    if re.search(r"\blbs?\b", text):
        return "lb"
    return None


def convert(amount, unit, target):
    if unit == target:
        return amount
    return amount / 112 if target == "cwt" else amount * 112


def row_figure(cells, target):
    """One ledger row: (quantity in target unit, value in rupees, worst reading, how the quantity was formed)."""
    weights = [c for c in cells if c["measure"].startswith("quantity") and unit_of(c["unit_as_printed"])]
    totals = [c for c in weights if c["measure"] == "quantity_total"]
    parts = [c for c in weights if c["measure"] != "quantity_total"]
    used, how = (totals, "total cell") if totals else (parts, "sum of components")
    worst = max((RANK[c["reading"]] for c in used), default=2)   # reading of the quantity cells used
    if not used or any(not c["value"] for c in used):
        quantity = None
    else:
        quantity = sum(convert(float(c["value"]), unit_of(c["unit_as_printed"]), target) for c in used)
    # A printed total that its own components contradict is worth knowing about.
    disagrees = ""
    if totals and parts and quantity is not None and all(c["value"] for c in parts):
        component_sum = sum(convert(float(c["value"]), unit_of(c["unit_as_printed"]), target) for c in parts)
        # Chips and similar parts are sometimes printed as totals too; only compare when one total cell exists.
        if len(totals) == 1 and abs(component_sum - quantity) > max(1.0, 0.0005 * quantity):
            disagrees = f"components sum to {component_sum:.0f}, total cell reads {quantity:.0f}"
    values = [c for c in cells if c["measure"] == "value_total_rs"] or \
             [c for c in cells if c["measure"].startswith("value") and c["measure"] != "value_total_rs"]
    value = sum(float(c["value"]) for c in values) if values and all(c["value"] for c in values) else None
    return quantity, value, worst, how, disagrees


def main():
    with open(HERE / "mirror.tsv", encoding="utf-8") as handle:
        first = {(r["commodity"], r["year"]): r for r in csv.DictReader(handle, delimiter="\t")}
    with open(REREAD, encoding="utf-8") as handle:
        records = list(csv.DictReader(handle, delimiter="\t"))

    # block = one article in one volume; row = one destination line of it
    rows = defaultdict(list)
    for r in records:
        if r["row_kind"] == "country":
            # Keyed by destination within the table, not by source row: some ledgers split one destination's
            # quantity and value over two rows of the parsed table.
            rows[(r["commodity"], r["year_volume"], r["article_as_printed"], r["table_id"],
                  r["country_as_printed"])].append(r)

    by_block = defaultdict(list)
    for (commodity, volume, article, table, country), cells in rows.items():
        source_row = "+".join(sorted({c["source_row"] for c in cells}, key=int))
        quantity, value, worst, how, disagrees = row_figure(cells, MIRROR_UNIT[commodity])
        by_block[(commodity, volume, article)].append(
            dict(country=country, table=table, row=source_row, quantity=quantity, value=value, worst=worst,
                 how=how, disagrees=disagrees))

    out = []
    for commodity in NAME:
        volumes = sorted({v for (c, v, _a) in by_block if c == commodity})
        for volume in volumes:
            year = volume[:4]
            blocks = {a: lines for (c, v, a), lines in by_block.items() if c == commodity and v == volume}
            total, value_total, worst, articles, notes, tables = 0.0, 0.0, 0, [], [], set()
            have_uk, readable, price_notes = False, True, []
            for article, lines in blocks.items():
                uk = [l for l in lines if re.search(r"kingdom", l["country"], re.I)]
                if not uk:
                    continue
                have_uk = True
                prices = [l["value"] / l["quantity"] for l in lines
                          if l["quantity"] and l["value"] and l["worst"] == 0 and not re.search(r"kingdom", l["country"], re.I)]
                # An official price exists only where the other destinations share one (within 2%).
                common = statistics.median(prices) if len(prices) >= 3 else None
                if common and sum(abs(p / common - 1) <= 0.02 for p in prices) < 0.7 * len(prices):
                    common = None
                for line in uk:
                    tables.add(f'{line["table"]}:r{line["row"]}')
                    worst = max(worst, line["worst"])
                    if line["quantity"] is None:
                        readable = False
                        continue
                    total += line["quantity"]
                    value_total += line["value"] or 0
                    articles.append(f'{article.strip()} {line["quantity"]:.0f}')
                    if line["disagrees"]:
                        notes.append(f'{article.strip()}: {line["disagrees"]}')
                    if common and line["value"]:
                        ratio = (line["value"] / line["quantity"]) / common
                        if not 0.9 <= ratio <= 1.1:
                            implied = line["value"] / common
                            price_notes.append(
                                f'{article.strip()}: row price is {ratio:.2f} times the block price of Rs {common:.4g}; '
                                f'the value implies a quantity of {implied:.0f}')
            uk_row = first.get((NAME[commodity], year), {})
            uk_figure = float(uk_row["uk_imports_from_ceylon"]) if uk_row.get("uk_imports_from_ceylon") else None
            ceylon = total if have_uk and readable and total else None
            ratio = ceylon / uk_figure if ceylon and uk_figure else None
            if ceylon is None and uk_figure is None:
                status = "both missing"
            elif ceylon is None:
                status = "ceylon unreadable" if have_uk else "ceylon: no United Kingdom row"
            elif uk_figure is None:
                status = "uk missing"
            elif abs(ratio - 1) <= 0.05:
                status = "agree within 5%"
            elif abs(ratio - 1) <= 0.15:
                status = "differ 5-15%"
            else:
                status = "differ more than 15%"
            out.append({
                "commodity": NAME[commodity], "year": year, "volume": volume, "unit": MIRROR_UNIT[commodity],
                "ceylon_exports_to_uk_reread": f"{ceylon:.0f}" if ceylon else "",
                "ceylon_reading": ["clear", "doubtful", "unreadable"][worst] if have_uk else "",
                "uk_imports_from_ceylon": uk_row.get("uk_imports_from_ceylon", ""),
                "ratio_ceylon_to_uk": f"{ratio:.3f}" if ratio else "",
                "status": status,
                "first_pass_ceylon": uk_row.get("ceylon_exports_to_uk", ""),
                "first_pass_status": uk_row.get("status", ""),
                "ceylon_value_rs": f"{value_total:.0f}" if ceylon and value_total else "",
                "ceylon_articles": "; ".join(articles),
                "ceylon_total_vs_components": "; ".join(notes),
                "ceylon_price_check": "; ".join(price_notes),
                "uk_rank": uk_row.get("uk_rank", ""),
                "uk_vs_neighbours": uk_row.get("uk_vs_neighbours", ""),
                "ceylon_rows": "; ".join(sorted(tables)),
            })

    with open(HERE / "mirror_reread.tsv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)

    counts = defaultdict(int)
    for r in out:
        counts[r["status"]] += 1
    print(f"{len(out)} commodity-volumes")
    for status, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {status}")


if __name__ == "__main__":
    main()
