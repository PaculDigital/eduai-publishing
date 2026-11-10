"""KEPUTUSAN SAMBUNG BARIS OLEH KODE — tanpa Jev, tanpa tebakan bentuk.

Dipakai pass-1 stitch di dua tempat:
  · `app/konversi._pecah_blok`  — pasangan baris berurutan.
  · `peta3_jev._stitch_baris`   — pasangan lintas baris-kosong.
Modul ini MURNI (stdlib saja) supaya bisa diuji offline tanpa modul berat.

`sambung_kode(a, b)` -> True | False | None
  True  = PASTI sambung. Bukan tebakan: kalimatnya BELUM SELESAI secara
          logika (fragmen 1-2 huruf, diakhiri koma/strip/kurung buka, atau
          kata terakhirnya kata gantung yang wajib diikuti lanjutan).
  False = PASTI tidak sambung. B juga unsur baru (nomor halaman, judul,
          baris tabel), atau A sudah kalimat selesai.
  None  = kode tidak bisa putuskan -> tanya Jev (jalur lama, tidak berubah).

ATURAN INDUK (putusan Bos 10 Okt 2026): kode TIDAK BOLEH menebak bentuk
lewat heuristik — itu pernah menelan judul asli (`_rapikan_baris.py` gagal
3x). Karena itu yang diotomasi di sini HANYA yang dipaksa logika bahasa:
kalimat selesai tidak bisa dilanjutkan, judul tidak melanjutkan kalimat,
dan fragmen 1-2 huruf bukan unsur berdiri sendiri. Yang meragukan tetap
ditanya ke Jev.
"""
from __future__ import annotations

import re

# ── akhir kalimat: titik / seru / tanya / elipsis / titik-koma / titik-dua.
#    Titik-dua ikut: "Tujuan:" tidak melanjutkan kalimat sebelumnya.
_AKHIR_KALIMAT = re.compile(r'[.!?\u2026;:]["\')\]]*\s*$')

# ── Singkatan yang diakhiri titik tapi BUKAN akhir kalimat.
_SINGKATAN = {
    'dr', 'drs', 'prof', 'h', 'hj', 'ir', 'st', 'sh', 'mm', 'mpd', 'msi',
    'dkk', 'dll', 'dsb', 'dst', 'bpk', 'ibu', 'sdr', 'tn', 'ny', 'no',
    'hal', 'jil', 'ed', 'vol', 'th', 'tgl', 'jl', 'al', 'etc', 'vs',
    'mr', 'mrs', 'ms', 'br', 'sc', 'spd', 'sag', 'sos',
}

# ── Kata gantung: kata terakhir baris yang WAJIB diikuti lanjutan dalam
#    kalimat yang sama (konjungsi / preposisi / kopula). Judul tidak pernah
#    diakhiri kata-kata ini, jadi ini BUKAN tebakan bentuk.
_KATA_GANTUNG = {
    'dan', 'yang', 'di', 'ke', 'dari', 'untuk', 'dengan', 'atau', 'serta',
    'dalam', 'pada', 'oleh', 'sebagai', 'adalah', 'bahwa', 'jika', 'karena',
    'agar', 'supaya', 'yaitu', 'yakni', 'saat', 'ketika', 'sambil', 'tanpa',
    'antara', 'melalui', 'terhadap', 'kepada', 'demi', 'guna', 'hingga',
    'sampai', 'sejak', 'sebelum', 'sesudah', 'setelah', 'apabila',
    'meskipun', 'walaupun', 'namun', 'tetapi', 'sedangkan', 'sementara',
    'juga', 'pun', 'lah', 'kah', 'tah',
}

_POLA_BAB = re.compile(r'^BAB\s+([IVX0-9]+)\b', re.I)
_POLA_NOMOR_HALAMAN = re.compile(r'^\d{1,3}$')
_POLA_NOMOR_JUDUL = re.compile(r'^\d+(?:\.\d+)*\.?\s+\S')
_ROMAWI_TUNGGAL = re.compile(r'^[IVXLC]+$', re.I)


