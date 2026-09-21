#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/extension-dist/purificadoras-scout-ext.zip"
mkdir -p "$ROOT/extension-dist"
rm -f "$OUT"
python3 - << PY
import zipfile, os
root = r"$ROOT/extension"
out = r"$OUT"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.startswith('.'): continue
            full = os.path.join(dirpath, f)
            z.write(full, os.path.relpath(full, root))
print("Wrote", out, os.path.getsize(out), "bytes")
PY
ls -la "$OUT"
