#!/usr/bin/env python3
"""TOOLING: bounded official regulatory-vector intake; no model writes."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'data/validation/goslar_multiriver_regulatory'
TMP = ROOT / 'data/tmp/goslar_multiriver_regulatory'
SERVICE = 'https://www.umweltkarten-niedersachsen.de/arcgis/rest/services/HWSchutz_wms/MapServer'
BBOX = '10.2,51.7,10.8,52.1'
SOURCES = [
    ('Ecker', 39, 691, 'Ecker', '2015-05-13'),
    ('Schamlah', 39, 632, 'Schamlahbach', '2014-09-03'),
    ('Oker', 40, 793, 'Oker-6 Stadt Goslar', '2017-05-02'),
    ('Innerste', 40, 792, 'Innerste-5 Stadt Goslar', '2017-05-02'),
]

def fetch(url, params):
    request_url = url + '?' + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request_url, timeout=45) as response:
                raw = response.read()
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1 + attempt)
    obj = json.loads(raw)
    if 'error' in obj or obj.get('exceededTransferLimit'):
        raise RuntimeError(f'Incomplete or failed response {request_url}: {obj.get("error")}')
    return obj, raw, request_url

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    manifest = {
        'dataset_id': 'goslar_multiriver_regulatory', 'claim_level': 'diagnostic_only',
        'accessed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'selection_envelope_wgs84': BBOX, 'geometry_clipped': False,
        'coverage_denominator': 'complete selected official features; not entire river',
        'licence': 'No explicit reuse licence in layer metadata; local diagnostic use, redistribution not approved',
        'sources': [], 'failures': [],
    }
    features = []
    for river, layer, uid, name, date in SOURCES:
        params = {'f':'geojson', 'where':f'uesg_id={uid}', 'outFields':'*',
                  'geometry':BBOX, 'geometryType':'esriGeometryEnvelope', 'inSR':4326,
                  'spatialRel':'esriSpatialRelIntersects', 'returnGeometry':'true', 'outSR':4326}
        try:
            metadata, meta_raw, meta_url = fetch(f'{SERVICE}/{layer}', {'f':'json'})
            (DEST / f'layer_{layer}_metadata.json').write_bytes(meta_raw)
            obj, raw, url = fetch(f'{SERVICE}/{layer}/query', params)
            fs = obj.get('features', [])
            if len(fs) != 1 or fs[0]['properties']['uesg_gn'] != name:
                raise RuntimeError(f'Expected one {name} feature, found {[x.get("properties") for x in fs]}')
            if not fs[0].get('geometry') or fs[0]['geometry']['type'] not in ('Polygon','MultiPolygon'):
                raise RuntimeError('Missing or non-polygon geometry')
            path = DEST / f'{river.lower()}_regulatory.geojson'
            temporary = TMP / path.name
            temporary.write_bytes(raw)
            temporary.replace(path)
            props = fs[0]['properties']
            effective = dt.datetime.fromtimestamp(props['von_datum']/1000, dt.timezone.utc).date().isoformat()
            manifest['sources'].append({'river':river, 'layer':layer, 'uesg_id':uid,
                'file':str(path.relative_to(ROOT)), 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest(),
                'url':url, 'request_params':params, 'layer_metadata_url':meta_url,
                'copyright':metadata.get('copyrightText'), 'webpage_announcement_date':date,
                'server_effective_date':effective, 'feature_attributes':props})
            for feature in fs:
                feature['properties'] = dict(feature['properties'], source_layer=layer, river=river, webpage_announcement_date=date)
            features.extend(fs)
        except Exception as exc:
            manifest['failures'].append({'river':river, 'params':params, 'error':str(exc)})
    combined = DEST / 'regulatory_features.geojson'
    combined.write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False))
    manifest['combined_file'] = str(combined.relative_to(ROOT))
    manifest['combined_sha256'] = hashlib.sha256(combined.read_bytes()).hexdigest()
    (DEST/'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({'features':len(features),'failures':manifest['failures'],'manifest':str((DEST/'source_manifest.json').relative_to(ROOT))}))
    if manifest['failures']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
