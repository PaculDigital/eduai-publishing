#!/usr/bin/env python3
"""UJI BERGIGI v2: buktikan gerbang v2 menangkap lubang audit 22 Okt 2026.

Kerusakan-kerusakan ini pada gerbang LAMA (20 asersi) LOLOS semua —
dibuktikan saat audit commit 5652e01. Sekarang semuanya WAJIB tertangkap.
V9  = sectPr kedua berukuran salah (gerbang lama cuma membaca sectPr pertama)
V10 = font paragraf PENDEK (55 kar) diubah — basisnya buku contoh hasil
      generator (template asli hampir tak punya paragraf isi 40-149 kar).

Kontrol: template asli WAJIB lulus; buku contoh WAJIB lulus.
"""
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATE = SKILL / 'templates' / 'template-buku-resmi.docx'
GERBANG = HERE / 'periksa_buku_template.py'
GENERATOR = HERE / 'buat_buku.py'
CONTOH = HERE / 'contoh_buku.json'


def suntik(tujuan, sumber, ganti, buang=()):
    with zipfile.ZipFile(sumber) as z:
        isi = {n: z.read(n) for n in z.namelist()}
    for berkas, pasangan in (ganti or {}).items():
        teks = isi[berkas].decode('utf-8')
        for lama, baru in pasangan:
            n = teks.count(lama)
            assert n > 0, f'SUNTIKAN GAGAL: pola tidak ada di {berkas}: {lama[:60]!r}'
            teks = teks.replace(lama, baru)
            print(f'         disuntik {n}x: {lama[:46]}')
        isi[berkas] = teks.encode('utf-8')
    with zipfile.ZipFile(tujuan, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, b in isi.items():
            if n not in buang:
                z.writestr(n, b)


def suntik_khusus(tujuan, sumber, fungsi):
    with zipfile.ZipFile(sumber) as z:
        isi = {n: z.read(n) for n in z.namelist()}
    isi = fungsi(isi)
    with zipfile.ZipFile(tujuan, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, b in isi.items():
            z.writestr(n, b)


def jalankan(p):
    r = subprocess.run([sys.executable, str(GERBANG), str(p)],
                       capture_output=True, text=True)
    gagal = [ln.strip() for ln in r.stdout.splitlines() if 'GAGAL' in ln]
    return r.returncode, gagal


def sectpr_kedua_salah(isi):
    doc = isi['word/document.xml'].decode('utf-8')
    sisipan = ('<w:p><w:pPr><w:sectPr><w:pgSz w:w="1000" w:h="1000"/>'
               '<w:pgMar w:top="907" w:right="907" w:bottom="907" w:left="578" '
               'w:header="720" w:footer="720" w:gutter="505"/></w:sectPr></w:pPr></w:p>')
    kepala, _, ekor = doc.rpartition('<w:sectPr')
    assert ekor, 'sectPr terakhir tidak ditemukan'
    isi['word/document.xml'] = (kepala + sisipan + '<w:sectPr' + ekor).encode('utf-8')
    print('         disuntik 1x: sectPr kedua pgSz 1000x1000')
    return isi


def hapus_paragraf_pengantar(isi):
    doc = isi['word/document.xml'].decode('utf-8')
    pola = re.compile(r'<w:p(?: [^>]*)?>(?:(?!</w:p>).)*KATA PENGANTAR.*?</w:p>', re.S)
    doc2, n = pola.subn('', doc, count=1)
    assert n == 1, 'paragraf KATA PENGANTAR tidak ditemukan'
    isi['word/document.xml'] = doc2.encode('utf-8')
    print('         disuntik 1x: paragraf KATA PENGANTAR dibuang')
    return isi


def font_paragraf_pendek_salah(isi):
    doc = isi['word/document.xml'].decode('utf-8')
    target = 'Paragraf pendek pun harus tunduk pada format yang sama.'
    i = doc.index(target)
    awal = doc.rindex('<w:p ', 0, i)
    akhir = doc.index('</w:p>', i)
    para = doc[awal:akhir]
    assert 'Palatino Linotype' in para
    para2 = para.replace('w:ascii="Palatino Linotype"', 'w:ascii="Cambria"')
    isi['word/document.xml'] = (doc[:awal] + para2 + doc[akhir:]).encode('utf-8')
    print('         disuntik 1x: font paragraf pendek (55 kar) -> Cambria')
    return isi


KASUS_TEMPLATE = [
    ('V1 latar Heading2 F2F2F2 -> FF0000',
     lambda t: suntik(t, TEMPLATE, {'word/styles.xml': [('w:fill="F2F2F2"', 'w:fill="FF0000"')]})),
    ('V2 spasi Heading1 before 100 -> 900',
     lambda t: suntik(t, TEMPLATE, {'word/styles.xml': [('<w:spacing w:before="100" w:beforeAutospacing="1" w:after="240"/>', '<w:spacing w:before="900" w:beforeAutospacing="1" w:after="240"/>')]})),
    ('V3 font Normal Times New Roman -> Arial',
     lambda t: suntik(t, TEMPLATE, {'word/styles.xml': [('w:ascii="Times New Roman"', 'w:ascii="Arial"')]})),
    ('V4 footer2.xml dibuang',
     lambda t: suntik(t, TEMPLATE, {}, buang=('word/footer2.xml',))),
    ('V5 KATA PENGANTAR dihapus',
     lambda t: suntik_khusus(t, TEMPLATE, hapus_paragraf_pengantar)),
    ('V6 ukuran run sampul 28 -> 60',
     lambda t: suntik(t, TEMPLATE, {'word/document.xml': [('<w:sz w:val="28"/>', '<w:sz w:val="60"/>')]})),
    ('V7 margin header/footer 720 -> 1440',
     lambda t: suntik(t, TEMPLATE, {'word/document.xml': [('w:header="720" w:footer="720"', 'w:header="1440" w:footer="1440"')]})),
    ('V8 tab TOC 5938 -> 3000',
     lambda t: suntik(t, TEMPLATE, {'word/styles.xml': [('w:pos="5938"', 'w:pos="3000"')]})),
    ('V9 sectPr kedua ukuran salah',
     lambda t: suntik_khusus(t, TEMPLATE, sectpr_kedua_salah)),
]

print(f'TEMPLATE : {TEMPLATE}')
kode, _ = jalankan(TEMPLATE)
print(f'KONTROL  template utuh -> EXIT {kode} (harus 0)')
assert kode == 0, 'BERHENTI: template utuh gagal di gerbang v2'

LULUS = GAGAL = 0
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    contoh = td / 'buku-contoh.docx'
    r = subprocess.run([sys.executable, str(GENERATOR), str(CONTOH), str(contoh),
                        '--tanpa-gerbang'], capture_output=True, text=True)
    assert r.returncode == 0, f'generator gagal: {r.stdout[-400:]} {r.stderr[-400:]}'
    kode_c, _ = jalankan(contoh)
    print(f'KONTROL  buku contoh  -> EXIT {kode_c} (harus 0)')
    assert kode_c == 0, 'BERHENTI: buku contoh gagal di gerbang v2'

    kasus = list(KASUS_TEMPLATE)
    kasus.append(('V10 font paragraf pendek diubah (basis buku contoh)',
                  lambda t: suntik_khusus(t, contoh, font_paragraf_pendek_salah)))
    for nama, buat in kasus:
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
print(f'RINGKAS UJI BERGIGI v2: {LULUS} LULUS / {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
