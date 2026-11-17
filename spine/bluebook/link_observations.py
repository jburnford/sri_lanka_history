"""Give the extracted Blue Book figures (agriculture, trade) links to the spine: the area or country a figure is
about and the crop, article or animal it measures, where the printed label is a name the spine has already
matched. The printed labels stay as they are; unresolved ones are counted in observation_labels_unlinked.tsv.
Output: bluebook/observations.tsv.gz  (one row per printed figure, both extracts, common columns)

unit_as_printed is the unit of the figure itself (Rs. for a value); article_unit_as_printed is the unit printed beside
a trade article, which applies to its quantities. period_as_printed is the period the figure covers as the source
gives it ("1910-11", "6 months ended 1910-06"); year_data is only its end year. area_relation and measure_relation
say how the printed label stands to the name it is linked to: only "exact" links should be added into a total for
that place or commodity.
"""
import collections, csv, gzip, re, sys
from pathlib import Path
BB = Path(__file__).parent
sys.path.insert(0, str(BB.parent))
from common import *
from link_cells import ALIAS
csv.field_size_limit(sys.maxsize)
EXC = re.compile(r"[,(]\s*(?:exc|exo|exe|excl|ex|excluding|except|non)\b[-.,]*", re.I)
INC = re.compile(r"[,(]\s*(?:inc|incl|including|with)\b", re.I)
PROV = re.compile(r"^(western|central|northern|southern|eastern|north western|north central|uva|sabaragamuwa)$")

