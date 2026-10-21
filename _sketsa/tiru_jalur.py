"""TIRU _revisi_kerja LENGKAP sampai C10 — dengan JEJAK cetak di tiap langkah.

KENAPA: C10 bilang `konten` kosong TAPI log C9 (dalam loop) tidak muncul.
    Kalau loop jalan, C9 PASTI muncul. Uji ini meniru urutannya PERSIS dan
    mencetak isi variabel penting di tiap titik.
"""
import os
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix='tiru_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
os.makedirs(os.environ['EDUAI_UPLOAD_DIR'], exist_ok=True)
sys.path.insert(0, '/app')

import pathlib                                                        # noqa: E402
from app.ai import (_teks_dari_berkas, potong_cerdas,                 # noqa: E402
                    _pisah_blok_komentar, BAB_SELURUH)

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
naskah = _teks_dari_berkas(DOCX, 'BAB1_drive_terbaru.docx').strip()
print(f'1. _teks_dari_berkas (jalur SERVER) → {len(naskah):,} kar')

#  ── 4a) PETA DOKUMEN ──
from app.state import petakan as _petakan, buang_daftar_isi as _buang  # noqa: E402
_utuh = naskah
_peta = _petakan(_buang(_utuh))
print(f'2. peta dokumen → {len(_peta)} bagian')
for x in _peta[:6]:
    print(f"     id={x.get('section_id')!r} isi={len(x.get('isi_teks','')):,} kar")

#  ── 4b) potong ──
bagian_naskah = potong_cerdas(naskah)
jml_bagian = len(bagian_naskah)
print(f'3. potong_cerdas → {jml_bagian} bagian '
      f'(panjang={[len(x) for x in bagian_naskah]})')

#  ── loop: apakah jalan? ──
print('4. LOOP — berapa kali dieksekusi?')
jalan = 0
for idx, potongan in enumerate(bagian_naskah, start=1):
    jalan += 1
    print(f'     bagian {idx}: {len(potongan):,} kar'
          f' → {"KOSONG!" if not potongan.strip() else "ada isi"}')
print(f'   → loop dieksekusi {jalan}×')

#  ── C10: konten ──
print(f'5. C10 akan memeriksa: hasil_bagian berisi {jalan} isi')
print(f'   konten = hasil_bagian[0] = '
      f'{len(bagian_naskah[0]) if bagian_naskah else 0:,} kar MENTAH')
print('   (konten diisi hasil AI, bukan potongan — di sini simulasi)')

#  ── CEK: apakah `bab` kosong membuat jalur lain? ──
print(f'\n6. BAB_SELURUH = {BAB_SELURUH!r}')
print(f'   komentar terpisah: {len(_pisah_blok_komentar("[K1-KUTIP-ASLI] a\\n[K1-GANTI-JADI] b"))}')