def tanpa_nomor_halaman(s: str) -> str:
    """Kupas awalan nomor halaman ("13 BAB I" -> "BAB I").

    Dipakai saat MENCARI pola BAB/judul bernomor: nomor halaman menempel
    di awal baris hasil ekstraksi. Hanya mengupas 1-3 digit di awal baris;
    teks lain tidak disentuh.
    """
    return re.sub(r'^\d{1,3}\s+', '', (s or '').strip(), count=1)


def akhir_kalimat_nyata(s: str) -> bool:
    """True bila baris diakhiri tanda akhir kalimat (bukan singkatan/desimal)."""
    t = (s or '').strip()
    if not _AKHIR_KALIMAT.search(t):
        return False
    m = re.search(r'([A-Za-z]+)\s*[.!?]["\')\]]*\s*$', t)
    if m and m.group(1).lower() in _SINGKATAN:
        return False
    if re.search(r'\d\.\d+\s*$', t):          # angka desimal, mis. 2,53 / 2.53
        return False
    return True


def awal_judul_baru(s: str) -> bool:
    """True bila B jelas awal unsur baru (judul/bab/butir), bukan lanjutan.

    Angka Romawi tunggal ("II") dan huruf tunggal ("I") DIKECUALIKAN:
    keduanya bisa jadi bagian dari "BAB I/II" yang terbelah, jadi tetap
    ditanya ke Jev, bukan di-skip.
    """
    t = (s or '').strip()
    if not t:
        return False
    if _POLA_BAB.match(t):
        return True
    if _POLA_NOMOR_JUDUL.match(t):
        return True
    if _ROMAWI_TUNGGAL.match(t) or (len(t) == 1 and t.isalpha()):
        return False
    kata = t.split()
    if len(kata) <= 8 and t == t.upper() and any(c.isalpha() for c in t):
        return True
    return False


def sambung_kode(a: str, b: str):
    """Putuskan pasangan (a, b) oleh kode. True/False/None (lihat atas).

    URUTAN PENTING: semua aturan SKIP dicek dulu sebelum aturan JOIN,
    supaya "a." (penanda butir) tidak ikut ter-join dan "pasar dan" +
    "BAB II" tidak menelan judul.
    """
    ta, tb = (a or '').strip(), (b or '').strip()
    if not ta or not tb:
        return None
    # ── SKIP: B nomor halaman saja ──────────────────────────────────────
    if _POLA_NOMOR_HALAMAN.match(tb):
        return False
    # ── SKIP: B unsur baru (judul/bab/butir) ────────────────────────────
    if awal_judul_baru(tb):
        return False
    # ── SKIP (v6): A judul BAB + B awal kalimat ─────────────────────────
    #    "BAB III METODOLOGI PENELITIAN" + "bagian ini menjelaskan..." —
    #    B huruf kecil / "Bab ini" = kalimat baru, bukan sambungan judul.
    #    Lanjutan judul huruf BESAR ("Penelitian") tetap ditanya ke Jev.
    if _POLA_BAB.match(tanpa_nomor_halaman(ta)) and (
            tb[:1].islower() or re.match(r'^(bab|bagian)\s+ini\b', tb, re.I)):
        return False
    # ── SKIP: baris tabel (pipa) ────────────────────────────────────────
    if '|' in ta or '|' in tb:
        return False
    # ── SKIP: A kalimat selesai ─────────────────────────────────────────
    if akhir_kalimat_nyata(ta):
        return False
    # ── JOIN: fragmen 1-2 huruf (bukan unsur berdiri sendiri) ───────────
    if len(ta) <= 2 and ta.isalpha() and (tb[0].islower() or len(tb) <= 2):
        return True
    # ── JOIN: A diakhiri koma / strip / kurung buka (kalimat belum selesai)
    isi_a = ta[:-1].strip() if ta else ''
    if ta.endswith((',', '-', '(')) and isi_a and any(c.isalpha() for c in isi_a):
        return True
    # ── JOIN: kata terakhir A kata gantung (wajib ada lanjutan) ─────────
    kata = ta.split()
    if kata and re.sub(r'[^A-Za-z]+$', '', kata[-1].lower()) in _KATA_GANTUNG:
        return True
    return None


