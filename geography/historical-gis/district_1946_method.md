# District boundaries in the 1946 census report

The 20 geometries trace the Survey Department’s *Ceylon showing Provinces and Districts*, printed July 1950. The map faces page 30 of A. G. Ranasinha’s *Census of Ceylon 1946*, Volume I, Part I, *General Report*. The 1946 representation date comes from the census context. The plate itself gives a July 1950 publication date. The plate and Table 97 both distinguish Chilaw and Puttalam. [Map scan, PDF page 59](https://noolaham.net/project/1018/101739/101739.pdf#page=59)

The trace follows the centre of each printed boundary, with one shared edge for adjoining districts. The linework simplifies the map’s coastline and coastal lagoons, and includes the named outer islands drawn off Jaffna and the island of Mannar. Coast and boundaries come from the same plate. The map is suitable for island-scale display.

Pixel coordinates use the full PDF page rendered at 160 dpi (1354 × 1698), with the origin at the top left. The command `pdftoppm -singlefile -png -r 160 -f 59 101739.pdf district1946` recreates that reference image. `district_1946_edges.txt` holds the hand-traced vertices. `district_1946_faces.tsv` assigns each polygonized face to the published district name and a persistent census feature ID. `district_1946_controls.tsv` lists the settlement marks and reference coordinates used to register the image, with a GeoNames locator for each coordinate.

The affine fit had an RMS residual of 2.72 km across 14 controls and 3.41 km when each was withheld in turn. Three withheld tentative correspondences at Matara, Badulla and Batticaloa differed by 10.18–13.82 km. Those locations indicate the limits of the positional check.

Run `/usr/bin/python3 district_1946_build.py` to regenerate the GeoJSON using GDAL/OGR with GEOS and NumPy. The build polygonizes all 28 mainland and island faces, assigns them to 20 district multipolygons, and checks validity. Each district ID joins to `census_units`. Modern Wikidata identifiers in that registry link corresponding named entities. The historical feature IDs remain stable across boundary edits and Wikidata matches.