def main():
    resolved = collections.defaultdict(dict)
    for r in csv.DictReader(gzip.open(HERE / "graph/resolutions.tsv.gz", "rt"), delimiter="\t"):
        if r["status"] == "matched" and r["entity_id"]: resolved[r["key"]].setdefault(r["type"], r["entity_id"])
    senses = {r["label_key"]: r for r in csv.DictReader(open(BB / "trade_place_senses.tsv"), delimiter="\t")}
    def forms(t):
        """-> [(key, cut)]: keys for the whole printed label first, then keys for the label cut at a bracket or comma."""
        t = re.sub(r"[.:;,*†‡§— \-]+$", "", re.sub(r"\s*\.\.+.*$", "", t)).strip()
        out = []
        for txt, cut in ((t, False), (re.split(r"\s*[(\[]", t)[0], True), (t.split(",")[0], True)):
            k = key(txt)
            for v in (k, k[:-1] if k.endswith("s") and len(k) > 4 else k + "s" if len(k) > 3 else k):
                v = ALIAS.get(v, v)
                if len(v) >= 3 and v not in [o[0] for o in out]: out.append((v, cut))
        return out
    def find(label, types, province=False):
        """-> (type, key, relation). relation says how the printed label stands to the name it is linked to:
        exact; excludes_part ("China, exc. Hong Kong"); includes_more ("Poland (including Danzig)"); qualified
        (some other bracket or comma qualifier was dropped); broader_head ("Oil, castor" linked only to "oil")."""
        fs = forms(label)
        if province and fs and PROV.match(fs[0][0]): fs = [(fs[0][0] + " province", False)] + fs      # "Western" in a province column
        for k, cut in fs:
            for t in types:
                if t in resolved.get(k, {}):
                    rel = "exact" if not cut else "excludes_part" if EXC.search(label) else "includes_more" if INC.search(label) else "qualified"
                    return t, k, rel
        return "", "", ""
    def find_country(label):
        """A country or area heading in a trade return. trade_place_senses.tsv decides the labels that the journal's
        names cannot: a heading that excludes the very thing its first word names, or a name with another sense here."""
        sense = senses.get(key(label)) or senses.get(key(EXC.split(label)[0]) + " exc") if EXC.search(label) else senses.get(key(label))
        if sense:
            if sense["action"] == "unlink": return "", "", ""
            return "PLACE", sense["spine_key"], sense["relation"] or "exact"
        return find(label, ["PLACE"])
    out, miss, n, seq = [], collections.Counter(), collections.Counter(), collections.Counter()
    def oid(table, letter):
        """An id that numbers figures within their own table, so a change to one table leaves the others' ids alone."""
        seq[(table, letter)] += 1
        return f"{table}#{letter}{seq[(table, letter)]}"
    p = BB / "extracted/agriculture.tsv"
    if p.exists():
        for r in csv.DictReader(open(p, newline=""), delimiter="\t"):
            at, ak, ar = find(r["area_as_printed"], ["PLACE"], province=r["area_level"] == "province") if r["area_as_printed"] else ("", "", "")
            mt, mk, mr = find(r["measure_as_printed"], ["COMMODITY", "TAXON"])
            if r["area_as_printed"] and not ak: miss[("area", r["area_as_printed"])] += 1
            if not mk: miss[("measure", r["measure_as_printed"])] += 1
            n["agriculture"] += 1; n["agri area linked"] += bool(ak); n["agri measure linked"] += bool(mk)
            out.append((oid(r["table_id"], "a"), r["table_id"], "agriculture:" + r["table_kind"], r["year_volume"], r["year_data"], r["year_data"], r["area_as_printed"], r["parent_area_as_printed"],
                        r["measure_as_printed"], r["unit_as_printed"], "", r["value_as_printed"], r["value"], r["note"], ak, ar, mt, mk, mr))
    # the period each ledger table covers (trade_periods.py): not always the calendar year of the volume
    period = {r["table_id"]: r for r in csv.DictReader(open(BB / "extracted/trade_periods.tsv"), delimiter="\t")} \
        if (BB / "extracted/trade_periods.tsv").exists() else {}
    # the article-by-country ledgers: 1907-1928 (jobs/trade_work), 1901-1906 (read_trade_old.py), 1880-1900 (Codex job)
    # Only ledgers that have passed a check against the page images are linked. The 1901-1906 file
    # (read_trade_old.py) and the 1880-1900 file (Codex job) are not yet in that state: add them here when they are.
    ACCEPTED = ["trade.tsv.gz"]
    for p in [BB / "extracted" / f for f in ACCEPTED]:
        if not p.exists(): continue
        for r in csv.DictReader(gzip.open(p, "rt", newline=""), delimiter="\t"):
            if r.get("row_kind") != "country": continue
            at, ak, ar = find_country(r["country_as_printed"])
            art = re.sub(r"[—\-:]+$", "", r["article_as_printed"]).strip()
            mt = mk = mr = ""
            if "," in art:                                  # "Oil, citronella" -> "citronella oil", before any cut at the comma
                a, b = [x.strip() for x in art.split(",", 1)]
                mt, mk, mr = find(f"{b} {a}", ["COMMODITY", "TAXON"])
                if mr != "exact": mt = mk = mr = ""
            if not mk:
                mt, mk, mr = find(art, ["COMMODITY", "TAXON"])
                if mk and mr != "exact" and "," in art: mr = "broader_head"      # only the head word matched: "Oil, castor" -> "oil"
            if not ak: miss[("country", r["country_as_printed"])] += 1
            if not mk: miss[("article", art)] += 1
            n["trade"] += 1; n["trade country linked"] += bool(ak); n["trade article linked"] += bool(mk)
            pd = period.get(r["table_id"]); yd, note, per = r["year_volume"], r["note"], ""
            if pd:
                yd = pd["period_end"][:4]; per = f"{pd['months']} months ended {pd['period_end']}" + (" (assumed)" if pd["basis"].startswith("assumed") else "")
                if pd["months"] != "12" or not pd["period_end"].endswith("-12"):
                    note += f"; period: {pd['months']} months ended {pd['period_end']} (not a calendar year); year_data is the year the period ends"
                elif pd["basis"].startswith("assumed"):
                    note += "; period caption not read: the calendar year of the volume is assumed"
            money = r["measure"].startswith("value")          # the value columns are headed Rs.; the unit printed beside the article is for its quantities
            out.append((oid(r["table_id"], "t"), r["table_id"], "trade:" + r["flow"] + ":" + r["measure"], r["year_volume"], yd, per, r["country_as_printed"], r["country_group_as_printed"],
                        art, "Rs." if money else r["unit_as_printed"], r["unit_as_printed"], r["value_as_printed"], r["value"], note, ak, ar, mt, mk, mr))
    # value of trade with each country by class, 1922-1938 (extract_trade_summary.py): country rows only
    p = BB / "extracted/trade_by_country_class.tsv"
    if p.exists():
        for r in csv.DictReader(open(p, newline=""), delimiter="\t"):
            if r["row_kind"] != "country": continue
            at, ak, ar = find_country(r["country_as_printed"])
            if not ak: miss[("country", r["country_as_printed"])] += 1
            n["trade summary"] += 1; n["trade summary country linked"] += bool(ak)
            note = r["note"] + ("" if r["row_check"] == "adds up" else "; row check: " + r["row_check"])
            out.append((oid(r["table_id"], "s"), r["table_id"], "trade_summary:" + r["statement"] + ":" + r["measure"], r["year_volume"], r["year_data"], r["year_data"],
                        r["country_as_printed"], r["region_as_printed"], r["column_as_printed"], "Rs.", "", r["value_as_printed"], r["value"], note, ak, ar, "", "", ""))
    # the island's annual series from the "Statistical View of the Progress of Ceylon": one value per series and year,
    # the one most volumes print (statistical_view_consensus.py), tied to the latest table that prints it
    p, pd_ = BB / "extracted/statistical_view_series.tsv", BB / "extracted/statistical_view.tsv.gz"
    if p.exists() and pd_.exists():
        where = {}
        for r in csv.DictReader(gzip.open(pd_, "rt", newline=""), delimiter="\t"):
            where[(r["series"], r["data_year"], r["value"])] = (r["table_id"], r["year_volume"], r["column_as_printed"], r["value_as_printed"])
        at, ak, ar = find("Ceylon", ["PLACE"])
        for r in csv.DictReader(open(p, newline=""), delimiter="\t"):
            w = where.get((r["series"], r["data_year"], r["value"]))
            if not w: continue
            n["series"] += 1
            note = (f"Statistical View series; printed with this value in {r['volumes_agreeing']} of {r['volumes_printing']} volumes; support {r['support']}"
                    + (f"; other values printed: {r['other_values']}" if r["other_values"] else ""))
            out.append((f"sv:{r['series']}:{r['data_year']}", w[0], "series:" + r["series"], w[1][:4], r["data_year"][:4], r["data_year"], "Ceylon", "", w[2], "", "", w[3], r["value"], note, ak, ar, "", "", ""))
    with gzip.open(BB / "observations.tsv.gz", "wt", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["id", "table", "kind", "year_volume", "year_data", "period_as_printed", "area_as_printed", "parent_as_printed", "measure_as_printed", "unit_as_printed",
                    "article_unit_as_printed", "value_as_printed", "value", "note", "area_key", "area_relation", "measure_type", "measure_key", "measure_relation"]); w.writerows(out)
    with open(BB / "observation_labels_unlinked.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["role", "label_as_printed", "rows"])
        for (role, lab), c in miss.most_common(): w.writerow([role, lab, c])
    print(dict(n)); print("top unlinked:", [(k[0], k[1], c) for k, c in miss.most_common(25)])

if __name__ == "__main__":
    main()
