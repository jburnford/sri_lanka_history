"""Link Blue Book table labels to names already resolved in the spine (places, commodities, taxa, organisations).

Only label cells are read: header rows and the first two columns, non-numeric. A label links when its
normalised form (or its singular/plural variant, or the form before a bracket or comma) is a name the spine
has already MATCHED to an entity. Nothing new is decided here; unlinked frequent labels are listed for review.
Output: bluebook/cell_links.tsv.gz        table, row, col, printed label, name type, name key, entity id
        bluebook/unlinked_labels.tsv      frequent labels with no resolved name (the Blue Book review queue)
        bluebook/tables_index.tsv.gz      one line per table for the graph (id, year, page, section, headings, size)
"""
import collections, csv, glob, gzip, json, re, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from common import *
BB = HERE / "bluebook"
NUM = re.compile(r"^[\d\s,.\-–—/£%*†‡§()]*$|^(do|ditto|total|nil|\.\.+|—+)\.?$", re.I)
ORDER = ["PLACE", "COMMODITY", "TAXON", "ORG"]

_AL = BB / "label_aliases.tsv"        # printed Blue Book spellings that mean a name the spine already has
ALIAS = {r["label_key"]: r["spine_key"] for r in csv.DictReader(open(_AL), delimiter="\t")} if _AL.exists() else {}

def variants(t):
    t = re.sub(r"[.:;,*†‡§ ]+$", "", re.sub(r"\s*\.\.+.*$", "", t)).strip()
    ks = [key(t)]
    for cut in (re.split(r"\s*[(\[]", t)[0], t.split(",")[0]):
        if key(cut) and key(cut) not in ks: ks.append(key(cut))
    for k in list(ks):
        if k.endswith("s") and len(k) > 4: ks.append(k[:-1])
        elif len(k) > 3: ks.append(k + "s")
    ks = [ALIAS.get(k, k) for k in ks]
    return [k for k in dict.fromkeys(ks) if len(k) >= 3]

def main():
    resolved = collections.defaultdict(dict)        # key -> {type: entity_id}
    for r in csv.DictReader(gzip.open(HERE / "graph/resolutions.tsv.gz", "rt"), delimiter="\t"):
        if r["status"] == "matched" and r["entity_id"]: resolved[r["key"]].setdefault(r["type"], r["entity_id"])
    links, unl, idx, stats = [], collections.Counter(), [], collections.Counter()
    for f in sorted(glob.glob(str(BB / "tables/*.jsonl.gz"))):
        for line in gzip.open(f, "rt"):
            t = json.loads(line); n_link = 0
            for ri, row in enumerate(t["rows"]):
                cols = range(len(row)) if ri < max(t["header_rows"], 1) else range(min(2, len(row)))
                seen = set()
                for ci in cols:
                    cell = row[ci]
                    if not cell or len(cell) > 80 or NUM.match(cell) or cell in seen: continue
                    seen.add(cell)
                    hit = next((k for k in variants(cell) if k in resolved), None)
                    if hit is None:
                        if ri >= t["header_rows"] and ci == 0 and re.match(r"[A-Z][a-z]", cell): unl[(t["year"], key(cell))] += 1
                        continue
                    for ty in ORDER:
                        if ty in resolved[hit]:
                            links.append((t["id"], ri, ci, cell, ty, hit, resolved[hit][ty])); n_link += 1; stats[ty] += 1
            idx.append((t["id"], t["year"], t["pdf_page"], t["printed_page"] or "", t["section"] or "", " | ".join(t["headings"])[:500], t["n_rows"], t["n_cols"], n_link))
    with gzip.open(BB / "cell_links.tsv.gz", "wt", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["table", "row", "col", "label", "type", "key", "entity_id"]); w.writerows(links)
    with gzip.open(BB / "tables_index.tsv.gz", "wt", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["id", "year", "pdf_page", "printed_page", "section", "headings", "n_rows", "n_cols", "n_links"]); w.writerows(idx)
    # aggregated for the graph: one row per table and name, with the polity that held a place in the volume's year
    from empire import Empire
    E = Empire(); agg = collections.OrderedDict(); year_of = {i[0]: i[1] for i in idx}; pol = {}
    for tid, ri, ci, cell, ty, k, eid in links:
        a = agg.setdefault((tid, ty, k), [0, collections.Counter()]); a[0] += 1; a[1][cell] += 1
    with gzip.open(BB / "table_name_links.tsv.gz", "wt", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["table", "type", "key", "cells", "labels", "polity_at_date"])
        for (tid, ty, k), (n, labs) in agg.items():
            p = ""
            if ty == "PLACE":
                q = resolved[k]["PLACE"][3:]; y = year_of[tid]
                if (q, y) not in pol:
                    try: pol[(q, y)] = (E.polity_at(q, y)[0] or {}).get("id", "") if E.by_qid.get(q) else ""
                    except Exception: pol[(q, y)] = ""
                p = pol[(q, y)]
            w.writerow([tid, ty, k, n, " | ".join(f"{l} ({c})" for l, c in labs.most_common(3)), p])
    tot = collections.Counter(); yrs = collections.defaultdict(set)
    for (y, k), n in unl.items(): tot[k] += n; yrs[k].add(y)
    with open(BB / "unlinked_labels.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["label_key", "rows", "volumes"])
        for k, n in tot.most_common(3000):
            if n >= 3: w.writerow([k, n, len(yrs[k])])
    print("tables", len(idx), "with links", sum(1 for i in idx if i[-1]), "links", len(links), dict(stats))
    print("top unlinked:", [f"{k} ({n})" for k, n in tot.most_common(40)])

if __name__ == "__main__":
    main()
