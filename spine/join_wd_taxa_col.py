"""Join Wikidata taxon items used in grounding/*_wd.jsonl to the pinned Catalogue of Life release by their
taxon name (P225), so a vernacular name ("coconut") reaches the same Taxon record as the scientific name.
Cache: cache/col_match_wd.jsonl. Output: grounding/wd_taxon_col.jsonl. Unmatched names are kept with status.
"""
import json, concurrent.futures as cf
from common import *
import ground_taxa_col as g
CACHE = HERE / "cache/col_match_wd.jsonl"

def main():
    want = {}
    for t in ("taxon", "commodity"):
        p = HERE / f"grounding/{t}_wd.jsonl"
        if not p.exists(): continue
        for d in read_jsonl(p):
            if d["status"] != "matched": continue
            if d.get("taxon_name"): want[d["qid"]] = d["taxon_name"]
            for s in d.get("source_taxa", []):
                if s.get("taxon_name"): want[s["qid"]] = s["taxon_name"]
    cache = {d["q"]: d["r"] for d in read_jsonl(CACHE)} if CACHE.exists() else {}
    todo = sorted(set(want.values()) - set(cache))
    def one(n):
        res = g.ask(n)
        if res is None: return n, None
        slim = {"match": res.get("match"), "type": res.get("type")}
        u = res.get("usage")
        if u:
            slim["usage"] = {k: u.get(k) for k in ("id", "name", "authorship", "rank", "status")}
            cl = u.get("classification") or []
            if is_synonym_status(u.get("status")) and cl:      # a provisionally accepted name has its genus first here, not an accepted name
                slim["accepted"] = {k: cl[0].get(k) for k in ("id", "name", "authorship", "rank", "status")}
            slim["family"] = next((c["name"] for c in cl if c.get("rank") == "family"), None)
            slim["kingdom"] = next((c["name"] for c in cl if c.get("rank") == "kingdom"), None)
        return n, slim
    with open(CACHE, "a") as fh, cf.ThreadPoolExecutor(4) as ex:
        for n, slim in ex.map(one, todo):
            if slim is None: continue
            cache[n] = slim; fh.write(json.dumps({"q": n, "r": slim}, ensure_ascii=False) + "\n")
    ok = 0
    with open(HERE / "grounding/wd_taxon_col.jsonl", "w") as fh:
        for qid, n in sorted(want.items()):
            c = cache.get(n) or {}; u = c.get("usage")
            d = {"qid": qid, "taxon_name": n, "source": f"catalogue_of_life:{g.RELEASE}"}
            if c.get("match") and u and key(u["name"]) == key(n):
                d.update(status="matched", col_usage_id=u["id"], col_name=u["name"], col_authorship=u.get("authorship"), col_rank=u.get("rank"),
                         col_status=u.get("status"), col_accepted=c.get("accepted") if is_synonym_status(u.get("status")) else None, family=c.get("family"), kingdom=c.get("kingdom")); ok += 1
            else: d.update(status="unmatched")
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"wikidata taxon items: {len(want)}; joined to Catalogue of Life: {ok}")

if __name__ == "__main__":
    main()
