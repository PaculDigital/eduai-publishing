"""GERBANG PAGAR UNGGAH v2 — UJI PERILAKU (bukan grep teks).

⚠️ PELAJARAN 10 Okt 2026: versi-1 TIDAK BERGIGI — hanya `grep` teks
   "periksa_berkas_aman" di main.py. Saat pagar DIMATIKAN (`if not aman:`
   → `if False:`), grep tetap menemukan teksnya ⇒ gerbang tetap 7/0 LULUS.
   ⇒ Gerbang WAJIB memanggil PERILAKU, bukan memeriksa tulisan.

CARA v2: kirim berkas BERBAHAYA ke rute /unggah SUNGGUHAN, pastikan DITOLAK.
Gerbang ini TIDAK BISA lolos kalau pagar mati.

Jalankan DI DALAM container eduai-app.
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
        z.writestr('word/vbaProject.bin', b'\x00\x01MAKRO-JAHAAT')
    return b.getvalue()


def zip_nyamar() -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr('x.txt', 'bukan dokumen word')
    return b.getvalue()


def main():
    #  ── DB SALINAN (WAJIB — jangan cemari DB produksi) ─────────────────────
    #  ⚠️ TEMUAN NYATA 10 Okt 2026: versi-1 gerbang ini memakai DB PRODUKSI
    #     lewat TestClient ⇒ akun uji (`gerbang_pagar@uji.local`) + berkas uji
    #     MASUK ke DB user sungguhan. Pola BENAR ada di `_gerbang_unduh_dobel.py`
    #     (salin DB → `EDUAI_DB` → session dipaksa ke salinan).
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

    #  ── PERSIAPAN: akun uji lewat rute resmi ───────────────────────────────
    print('── PERSIAPAN akun uji ──')
    email = 'gerbang_pagar@uji.local'
    sandi = 'Rahasia123!'
    #  ⚠️ JEBAKAN TERUKUR 10 Okt 2026: rute login yang BENAR = `/daftar` +
    #     `/masuk` (form: nama/email/password). Versi lama gerbang ini memakai
    #     `/api/daftar` + `/api/masuk` (HTTP 404) ⇒ TIDAK PERNAH login ⇒
    #     `/unggah` membalas **HTTP 303 See Other** ⇒ 4 GAGAL PALSU.
    #     (Pelajaran sama seperti `_gerbang_format_standar.py`.)
    c.post('/daftar', data={'nama': 'Uji Pagar', 'email': email,
                             'password': sandi}, follow_redirects=False)
    r = c.post('/masuk', data={'email': email, 'password': sandi},
               follow_redirects=False)
    print(f'   cookie: {sorted(c.cookies.keys())}')
    print(f'   masuk : HTTP {r.status_code}')

    def kirim(nama: str, isi: bytes) -> tuple:
        rr = c.post('/unggah', files={'berkas': (nama, isi, 'application/octet-stream')},
                    follow_redirects=False)
        return rr.status_code, (rr.text or '')[:200]

    print()
    print('── UJI PERILAKU DI PINTU /unggah ──')
    st, tx = kirim('jahat.docx', docx_bermakro())
    cek('docx bernama .docx tapi ISI-nya bermakro ⇒ DITOLAK 400 + pesan MAKRO',
        st == 400 and 'makro' in tx.lower(), f'(HTTP {st}) {tx[:120]}')

    st, tx = kirim('tipu.docx', zip_nyamar())
    cek('ZIP dinamai .docx (bukan Word) ⇒ DITOLAK 400',
        st == 400, f'(HTTP {st}) {tx[:120]}')

    st, tx = kirim('rusak.docx', b'ini jelas bukan zip')
    cek('docx bukan-zip ⇒ DITOLAK 400', st == 400, f'(HTTP {st}) {tx[:120]}')

    st, tx = kirim('makro.doc', b'MZ\x00\x01apapun')
    cek('.doc ⇒ DITOLAK 400', st == 400, f'(HTTP {st}) {tx[:120]}')

    print()
    print('── UJI TIDAK MERUSAK YANG BAIK (kontrol negatif) ──')
    st, tx = kirim('baik.docx', docx_biasa())
    ditolak_pagar = (st == 400 and 'makro' in tx.lower())
    cek('docx SAH ⇒ TIDAK ditolak pagar', not ditolak_pagar,
        f'(HTTP {st}) {tx[:90]}')

    print()
    print(f'HASIL GERBANG PAGAR UNGGAH v2: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