# ═══════════════════════════════════════════════════════════════════════
# PERBAIKAN TEKS PECAH PER HURUF (v5)
# ───────────────────────────────────────────────────────────────────────
# Artefak ekstraksi PDF: "D i n a m i k a" — setiap huruf dipisah spasi.
# Terukur live fid=115 (10 Nov 2026): judul "Dinamika Pasar" tidak
# dikenali, kata-katanya jadi kandidat `biasa` / `buang`.
#
# CARA: cari rangkaian huruf tunggal berspasi ("D i n a m i k a"),
# lalu SEGMENTASI kata dengan program dinamis atas kamus:
#   · KATA_UMUM — kata Indonesia dari korpus naskah Asih + dokumen repo
#     (frekuensi asli) + daftar inti istilah skripsi (frekuensi 30).
#   · kosakata DALAM NASKAH — token multi-huruf yang muncul utuh di
#     naskah yang sama (nama/kata khas naskah ikut dikenali).
#   · angka Romawi tunggal (I, V, X, ...) boleh jadi segmen sendiri.
# Skor segmen = log(frekuensi+1) − 0.5 per kata (denda per kata supaya
# "subbab" menang atas "sub"+"bab"). Kata tak dikenal boleh, tapi
# didenda berat (−6) dan MAKS 25% huruf rangkaian.
#
# JUJUR: rangkaian yang TIDAK bisa disegmentasi (kata asing / nama yang
# tidak ada di kamus manapun) DIBIARKAN APA ADANYA — tidak ada kata yang
# dikarang. `perbaiki_spasi_huruf` mengembalikan (teks_baru, jumlah).
# ═══════════════════════════════════════════════════════════════════════
import math as _math

