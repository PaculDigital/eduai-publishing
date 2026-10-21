"""UKUR KEKURANGAN NASKAH ASIH versi JEV — bahan jualan Bos.

Ini yang Bos butuh: daftar kekurangan nyata (novelty, gap, dll) + harga token.
Jev = MATA, lapor apa adanya. Angka WAJIB dicetak, bukan dikira.
"""
import sys
import time

sys.path.insert(0, '/app')
from app import konversi as K                                      # noqa: E402
from app.models import User, FileBerkas, SessionLocal              # noqa: E402

db = SessionLocal()
fb = db.get(FileBerkas, 81)
u = db.get(User, fb.user_id)
print(f'naskah : {fb.nama}')
print(f'pemilik: {u.email}')

#  Baca naskah ASLI (bukan artikel hasil)
import app.ai as ai_mod                                            # noqa: E402
naskah = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
print(f'naskah : {len(naskah):,} karakter')
print()

#  ── JEV PERIKSA MUTU NASKAH (18 poin) ──
print('═' * 70)
print('JEV PERIKSA NASKAH ASIH (18 poin mutu)')
print('═' * 70)
t0 = time.time()
mutu = K.periksa_mutu(db, 81, naskah)
dt = time.time() - t0
print(f'ok        : {mutu.get("ok")}')
print(f'keputusan : {mutu.get("keputusan")}')
print(f'skor      : {mutu.get("skor")}')
print(f'detik     : {round(dt, 2)}')
print(f'model     : {mutu.get("model")}')
print(f'alasan    : {mutu.get("alasan")}')
print()

print('── NILAI PER POIN (rendah = kekurangan = bahan jualan) ──')
ada = mutu.get('ada') or {}
for nama, nilai in sorted(ada.items(), key=lambda x: x[1]):
    tanda = '🔴' if nilai < 0.35 else ('🟡' if nilai < 0.5 else '✅')
    print(f'  {tanda} {nilai:.2f}  {nama}')
print()

print('kurang (<0,35) :', mutu.get('kurang'))
print('ragu (0,35-0,5):', mutu.get('ragu'))
print()

#  ── HARGA JUALAN: kekurangan × 2 token ──
print('═' * 70)
print('HARGA JUALAN — kekurangan × 2 token/item')
print('═' * 70)
kurang = list(mutu.get('kurang') or []) + list(mutu.get('ragu') or [])
print(f'jumlah kekurangan: {len(kurang)} item')
print(f'harga per item   : {K.TOKEN_PER_REVISI} token')
print(f'total  kalau semua dibeli: {len(kurang) * K.TOKEN_PER_REVISI} token')
print()
for k in kurang:
    print(f'  · {k}  → {K.TOKEN_PER_REVISI} token')
print()
print('── BUKTI: mesin hitung biaya ──')
b = K.hitung_biaya_revisi(['elemen:novelty', 'elemen:gap'])
print(f'  novelty + gap → {b}')
db.close()
