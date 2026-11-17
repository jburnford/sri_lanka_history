"""Year-aware polity resolution over the Empire Evolution graph.

A territory row is one polity with dates. Lineage relationships (EVOLVED_INTO, INCORPORATED_INTO, SUCCEEDED,
PARTITIONED_INTO, FEDERATED_INTO, ...) connect it to what came before, after, or contained it. Given a
territory and a year, polity_at() returns the nearest territory in that lineage whose dates contain the year,
with the path that got there. Nothing is overwritten: the caller keeps the original item and adds the polity.

The walk follows succession only, in one direction of time: to predecessors when the year is before the
territory began, to successors when it is after the territory ended, and never back again. Containment
(PART_OF, WAS_MEMBER_OF) is not used to answer for a year outside the territory's own dates, because the graph does
not date those links; ADMINISTERED_UNDER (princely states under the Raj) is used only as a last resort, when the
container itself covers the year. Without these two rules a walk could jump sideways into a sibling
(Singapore 1900 -> Malaysia -> Labuan) or borrow a container from the wrong period (Newfoundland and Labrador,
a province from 1949, -> Dominion of Canada for 1900). The walk also stops at a merge (going back) or a split
(going forward), because the dates cannot say which branch was this place (Penang 1950 reaches the Straits
Settlements, which split into the Malayan Union and Singapore), unless one branch is the same Wikidata item as the
starting territory. When nothing is reached the answer is None, not a guess.
"""
import collections, csv, re
from pathlib import Path
from common import PROJECT
DATA = PROJECT / "empire-evolution/data"
EDGE = re.compile(r"MATCH \(a:HistoricalTerritory \{colony_id: '([^']+)'\}\), \(b:HistoricalTerritory \{colony_id: '([^']+)'\}\) MERGE \(a\)-\[:([A-Z_]+)")
CONTEXT_ONLY = {"BORDERS_WITH", "NEAR_COAST_OF", "WAS_MEMBER_OF"}   # not lineage
CONTAINMENT = {"PART_OF", "ADMINISTERED_UNDER"}                     # contemporaneous, undated: not a succession
BACKWARD = {"SUCCEEDED"}                                            # a -[SUCCEEDED]-> b: b came first
# every other lineage type, a -[REL]-> b, means b followed a (EVOLVED_INTO, BECAME_*, MERGED_INTO, PARTITIONED_INTO,
# FEDERATED_INTO, INCORPORATED_INTO, REORGANIZED_AS, TRANSFERRED_*)

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
        self.adj = collections.defaultdict(list)                     # all lineage edges, either way (kept for callers)
        self.later, self.earlier = collections.defaultdict(list), collections.defaultdict(list)   # succession only
        for line in open(DATA / "britishempire_kg_export.cypher"):
            m = EDGE.search(line)
            if not m or m.group(3) in CONTEXT_ONLY: continue
            a, b, rel = m.groups()
            self.adj[a].append((b, rel, "out")); self.adj[b].append((a, rel, "in"))
            if rel in CONTAINMENT: continue
            first, then = (b, a) if rel in BACKWARD else (a, b)
            self.later[first].append((then, rel)); self.earlier[then].append((first, rel))

    def covers(self, tid, y0, y1):
        t = self.terr[tid]
        return (t["start"] is None or y1 >= t["start"]) and (t["end"] is None or y0 <= t["end"])

    def polity_at(self, qid, y0, y1=None, max_hops=4):
        """-> (territory dict, path list, hops) or (None, [], None). hops == 0 means the item itself is in date."""
        y1 = y1 or y0
        starts = self.by_qid.get(qid, [])
        for s in starts:
            if self.covers(s, y0, y1): return self.terr[s], [], 0
        frontier = []
        for s in starts:                       # which way in time each starting territory has to go
            t = self.terr[s]
            if t["start"] is not None and y1 < t["start"]: frontier.append((s, [], "earlier"))
            elif t["end"] is not None and y0 > t["end"]: frontier.append((s, [], "later"))
        seen, branch = set(starts), None
        for hop in range(1, max_hops + 1):
            nxt, hits = [], []
            for tid, path, way in frontier:
                links = (self.earlier if way == "earlier" else self.later).get(tid, [])
                # past the start, a merge (going back) or a split (going forward) is a branch the dates cannot choose:
                # Malaysia's predecessors include Labuan and Sarawak, not only Singapore's own past. Follow a branch only when it is the same Wikidata item as where we started (the
                # Federation of Rhodesia and Nyasaland -> "Northern Rhodesia", same QID as Northern Rhodesia Colony).
                # (not at the starting territory itself: New South Wales (Original) is followed both by the colonies
                # cut out of it and by the Commonwealth, and the dates pick correctly there)
                if path and len({o for o, _ in links}) > 1:
                    same = [(o, r) for o, r in links if o in self.terr and self.terr[o]["qid"] == qid]
                    if len({o for o, _ in same}) == 1: links = same
                    else: branch = branch or self.terr[tid]["name"]; continue
                for other, rel in links:
                    if other in seen or other not in self.terr: continue
                    seen.add(other)
                    p = path + [f"{self.terr[tid]['name']} {'<- follows -' if way == 'earlier' else '- followed by ->'} {self.terr[other]['name']} [{rel}]"]
                    if self.covers(other, y0, y1): hits.append((self.terr[other], p))
                    nxt.append((other, p, way))
            if hits:
                # Several territories at the same distance all cover the year (Australia before 1901 reaches six
                # colonies). Picking one would invent a fact, so the answer is "no single polity".
                if len({h[0]["id"] for h in hits}) > 1: return None, [f"ambiguous: {len(hits)} territories cover {y0}"], None
                return hits[0][0], hits[0][1], hop
            frontier = nxt
        # last resort: a princely state "administered under" the Raj (or a Gold Coast territory under its colony) is
        # under that container in any year the container covers, including after the state lapsed or was annexed.
        # PART_OF is not used: the graph does not date it (Newfoundland and Labrador is PART_OF Canada only from 1949).
        cont = {o for s in starts for o, rel, d in self.adj.get(s, []) if d == "out" and rel == "ADMINISTERED_UNDER"
                and o in self.terr and self.covers(o, y0, y1)}
        if len(cont) == 1:
            o = cont.pop()
            return self.terr[o], [f"{self.terr[starts[0]]['name']} administered under {self.terr[o]['name']} [ADMINISTERED_UNDER]"], 1
        return None, ([f"lineage branches at {branch}"] if branch else []), None
