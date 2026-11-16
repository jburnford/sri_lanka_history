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
    return list(dict.fromkeys([f"{name} {h}".strip(), name]))

def main():
    t = sys.argv[1]; min_articles = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    cache = {d["query"] for d in read_jsonl(sp.CACHE)} if sp.CACHE.exists() else set()
    todo = []
    for r in read_names(t):
        if r["articles"] < min_articles: continue
        todo += [q for q in queries(r, t) if q not in cache]
    todo = list(dict.fromkeys(todo))
    print(f"{t}: queries to run {len(todo)}", flush=True)
    sp.mcp_client.init()
    with open(sp.CACHE, "a") as fh, cf.ThreadPoolExecutor(2) as ex:
        for i, (q, res) in enumerate(zip(todo, ex.map(sp._safe, todo)), 1):
            if res is None: continue
            fh.write(json.dumps({"query": q, "results": res}, ensure_ascii=False) + "\n"); fh.flush()
            if i % 200 == 0: print(i, flush=True)

if __name__ == "__main__":
    main()
