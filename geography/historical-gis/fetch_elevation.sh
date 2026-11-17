#!/bin/bash
# Rebuild the SRTM 30 m elevation and hillshade for Sri Lanka (about 500 MB) in geography/elevation/srtm_30m.
# Source: Tilezen terrain tiles on the public AWS mirror (SRTM over land).
# Attribution: https://github.com/tilezen/joerd/blob/master/docs/attribution.md
set -euo pipefail
out="$(cd "$(dirname "$0")/.." && pwd)/elevation/srtm_30m"
mkdir -p "$out" && cd "$out"
for lat in 05 06 07 08 09; do
  for lon in 079 080 081; do
    tile="N${lat}E${lon}.hgt"
    [ -f "$tile" ] || curl -sSf "https://s3.amazonaws.com/elevation-tiles-prod/skadi/N${lat}/${tile}.gz" | gunzip > "$tile"
  done
done
gdalbuildvrt -q mosaic.vrt N*.hgt
gdalwarp -q -overwrite -te 79.4 5.8 82.0 10.0 -co COMPRESS=DEFLATE -co TILED=YES mosaic.vrt cut.tif
# Sea and anything at or below 0 m become no data.
gdal_calc.py --quiet --overwrite -A cut.tif --calc="where(A<=0,-32768,A)" --NoDataValue=-32768 --type=Int16 \
  --co COMPRESS=DEFLATE --co TILED=YES --outfile=ceylon_srtm_30m.tif
gdaldem hillshade -q -multidirectional -z 3 -s 111120 -co COMPRESS=DEFLATE -co TILED=YES \
  ceylon_srtm_30m.tif ceylon_srtm_30m_hillshade.tif
rm -f mosaic.vrt cut.tif
echo "Elevation written to $out"
