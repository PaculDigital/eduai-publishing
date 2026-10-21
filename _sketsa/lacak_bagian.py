"""LACAK: apakah loop benar-benar JALAN? Berapa isi `bagian_naskah`?

KENAPA: C10 bilang "konten kosong" TAPI log C9 (di dalam loop) TIDAK muncul.
    Kalau loop jalan ≥1×, C9 PASTI muncul saat konten kosong.
    ⇒ dugaan: loop TIDAK pernah dijalankan → `bagian_naskah` KOSONG.

Uji ini meniru jalur `_revisi_kerja` sampai titik itu PERSIS, dengan
menambahkan jejak cetak.
"""
import os
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix='lacak_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
os.makedirs(os.environ['EDUAI_UPLOAD_DIR'], exist_ok=True)
sys.path.insert(0, '/app')

import pathlib                                                        # noqa: E402
from app.ai import _teks_dari_docx, potong_cerdas, AI_POTONG_KARAKTER  # noqa: E402

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
print(f'berkas ada: {DOCX.exists()} · {DOCX.stat().st_size:,} byte')

#  ── Cara 1: persis seperti _revisi_kerja (teks dari docx) ──
naskah = _teks_dari_docx(DOCX)
print(f'\n1. _teks_dari_docx  → {len(naskah):,} kar')
bag1 = potong_cerdas(naskah)
print(f'   potong_cerdas    → {len(bag1)} bagian '
      f'(panjang={[len(x) for x in bag1]})')

#  ── Cara 2: dari dokumen yang SAMA tapi lewat jalur berbeda ──
#  Apakah `naskah` di _revisi_kerja berasal dari _isi_naskah (BUKAN _teks_dari_docx)?
import inspect                                                        # noqa: E402
import app.ai as A                                                    # noqa: E402

src = inspect.getsource(A._revisi_kerja)
print('\n2. dari mana `naskah` diambil di _revisi_kerja?')
for i, baris in enumerate(src.split('\n'), 1):
    if 'naskah =' in baris and 'potong' not in baris:
        print(f'   {i}: {baris.strip()[:100]}')

#  ── Cara 3: berapa bagian untuk berbagai ukuran ──
print('\n3. potong_cerdas pada berbagai ukuran:')
for n in (1000, 50000, 55000, 60000, 64243):
    teks = 'kata ' * (n // 5)
    print(f'   {n:>6,} kar → {len(potong_cerdas(teks))} bagian')

#  ── Cara 4: JSON header → naskah → potong ──
print('\n4. apakah JSON MENGIRIM naskah? cek rute /v1/revisi')
src2 = inspect.getsource(A._revisi_kerja)
for i, baris in enumerate(src2.split('\n'), 1):
    if 'json()' in baris or 'body.get' in baris or 'naskah' in baris.lower():
        print(f'   {i}: {baris.strip()[:110]}')
