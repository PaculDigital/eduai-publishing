"""Uji larangan em dash (U+2014), 29 Okt 2026. Jalankan dari root checkout:
  /opt/data/.venv/bin/python3 uji_em_dash.py
Berkas ini tidak mengandung karakter U+2014 literal; semua memakai escape."""

import sys

EM = '\u2014'
EN = '–'


def cek(nama, dapat, harap):
    ok = (dapat == harap) and (EM not in dapat)
    print(('LULUS' if ok else 'GAGAL'), '-', nama, '| dapat:', repr(dapat))
    return ok


from buku_umum_assembly import bersihkan_markdown_teks

semua = True
semua &= cek('spasi',
              bersihkan_markdown_teks('Hasil naik \u2014 penjualan melonjak.'),
              'Hasil naik, penjualan melonjak.')
semua &= cek('tanpa spasi',
              bersihkan_markdown_teks('kata\u2014kata'),
              'kata, kata')
semua &= cek('ganda',
              bersihkan_markdown_teks('A \u2014 B \u2014 C'),
              'A, B, C')
semua &= cek('akhir',
              bersihkan_markdown_teks('Bab ini \u2014'),
              'Bab ini')
semua &= cek('awal',
              bersihkan_markdown_teks('\u2014 Pembuka'),
              'Pembuka')
semua &= cek('multibaris',
              bersihkan_markdown_teks('Baris satu \u2014 lanjut\nBaris dua.'),
              'Baris satu, lanjut\nBaris dua.')
teks = bersihkan_markdown_teks('Rentang 2020–2025 dan kata-kata tetap.')
ok = (EN in teks) and ('-' in teks) and (EM not in teks) and (
    teks == 'Rentang 2020–2025 dan kata-kata tetap.')
print(('LULUS' if ok else 'GAGAL'),
      '- en dash dan hyphen dipertahankan | dapat:', repr(teks))
semua &= ok
teks = bersihkan_markdown_teks('**tebal** dan *miring*')
ok = (teks == 'tebal dan miring') and (EM not in teks)
print(('LULUS' if ok else 'GAGAL'),
      '- markdown lama tetap dibersihkan | dapat:', repr(teks))
semua &= ok
with open('buku_umum_pipeline.py', encoding='utf-8') as f:
    sumber = f.read()
awal = sumber.find('def editor_prompt')
akhir = sumber.find('\ndef ', awal + 1)
blok = sumber[awal:akhir]
ok = ('TANDA EM DASH' in blok) and ('U+2014' in blok)
print(('LULUS' if ok else 'GAGAL'),
      '- aturan editor 12 ada di editor_prompt')
semua &= ok
print('UJI-EM-DASH', 'LULUS SEMUA' if semua else 'ADA GAGAL')
sys.exit(0 if semua else 1)
