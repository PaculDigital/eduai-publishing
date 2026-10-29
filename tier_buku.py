"""Tier buku: Hemat / Normal / Full (perintah Boss 29 Okt 2026).

Tier = paket MASUKAN, bukan janji halaman pasti. Halaman adalah hasil
(jumlah bab x ~25 halaman/bab, dari bukti buku 219: 8 bab -> ~200-an
halaman, Bab 7 di halaman 176), jadi rentang halaman di sini PERKIRAAN
dengan toleransi; hasil di luar rentang DITERIMA apa adanya (perintah
Boss), tidak dipaksakan. Mutu TIDAK diturunkan: gerbang mutu (mutu
[1]-[6] + gerbang U/R/Rw) berlaku sama untuk semua tier; yang berkurang
hanya JUMLAH pembahasan (bab lebih sedikit) dan jumlah ilustrasi adegan.
Tabel/diagram TIDAK kena cap ilustrasi (wajib gerbang R3).
Harga per tier DITUNDA (dibahas terpisah, perintah Boss); modul ini
tidak menyentuh harga sama sekali.
"""
TIER_BUKU = {
    'hemat': {'bab': 5, 'ilustrasi_maks': 2, 'perkiraan_halaman': '100-150'},
    'normal': {'bab': 8, 'ilustrasi_maks': None, 'perkiraan_halaman': '150-200'},
    'full': {'bab': 12, 'ilustrasi_maks': None, 'perkiraan_halaman': '180-300'},
}
DEFAULT_TIER = 'normal'


def tier_buku(nama):
    """Normalisasi nama tier; tidak dikenal / kosong -> 'normal'."""
    nama = (nama or '').strip().lower()
    return nama if nama in TIER_BUKU else DEFAULT_TIER


def jumlah_bab(tier):
    """Jumlah bab untuk satu tier (hemat 5, normal 8, full 12)."""
    return TIER_BUKU[tier_buku(tier)]['bab']


def boleh_ilustrasi(tier, bab_num):
    """Hemat: ilustrasi adegan hanya untuk bab 1-2 (maks 2 total).
    Tier lain: tanpa cap."""
    maks = TIER_BUKU[tier_buku(tier)]['ilustrasi_maks']
    return True if maks is None else bab_num <= maks
