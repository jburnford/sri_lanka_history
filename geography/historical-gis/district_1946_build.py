#!/usr/bin/env python3
"""Polygonize a hand trace of the district map accompanying the 1946 census."""

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from osgeo import ogr


HERE = Path(__file__).resolve().parent
SOURCE_URL = "https://noolaham.net/project/1018/101739/101739.pdf#page=59"


def read_tsv(name):
    with (HERE / name).open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def cartesian_errors(points, expected):
    offset = points - expected
    east = offset[..., 0] * 111.2 * np.cos(np.radians(expected[..., 1]))
    north = offset[..., 1] * 111.2
    return np.hypot(east, north)


def register():
    controls = read_tsv("district_1946_controls.tsv")
    xy = np.array([[float(row["x"]), float(row["y"]), 1] for row in controls])
    lonlat = np.array([[float(row["lon"]), float(row["lat"])] for row in controls])
    fit = np.array([row["role"] == "fit" for row in controls])

    params = np.linalg.lstsq(xy[fit], lonlat[fit], rcond=None)[0]
    errors = cartesian_errors(xy @ params, lonlat)
    cross_validation = []
    for idx in np.flatnonzero(fit):
        holdout = fit.copy()
        holdout[idx] = False
        remaining = np.linalg.lstsq(xy[holdout], lonlat[holdout], rcond=None)[0]
        cross_validation.append(cartesian_errors(xy[idx] @ remaining, lonlat[idx]))
    stats = {
        "fit_count": int(fit.sum()),
        "fit_rmse_km": round(float(np.sqrt(np.mean(errors[fit] ** 2))), 2),
        "fit_loo_rmse_km": round(float(np.sqrt(np.mean(np.square(cross_validation)))), 2),
        "check_errors_km": {
            row["name"]: round(float(errors[i]), 2)
            for i, row in enumerate(controls) if not fit[i]
        },
    }
    return params, stats


def polygonize():
    linework = ogr.Geometry(ogr.wkbMultiLineString)
    for row in (HERE / "district_1946_edges.txt").read_text().splitlines():
        if not row or row.startswith("#"):
            continue
        _, *pairs = row.split()
        vertices = [tuple(map(int, value.split(","))) for value in pairs]
        for (x1, y1), (x2, y2) in zip(vertices, vertices[1:]):
            line = ogr.Geometry(ogr.wkbLineString)
            line.AddPoint_2D(x1, y1)
            line.AddPoint_2D(x2, y2)
            linework.AddGeometry(line)
    if not linework.IsSimple():
        raise ValueError("The pixel trace contains an un-noded intersection.")
    polygon_collection = linework.Polygonize()
    faces = [part.Clone() for part in polygon_collection]
    if any(not face.IsValid() for face in faces):
        raise ValueError("Polygonization produced invalid faces.")
    return faces


def rings(polygon, params):
    coordinates = []
    for index, ring in enumerate(polygon):
        xy = [(point[0], point[1], 1) for point in ring.GetPoints()]
        points = np.round(np.array(xy) @ params, 8).tolist()
        signed_area = sum(
            x1 * y2 - x2 * y1
            for (x1, y1), (x2, y2) in zip(points, points[1:])
        )
        if (signed_area > 0) != (index == 0):
            points.reverse()
        coordinates.append(points)
    return coordinates


def main():
    ogr.UseExceptions()
    params, stats = register()
    faces = polygonize()
    matched = set()
    parts = defaultdict(list)
    names = {}
    for seed in read_tsv("district_1946_faces.tsv"):
        marker = ogr.Geometry(ogr.wkbPoint)
        marker.AddPoint_2D(float(seed["x"]), float(seed["y"]))
        hits = [idx for idx, face in enumerate(faces) if face.Contains(marker)]
        if len(hits) != 1 or hits[0] in matched:
            raise ValueError(f"District seed does not uniquely identify a face: {seed}")
        idx = hits[0]
        matched.add(idx)
        feature_id = seed["feature_id"]
        names[feature_id] = seed["name"]
        parts[feature_id].append(rings(faces[idx], params))
    if len(matched) != len(faces) or len(parts) != 20:
        raise ValueError("Expected all faces in the twenty named districts.")

    features = []
    for feature_id, polygons in sorted(parts.items()):
        feature = {
            "type": "Feature",
            "properties": {
                "feature_id": feature_id,
                "name": names[feature_id],
                "represented_date": "1946",
                "represented_date_basis": "Census year inferred from report context",
                "published_date": "1950-07",
                "source_id": "census-1946-final",
                "source_page": "Map facing printed p. 30, PDF p. 59",
                "source_url": SOURCE_URL,
                "geometry_method": "Hand trace of small-scale Survey Department sheet, affine fit",
                "geometry_use": "Generalized display. Some small islands and inland coastal waters are simplified.",
                "fit_rmse_km": stats["fit_rmse_km"],
                "fit_loo_rmse_km": stats["fit_loo_rmse_km"],
            },
            "geometry": {"type": "MultiPolygon", "coordinates": polygons},
        }
        if not ogr.CreateGeometryFromJson(json.dumps(feature["geometry"])).IsValid():
            raise ValueError(f"Invalid WGS84 geometry: {feature_id}")
        features.append(feature)
    with (HERE / "district_1946.geojson").open("w", encoding="utf-8") as stream:
        json.dump({"type": "FeatureCollection", "features": features}, stream, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
