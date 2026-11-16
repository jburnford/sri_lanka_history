"""Year-aware polity resolution over the Empire Evolution graph.

A territory row is one polity with dates. Lineage relationships (EVOLVED_INTO, INCORPORATED_INTO, SUCCEEDED,
PARTITIONED_INTO, FEDERATED_INTO, ...) connect it to what came before, after, or contained it. Given a
territory and a year, polity_at() returns the nearest territory in that lineage whose dates contain the year,
with the path that got there. Nothing is overwritten: the caller keeps the original item and adds the polity.
"""
import collections, csv, re
from pathlib import Path
DATA = Path("/home/jic823/Documents/ceylon/empire-evolution/data")
EDGE = re.compile(r"MATCH \(a:HistoricalTerritory \{colony_id: '([^']+)'\}\), \(b:HistoricalTerritory \{colony_id: '([^']+)'\}\) MERGE \(a\)-\[:([A-Z_]+)")
CONTEXT_ONLY = {"BORDERS_WITH", "NEAR_COAST_OF", "WAS_MEMBER_OF"}   # not lineage

class Empire:
    def __init__(self):
        self.terr, self.by_qid = {}, collections.defaultdict(list)
        cy_end = {}
        for m in re.finditer(r"MERGE \(c:[A-Za-z:]+ \{colony_id: '([^']+)'\}\)\s*SET c \+= \{(.*?)\n\}", open(DATA / "britishempire_kg_export.cypher").read(), re.S):
            iy = re.search(r"^\s+independence_year: (\d{4})", m.group(2), re.M)
            if iy: cy_end[m.group(1)] = int(iy.group(1))
        for r in csv.DictReader(open(DATA / "qid_manifest.tsv"), delimiter="\t"):
            y0 = int(r["established_year"]) if r["established_year"].strip().lstrip("-").isdigit() else None
            y1 = int(r["end_date"][:4]) if r["end_date"][:4].isdigit() else None
            end_source = "manifest end_date" if y1 else None
            if y1 is None:                                  # the manifest leaves 505 of 739 end dates empty; the graph export
                iy = cy_end.get(r["colony_id"])             # carries independence_year for 330 of them
                if iy and (y0 is None or iy > y0): y1, end_source = iy, "graph independence_year"
            t = {"id": r["colony_id"], "name": r["name"] or r["canonical_name"], "qid": r["wikidata_id"].strip() or None, "start": y0, "end": y1,
                 "type": r["colony_type"], "end_source": end_source}
            self.terr[t["id"]] = t
            if t["qid"]: self.by_qid[t["qid"]].append(t["id"])
        self.adj = collections.defaultdict(list)
        for line in open(DATA / "britishempire_kg_export.cypher"):
            m = EDGE.search(line)
            if not m or m.group(3) in CONTEXT_ONLY: continue
            a, b, rel = m.groups()
            self.adj[a].append((b, rel, "out")); self.adj[b].append((a, rel, "in"))

    def covers(self, tid, y0, y1):
        t = self.terr[tid]
        return (t["start"] is None or y1 >= t["start"]) and (t["end"] is None or y0 <= t["end"])

    def polity_at(self, qid, y0, y1=None, max_hops=4):
        """-> (territory dict, path list, hops) or (None, [], None). hops == 0 means the item itself is in date."""
        y1 = y1 or y0
        starts = self.by_qid.get(qid, [])
        for s in starts:
            if self.covers(s, y0, y1): return self.terr[s], [], 0
        seen, frontier = set(starts), [(s, []) for s in starts]
        for hop in range(1, max_hops + 1):
            nxt, hits = [], []
            for tid, path in frontier:
                for other, rel, direction in self.adj.get(tid, []):
                    if other in seen or other not in self.terr: continue
                    seen.add(other)
                    p = path + [f"{self.terr[tid]['name']} {'-' if direction == 'out' else '<-'}[{rel}]{'->' if direction == 'out' else '-'} {self.terr[other]['name']}"]
                    if self.covers(other, y0, y1): hits.append((self.terr[other], p))
                    nxt.append((other, p))
            if hits:
                # Several territories at the same distance all cover the year (Australia before 1901 reaches six
                # colonies). Picking one would invent a fact, so the answer is "no single polity".
                if len({h[0]["id"] for h in hits}) > 1: return None, [f"ambiguous: {len(hits)} territories cover {y0}"], None
                return hits[0][0], hits[0][1], hop
            frontier = nxt
        return None, [], None
