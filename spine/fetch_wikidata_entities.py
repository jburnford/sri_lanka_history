"""Fetch labels, aliases, descriptions, types and coordinates for a list of QIDs into a local JSONL gazetteer.

Usage: fetch_wikidata_entities.py OUT.jsonl < qids.txt      (resumable: QIDs already in OUT are skipped)
Reads specific known QIDs via wbgetentities (50 per call). This is a lookup of known identifiers, not a search.
"""
import json, sys, time, urllib.parse, urllib.request
API = "https://www.wikidata.org/w/api.php"
UA = "historical-gazetteer-builder/0.1 (research script)"
LANGS = "en|si|ta|mul"
KEEP = {"P31": "instance_of", "P131": "admin_parent", "P17": "country", "P279": "subclass_of",
        "P1566": "geonames", "P225": "taxon_name", "P171": "parent_taxon", "P105": "taxon_rank",
        "P1582": "natural_product_of_taxon", "P1672": "taxon_source_of", "P1843": "taxon_common_name", "P159": "headquarters",
        "P571": "inception", "P576": "dissolved", "P1365": "replaces", "P1366": "replaced_by", "P846": "gbif_id", "P10585": "col_id"}

def claim_ids(claims, pid):
    out = []
    for c in claims.get(pid, []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, dict) and "id" in v: out.append(v["id"])
        elif isinstance(v, dict) and "time" in v: out.append(v["time"][:5].lstrip("+"))
        elif isinstance(v, dict) and "text" in v: out.append(v["text"])
        elif isinstance(v, str): out.append(v)
    return out

def slim(e):
    c = e.get("claims", {})
    r = {"qid": e["id"],
         "labels": {l: v["value"] for l, v in e.get("labels", {}).items()},
         "aliases": {l: [a["value"] for a in v] for l, v in e.get("aliases", {}).items()},
         "description": e.get("descriptions", {}).get("en", {}).get("value"),
         "sitelinks": len(e.get("sitelinks", {}))}
    for pid, name in KEEP.items():
        ids = claim_ids(c, pid)
        if ids: r[name] = ids
    for cc in c.get("P625", [])[:1]:
        v = cc.get("mainsnak", {}).get("datavalue", {}).get("value")
        if v: r["lat"], r["lon"] = round(v["latitude"], 5), round(v["longitude"], 5)
    if "redirects" in e: r["redirected_from"] = e["redirects"].get("from")
    return r

def fetch(batch):
    q = urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(batch), "format": "json",
        "props": "labels|aliases|descriptions|claims|sitelinks", "languages": LANGS})
    for k in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{API}?{q}", headers={"User-Agent": UA}), timeout=90) as r:
                d = json.loads(r.read())
            if "error" in d: raise RuntimeError(d["error"].get("code"))
            return d["entities"]
        except Exception as ex:
            print("retry", k, repr(ex)[:120], file=sys.stderr); time.sleep(3 * 2 ** k)
    raise SystemExit("gave up; rerun to resume")

def main():
    out = sys.argv[1]
    want = [l.strip() for l in sys.stdin if l.strip().startswith("Q")]
    have = set()
    try:
        for l in open(out): have.add(json.loads(l).get("requested", json.loads(l)["qid"]))
    except FileNotFoundError: pass
    todo = [q for q in dict.fromkeys(want) if q not in have]
    print(f"want {len(want)} have {len(have)} todo {len(todo)}", file=sys.stderr)
    with open(out, "a") as fh:
        for i in range(0, len(todo), 50):
            batch = todo[i:i + 50]
            ents = fetch(batch)
            byid = {}
            for k, e in ents.items():
                if "missing" in e: byid[k] = {"qid": k, "missing": True}
                else: byid[k] = slim(e)
            for qid in batch:
                r = byid.get(qid) or next((v for v in byid.values() if v.get("redirected_from") == qid), {"qid": qid, "missing": True})
                r = dict(r); r["requested"] = qid
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush(); time.sleep(0.5)
            if (i // 50) % 20 == 0: print(f"{i + len(batch)}/{len(todo)}", file=sys.stderr)

if __name__ == "__main__":
    main()
