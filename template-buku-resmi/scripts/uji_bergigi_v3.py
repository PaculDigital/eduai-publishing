#!/usr/bin/env python3
"""UJI BERGIGI v3: buktikan gerbang menangkap kerusakan TABEL & GAMBAR.

Basis semua kasus = buku contoh hasil generator (memuat 1 tabel + 1 gambar).
Setiap kasus merusak TEPAT satu hal di wilayah tabel/gambar buku itu.
Kontrol: buku contoh utuh WAJIB lulus.
"""
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GERBANG = HERE / 'periksa_buku_template.py'
GENERATOR = HERE / 'buat_buku.py'
CONTOH = HERE / 'contoh_buku.json'


def jalankan(p):
    r = subprocess.run([sys.executable, str(GERBANG), str(p)],
                       capture_output=True, text=True)
    gagal = [ln.strip() for ln in r.stdout.splitlines() if 'GAGAL' in ln]
    return r.returncode, gagal


def suntik_wilayah(tujuan, sumber, penanda_awal, penanda_akhir, lama, baru):
    """Ganti pola HANYA di wilayah dokumen antara dua penanda."""
    with zipfile.ZipFile(sumber) as z:
        isi = {n: z.read(n) for n in z.namelist()}
    doc = isi['word/document.xml'].decode('utf-8')
    a = doc.index(penanda_awal)
    b = doc.index(penanda_akhir, a) + len(penanda_akhir)
    wilayah = doc[a:b]
    n = wilayah.count(lama)
    assert n > 0, f'pola tidak ada di wilayah: {lama[:50]!r}'
    wilayah = wilayah.replace(lama, baru)
    print(f'         disuntik {n}x di wilayah: {lama[:44]}')
    isi['word/document.xml'] = (doc[:a] + wilayah + doc[b:]).encode('utf-8')
    with zipfile.ZipFile(tujuan, 'w', zipfile.ZIP_DEFLATED) as z:
        for nm, bb in isi.items():
            z.writestr(nm, bb)


def suntik_dokumen(tujuan, sumber, fungsi):
    with zipfile.ZipFile(sumber) as z:
        isi = {n: z.read(n) for n in z.namelist()}
    doc = isi['word/document.xml'].decode('utf-8')
    isi['word/document.xml'] = fungsi(doc).encode('utf-8')
    with zipfile.ZipFile(tujuan, 'w', zipfile.ZIP_DEFLATED) as z:
        for nm, bb in isi.items():
            z.writestr(nm, bb)


def gambar_terlalu_lebar(doc):
    i = doc.index('wp:inline')
    awal = doc.rindex('<w:p>', 0, i)
    akhir = doc.index('</w:p>', i)
    para = doc[awal:akhir]
    para2 = re.sub(r'<wp:extent cx="\d+"', '<wp:extent cx="5000000"', para, count=1)
    assert para2 != para
    print('         disuntik 1x: cx gambar inline -> 5000000 (13,9 cm)')
    return doc[:awal] + para2 + doc[akhir:]


def keterangan_dibuang(doc):
    pola = re.compile(r'<w:p(?: [^>]*)?>(?:(?!</w:p>).)*Gambar: Contoh diagram batang.*?</w:p>', re.S)
    doc2, n = pola.subn('', doc, count=1)
    assert n == 1
    print('         disuntik 1x: paragraf keterangan gambar dibuang')
    return doc2


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    contoh = td / 'buku-contoh.docx'
    r = subprocess.run([sys.executable, str(GENERATOR), str(CONTOH), str(contoh),
                        '--tanpa-gerbang'], capture_output=True, text=True)
    assert r.returncode == 0, f'generator gagal: {r.stderr[-300:]}'
    kode, _ = jalankan(contoh)
    print(f'KONTROL  buku contoh utuh -> EXIT {kode} (harus 0)')
    assert kode == 0

    KASUS = [
        ('W1 lebar grid tabel diubah',
         lambda t: suntik_wilayah(t, contoh, '<w:tbl>', '</w:tbl>',
                                  '<w:gridCol w:w="2151"/>', '<w:gridCol w:w="2000"/>')),
        ('W2 warna garis tabel 808080 -> FF0000',
         lambda t: suntik_wilayah(t, contoh, '<w:tblBorders>', '</w:tblBorders>',
                                  'w:color="808080"', 'w:color="FF0000"')),
        ('W3 latar kepala tabel F2F2F2 dibuang',
         lambda t: suntik_wilayah(t, contoh, '<w:tbl>', '</w:tbl>',
                                  'w:fill="F2F2F2"', 'w:fill="FFFFFF"')),
        ('W4 font sel tabel Palatino -> Cambria',
         lambda t: suntik_wilayah(t, contoh, '<w:tbl>', '</w:tbl>',
                                  'w:ascii="Palatino Linotype"', 'w:ascii="Cambria"')),
        ('W5 gambar inline diperlebar melebihi area teks',
         lambda t: suntik_dokumen(t, contoh, gambar_terlalu_lebar)),
        ('W6 keterangan gambar dibuang',
         lambda t: suntik_dokumen(t, contoh, keterangan_dibuang)),
    ]
    LULUS = GAGAL = 0
    for nama, buat in KASUS:
        tujuan = td / (nama.split()[0] + '.docx')
        buat(tujuan)
        kode, gagal = jalankan(tujuan)
        if kode == 1 and gagal:
            LULUS += 1
            print(f'  LULUS  {nama} -> tertangkap: {gagal[0][:90]}')
        else:
            GAGAL += 1
            print(f'  GAGAL  {nama} -> EXIT {kode}, TIDAK tertangkap')

print('\n' + '=' * 66)
print(f'RINGKAS UJI BERGIGI v3: {LULUS} LULUS / {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
