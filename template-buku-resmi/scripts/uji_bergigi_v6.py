#!/usr/bin/env python3
"""UJI BERGIGI v6 — gerbang BOOK CHAPTER (barang 18 & 20).

Daftar uji §9 SPESIFIKASI book chapter sendiri: judul bab diubah ke
20 pt WAJIB gagal; page break liar WAJIB gagal; heading berwarna
WAJIB gagal; chapter kepanjangan (> 15 hlm render) WAJIB gagal.
Kontrol utuh WAJIB lulus.
"""
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SINI = Path(__file__).resolve().parent
LULUS = GAGAL = 0


def ok(nama, syarat):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}')


def mutasi(src, dst, ubah):
    zin = zipfile.ZipFile(src)
    with zipfile.ZipFile(dst, 'w') as zout:
        for item in zin.namelist():
            data = zin.read(item)
            if item == 'word/document.xml':
                data = ubah(data.decode('utf-8')).encode('utf-8')
            zout.writestr(item, data)


def gerbang(path, *extra):
    return subprocess.run([sys.executable, str(SINI / 'periksa_book_chapter.py'),
                           str(path), *extra], capture_output=True, text=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix='bergigi6-'))
    spec = json.loads((SINI / 'contoh_chapter.json').read_text(encoding='utf-8'))
    emas = tmp / 'chapter.docx'
    r = subprocess.run([sys.executable, str(SINI / 'buat_book_chapter.py'),
                        str(SINI / 'contoh_chapter.json'), str(emas)],
                       capture_output=True, text=True)
    ok('KONTROL chapter contoh terbangun & lulus gerbang',
       r.returncode == 0 and emas.exists())

    def judul_20pt(xml):
        # hanya run judul (dua paragraf pertama): sz 28 -> 40
        return xml.replace('<w:sz w:val="28"/>', '<w:sz w:val="40"/>', 2)
    m1 = tmp / 'm1.docx'
    mutasi(emas, m1, judul_20pt)
    ok('MUTASI judul bab 20 pt -> gerbang MENOLAK', gerbang(m1, '--tanpa-halaman').returncode == 1)

    def pb_liar(xml):
        i = xml.find('Pendahuluan')
        j = xml.rfind('<w:pPr>', 0, i)
        return xml[:j + 7] + '<w:pageBreakBefore/>' + xml[j + 7:]
    m2 = tmp / 'm2.docx'
    mutasi(emas, m2, pb_liar)
    ok('MUTASI page break di Pendahuluan -> gerbang MENOLAK',
       gerbang(m2, '--tanpa-halaman').returncode == 1)

    def heading_warna(xml):
        i = xml.find('Heading1')
        j = xml.find('<w:b/>', i)
        return xml[:j] + '<w:b/><w:color w:val="366091"/>' + xml[j + 6:]
    m3 = tmp / 'm3.docx'
    mutasi(emas, m3, heading_warna)
    ok('MUTASI heading berwarna -> gerbang MENOLAK',
       gerbang(m3, '--tanpa-halaman').returncode == 1)

    panjang = json.loads(json.dumps(spec))
    panjang['section'][1]['paragraf'] = panjang['section'][1]['paragraf'] * 30
    p4 = tmp / 'panjang.json'
    p4.write_text(json.dumps(panjang))
    o4 = tmp / 'panjang.docx'
    r = subprocess.run([sys.executable, str(SINI / 'buat_book_chapter.py'),
                        str(p4), str(o4)], capture_output=True, text=True)
    ok('MUTASI chapter kepanjangan (> 15 hlm) -> generator MENOLAK',
       r.returncode != 0 and not o4.exists())

    def footer_warisan(xml):
        return xml.replace('</w:sectPr>',
                           '<w:footerReference w:type="default" r:id="rId99"/></w:sectPr>', 1)
    m4 = tmp / 'm4.docx'
    mutasi(emas, m4, footer_warisan)
    ok('MUTASI footer warisan template -> gerbang MENOLAK',
       gerbang(m4, '--tanpa-halaman').returncode == 1)

    print(f'\nRINGKAS UJI BERGIGI v6: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
