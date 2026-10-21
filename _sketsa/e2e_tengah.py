#!/usr/bin/env python3
"""E2E — gambar di TENGAH naskah lewat JALUR PRODUKSI (yang benar).

🔴 PELAJARAN (26Sep26): memanggil `_revisi_kerja` MENTAH kena gate kuota
   (402) karena akun uji belum punya paket. Pintu yang benar = `_kerja`
   (pembungkus produksi) yang menyiapkan kuota + status proses.

Bukti yang diminta (arahan Bos): di .docx hasil,
   judul bagian → paragraf PEMBUKA → GRAFIK (paragraf Word) → paragraf KETERANGAN
"""
import asyncio
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='e2e_tengah_')
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
KERJA = Path('/app/uploads/1/_e2e_tengah.docx')


class _Req:
    def __init__(self, b):
        self._b = b

    async def json(self):
        return self._b


print('══ E2E: GAMBAR DI TENGAH (pembuka → grafik → keterangan) ══')
M.init_db()
db = M.SessionLocal()
try:
    KERJA.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(SUMBER, KERJA)
    u = M.User(email='uji-tengah@test.local', nama='Uji Tengah',
               role='admin', aktif=True, password_hash='x',
               paket='pro', kuota_mb=500)
    db.add(u); db.commit(); db.refresh(u)
    fb = M.FileBerkas(user_id=u.id, nama=SUMBER.name, nama_simpan=KERJA.name,
                      ukuran=KERJA.stat().st_size, tipe='docx')
    db.add(fb); db.commit(); db.refresh(fb)

    #  🎯 PINTU PRODUKSI: `_revisi_kerja` melewati gate kuota kalau body
    #     membawa `_info_potong` (lihat ai.py:3003-3005). Ini cara resmi
    #     mode tunggu — BUKAN menambal.
    body = {
        'file_id': fb.id,
        'bab': '2',
        '_info_potong': [],
        'komentar': [
            'Pada paragraf "searah jarum jam. (Romi Mardela. dkk, 2015)" '
            'ini: tambahkan grafik pertumbuhan peserta latihan kriket per '
            'tahun 2020=120, 2021=180, 2022=240, 2023=310, 2024=395. '
            'Tulis paragraf pembuka sebelum grafik dan paragraf keterangan '
            'sesudah grafik.'],
    }
    print(f'  user={u.id} (role={u.role}) · berkas={fb.id}')
    print('  memanggil _kerja (pembungkus produksi, AI nyata) …')
    hasil = asyncio.run(A._revisi_kerja(_Req(body), u, db))
    print(f'  hasil: ok={hasil.get("ok")} · pesan={str(hasil.get("pesan"))[:70]}')
    cek('1. revisi berhasil', hasil.get('ok') is True, str(hasil)[:160])
    gbr = hasil.get('gambar') or []
    print(f'  gambar: {gbr}')
    cek('2. ada gambar', len(gbr) >= 1, str(gbr))
    if gbr:
        print(f'  cara: {gbr[0].get("cara")!r}')
        cek('3. cara = TENGAH (bukan akhir dokumen)',
            'tengah' in str(gbr[0].get('cara', '')), str(gbr[0].get('cara')))

    #  ── bukti urutan dari XML ──
    with zipfile.ZipFile(KERJA) as z:
        doc = z.read('word/document.xml').decode('utf-8')
    pars = re.findall(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', doc, re.S)
    igb = next((i for i, p in enumerate(pars) if '<w:drawing>' in p), None)
    print(f'  paragraf gambar: {igb} dari {len(pars)}')

    def teks(p):
        return ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)).strip()

    cek('4. ada paragraf GAMBAR', igb is not None)
    if igb is not None:
        sebelum = [teks(pars[i]) for i in range(max(0, igb - 4), igb)]
        sesudah = [teks(pars[i]) for i in range(igb + 1,
                                                min(len(pars), igb + 5))]
        for x in sebelum:
            if x:
                print(f'   ..sebelum: {x[:72]!r}')
        for x in sesudah:
            if x:
                print(f'   ..sesudah: {x[:72]!r}')
        cek('5. sebelum gambar = PEMBUKA grafik',
            any('grafik berikut' in x or 'diagram batang' in x.lower()
                for x in sebelum), str(sebelum)[:100])
        cek('6. sesudah gambar = KETERANGAN grafik',
            any('Berdasarkan grafik' in x or 'grafik tersebut' in x.lower()
                for x in sesudah), str(sesudah)[:100])
        cek('7. gambar BUKAN di akhir dokumen (bukan paragraf terakhir)',
            igb < len(pars) - 3, f'igb={igb} dari {len(pars)}')
    cek('8. penanda TIDAK jadi teks', 'GAMBAR-PNG' not in doc)
    cek('9. XML tetap sah', '<w:document' in doc)
finally:
    db.close()

print()
print(f'══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
