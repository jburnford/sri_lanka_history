"""Wikidata vector-search candidates for frequent journal names of one entity type (TAXON, COMMODITY, ORG...).

Same rules as search_places_wd.py: candidates only from the WikidataMCP search_items tool, cached in
cache/wd_search.jsonl, empty answers retried. Two queries per name: with a type hint, and the name alone.
Usage: search_names_wd.py TYPE [min_articles=15]
"""
import json, re, sys, concurrent.futures as cf
from common import *
import search_places_wd as sp

HINT = {"TAXON": "plant species", "COMMODITY": "commodity product", "ORG": "organization", "PUBLICATION": "periodical",
        "PRODUCT": "product", "GROUP": "ethnic group"}

def queries(r, t):
    # the normalised key, not the commonest printed form: taxa are often printed abbreviated ("succirubra")
    name = r["key"]
    roles = " ".join(re.sub(r" \(\d+\)", "", p) for p in r["roles"].split(" | "))
    h = HINT.get(t, "")
    if t == "TAXON":
        h = "insect species" if re.search(r"\b(insect|pest|beetle|moth|bug|scale)\b", roles) else \
            "fungus species" if re.search(r"\b(fung|disease|blight|rust|mildew)\b", roles) else \
            "animal species" if re.search(r"\b(animal|bird|fish|mammal|cattle)\b", roles) else "plant species"
    qs = [f"{name} {h}".strip(), name]
    # third query: the name with the journal's own commonest description of it ("plumbago mineral",
    # "dadap shade tree"), which finds items filed under a modern name with the old one as an alias
    top = re.sub(r" \(\d+\)$", "", r["roles"].split(" | ")[0]).strip()
    if t in ("TAXON", "COMMODITY") and top and top not in ("product", "crop", "plant", "traded product", "commodity", "agricultural product"): qs.append(f"{name} {top}")
    elif t in ("TAXON", "COMMODITY"):
        alt = [re.sub(r" \(\d+\)$", "", x).strip() for x in r["roles"].split(" | ")[1:4]]
        alt = [a for a in alt if a not in ("product", "crop", "plant", "traded product", "commodity", "agricultural product", "export")]
        if alt: qs.append(f"{name} {alt[0]}")
    return list(dict.fromkeys(qs))

def main():
    t = sys.argv[1]; min_articles = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    cache = {d["query"] for d in read_jsonl(sp.CACHE)} if sp.CACHE.exists() else set()
    todo = []
    for r in read_names(t):
        if r["articles"] < min_articles: continue
        todo += [q for q in queries(r, t) if q not in cache]
    todo = list(dict.fromkeys(todo))
    print(f"{t}: queries to run {len(todo)}", flush=True)
    sys.path.insert(0, sp.MCP_CLIENT); import mcp_client
    sp.mcp_client = mcp_client            # sp._safe uses it
    mcp_client.init()
    with open(sp.CACHE, "a") as fh, cf.ThreadPoolExecutor(2) as ex:
        for i, (q, res) in enumerate(zip(todo, ex.map(sp._safe, todo)), 1):
            if res is None: continue
            fh.write(json.dumps({"query": q, "results": res}, ensure_ascii=False) + "\n"); fh.flush()
            if i % 200 == 0: print(i, flush=True)

if __name__ == "__main__":
    main()
