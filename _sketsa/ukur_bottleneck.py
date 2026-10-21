"""UKUR BOTTLE NECK: berapa besar tiap blok di `user_msg` E2E nyata?

PERTANYAAN BOS 25Sep26: kenapa E2E lambat (>180 dtk) padahal uji langsung
9router cuma 17 dtk? Petunjuk: uji langsung `in=17.800` token, E2E `in=33.497`
token → hampir 2x lipat. ⇒ ada blok BESAR yang cuma muncul di E2E.

CARA: lintasi `_revisi_kerja` dgn PENYADAP (monkey-patch) `_revisi_dengan_
failover` — user_msg dibaca TANPA memanggil AI (Rp 0, kuota aman).

⚠️ Membaca DB produksi (read-only). Tidak mengubah apa pun.
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, '/app')

import app.ai as A                                                    # noqa: E402
from sqlalchemy import select                                         # noqa: E402
from app.models import (CatatanPembimbing, FileBerkas,                 # noqa: E402
                        BerkasPembimbingan, SessionLocal, User)

CATATAN_ID = 106
TERSANGKA: list[dict] = []


async def penyadap(user_msg: str, jumlah_komentar: int,
                   naskah_banding: str = ''):
    TERSANGKA.append({'um': user_msg, 'jk': jumlah_komentar,
                      'banding': naskah_banding})
    raise RuntimeError('SADAP: berhenti sebelum panggil AI')


A._revisi_dengan_failover = penyadap

print('═' * 76)
print('  UKUR BOTTLE NECK — isi user_msg E2E (TANPA panggil AI)')
print('═' * 76)

db = SessionLocal()
k = db.execute(select(CatatanPembimbing).where(
    CatatanPembimbing.id == CATATAN_ID)).scalar_one_or_none()
if k is None:
    print(f'❌ catatan {CATATAN_ID} tak ada')
    sys.exit(1)
pb = db.execute(select(BerkasPembimbingan).where(
    BerkasPembimbingan.id == k.berkas_id)).scalar_one_or_none()
if pb is None:
    print(f'❌ pembimbingan_berkas {k.berkas_id} tak ada')
    sys.exit(1)
fb = db.execute(select(FileBerkas).where(
    FileBerkas.id == pb.file_id)).scalar_one_or_none()
if fb is None:
    print(f'❌ files {pb.file_id} tak ada')
    sys.exit(1)
u = db.execute(select(User).where(User.id == fb.user_id)).scalar_one()

sorotan = k.teks_asli or ''
print(f'catatan  : id={k.id} · pembimbingan_berkas={pb.id} · files={fb.id}')
print(f'  sorotan={len(sorotan)} kar · isi={(k.isi or "")[:70]!r}')
print(f'berkas   : {fb.nama_simpan} pemilik={fb.user_id} '
      f'tipe={fb.tipe} ukuran={fb.ukuran}')

p = Path('/app/uploads') / str(fb.user_id) / fb.nama_simpan
print(f'berkas disk: ada={p.exists()}')
if p.exists():
    print(f'  ukuran={p.stat().st_size:,} byte')
    t0 = time.time()
    teks = A._teks_dari_berkas(p, fb.nama or '')
    print(f'  teks={len(teks):,} kar (baca {time.time()-t0:.2f} dtk)')


class ReqTiruan:                                                           # noqa: D101
    def __init__(self, body):
        self._b = body

    async def json(self):
        return self._b


body = {
    'file_id': fb.id,
    'bab': '__seluruh__',
    'komentar': [k.isi or 'perbaiki bagian ini'],
    'setuju_bagian': True,
}

print('\n── panggil _revisi_kerja (AI DISADAP) ──')
t0 = time.time()
try:
    asyncio.run(A._revisi_kerja(ReqTiruan(body), u, db))
except Exception as e:                                                     # noqa: BLE001
    print(f'berhenti: {type(e).__name__}: {str(e)[:90]}')
print(f'(waktu sampai sadapan: {time.time()-t0:.1f} dtk)')

if not TERSANGKA:
    print('❌ tidak ada user_msg terekam')
    sys.exit(1)

um = TERSANGKA[0]['um']
tot = len(um) + len(A.SYSTEM_REVISI)
print('\n══ HASIL ══')
print(f'   user_msg      = {len(um):,} kar')
print(f'   SYSTEM_REVISI = {len(A.SYSTEM_REVISI):,} kar')
print(f'   TOTAL KIRIM   = {tot:,} kar  ≈ {tot/2.4:,.0f} token')
print('   (uji langsung Wulan: 17.800 token → E2E hampir 2x lipat!)')

pos_naskah = um.find('<<<NASKAH')
pos_tutup_n = um.find('NASKAH;>>>')
pos_kom = um.find('<<<KOMENTAR')
pos_tutup_k = um.find('KOMENTAR;>>>')
print('\n── PECAHAN (kar) ──')
print(f'   SEBELUM NASKAH : {pos_naskah:>9,}   ← TERSANGKA BOTTLE NECK')
print(f'   isi NASKAH     : {pos_tutup_n - pos_naskah:>9,}')
print(f'   KOMENTAR       : {pos_tutup_k - pos_kom:>9,}')

print('\n── 1.500 kar PERTAMA user_msg ──')
print(um[:1500])
print('\n── 500 kar TEPAT SEBELUM <<<NASKAH (blok terakhir) ──')
print(um[max(0, pos_naskah - 500):pos_naskah])