KATA_UMUM = {
    'abstrak': 30, 'ada': 396, 'adalah': 46, 'agar': 36, 'agen': 48, 'aktivitas': 30,
    'ambang': 59, 'analisis': 66, 'anggaran': 30, 'angka': 87, 'angket': 30, 'apa': 81,
    'artikel': 140, 'asli': 58, 'atas': 66, 'atau': 136, 'aturan': 136, 'audio': 30,
    'autokorelasi': 30, 'awal': 63, 'ayam': 78, 'ayat': 30, 'bab': 407, 'baca': 42,
    'bagan': 30, 'bagian': 128, 'bahan': 43, 'bahwa': 121, 'baik': 38, 'bakar': 78,
    'baris': 239, 'baru': 151, 'batas': 62, 'bawah': 43, 'bayar': 40, 'bekasi': 75,
    'belajar': 34, 'belakang': 30, 'belum': 205, 'benar': 81, 'bentuk': 98, 'berdasarkan': 53,
    'berkas': 137, 'berpengaruh': 74, 'besar': 44, 'biaya': 35, 'bidang': 30, 'bisa': 157,
    'bisnis': 58, 'boleh': 58, 'budaya': 30, 'bukan': 329, 'bukti': 63, 'buku': 232,
    'business': 84, 'butir': 44, 'cara': 85, 'catatan': 50, 'cek': 55, 'cetak': 30,
    'ciri': 30, 'coba': 30, 'contoh': 51, 'criteria': 46, 'daerah': 30, 'daftar': 151,
    'dalam': 321, 'dampak': 30, 'dan': 623, 'dapat': 76, 'dari': 303, 'data': 268,
    'definisi': 30, 'dengan': 282, 'desa': 30, 'deskriptif': 30, 'determinasi': 30, 'deviasi': 30,
    'diagram': 47, 'digital': 306, 'digunakan': 60, 'dilakukan': 54, 'dilarang': 49, 'dinamika': 30,
    'diolah': 45, 'dipakai': 97, 'disiplin': 30, 'distribusi': 30, 'ditolak': 38, 'diubah': 96,
    'dokumen': 92, 'dokumentasi': 30, 'dominan': 30, 'dosen': 30, 'dua': 62, 'dulu': 65,
    'dunia': 30, 'ekonomi': 45, 'eksperimen': 30, 'elektronik': 30, 'elemen': 47, 'entrepreneurial': 40,
    'evaluasi': 30, 'fakta': 43, 'faktor': 30, 'fitur': 47, 'format': 37, 'frekuensi': 30,
    'fungsi': 30, 'gagal': 95, 'gambar': 163, 'gaya': 35, 'gerbang': 159, 'grafik': 30,
    'gratis': 53, 'guru': 30, 'hakim': 63, 'halaman': 158, 'hanya': 143, 'harga': 34,
    'harus': 53, 'hasil': 359, 'heteroskedastisitas': 30, 'hipotesis': 59, 'hitung': 36, 'homogenitas': 30,
    'hubungan': 34, 'huruf': 44, 'ilmiah': 30, 'ilmu': 30, 'implementasi': 30, 'indeks': 30,
    'individu': 30, 'indonesia': 40, 'industri': 30, 'inferensial': 30, 'informan': 30, 'informasi': 30,
    'ini': 417, 'inovasi': 33, 'instrumen': 53, 'internet': 30, 'isi': 145, 'item': 54,
    'itu': 109, 'jadi': 96, 'jalur': 71, 'jangan': 277, 'jembatan': 61, 'jenis': 92,
    'journal': 50, 'judul': 176, 'juga': 63, 'jumlah': 52, 'jurnal': 148, 'kabupaten': 63,
    'kalau': 83, 'kalimat': 109, 'kandidat': 46, 'kapital': 42, 'karakteristik': 30, 'karena': 57,
    'karyawan': 30, 'kasus': 30, 'kata': 100, 'keadaan': 30, 'keberlanjutan': 235, 'kecil': 43,
    'kedua': 33, 'kegiatan': 30, 'kejadian': 30, 'kelompok': 30, 'keluarga': 30, 'kemampuan': 44,
    'kepemimpinan': 30, 'kepuasan': 30, 'keputusan': 63, 'kerangka': 30, 'kerja': 37, 'kesimpulan': 30,
    'keterangan': 30, 'kewirausahaan': 175, 'kinerja': 42, 'kiri': 38, 'kita': 45, 'klasifikasi': 30,
    'kode': 134, 'kolom': 75, 'komponen': 30, 'komunikasi': 30, 'komunitas': 30, 'kondisi': 30,
    'konsep': 30, 'konsumen': 30, 'konteks': 89, 'konversi': 165, 'korelasi': 30, 'kosong': 54,
    'kota': 30, 'kovarians': 30, 'kriteria': 30, 'kualitatif': 47, 'kuantitatif': 40, 'kuesioner': 42,
    'kuliner': 81, 'kunci': 68, 'kuota': 53, 'kutipan': 30, 'label': 34, 'lagi': 39,
    'lain': 69, 'lama': 82, 'lampiran': 57, 'langkah': 30, 'langsung': 58, 'lapis': 42,
    'latar': 30, 'lebih': 105, 'lewat': 58, 'likert': 30, 'linearitas': 30, 'lingkungan': 30,
    'lokasi': 30, 'lolos': 36, 'loyalitas': 30, 'lulus': 50, 'mahasiswa': 30, 'mampu': 33,
    'manajemen': 30, 'manfaat': 30, 'marketing': 251, 'masalah': 37, 'masih': 45, 'masuk': 49,
    'masyarakat': 30, 'mati': 34, 'media': 37, 'median': 30, 'mekanisme': 30, 'melalui': 61,
    'memakai': 35, 'memiliki': 45, 'menggunakan': 64, 'menjadi': 54, 'menulis': 38, 'menunjukkan': 98,
    'mesin': 149, 'metode': 36, 'metodologi': 30, 'model': 105, 'modul': 44, 'modus': 30,
    'motivasi': 30, 'multikolinearitas': 30, 'mutu': 80, 'nama': 112, 'narasi': 42, 'naskah': 281,
    'negara': 30, 'nilai': 90, 'nol': 39, 'nomor': 78, 'nonparametrik': 30, 'normal': 39,
    'normalitas': 30, 'nyata': 51, 'objek': 30, 'observasi': 30, 'oleh': 67, 'organisasi': 30,
    'orientasi': 178, 'orientation': 44, 'pada': 198, 'pagar': 96, 'pakai': 92, 'paket': 47,
    'panggilan': 34, 'panjang': 50, 'paradigma': 30, 'paragraf': 156, 'parametrik': 30, 'parsial': 30,
    'partisipan': 30, 'pasal': 30, 'pasar': 48, 'pedoman': 34, 'pelaku': 76, 'pelanggan': 40,
    'pemasaran': 30, 'pembaca': 30, 'pembahasan': 30, 'pembelajaran': 30, 'pembelian': 30, 'pembimbing': 30,
    'pendahuluan': 30, 'pendekatan': 30, 'pendidikan': 30, 'peneliti': 30, 'penelitian': 307, 'penerapan': 30,
    'pengaruh': 71, 'pengembangan': 30, 'pengertian': 30, 'pengetahuan': 30, 'pengguna': 30, 'pengolahan': 30,
    'penguji': 30, 'pengumpulan': 30, 'penting': 44, 'penulis': 126, 'penyajian': 30, 'peran': 46,
    'perbandingan': 30, 'performance': 38, 'periksa': 81, 'perilaku': 30, 'peristiwa': 30, 'perlu': 59,
    'pernah': 36, 'pernyataan': 37, 'persentase': 30, 'persepsi': 30, 'pertanyaan': 66, 'perubahan': 37,
    'perusahaan': 30, 'peta': 215, 'pintu': 60, 'poin': 30, 'pola': 76, 'populasi': 30,
    'positif': 61, 'prakata': 30, 'pratinjau': 30, 'produk': 43, 'produksi': 73, 'program': 30,
    'promosi': 30, 'proporsi': 30, 'proposal': 30, 'prosedur': 30, 'proses': 30, 'provinsi': 30,
    'proyek': 48, 'punya': 39, 'pustaka': 41, 'putusan': 88, 'ranah': 30, 'rata': 38,
    'reduksi': 30, 'referensi': 30, 'regresi': 61, 'reliabilitas': 30, 'rencana': 30, 'resmi': 63,
    'responden': 59, 'revisi': 66, 'ringkasan': 30, 'risiko': 34, 'rumusan': 30, 'rusak': 42,
    'rute': 34, 'saat': 59, 'saja': 52, 'salah': 105, 'sama': 87, 'sampel': 30,
    'saran': 30, 'sasaran': 30, 'satu': 185, 'saya': 74, 'sebagai': 92, 'sebelum': 100,
    'sebesar': 44, 'secara': 84, 'sehingga': 58, 'sekolah': 30, 'sektor': 30, 'selalu': 33,
    'selisih': 30, 'seluruh': 36, 'semakin': 33, 'seminar': 30, 'semua': 106, 'sendiri': 81,
    'seperti': 45, 'serta': 71, 'sesuai': 41, 'sesudah': 37, 'setelah': 47, 'setiap': 44,
    'setuju': 39, 'sidang': 30, 'sifat': 30, 'signifikan': 57, 'simulasi': 39, 'simultan': 30,
    'sini': 65, 'sistem': 30, 'siswa': 30, 'sitasi': 30, 'situasi': 30, 'skala': 30,
    'sketsa': 38, 'skor': 30, 'skripsi': 55, 'sosial': 30, 'spss': 48, 'standar': 30,
    'statistics': 39, 'statistik': 62, 'status': 84, 'strategi': 33, 'struktur': 30, 'studi': 30,
    'subbab': 30, 'subjek': 30, 'sudah': 221, 'sumber': 133, 'survei': 49, 'sustainability': 53,
    'sustainable': 37, 'syarat': 30, 'tabel': 244, 'tahap': 53, 'tahu': 43, 'tahun': 68,
    'tak': 65, 'tanpa': 145, 'tanya': 34, 'tapi': 50, 'teknik': 30, 'teknologi': 30,
    'teks': 94, 'tempat': 36, 'template': 57, 'temuan': 56, 'tengah': 78, 'teori': 30,
    'terbukti': 53, 'terhadap': 162, 'terkunci': 59, 'tersebut': 72, 'terukur': 67, 'tetap': 85,
    'tiap': 39, 'tidak': 542, 'tingkat': 40, 'tinjauan': 30, 'titik': 49, 'token': 104,
    'tombol': 40, 'total': 36, 'triangulasi': 30, 'tridarma': 57, 'tujuan': 30, 'uji': 386,
    'ukuran': 41, 'ulang': 46, 'umkm': 160, 'umum': 78, 'unsur': 30, 'untuk': 294,
    'urutan': 41, 'usaha': 398, 'validitas': 30, 'variabel': 171, 'varians': 30, 'verifikasi': 41,
    'versi': 34, 'visual': 30, 'wajib': 116, 'waktu': 34, 'wawancara': 30, 'wilayah': 30,
    'wulan': 94, 'yang': 895,
}

