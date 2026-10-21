"""BUKTI: `tulis_docx.rakit()` MENGGANTI SELURUH NASKAH dgn jawaban potongan AI.

Uji 2 ARAH (standar Bos):
  A. Masukan = POTONGAN KECIL (seperti jawaban AI nyata 2.961 kar)
     → berapa paragraf dokumen yang HILANG?
  B. Masukan = NASKAH UTUH (seperti asumsi rancangan lama)
     → apakah aman?
"""
import pathlib
import re
import sys
import zipfile

sys.path.insert(0, '/app')
from app.tulis_docx import peta_paragraf, rakit                 # noqa: E402

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
with zipfile.ZipFile(DOCX) as z:
    xml = z.read('word/document.xml').decode('utf-8')

par = peta_paragraf(xml)
print('═' * 74)
print('DOKUMEN UJI')
print('═' * 74)
print(f'   paragraf badan : {len(par):,}')
print(f'   panjang xml    : {len(xml):,} kar')
awal_teks = '\n'.join(p['teks'] for p in par)
print(f'   teks paragraf  : {len(awal_teks):,} kar')

# ── A. JAWABAN AI NYATA (potongan kecil) ────────────────────────────────
print()
print('═' * 74)
print('A. MASUKAN = POTONGAN KECIL (jawaban AI nyata, 2.961 kar)')
print('═' * 74)
potongan = ('1.2  Rumusan Masalah\n'
            'Berdasarkan latar belakang yang telah diuraikan, penelitian ini '
            'bertujuan menganalisis pengaruh kualitas kehidupan kerja dan '
            'efikasi diri digital terhadap kinerja adaptif dengan kesiapan '
            'digital sebagai variabel mediasi.\n'
            'Kesenjangan penelitian yang hendak dijawab adalah belum adanya '
            'kajian yang menguji peran mediasi kesiapan digital.')
print(f'   masukan        : {len(potongan):,} kar (potongan)')

xml_baru, info = rakit(xml, potongan, bab_label='__seluruh__')
if not xml_baru:
    print(f'   ❌ DITOLAK: {info.get("pesan")}')
else:
    par_baru = peta_paragraf(xml_baru)
    teks_baru = '\n'.join(p['teks'] for p in par_baru)
    print(f'   paragraf SESUDAH : {len(par_baru):,} (dari {len(par):,})')
    print(f'   teks SESUDAH     : {len(teks_baru):,} kar (dari {len(awal_teks):,})')
    susut = 100 - (len(teks_baru) / len(awal_teks) * 100)
    print()
    print(f'   📉 NASKAH SUSUT  : {susut:.1f}%   ← {len(awal_teks)-len(teks_baru):,} kar HILANG')
    print(f'   info             : {info}')
    print()
    print('   --- 300 kar teks SESUDAH ---')
    print('   ' + teks_baru[:300].replace('\n', '\n   '))
    print()
    if susut > 50:
        print('   🚨 TERBUKTI: potongan MENGGANTIKAN seluruh naskah — naskah HANCUR.')
    else:
        print('   ✅ aman')

# ── B. MASUKAN = NASKAH UTUH ────────────────────────────────────────────
print()
print('═' * 74)
print('B. MASUKAN = NASKAH UTUH (asumsi rancangan lama)')
print('═' * 74)
xml_baru2, info2 = rakit(xml, awal_teks, bab_label='__seluruh__')
if not xml_baru2:
    print(f'   ❌ DITOLAK: {info2.get("pesan")}')
else:
    teks2 = '\n'.join(p['teks'] for p in peta_paragraf(xml_baru2))
    print(f'   teks SESUDAH : {len(teks2):,} kar (dari {len(awal_teks):,})')
    print(f'   info         : {info2}')
    print('   → jalur ini AMAN (naskah utuh diganti naskah utuh)')
