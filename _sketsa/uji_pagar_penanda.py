#!/usr/bin/env python3
"""UJI: penanda tabel/gambar TIDAK BOLEH lolos ke dokumen mahasiswa.

2 arah: SEHAT (ada penanda → dibuang) · DIRUSAK (penanda tetap → GAGAL).
"""
import sys

sys.path.insert(0, '/app')
from app import ai as A                                     # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')


print('══ 1. BENTUK BARU (KUTIP-ASLI/GANTI-JADI) ══')
jawab = (
    '[K1-KUTIP-ASLI]\nPerkembangan penelitian pada empat ranah.\n'
    '[K1-GANTI-JADI]\n[[TABEL-6: 5 baris × 3 kolom — JANGAN diubah, ini konteks]]\n'
    'Tabel berikut memetakan perkembangan terkini pada setiap ranah.\n'
    '[[/TABEL-6]]\n'
)
bersih = A.bersihkan_jawaban_ai(jawab)
print(f'  hasil: {bersih[:150]!r}')
cek('penanda TABEL dibuang', '[[' not in bersih and 'TABEL-6' not in bersih)
cek('isi naskah TETAP ada', 'Tabel berikut memetakan' in bersih)

print()
print('══ 2. GAMBAR ikut dibuang ══')
jawab2 = ('[K1-KUTIP-ASLI]\nKalimat lama yang dikutip.\n'
          '[K1-GANTI-JADI]\n'
          '[[GAMBAR-1: di sini — JANGAN diubah, ini konteks]]\n'
          'Kalimat baru yang benar.\n')
b2 = A.bersihkan_jawaban_ai(jawab2)
print(f'  hasil: {b2[:120]!r}')
cek('penanda GAMBAR dibuang', 'GAMBAR-1' not in b2 and '[[' not in b2)
cek('isi tetap ada', 'Kalimat baru yang benar' in b2)

print()
print('══ 3. BENTUK LAMA (jawaban bebas) ══')
jawab3 = 'Kalimat naskah biasa.\n[[TABEL-3: 2 baris × 2 kolom — JANGAN diubah]]\nKalimat berikutnya.'
b3 = A.bersihkan_jawaban_ai(jawab3)
print(f'  hasil: {b3!r}')
cek('penanda dibuang di bentuk lama', '[[' not in b3 and 'TABEL-3' not in b3)
cek('kalimat tetap ada', 'Kalimat naskah biasa' in b3 and 'Kalimat berikutnya' in b3)

print()
print('══ 4. DIRUSAK — kalau pembersih DIMATIKAN, harus GAGAL ══')
#  simulasikan: regex penanda tabel dibuat tidak cocok (uji palsu-bisa-gagal)
import re as _re
pola_asli = A._RE_PENANDA_TABEL.pattern
A._RE_PENANDA_TABEL = _re.compile(r'ZZZTIDAKAKANCOCOKZZZ')
b4 = A.bersihkan_jawaban_ai(jawab)
A._RE_PENANDA_TABEL = _re.compile(pola_asli)     # pulihkan
cek('tanpa pembersih → penanda LOLOS (bukti uji bukan palsu)',
    'TABEL-6' in b4, '(penanda tetap hilang padahal pembersih mati → uji palsu!)')
print(f'     (dirusak: penanda masih ada? {"ya" if "TABEL-6" in b4 else "TIDAK"})')

print()
print('══ 5. TABEL DI TENGAH KALIMAT (kasus paling sulit) ══')
jawab5 = ('[K1-KUTIP-ASLI]\nKalimat lama.\n[K1-GANTI-JADI]\n'
          'Sebelum tabel. [[TABEL-1: 3 baris — JANGAN diubah]] Sesudah tabel.')
b5 = A.bersihkan_jawaban_ai(jawab5)
print(f'  hasil: {b5!r}')
cek('penanda TENGAH kalimat ikut dibuang', 'TABEL-1' not in b5)
cek('teks sebelum & sesudah tetap', 'Sebelum tabel' in b5 and 'Sesudah tabel' in b5)

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
sys.exit(1 if GAGAL else 0)