"""Prioritas sumber artikel, Gas Bos 31 Okt 2026 19:03, diubah
menjadi seimbang 2-2-2-2 atas keputusan Bos 31 Okt 2026 19:36,
yang menggantikan prioritas Scopus penuh.

Urutan kelompok yang sama dipakai di tiga tempat:
1. Tampilan artikel pendukung di halaman proses, lewat
   urutkan_prioritas_sumber (Scopus dulu, stabil, bukan seimbang,
   karena tampilan hanya mengurutkan snapshot yang sudah seimbang).
2. Pemilihan snapshot panen di _refs_dari_harvest, lewat
   pilih_seimbang, sebelum potong 8.
3. Jalur cache hit di panen_semua, lewat pilih_seimbang, sebelum
   tulis_snapshot, supaya judul berulang tidak lolos dari seimbang.

Aturan seimbang, tepatnya: dari kandidat yang SUDAH lolos saring
relevansi dan filter tahun, sesudah dedup, ambil kuota 2 per sumber
(2 Scopus, 2 OpenAlex, 2 CrossRef, 2 Garuda), total 8, urutan
kelompok Scopus dulu, lalu OpenAlex, lalu CrossRef, lalu Garuda,
dan di dalam tiap sumber pertahankan urutan asli (stabil).
Bila satu sumber kurang dari 2, slot yang kurang diisi dari sumber
lain menurut prioritas Scopus, OpenAlex, CrossRef, Garuda, lain,
tetap dalam urutan asli di dalam sumber, sampai total 8 atau sampai
kandidat habis. Tidak pernah mengarang artikel, dan gerbang minimum
8 yang sudah ada tidak diubah di sini.

Sumber dinormalisasi huruf kecil dan dicocokkan mengandung nama,
supaya variasi ejaan seperti CrossRef dan Crossref diperlakukan sama.
Modul ini murni, tanpa impor aplikasi, supaya bisa dipakai dari
app/proses.py, app/pra_panen.py, maupun dari buku_umum_pipeline.py
tanpa impor melingkar.
"""

PRIORITAS_SUMBER = {
    'scopus': 0,
    'openalex': 1,
    'crossref': 2,
    'garuda': 3,
}

KUOTA_SEIMBANG_PER_SUMBER = 2
TOTAL_SEIMBANG = 8


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
    Dipakai tampilan saja, bukan pemilihan snapshot.
    """
    if not isinstance(daftar, (list, tuple)):
        return []
    return sorted(list(daftar),
                  key=lambda item: prioritas_sumber(sumber_dari_item(item)))


def pilih_seimbang(daftar, kuota=KUOTA_SEIMBANG_PER_SUMBER,
                   total=TOTAL_SEIMBANG, kunci=None):
    """Pilih artikel seimbang dari daftar kandidat, stabil.

    daftar: list atau tuple item, dalam urutan asli. Bukan list atau
    tuple menghasilkan list kosong. kunci: fungsi opsional yang
    menerima satu item dan mengembalikan nama sumbernya, dipakai
    bila item bukan dict artikel biasa, misalnya pasangan
    (baris_snapshot, ref) di jalur cache hit, di mana sumber ada
    di elemen pertama pasangan. Tanpa kunci, sumber diambil dengan
    sumber_dari_item.

    Langkah: kelompokkan menurut prioritas (Scopus, OpenAlex,
    CrossRef, Garuda, lain), pertahankan urutan asli di dalam tiap
    kelompok, ambil sampai kuota dari tiap kelompok bernama dalam
    urutan prioritas, lalu isi kekurangan dari sisa kelompok dalam
    urutan prioritas yang sama (termasuk kelompok lain di akhir),
    sampai total atau sampai kandidat habis. Daftar asli tidak
    diubah, hasil adalah list baru, tanpa duplikat, tanpa artikel
    yang tidak ada di masukan.
    """
    if not isinstance(daftar, (list, tuple)):
        return []
    if total is None or total <= 0:
        return []
    if kuota is None or kuota < 0:
        kuota = 0
    ambil_sumber = kunci if kunci is not None else sumber_dari_item
    kelompok = {0: [], 1: [], 2: [], 3: [], 4: []}
    for item in daftar:
        try:
            nama = ambil_sumber(item)
        except Exception:
            nama = ''
        kelompok[prioritas_sumber(nama)].append(item)
    terpilih = []
    for angka in (0, 1, 2, 3):
        terpilih.extend(kelompok[angka][:kuota])
        if len(terpilih) >= total:
            return terpilih[:total]
    for angka in (0, 1, 2, 3, 4):
        sisa = kelompok[angka][kuota:]
        for item in sisa:
            if len(terpilih) >= total:
                return terpilih[:total]
            terpilih.append(item)
    return terpilih
