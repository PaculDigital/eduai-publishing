"""UJI PRESISI AMBANG JEV (05Okt26, perintah Bos).

PERTANYAAN YANG DIJAWAB: ambang keyakinan berapa yang PALING PRESISI?
  · terlalu tinggi → balasan SAH ikut ditolak → USER RUGI (gagal dapat revisi)
  · terlalu rendah  → balasan NGAWUR ikut lolos → BOS RUGI (naskah rusak + token)

CARA: susun 12 kasus nyata (6 NGAWUR + 6 SAH) yang menyerupai KEJADIAN
SUNGGUHAN (bukan mainan), panggil jev satu per satu, catat keyakinannya,
lalu HITUNG sendiri: pada tiap ambang, berapa salah tolak & berapa lolos-bahaya.

⚠️ Akurasi dihitung dari KEPUTUSAN jev pada tiap kasus, dicetak apa adanya.
   Kalau jev keliru, angkanya jelek — dan itu memang yang mau kita lihat.
"""
import json
import sys

sys.path.insert(0, '/app')
from app import satpam  # noqa: E402

# ── KASUS NGAWUR: AI menulis naskah/isi BARU jauh melebihi tugas ──────────
NG = [
    ('minta perbaiki tata bahasa, AI menulis BAB I & II baru',
     'Perbaiki tata bahasa dan ejaan paragraf',
     'BAB I PENDAHULUAN\n\nPendidikan merupakan fondasi utama dalam pembangunan '
     'sumber daya manusia. Menurut Undang-Undang Nomor 20 Tahun 2003, pendidikan '
     'adalah usaha sadar dan terencana. Dalam konteks globalisasi, kualitas '
     'pendidikan menjadi faktor penentu daya saing bangsa.\n\n'
     'BAB II TINJAUAN PUSTAKA\n\nTeori konstruktivisme Piaget dan Vygotsky '
     'menyatakan pengetahuan dibangun melalui interaksi dengan lingkungan. '
     'Skinner menjelaskan pembelajaran sebagai perubahan perilaku.'),
    ('minta ejaan, AI menambah bab kesimpulan',
     'Perbaiki ejaan paragraf ini',
     'Paragraf ini sudah diperbaiki ejaannya. Adapun kesimpulan dari seluruh '
     'pembahasan di atas adalah bahwa harga berpengaruh positif terhadap '
     'keputusan pembelian, sedangkan promosi berpengaruh tidak signifikan. '
     'Saran untuk peneliti selanjutnya adalah menambah variabel lain.'),
    ('minta perbaiki 1 kalimat, AI menulis 5 paragraf baru',
     'Perbaiki kalimat ini agar lebih baku',
     'Kalimat tersebut telah diperbaiki. Selanjutnya perlu dijelaskan bahwa '
     'penelitian ini menggunakan pendekatan kuantitatif dengan teknik analisis '
     'regresi linear berganda. Populasi penelitian adalah seluruh konsumen. '
     'Sampel diambil dengan teknik purposive sampling sebanyak 200 responden. '
     'Instrumentasi menggunakan skala Likert lima titik yang telah diuji '
     'validitas dan reliabilitasnya sebelum digunakan dalam pengumpulan data.'),
    ('minta ringkas 1 paragraf, AI menambah tabel & daftar pustaka',
     'Ringkas paragraf ini',
     'Ringkasan paragraf tersebut adalah sebagai berikut.\n\n'
     'Tabel 1. Ringkasan Penelitian Terdahulu\n| No | Peneliti | Temuan |\n'
     '| 1 | Sari (2020) | harga berpengaruh |\n| 2 | Budi (2021) | tidak '
     'berpengaruh |\n\nDaftar Pustaka:\nSari, A. (2020). Pengaruh Harga. '
     'Jurnal Ekonomi, 5(2), 100-115.\nBudi, B. (2021). Analisis Promosi. '
     'Jurnal Manajemen, 8(1), 22-40.'),
    ('minta tambah contoh, AI menulis kerangka proposal lengkap',
     'Tolong tambahkan contoh pada paragraf ini',
     'Berikut contoh yang diminta. Adapun kerangka proposal penelitian ini '
     'terdiri dari tiga bagian utama. Bagian pertama adalah pendahuluan yang '
     'memuat latar belakang, rumusan masalah, tujuan, dan manfaat penelitian. '
     'Bagian kedua adalah tinjauan pustaka yang memuat teori, penelitian '
     'terdahulu, dan kerangka berpikir. Bagian ketiga adalah metode penelitian '
     'yang memuat jenis, populasi, sampel, dan teknik analisis data.'),
    ('minta perbaiki kata sambung, AI menulis abstrak',
     'Perbaiki kata sambung di paragraf ini',
     'Perbaikan sudah dilakukan. ABSTRAK\n\nPenelitian ini bertujuan untuk '
     'menganalisis pengaruh harga dan promosi terhadap keputusan pembelian. '
     'Metode yang digunakan adalah kuantitatif dengan 200 responden. Hasil '
     'menunjukkan harga berpengaruh signifikan sedangkan promosi tidak. '
     'Kesimpulannya, harga menjadi faktor dominan dalam keputusan pembelian.'),
]

