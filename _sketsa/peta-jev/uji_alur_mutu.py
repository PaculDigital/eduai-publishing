"""UJI TAMPILAN: panggil /mulai → unggah naskah RUSAK → petakan → lihat hasil.

Ukur: apakah server MENEMPELKAN hasil mutu (kunci 'mutu') pada naskah rusak,
dan TIDAK menempel 'ganti_ke_docx' pada naskah sehat.

Jalankan DI DALAM container (akses 127.0.0.1:8000 langsung).
"""
from __future__ import annotations

import io
import json
import sys
import zipfile

sys.path.insert(0, '/app')

from fastapi.testclient import TestClient                          # noqa: E402

LULUS = 0
GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama} {bukti}')


def docx_dari_teks(teks: str) -> bytes:
    """docx minimal berisi paragraf dari `teks`."""
    paras = ''.join(
        f'<w:p><w:r><w:t xml:space="preserve">{x}</w:t></w:r></w:p>'
        for x in teks.split('\n') if x.strip())
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
        z.writestr('word/document.xml',
                   '<?xml version="1.0"?><w:document xmlns:w="x"><w:body>'
                   f'{paras}</w:body></w:document>')
    return b.getvalue()


SEHAT = '\n'.join(
    'Pendidikan merupakan salah satu faktor penting dalam pembangunan sumber '
    'daya manusia yang berkualitas serta berdaya saing tinggi di era ini'
    for _ in range(25))

RUSAK = '\n'.join(
    c for kata in ('Dina Alna Helmania Putri meneliti stunting pada balita '
                   'di wilayah kerja puskesmas kecamatan itu').split()
    for c in kata)


def main():
    from app.main import app
    c = TestClient(app)

    email = 'uji_mutu_tampil@uji.local'
    sandi = 'Rahasia123!'
    c.post('/daftar', data={'nama': 'Uji Mutu', 'email': email,
                            'password': sandi}, follow_redirects=False)
    c.post('/masuk', data={'email': email, 'password': sandi},
           follow_redirects=False)
    print(f'   cookie: {sorted(c.cookies.keys())}')

    print()
    print('── UJI: naskah RUSAK lewat ALUR SUNGGUHAN ──')
    up = c.post('/unggah', files={'berkas': ('rusak.docx', docx_dari_teks(RUSAK),
                                             'application/octet-stream')},
                follow_redirects=False)
    print(f'   unggah: HTTP {up.status_code}')
    fid = None
    try:
        fid = up.json().get('file_id') or up.json().get('fid')
    except Exception:                                              # noqa: BLE001
        fid = None
    if not fid:
        from app.ai import SessionLocal
        from app.models import FileBerkas
        db = SessionLocal()
        fr = db.query(FileBerkas).order_by(FileBerkas.id.desc()).first()
        fid = fr.id if fr else None
        db.close()
    print(f'   fid: {fid}')

    r = c.post('/api/ai/v1/alur/petakan',
               json={'pilihan': 'lanjut', 'file_id': fid},
               follow_redirects=False)
    print(f'   petakan: HTTP {r.status_code}')
    d = r.json() if r.status_code == 200 else {}
    m = d.get('mutu') or {}
    cek('hasil memuat kunci "mutu"', bool(m), f'({list(d.keys())})')
    cek('naskah RUSAK ⇒ tingkat rusak_konversi',
        m.get('tingkat') == 'rusak_konversi', f'(dapat {m.get("tingkat")})')
    cek('⇒ saran ganti_ke_docx', m.get('saran') == 'ganti_ke_docx',
        f'(dapat {m.get("saran")})')
    cek('masih GRATIS (tidak mengubah harga)',
        d.get('gratis') is True)

    print()
    print('── UJI: naskah SEHAT lewat ALUR SUNGGUHAN ──')
    up2 = c.post('/unggah', files={'berkas': ('sehat.docx', docx_dari_teks(SEHAT),
                                              'application/octet-stream')},
                 follow_redirects=False)
    fid2 = None
    try:
        fid2 = up2.json().get('file_id') or up2.json().get('fid')
    except Exception:                                              # noqa: BLE001
        fid2 = None
    if not fid2:
        from app.ai import SessionLocal
        from app.models import FileBerkas
        db = SessionLocal()
        fr = db.query(FileBerkas).order_by(FileBerkas.id.desc()).first()
        fid2 = fr.id if fr else None
        db.close()
    r2 = c.post('/api/ai/v1/alur/petakan',
                json={'pilihan': 'lanjut', 'file_id': fid2},
                follow_redirects=False)
    d2 = r2.json() if r2.status_code == 200 else {}
    m2 = d2.get('mutu') or {}
    print(f'   unggah HTTP {up2.status_code} · petakan HTTP {r2.status_code}')
    cek('naskah SEHAT ⇒ tingkat sehat', m2.get('tingkat') == 'sehat',
        f'(dapat {m2.get("tingkat")})')
    cek('naskah SEHAT ⇒ TIDAK diarahkan ganti .docx',
        m2.get('saran') != 'ganti_ke_docx', f'(dapat {m2.get("saran")})')

    print()
    print(f'HASIL UJI TAMPILAN MUTU: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
