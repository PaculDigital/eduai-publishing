"""UKUR: apa yang terbaca sebagai BAB kalau naskah punya halaman depan lengkap?

PERTANYAAN BOS (24Sep26): "jika mahasiswa dokumennya sudah ada cover,
halaman persetujuan, halaman tabel, gambar, daftar isi dan daftar pustaka
— masuk dihitung atau tidak? Jadi penuh lagi dong."

Yang diukur: daftar bab yang muncul di DROPDOWN + kelompok yang terbentuk.
JANGAN menebak — jalankan dan lihat.
"""
import sys

sys.path.insert(0, '/app')
from app import kelompok_catatan as KC

#  ── NASKAH NYATA dengan halaman depan lengkap (pola umum skripsi) ──────
NASKAH = """SKRIPSI

PENGARUH KUALITAS PRODUK TERHADAP KEPUTUSAN PEMBELIAN

Diajukan sebagai salah satu syarat memperoleh gelar Sarjana

OLEH:
NAMA MAHASISWA
NIM 12345678

UNIVERSITAS CONTOH
FAKULTAS EKONOMI
2026

HALAMAN PERSETUJUAN PEMBIMBING

Skripsi dengan judul ini telah diperiksa dan disetujui.

Pembimbing I                        Pembimbing II

Dr. Contoh Satu                     Dr. Contoh Dua

HALAMAN PENGESAHAN

Skripsi ini telah dipertahankan di depan penguji.

DAFTAR ISI

HALAMAN JUDUL ................... i
HALAMAN PERSETUJUAN ............. ii
HALAMAN PENGESAHAN .............. iii
DAFTAR TABEL .................... v
DAFTAR GAMBAR ................... vi
BAB I PENDAHULUAN ............... 1
BAB II TINJAUAN PUSTAKA ......... 12
BAB III METODE PENELITIAN ....... 30
BAB IV HASIL DAN PEMBAHASAN ..... 45
BAB V KESIMPULAN ................ 60
DAFTAR PUSTAKA .................. 65

DAFTAR TABEL

Tabel 1.1 Jumlah penduduk ........ 3
Tabel 2.1 Penelitian terdahulu ... 15

DAFTAR GAMBAR

Gambar 2.1 Kerangka pemikiran .... 20

BAB I PENDAHULUAN

Latar belakang masalah penelitian ini adalah persaingan bisnis yang
semakin ketat.

BAB II TINJAUAN PUSTAKA

Teori kualitas produk menurut para ahli.

BAB III METODE PENELITIAN

Penelitian ini menggunakan metode kuantitatif.

BAB IV HASIL DAN PEMBAHASAN

Hasil penelitian menunjukkan pengaruh positif.

BAB V KESIMPULAN DAN SARAN

Kesimpulan dari penelitian ini adalah ada pengaruh positif.

DAFTAR PUSTAKA

Kotler, P. (2020). Manajemen Pemasaran. Jakarta: Erlangga.
"""

print('═' * 70)
print('APA YANG TERBACA SEBAGAI BAB — naskah dengan halaman depan lengkap')
print('═' * 70)

bab = KC.daftar_bab_naskah(NASKAH)
print(f'\n  Jumlah yang muncul di DROPDOWN: {len(bab)}')
for i, x in enumerate(bab, 1):
    print(f'   {i:>2}. {x["label"]}')

print('\n  ═══ APA YANG DIHARAPKAN (hanya bab isi) ═══')
print('       BAB I, BAB II, BAB III, BAB IV, BAB V  → 5')
print(f'  ═══ KENYATAAN: {len(bab)} ═══')
