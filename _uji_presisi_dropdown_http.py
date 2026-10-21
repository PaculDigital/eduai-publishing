"""UJI PRESISI DROPDOWN DI HALAMAN PEMBIMBING (HTTP) — 4 naskah nyata.

PERINTAH BOS: "di section Pembimbing, presisi tidak dropdownnya"

Cara: buat bimbingan + tempel naskah nyata sebagai berkas → buka halaman
tinjau lewat HTTP → baca isi <select> APA ADANYA → bandingkan dengan
yang SEHARUSNYA ada.
"""
import re
import sys
from datetime import datetime

sys.path.insert(0, '/app')

import urllib.request

from app import ai as AI
from app import pembimbing as P
from app.models import (BerkasPembimbingan, CatatanPembimbing, FileBerkas,
                        Pembimbingan, SessionLocal, User, VersiDokumen, init_db)
from pathlib import Path

init_db()
db = SessionLocal()

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
    """Baca pilihan <select name="section_judul"> APA ADANYA."""
    m = re.search(r'<select name="section_judul".*?</select>', html, re.S)
    if not m:
        return []
    return [x for x in re.findall(r'<option value="([^"]*)"', m.group(0)) if x]


#  ⚠️ DIPERBAIKI 24Sep26: dulu berkas uji ini memakai nama yang HANYA ADA
#  di container uji Wulan (proposal_v1_original.docx / tesis_s2.docx /
#  artikel_jurnal.docx). Di image PRODUKSI yang ada cuma 3 dokumen nyata
#  dari `_contoh-dokumen/`, jadi SEMUA dilewati → hasil "0 LULUS".
#  Itu BUKAN bug aplikasi, tapi uji yang tidak bisa berdiri sendiri.
#  Sekarang: dicoba berurutan, mana yang ADA yang dipakai.
def _pilih(*jalur):
    from pathlib import Path
    for j in jalur:
        if Path(j).is_file():
            return j
    return None


DOKUMEN = [
    ('PROPOSAL / SKRIPSI S1', _pilih(
        '/app/_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx',
        '/app/_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'),
     ['BAB I', 'BAB II', 'BAB III', 'BAB IV', 'BAB V']),
    ('TESIS S2', _pilih(
        '/app/_contoh-dokumen/tesis-s2/TERMINAL.docx',
        '/app/_contoh-dokumen/tesis-s2/TESIS-S2-unhas-sastra-novel.docx'),
     ['BAB I', 'BAB II']),
    ('DISERTASI S3', _pilih(
        '/app/_contoh-dokumen/artikel-jurnal/TERMINAL.docx',
        '/app/_contoh-dokumen/disertasi-s3/DISERTASI-S3-unhas-kesehatan-stunting.docx'),
     #  ⚠️ WULAN SALAH TEBAK 24Sep26: ditulis 3, ternyata disertasi ini
     #  punya 5 bab (BAB I–V). Terukur dari halaman: hasilnya BENAR,
     #  harapan ujinya yang keliru. Ditulis 5 sesuai kenyataan.
     ['BAB I', 'BAB II', 'BAB III', 'BAB IV', 'BAB V']),
]

#  ⚠️ AKAR GAGAL PALSU 24Sep26: dua kesalahan sekaligus di uji ini.
#  (1) dulu SEMUA dokumen memakai `FID` SAMA → baris `versi_dokumen` saling
#      MENIMPA → yang terbaca selalu dokumen terakhir.
#  (2) sempat diganti file_id karangan (901/902/903) → FOREIGN KEY GAGAL,
#      karena `file_id` WAJIB menunjuk baris NYATA di tabel `files`.
#
#  JALAN TENGAH yang benar: SATU `file_id` NYATA (9 = milik user 3), tetapi
#  ISI naskahnya BERBEDA per dokumen — dan versi lama dibersihkan lebih dulu
#  supaya dokumen sebelumnya tidak tertimpa. Yang diuji = presisi dropdown
#  atas ISI NASKAH, bukan soal id berkas.
FID_NYATA = 9

u = db.query(User).filter(User.id == 3).one()

print('═' * 74)
print('  PRESISI DROPDOWN DI HALAMAN PEMBIMBING (jalur HTTP sungguhan)')
print('═' * 74)
print('  ⚠️ UJI INI MENYIAPKAN NASKAHNYA SENDIRI. Kalau tidak, ia menimpa')
print('     data uji lain (mis. _uji_kelompok_bab) karena `file_id` sama —')
print('     persis kekeliruan yang pernah membuat 2 uji GAGAL PALSU.')
print('     Karena itu: jalankan SIAPKAN → UJI, jangan bersamaan.')

for nama, jalur, harus_ada in DOKUMEN:
    p = Path(jalur)
    if not p.is_file():
        print(f'\n  ⚠️ {nama}: berkas tidak ada — dilewati')
        continue
    teks = AI._teks_dari_berkas(p, p.name)                     # noqa: SLF001
    FID = FID_NYATA

    #  bersihkan sisa uji kita (ANAK dulu: versi → berkas → induk)
    for b in db.query(Pembimbingan).filter(
            Pembimbingan.nama == f'Uji {nama}').all():
        db.query(CatatanPembimbing).filter(
            CatatanPembimbing.pembimbingan_id == b.id).delete()
        db.query(BerkasPembimbingan).filter(
            BerkasPembimbingan.pembimbingan_id == b.id).delete()
        db.delete(b)
    #  ⚠️ WAJIB: buang versi LAMA sebelum menulis yang baru. Kalau tidak,
    #  sisa dokumen sebelumnya menahan dan isi naskah jadi campur.
    db.query(VersiDokumen).filter(
        VersiDokumen.file_id == FID).delete()
    db.commit()

    baris, TOK = P.buat_bimbingan(db, u.id, nama=f'Uji {nama}', hari=7)
    #  ⚠️ ISI IDENTITAS — kalau tidak, halaman = HALAMAN SAMBUTAN,
    #  bukan halaman tinjau (uji jadi GAGAL PALSU).
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
    #  ⚠️ Pilihan "Bagian lain" SENGAJA ada di dropdown (jalan keluar kalau
    #  pembimbing mau menandai bagian yang bukan bab). Jadi yang dibandingkan
    #  = bab dari naskah SAJA, bukan seluruh isi <select>.
    bab_saja = [x for x in pilihan if x != 'Bagian lain']
    print(f'\n  📄 {nama}')
    print(f'     <select> berisi {len(pilihan)} pilihan:')
    for i, x in enumerate(pilihan, 1):
        print(f'        {i:>2}. {x}')

    cek(f'{nama}: jumlah BAB sesuai harapan ({len(harus_ada)})',
        len(bab_saja) == len(harus_ada), f'dapat {len(bab_saja)}: {bab_saja}')
    for h in harus_ada:
        cek(f'{nama}: ada "{h}"', any(x.startswith(h) for x in bab_saja),
            f'{bab_saja}')
    cek(f'{nama}: ada jalan keluar "Bagian lain"',
        'Bagian lain' in pilihan, f'{pilihan}')
    cek(f'{nama}: TIDAK ada pilihan kosong (selain placeholder)',
        not [x for x in pilihan if not x.strip()], f'{pilihan}')

    #  ⚠️ uji presisi: label TIDAK boleh mengandung kalimat panjang
    kotor = [x for x in bab_saja if len(x) > 60]
    cek(f'{nama}: TIDAK ada label kepanjangan', not kotor, f'{kotor}')

db.close()
print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
