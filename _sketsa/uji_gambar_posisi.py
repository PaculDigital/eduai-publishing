#!/usr/bin/env python3
"""UJI — gambar ditaruh TEPAT di akhir sub-bab (bukan akhir dokumen).

Naskah nyata: 349508cb13697288.docx (44.782 kar, sub-bab 2.1–2.5).
Target uji: sub-bab 2.3 → gambar harus muncul SETELAH isi 2.3 dan
SEBELUM judul "2.4 Kerangka Teori".

2 ARAH:
  A. Bagian yang ADA (2.3)          → gambar masuk di posisi benar
  B. Bagian yang TIDAK ADA (9.9)    → ok=False (jangan menebak)
"""
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_posisi_')
sys.path.insert(0, '/app')

from app import gambar as G                                    # noqa: E402
from app import state as S                                     # noqa: E402
from app import ai as A                                        # noqa: E402

L, GA = 0, 0


def _cocok_isi(par: str, bagian: str) -> bool:
    """True kalau paragraf ini JUDUL bagian (BUKAN baris daftar isi)."""
    t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', par)).strip()
    if not t.startswith(bagian):
        return False
    sisa = t[len(bagian):]
    if not sisa or sisa[0] not in '. \t':
        return False
    if re.search(r'\.{3,}', t) or re.search(r'\d{1,4}\s*$', t):
        return False
    return 0 < len(sisa.lstrip('. \t')) <= 120


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1; print(f'  ✅ {nama}')
    else:
        GA += 1; print(f'  ❌ {nama}  {bukti}')


SUMBER = Path('/app/uploads/6/349508cb13697288.docx')
DATA = [{'label': str(2020 + i), 'nilai': 120 + i * 70} for i in range(5)]
PNG = G.gambar_grafik(DATA, jenis='batang',
                      judul='Pertumbuhan Peserta Latihan Kriket',
                      satuan='orang')

print('══ UJI POSISI GAMBAR TEPAT DI SUB-BAB ══')
print(f'  PNG {len(PNG):,} byte · naskah {SUMBER.stat().st_size:,} byte')
print()

#  ── A. bagian 2.3 (ADA) ──
print('── A. bagian 2.3 (ADA) ──')
salin = Path('/app/_uji_posisi_A.docx')
shutil.copy(SUMBER, salin)
hasil = G.sisip_gambar_setelah_bagian(
    salin, PNG, bagian='2.3', bagian_berikut='2.4',
    keterangan='Gambar 2.3.1 Pertumbuhan Peserta Latihan Kriket')
print(f'   hasil: {hasil}')
cek('A. ok=True', hasil.get('ok') is True, str(hasil.get('sebab')))
cek('A. paragraf judul 2.3 ditemukan', hasil.get('paragraf_judul') is not None)
cek('A. paragraf akhir bagian ditemukan',
    hasil.get('paragraf_akhir_bagian') is not None)

#  periksa LETAK sesungguhnya di XML
with zipfile.ZipFile(salin) as z:
    doc = z.read('word/document.xml').decode('utf-8')
    media = [n for n in z.namelist() if n.endswith('.png')]

#  🔴 CATATAN: `doc.find('>2.4')` SALAH — ketemu di DAFTAR ISI dulu.
#     Ukur yang benar: paragraf (indeks <w:p>), bukan posisi teks mentah.
pars_ukur = re.findall(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', doc, re.S)
i_gbr = next((i for i, p in enumerate(pars_ukur) if 'grafik_ai' in p), None)
i_23 = next((i for i, p in enumerate(pars_ukur)
             if _cocok_isi(p, '2.3')), None)
i_24 = next((i for i, p in enumerate(pars_ukur)
             if _cocok_isi(p, '2.4')), None)
print(f'   indeks paragraf: 2.3@{i_23} · GAMBAR@{i_gbr} · 2.4@{i_24}')
cek('A. gambar SETELAH judul 2.3', i_gbr is not None and i_23 is not None
    and i_gbr > i_23, '')
cek('A. gambar SEBELUM judul 2.4', i_gbr is not None and i_24 is not None
    and i_gbr < i_24, '')

#  🔴 UJI KUAT: gambar TIDAK boleh ada di DAFTAR ISI.
#     Daftar isi = baris judul yang bertitik pengarah (".....") dan/atau
#     diakhiri nomor halaman. Buktikan paragraf tempat gambar masuk
#     BUKAN baris daftar isi.
pars_a = re.findall(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', doc, re.S)
idx_gambar = next((i for i, p in enumerate(pars_a) if 'grafik_ai' in p), None)
cek('A. paragraf gambar ditemukan', idx_gambar is not None)
isi_par_gambar = ''
if idx_gambar is not None:
    #  paragraf TEPAT sebelum gambar = akhir bagian sebenarnya
    seblm = idx_gambar - 1
    while seblm >= 0:
        t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', pars_a[seblm])).strip()
        if t:
            isi_par_gambar = t
            break
        seblm -= 1
print(f'   paragraf sebelum gambar (ke-{seblm}): {isi_par_gambar[:70]!r}')
cek('A. TIDAK di daftar isi (tanpa titik pengarah)',
    not re.search(r'\.{3,}', isi_par_gambar), isi_par_gambar[:50])
print(f'   indeks paragraf gambar: {idx_gambar} (daftar isi ada di 170-179)')
cek('A. gambar JAUH setelah daftar isi (idx > 200)',
    idx_gambar is not None and idx_gambar > 200, f'idx={idx_gambar}')
cek('A. ada 1 berkas png baru', len(media) == 1, f'{len(media)}')
cek('A. XML sah', re.search(r'<w:document[^>]*>', doc) is not None)

#  ── B. bagian yang TIDAK ADA → harus ok=False ──
print()
print('── B. DIRUSAK: bagian 9.9 (TIDAK ADA) ──')
salin2 = Path('/app/_uji_posisi_B.docx')
shutil.copy(SUMBER, salin2)
hasil2 = G.sisip_gambar_setelah_bagian(
    salin2, PNG, bagian='9.9', bagian_berikut='9.10')
print(f'   hasil: {hasil2}')
cek('B. ok=False (tidak menebak)', hasil2.get('ok') is False, str(hasil2))
cek('B. berkas TIDAK berubah',
    salin2.stat().st_size == SUMBER.stat().st_size,
    f'{salin2.stat().st_size} vs {SUMBER.stat().st_size}')

#  ── C. tabel/gambar lama tetap utuh ──
print()
print('── C. isi lama tidak rusak ──')
with zipfile.ZipFile(SUMBER) as z:
    n0 = set(z.namelist())
with zipfile.ZipFile(salin) as z:
    n1 = set(z.namelist())
cek('C. berkas lama tetap ada semua', n0.issubset(n1),
    f'hilang: {sorted(n0 - n1)[:3]}')
cek('C. hanya 1 berkas baru', len(n1 - n0) == 1, f'{sorted(n1 - n0)}')

print()
print(f'══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