_HURUF_ROMAWI = set('ivxlcdm')

# ── KATA TAMBAHAN v6 (10 Nov 2026) ───────────────────────────────────────
#    Kata Indonesia umum yang belum ada di KATA_UMUM di atas — kata kerja
#    akademik + penghubung + istilah kampus yang sering muncul di naskah.
#    Dipakai segmentasi teks pecah per huruf SESUDAH stitch (v6.1).
#    Hanya kata berdiri sendiri yang benar (bukan gabungan yang salah
#    seperti 'tanggungjawab'/'matakuliah' — dua kata itu TIDAK ada di sini).
KATA_UMUM_V6 = {
    'membahas': 30, 'menjelaskan': 30, 'menyatakan': 30, 'merupakan': 30,
    'mengenai': 30, 'berkaitan': 30, 'berikut': 30, 'selanjutnya': 30,
    'kemudian': 30, 'meliputi': 30, 'mencakup': 30, 'terdiri': 30,
    'meningkatkan': 30, 'memberikan': 30, 'memperoleh': 30, 'menyebabkan': 30,
    'menghasilkan': 30, 'menganalisis': 30, 'mengidentifikasi': 30,
    'menentukan': 30, 'memahami': 30, 'mengetahui': 30, 'melakukan': 30,
    'menyusun': 30, 'menyajikan': 30, 'menguraikan': 30, 'mengumpulkan': 30,
    'menerapkan': 30, 'memilih': 30, 'menilai': 30, 'mengukur': 30,
    'membandingkan': 30, 'membedakan': 30, 'menghubungkan': 30,
    'memengaruhi': 30, 'mempengaruhi': 30, 'dipengaruhi': 30, 'dimaksud': 30,
    'disebut': 30, 'dinamakan': 30, 'termasuk': 30, 'melibatkan': 30,
    'membutuhkan': 30, 'diperlukan': 30, 'diperoleh': 30, 'ditemukan': 30,
    'diberikan': 30, 'dilaksanakan': 30, 'ditetapkan': 30, 'dijelaskan': 30,
    'disebutkan': 30, 'menurut': 30, 'berpendapat': 30, 'mengemukakan': 30,
    'menyebutkan': 30, 'mengatakan': 30, 'menambahkan': 30, 'mengurangi': 30,
    'menambah': 30, 'berkurang': 30, 'bertambah': 30, 'sangat': 30,
    'cukup': 30, 'kurang': 30, 'paling': 30, 'hampir': 30, 'sekitar': 30,
    'antara': 30, 'hingga': 30, 'selama': 30, 'sementara': 30,
    'sedangkan': 30, 'meskipun': 30, 'walaupun': 30, 'apabila': 30,
    'jika': 30, 'sebab': 30, 'akibat': 30, 'kedudukan': 30, 'kewenangan': 30,
    'menjawab': 30, 'pertanggungjawaban': 30, 'pendidik': 30, 'kampus': 30,
    'fakultas': 30, 'semester': 30, 'perkuliahan': 30, 'bimbingan': 30,
    'ujian': 30, 'wisuda': 30, 'alumni': 30, 'lulusan': 30, 'praktik': 30,
    'magang': 30, 'pelatihan': 30, 'pemberdayaan': 30, 'keberhasilan': 30,
    'kegagalan': 30, 'permasalahan': 30, 'persoalan': 30, 'tantangan': 30,
    'peluang': 30, 'ancaman': 30, 'kekuatan': 30, 'kelemahan': 30,
    'kesempatan': 30, 'kemungkinan': 30, 'kepastian': 30, 'kebenaran': 30,
    'keadilan': 30, 'kejujuran': 30, 'kepercayaan': 30, 'kepedulian': 30,
    'kesadaran': 30, 'pemahaman': 30, 'keterampilan': 30, 'kecakapan': 30,
    'sikap': 30, 'kebiasaan': 30, 'norma': 30, 'etika': 30, 'moral': 30,
    'hukum': 30, 'peraturan': 30, 'kebijakan': 30, 'kesepakatan': 30,
    'perjanjian': 30, 'kerjasama': 30, 'kemitraan': 30, 'jejaring': 30,
    'penduduk': 30, 'warga': 30, 'generasi': 30, 'anak': 30, 'remaja': 30,
    'dewasa': 30, 'lansia': 30, 'perempuan': 30, 'kesehatan': 30,
    'politik': 30, 'transportasi': 30, 'infrastruktur': 30,
    'perekonomian': 30, 'perdagangan': 30, 'pertanian': 30, 'perikanan': 30,
    'peternakan': 30, 'kehutanan': 30, 'pertambangan': 30, 'energi': 30,
    'pariwisata': 30,
}
KATA_UMUM.update(KATA_UMUM_V6)
_POLA_RUN_SPASI = re.compile(r'(?<![A-Za-z0-9])([A-Za-z](?: [A-Za-z]){2,})(?![A-Za-z0-9])')
_POLA_TOKEN = re.compile(r'[A-Za-z]{3,}')
_PANJANG_KATA_MAKS = 24
_PANJANG_TAK_DIKENAL_MAKS = 10
_DENDA_PER_KATA = 0.5
_DENDA_TAK_DIKENAL = 6.0
_BATAS_TAK_DIKENAL = 0.25          # maks 25% huruf rangkaian boleh tak dikenal
_SKOR_ROMAWI = _math.log(11) - _DENDA_PER_KATA


