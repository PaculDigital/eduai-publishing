#!/usr/bin/env python3
"""UJI BERGIGI: rusak template dengan 8 cara, gerbang WAJIB menangkap semua.

Setiap kerusakan disuntik ke SALINAN (template asli tidak disentuh),
lalu gerbang dijalankan dan harus GAGAL.
"""
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATE = SKILL / 'templates' / 'template-buku-resmi.docx'
GERBANG = HERE / 'periksa_buku_template.py'


def suntik(tujuan, ganti):
    """Salin template, lalu ganti isi document.xml / styles.xml.

    Ganti = daftar (lama, baru). WAJIB gagal keras bila pola tidak ketemu —
    kalau tidak, kerusakan tidak tersuntik dan gerbang seolah "buta".
    """
    with zipfile.ZipFile(TEMPLATE) as z:
        isi = {n: z.read(n) for n in z.namelist()}
    for berkas, pasangan in ganti.items():
        teks = isi[berkas].decode('utf-8')
        for lama, baru in pasangan:
            n = teks.count(lama)
            assert n > 0, (
                f'SUNTIKAN GAGAL: pola tidak ada di {berkas}: {lama[:60]!r}')
            teks = teks.replace(lama, baru)
            print(f'         disuntik {n}x: {lama[:46]}')
        isi[berkas] = teks.encode('utf-8')
    with zipfile.ZipFile(tujuan, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, b in isi.items():
            z.writestr(n, b)


def jalankan(p):
    r = subprocess.run([sys.executable, str(GERBANG), str(p)],
                       capture_output=True, text=True)
    gagal = [ln.strip() for ln in r.stdout.splitlines() if 'GAGAL' in ln]
    return r.returncode, gagal, r.stdout


KASUS = [
    ('D1 ukuran halaman diubah 14x20 -> 16x24',
     {'word/document.xml': [('w:w="7938" w:h="11340"', 'w:w="9072" w:h="13608"')]}),
    ('D2 batas kiri diubah 578 -> 1134',
     {'word/document.xml': [('w:left="578"', 'w:left="1134"')]}),
    ('D3 font isi Palatino -> Cambria',
     {'word/document.xml': [('w:ascii="Palatino Linotype"', 'w:ascii="Cambria"')]}),
    ('D4 ukuran isi 20 -> 24 (10pt jadi 12pt)',
     {'word/document.xml': [('<w:sz w:val="20"/>', '<w:sz w:val="24"/>')]}),
    ('D5 Heading1 font Trajan Pro -> Arial',
     {'word/styles.xml': [('w:ascii="Trajan Pro"', 'w:ascii="Arial"')]}),
    ('D6 Heading1 ukuran 44 -> 36 (22pt jadi 18pt)',
     {'word/styles.xml': [('<w:sz w:val="44"/><w:szCs w:val="44"/>',
                           '<w:sz w:val="36"/><w:szCs w:val="36"/>')]}),
    ('D7 isi rata both -> kiri',
     {'word/document.xml': [('<w:jc w:val="both"/>', '<w:jc w:val="left"/>')]}),
    ('D8 batas atas diubah 907 -> 1440',
     {'word/document.xml': [('w:top="907"', 'w:top="1440"')]}),
]

print(f'TEMPLATE : {TEMPLATE}')
print(f'GERBANG  : {GERBANG}\n')

#  Kontrol dulu: template UTUH wajib LULUS
kode, _, out = jalankan(TEMPLATE)
print(f'KONTROL  template utuh -> EXIT {kode} (harus 0)')
if kode != 0:
    print(out[-800:])
    sys.exit('BERHENTI: template utuh gagal -> gerbangnya salah')
print()

LULUS = GAGAL = 0
with tempfile.TemporaryDirectory() as td:
    for nama, ganti in KASUS:
        tujuan = Path(td) / f'{nama.split()[0]}.docx'
        suntik(tujuan, ganti)
        kode, gagal, out = jalankan(tujuan)
        tertangkap = kode == 1 and bool(gagal)
        if tertangkap:
            LULUS += 1
            print(f'  LULUS  {nama}  -> tertangkap: {len(gagal)} asersi gagal')
            print(f'         {gagal[0][:100]}')
        else:
            GAGAL += 1
            print(f'  GAGAL  {nama}  -> EXIT {kode}, tidak ada asersi gagal')
            print(f'         {out[-300:]}')

print('\n' + '=' * 66)
print(f'RINGKAS UJI BERGIGI: {LULUS} LULUS / {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