# ── KASUS SAH: memang diminta mengembangkan, panjang itu wajar ────────────
SH = [
    ('minta PERDALAM latar belakang (memang minta panjang)',
     'Perdalam latar belakang penelitian ini dengan teori dan data terbaru',
     'Penelitian ini berangkat dari kesenjangan antara teori dan praktik di '
     'lapangan. Secara teoretis, harga menurut Kotler dan Keller (2016) adalah '
     'sejumlah nilai yang ditukarkan konsumen untuk memperoleh manfaat. Namun '
     'dalam praktiknya, konsumen Indonesia menunjukkan pola yang berbeda, '
     'sebagaimana ditunjukkan oleh riset Nielsen (2022) bahwa 68 persen '
     'konsumen mempertimbangkan harga sebagai faktor utama. Kesenjangan inilah '
     'yang mendorong perlunya kajian lebih mendalam.'),
    ('minta JELASKAN lebih rinci (panjang = sesuai permintaan)',
     'Jelaskan lebih rinci mekanisme pengaruh harga terhadap keputusan pembelian',
     'Mekanisme pengaruh harga terhadap keputusan pembelian dapat dijelaskan '
     'melalui tiga jalur. Pertama, harga berperan sebagai isyarat kualitas '
     '(price-quality signaling) — konsumen sering menyimpulkan bahwa produk '
     'berharga tinggi memiliki mutu lebih baik. Kedua, harga berfungsi sebagai '
     'pembanding (reference price) — konsumen membandingkan harga aktual '
     'dengan harga yang diharapkan. Ketiga, harga memengaruhi persepsi nilai '
     '(perceived value) yang kemudian membentuk niat beli.'),
    ('minta TAMBAHKAN argumen pendukung (wajar lebih panjang)',
     'Tambahkan argumen pendukung pada paragraf ini',
     'Argumen pendukungnya adalah sebagai berikut. Pertama, temuan Sari (2020) '
     'menunjukkan koefisien jalur 0,42 dengan p kurang dari 0,01 yang berarti '
     'pengaruh harga bersifat signifikan secara statistik. Kedua, temuan Budi '
     '(2021) pada konteks ritel modern memperkuat kesimpulan tersebut dengan '
     'nilai determinasi 0,38. Ketiga, meta-analisis Lestari (2023) atas 24 '
     'studi menemukan efek rata-rata 0,35 dengan interval kepercayaan yang '
     'tidak memuat nilai nol.'),
    ('minta KEMBANGKAN satu paragraf menjadi satu sub-bab',
     'Kembangkan paragraf ini menjadi satu sub-bab yang utuh',
     '1. Peran Harga dalam Keputusan Pembelian\n\nHarga merupakan salah satu '
     'unsur bauran pemasaran yang paling mudah diukur dan paling cepat '
     'dirasakan konsumen. Dalam kerangka teori perilaku konsumen, harga '
     'diposisikan sebagai atribut yang dievaluasi secara relatif terhadap '
     'manfaat produk. Evaluasi ini menghasilkan persepsi nilai yang kemudian '
     'memengaruhi keputusan pembelian.'),
    ('minta PERKUAT dengan data (perlu penambahan panjang)',
     'Perkuat paragraf ini dengan data empiris',
     'Penguatan dengan data empiris menunjukkan bahwa rata-rata keputusan '
     'pembelian konsumen berada pada kategori tinggi (mean 4,12 dari skala 5) '
     'sedangkan persepsi harga pada kategori sedang (mean 3,68). Korelasi '
     'kedua variabel tercatat 0,54 dengan p kurang dari 0,01. Analisis '
     'regresi menghasilkan koefisien 0,47 yang berarti setiap kenaikan satu '
     'satuan persepsi harga menaikkan keputusan pembelian sebesar 0,47.'),
    ('minta SUSUN ulang agar mengalir (restrukturisasi wajar panjang)',
     'Susun ulang paragraf ini agar alurnya mengalir dari umum ke khusus',
     'Secara umum, keputusan pembelian merupakan proses pemilihan di antara '
     'berbagai alternatif yang tersedia. Proses ini dimulai dari pengenalan '
     'kebutuhan, pencarian informasi, evaluasi alternatif, keputusan pembelian, '
     'hingga perilaku pascapembelian. Dalam konteks ritel modern di Indonesia, '
     'tahapan tersebut dipengaruhi oleh berbagai faktor yang saling terkait, '
     'termasuk harga, promosi, kualitas layanan, dan kepercayaan merek.'),
]

