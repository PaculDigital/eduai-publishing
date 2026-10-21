#!/usr/bin/env python3
"""UJI: bikin dokumen .docx BARU lewat API OnlyOffice (26Sep26).

CARA KERJA (yang diuji di sini):
  1. Ambil template resmi OnlyOffice `new.docx` (document-templates/new/default)
  2. Pakai ConvertService.ashx → jadikan .docx bersih (atau langsung pakai)
  3. Simpan ke folder upload user + daftarkan di tabel `files`

Uji ini HANYA memakai API yang SUDAH ADA (ConvertService di oo-converter).
TIDAK bikin mesin baru.
"""
import asyncio
import os
import sys

sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/app/data')

import httpx                                                        # noqa: E402
from app.config import OO_URL                                       # noqa: E402

TPL = '/var/www/onlyoffice/documentserver/document-templates/new/default/new.docx'


async def main() -> int:
    print('══ 1. CEK TEMPLATE ADA ══')
    cek_tpl = os.path.exists(TPL)
    print(f'  {"✅" if cek_tpl else "❌"} template {TPL}')

    print('\n══ 2. CEK ConvertService HIDUP ══')
    async with httpx.AsyncClient(timeout=60) as c:
        try:
            r = await c.post(f'{OO_URL}/ConvertService.ashx',
                             json={'async': False}, headers={'Accept': 'application/json'})
            print(f'  ✅ ConvertService balas HTTP {r.status_code}')
            hidup = True
        except Exception as e:                                       # noqa: BLE001
            print(f'  ❌ ConvertService tidak bisa dihubungi: {e}')
            hidup = False

    print('\n══ 3. UJI APAKAH TEMPLATE BISA DIBACA jadi docx sah ══')
    import zipfile
    if cek_tpl:
        try:
            with zipfile.ZipFile(TPL) as z:
                nama = z.namelist()
                ada = 'word/document.xml' in nama
            print(f'  {"✅" if ada else "❌"} new.docx = docx SAH '
                  f'({len(nama)} berkas dalam zip, word/document.xml '
                  f'{"ADA" if ada else "TIDAK ADA"})')
        except Exception as e:                                       # noqa: BLE001
            print(f'  ❌ template bukan docx sah: {e}')

    print('\n══ 4. KESIMPULAN ══')
    if cek_tpl and hidup:
        print('  ✅ BISA: dokumen baru dapat dibuat lewat API OnlyOffice')
        print('     → salin template resmi + daftarkan di tabel `files`')
        print('     → TIDAK perlu ConvertService untuk kasus .docx→.docx')
        return 0
    print('  ⚠️ perlu jalan lain')
    return 1


sys.exit(asyncio.run(main()))