def _kosakata_dari_teks(teks):
    """Token multi-huruf utuh dalam naskah (di luar rangkaian spasi).

    Kembalikan dict kata -> frekuensi (min 3) — kosakata dalam naskah
    untuk kata/nama khas yang tidak ada di KATA_UMUM.
    """
    bersih = _POLA_RUN_SPASI.sub(' ', teks or '')
    hitung = {}
    for tok in _POLA_TOKEN.findall(bersih.lower()):
        hitung[tok] = hitung.get(tok, 0) + 1
    return {w: 3 + n for w, n in hitung.items()}


def _segmentasi(huruf, frek):
    """Segmentasi rangkaian huruf jadi kata-kata kamus (program dinamis).

    `huruf`: string huruf kecil tanpa spasi. Kembalikan daftar
    (awal, akhir, kata) — kata None berarti segmen tak dikenal —
    atau None bila tidak ada segmentasi yang lolos pagar.
    """
    n = len(huruf)
    # dp[i] = (skor, pilihan) terbaik untuk huruf[:i]; pilihan = daftar segmen.
    dp = [(None, None)] * (n + 1)
    dp[0] = (0.0, [])
    for i in range(n):
        skor_i, pil_i = dp[i]
        if skor_i is None:
            continue
        # ── angka Romawi tunggal ──
        if huruf[i] in _HURUF_ROMAWI:
            s = skor_i + _SKOR_ROMAWI
            if dp[i + 1][0] is None or s > dp[i + 1][0]:
                dp[i + 1] = (s, pil_i + [(i, i + 1, huruf[i])])
        # ── kata kamus (2..24 huruf) ──
        for j in range(i + 2, min(n, i + _PANJANG_KATA_MAKS) + 1):
            kata = huruf[i:j]
            if kata in frek:
                s = skor_i + _math.log(frek[kata] + 1) - _DENDA_PER_KATA
                if dp[j][0] is None or s > dp[j][0]:
                    dp[j] = (s, pil_i + [(i, j, kata)])
        # ── kata tak dikenal (3..10 huruf, didenda berat) ──
        for j in range(i + 3, min(n, i + _PANJANG_TAK_DIKENAL_MAKS) + 1):
            s = skor_i - _DENDA_TAK_DIKENAL
            if dp[j][0] is None or s > dp[j][0]:
                dp[j] = (s, pil_i + [(i, j, None)])
    skor, pilihan = dp[n]
    if skor is None or not pilihan:
        return None
    tak_dikenal = sum(b - a for a, b, k in pilihan if k is None)
    ada_kamus = any(k is not None and len(k) > 1 for _, _, k in pilihan)
    semua_romawi = all(k is not None and len(k) == 1 for _, _, k in pilihan)
    if tak_dikenal / n > _BATAS_TAK_DIKENAL:
        return None
    if not ada_kamus and not semua_romawi:
        return None
    return pilihan


