"""UJI GERBANG `_valid()` — 2 ARAH + BERGIGI (25Sep26, AKAR #7 & #8).

KENAPA ADA: 25Sep26 E2E nyata membuktikan `_valid()` MELOLOSKAN jawaban yang
tidak patuh bentuk pipa, lalu jawaban itu BARU ditolak `pipa.periksa()` di
hilir → 503 + mahasiswa lihat "Gagal" padahal 2 model sudah dicoba.

Yang diuji: 4 BENTUK JAWABAN SAH harus DITERIMA, dan 3 BENTUK CACAT harus
DITOLAK. Dua arah — supaya pagar tidak dilonggarkan tanpa sadar.

JALANKAN (di dalam container):
    docker exec -w /app eduai-app python3 _uji_valid_pipa.py
"""
import sys

sys.path.insert(0, '/app')

import app.ai as A                                                    # noqa: E402

#  ── BAHAN ────────────────────────────────────────────────────────────────
KUTIP_A = 'kalimat asli yang panjang sekali disini ya bos supaya lewat ambang'
GANTI_A = 'kalimat baru yang lebih panjang juga disini baik dan bermakna'
NASKAH = ('Paragraf naskah pembanding yang cukup panjang untuk mengukur '
          'apakah jawaban hanya salinan atau bukan. ') * 20

SAH = [
    ('BENTUK BARU (kutip+ganti)',
     f'[PROFIL] x\n[K1-KUTIP-ASLI] {KUTIP_A}\n[K1-GANTI-JADI] {GANTI_A}'),
    ('TIDAK ADA PERUBAHAN (jujur)',
     '[PROFIL] x\nTIDAK ADA PERUBAHAN\nBagian tidak ditemukan di sini'),
    ('[K1-TIDAK] (varian AI nyata)',
     '[PROFIL] x\n[K1-TIDAK]\nTIDAK ADA PERUBAHAN'),
    ('CAKUPAN TOLAK',
     '[PROFIL] x\n[K1-CAKUPAN: tolak]'),
    ('CAMPUR: K1 revisi + K2 tolak',
     f'[PROFIL] x\n[K1-KUTIP-ASLI] {KUTIP_A}\n[K1-GANTI-JADI] {GANTI_A}\n'
     '[K2-CAKUPAN: tolak]'),
]

CACAT = [
    ('BLOK SUNGGUHAN KOSONG', '[PROFIL] x\n[K1]\n'),
    ('SALINAN NASKAH', f'[PROFIL] x\n[K1] {NASKAH[:200]}'),
    ('GAYA LAMA (tanpa penanda pipa)',
     '[PROFIL] x\n[K1] revisi gaya lama yang cukup panjang ini ya bos'),
]

lulus = gagal = 0


def jalankan(nama, jawab, harap_valid, catatan=''):
    global lulus, gagal
    A._NASKAH_BANDING = NASKAH          # titip naskah pembanding
    hasil = A._valid(jawab, 1)
    A._NASKAH_BANDING = ''
    diterima = hasil is None
    ok = diterima == harap_valid
    if ok:
        lulus += 1
    else:
        gagal += 1
    tanda = '✅' if ok else '❌'
    print(f'  {tanda} {nama}')
    print(f'       harap={"DITERIMA" if harap_valid else "DITOLAK"} · '
          f'nyata={"DITERIMA" if diterima else "DITOLAK"} · {hasil!r}')
    if catatan:
        print(f'       {catatan}')


print('═' * 74)
print('  UJI GERBANG `_valid()` — 2 ARAH (SAH harus LOLOS · CACAT harus TOLAK)')
print('═' * 74)

print('\n── A. JAWABAN SAH (WAJIB DITERIMA) ──')
for nama, jawab in SAH:
    jalankan(nama, jawab, True)

print('\n── B. JAWABAN CACAT (WAJIB DITOLAK) ──')
for nama, jawab in CACAT:
    jalankan(nama, jawab, False)

print()
print('═' * 74)
print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
print('═' * 74)
sys.exit(1 if gagal else 0)
