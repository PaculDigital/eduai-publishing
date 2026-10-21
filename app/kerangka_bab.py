"""KERANGKA BAKU PER BAB — disesuaikan kaidah tiap bab (26Sep26).

📌 ARAHAN BOS: "bisa juga diterapkan di bab lainnya tapi disesuaikan babnya"

📌 KAIDAH TIAP BAB (dari skill penelitian-ilmiah + praktik skripsi/tesis):
   BAB I  PENDAHULUAN     — latar belakang → rumusan → tujuan → manfaat
   BAB II TINJAUAN PUSTAKA — teori, penelitian terdahulu, kerangka pikir,
                             HIPOTESIS (khusus kuantitatif)
   BAB III METODE          — desain, populasi/sampel, instrumen, analisis
   BAB IV HASIL & PEMBAHASAN — deskripsi data, uji hipotesis, pembahasan
   BAB V  KESIMPULAN        — simpulan, implikasi, keterbatasan, saran
   BAB VI DAFTAR PUSTAKA    — tidak berkerangka (dari mesin sitasi)

📌 TABEL & GRAFIK DIPASANG DI BAB YANG TEPAT (arahan Bos):
   BAB II  → kerangka pikir (gambar panah), tabel penelitian terdahulu
   BAB III → tabel populasi/sampel, tabel instrumen (kisi-kisi)
   BAB IV  → TABEL hasil uji + GRAFIK data (ini bab paling banyak visual)
"""
from __future__ import annotations

