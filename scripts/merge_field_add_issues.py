#!/usr/bin/env python3
"""Merge open GitHub issues titled/labeled field-add into data/field_adds.geojson."""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / 'data' / 'field_adds.geojson'

def gh_json(args):
    out = subprocess.check_output(['gh', *args], text=True)
    return json.loads(out) if out.strip() else []

def main():
    issues = gh_json(['issue', 'list', '--repo', 'CASCA-code/mapa-purificadoras',
                      '--state', 'open', '--limit', '50', '--json', 'number,title,body,labels'])
    # also catch by title prefix
    picked = []
    for it in issues:
        labels = {l.get('name') for l in (it.get('labels') or [])}
        if 'field-add' in labels or (it.get('title') or '').startswith('field-add:'):
            picked.append(it)
    if not picked:
        print('NO_CHANGES')
        return 0
    fc = {'type': 'FeatureCollection', 'features': []}
    if GEO.exists():
        try:
            fc = json.loads(GEO.read_text(encoding='utf-8'))
        except Exception:
            pass
    if not isinstance(fc.get('features'), list):
        fc = {'type': 'FeatureCollection', 'features': []}
    ids = {f.get('properties', {}).get('id') for f in fc['features'] if f.get('properties')}
    merged = []
    for it in picked:
        body = it.get('body') or ''
        m = re.search(r'```json\s*([\s\S]*?)```', body, re.I)
        if not m:
            print('SKIP no json', it['number'])
            continue
        try:
            feat = json.loads(m.group(1))
        except Exception as e:
            print('SKIP bad json', it['number'], e)
            continue
        if feat.get('type') != 'Feature':
            print('SKIP not feature', it['number'])
            continue
        pid = (feat.get('properties') or {}).get('id')
        if pid and pid in ids:
            print('DUP', pid)
        else:
            fc['features'].append(feat)
            if pid:
                ids.add(pid)
            merged.append((it['number'], feat.get('properties') or {}))
        subprocess.check_call(['gh', 'issue', 'close', str(it['number']),
                               '--repo', 'CASCA-code/mapa-purificadoras',
                               '--comment', 'Mergeado a data/field_adds.geojson (bandeja campo).'])
    GEO.parent.mkdir(exist_ok=True)
    GEO.write_text(json.dumps(fc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('MERGED', len(merged))
    for num, props in merged:
        print(f"ISSUE {num} kind={props.get('kind')} raw={props.get('nota_raw')!r} name={props.get('name')!r}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
