"""UJI TAMPILAN MUTU v3 — docx SUNGGUHAN yang LOLOS pagar & terbaca.

⚠️ JEBAKAN yang sudah kena (10 Okt 2026, 2× salah):
  v1: docx XML karangan (`xmlns:w="x"`) ⇒ pembaca Word baca 0 paragraf.
  v2: menulis ulang ZIP templat ⇒ entri `word/_rels/` jadi DIRECTORY kosong
      (`ZipFile.writestr('word/_rels/', b'')`) ⇒ pagar/Word bingung.
⇒ CARA BENAR: SALIN templat apa adanya, HANYA ganti byte `word/document.xml`
  di dalam ZIP asli (pola `konversi.tulis_artikel_docx`).
"""
from __future__ import annotations

import io
import re
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


def docx_dari_templat(teks: str) -> bytes:
    """SALIN templat, ganti HANYA word/document.xml (ZIP asli dipertahankan)."""
    sumber = '/app/app/templat/naskah-baru.docx'
    keluar = io.BytesIO()
    with zipfile.ZipFile(sumber) as zs, \
            zipfile.ZipFile(keluar, 'w', zipfile.ZIP_DEFLATED) as zk:
        for it in zs.infolist():
            data = zs.read(it.filename)
            if it.filename == 'word/document.xml':
                doc = data.decode('utf-8')
                par = []
                for b in teks.split('\n'):
                    if not b.strip():
                        continue
                    aman = (b.replace('&', '&amp;').replace('<', '&lt;')
                            .replace('>', '&gt;'))
                    par.append('<w:p><w:r><w:t xml:space="preserve">' + aman +
                               '</w:t></w:r></w:p>')
                doc = re.sub(r'(<w:body>).*?(</w:body>)',
                             lambda m: m.group(1) + ''.join(par) + m.group(2),
                             doc, count=1, flags=re.S)
                data = doc.encode('utf-8')
            #  SALIN APA ADANYA — termasuk entri directory (bertanda '/')
            zk.writestr(it, data)
    return keluar.getvalue()


SEHAT = '\n'.join(
    'Pendidikan merupakan salah satu faktor penting dalam pembangunan sumber '
    'daya manusia yang berkualitas serta berdaya saing tinggi di era ini'
    for _ in range(25))

RUSAK = '\n'.join(
    c for kata in ('Dina Alna Helmania Putri meneliti stunting pada balita '
                   'di wilayah kerja puskesmas kecamatan itu').split()
    for c in kata)


def main():
    from app.ai import SessionLocal, _teks_dari_berkas
    from app.config import UPLOAD_DIR
    from app.main import app
    from app.models import FileBerkas

    print('── PERSIAPAN: docx buatan uji harus TERBACA ──')
    b_rusak = docx_dari_templat(RUSAK)
    p_cek = UPLOAD_DIR / '12' / '_cek_uji.docx'
    p_cek.parent.mkdir(parents=True, exist_ok=True)
    p_cek.write_bytes(b_rusak)
    t = _teks_dari_berkas(p_cek, 'cek.docx')
    print(f'   docx uji: {len(b_rusak)} byte ⇒ teks {len(t)} kar')
    cek('docx uji TERBACA (teks > 0)', len(t) > 0, f'({len(t)} kar)')
    cek('docx uji terpecah per huruf', t.count('\n') > 30,
        f'({t.count(chr(10))} baris)')
    p_cek.unlink(missing_ok=True)

    c = TestClient(app)
    email = 'uji_mutu_v3@uji.local'
    c.post('/daftar', data={'nama': 'Uji3', 'email': email,
                            'password': 'Rahasia123!'}, follow_redirects=False)
    c.post('/masuk', data={'email': email, 'password': 'Rahasia123!'},
           follow_redirects=False)

    def unggah_petakan(nama, teks):
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
            db = SessionLocal()
            fr = db.query(FileBerkas).order_by(FileBerkas.id.desc()).first()
            fid = fr.id if fr else None
            db.close()
        r = c.post('/api/ai/v1/alur/petakan',
                   json={'pilihan': 'lanjut', 'file_id': fid},
                   follow_redirects=False)
        return up, fid, (r.json() if r.status_code == 200 else {})

    print()
    print('── naskah RUSAK lewat ALUR SUNGGUHAN ──')
    up, fid, d = unggah_petakan('rusak.docx', RUSAK)
    print(f'   unggah HTTP {up.status_code} · fid {fid}')
    print(f'   unggah balikan: {(up.text or "")[:150]}')
    m = d.get('mutu') or {}
    print(f'   kunci hasil: {sorted(d.keys())}')
    cek('hasil memuat "mutu"', bool(m))
    cek('tingkat = rusak_konversi', m.get('tingkat') == 'rusak_konversi',
        f'(dapat {m.get("tingkat")})')
    cek('saran = ganti_ke_docx', m.get('saran') == 'ganti_ke_docx',
        f'(dapat {m.get("saran")})')
    cek('gratis tetap true', d.get('gratis') is True)
    if m:
        print(f'   pesan: {m.get("pesan", "")[:140]}')

    print()
    print('── naskah SEHAT lewat ALUR SUNGGUHAN ──')
    up2, fid2, d2 = unggah_petakan('sehat.docx', SEHAT)
    print(f'   unggah HTTP {up2.status_code} · fid {fid2}')
    m2 = d2.get('mutu') or {}
    cek('hasil memuat "mutu"', bool(m2))
    cek('tingkat = sehat', m2.get('tingkat') == 'sehat',
        f'(dapat {m2.get("tingkat")})')
    cek('TIDAK diarahkan ganti .docx', m2.get('saran') != 'ganti_ke_docx',
        f'(dapat {m2.get("saran")})')
    if m2:
        print(f'   pesan: {m2.get("pesan", "")[:140]}')

    print()
    print(f'HASIL UJI TAMPILAN MUTU v3: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