def _bentuk_kata(kata, kapital_awal, semua_kapital):
    if semua_kapital:
        return kata.upper()
    if kapital_awal:
        return kata[:1].upper() + kata[1:]
    return kata


def _perbaiki_satu_run(run, frek):
    """Perbaiki SATU rangkaian huruf berspasi. Kembalikan (teks, diperbaiki).

    `diperbaiki` True bila ada kata yang digabung; False = dibiarkan.
    """
    huruf = run.replace(' ', '').lower()
    if len(huruf) < 3:
        return run, False
    pilihan = _segmentasi(huruf, frek)
    if pilihan is None:
        return run, False
    huruf_asli = run.replace(' ', '')
    semua_kapital = huruf_asli.isupper()
    keluar, gabung = [], False
    for a, b, kata in pilihan:
        if kata is None:
            # segmen tak dikenal: biarkan berspasi seperti aslinya.
            keluar.append(' '.join(huruf_asli[a:b]))
        else:
            # angka Romawi tunggal yang berurutan digabung jadi satu bilangan.
            if len(kata) == 1 and keluar and keluar[-1] and \
                    all(c in 'IVXLC' for c in keluar[-1]):
                keluar[-1] = keluar[-1] + kata.upper()
            else:
                # kapital mengikuti huruf ASLI awal segmen ("P a s a r" -> "Pasar").
                keluar.append(_bentuk_kata(kata, huruf_asli[a].isupper(),
                                           semua_kapital))
            gabung = True
    return ' '.join(keluar), gabung


def perbaiki_spasi_huruf(teks):
    """Perbaiki teks pecah per huruf di seluruh teks.

    Kembalikan (teks_baru, jumlah_rangkaian_yang_diperbaiki).
    Rangkaian yang tidak bisa disegmentasi dengan aman dibiarkan utuh.
    """
    t = teks or ''
    if ' ' not in t:
        return t, 0
    frek = dict(KATA_UMUM)
    frek.update(_kosakata_dari_teks(t))
    jml = 0

    def _ganti(m):
        nonlocal jml
        baru, ok = _perbaiki_satu_run(m.group(1), frek)
        if ok:
            jml += 1
        return baru

    return _POLA_RUN_SPASI.sub(_ganti, t), jml
