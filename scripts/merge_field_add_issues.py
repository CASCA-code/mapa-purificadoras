#!/usr/bin/env python3
"""Merge field-adds from ntfy silent inbox (+ optional GitHub issues) into data/field_adds.geojson."""
import json, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / 'data' / 'field_adds.geojson'
NTFY_TOPIC = 'purif-zmm-campo-casca-v1'
DELETED = ROOT / 'data' / 'field_adds_deleted.json'

def gh_json(args):
    try:
        out = subprocess.check_output(['gh', *args], text=True, stderr=subprocess.DEVNULL)
        return json.loads(out) if out.strip() else []
    except Exception:
        return []

def load_fc():
    fc = {'type': 'FeatureCollection', 'features': []}
    if GEO.exists():
        try:
            fc = json.loads(GEO.read_text(encoding='utf-8'))
        except Exception:
            pass
    if not isinstance(fc.get('features'), list):
        fc = {'type': 'FeatureCollection', 'features': []}
    return fc

def load_deleted():
    if DELETED.exists():
        try:
            return set(json.loads(DELETED.read_text(encoding='utf-8')))
        except Exception:
            return set()
    return set()

def save_deleted(s):
    DELETED.parent.mkdir(exist_ok=True)
    DELETED.write_text(json.dumps(sorted(s), indent=2) + '\n', encoding='utf-8')

def fetch_ntfy():
    url = f'https://ntfy.sh/{NTFY_TOPIC}/json?poll=1&since=all'
    req = urllib.request.Request(url, headers={'User-Agent': 'PurificadorMap/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode('utf-8', 'replace')
    except Exception as e:
        print('ntfy fail', e)
        return []
    out = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        # message body may be the JSON we posted
        body = msg.get('message') or msg.get('event') or ''
        if isinstance(body, dict):
            out.append(body)
            continue
        if not isinstance(body, str):
            continue
        try:
            out.append(json.loads(body))
        except Exception:
            # sometimes double-encoded
            try:
                out.append(json.loads(body.strip('"')))
            except Exception:
                pass
    return out

def main():
    fc = load_fc()
    deleted = load_deleted()
    ids = {f.get('properties', {}).get('id') for f in fc['features'] if f.get('properties')}
    changed = False
    merged = []

    for payload in fetch_ntfy():
        if not isinstance(payload, dict):
            continue
        action = payload.get('action')
        if action == 'delete':
            did = payload.get('id')
            if did:
                deleted.add(did)
                before = len(fc['features'])
                fc['features'] = [f for f in fc['features'] if (f.get('properties') or {}).get('id') != did]
                if len(fc['features']) != before:
                    changed = True
                    merged.append(('delete', did, {}))
                ids.discard(did)
            continue
        feat = payload.get('feature') if action == 'upsert' else payload
        if isinstance(feat, dict) and feat.get('type') == 'Feature':
            props = feat.get('properties') or {}
            pid = props.get('id')
            if pid and pid in deleted:
                continue
            if pid and pid in ids:
                # replace existing
                fc['features'] = [f for f in fc['features'] if (f.get('properties') or {}).get('id') != pid]
                fc['features'].append(feat)
                changed = True
                merged.append(('update', pid, props))
                continue
            fc['features'].append(feat)
            if pid:
                ids.add(pid)
            changed = True
            merged.append(('upsert', pid, props))

    # optional legacy github issues
    issues = gh_json(['issue', 'list', '--repo', 'CASCA-code/mapa-purificadoras',
                      '--state', 'open', '--limit', '50', '--json', 'number,title,body,labels'])
    for it in issues:
        labels = {l.get('name') for l in (it.get('labels') or [])}
        if 'field-add' not in labels and not (it.get('title') or '').startswith('field-add:'):
            continue
        body = it.get('body') or ''
        m = re.search(r'```json\s*([\s\S]*?)```', body, re.I)
        if not m:
            continue
        try:
            feat = json.loads(m.group(1))
        except Exception:
            continue
        if feat.get('type') != 'Feature':
            continue
        pid = (feat.get('properties') or {}).get('id')
        if pid and pid in deleted:
            continue
        if pid and pid in ids:
            pass
        else:
            fc['features'].append(feat)
            if pid:
                ids.add(pid)
            changed = True
            merged.append(('issue', pid, feat.get('properties') or {}))
        try:
            subprocess.check_call(['gh', 'issue', 'close', str(it['number']),
                                   '--repo', 'CASCA-code/mapa-purificadoras',
                                   '--comment', 'Mergeado a data/field_adds.geojson.'])
        except Exception:
            pass

    # apply deleted filter once more
    if deleted:
        fc['features'] = [f for f in fc['features'] if (f.get('properties') or {}).get('id') not in deleted]

    if not changed and not merged:
        print('NO_CHANGES')
        return 0

    GEO.parent.mkdir(exist_ok=True)
    GEO.write_text(json.dumps(fc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    save_deleted(deleted)
    print('MERGED', len(merged))
    for kind, pid, props in merged:
        print(f'{kind} id={pid} name={props.get("name")!r} raw={props.get("nota_raw")!r} type={props.get("kind")!r}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
