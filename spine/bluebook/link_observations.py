"""Give the extracted Blue Book figures (agriculture, trade) links to the spine: the area or country a figure is
about and the crop, article or animal it measures, where the printed label is a name the spine has already
matched. The printed labels stay as they are; unresolved ones are counted in observation_labels_unlinked.tsv.
Output: bluebook/observations.tsv.gz  (one row per printed figure, both extracts, common columns)
"""
import collections, csv, gzip, re, sys
from pathlib import Path
BB = Path(__file__).parent
sys.path.insert(0, str(BB.parent))
from common import *
from link_cells import variants
csv.field_size_limit(sys.maxsize)
PROV = re.compile(r"^(western|central|northern|southern|eastern|north western|north central|uva|sabaragamuwa)$")

def main():
    resolved = collections.defaultdict(dict)
    for r in csv.DictReader(gzip.open(HERE / "graph/resolutions.tsv.gz", "rt"), delimiter="\t"):
        if r["status"] == "matched" and r["entity_id"]: resolved[r["key"]].setdefault(r["type"], r["entity_id"])
    def find(label, types, province=False):
        ks = variants(label)
        if province and ks and PROV.match(ks[0]): ks = [ks[0] + " province"] + ks      # "Western" in a province column
        for k in ks:
            for t in types:
                if t in resolved.get(k, {}): return t, k
        return "", ""
    out, miss, n = [], collections.Counter(), collections.Counter()
    p = BB / "extracted/agriculture.tsv"
    if p.exists():
        for r in csv.DictReader(open(p, newline=""), delimiter="\t"):
            at, ak = find(r["area_as_printed"], ["PLACE"], province=r["area_level"] == "province") if r["area_as_printed"] else ("", "")
            mt, mk = find(r["measure_as_printed"], ["COMMODITY", "TAXON"])
            if r["area_as_printed"] and not ak: miss[("area", r["area_as_printed"])] += 1
            if not mk: miss[("measure", r["measure_as_printed"])] += 1
            n["agriculture"] += 1; n["agri area linked"] += bool(ak); n["agri measure linked"] += bool(mk)
            out.append((f"{r['table_id']}#a{n['agriculture']}", r["table_id"], "agriculture:" + r["table_kind"], r["year_volume"], r["year_data"], r["area_as_printed"], r["parent_area_as_printed"],
                        r["measure_as_printed"], r["unit_as_printed"], r["value_as_printed"], r["value"], r["note"], ak, mt, mk))
    p = BB / "extracted/trade.tsv"
    if p.exists():
        for r in csv.DictReader(open(p, newline=""), delimiter="\t"):
            if r.get("row_kind") != "country": continue
            at, ak = find(r["country_as_printed"], ["PLACE"])
            art = re.sub(r"[—\-:]+$", "", r["article_as_printed"]).strip()
            mt, mk = find(art, ["COMMODITY", "TAXON"])
            if not mk and "," in art:                       # "Oil, citronella" -> "citronella oil"
                a, b = [x.strip() for x in art.split(",", 1)]
                mt, mk = find(f"{b} {a}", ["COMMODITY", "TAXON"])
                if not mk: mt, mk = find(a, ["COMMODITY", "TAXON"])
            if not ak: miss[("country", r["country_as_printed"])] += 1
            if not mk: miss[("article", art)] += 1
            n["trade"] += 1; n["trade country linked"] += bool(ak); n["trade article linked"] += bool(mk)
            out.append((f"{r['table_id']}#t{n['trade']}", r["table_id"], "trade:" + r["flow"] + ":" + r["measure"], r["year_volume"], r["year_volume"], r["country_as_printed"], r["country_group_as_printed"],
                        art, r["unit_as_printed"], r["value_as_printed"], r["value"], r["note"], ak, mt, mk))
    with gzip.open(BB / "observations.tsv.gz", "wt", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["id", "table", "kind", "year_volume", "year_data", "area_as_printed", "parent_as_printed", "measure_as_printed", "unit_as_printed",
                    "value_as_printed", "value", "note", "area_key", "measure_type", "measure_key"]); w.writerows(out)
    with open(BB / "observation_labels_unlinked.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["role", "label_as_printed", "rows"])
        for (role, lab), c in miss.most_common(): w.writerow([role, lab, c])
    print(dict(n)); print("top unlinked:", [(k[0], k[1], c) for k, c in miss.most_common(25)])

if __name__ == "__main__":
    main()
