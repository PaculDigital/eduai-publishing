"""LACAK JALUR LENGKAP: dari jawaban AI sampai keputusan C10.

KENAPA: 3× E2E gagal "hasil revisi KOSONG" padahal AI sudah patuh bentuk baru.
    Kali ini TIDAK ada log `invalid/retry` → berarti `_valid()` LOLOS.
    Jadi `konten` yang sampai ke C10 sudah KOSONG setelah dibersihkan.
    Uji ini meniru jalur itu PERSIS, mencetak di tiap langkah.
"""
import asyncio
import pathlib
import sys

sys.path.insert(0, '/app')
from app.ai import (_teks_dari_docx, _valid, bersihkan_jawaban_ai,   # noqa: E402
                    pakai_bentuk_baru, potong_cerdas,
                    _revisi_dengan_failover)

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
t = _teks_dari_docx(DOCX)
potongan = potong_cerdas(t)[0]
print(f'naskah {len(t):,} kar · potongan1 {len(potongan):,} kar')

KOMENTAR = ['Perbaiki kalimat pertama paragraf yang memuat '
            '"Perkembangan pesat teknologi dan transformasi digital" — '
            'buat lebih ringkas dan tambahkan penekanan pada tujuan '
            'penelitian.']
pesan = (f'NASKAH:\n{potongan}\n\nCATATAN PEMBIMBING:\n- {KOMENTAR[0]}\n')

jawab, model, info = asyncio.run(_revisi_dengan_failover(
    pesan, 1, naskah_banding=potongan))
print(f'\n===== JAWABAN AI ({len(jawab):,} kar) =====')
print(jawab)
print('===== AKHIR JAWABAN =====\n')

print('── LACAK ─────────────────────────────────────────────')
print(f'1. pakai_bentuk_baru(jawab)   : {pakai_bentuk_baru(jawab)}')
v = _valid(jawab, 1)
print(f'2. _valid(jawab, 1)           : {v!r}  {"(LOLOS)" if v is None else "(DITOLAK)"}')
bersih = bersihkan_jawaban_ai(jawab, potongan)
print(f'3. bersihkan_jawaban_ai       : {len(bersih):,} kar')
print(f'   → {"KOSONG → inilah sebab 503" if not bersih.strip() else "ADA ISI"}')
if bersih.strip():
    print(f'   isi: {bersih[:300]}')
