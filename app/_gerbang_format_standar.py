"""GERBANG FORMAT STANDAR + PAGAR ISI BERKAS — uji PERILAKU (bukan grep).

Putusan Bos 10 Okt 2026: format lama Office (.doc/.xls/.ppt) DILARANG di mana
saja ("agar standard aplikasi"); user yang kirim .doc diminta ganti .docx.

⚠️ PELAJARAN (gerbang versi-1 tidak bergigi): JANGAN menguji dengan `grep`
   teks di main.py — saat pagar dimatikan, grep tetap menemukan teks ⇒ LULUS
   palsu. UJI PERILAKU: panggil rutenya, pastikan DITOLAK.

Jalankan DI DALAM container eduai-app:
   docker cp app/_gerbang_format_standar.py eduai-app:/app/app/ && \
   docker exec -w /app eduai-app python3 app/_gerbang_format_standar.py
"""
from __future__ import annotations

import io
import sys
import zipfile

sys.path.insert(0, '/app')

from fastapi.testclient import TestClient                          # noqa: E402

LULUS = 0
GAGAL = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama} {bukti}')


def docx_biasa() -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
        z.writestr('word/document.xml',
                   '<?xml version="1.0"?><w:document xmlns:w="x">'
                   '<w:body><w:p><w:r><w:t>Halo</w:t></w:r></w:p></w:body>'
                   '</w:document>')
    return b.getvalue()


def docx_bermakro() -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
        z.writestr('word/document.xml',
                   '<?xml version="1.0"?><w:document xmlns:w="x">'
                   '<w:body></w:body></w:document>')
        z.writestr('word/vbaProject.bin', b'\x00\x01MAKRO')
    return b.getvalue()


def zip_nyamar() -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr('x.txt', 'bukan dokumen word')
    return b.getvalue()


DOC_OLE = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\x00' * 64


def main():
    #  ── DB SALINAN (WAJIB — jangan cemari DB produksi) ─────────────────────
    #  ⚠️ TEMUAN NYATA 10 Okt 2026: versi-1 gerbang ini memakai DB PRODUKSI
    #     lewat TestClient ⇒ tiap kali dijalankan ia MENDAFTARKAN akun uji
    #     (`gerbang_format@uji.local`) + MENYIMPAN berkas uji ke DB user
    #     sungguhan (terukur: 17 berkas + 2 akun uji kotor harus dibersihkan
    #     manual). Pola BENAR sudah ada di `_gerbang_unduh_dobel.py`:
    #     salin DB ke tmpdir → `EDUAI_DB` → session dipaksa ke salinan.
    #     ⇒ dipakai APA ADANYA di sini (aturan Bos: pakai yang sudah ada).
    import os
    import shutil
    import tempfile
    from pathlib import Path

    _akar = Path('/app')
    _tmpdir = Path(tempfile.mkdtemp())
    _db_asli = _akar / 'data' / 'eduai.db'
    _db_uji = _tmpdir / 'uji.db'
    if _db_asli.exists():
        shutil.copyfile(_db_asli, _db_uji)
    os.environ['EDUAI_DB'] = str(_db_uji)

    from sqlalchemy import create_engine                                # noqa: E402
    from sqlalchemy.orm import sessionmaker                             # noqa: E402

    import app.models as M                                              # noqa: E402
    M.SessionLocal = sessionmaker(bind=create_engine(f'sqlite:///{_db_uji}'),
                                  autoflush=False, autocommit=False)

    from app.main import app
    c = TestClient(app)

    print('── PERSIAPAN akun uji ──')
    email = 'gerbang_format@uji.local'
    sandi = 'Rahasia123!'
    c.post('/daftar', data={'nama': 'Uji Format', 'email': email,
                             'password': sandi}, follow_redirects=False)
    r = c.post('/masuk', data={'email': email, 'password': sandi},
               follow_redirects=False)
    #  pastikan cookie sesi terpasang
    print(f'   cookie: {sorted(c.cookies.keys())}')
    print(f'   masuk: HTTP {r.status_code}')

    def kirim(nama: str, isi: bytes) -> tuple:
        rr = c.post('/unggah',
                    files={'berkas': (nama, isi, 'application/octet-stream')},
                    follow_redirects=False)
        return rr.status_code, (rr.text or '')[:260]

    print()
    print('── UJI 1: FORMAT LAMA OFFICE (.doc/.xls/.ppt) DITOLAK + ARAHKAN ──')
    st, tx = kirim('naskah.doc', DOC_OLE)
    cek('.doc ⇒ 400 + pesan menyebut ".docx"',
        st == 400 and '.docx' in tx, f'(HTTP {st}) {tx[:130]}')

    st, tx = kirim('data.xls', DOC_OLE)
    cek('.xls ⇒ 400 + pesan menyebut ".xlsx"',
        st == 400 and '.xlsx' in tx, f'(HTTP {st}) {tx[:130]}')

    st, tx = kirim('slide.ppt', DOC_OLE)
    cek('.ppt ⇒ 400 + pesan menyebut ".pptx"',
        st == 400 and '.pptx' in tx, f'(HTTP {st}) {tx[:130]}')

    st, tx = kirim('template.dotm', docx_bermakro())
    cek('.dotm ⇒ 400 (ditolak)', st == 400, f'(HTTP {st}) {tx[:130]}')

    print()
    print('── UJI 2: PAGAR ISI BERKAS (anti-makro / anti-zip-nyamar) ──')
    st, tx = kirim('jahat.docx', docx_bermakro())
    cek('docx ISI bermakro ⇒ 400 + pesan MAKRO',
        st == 400 and 'makro' in tx.lower(), f'(HTTP {st}) {tx[:130]}')

    st, tx = kirim('tipu.docx', zip_nyamar())
    cek('ZIP dinamai .docx ⇒ 400', st == 400, f'(HTTP {st}) {tx[:130]}')

    st, tx = kirim('rusak.docx', b'ini bukan zip sama sekali')
    cek('docx bukan-zip ⇒ 400', st == 400, f'(HTTP {st}) {tx[:130]}')

    print()
    print('── UJI 3: KONTROL NEGATIF (jangan merusak yang sah) ──')
    st, tx = kirim('baik.docx', docx_biasa())
    cek('docx SAH ⇒ TIDAK ditolak pesan format/makro',
        not (st == 400 and ('.docx' in tx or 'makro' in tx.lower())),
        f'(HTTP {st}) {tx[:120]}')

    print()
    print('── UJI 4: KONSISTENSI DAFTAR (satu sumber, tidak setengah) ──')
    from app.config import EKSTENSI_DIIZINKAN, EKSTENSI_LAMA
    from app.lampiran_pembimbing import EKSTENSI_LAMPIRAN
    cek('EKSTENSI_DIIZINKAN tidak memuat .doc/.xls/.ppt',
        not ({'.doc', '.xls', '.ppt'} & EKSTENSI_DIIZINKAN))
    cek('EKSTENSI_LAMPIRAN tidak memuat .doc/.xls/.ppt',
        not ({'.doc', '.xls', '.ppt'} & EKSTENSI_LAMPIRAN))
    cek('semua ekstensi lama punya arahan pengganti',
        all(v for v in EKSTENSI_LAMA.values()))

    print()
    print(f'HASIL GERBANG FORMAT STANDAR: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
