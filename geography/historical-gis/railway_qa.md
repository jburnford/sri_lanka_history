# Railway review, 16 November 2026

I compared the 1893 Ferguson, March 1915 Railway Board, and 1936 Survey Department scans with their layers in [ceylon-history.gpkg](ceylon-history.gpkg) and the project's 12 November 2026 OpenStreetMap snapshot. The review covers the OSM way graph, selected station and bridge locations, conspicuous omissions on each sheet, and whether evidence dates apply to route sections or whole lines. The measurements describe the package at the time of review.

## 1936 priorities

| Priority | Finding | Evidence and proposed correction |
| --- | --- | --- |
| High | **Batticaloa stops short of its station.** | The original Batticaloa inset draws the track into the labeled railway station, with a small spur branching off before the terminal. Retained way `1228988154` ends at OSM node `1895581401` (81.6953004° E, 7.7282928° N). All four mapped stop positions are absent from the selected graph and lie 566–567 m from its nearest node. The modern track path to stop `1895581441` is 568.45 m and uses way `938335798` followed by part of `179212062`. The first way is tagged `service=yard`, which explains why a blanket service filter can break the terminal approach. Add a scoped station connector through the depicted station corridor, retaining OSM geometry provenance and avoiding unrelated yard tracks. The inset supports the historical approach and station, with the exact modern track and switches requiring their own geometry provenance. [1936 Motor Map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~332276~90100738) |
| High | **The Main Line crossing of the Kelani has an omitted span.** | The original sheet depicts the railway crossing the river between the Wattala and Wellampitiya area. The selected graph retains both approaches to OSM span `29481996`, from node `304322093` (79.8895496° E, 6.9558735° N) to `304322095` (79.8897901° E, 6.9534357° N). The OSM span measures **271.04 m**. A route between those exact endpoints in the retained graph measures **26.988 km** because it takes another path. An additional parallel omitted span, `259451398`, is **271.94 m**. Restore one locally continuous alignment first. Use the historical map for the river-crossing location and date, and the modern OSM bridge for the span geometry. Review the date of the physical span and the parallel track separately. [1936 Motor Map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~332276~90100738) |
| High | **Three closed narrow-gauge branches are absent.** | The 1936 railway symbol continues from Avissawella to **Yatiyantota** via Dehiowita and Karawanella, from Avissawella to **Opanake** via Ratnapura, Dela and Kahawatta, and from Nanu Oya to **Ragalla** via Nuwara Eliya and Kandapola. The OSM-derived layer ends at Avissawella and has no Uda Pussellawa geometry. Trace the 1936 symbols, retain the source pixels, and record 762 mm gauge against the printed railway source. The 1915 schematic helps corroborate the Yatiyantota and Ragalla branches and the Kelani Valley route as far as Ratnapura. The OSM snapshot contains two abandoned ways near the Kelani Valley line south of Avissawella, `550674269` and `550887305`, for local comparison. In the Nuwara Eliya area the retrieved non-main-line ways are for the Victoria Park miniature railway. [1936 Motor Map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~332276~90100738), [March 1915 Railway Board map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~328296~90096788) |
| Medium | **Family-wide dates can be mistaken for segment dates.** | Badulla-area OSM ways `102227187` and `417950619` inherit `first_checked_map_year=1893` and `earliest_linked_record_year=1858`. Those dates come from evidence elsewhere on the Main Line. The former dates an earlier mapped reach of the line and the latter dates the first sod near Colombo. The Bandarawela–Badulla opening record is 1924. Preserve the current name and section stamps in `transport_evidence` and `transport_evidence_links`, and treat the dates on individual OSM ways as corridor summaries. Segment dates require links through the named sections. [Official railway history, printed p. 12](https://railway.gov.lk/web/images/pdf/railway_toursim_sri_lanka.pdf#page=12) |
| Lower | **A number of small stubs reflect modern track selection.** | Examples are Northern Line ways `279729359` near Thambuttegama (438.50 m) and `808882862` near Kokuvil (559.70 m), Puttalam Line way `400543366` near Kurana (398.2 m), and a dead end on the secondary Coast Line track north of Kalutara South whose modern continuation is `1159085294` (743.59 m). Another retained route through Kalutara remains continuous. Local modern parallel track can look like a false branch on the historical sheet. Confirm against a station or engineering plan before claiming period sidings and individual trackways. |

The Yatiyantota opening is already recorded in `transport_evidence` on 14 September 1903 and the Uda Pussellawa sections opened in stages in 1903–04. A gazette notice adds a source-backed end date for traffic to Dehiowita, Karawanella and Yatiyantota effective 1 January 1942. The 1939 Gazette index records that Uda Pussellawa passenger service was to cease on 7 January 1940, a date specific to passenger service. The current Dela record is April 1916. The 1936 map is direct evidence for the continuation through Kahawatta to Opanake by the date of the sheet. [Ceylon Government Gazette no. 8,781, 15 August 1941, printed p. 1180](https://diglib.natlib.lk/bitstream/handle/123456789/27986/024_1941-JULY-DECEMBER_8781_I_E.pdf?isAllowed=y&sequence=1), [Ceylon Government Gazette index, July–December 1939, p. xi, referring to printed p. 2186](https://diglib.natlib.lk/bitstream/handle/123456789/27557/001_1939-JULY-DECEMBER_INDEX_I_E.pdf?isAllowed=y&sequence=1)

### Geography and topology that check out

- `rail_1936_osm` has **653 ways, 653 unique stable feature IDs, 16,874 OSM nodes and one connected component**. Its 1,469.509 km is the sum of track-way lengths and includes parallel tracks. All 653 geometries, node lists, version fields and snapshot fields match the corresponding local OSM ways exactly. Of the 653 ways, 639 carry a gauge of 1,676 mm and 14 have no OSM gauge value. On the 32 Kelani Valley candidates the count is 30 broad gauge and two unknown. The 1936 source date and the modern geometry reference timestamp are both present. The layer has a corridor QID on every way and one feature QID directly sourced from an OSM tag.
- Family counts are Main **222**, Coast **156**, Batticaloa **83**, Northern **79**, Kelani Valley **32**, Puttalam **30**, Matale **25**, Mannar **13** and Trincomalee **13**. The Main and Kelani Valley family subgraphs have three and five components. They join when family labels are ignored. The current combined graph reaches at least one exact station stop node at Colombo Fort, Maradana, Matara, Avissawella, Badulla, Maho, Gal Oya, Trincomalee, Matale, Kankesanturai, Ragama, Puttalam, Polgahawela, Medawachchiya and Talaimannar. The 1936 sheet depicts the line from Polonnaruwa to Batticaloa and the branch to Trincomalee. Annual reports document both separately, including the Polonnaruwa–Batticaloa opening for all traffic on 12 March 1928. [1927 Annual General Report, printed pp. 7 and 66](https://archive.org/download/colonial-reports-1927-1378/ColonialReports1927-1378.pdf#page=944)
- Twenty-one ways are labeled as connectivity corrections. Removing them from this version yields 14 components. The corrected ways include 42.905 km on the Mannar Line (three ways), 32.240 km approaching Batticaloa (way `1228988154`) and 18.030 km on the Puttalam Line (way `529041701`). The two gaps the user saw earlier were reported without coordinates. Their correspondence to the repaired ways or current gaps is unresolved.
- The modern Mihintale branch `62005148` is excluded. The original 1936 sheet shows the road east from Anuradhapura in the region of this branch. The map also ends the Coast corridor at Matara, and the modern extension eastward including tunnel way `1184934049` is excluded. The layer retains 285 m beyond the modern Matara stop, so the exact historical terminal limit would benefit from a station plan. The 1936 Puttalam main sheet shows the railway from Mundal through Palavi into town. Its inset confirms that the historic track runs north of the labeled Puttalam Railway Station to a marked terminal. The retained track continues 1.521 km north of the modern stop. The inset supports a continuation beyond the stop, with the historical and modern stop positions requiring a separate comparison. [1936 Motor Map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~332276~90100738)

## Earlier railway layers

| Layer | Finding |
| --- | --- |
| **1915 schematic, 11 traces** | The Ragama–Chilaw trace begins at source-crop pixel `(511,978)` and stops **10.607 km** short of the Main trace in the delivered geometries. The two green lines visibly meet at the Ragama symbol near `(519,979)` in the source crop. Add a verified common source-pixel vertex to the Main and branch traces. The other ten traces intersect to form the second schematic component. The 67.041 km modern Ragama–Chilaw comparison path reaches its exact OSM stops and uses 16 ways. The 1915 map's portrayal and the 1916 dates of opening for goods and all traffic are distinct evidence. [March 1915 Railway Board map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~328296~90096788), [1916 Annual General Report, printed p. 30](https://noolaham.net/project/970/96999/96999.pdf#page=36) |
| **1915 schematic, eastern end** | A short green mark extends past the interpreted Bandarawela endpoint toward the Badulla marking in the original inset. The stroke is small and overlaps other print. Retain the existing endpoint uncertainty and the separately attested 1924 opening to Badulla. Treat any additional pixels traced here as uncertain map depiction. [March 1915 Railway Board map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~328296~90096788), [Official railway history, printed p. 12](https://railway.gov.lk/web/images/pdf/railway_toursim_sri_lanka.pdf#page=12) |
| **1893 Ferguson, five traces** | **Polgahawela–Kurunegala** is missing. The map shows the dash-and-dot constructing symbol north of Polgahawela, then a change to longer dashes beyond Kurunegala. Ferguson's contemporary text confirms construction of the Polgahawela–Kurunegala reach. The continuation should carry a distinct proposal status. **Kandy–Matale** is also missing. The map draws a continuous rail line north from the Kandy area toward Matale around the sheet fold, and the PWD records opening on 4 October 1880. **Galle–Matara** is depicted, with a broken rail line alongside coastal road symbols. Its existing `uncertain` treatment is defensible along the overlapping section and the 1895 opening date is independent. [1893 Ferguson sheet](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~338023~90105863), [Ferguson, Ceylon in 1893, printed p. 20](https://www.columbia.edu/cu/lweb/digital/collections/cul/texts/ldpd_10250911_000/pages/ldpd_10250911_000_00000040.html), [PWD history vol. 1, printed p. xix](https://noolaham.net/project/961/96086/96086.pdf#page=25) |
| **1893 status within a reach** | The Colombo–Galle trace is tagged `made` over its full length. Ferguson's contemporary text distinguishes an open coastal line and the final reach into Galle under construction, and the map carries multiple line styles along that corridor. Review and split the trace at the cartographic change. If the switch cannot be identified confidently, record the overlapping reach as uncertain while preserving the source distinction. [Ferguson, Ceylon in 1893, printed p. 20](https://www.columbia.edu/cu/lweb/digital/collections/cul/texts/ldpd_10250911_000/pages/ldpd_10250911_000_00000040.html) |

### Measured offset and use

Distances below describe coincidence with present-day geometry, which combines georeferencing, drawing generalization and possible alignment changes. The 1893 Ferguson fit assumes WGS 84 for the historical graticule. Its check file reports town-symbol offsets of 4.579 km for Galle and 6.928 km for Kandy. The end of the 1893 Peradeniya–Kandy trace is **7.428 km** from the modern Kandy stop `12656864618`. Its sampled median distance from the modern Matale Line alignment is only **0.848 km**, because the modern Matale Line includes the track through the Kandy area. A distance to the nearest line can therefore overlook an endpoint discrepancy.

I sampled trace vertices plus subdivisions of no more than 1 km in EPSG:32644, measuring to the modern OSM line family under comparison. For 1893 the median/max are **1.01/2.61 km** for Colombo–Peradeniya, **1.82/5.22 km** for Peradeniya–Haputale, and **4.45/6.08 km** for Colombo–Galle. For 1915 they are **6.68/12.98 km** for Main west of Peradeniya, **4.51/12.27 km** for Main east of Peradeniya, **2.65/8.43 km** for Northern, and **3.61/19.64 km** for Coast. Use the 1915 traces as schematic depictions. Their georeferencing records **11.6 km** leave-one-out RMS. I did not score the closed lines against surviving OSM railway because the comparison would measure distance to a different corridor.

Nine named 1936 check points give **0.963 km RMS** (0.290–1.288 km). The individual railway-station checks are 290 m at Polgahawela, 845 m at Maho and 971 m at Nanu Oya. These uncertainties are larger than several of the OSM geometry gaps. The original map supports the presence and connection of the railway corridor in such cases. Use its source marks and station labels to identify the corridor, with OSM node IDs to measure small gaps and preserve alignment provenance. [1893 town checks](../ferguson-1893/town-checks.csv), [1915 controls](rail_1915_controls.tsv), [1936 control points](../motor-map-1936/control-points.csv)

## Reproduce selected checks

Run from the repository root. The commands use the local archive originals. Raster windows are full-resolution `xoff yoff xsize ysize`.

| Original scan | Window or crop |
| --- | --- |
| `10791002.jp2`, 1936 rail legend | `12900 3400 1340 2480` |
| `10791002.jp2`, Batticaloa inset detail | `13920 8940 2420 1560` |
| `10791002.jp2`, main sheet at Batticaloa | `13860 10960 2340 1960` |
| `10791002.jp2`, northern Colombo and Kelani River | `4800 14960 1160 1000` |
| `10791002.jp2`, Puttalam inset | `3040 7200 1360 1460` |
| `10791002.jp2`, Avissawella–Opanake | `6400 15400 3700 2400` |
| `10791002.jp2`, Avissawella–Yatiyantota | `6700 14480 1280 1550` |
| `10791002.jp2`, Nanu Oya–Ragalla | `9200 14980 1300 1340` |
| `11597002.jp2`, Polgahawela–Kurunegala | `3006 6756 632 807` |
| `11597002.jp2`, Kandy–Matale | `3870 6677 512 1048` |
| `11597002.jp2`, Galle–Matara | `2878 10514 1160 544` |
| `13440000.jp2`, 1915 base crop in repo | `8800 17700 2900 3750`. Export at `-outsize 1100 0`. Ragama is then at about `(519,979)`. |

```sh
gdal_translate -srcwin 13920 8940 2420 1560 -of JPEG \
  /mnt/data/jic823/gis/maps/archive_org/dr_survey-department-motor-map-of-ceylon-10791002/10791002.jp2 \
  /tmp/ceylon-batticaloa-rail-inset.jpg
```

The following calculates exact OSM-node topology, WGS 84 geodesic track lengths and the two crossing or terminal tests. Its shortest-path result is independent of distance tolerances or any geometric snapping.

```python
import json
from collections import defaultdict
from heapq import heappop, heappush
from math import inf

from osgeo import ogr
from pyproj import Geod

g = ogr.Open("geography/historical-gis/ceylon-history.gpkg")
o = ogr.Open("kg/spatial/osm-sri-lanka-reference-2026-11-12.gpkg")
geod = Geod(ellps="WGS84")

def load(layer):
    result = {}
    for feature in layer:
        points = feature.GetGeometryRef().GetPoints()
        nodes = json.loads(feature["osm_nodes_json"])
        assert len(points) == len(nodes)
        result[feature["osm_id"]] = nodes, points, feature["osm_version"], feature["snapshot"]
    return result

def graph(ways):
    edges = defaultdict(list)
    lengths = {}
    for way, (nodes, points, _, _) in ways.items():
        lengths[way] = geod.line_length(*zip(*points))
        for u, v, a, b in zip(nodes, nodes[1:], points, points[1:]):
            cost = geod.inv(*a, *b)[2]
            edges[u].append((v, cost))
            edges[v].append((u, cost))
    return edges, lengths

def reach(edges, start):
    distances = {start: 0.0}
    queue = [(0.0, start)]
    while queue:
        dist, node = heappop(queue)
        if dist > distances[node]:
            continue
        for other, length in edges.get(node, []):
            candidate = dist + length
            if candidate < distances.get(other, inf):
                distances[other] = candidate
                heappush(queue, (candidate, other))
    return distances

included = load(g.GetLayerByName("rail_1936_osm"))
source = load(o.GetLayerByName("rail"))
assert all(item == source[way] for way, item in included.items())
edges, lengths = graph(included)
print(len(included), len(edges), len(reach(edges, next(iter(edges)))), sum(lengths.values()))
print("Kelani retained route", reach(edges, 304322093)[304322095])
print("Batticaloa stop present", 1895581441 in edges)
for way in (29481996, 259451398):
    _, points, _, _ = source[way]
    print(way, geod.line_length(*zip(*points)))
extra = {way: source[way] for way in (938335798, 179212062)}
station_edges, _ = graph(extra)
print("Batticaloa station approach", reach(station_edges, 1895581401)[1895581441])
```

The review used selected original scan windows, the full retained OSM way graph, major station stops and available opening or closure records. Individual historical track beds, double-track commissioning dates, switches, station relocations and yards still require local sources.
