import json, re, unicodedata
from pathlib import Path
HERE = Path(__file__).parent
COL = Path("/home/jic823/Documents/ceylon/col_matching/data/kg/graph_stage3")

def key(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return re.sub(r"^the ", "", s)

def read_names(t):
    rows = []
    with open(HERE / "names" / f"{t}.tsv") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for l in fh:
            r = dict(zip(head, l.rstrip("\n").split("\t")))
            r["records"] = int(r["records"]); r["articles"] = int(r["articles"])
            rows.append(r)
    return rows

def read_jsonl(p):
    with open(p) as fh:
        return [json.loads(l) for l in fh if l.strip()]

def wd_names(w):
    n = {key(v) for v in w.get("labels", {}).values()}
    for al in w.get("aliases", {}).values(): n |= {key(a) for a in al}
    return n - {""}

SETTLEMENT = re.compile(r"\b(city|town|port|village|capital|suburb|settlement|municipality)\b")
POLITY = re.compile(r"\b(colony|presidency|protectorate|province|state|country|kingdom|possession|territor|dominion|empire|rule|monarchy|khedivate|administrative unit)")

def role_class(roles):
    """Coarse class of how the journal uses a name, from the extractor's role phrases (weighted by count)."""
    s = p = 0
    for part in roles.split(" | "):
        m = re.match(r"(.*) \((\d+)\)$", part)
        if not m: continue
        txt, n = m.group(1), int(m.group(2))
        if re.search(r"\b(city|town|port|village)\b", txt): s += n
        if re.search(r"\b(colony|presidency|province|state|country|protectorate|district|region|island|continent)\b", txt): p += n
    return "settlement" if s > 2 * p and s else "area" if p > 2 * s and p else "mixed"
