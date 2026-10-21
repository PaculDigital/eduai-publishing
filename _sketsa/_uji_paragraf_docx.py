"""UJI PERBAIKAN PARAGRAF — 2 ARAH (standar Bos).

SEHAT  : docx Bos → paragraf HARUS banyak (≥100), BUKAN 1.
DIRUSAK: kembalikan `\\n` tunggal → uji HARUS GAGAL (bukti uji bergigi).

ATURAN: uji ini memanggil PERILAKU (fungsi sungguhan), bukan baca teks kode.
"""
import pathlib
import re
import sys

sys.path.insert(0, '/app')

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))
    return bool(syarat)


print('═' * 74)
print('UJI PARAGRAF DOCX — 2 ARAH')
print('═' * 74)

# ── 1. PERILAKU SUNGGUHAN (_teks_dari_docx versi tayang) ─────────────────
from importlib import reload                          # noqa: E402

import app.ai as A                                    # noqa: E402
reload(A)                                             # baca berkas dari disk

t = A._teks_dari_docx(DOCX)
n_par = len([p for p in re.split(r'\n{2,}', t) if p.strip()])

print('\nA. SEHAT — naskah Bos (63.797 kar, 478 paragraf Word)')
print(f'   panjang          : {len(t):,} kar')
print(f'   \\n\\n (pemisah)    : {t.count(chr(10) * 2):,}')
print(f'   paragraf hasil   : {n_par:,}')
cek('A1 paragraf BANYAK (bukan 1 blok)', n_par >= 100, f'{n_par} paragraf')
cek('A2 naskah tidak berubah panjangnya', 60000 < len(t) < 70000, f'{len(t):,} kar')

#  Tegakkan: jumlah <w:p> di docx == jumlah paragraf hasil
import zipfile                                        # noqa: E402
with zipfile.ZipFile(DOCX) as z:
    xml = z.read('word/document.xml').decode('utf-8', 'replace')
n_wp = len(re.findall(r'<w:p[ >]', xml))
cek('A3 jumlah paragraf = jumlah <w:p> docx (selisih <10%)',
    abs(n_par - n_wp) / n_wp < 0.10, f'hasil={n_par} vs docx={n_wp}')

print('\nB. URUTAN ISI TIDAK RUSAK (paragraf pertama & terakhir)')
paras = [p.strip() for p in re.split(r'\n{2,}', t) if p.strip()]
print(f'   paragraf[0]  : {paras[0][:70]!r}')
print(f'   paragraf[1]  : {paras[1][:70]!r}')
print(f'   paragraf[-1] : {paras[-1][:70]!r}')
cek('B1 paragraf pertama = judul naskah',
    'PENGARUH KUALITAS' in paras[0].upper())
cek('B2 paragraf kedua = baris lanjutan judul',
    'DIRI DIGITAL' in paras[1].upper() or 'KESIAPAN' in paras[1].upper())

print('\nC. SEHAT — teks dengan \\n\\n tetap benar (tidak rusak)')
uji = 'Satu.\n\nDua.\n\nTiga.'
cek('C1 pecah(\\n{2,}) tetap 3', len([p for p in re.split(r'\n{2,}', uji) if p.strip()]) == 3)

print('\nD. DIRUSAK — kembalikan \\n tunggal → HARUS GAGAL')
t_rusak = '\n'.join(paras)
n_rusak = len([p for p in re.split(r'\n{2,}', t_rusak) if p.strip()])
print(f'   paragraf kalau pakai \\n tunggal : {n_rusak}')
cek('D1 DIRUSAK menghasilkan 1 paragraf (bukti uji BERGIGI)',
    n_rusak == 1, f'{n_rusak} paragraf — jadi uji A1 memang bisa gagal')

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