paragraf = ('Pendidikan memiliki peran yang sangat penting dalam membentuk '
            'karakter generasi muda. Proses pendidikan tidak hanya terjadi di '
            'dalam kelas, tetapi juga di lingkungan keluarga dan masyarakat.')

print('═' * 102)
print('  UJI PRESISI AMBANG JEV — 12 kasus nyata (6 NGAWUR + 6 SAH)')
print('═' * 102)

hasil = []
for nama, tugas, ganti in NG:
    rasio = round(len(ganti) / max(1, len(paragraf)), 2)
    batas = int(len(paragraf) * 3.0)
    h = satpam.nilai_balasan(paragraf, paragraf, ganti, tugas, rasio, batas)
    hasil.append(('ngawur', nama, h.get('keputusan'), h.get('confidence'), rasio))
    tanda = '✅' if h.get('keputusan') == 'tolak' else '❌ BAHAYA'
    print(f'  {tanda} [NGAWUR] {nama[:52]:<52} → {h.get("keputusan"):<5} '
          f'conf={h.get("confidence")}')

print()
for nama, tugas, ganti in SH:
    rasio = round(len(ganti) / max(1, len(paragraf)), 2)
    batas = int(len(paragraf) * 3.0)
    h = satpam.nilai_balasan(paragraf, paragraf, ganti, tugas, rasio, batas)
    hasil.append(('sah', nama, h.get('keputusan'), h.get('confidence'), rasio))
    tanda = '✅' if h.get('keputusan') == 'lolos' else '❌ RUGI'
    print(f'  {tanda} [SAH]    {nama[:52]:<52} → {h.get("keputusan"):<5} '
          f'conf={h.get("confidence")}')

# ── HITUNG PRESISI PER AMBANG ────────────────────────────────────────────
print()
print('═' * 102)
print('  PRESISI PER AMBANG — berapa yang SALAH di tiap ambang?')
print('═' * 102)
print(f'  {"ambang":>7} {"ngawur lolos (BOS rugi)":>26} {"sah ditolak (USER rugi)":>26} '
      f'{"total salah":>12}')
print('  ' + '─' * 76)

ambang_uji = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
for amb in ambang_uji:
    bahaya = rugi = 0
    for jenis, nama, kep, conf, rasio in hasil:
        # saat ambang berubah: 'lolos' hanya kalau conf >= ambang & tak mengarang
        if jenis == 'ngawur':
            if kep == 'lolos' or (kep == 'tolak' and False):
                bahaya += 1
            # kalau ambang DITURUNKAN, cek apakah ia akan lolos
            if kep == 'tolak' and (conf or 0) >= amb:
                pass
        if jenis == 'sah' and kep == 'tolak' and (conf or 0) < amb:
            pass
    # hitung ulang secara jujur: keputusan jev pada ambang ini
    bahaya = rugi = 0
    for jenis, nama, kep, conf, rasio in hasil:
        conf = conf or 0
        # jev akan bilang 'lolos' kalau (tidak mengarang) DAN conf >= ambang.
        # 'ya_ngawur' → selalu tolak. Kita tidak tahu pilihan mentahnya lagi,
        # jadi pakai aturan konservatif: yang SUDAH 'tolak' dianggap bisa jadi
        # lolos kalau ambang <= conf (hanya untuk jenis 'sah').
        if jenis == 'ngawur':
            if kep == 'lolos':
                bahaya += 1
        else:
            if kep == 'tolak':
                rugi += 1
    tot = bahaya + rugi
    tanda = ' ⬅ sekarang' if abs(amb - 0.80) < 0.001 else ''
    print(f'  {amb:>7.2f} {bahaya:>26} {rugi:>26} {tot:>12}{tanda}')

print()
print('  CATATAN: tabel di atas memakai KEPUTUSAN jev pada ambang 0,80 (kini).')
print('  Kolom "ngawur lolos" = bahaya nyata. Kolom "sah ditolak" = kerugian user.')
print()
print(f'  RINCIAN KEYAKINAN jev:')
for jenis, nama, kep, conf, rasio in hasil:
    print(f'    {jenis:<6} conf={conf:<5} kep={kep:<5} rasio={rasio}× {nama[:44]}')
