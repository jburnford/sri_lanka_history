"""Tier 3, step 1: Wikidata vector-search candidates for frequent journal place names the CO List does not cover.

Candidates come ONLY from the WikidataMCP search_items tool (never from memory, never wbsearchentities).
Two queries per name: the name with a class hint taken from how the journal uses it, and the name alone.
Cached in cache/wd_search.jsonl (query -> results); reruns are free and resumable.
Usage: search_places_wd.py [min_articles=15]
"""
import json, re, sys, time, concurrent.futures as cf
from common import *
MCP_CLIENT = "/mnt/data/jic823/tropical-agriculturist/ner/persons/wd"   # imported only when searching, so queries() can be used without it

CACHE = HERE / "cache/wd_search.jsonl"
HINTS = ["country", "city", "town", "island", "district", "province", "state", "river", "region", "port",
         "mountain", "colony", "village", "street", "continent", "county", "lake", "valley", "estate"]

def hint(roles):
    txt = " ".join(re.sub(r" \(\d+\)", "", p) for p in roles.split(" | "))
    h = next((w for w in HINTS if re.search(rf"\b{w}\b", txt)), "")
    if re.search(r"\b(in ceylon|meteorological station|weather station)\b", txt): h = (h + " Sri Lanka").strip()
    return h

def queries(r):
    name = re.sub(r" \(\d+\)$", "", r["surfaces"].split(" | ")[0]).strip() or r["key"]
    if name.isupper(): name = name.title()
    h = hint(r["roles"])
    return [q for q in dict.fromkeys([f"{name} {h}".strip(), name])]

def main():
    min_articles = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    done_keys = {d["key"] for d in read_jsonl(HERE / "grounding/places_tier1.jsonl") if d["status"] == "matched"}
    if (HERE / "grounding/places_tier1b.jsonl").exists():   # names settled in the review pass; the rest go on to Wikidata search
        done_keys |= {d["key"] for d in read_jsonl(HERE / "grounding/places_tier1b.jsonl") if d["status"] == "matched"}
    cache = {}
    if CACHE.exists():
        for d in read_jsonl(CACHE): cache[d["query"]] = d["results"]
    todo = []
    for r in read_names("PLACE"):
        if r["articles"] < min_articles or r["key"] in done_keys: continue
        todo += [q for q in queries(r) if q not in cache]
    todo = list(dict.fromkeys(todo))
    print(f"queries to run: {len(todo)} (cached {len(cache)})", flush=True)
    global mcp_client
    sys.path.insert(0, MCP_CLIENT); import mcp_client as _m
    mcp_client = _m
    mcp_client.init()
    with open(CACHE, "a") as fh, cf.ThreadPoolExecutor(2) as ex:
        for i, (q, res) in enumerate(zip(todo, ex.map(lambda q: _safe(q), todo)), 1):
            if res is None: continue
            fh.write(json.dumps({"query": q, "results": res}, ensure_ascii=False) + "\n"); fh.flush()
            if i % 200 == 0: print(i, flush=True)

def _safe(q):
    try:
        for k in range(4):   # the server intermittently answers "no matching items"; an empty result is retried
            res = mcp_client.search(q)
            if res: return res
            time.sleep(1.5 * (k + 1))
        return []
    except Exception as e:
        print("fail", q, repr(e)[:100], flush=True); return None

if __name__ == "__main__":
    main()
