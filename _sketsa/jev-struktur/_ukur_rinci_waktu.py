"""UKUR RINCI WAKTU _posisi_dari_jev — di mana 20 detik itu habis?

Jangan menebak. Ukur: jumlah panggilan, waktu per panggilan, waktu jeda,
waktu kode (bukan jaringan).
"""
import sys, time, re
sys.path.insert(0, '/app')
from app import konversi as K
import app.models as M
from app.models import SessionLocal

db = SessionLocal()
fb = db.query(M.FileBerkas).filter(M.FileBerkas.nama.like('%Asih%')).first()
if fb is None:
    fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == 81).first()
print(f'naskah fid={fb.id} {fb.nama}')

import app.ai as ai_mod
teks = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
print(f'naskah: {len(teks)} kar, {teks.count(chr(10))} baris')

# ── Bungkus tanya_bebas untuk hitung panggilan & waktu ──
#  ✅ TERUKUR: satpam.tanya_bebas & tanya_bebas_mutu itu **SYNC** (bukan async)
#  — dipanggil dari `_tanya_jev_kuat()` yang juga sync. Pembungkus = sync.
#  (Wulan sempat bikin async → 'coroutine object is not iterable'.)
from app import satpam
catat = []

def _catat(t, bahan, pertanyaan):
    try:
        n = len(pertanyaan)
    except Exception:
        n = 1
    catat.append({'t': t, 'kar_bahan': len(bahan or ''), 'n_tanya': n})

def _bungkus(asal):
    def _dalam(bahan, pertanyaan, *a, **k):
        t0 = time.time()
        hasil = asal(bahan, pertanyaan, *a, **k)
        _catat(time.time() - t0, bahan, pertanyaan)
        return hasil
    return _dalam

satpam.tanya_bebas_mutu = _bungkus(satpam.tanya_bebas_mutu)
satpam.tanya_bebas = _bungkus(satpam.tanya_bebas)

t0 = time.time()
pos = K._posisi_dari_jev(teks)
total = time.time() - t0

print()
print(f'════ HASIL: {len(pos)} bab, {total:.1f} dtk ════')
for p in pos:
    print(f"  {p}")

print()
print(f'════ RINCI {len(catat)} PANGGILAN ════')
s_jaringan = sum(c['t'] for c in catat)
print(f'  waktu PANGGILAN Jev   : {s_jaringan:6.1f} dtk  ({len(catat)} panggilan)')
print(f'  rata-rata per panggilan: {s_jaringan/max(1,len(catat)):5.2f} dtk')
print(f'  JUMLAH KAR BAHAN      : {sum(c["kar_bahan"] for c in catat):,} kar')
print(f'  TOTAL WAKTU           : {total:6.1f} dtk')
print(f'  SELAIN Jev (kode/jeda) : {total - s_jaringan:6.1f} dtk')
print()
print('  10 panggilan terlama:')
for c in sorted(catat, key=lambda x: -x['t'])[:10]:
    print(f'    {c["t"]:5.2f} dtk · bahan {c["kar_bahan"]:>7,} kar · {c["n_tanya"]} tanya')
print()
print('  bahan TERBESAR:')
for c in sorted(catat, key=lambda x: -x['kar_bahan'])[:5]:
    print(f'    {c["kar_bahan"]:>7,} kar · {c["t"]:5.2f} dtk')
db.close()
