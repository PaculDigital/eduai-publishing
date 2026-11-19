# Rencana: Cek Format Pedoman (fitur 2 dari 10)

Gas Boss 19 Nov 2026 17:09 WIB. EduAi membantu mahasiswa menulis skripsi yang benar.
Fitur ini untuk mahasiswa yang membawa naskah sendiri: memeriksa apakah format
naskahnya sudah sesuai Pedoman Skripsi Prodi Manajemen FEB UPB Edisi Revisi 2025.

## Prinsip (disetujui Boss 19 Nov 17:06-17:08 WIB)
- LENGKAPI modul yang sudah ada (`app/standar_penulisan.py`), BUKAN modul baru.
  Aturan sudah ada sebagai DATA (`ATURAN_BAKU`); yang dibangun hanya pemeriksanya.
- Deterministik, TANPA LLM, GRATIS (0 token). Hasil pasti sama setiap kali dicek.
- Satu aturan = satu baris. Panel hanya menampilkan yang belum lulus,
  masing-masing satu kalimat alasan. Yang lulus cukup centang hijau.
- Mesin tidak pernah memblokir mahasiswa, hanya menunjukkan.
- Vonis tiga macam: `lulus` / `tidak` / `ragu` ("Perlu diperiksa").
  Ragu dipakai bila mesin tidak bisa memastikan (bukan berpura-pura tahu).
- Satu pola dengan konsistensi/pustaka: hasil di Setelan, gerbang sidik berkas,
  pekerja latar, panel di `naskah.html`.

## Temuan sonde fid 81 (19 Nov 2026, BUKTI sebelum bangun)
Sonde membaca `/tmp/fid81.docx` (salinan live fid 81, 131 halaman) dengan
python-docx. Temuan ini menentukan rancangan:

1. **Font/ukuran/spasi/rata TIDAK tertulis di run.** Semua run mengembalikan
   `font.name=None`, `font.size=None`. Font TNR 12 ternyata tertulis di
   DEFAULT DOKUMEN (`docDefaults`: `rFonts` Times New Roman, `sz` 24 = 12pt).
   Akibatnya pemeriksa WAJIB menyelesaikan rantai gaya: run → gaya paragraf
   → default dokumen. Tanpa ini semua terbaca None dan pemeriksa salah tandai.
2. **Margin seksi 1-7 sudah benar** (4,0 / 3,0 / 4,0 / 3,0 cm). Seksi 0
   (bagian awal) TIDAK punya `pgMar` di XML → kemungkinan memakai bawaan
   2,54 cm. Pemeriksa menandai seksi tanpa margin eksplisit sebagai `ragu`,
   bukan `tidak` (jujur: tidak tertulis di berkas).
3. **Nomor halaman sudah benar**: seksi 0 `pgNumType` lowerRoman (bagian awal),
   seksi 1 decimal (Bab I ke atas), seksi 2-7 None (mewarisi decimal).
   Pemeriksa menyelesaikan `pgNumType` dengan cara yang sama (eksplisit,
   kalau tidak ada mewarisi seksi sebelumnya).
4. **Spasi 1,5 mendominasi isi** (595 paragraf), 1,0 ada 88 paragraf (keterangan
   tabel/gambar dan bagian awal — BENAR menurut pedoman, spasi 1,0 di sana).
   Jadi pemeriksa spasi HANYA menilai paragraf isi (gaya Normal/List Paragraph),
   bukan keterangan dan bagian awal.
5. **Judul bab asli adalah penanda telanjang** ('BAB I' .. 'BAB V', gaya Heading 1,
   tebal dari gaya, rata tengah dari gaya). Judul terbelah dua baris
   ('BAB I' + 'PENDAHULUAN') adalah sisa Bagian Awal, BUKAN pelanggaran format,
   tidak ditandai di v1.
6. **Keterangan tabel asli ada 28 tabel.** Keterangan 'Tabel 1. 3' dan 'Tabel 1. 4'
   ternyata RATA TENGAH — padahal pedoman minta rata kiri. Itu pelanggaran nyata
   yang pemeriksa harus tangkap. Nomor tertulis '1. 1' (spasi sesudah titik);
   pemeriksa menormalkan spasi saat membaca nomor ('1. 1' → '1.1'), tidak ditandai.
7. **Hasil SPSS ditempel sebagai GAMBAR, bukan tabel.** Di Bab IV, 'Tabel 4.x'
   diikuti gambar tangkapan SPSS, bukan elemen tabel. Pemeriksa memasangkan
   keterangan Tabel dengan tabel (tbl) ATAU gambar yang ditempeli keterangan
   Tabel. Gambar yang sudah dipasangkan sebagai tabel BUKAN gambar isi.
   Tabel lampiran (sesudah Daftar Pustaka) tidak memakai keterangan 'Tabel N.M'
   dan tidak dinilai — pemeriksa hanya menilai isi (Bab I sampai Daftar Pustaka).
8. **Kalimat rujukan bukan keterangan.** 'Tabel 4.1 menunjukkan bahwa...' dan
   'Gambar 4.1 memperlihatkan...' adalah kalimat isi yang merujuk, bukan
   keterangan. Pemeriksa menolak paragraf yang sesudah nomornya ada kata
   rujukan (menunjukkan, memperlihatkan, bahwa, ...).
