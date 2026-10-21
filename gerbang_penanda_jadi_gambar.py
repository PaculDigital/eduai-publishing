"""GERBANG: setiap penanda [TABEL]/[DIAGRAM] WAJIB jadi gambar/tabel di .docx.

🚨 AKAR YANG DITUTUP (20 Okt 2026, TERUKUR):
  Naskah memuat 2 penanda diagram, tetapi .docx hanya memuat 1 diagram.
  Diagram 1.1 TERCETAK MENTAH sebagai teks `[DIAGRAM 1.1: Perjalanan…]`.

  Sebab: `jev_buku_umum._POLA_DIAGRAM` MEWAJIBKAN `]` penutup. Penulis
  (LLM) memotong tanda itu — baris 135 karakter tanpa `]` — sehingga
  penanda lolos sebagai `paragraf`. Jalur regex (`parse_bab_file`) BENAR,
  jalur Jev SALAH ⇒ hanya jalur Jev yang kehilangan diagram.

  Sifat bug: SENYAP. Tidak ada error, .docx tetap terbit, `visual_hilang`
  kosong (karena PNG-nya memang ADA di disk) — padahal gambarnya tak masuk.

LULUS = 0 GAGAL.
"""
import os
import re
import sys

#  🚨 JEBAKAN UJI BERGIGI (terukur 20 Okt 2026): dulu baris ini menulis
#  `sys.path.insert(0, '/app')` MATI. Akibatnya gerbang SELALU membaca
#  /app walau dijalankan dari folder salinan /tmp ⇒ suntikan tak pernah
#  terbaca ⇒ uji bergigi melaporkan "0 BERGIGI, 3 HIASAN" padahal kodenya
#  sehat. Yang benar: pakai FOLDER BERKAS INI, supaya salinan benar-benar
#  diuji.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, '/app')      # cadangan untuk impor paket lain

import jev_buku_umum as J      # noqa: E402

lulus = 0
gagal = []


def cek(nama, syarat, pesan):
    global lulus
    if syarat:
        lulus += 1
    else:
        gagal.append(f'{nama}: {pesan}')


print('=' * 64)
print('GERBANG PENANDA ⇒ GAMBAR')
print('=' * 64)

#  ── 1. Penanda LENGKAP harus dikenali ──────────────────────────────────
LENGKAP = [
    ('[DIAGRAM 1.1: Judul - deskripsi]', 'diagram_marker'),
    ('[TABEL 2.3: Judul - A, B, C]', 'tabel_marker'),
    ('[diagram 1.4: huruf kecil]', 'diagram_marker'),
]
for teks, harus in LENGKAP:
    hasil = J._pecah_penanda(teks)
    cek(f'lengkap → {harus}: {teks[:26]}',
        len(hasil) == 1 and hasil[0][0] == harus,
        f'dapat {[h[0] for h in hasil]}')

#  ── 2. Penanda TERPOTONG (tanpa `]`) harus TETAP dikenali ─────────────
#  Ini inti gerbang — kasus NYATA dari buku 20 Okt 2026.
POTONG = [
    '[DIAGRAM 1.1: Perjalanan Matahari dan Bayanganmu - Gambar matahari '
    'bergerak dari timur ke barat, dengan tongkat di tenga',
    '[TABEL 1.1: Pengamatan Matahari, Suhu, dan Bayangan - Waktu, Posisi',
]
for teks in POTONG:
    hasil = J._pecah_penanda(teks)
    cek(f'terpotong dikenali: {teks[:24]}',
        len(hasil) == 1 and hasil[0][0] in ('diagram_marker', 'tabel_marker'),
        f'dapat {[h[0] for h in hasil]} — akan tercetak MENTAH')

#  ── 3. Penanda terpotong TIDAK boleh jadi paragraf ─────────────────────
for teks in POTONG:
    hasil = J._pecah_penanda(teks)
    cek(f'terpotong bukan paragraf: {teks[:24]}',
        all(h[0] != 'paragraf' or '[DIAGRAM' not in h[1]
            for h in hasil),
        'masih lolos sebagai paragraf ⇒ teks mentah di .docx')

#  ── 4. Teks biasa TIDAK boleh dianggap penanda ─────────────────────────
BIASA = [
    'Pagi hari, bayanganmu memanjang ke barat.',
    'Ini bukan penanda [tanda kurung biasa] sama sekali.',
    'Diagram ini menunjukkan perjalanan air.',
]
for teks in BIASA:
    hasil = J._pecah_penanda(teks)
    cek(f'teks biasa tetap paragraf: {teks[:26]}',
        len(hasil) == 1 and hasil[0][0] == 'paragraf',
        f'salah jadi {[h[0] for h in hasil]}')

#  ── 5. UJI NYATA pada naskah yang benar-benar dipakai ──────────────────
try:
    teks_bab = open('/tmp/uji_buku_docx/bab1.txt', encoding='utf-8').read()
except FileNotFoundError:
    teks_bab = ''
if teks_bab:
    naskah_penanda = re.findall(r'\[(?:DIAGRAM|TABEL)\s+\d+\.\d+',
                                teks_bab, re.IGNORECASE)
    blok, _ = J.blok_buku(teks_bab, pakai_cache=False)
    dari_jev = [b for b in blok if b[0] in ('diagram_marker',
                                            'tabel_marker')]
    cek('naskah nyata: jumlah penanda == jumlah blok penanda',
        len(naskah_penanda) == len(dari_jev),
        f'naskah {len(naskah_penanda)} penanda, Jev hanya '
        f'{len(dari_jev)} — sisanya tercetak mentah')
    mentah = [b[1][:40] for b in blok
              if b[0] == 'paragraf'
              and re.match(r'\s*\[(DIAGRAM|TABEL)\s+\d', b[1], re.I)]
    cek('naskah nyata: tidak ada penanda jadi paragraf',
        not mentah, f'masih mentah: {mentah}')
else:
    print('  ⚠️  /tmp/uji_buku_docx/bab1.txt tidak ada — uji naskah dilewati')

print()
for g in gagal:
    print(f'  ❌ {g}')
print('=' * 64)
print(f'{{"lulus": {lulus}, "gagal": {len(gagal)}}}')
print('=' * 64)
sys.exit(1 if gagal else 0)
