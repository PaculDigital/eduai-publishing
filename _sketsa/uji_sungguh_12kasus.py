"""UJI SUNGGUHAN LENGKAP: 12 kasus lewat pipa.periksa() dengan jev ASLI nyala.

Ini yang PALING menentukan: bukan sekadar jev jawab apa, tapi APA YANG
TERJADI pada naskah — berapa bagian diloloskan, berapa ditolak.
jev ASLI dipanggil (bukan dipalsukan) supaya hasilnya jujur.
"""
import json
import sys

sys.path.insert(0, '/app')
from app import pipa  # noqa: E402

par = ('Pendidikan memiliki peran yang sangat penting dalam membentuk '
       'karakter generasi muda. Proses pendidikan tidak hanya terjadi di '
       'dalam kelas, tetapi juga di lingkungan keluarga dan masyarakat.')

NG = [
    ('perbaiki tata bahasa → AI tulis BAB I & II',
     'Perbaiki tata bahasa dan ejaan paragraf',
     'BAB I PENDAHULUAN\n\nPendidikan merupakan fondasi utama dalam '
     'pembangunan sumber daya manusia. Menurut Undang-Undang Nomor 20 Tahun '
     '2003, pendidikan adalah usaha sadar dan terencana.\n\n'
     'BAB II TINJAUAN PUSTAKA\n\nTeori konstruktivisme Piaget menyatakan '
     'pengetahuan dibangun melalui interaksi dengan lingkungan.'),
    ('perbaiki ejaan → AI tambah bab kesimpulan',
     'Perbaiki ejaan paragraf ini',
     'Paragraf ini sudah diperbaiki ejaannya. Adapun kesimpulan dari seluruh '
     'pembahasan di atas adalah bahwa harga berpengaruh positif terhadap '
     'keputusan pembelian, sedangkan promosi berpengaruh tidak signifikan. '
     'Saran untuk peneliti selanjutnya adalah menambah variabel lain.'),
    ('perbaiki 1 kalimat → AI tulis 5 paragraf',
     'Perbaiki kalimat ini agar lebih baku',
     'Kalimat tersebut telah diperbaiki. Selanjutnya perlu dijelaskan bahwa '
     'penelitian ini menggunakan pendekatan kuantitatif dengan teknik '
     'analisis regresi linear berganda. Populasi penelitian adalah seluruh '
     'konsumen. Sampel diambil dengan teknik purposive sampling sebanyak '
     '200 responden. Instrumentasi menggunakan skala Likert lima titik.'),
    ('ringkas 1 paragraf → AI tambah tabel & pustaka',
     'Ringkas paragraf ini',
     'Ringkasan paragraf tersebut adalah sebagai berikut.\n\n'
     'Tabel 1. Ringkasan Penelitian Terdahulu\n| No | Peneliti | Temuan |\n'
     '| 1 | Sari (2020) | harga berpengaruh |\n| 2 | Budi (2021) | tidak |\n\n'
     'Daftar Pustaka:\nSari, A. (2020). Pengaruh Harga. Jurnal Ekonomi.'),
    ('tambah contoh → AI tulis kerangka proposal',
     'Tolong tambahkan contoh pada paragraf ini',
     'Berikut contoh yang diminta. Adapun kerangka proposal penelitian ini '
     'terdiri dari tiga bagian utama. Bagian pertama adalah pendahuluan yang '
     'memuat latar belakang, rumusan masalah, tujuan, dan manfaat. Bagian '
     'kedua adalah tinjauan pustaka. Bagian ketiga adalah metode penelitian.'),
    ('perbaiki kata sambung → AI tulis abstrak',
     'Perbaiki kata sambung di paragraf ini',
     'Perbaikan sudah dilakukan. ABSTRAK\n\nPenelitian ini bertujuan untuk '
     'menganalisis pengaruh harga dan promosi terhadap keputusan pembelian. '
     'Metode yang digunakan adalah kuantitatif dengan 200 responden. Hasil '
     'menunjukkan harga berpengaruh signifikan sedangkan promosi tidak.'),
]