#  Bentuk: bab → list[(kode, judul sub-bab, [poin])]
#  Tiap bab punya `butuh` = kebutuhan tabel/grafik (dipakai mesin gambar)
KERANGKA_BAB: dict[str, dict] = {
    '1': {
        'nama': 'PENDAHULUAN',
        'sub_bab': [
            ('1.1', 'Latar Belakang Masalah', [
                'Fenomena/kondisi nyata di lapangan (data awal, berita, studi)',
                'Kesenjangan antara kenyataan dan harapan (research gap)',
                'Dukungan teori/penelitian terdahulu yang relevan dengan tema',
                'Alasan mengapa masalah ini penting diteliti sekarang',
            ]),
            ('1.2', 'Identifikasi Masalah', [
                'Daftar masalah yang terlihat dari latar belakang',
                'Pembatasan masalah yang akan diteliti (ruang lingkup)',
                'Pernyataan masalah utama yang menjadi fokus penelitian',
            ]),
            ('1.3', 'Rumusan Masalah', [
                'Pertanyaan penelitian sesuai hubungan antar variabel',
                'Rumusan yang dapat dijawab dengan data (bukan retorik)',
                'Kesesuaian rumusan dengan judul penelitian',
            ]),
            ('1.4', 'Tujuan dan Manfaat Penelitian', [
                'Tujuan sesuai rumusan masalah (satu rumusan satu tujuan)',
                'Manfaat teoretis (sumbangan bagi pengembangan ilmu)',
                'Manfaat praktis (bagi lembaga, praktisi, peneliti berikutnya)',
            ]),
            ('1.5', 'Sistematika Penulisan', [
                'Urutan isi tiap bab dijelaskan singkat',
                'Hubungan antar bab (alur logika penelitian)',
                'Posisi bab ini dalam keseluruhan naskah',
            ]),
        ],
        'butuh': {'tabel': [], 'grafik': []},
    },
    '2': {
        'nama': 'TINJAUAN PUSTAKA',
        'sub_bab': [
            ('2.1', 'Kajian Teori Variabel Penelitian', [
                'Teori utama variabel bebas (X) + definisi para ahli',
                'Teori utama variabel terikat (Y) + definisi para ahli',
                'Teori variabel perantara/penguat (kalau ada M/Z)',
            ]),
            ('2.2', 'Penelitian Terdahulu yang Relevan', [
                'Ringkasan penelitian sejenis (5 tahun terakhir)',
                'Persamaan dan perbedaan dengan penelitian ini',
                'Celah penelitian yang belum diteliti (gap)',
            ]),
            ('2.3', 'Kerangka Pikir Penelitian', [
                'Hubungan antar variabel dijelaskan naratif',
                'Alasan teoretis mengapa hubungan itu ada',
                'GAMBAR kerangka pikir (diagram panah antar variabel)',
            ]),
            ('2.4', 'Hipotesis Penelitian', [
                'Hipotesis per rumusan masalah (H1, H2, ...)',
                'Dasar teoretis tiap hipotesis',
                'Arah hubungan yang diduga (positif/negatif)',
            ]),
            ('2.5', 'Kerangka Konseptual Penelitian', [
                'Ringkasan model penelitian dari teori ke hipotesis',
                'Definisi operasional tiap variabel',
                'Batas pengertian istilah penting',
            ]),
        ],
        'butuh': {
            'tabel': ['penelitian terdahulu (penulis, tahun, variabel, hasil, '
                      'perbedaan)'],
            'grafik': ['kerangka pikir (diagram panah)'],
        },
    },
    '3': {
        'nama': 'METODE PENELITIAN',
        'sub_bab': [
            ('3.1', 'Jenis dan Pendekatan Penelitian', [
                'Jenis penelitian (kuantitatif/kualitatif) + alasannya',
                'Pendekatan yang dipakai (survei/eksperimen/kasus)',
                'Alasan pemilihan sesuai tujuan penelitian',
            ]),
            ('3.2', 'Lokasi dan Waktu Penelitian', [
                'Tempat penelitian + alasan pemilihannya',
                'Jadwal penelitian (tahap demi tahap)',
                'Kondisi objek penelitian secara umum',
            ]),
            ('3.3', 'Populasi dan Sampel', [
                'Jumlah populasi + sumber datanya',
                'Teknik pengambilan sampel + rumus yang dipakai',
                'Jumlah sampel yang ditetapkan + alasannya',
            ]),
            ('3.4', 'Teknik Pengumpulan Data', [
                'Jenis data (primer/sekunder)',
                'Instrumen yang dipakai (kuesioner/observasi/dokumen)',
                'Prosedur pengumpulan + uji coba instrumen',
            ]),
            ('3.5', 'Teknik Analisis Data', [
                'Uji instrumen (validitas & reliabilitas)',
                'Uji asumsi/prasyarat (normalitas, linearitas, dsb)',
                'Uji hipotesis yang dipakai + alat (SPSS/PLS/SmartPLS)',
            ]),
        ],
        'butuh': {
            'tabel': ['populasi & sampel', 'kisi-kisi instrumen'],
            'grafik': [],
        },
    },
    '4': {
        'nama': 'HASIL DAN PEMBAHASAN',
        'sub_bab': [
            ('4.1', 'Deskripsi Umum Objek Penelitian', [
                'Gambaran umum tempat/objek penelitian',
                'Karakteristik responden (jenis kelamin, usia, dsb)',
                'Tingkat pengembalian kuesioner/data',
            ]),
            ('4.2', 'Deskripsi Data Penelitian', [
                'Statistik deskriptif tiap variabel (mean, SD, kategori)',
                'Kategorisasi jawaban responden per variabel',
                'GRAFIK sebaran/skala tiap variabel',
            ]),
            ('4.3', 'Hasil Uji Prasyarat', [
                'Hasil uji normalitas + penafsirannya',
                'Hasil uji linearitas/multikolinearitas',
                'Kesimpulan data layak/tidak untuk uji lanjut',
            ]),
            ('4.4', 'Hasil Uji Hipotesis', [
                'Hasil tiap hipotesis (H1, H2, ...) + koefisiennya',
                'TABEL ringkasan hasil uji (koefisien, t/F, p-value)',
                'Keputusan tiap hipotesis (diterima/ditolak) + alasannya',
            ]),
            ('4.5', 'Pembahasan', [
                'Tafsir hasil dikaitkan dengan teori di BAB II',
                'Bandingkan dengan penelitian terdahulu (sama/beda + sebab)',
                'Implikasi praktis temuan bagi objek penelitian',
            ]),
        ],
        'butuh': {
            'tabel': ['statistik deskriptif', 'ringkasan hasil uji hipotesis'],
            'grafik': ['sebaran tiap variabel', 'hubungan antar variabel'],
        },
    },
    '5': {
        'nama': 'KESIMPULAN DAN SARAN',
        'sub_bab': [
            ('5.1', 'Kesimpulan', [
                'Jawaban tiap rumusan masalah (ringkas, tidak mengulang)',
                'Simpulan hasil uji hipotesis',
                'Pernyataan temuan utama penelitian',
            ]),
            ('5.2', 'Implikasi Penelitian', [
                'Implikasi teoretis bagi pengembangan ilmu',
                'Implikasi praktis bagi pihak terkait',
                'Kontribusi penelitian ini yang membedakan dari yang lain',
            ]),
            ('5.3', 'Keterbatasan Penelitian', [
                'Batasan yang dihadapi saat penelitian',
                'Pengaruh batasan itu terhadap hasil',
                'Hal yang belum tercakup dalam penelitian ini',
            ]),
            ('5.4', 'Saran', [
                'Saran bagi objek/lembaga penelitian',
                'Saran bagi peneliti berikutnya (apa yang bisa dikembangkan)',
                'Saran praktis yang dapat langsung dijalankan',
            ]),
            ('5.5', 'Penutup', [
                'Ringkasan akhir kontribusi penelitian',
                'Harapan penulis atas pemanfaatan hasil',
                'Pernyataan singkat penutup',
            ]),
        ],
        'butuh': {'tabel': [], 'grafik': []},
    },
}

#  Bab 6 = DAFTAR PUSTAKA → tidak berkerangka (hasil mesin sitasi langsung).
BAB_KERANGKA = list(KERANGKA_BAB.keys())


def ambil(bab: str) -> dict:
    """Kerangka baku satu bab. Return {} kalau belum didukung."""
    return KERANGKA_BAB.get(str(bab or '').strip(), {})


def daftar_bab() -> list[dict]:
    """Daftar bab yang BISA dibuat kerangkanya (untuk tombol pemilih)."""
    return [{'bab': k, 'nama': v['nama'],
             'sub_bab': len(v['sub_bab']),
             'butuh_tabel': len(v['butuh']['tabel']),
             'butuh_grafik': len(v['butuh']['grafik'])}
            for k, v in KERANGKA_BAB.items()]
