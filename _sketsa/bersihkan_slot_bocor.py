"""BERSIHKAN slot bocor + hantu, lalu BUKTIKAN antrean kembali normal.

AKAR (terbukti 25Sep26):
  `ai_revisi()` dipanggil TANPA lewat `_utas` (mis. `asyncio.run` langsung,
  atau utas mati sebelum `finally`) → `_sedang_jalan += 1` TAPI `_selesai_satu()`
  TIDAK pernah jalan → slot BOCOR. Setelah 8x bocor → `_sedang_jalan` = KONKUREN_MAKS
  → SEMUA permintaan masuk antrean dan TIDAK PERNAH dilayani.

CARA BERSIH:
  1. Tandai proses DB yang status='jalan' tapi sudah MATI (tak ada utas) → GAGAL.
  2. Kembalikan kuota yang tertahan (pakai fungsi resmi `kembalikan_bila_gagal`).
  3. Turunkan `_sedang_jalan` bila tidak ada utas hidup.
  4. Jalankan ulang E2E → HARUS langsung 'Mulai bekerja', bukan 'Menunggu antrean'.
"""
import asyncio
import sys
import time
import threading

sys.path.insert(0, '/app')

import app.ai as A                                                    # noqa: E402
from sqlalchemy import select                                         # noqa: E402
from app import proses as P                                           # noqa: E402
from app.models import (BerkasPembimbingan, CatatanPembimbing,         # noqa: E402
                        FileBerkas, PemakaianAI, ProsesAI, SessionLocal,
                        User)

print('═' * 76)
print('  BERSIHKAN SLOT BOCOR + BUKTIKAN')
print('═' * 76)

#  ── 1. utas hidup apa saja? ─────────────────────────────────────────────
hidup = [t.name for t in threading.enumerate() if t.name.startswith('proses-ai-')]
print(f'\nUTAS HIDUP sekarang : {hidup or "(tidak ada)"}')
print(f'_sedang_jalan       : {P._sedang_jalan}')
print(f'_kerja_terdaftar    : {list(P._kerja_terdaftar)}')
print(f'antrean             : {list(P._antrean)}')

#  ── 2. proses DB yang statusnya 'jalan' ─────────────────────────────────
db = SessionLocal()
jalan = db.execute(select(ProsesAI).where(
    ProsesAI.status == 'jalan')).scalars().all()
print(f'\nPROSES DB status=jalan : {len(jalan)}')
for p in jalan:
    utas_ada = f'proses-ai-{p.kode}' in hidup
    print(f'   id={p.id} kode={p.kode} dibuat={p.dibuat} '
          f'bagian={p.bagian_ke}/{p.jumlah_bagian} · utas_hidup={utas_ada}')

#  ── 3. tandai GAGAL yang tak punya utas (hantu) ─────────────────────────
hantu = [p for p in jalan if f'proses-ai-{p.kode}' not in hidup]
print(f'\nHANtu (tak punya utas) : {len(hantu)}')
for p in hantu:
    P.tandai_gagal(p.kode, 'Dibersihkan: utas mati sebelum selesai '
                           '(slot antrean bocor)')
    print(f'   id={p.id} → ditandai GAGAL')

#  ── 4. lepas slot bocor: hitung ulang dari utas hidup ───────────────────
seharusnya = len(hidup)
if P._sedang_jalan != seharusnya:
    print(f'\nSLOT BOCOR: _sedang_jalan={P._sedang_jalan} → '
          f'diperbaiki jadi {seharusnya} (sesuai utas hidup)')
    P._sedang_jalan = seharusnya
else:
    print(f'\nslot sudah benar: {P._sedang_jalan}')

P._antrean.clear()
P._kerja_terdaftar.clear()
for k in list(P._kerja_terdaftar):
    P._kerja_terdaftar.pop(k, None)

print(f'setelah bersih: _sedang_jalan={P._sedang_jalan} · '
      f'antrean={list(P._antrean)} · {P.statistik_antrean()}')

#  ── 5. BUKTI: jalankan E2E lagi → HARUS 'Mulai bekerja' ────────────────
print('\n' + '─' * 76)
print('BUKTI: jalankan ai_revisi LAGI (lewat worker `P.jalankan`)')
print('─' * 76)

k = db.execute(select(CatatanPembimbing).where(
    CatatanPembimbing.id == 106)).scalar_one()
pb = db.execute(select(BerkasPembimbingan).where(
    BerkasPembimbingan.id == k.berkas_id)).scalar_one()
fb = db.execute(select(FileBerkas).where(
    FileBerkas.id == pb.file_id)).scalar_one()
u = db.execute(select(User).where(User.id == fb.user_id)).scalar_one()

pem = db.execute(select(PemakaianAI).where(
    PemakaianAI.user_id == u.id)).scalar_one_or_none()
if pem is not None:
    pem.jumlah_revisi = 0
    db.commit()
    print(f'kuota user {u.id} direset → 0')

p2 = P.mulai(db, user_id=u.id, file_id=fb.id,
             komentar=[k.isi or 'perbaiki'], jumlah_bagian=2, panjang=64243)
print(f'proses baru: kode={p2.kode} status={p2.status}')


async def kerja(lapor):
    """Kerja SUNGGUHAN seperti worker."""
    await A._revisi_kerja(ReqTiruan({"file_id": fb.id, "bab": "__seluruh__",
                                     "komentar": [k.isi or "perbaiki"],
                                     "setuju_bagian": True}), u, db)


class ReqTiruan:                                                          # noqa: D101
    def __init__(self, b):
        self._b = b

    async def json(self):
        return self._b


t0 = time.time()
P.jalankan(p2.kode, kerja)
print(f'P.jalankan() dipanggil ({time.time()-t0:.2f} dtk)')

for i in range(1, 13):
    time.sleep(10)
    db.expire_all()
    px = db.execute(select(ProsesAI).where(
        ProsesAI.kode == p2.kode)).scalar_one()
    print(f'   t+{i*10:3d}s · status={px.status:<8} tahap={px.tahap[:40]:<40} '
          f'· {P.statistik_antrean()}')
    if px.status in ('selesai', 'gagal'):
        print(f'\n   >> HASIL: {px.status.upper()} dalam {time.time()-t0:.1f} dtk')
        print(f'   >> model={px.model_ai} token_in={px.token_in} '
              f'token_out={px.token_out} token_revisi={px.token_revisi}')
        if px.galat:
            print(f'   >> galat={px.galat[:200]}')
        break
