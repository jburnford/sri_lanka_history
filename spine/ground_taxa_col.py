"""Taxon grounding, authority 1: Catalogue of Life name matching (ChecklistBank), pinned to one release.

For each journal TAXON name, ask the COL release's name matcher. A scientific name comes back with its
authorship, rank, status (accepted / synonym / ...) and, for a synonym, the accepted name it points to.
Vernacular names ("coconut") return no match and are left for the Wikidata tier. Nothing is collapsed: the
row keeps the name as printed, the matched name record, and the accepted name as separate fields.
Cache: cache/col_match.jsonl (resumable). Output: grounding/taxa_col.jsonl.
Usage: ground_taxa_col.py [min_articles=3]
"""
import json, re, sys, time, urllib.parse, urllib.request, collections
from common import *
RELEASE = 317005          # Catalogue of Life COL26.11, issued 2026-11-11, doi:10.48580/dgzy8
API = f"https://api.checklistbank.org/dataset/{RELEASE}/match/nameusage?q="
UA = "historical-gazetteer-builder/0.1 (research script)"
CACHE = HERE / "cache/col_match.jsonl"

def ask(name):
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + urllib.parse.quote(name), headers={"User-Agent": UA}), timeout=60) as r:
                return json.loads(r.read())
        except Exception as ex:
            print("retry", name, repr(ex)[:100], file=sys.stderr); time.sleep(5 * (k + 1))
    return None

def main():
    min_articles = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    cache = {d["q"]: d["r"] for d in read_jsonl(CACHE)} if CACHE.exists() else {}
    rows = [r for r in read_names("TAXON") if r["articles"] >= min_articles]
    def one(r):
        res = ask(r["key"][:1].upper() + r["key"][1:])     # the matcher needs a capitalised genus
        if res is None: return r["key"], None
        slim = {"match": res.get("match"), "type": res.get("type"), "issues": res.get("issues"), "cap": True}
        u = res.get("usage")
        if u:
            slim["usage"] = {k: u.get(k) for k in ("id", "name", "authorship", "rank", "status", "code", "label")}
            cl = u.get("classification") or []
            if u.get("status") != "accepted" and cl: slim["accepted"] = {k: cl[0].get(k) for k in ("id", "name", "authorship", "rank", "status", "label")}
            slim["family"] = next((c["name"] for c in cl if c.get("rank") == "family"), None)
            slim["kingdom"] = next((c["name"] for c in cl if c.get("rank") == "kingdom"), None)
        return r["key"], slim
    # entries asked in lower case before the capitalisation fix are retried unless they matched exactly
    todo = [r for r in rows if r["key"] not in cache or (not cache[r["key"]].get("cap") and not (cache[r["key"]].get("usage") and key(cache[r["key"]]["usage"]["name"]) == r["key"]))]
    print(f"to match: {len(todo)}", flush=True)
    import concurrent.futures as cf
    with open(CACHE, "a") as fh, cf.ThreadPoolExecutor(4) as ex:
        for i, (k, slim) in enumerate(ex.map(one, todo), 1):
            if slim is None: continue
            cache[k] = slim
            fh.write(json.dumps({"q": k, "r": slim}, ensure_ascii=False) + "\n"); fh.flush()
            if i % 500 == 0: print(i, len(todo), flush=True)
    PLANT = re.compile(r"\b(plant|tree|crop|palm|grass|fibre|fiber|fruit|shrub|weed|timber|rubber|vegetable|cereal|grain|flower|herb|vine|creeper|legume|fodder|shade|variety|seed|bark|nut|spice|drug|dye|bean|root|tuber|bamboo)")
    ANIMAL = re.compile(r"\b(insect|pest|beetle|moth|bug|scale|worm|caterpillar|borer|fly|ant|animal|bird|fish|mammal|cattle|mite|weevil|aphis|aphid|locust|snail)")
    FUNGUS = re.compile(r"\b(fung|blight|rust|mildew|mould|mold|canker|rot|parasite|pathogen|bacteri|virus)")
    DISEASE = re.compile(r"\b(disease|fever|epidemic|infection|plague|sickness|ailment)")
    def journal_kingdoms(roles):
        """Which kinds of organism the journal's role phrases point to, weighted by count."""
        w = collections.Counter()
        for part in roles.split(" | "):
            m = re.match(r"(.*) \((\d+)\)$", part)
            if not m: continue
            txt, n = m.group(1), int(m.group(2))
            for name, rx in (("Plantae", PLANT), ("Animalia", ANIMAL), ("Fungi", FUNGUS), ("disease", DISEASE)):
                if rx.search(txt): w[name] += n
        return w
    out, tally, rec = [], collections.Counter(), collections.Counter()
    total = sum(r["records"] for r in read_names("TAXON"))
    for r in rows:
        c = cache.get(r["key"])
        if c is None: continue
        d = {"type": "TAXON", "key": r["key"], "records": r["records"], "articles": r["articles"], "first": r["first"], "last": r["last"],
             "surfaces": r["surfaces"], "roles": r["roles"], "source": f"catalogue_of_life:{RELEASE}"}
        u = c.get("usage")
        if c.get("match") and u and key(u["name"]) == r["key"]:
            d.update(status="matched", col_usage_id=u["id"], col_name=u["name"], col_authorship=u.get("authorship"), col_rank=u.get("rank"),
                     col_status=u.get("status"), col_accepted=c.get("accepted"), family=c.get("family"), kingdom=c.get("kingdom"), col_match_type=c.get("type"))
            s = "matched:" + (u.get("status") or "?")
            # A common word can collide with an unrelated genus (anthrax the disease / Anthrax the fly; castor the
            # oil plant / Castor the beaver). Refuse the match when the journal's own usage points to another kingdom.
            jk = journal_kingdoms(r["roles"]); kg = c.get("kingdom")
            top = jk.most_common(1)[0][0] if jk else None
            micro = {"Fungi", "Chromista", "Bacteria", "Protozoa", "Viruses"}
            conflict = top and kg and not (top == kg or (top == "Fungi" and kg in micro) or (top == "disease" and kg in micro))
            if conflict and jk[top] >= 2 * jk.get(kg, 0):
                d.update(status="review", reason=f"kingdom conflict: journal uses it as {top}, Catalogue of Life name is {kg} (likely a common name)")
                s = "review:kingdom conflict"
            elif " " not in r["key"] and not jk:
                d["confidence_note"] = "single word with no usage evidence"
        elif c.get("match") and u:
            higher = r["key"].startswith(key(u["name"]) + " ")
            d.update(status="review", reason="COL matched only the genus or a higher rank" if higher else "COL matched a differently spelled name",
                     col_name=u["name"], col_usage_id=u["id"], col_status=u.get("status"), col_rank=u.get("rank")); s = "review:higher rank" if higher else "review:spelling"
        else:
            d.update(status="unmatched", reason="no scientific name match (vernacular or misspelt)"); s = "unmatched"
        tally[s] += 1; rec[s] += r["records"]; out.append(d)
    with open(HERE / "grounding/taxa_col.jsonl", "w") as fh:
        for d in out: fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"taxon records in journal: {total}")
    for s in sorted(tally): print(f"  {s:28} names={tally[s]:5}  records={rec[s]:7}  ({rec[s]/total:.1%})")

if __name__ == "__main__":
    main()