9. **Keterangan gambar asli ada 45 drawing.** 'Gambar 2.2 Model Penelitian'
   ternyata RATA KIRI — padahal pedoman minta rata tengah. Pelanggaran nyata.
   Ada paragraf kosong sesudah drawing; pemeriksa melompati paragraf kosong
   saat mencari keterangan. Gambar di bagian awal (logo sampul, foto penulis)
   bukan gambar isi dan tidak dinilai.
8. **Daftar Isi/Tabel/Gambar ikut terbaca** sebagai paragraf 'BAB I. PENDAHULUAN\t21'
   dan 'Tabel 1. 1 ...\t26'. Pemeriksa TIDAK menilai entri daftar isi (bukan
   judul/keterangan asli). Judul bab dicari dari gaya Heading 1 + pola 'BAB ',
   keterangan dicari dari posisi relatif terhadap tabel/gambar, bukan dari teks saja.

## 8 pemeriksaan (v1)
| # | id | Aturan (dari ATURAN_BAKU) | Cara cek |
|---|----|---------------------------|----------|
| 1 | margin | margin 4/3/4/3 cm | `section.*_margin` per seksi; None → ragu |
| 2 | huruf | isi Times New Roman 12 | font+ukuran efektif paragraf isi, dominan ≥90% |
| 3 | spasi | isi spasi 1,5 | spasi efektif paragraf isi, dominan ≥90% |
| 4 | perataan | isi rata kiri kanan | rata efektif paragraf isi, dominan JUSTIFY ≥90% |
| 5 | judul_bab | tengah, tebal, kapital, tanpa titik | paragraf 'BAB ...' (Heading 1/tebal/tengah): rata tengah, tebal, kapital, tanpa titik |
| 6 | tabel | nomor rangkap dua, judul DI ATAS, rata kiri, tidak tebal, tanpa titik | tiap tabel: paragraf sebelumnya cocok 'Tabel N.M'; cek rata kiri, tidak tebal, tanpa titik, nomor ganda. Tanpa keterangan → ragu |
| 7 | gambar | nomor rangkap dua, judul DI BAWAH, rata tengah, tidak tebal | tiap drawing: paragraf tak-kosong sesudahnya cocok 'Gambar N.M'; cek rata tengah, tidak tebal, tanpa titik, nomor ganda. Tanpa keterangan → ragu |
| 8 | nomor_halaman | bagian awal romawi kecil, Bab I ke atas arab | `pgNumType` efektif per seksi: seksi 0 romawi, sisanya desimal. Satu seksi saja → ragu |

Nilai efektif = run → gaya paragraf → default dokumen (`docDefaults`).
Ambang dominan 90%: bila ≥90% paragraf isi cocok, lulus; bila tidak, `tidak`
dengan alasan menyebut nilai dominan dan jumlah yang menyimpang.
Nomor halaman dan margin yang tidak tertulis → `ragu`, bukan `tidak`.

## Bukan di v1 (batas jujur)
- Jumlah halaman minimal 50: python-docx tidak bisa menghitung halaman.
  Jumlah halaman sudah tampil di panel Struktur (diukur OnlyOffice). Tidak dibuat-buat.
- Judul bab terbelah dua baris: sisa Bagian Awal, bukan pelanggaran format.
- Isi tabel (font tabel, garis vertikal): pedoman tidak menetapkan ukuran font
  tabel; garis vertikal butuh baca XML tabel, ditunda.
- Kutipan blok (menjorok 1,2 cm, spasi tunggal): butuh deteksi kutipan panjang,
  ditunda ke v2.

## Arsitektur (pola konsistensi/pustaka, tanpa modul baru)
- Logika: `app/standar_penulisan.py` Bagian 2 (fungsi `periksa_format`,
  `baca_docx_format`, `langkah_berikut_format`, pemeriksa `_cek_*`).
- Rute: `app/rute_format.py` (pola `rute_konsistensi.py`): POST
  `/v1/format/mulai-latar` (pekerja latar `proses`, tekan 2x ditahan sopan),
  GET `/v1/format/status`. Gerbang sidik berkas (SHA-256, pola
  `pustaka_periksa.sidik_berkas`): berkas tidak berubah → hasil lama, tanpa
  baca ulang. Kunci Setelan `format_hasil_berkas_<fid>`, komentar proses
  'Cek Format'. Didaftarkan di `app/main.py` sesudah router konsistensi.
- Panel: `app/templates/naskah.html`, tombol 'Cek Format' di samping
  'Cek Konsistensi'; wadah `panel-format-<fid>`; CSS `.panel-format`
  (tiga status: lulus ✓ hijau, tidak ! merah, ragu ? kuning); blok JS sendiri
  (polling 3 detik, ketuk baris buka alasan). Tidak ada kata 'salah' di teks tampil.
- Tes: `tests/test_format.py` (docx kecil buatan python-docx: benar + tiap
  pelanggaran) dan `tests/test_format_rute.py` (Setelan round-trip + endpoint
  + panel). Kriteria: semua tes lulus; fid 81: lulus 5, tidak 2, ragu 1
  (tabel 17/17 keterangan tidak rata kiri, gambar 2/11 tidak rata tengah,
  margin seksi 1 ragu karena tidak tertulis).
