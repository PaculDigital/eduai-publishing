import subprocess
import sys

KODE = r'''
import sys
sys.path.insert(0, '/app')
from pathlib import Path
from app.models import SessionLocal, FileBerkas
from app.ai import _teks_dari_berkas

db = SessionLocal()
b = db.get(FileBerkas, 81)
print('NAMA:', getattr(b, 'nama', 'TIDAK ADA'))
# cari kolom path berkasnya
kol = [k for k in ('path', 'lokasi', 'berkas', 'nama_simpan', 'jalur') if hasattr(b, k)]
print('KOLOM path:', kol)
p = None
for k in kol:
    v = getattr(b, k, None)
    if v:
        p = Path(v)
        print('coba:', k, '=', str(v)[:90])
        if p.exists():
            break
if p is None or not p.exists():
    import glob
    kandidat = glob.glob('/app/data/**/*Asih*', recursive=True) + glob.glob('/app/uploads/**/*Asih*', recursive=True)
    print('kandidat berkas:', kandidat[:5])
    raise SystemExit('path tidak ketemu')
t = _teks_dari_berkas(p, b.nama)
sys.stdout.write('__TEKS__' + t)
'''

r = subprocess.run(
    ['docker', 'exec', '-e', 'PYTHONPATH=/app', '-w', '/app', 'eduai-app',
     'python3', '-c', KODE],
    capture_output=True, text=True, timeout=240)

out = r.stdout or ''
if '__TEKS__' in out:
    head, teks = out.split('__TEKS__', 1)
    print(head.strip())
    print('panjang teks:', len(teks))
    open('/opt/data/services/eduai-publishing/_naskah_asih.txt', 'w').write(teks)
    print('tersimpan: _naskah_asih.txt')
else:
    print('STDOUT:', out[-800:])
    print('STDERR:', (r.stderr or '')[-800:])
    print('EXIT:', r.returncode)
