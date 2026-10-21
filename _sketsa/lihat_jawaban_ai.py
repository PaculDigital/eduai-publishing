"""LIHAT: apa yang SEBENARNYA dijawab AI dengan prompt PRODUKSI?

KENAPA: proses gagal "hasil revisi KOSONG" padahal prompt sudah minta
    bentuk KUTIP-ASLI/GANTI-JADI. Dugaan: `bersihkan_jawaban_ai()`
    membuang penanda → tersisa kosong.

Uji ini memakai PROMPT PRODUKSI ASLI (bukan karangan Wulan).
"""
import asyncio
import pathlib
import sys

sys.path.insert(0, '/app')
from app.ai import (_teks_dari_docx, bersihkan_jawaban_ai,        # noqa: E402
                    potong_cerdas, _revisi_dengan_failover)

DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
t = _teks_dari_docx(DOCX)
bagian = potong_cerdas(t)
potongan = bagian[0]
print(f'naskah {len(t):,} kar → {len(bagian)} bagian · potongan1 '
      f'{len(potongan):,} kar')

#  Cari paragraf yang MEMANG ADA di potongan
paras = [p.strip() for p in potongan.split('\n\n') if len(p.strip()) > 150]
print(f'paragraf isi di potongan: {len(paras)}')

KOMENTAR = ['Perbaiki kalimat pertama paragraf yang memuat '
            '"Perkembangan pesat teknologi dan transformasi digital" — '
            'buat lebih ringkas dan tambahkan penekanan pada tujuan '
            'penelitian.']

#  ── Pakai PROMPT PRODUKSI yang sebenarnya ──
from app.ai import PROMPT_REVISI, SYSTEM_REVISI                          # noqa: E402
print(f'PROMPT_REVISI  : {len(PROMPT_REVISI):,} kar')
print(f'SYSTEM_REVISI  : {len(SYSTEM_REVISI):,} kar')
#  Bentuk pesan sebenarnya: system + naskah + komentar (tanpa konteks tetangga)
pesan = (f'NASKAH:\n{potongan}\n\n'
         f'CATATAN PEMBIMBING:\n- {KOMENTAR[0]}\n')
print(f'pesan pemakai  : {len(pesan):,} kar')

print('\nmemanggil AI (prompt produksi)…')
jawab, model, info = asyncio.run(_revisi_dengan_failover(
    pesan, 1, naskah_banding=potongan))
print(f'model={model} token=in{info.get("token_in"):,}/out{info.get("token_out"):,}')
print(f'PANJANG JAWABAN MENTAH: {len(jawab):,} kar')
print('\n--- 900 kar pertama jawaban MENTAH ---')
print(jawab[:900])

#  ── Lalu BERSIHKAN seperti produksi ──
bersih = bersihkan_jawaban_ai(jawab, potongan)
print(f'\nPANJANG SETELAH BERSIHKAN: {len(bersih):,} kar')
print(f'   → {"KOSONG! inilah sebab kegagalan" if not bersih.strip() else "ada isi"}')
if bersih.strip():
    print('--- 400 kar pertama hasil bersih ---')
    print(bersih[:400])
pathlib.Path('/app/_jawab_mentah.txt').write_text(jawab)
