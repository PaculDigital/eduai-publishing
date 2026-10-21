"""UJI TAMPILAN MUTU v2 — pakai docx SUNGGUHAN (templat aplikasi).

⚠️ PELAJARAN (uji v1 GAGAL PALSU): docx buatan sendiri dengan XML karangan
   `<w:document xmlns:w="x">` TIDAK terbaca pembaca Word ⇒ teks 0 karakter
   ⇒ "mutu" tak muncul. Itu ALAT UKUR yang salah, BUKAN kode salah.
   ⇒ UJI WAJIB memakai naskah SUNGGUHAN (templat resmi aplikasi).
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

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


def docx_dari_templat(teks: str) -> bytes:
    """Bikin docx dari TEMPLAT RESMI aplikasi (namespace Word yang benar)."""
    templat = Path('/app/app/templat/naskah-baru.docx')
    xml = templat.read_bytes()
    with zipfile.ZipFile(io.BytesIO(xml)) as z:
        isi = {n: z.read(n) for n in z.namelist()}
    doc = isi['word/document.xml'].decode('utf-8')
    #  ambil 1 paragraf templat sebagai CANGKANG, isi teks kita
    m = re.search(r'<w:p\b[^>]*>.*?</w:p>', doc, re.S)
    cangkang = m.group(0) if m else '<w:p><w:r><w:t>X</w:t></w:r></w:p>'
    par = []
    for b in teks.split('\n'):
        if not b.strip():
            continue
        if 'xml:space' in cangkang:
            par.append(cangkang.replace(m.group(0), cangkang))  # placeholder
        #  sisipkan teks ke cangkang: ganti isi <w:t>…</w:t>
        par.append(re.sub(r'(<w:t[^>]*>).*?(</w:t>)',
                          lambda mm: mm.group(1) + b.replace('&', '&amp;')
                          .replace('<', '&lt;') + mm.group(2),
                          cangkang, count=1))
    doc2 = re.sub(r'(<w:body>).*?(</w:body>)',
                  lambda mm: mm.group(1) + ''.join(par) + mm.group(2),
                  doc, count=1, flags=re.S)
    isi['word/document.xml'] = doc2.encode('utf-8')
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        for n, v in isi.items():
            z.writestr(n, v)
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

    email = 'uji_mutu_v2@uji.local'
    sandi = 'Rahasia123!'
    c.post('/daftar', data={'nama': 'Uji Mutu2', 'email': email,
                            'password': sandi}, follow_redirects=False)
    c.post('/masuk', data={'email': email, 'password': sandi},
           follow_redirects=False)

    def unggah_dan_petakan(nama, teks):
        up = c.post('/unggah',
                    files={'berkas': (nama, docx_dari_templat(teks),
                                      'application/octet-stream')},
                    follow_redirects=False)
        fid = None
        try:
            fid = up.json().get('file_id') or up.json().get('fid')
        except Exception:                                          # noqa: BLE001
            pass
        if not fid:
            from app.ai import SessionLocal
            from app.models import FileBerkas
            db = SessionLocal()
            fr = db.query(FileBerkas).order_by(FileBerkas.id.desc()).first()
            fid = fr.id if fr else None
            db.close()
        r = c.post('/api/ai/v1/alur/petakan',
                   json={'pilihan': 'lanjut', 'file_id': fid},
                   follow_redirects=False)
        return up.status_code, fid, (r.json() if r.status_code == 200 else {})

    print('── naskah RUSAK (per-huruf) lewat ALUR SUNGGUHAN ──')
    st, fid, d = unggah_dan_petakan('rusak.docx', RUSAK)
    m = d.get('mutu') or {}
    print(f'   unggah {st} · fid {fid} · kunci: {sorted(d.keys())}')
    cek('hasil memuat "mutu"', bool(m))
    cek('tingkat = rusak_konversi', m.get('tingkat') == 'rusak_konversi',
        f'(dapat {m.get("tingkat")})')
    cek('saran = ganti_ke_docx', m.get('saran') == 'ganti_ke_docx',
        f'(dapat {m.get("saran")})')
    cek('gratis tetap true', d.get('gratis') is True)
    print(f'   pesan: {m.get("pesan", "")[:130]}')

    print()
    print('── naskah SEHAT lewat ALUR SUNGGUHAN ──')
    st2, fid2, d2 = unggah_dan_petakan('sehat.docx', SEHAT)
    m2 = d2.get('mutu') or {}
    print(f'   unggah {st2} · fid {fid2}')
    cek('tingkat = sehat', m2.get('tingkat') == 'sehat',
        f'(dapat {m2.get("tingkat")})')
    cek('TIDAK diarahkan ganti .docx', m2.get('saran') != 'ganti_ke_docx',
        f'(dapat {m2.get("saran")})')
    print(f'   pesan: {m2.get("pesan", "")[:130]}')

    print()
    print(f'HASIL UJI TAMPILAN MUTU v2: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
