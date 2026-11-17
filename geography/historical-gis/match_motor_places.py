#!/usr/bin/env python3
"""Match places named in the 1936 Motor Map margins to modern gazetteer coordinates."""
import csv
import json
from pathlib import Path
import re
import unicodedata

HERE = Path(__file__).resolve().parent
GAZETTEER = HERE.parent.parent / 'spine/gazetteer/sri_lanka_wikidata.jsonl'
REPRESENTATIVE = {
    'Alutgama': 'Q4737582', 'Alutgama:station': 'Q20717422',
    'Batticaloa': 'Q810963', 'Chavakachcheri': 'Q1068504',
    'Colombo Fort:station': 'Q5471883', 'Dehiwala': 'Q28197113',
    'Dambulla': 'Q377343', 'Galagedara': 'Q5517872',
    'Gampaha': 'Q2616818', 'Habarane': 'Q5636630', 'Haputale': 'Q3533257',
    'Kadawata': 'Q2041605', 'Kankesanturai': 'Q531494', 'Kegalla': 'Q1968268',
    'Maha Oya': 'Q105200529', 'Mankulam': 'Q12987409', 'Medawachchiya:station': 'Q6805158',
    'Mount Lavinia': 'Q28446872', 'Mullaittivu': 'Q507144', 'Nattandiya': 'Q27963446',
    'Pallai': 'Q7127723', 'Passara': 'Q28653519', 'Sigiriya': 'Q7512155',
    'Talaimannar Pier': 'Q667664', 'Teldeniya': 'Q7695692', 'Wattala': 'Q7974929',
    'Yatiyantota': 'Q8050255',
}
VARIANTS = {
    'Belihul Oya': 'Belihuloya', 'Chavakachcheri': 'Chavakacheri', 'Horewupotana': 'Horowupotana',
    'Narammale': 'Narammala', 'Mutur': 'Muttur', 'Piliyandara': 'Piliyandala',
    'Tangalla': 'Tangalle',
}
# Multiple same-name places, broad features and conflicting candidate coordinates need local review.
HOLD = {
    'Alutnuwara', 'Ambalantota', 'Hakmana', 'Kahawatta', 'Kalkuda', 'Kochchikade',
    'Kosgama', 'Kotiyagala', 'Maho', 'Mahagama', 'Madampe', 'Manampitiya', 'Peradeniya (New)',
    'Puwakpitiya', 'Thiriwanaketiya', 'Weke', 'Yangala',
}
# The Wikidata coordinate for these items is several km from the settlement. Each was compared with the
# GeoNames populated place of the same name (17 November 2026); the GeoNames point is used in its place.
# QID: (lon, lat, GeoNames id, distance of the Wikidata coordinate in km)
COORDINATE_REVIEW = {
    'Q12976928': (80.4068, 6.9966, '1239978', 48.4),    # Kitulgala: Wikidata has 6.59, 80.25 (6°59′, 80°25′ as decimals)
    'Q14220105': (79.75988, 8.22873, '1242089', 8.4),   # Kalpitiya
    'Q7194068': (79.9249, 6.7999, '1230224', 6.2),      # Piliyandala
}
SETTLEMENTS = {'Q486972', 'Q515', 'Q3957', 'Q532', 'Q123705', 'Q253019', 'Q148469'}


def read(name):
    with (HERE / (name + '.tsv')).open(encoding='utf-8', newline='') as file:
        return list(csv.DictReader(file, delimiter='\t'))


def normalize(text):
    return ''.join(ch for ch in unicodedata.normalize('NFKD', text.casefold())
                   if ch.isascii() and ch.isalnum())


def main():
    places, stations, by_id = {}, {}, {}
    with GAZETTEER.open(encoding='utf-8') as file:
        for line in file:
            data = json.loads(line)
            if data.get('lon') is None or data.get('lat') is None:
                continue
            if not 79.5 <= data['lon'] <= 82.2 or not 5.8 <= data['lat'] <= 10:
                continue
            label = data['labels'].get('en') or data['labels'].get('mul') or ''
            types = set(data.get('instance_of', []))
            by_id[data['qid']] = (data, label)
            if types & SETTLEMENTS:
                places.setdefault(normalize(label), []).append(data['qid'])
            if 'Q55488' in types:
                short = re.sub(r'\s+(?:railway\s+)?station$', '', label, flags=re.I)
                stations.setdefault(normalize(short), []).append(data['qid'])

    listings = read('motor_map_1936_transport_listings')
    listings.extend(dict(row, facility_kind='rest_house') for row in read('motor_map_1936_resthouses'))
    fields = ('feature_id', 'place_qid', 'anchor_name', 'lon', 'lat', 'match_method',
              'location_role', 'gazetteer_snapshot', 'geonames_id', 'coordinate_note')
    out = []
    for row in listings:
        name = row['place_as_printed']
        station = row['facility_kind'] == 'railway_car_booking'
        key = normalize(VARIANTS.get(name, name))
        station_override = REPRESENTATIVE.get(f'{name}:station') if station else None
        candidates = (stations.get(normalize(name)) or stations.get(key, [])) if station else []
        qid = station_override or (candidates[0] if len(candidates) == 1 else None)
        role = 'modern station named in the listing'
        method = 'reviewed historical spelling or station name' if station_override else 'unique station name'
        if qid is None and name not in HOLD:
            candidate = places.get(key, [])
            override = REPRESENTATIVE.get(name)
            qid = override or (candidate[0] if len(candidate) == 1 else None)
            role = 'representative modern locality'
            method = 'reviewed named locality' if override else 'unique settlement name'
        if not qid or qid not in by_id:
            continue
        data, label = by_id[qid]
        lon, lat, geonames_id, note = data['lon'], data['lat'], '', ''
        if qid in COORDINATE_REVIEW:
            lon, lat, geonames_id, off = COORDINATE_REVIEW[qid]
            note = (f"Wikidata coordinate ({data['lon']}, {data['lat']}) lies {off} km from the settlement; "
                    f'the GeoNames populated place is used')
        out.append(dict(feature_id=row['feature_id'], place_qid=qid, anchor_name=label,
                        lon=lon, lat=lat, match_method=method,
                        location_role=role, gazetteer_snapshot='2026-11-16',
                        geonames_id=geonames_id, coordinate_note=note))
    with (HERE / 'motor_1936_place_matches.tsv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(out)


if __name__ == '__main__':
    main()
