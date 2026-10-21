#!/usr/bin/env python3
"""E2E — gambar ditaruh TEPAT di posisi sub-bab lewat jalur PRODUKSI.

Jalur: _revisi_kerja (sama seperti tombol "Revisi dengan EduAi"),
DB sementara, AI NYATA, naskah NYATA (349508cb13697288.docx).

Bukti yang diminta:
   1. gambar tersisip dengan `cara = 'posisi bagian'` (BUKAN 'akhir dokumen')
   2. di XML: GAMBAR berada SETELAH judul bagian & SEBELUM judul berikutnya
   3. di paragraf yang tepat (bukan daftar isi)
"""
import asyncio
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='e2e_posisi_')
sys.path.insert(0, '/app')

from app import ai as A                                        # noqa: E402
from app import models as M                                    # noqa: E402

L, GA = 0, 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1; print(f'  ✅ {nama}')
    else:
        GA += 1; print(f'  ❌ {nama}  {bukti}')


SUMBER = Path('/app/uploads/6/349508cb13697288.docx')
KERJA = Path('/app/uploads/1/_e2e_posisi.docx')  # di folder unggahan user


class _Req:
    """Request tiruan (butuh .json())."""

    def __init__(self, b):
        self._b = b

    async def json(self):
        return self._b


print('══ E2E: GAMBAR DI POSISI SUB-BAB (jalur produksi) ══')
M.init_db()
db = M.SessionLocal()
try:
    KERJA.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(SUMBER, KERJA)
    u = M.User(email='uji-posisi@test.local', nama='Uji Posisi',
               role='client', aktif=True, password_hash='x',
               paket='basic', kuota_mb=50)
    db.add(u); db.commit(); db.refresh(u)
    fb = M.FileBerkas(user_id=u.id, nama=SUMBER.name, nama_simpan=KERJA.name,
                      ukuran=KERJA.stat().st_size, tipe='docx')
    db.add(fb); db.commit(); db.refresh(fb)
    print(f'  user={u.id} · berkas={fb.id} ({KERJA.stat().st_size:,} byte)')

    body = {
        'file_id': fb.id,
        'komentar': ['Tambahkan grafik pertumbuhan peserta latihan kriket '
                     'per tahun: 2020=120, 2021=180, 2022=240, 2023=310, '
                     '2024=395.'],
    }
    print('  memanggil _revisi_kerja (AI nyata, bisa 30-90 dtk) …')
    hasil = asyncio.run(A._revisi_kerja(_Req(body), u, db))
    print(f'  hasil: ok={hasil.get("ok")} · pesan={str(hasil.get("pesan"))[:80]}')
    cek('1. revisi berhasil', hasil.get('ok') is True, str(hasil)[:150])
    gbr = hasil.get('gambar') or []
    print(f'  gambar: {gbr}')
    cek('2. ada gambar tersisip', len(gbr) >= 1, str(gbr))
    if gbr:
        cara = gbr[0].get('cara')
        print(f'  cara penyisipan: {cara!r}')
        cek('3. cara = POSISI BAGIAN (bukan akhir dokumen)',
            cara == 'posisi bagian', f'cara={cara}')

    #  ── bukti dari XML ──
    with zipfile.ZipFile(KERJA) as z:
        doc = z.read('word/document.xml').decode('utf-8')
    pars = re.findall(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', doc, re.S)

    def judul(par, bagian):
        t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', par)).strip()
        if not t.startswith(bagian):
            return False
        sisa = t[len(bagian):]
        if not sisa or sisa[0] not in '. \t':
            return False
        if re.search(r'\.{3,}', t) or re.search(r'\d{1,4}\s*$', t):
            return False
        return 0 < len(sisa.lstrip('. \t')) <= 120

    i23 = [i for i, p in enumerate(pars) if judul(p, '2.3')]
    i24 = [i for i, p in enumerate(pars) if judul(p, '2.4')]
    igb = [i for i, p in enumerate(pars) if 'grafik_ai' in p]
    print(f'  indeks: 2.3{i23} · GAMBAR{igb} · 2.4{i24}')
    cek('4. gambar SETELAH judul 2.3', igb and i23 and igb[0] > i23[0], '')
    cek('5. gambar SEBELUM judul 2.4', igb and i24 and igb[0] < i24[0], '')
    cek('6. gambar ADA di paragraf (bukan daftar isi)', bool(igb), '')
finally:
    db.close()

print()
print(f'══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
