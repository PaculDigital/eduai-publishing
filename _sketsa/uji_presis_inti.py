"""UJI PERSIS `_revisi_kerja` — pakai `_teks_dari_body` + CEK ARTI JML.

TEMUAN PENTING: `ai_revisi()` (endpoint) memotong `naskah_kerja`, lalu
`_revisi_kerja()` memotong LAGI `naskah` → apakah hasilnya SAMA?
Kalau berbeda (mis. 1 vs 2), maka:
    endpoint : potong kuota 2×  (loop `for _ in range(jml)`)
    inti     : hanya 1 bagian  → hasil 1 bagian → konten kecil
"""
import os
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix='presis_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
os.makedirs(os.environ['EDUAI_UPLOAD_DIR'], exist_ok=True)
sys.path.insert(0, '/app')

import pathlib                                                        # noqa: E402
import app.ai as A                                                    # noqa: E402

#  ── Data uji nyata: berkas 49 milik user 6 ──
NAMA = '03ae7920ae93a7cc.docx'
from app.config import UPLOAD_DIR as _UD                                  # noqa: E402
import glob                                                               # noqa: E402
#  Pakai nama_simpan yang BENAR dari DB untuk file_id 49
import sqlite3                                                            # noqa: E402
_c = sqlite3.connect('/app/data/eduai.db')
_ns = _c.execute('SELECT nama_simpan FROM files WHERE id=49').fetchone()
_c.close()
NAMA = (_ns or [NAMA])[0]
P = _UD / '6' / NAMA
print(f'UPLOAD_DIR = {_UD}')
print(f'nama_simpan (DB) = {NAMA}')
print(f'berkas ada: {P.exists()} · {P.stat().st_size if P.exists() else 0:,} byte')

#  ── 1) JALUR SAMA PERSIS seperti _revisi_kerja ──
naskah = A._teks_dari_berkas(P, NAMA).strip()
print(f'1) _teks_dari_berkas → {len(naskah):,} kar')

naskah_utuh = naskah
bab = A.BAB_SELURUH
sebelum, sesudah = '', ''
if bab != A.BAB_SELURUH:
    sebelum, isi_bab, sesudah = A.ambil_bab(naskah, bab)
    if isi_bab:
        naskah = isi_bab

bagian_naskah = A.potong_cerdas(naskah)
jml = len(bagian_naskah)
print(f'2) potong_cerdas      → {jml} bagian '
      f'(panjang={[len(x) for x in bagian_naskah]})')

#  ── 2) BANDING: apakah endpoint & inti melihat jumlah bagian SAMA? ──
#  endpoint: bab dari body; body kirim bab='' → BAB_SELURUH → sama
print(f'3) ENDPOINT: bab={bab!r} → potong → {jml} bagian '
      f'→ potong kuota {jml}× · minta izin: {jml > 1}')

#  ── 3) Uji cap & sisa ──
print(f'4) AI_POTONG_KARAKTER={A.AI_POTONG_KARAKTER:,} · '
      f'AI_POTONG_MAKS_BAGIAN={A.AI_POTONG_MAKS_BAGIAN}')
total = sum(len(x) for x in bagian_naskah)
print(f'5) total teks bagian = {total:,} kar (naskah {len(naskah):,}) · '
      f'selisih {len(naskah) - total:,}')
