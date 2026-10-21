import subprocess

KODE = r'''
import sys, glob, os
sys.path.insert(0, '/app')
from pathlib import Path
from app.models import SessionLocal, FileBerkas
from app.ai import _teks_dari_berkas

db = SessionLocal()
b = db.get(FileBerkas, 81)
nm = b.nama_simpan
print('nama_simpan:', nm)

# cari di semua tempat yang mungkin
pola = [
    f'/app/**/{nm}', f'/app/data/**/{nm}', f'/app/uploads/**/{nm}',
    f'/app/data/uploads/**/{nm}', f'/app/data/berkas/**/{nm}',
]
found = []
for p in pola:
    found += glob.glob(p, recursive=True)
print('ditemukan:', found[:5])

if not found:
    print('-- isi /app/data --')
    for x in os.listdir('/app/data')[:20]:
        print('   ', x)
    raise SystemExit('berkas tidak ketemu')

p = Path(found[0])
t = _teks_dari_berkas(p, b.nama)
sys.stdout.write('__TEKS__' + t)
'''

r = subprocess.run(
    ['docker', 'exec', '-e', 'PYTHONPATH=/app', '-w', '/app', 'eduai-app',
     'python3', '-c', KODE],
    capture_output=True, text=True, timeout=300)

out = r.stdout or ''
if '__TEKS__' in out:
    head, teks = out.split('__TEKS__', 1)
    print(head.strip())
    print('panjang teks:', len(teks))
    open('/opt/data/services/eduai-publishing/_naskah_asih.txt', 'w').write(teks)
    print('tersimpan.')
else:
    print('STDOUT:', out[-1500:])
    print('STDERR:', (r.stderr or '')[-600:])
