#!/bin/bash
# Build image baru untuk perbaikan akar potongan (29Sep2026) + verifikasi isi.
set -e
cd /opt/data/services/eduai-publishing
TAG="eduai-app:$(date -u +%Y%m%d-%H%M%S)-akarpot"

echo "--- build $TAG ---"
docker build -t "$TAG" . 2>&1 | tail -6

echo "--- verifikasi ISI image (jangan asal percaya log build) ---"
docker run --rm --entrypoint python3 "$TAG" -c "
import ast
s = open('/app/app/versi.py').read()
ast.parse(s)
assert '_potong_pembuka' in s, 'MARKER helper HILANG'
assert 'awal_isi_naskah' in s, 'MARKER awal_isi HILANG'
assert s.count('def deteksi_bab') == 1, 'def deteksi_bab tidak 1'
print('MARKER LULUS · _potong_pembuka ada · awal_isi dipakai · ast.parse OK')
"
docker run --rm --entrypoint python3 "$TAG" -c "
import ast, os
for f in ('/app/app/versi.py', '/app/app/ai.py', '/app/app/parser.py'):
    ast.parse(open(f).read())
    print('ast OK ·', os.path.basename(f))
"
docker images "$TAG" --format 'image {{.Repository}}:{{.Tag}} {{.Size}}'
echo "TAG_BARU=$TAG"
