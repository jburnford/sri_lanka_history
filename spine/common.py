import json, os, re, unicodedata
from pathlib import Path
HERE = Path(__file__).parent
# Where the sibling projects (col_matching, empire-evolution) are checked out. Default: the repository root, which on
# the workstation is the project folder /home/jic823/Documents/ceylon. Override with CEYLON_PROJECT.
PROJECT = Path(os.environ.get("CEYLON_PROJECT", HERE.parent))
# Large local stores (Tropical Agriculturist corpus, Blue Book PDFs and OCR). Override with CEYLON_DATA.
DATA = Path(os.environ.get("CEYLON_DATA", "/mnt/data/jic823"))
COL = PROJECT / "col_matching/data/kg/graph_stage3"

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

def in_sri_lanka(w):
    """A Wikidata read-back is in Sri Lanka when its country is Sri Lanka (Q854), or, for items with no country such
    as historical polities, when its coordinates fall inside the island. gazetteer/sri_lanka_wikidata.jsonl is NOT
    proof on its own: it also holds about 213 items outside Sri Lanka (countries, oceans, tectonic plates)."""
    if "Q854" in w.get("country", []): return True
    lat, lon = w.get("lat"), w.get("lon")
    return lat is not None and lon is not None and 5.85 <= lat <= 9.9 and 79.5 <= lon <= 81.95

CEYLON_PLACE = re.compile(r"\b(ceylon|colombo|kandy|galle|jaffna|dimbula|dikoya|uva|maskeliya|haputale|dumbara|badulla|matale|"
    r"kegalle|kegalla|ratnapura|kurunegala|nuwara eliya|hatton|kalutara|negombo|trincomalee|batticaloa|sabaragamuwa|kelani|"
    r"kalani|peradeniya|ambagamuwa|udapussellawa|pussellawa|madulsima|passara|bogawantalawa|agrapatana|dolosbage|kotmale|"
    r"hewaheta|pundaluoya|lindula|talawakele|nawalapitiya|gampola|kadugannawa|matara|chilaw|puttalam|anuradhapura|"
    r"polonnaruwa|mannar|vavuniya|mullaitivu|hambantota|ambalangoda)\b")
PLACE_WORD = (r"town|city|village|port|district|province|region|country|island|state|colony|county|parish|estate|garden|"
              r"gardens|park|river|lake|mountain|hill|valley|capital|location|locality|place|suburb|station|settlement|area")

def ceylon_context(roles):
    """True when the journal's own role phrases put the name in Ceylon ('garden in colombo', 'location in dimbula')
    at least as often as anywhere else. Only '<place word> in X' / '<place word>, X' phrases count."""
    cey = other = 0
    for part in roles.split(" | "):
        m = re.match(r"(.*) \((\d+)\)$", part)
        txt, n = (m.group(1), int(m.group(2))) if m else (part, 1)
        for ph in re.findall(rf"\b(?:{PLACE_WORD})\s*(?:in|,)\s+(?:the\s+)?([a-z][a-z .'\-]{{2,40}})", txt.lower()):
            if CEYLON_PLACE.search(ph): cey += n
            else: other += n
    return cey > 0 and cey >= other

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
