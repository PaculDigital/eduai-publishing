#!/usr/bin/env python3
"""UJI BERGIGI J2: buktikan gerbang MENOLAK judul bab yang menyatu.

A: template asli (BAB I <w:br/> JUDUL)      -> J2 HARUS LULUS
B: <w:br/> dibuang (BAB IJUDUL satu baris)  -> J2 HARUS GAGAL
C: nomor bab bukan Romawi (BAB 1)           -> J2 HARUS GAGAL
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


def jalankan(p):
    r = subprocess.run([sys.executable, str(GERBANG), str(p)],
                       capture_output=True, text=True)
    j2 = [ln.strip() for ln in r.stdout.splitlines()
          if 'J2' in ln and ('LULUS' in ln or 'GAGAL' in ln)]
    return r.returncode, j2


def suntik(tujuan, ganti):
    with zipfile.ZipFile(TEMPLATE) as z:
        isi = {n: z.read(n) for n in z.namelist()}
    teks = isi['word/document.xml'].decode('utf-8')
    for lama, baru in ganti:
        n = teks.count(lama)
        assert n > 0, f'SUNTIKAN GAGAL — pola tidak ada: {lama[:60]!r}'
        teks = teks.replace(lama, baru)
        print(f'         disuntik {n}x: {lama[:44]}')
    isi['word/document.xml'] = teks.encode('utf-8')
    with zipfile.ZipFile(tujuan, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, b in isi.items():
            z.writestr(n, b)


print('A. template ASLI — J2 harus LULUS')
kode_a, j2_a = jalankan(TEMPLATE)
for ln in j2_a:
    print('   ', ln)
print(f'    EXIT {kode_a}\n')

LULUS = GAGAL = 0
with tempfile.TemporaryDirectory() as td:
    #  B: buang <w:br/> di dalam paragraf judul bab -> jadi SATU baris
    p_b = Path(td) / 'menyatu.docx'
    print('B. <w:br/> judul bab DIBUANG — J2 harus GAGAL')
    suntik(p_b, [('<w:t>BAB I</w:t></w:r><w:r w:rsidR="00A24D91" '
                  'w:rsidRPr="00DB1A37"><w:br/></w:r>',
                  '<w:t>BAB I</w:t></w:r>')])
    kode_b, j2_b = jalankan(p_b)
    for ln in j2_b:
        print('   ', ln)
    print(f'    EXIT {kode_b}')
    if kode_b != 0 and any('GAGAL' in x for x in j2_b):
        LULUS += 1
    else:
        GAGAL += 1
        print('    ⛔ GAGAL: gerbang TIDAK menangkap judul menyatu')

    #  C: nomor bab jadi angka Arab — ganti teks di DALAM paragraf Heading1
    p_c = Path(td) / 'bukan-romawi.docx'
    print('\nC. nomor bab jadi angka Arab (BAB I -> BAB 1) — J2 harus GAGAL')
    #  ⚠️ KOREKSI audit 22 Okt 2026 malam: pola '<w:t>BAB I</w:t>' muncul
    #  DUA kali — judul BAB II di template terpecah antar-run ('BAB I' +
    #  'I'), jadi replace-all menciptakan 'BAB 1I' (jebakan J7 persis).
    #  Suntikan yang benar: ganti kemunculan PERTAMA saja (judul BAB I).
    with zipfile.ZipFile(TEMPLATE) as z:
        isi_c = {n: z.read(n) for n in z.namelist()}
    teks_c = isi_c['word/document.xml'].decode('utf-8')
    n_c = teks_c.count('<w:t>BAB I</w:t>')
    assert n_c == 2, f'praduga jumlah run BAB I berubah: {n_c}'
    teks_c = teks_c.replace('<w:t>BAB I</w:t>', '<w:t>BAB 1</w:t>', 1)
    print('         disuntik 1x (pertama saja): <w:t>BAB I</w:t> -> BAB 1')
    isi_c['word/document.xml'] = teks_c.encode('utf-8')
    with zipfile.ZipFile(p_c, 'w', zipfile.ZIP_DEFLATED) as z:
        for n_berkas, b_berkas in isi_c.items():
            z.writestr(n_berkas, b_berkas)
    kode_c, j2_c = jalankan(p_c)
    for ln in j2_c:
        print('   ', ln)
    print(f'    EXIT {kode_c}')
    if kode_c != 0:
        LULUS += 1
    else:
        GAGAL += 1
        print('    ⛔ GAGAL: gerbang TIDAK menangkap nomor bukan Romawi')

print('\n' + '=' * 66)
print(f'RINGKAS J2 BERGIGI: {LULUS + 1} LULUS / {GAGAL} GAGAL '
      f'(A kontrol + {LULUS} suntikan)')
sys.exit(1 if GAGAL else 0)
