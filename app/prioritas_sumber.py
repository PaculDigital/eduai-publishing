"""Prioritas sumber artikel, Gas Bos 31 Okt 2026 19:03.

Urutan yang sama dipakai di dua tempat, supaya Scopus kelihatan dulu:
1. Tampilan artikel pendukung di halaman proses.
2. Pemilihan snapshot panen di _refs_dari_harvest, sebelum potong 8.

Urutan: Scopus (0), OpenAlex (1), CrossRef (2), Garuda (3), lain (4).
Di dalam satu sumber, urutan asli dipertahankan (sort stabil Python),
jadi tidak ada pengurutan ulang berdasarkan sitasi di dalam sumber.
Modul ini murni, tanpa impor aplikasi, supaya bisa dipakai dari
app/proses.py maupun dari buku_umum_pipeline.py tanpa impor melingkar.
Sumber dinormalisasi huruf kecil dan dicocokkan mengandung nama,
supaya variasi ejaan seperti CrossRef dan Crossref diperlakukan sama.
"""

PRIORITAS_SUMBER = {
    'scopus': 0,
    'openalex': 1,
    'crossref': 2,
    'garuda': 3,
}


def prioritas_sumber(nama):
    """Angka prioritas satu nama sumber, lain = 4."""
    if not nama:
        return 4
    kunci = str(nama).strip().lower()
    for nama_prioritas, angka in PRIORITAS_SUMBER.items():
        if nama_prioritas in kunci:
            return angka
    return 4


def sumber_dari_item(item):
    """Ambil nama sumber dari satu item artikel, dalam bentuk apa pun."""
    if isinstance(item, dict):
        return item.get('sumber') or item.get('source') or ''
    sumber = getattr(item, 'sumber', None)
    if sumber:
        return sumber
    return getattr(item, 'source', '') or ''


def urutkan_prioritas_sumber(daftar):
    """Urutkan daftar artikel dengan prioritas sumber, stabil.

    Masukan bukan list atau tuple dikembalikan apa adanya sebagai
    list kosong, supaya pemanggil display-only tidak error.
    Daftar asli tidak diubah, hasil adalah list baru.
    """
    if not isinstance(daftar, (list, tuple)):
        return []
    return sorted(list(daftar),
                  key=lambda item: prioritas_sumber(sumber_dari_item(item)))
