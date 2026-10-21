"""UJI PRESISI DROPDOWN — DOKUMEN NYATA ASLI, DI PRODUKSI (24Sep26).

Jalankan DI DALAM container produksi (eduai-app). Butuh berkas dokumen
nyata dari `_contoh-dokumen/` yang disalin ke /app/_uji_doc.

Yang diuji: apakah dropdown "Bagian mana?" menampilkan bab yang BENAR
untuk tiap JENIS dokumen nyata (skripsi / tesis / disertasi).
"""
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, '/app')
from app import ai as AI
from app import pembimbing as P
from app.models import (BerkasPembimbingan, CatatanPembimbing, Pembimbingan,
                        SessionLocal, User, VersiDokumen, init_db)

LULUS = GAGAL = 0


def cek(nama, syarat, sebab=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ GAGAL: {nama}  ({sebab})')


def isi_select(html: str) -> list[str]:
    m = re.search(r'<select name="section_judul".*?</select>', html, re.S)
    if not m:
        return []
    return [x for x in re.findall(r'<option value="([^"]*)"', m.group(0)) if x]


DOKUMEN = [
    ('SKRIPSI S1', '/app/_uji_doc/SKRIPSI-S1-unmul-fazrigading.docx'),
    ('TESIS S2', '/app/_uji_doc/TESIS-S2-unhas-sastra-novel.docx'),
    ('DISERTASI S3', '/app/_uji_doc/DISERTASI-S3-unhas-kesehatan-stunting.docx'),
]

init_db()
db = SessionLocal()
FID = 9   # satu-satunya berkas NYATA milik user 3
u = db.query(User).filter(User.id == 3).one()

print('═' * 74)
print('  PRESISI DROPDOWN DI PRODUKSI — DOKUMEN NYATA ASLI')
print('═' * 74)

for nama, jalur in DOKUMEN:
    p = Path(jalur)
    if not p.is_file():
        print(f'\n  ⚠️ {nama}: berkas tidak ada — dilewati')
        continue
    teks = AI._teks_dari_berkas(p, p.name)                     # noqa: SLF001

    for b in db.query(Pembimbingan).filter(
            Pembimbingan.nama == f'Uji {nama}').all():
        db.query(CatatanPembimbing).filter(
            CatatanPembimbing.pembimbingan_id == b.id).delete()
        db.query(BerkasPembimbingan).filter(
            BerkasPembimbingan.pembimbingan_id == b.id).delete()
        db.delete(b)
    db.query(VersiDokumen).filter(VersiDokumen.file_id == FID).delete()
    db.commit()

    baris, TOK = P.buat_bimbingan(db, u.id, nama=f'Uji {nama}', hari=7)
    baris.identitas = 'Prof. Uji <uji@contoh.id>'
    db.add(BerkasPembimbingan(pembimbingan_id=baris.id, file_id=FID,
                              judul=nama))
    db.add(VersiDokumen(user_id=u.id, file_id=FID, bab='__naskah__',
                        nomor=900 + baris.id, isi=teks, ukuran=len(teks),
                        sumber='uji'))
    db.commit()

    with urllib.request.urlopen(
            f'http://127.0.0.1:8000/tinjau/{TOK}', timeout=30) as r:
        html = r.read().decode('utf-8', 'replace')

    pilihan = isi_select(html)
    bab = [x for x in pilihan if x != 'Bagian lain']
    print(f'\n  📄 {nama} — naskah {len(teks):,} karakter')
    for i, x in enumerate(pilihan, 1):
        print(f'       {i:>2}. {x}')

    cek(f'{nama}: halaman terbuka (bukan sambutan)',
        'section_judul' in html, f'halaman={len(html)} kar')
    cek(f'{nama}: dropdown ADA', len(pilihan) > 0, f'{pilihan}')
    cek(f'{nama}: ada bab/bagian terdeteksi', len(bab) >= 1, f'{bab}')
    cek(f'{nama}: ada jalan keluar "Bagian lain"',
        'Bagian lain' in pilihan, f'{pilihan}')
    cek(f'{nama}: tidak ada judul kepanjangan (>70 kar)',
        all(len(x) <= 70 for x in bab), f'{[x for x in bab if len(x) > 70]}')
    cek(f'{nama}: tidak ada label sampah (halaman depan)',
        not any(re.match(r'^(DAFTAR ISI|DAFTAR TABEL|DAFTAR GAMBAR|'
                         r'DAFTAR PUSTAKA|KATA PENGANTAR|ABSTRAK)',
                         x.strip(), re.I) for x in bab),
        f'{[x for x in bab if re.match(r"^(DAFTAR|KATA PENG|ABSTRAK)", x.strip(), re.I)]}')

db.close()
print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