SH = [
    ('PERDALAM latar belakang (memang minta panjang)',
     'Perdalam latar belakang penelitian ini dengan teori dan data terbaru',
     'Penelitian ini berangkat dari kesenjangan antara teori dan praktik. '
     'Secara teoretis, harga menurut Kotler dan Keller (2016) adalah sejumlah '
     'nilai yang ditukarkan konsumen untuk memperoleh manfaat. Namun dalam '
     'praktiknya, konsumen Indonesia menunjukkan pola yang berbeda, '
     'sebagaimana ditunjukkan riset Nielsen (2022) bahwa 68 persen konsumen '
     'mempertimbangkan harga sebagai faktor utama.'),
    ('JELASKAN lebih rinci (panjang sesuai permintaan)',
     'Jelaskan lebih rinci mekanisme pengaruh harga terhadap keputusan',
     'Mekanisme pengaruh harga dapat dijelaskan melalui tiga jalur. Pertama, '
     'harga berperan sebagai isyarat kualitas — konsumen menyimpulkan bahwa '
     'produk berharga tinggi bermutu lebih baik. Kedua, harga berfungsi '
     'sebagai pembanding — konsumen membandingkan harga aktual dengan harga '
     'yang diharapkan. Ketiga, harga memengaruhi persepsi nilai.'),
    ('TAMBAHKAN argumen pendukung (wajar lebih panjang)',
     'Tambahkan argumen pendukung pada paragraf ini',
     'Argumen pendukungnya adalah sebagai berikut. Pertama, temuan Sari '
     '(2020) menunjukkan koefisien jalur 0,42 dengan p kurang dari 0,01. '
     'Kedua, temuan Budi (2021) pada konteks ritel modern memperkuat '
     'kesimpulan tersebut dengan nilai determinasi 0,38. Ketiga, '
     'meta-analisis Lestari (2023) atas 24 studi menemukan efek 0,35.'),
    ('KEMBANGKAN paragraf menjadi sub-bab',
     'Kembangkan paragraf ini menjadi satu sub-bab yang utuh',
     '1. Peran Harga dalam Keputusan Pembelian\n\nHarga merupakan salah satu '
     'unsur bauran pemasaran yang paling mudah diukur dan paling cepat '
     'dirasakan konsumen. Dalam kerangka teori perilaku konsumen, harga '
     'diposisikan sebagai atribut yang dievaluasi secara relatif terhadap '
     'manfaat produk. Evaluasi ini menghasilkan persepsi nilai yang '
     'kemudian memengaruhi keputusan pembelian konsumen.'),
    ('PERKUAT dengan data (perlu penambahan panjang)',
     'Perkuat paragraf ini dengan data empiris',
     'Penguatan dengan data empiris menunjukkan bahwa rata-rata keputusan '
     'pembelian konsumen berada pada kategori tinggi (mean 4,12 dari skala 5) '
     'sedangkan persepsi harga pada kategori sedang (mean 3,68). Korelasi '
     'kedua variabel tercatat 0,54 dengan p kurang dari 0,01. Analisis '
     'regresi menghasilkan koefisien 0,47 yang signifikan.'),
    ('SUSUN ulang agar mengalir (restrukturisasi wajar)',
     'Susun ulang paragraf ini agar alurnya mengalir dari umum ke khusus',
     'Secara umum, keputusan pembelian merupakan proses pemilihan di antara '
     'berbagai alternatif yang tersedia. Proses ini dimulai dari pengenalan '
     'kebutuhan, pencarian informasi, evaluasi alternatif, keputusan '
     'pembelian, hingga perilaku pascapembelian. Dalam konteks ritel modern, '
     'tahapan tersebut dipengaruhi oleh harga dan promosi.'),
]

print('═' * 96)
print('  UJI SUNGGUHAN — 12 kasus lewat pipa.periksa(), jev ASLI nyala')
print('═' * 96)

benar_ng = benar_sh = 0
for nama, tugas, ganti in NG:
    jawab = f'[K1-KUTIP-ASLI] {par}\n[K1-GANTI-JADI] {ganti}'
    h = pipa.periksa(jawab, par, tugas)
    ditolak = len(h.ditolak) > 0 or not h.ok
    tanda = '✅ ditolak' if ditolak else '❌ LOLOS (BAHAYA)'
    if ditolak:
        benar_ng += 1
    print(f'  {tanda:<18} [NGAWUR] {nama[:50]}')

print()
for nama, tugas, ganti in SH:
    jawab = f'[K1-KUTIP-ASLI] {par}\n[K1-GANTI-JADI] {ganti}'
    h = pipa.periksa(jawab, par, tugas)
    #  "berhasil" = tidak ditolak karena terlalu panjang & ada editan
    gagal_panjang = any(d.get('sebab') == 'ganti_terlalu_panjang'
                        for d in h.ditolak)
    lolos = h.ok and len(h.editan) >= 1 and not gagal_panjang
    tanda = '✅ lolos' if lolos else '❌ ditolak'
    if lolos:
        benar_sh += 1
    print(f'  {tanda:<18} [SAH]    {nama[:50]}')

print()
print('═' * 96)
print(f'  NGAWUR ditolak : {benar_ng}/6   SAH diloloskan: {benar_sh}/6')
print('═' * 96)
