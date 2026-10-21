# DOKUMENTASI INDUK — RANCANGAN PEMBANGUNAN BAB IV EduAi

> **UNTUK DIBACA AGEN AI / PENGEMBANG MANA PUN SEBELUM MENYENTUH BAB IV.**
> Dokumen ini adalah KONSOLIDASI FINAL seluruh keputusan Bos tanggal
> 21 Oktober 2026. Isinya keputusan yang SUDAH TERKUNCI lewat diskusi
> panjang Bos ↔ Wulan. Bukan usulan, bukan draf bebas.
>
> ⚠️ **STATUS SAAT DOKUMEN INI DITULIS: BELUM ADA KODE FITUR BAB IV.**
> Mode kerja yang diperintahkan Bos: **BAHAS DULU, JANGAN KODING DULU.**
> Agen yang membaca ini TIDAK BOLEH mulai membangun sebelum Bos
> menyatakan mulai. Tugas dokumen ini: membuat agen paham rencana secara
> utuh dan TIDAK berhalusinasi (tidak mengarang aturan, harga, endpoint,
> atau kemampuan yang tidak ada).

Disusun: Wulan · 21 Oktober 2026 · Branch: `agen/wulan/bab4-statistik-backend`
Dokumen sumber (baca bila butuh rincian/riwayat):
`AUDIT_WULAN_BAB4_21OKT2026.md` · `RANCANGAN_JEMBATAN_BAB4_21OKT2026.md` ·
`RANGKUMAN_DISKUSI_BAB4_21OKT2026.md` · `CATATAN_DISKUSI_BAB4_KONVERSI_08OKT2026.md`

---

## 0. CARA MEMBACA DOKUMEN INI (ANTI-HALUSINASI)

1. Setiap aturan di dokumen ini berlabel **[TERKUNCI]** (keputusan Bos),
   **[FAKTA]** (terverifikasi dari kode/live), atau **[USULAN]** (belum
   diputuskan — JANGAN dibangun seolah-olah sudah pasti).
2. Kalau ada hal yang TIDAK tertulis di sini, artinya **belum diputuskan**.
   Agen wajib bertanya ke Bos, BUKAN mengisi sendiri dengan tebakan.
3. Angka harga, nama endpoint, dan bentuk data di dokumen ini adalah
   SATU-SATUNYA yang sah. Jangan menambah, mengurangi, atau "memperbaiki"
   tanpa keputusan Bos baru.
4. Istilah di dokumen ini wajib dipakai persis. Ada daftar istilah
   terlarang di §2.

---

## 1. APA YANG DIBANGUN

Fitur **BAB IV (Hasil dan Pembahasan)** di EduAi: user yang naskahnya
baru sampai BAB III dibantu menyiapkan penelitiannya, mengambil data,
mengolahnya lewat mesin **Statistik Lab sebagai backend**, dan menerima
draf BAB IV di editor EduAi.

**[TERKUNCI]** BAB IV = Hasil & Pembahasan. BUKAN Metodologi
(Metodologi = BAB III). Kebingungan istilah ini sudah diputuskan Bos
21 Okt 2026 — jangan dibuka lagi.

**[TERKUNCI]** Prinsip pengalaman user (berlaku untuk SEMUA bagian):
di dalam boleh rumit, di luar harus terasa SEDERHANA dan MUDAH.
Mahasiswa tidak boleh dibebani istilah teknis, pilihan jargon, atau
formulir berulang.

---

## 2. ISTILAH — WAJIB & TERLARANG

**[TERKUNCI] DILARANG memakai kata "senjata"** (keputusan Bos 21 Okt 2026)
untuk menyebut instrumen/alat. Pakai istilah berikut:

| Istilah resmi | Artinya |
|---|---|
| Peta Penelitian | Hasil pembacaan BAB I–III: jenis, desain, model, sampel — yang disahkan user |
| Instrumen | Kuesioner (kuantitatif) / panduan wawancara (kualitatif) + template datanya |
| Paket Olah Data | Satu-satunya paket berbayar untuk tahap ini (30 token) — lihat §10 |
| Halaman Data Lapangan | Satu halaman tempat semua data masuk (ketik / upload / simulasi) |
| Pra-Survei | Uji coba instrumen ke responden asli sedikit (10–30) sebelum survei utama |
| Simulasi | Data REKAAN untuk belajar (mesin kuantitatif / AI kualitatif) — bonus paket |
| Placeholder Simulasi | Contoh tampilan statis SEBELUM bayar (bukan simulasi sungguhan) |
| Kunci Hasil | Tombol pembeku hasil olah data; narasi hanya lahir dari hasil terkunci |
| Olah Data / Analisis Data | Tahap hitung (ke Statistik Lab) dan tahap tafsir |

**[TERKUNCI]** Peran variabel mengikuti konvensi mesin Statistik Lab:
**X** = bebas, **Y** = terikat/hasil, **M** = perantara (MEDIATOR),
**Z** = penguat (MODERATOR). Jangan menukar M dan Z.
(Kode mesin: `kolom_m` = mediasi, `kolom_z` = moderasi.)

**[TERKUNCI]** Teks yang dilihat user menyebut produk **"EduAi"** saja
(aturan repo: jangan menyebut "AI", nama agen, atau nama model di UI).

---

## 3. KEADAAN SEKARANG [FAKTA — terverifikasi 21 Okt 2026]

### 3.1 Di EduAi (repo ini, @ c57f5cd, produksi eduai.bikinaja.id LIVE)
SUDAH ADA (jangan bangun ulang):
- Kerangka BAB IV kuantitatif 4.1–4.5 di `app/kerangka_bab.py`
  (4.1 deskripsi objek · 4.2 deskripsi data · 4.3 uji prasyarat ·
  4.4 uji hipotesis · 4.5 pembahasan).
- Harga dua layanan BAB IV di `app/config.py`: `analisa` 30 token,
  `olah_data` 30 token (`TOKEN_KERANGKA_BAB['4']` dan `['4:olah_data']`),
  logika tampilannya di `app/kerangka.py::susun_rencana`.
- Peta bab oleh Jev, cek kelengkapan (`app/konversi.py`), satu dompet
  token (`app/kuota.py`), editor OnlyOffice, pola revisi terima/tolak
  per bagian, pola harga revisi (lihat §10.4).
- Mesin tulis bab (`kerangka.bangun_isi`), rute konversi jurnal.

BELUM ADA (inilah yang akan dibangun):
- Instrumen (kuesioner/panduan) hasil peta, template data, halaman Data
  Lapangan, pra-survei, simulasi BAB IV, jembatan API APAPUN ke
  Statistik Lab (grep "statistik" di `app/*.py` hanya menemukan teks dan
  konfigurasi harga — TIDAK ada panggilan HTTP ke Statistik Lab).

### 3.2 Di Statistik Lab (repo terpisah `PaculDigital/statistik-lab`,
### produksi statistik.bikinaja.id LIVE)
Mesin kuantitatif = API server sungguhan [FAKTA dari kode src @ 9ca0364]:
- `POST /api/diagnosis/unggah` (multipart, maks 10 MB) →
  `{kunci, n_baris, n_kolom, kolom[], pratinjau}` — menyimpan data
  SEMENTARA DI MEMORI server (maks 12 sesi, umur 45 menit, tidak ke disk).
- `POST /api/diagnosis/periksa-peran` `{kunci, peran}` → validasi peran
  kolom TANPA menghitung.
- `POST /api/diagnosis/periksa` `{kunci, mode: spss|pls, kolom_x, kolom_y,
  kolom_m, kolom_z, peran, konstruk, missing}` → hasil lengkap:
  koefisien (b/se/t/p), R² & R²adj, normalitas (KS/SW/D'Agostino),
  heteroskedastisitas (Glejser), VIF, linearitas, outlier, Durbin-Watson,
  `kaitan` (mediasi bootstrap + moderasi interaksi dari
  `app/hitung/kaitan.py`), bahan grafik (`titik`), dan `masalah[]`
  berisi nasihat perbaikan. Mode PLS: outer loading, AVE, CR, Cronbach
  alpha, VIF inner, Fornell-Larcker, HTMT.
- Fungsi hitungnya MURNI: `periksa_spss(df, ...)` dan
  `periksa_pls(df, ...)` di `app/diagnosis.py` menerima tabel dan
  mengembalikan dict — tidak bergantung penyimpanan sesi. Yang memakai
  sesi hanya rute HTTP lamanya.
- Mesin SIMULASI data: `POST /api/buat-data` dan
  `POST /api/buat-data/jalur` — membangun data terkalibrasi per jalur
  (regresi, mediasi, moderasi; teruji koefisien terbaca ≈ diminta,
  toleransi ±0,02) lengkap dengan unduhan format SPSS/SmartPLS.
- Modul KUALITATIF `/kualitatif` LIVE: dua instrumen analisis —
  (1) Analisis Tematik (panduan → koding → triangulasi → tafsir),
  (2) Analisis SWOT (faktor → matriks SO/WO/ST/WT → IFAS/EFAS + kuadran).
  KEDUA hitungan itu berjalan DI BROWSER user (JavaScript, data di
  localStorage) — BUKAN API server. Server hanya menyediakan
  `POST /api/kualitatif/saran` (proksi saran AI), dan
  `POST /api/kualitatif/ekspor-qdpx` + `/ekspor-qdc` (rakit ekspor
  REFI-QDA, valid XSD resmi). Ekspor hasil analisis: tombol
  "Unduh untuk Bab 4 (.md)" di halaman tersebut.
- `GET /api/status` → `{app, ai_aktif, versi}` (live: ai_aktif=true).

### 3.3 Jembatan yang SUDAH diizinkan [TERKUNCI sejak 08 Okt 2026]
`CATATAN_DISKUSI_BAB4_KONVERSI_08OKT2026.md` §4.4 memuat putusan Bos:
Statistik Lab BOLEH menjadi backend khusus EduAi lewat JEMBATAN RESMI
(panggilan API eksplisit, pola `oo-converter`), dengan syarat:
rumah data = EduAi; mesin hanya menghitung dan TIDAK menyimpan;
yang memarsing = EduAi (Jev/AI) sehingga mesin tidak menebak;
prasyarat (jenis/desain/model/sampel) diatur di EduAi.
Ini TIDAK melanggar `ATURAN_BATAS_PROYEK_03OKT2026.md` selama bukan
pinjam kredensial/.env proyek lain.

---

## 4. ALUR UTUH [TERKUNCI]

```
[0] User membuka naskah (BAB I–III ada) → memilih menyiapkan BAB IV
[1] Jev membaca bentuk naskah; AI membaca isi → USULAN PETA PENELITIAN
[2] User MENGESAHKAN peta (kartu konfirmasi, §5) ← gerbang wajib
[3] Paket Olah Data dibeli (30) → instrumen dibuat dari peta (§6)
[4] (Opsional dianjurkan) PRA-SURVEI (§8) — boleh dilewati / manual
[5] User ke lapangan; data kembali ke HALAMAN DATA LAPANGAN (§7)
    — atau menekan SIMULASI (§9) untuk belajar
[6] User memeriksa & membetulkan tabel → KIRIM
[7] Jembatan Opsi B (§11) → Statistik Lab menghitung → hasil pulang,
    disimpan DI EDUAI
[8] User menekan KUNCI HASIL → hasil membeku sebagai versi resmi
[9] Narasi dibeli (30, terpisah) → AI menulis draf BAB IV dari hasil
    terkunci + bacaan BAB II/III → masuk editor
[10] Jev memeriksa hasil; user terima/tolak per bagian (pola lama)
```

Tidak ada langkah yang boleh dilompati oleh sistem. Kalau peta belum
disahkan, instrumen TIDAK dibuat. Kalau hasil belum dikunci, narasi
TIDAK ditulis.

---

## 5. PETA PENELITIAN & MEKANISME PENGESAHAN [TERKUNCI]

### 5.1 Dari mana peta dibaca [FAKTA metodologis]
- Judul: kata "pengaruh A terhadap B" → calon X & Y; "melalui/dimediasi"
  → calon M; "dimoderasi/diperkuat" → calon Z.
- Rumusan masalah & hipotesis (BAB II): satu hipotesis = satu jalur;
  jumlah jalur WAJIB sama dengan jumlah hipotesis.
- Definisi operasional (BAB III): daftar resmi variabel + indikatornya
  (indikator inilah sumber butir instrumen).
- Teknik analisis (BAB III): regresi/analisis jalur/SEM-PLS/MRA
  mengonfirmasi bentuk model.
- Desain dibaca dari SIDIK JARI FAKTA (lihat 5.3), bukan dari label
  yang ditulis user.
- Kualitatif: yang dicari BUKAN variabel, melainkan fokus penelitian,
  informan (internal/eksternal), teknik (wawancara/observasi/dokumen),
  dan rencana triangulasi.

### 5.2 Siapa menjaga presisi — empat lapis [TERKUNCI]
1. **Jev** menunjuk TEMPAT (bab/subbab/tabel) — Jev hanya membaca
   BENTUK/STRUKTUR/KEBERADAAN, tidak menilai isi (aturan induk repo).
2. **AI** mengusulkan isi peta, dan SETIAP unsur usulan WAJIB ditempel
   BUKTI kalimat asli dari naskah. Tidak ada bukti → status
   "tidak ditemukan", DILARANG mengarang.
3. **Aturan pemeriksa** menjaga konsistensi bentuk: ada M ⇒ ada jalur
   masuk DAN keluar dari M; ada Z ⇒ ada interaksi; jumlah jalur =
   jumlah hipotesis. Usulan yang melanggar DITOLAK sistem, bukan
   diteruskan.
4. **User mengesahkan** di satu kartu peta. Per baris user cukup
   MENEKAN tombol: [Benar] · [Ganti peran] · [Ini bukan variabel].
   AI yang RAGU (keyakinan rendah / ada unsur tak ditemukan) ditanya
   LEBIH DULU secara terpisah, tidak dicampur ke kartu utama.

### 5.3 Prinsip TANYA FAKTA, BUKAN LABEL [TERKUNCI]
User TIDAK PERNAH ditanya label jargon (mis. "penelitianmu survei,
eksperimen, atau komparatif?") karena kebanyakan orang salah memilih
label dan instrumen bisa lahir salah. Aturannya:
- Label (jenis/desain) DITENTUKAN sistem dari sidik jari FAKTA di
  naskah: ada perlakuan/tidak; ada kelompok kontrol/tidak; diukur
  sebelum–sesudah/tidak; kuesioner sekali sebar/tidak.
- Bila fakta kurang, yang DITANYAKAN adalah pertanyaan fakta sehari-hari
  tentang apa yang user LAKUKAN (model pertanyaannya sudah dibahas
  dalam diskusi; user menjawab cerita, label dihitung aturan).
- User mengonfirmasi CERITA FAKTUALNYA, bukan labelnya.

### 5.4 Visual diagram [TERKUNCI]
Model digambar sebagai diagram berlabel jalur **H1, H2, H3, …**
(contoh acuan: model mediasi Nura — X1, X2, Z perantara, Y — 7 jalur
H1–H7: X1→Z, X2→Z, Z→Y, X1→Y, X2→Y, X1→Z→Y, X2→Z→Y).
Gambar yang SAMA dipakai ulang di tiga momen: (a) kartu pengesahan
peta, (b) panel pengaturan simulasi (pengatur menempel di panahnya),
(c) hasil hitung (panah signifikan menyala, tidak signifikan pudar,
angka tertera). Padanan kualitatif: gambar peta fokus × informan
(triangulasi).

### 5.5 Mixed methods / campuran [TERKUNCI]
Peta dapat terbaca CAMPURAN sejak awal (variabel+hipotesis DAN
fokus+informan). Alurnya dua putaran BERURUTAN (explanatory sequential):
putaran 1 kuantitatif penuh → putaran 2 kualitatif, yang pertanyaan
pendalamannya DIBANGUN DARI HASIL KUANTITATIF (mis. jalur yang tidak
signifikan digali sebabnya ke informan). BAB IV-nya:
4.1 gambaran umum · 4.2 hasil kuantitatif · 4.3 hasil kualitatif ·
4.4 pembahasan TERPADU. Harga mengikuti §10.2.

---

## 6. INSTRUMEN [TERKUNCI]

Instrumen SELALU berpasangan: alat ambil data + wadah pengembaliannya,
keduanya lahir dari peta YANG SAMA sehingga data yang pulang PASTI
cocok dengan mesin ("match data").

### 6.1 Kuantitatif
- **Kuesioner**: butir lahir dari indikator di definisi operasional
  (BAB III), skala Likert 1–5, bahasa diarahkan ke responden.
- **Template data**: kolom PERSIS struktur mesin — pola nama kolom
  per butir `Nama_Variabel_Nomor` (contoh: `Kualitas_Produk_1`),
  ditambah kolom identitas responden (untuk profil 4.1, §12.4).
- **Kartu petunjuk lapangan 1 halaman**: cara sebar, target jumlah,
  cara mengembalikan data.
- Ketiganya diserahkan sebagai **SATU paket unduhan** (§8.1).

### 6.2 Kualitatif
- **Panduan wawancara per jenis informan** (internal & eksternal
  terpisah) — pertanyaan dirancang BERPASANGAN antar jenis informan
  dan antar teknik, khusus agar triangulasinya bisa jalan (§12).
- **Template catatan lapangan** sesuai panduan.
- **Kartu petunjuk** 1 halaman.
- Daftar informan DIDAFTARKAN sejak tahap ini (dipakai otomatis di
  4.1 — user tidak mengetik ulang).

---

## 7. HALAMAN DATA LAPANGAN [TERKUNCI]

SATU halaman untuk semua data masuk. Tabelnya satu: baris = responden
atau informan; kolom = butir (kuantitatif) atau pertanyaan (kualitatif).
Data SELALU bisa diperiksa dan dibetulkan user di tabel itu SEBELUM
dikirim hitung. Tiga pintu masuk ke tabel yang sama:

1. **Ketik manual** — user menyalin hasil pengumpulannya sendiri
   (misalnya dari Google Form miliknya) ke tabel.
2. **Upload template** — file template dari paket instrumen diunggah,
   tabel langsung terisi otomatis.
3. **Simulasi** — tombol pengisi otomatis untuk belajar (§9).

**[TERKUNCI] Integrasi mengelola Google Form DITOLAK Bos** (rumit hak
akses/izin Google). JANGAN mengusulkan/membangun integrasi Google Form,
Google Drive user, atau API Google untuk fitur ini.

Pemeriksaan kecocokan kolom (nama kolom vs pola mesin) dilakukan DI
halaman ini, sebelum data dikirim ke jembatan.

---

## 8. PRA-SURVEI (UJI COBA INSTRUMEN) [TERKUNCI]

### 8.1 Beda dengan simulasi — jangan tertukar
| | Pra-Survei | Simulasi |
|---|---|---|
| Responden | ASLI, sedikit (10–30, di luar sampel utama) | TIDAK ADA (rekaan) |
| Data | Jawaban asli pada kuesioner asli | Dibuat mesin (kuantitatif) / AI (kualitatif) |
| Tujuan | Memeriksa KUESIONERNYA: butir valid? variabel reliabel? | Belajar & melihat contoh jadi |
| Posisi | TAHAPAN di alur (sebelum sebar besar) | Tombol di halaman Data Lapangan, kapan saja |

### 8.2 Aturan mainnya
- **Satu unduhan saja untuk seluruh alur** (keputusan anti-bingung):
  paket di §6 diunduh PALING AWAL, sebelum pra-survei. Pra-survei
  MEMAKAI paket yang sama; TIDAK ada berkas "versi pra-survei" dan
  "versi lapangan" yang terpisah.
- Pra-survei memakai **alat hitung yang SAMA** dengan olah data utama —
  BUKAN mesin/endpoint khusus baru. Ia adalah mode pemeriksaan awal
  dari alat yang sama: berhenti di validitas tiap butir + reliabilitas
  tiap variabel; data masuk berlabel `pra-survei`, terpisah dari data
  utama; keluarannya KARTU KESEHATAN KUESIONER (butir lolos / lemah →
  perbaiki kata-kata atau buang), bukan hasil penelitian.
- Yang menghitung adalah MESIN (rumus pasti: korelasi butir–total,
  Cronbach Alpha). AI hanya MENERJEMAHKAN hasil ke bahasa sederhana
  dan MENGUSULKAN kata-kata pengganti untuk butir lemah.
- Butir diperbaiki dari hasil pra-survei → user mengunduh ulang HANYA
  kuesioner versi perbaikannya (berkas yang sama, edisi revisi);
  semua lolos → tidak ada unduhan baru, paket yang sama langsung ke
  lapangan. Perbaikan instrumen dari pra-survei TIDAK memotong jatah
  revisi data (§10.3).
- **Boleh dilewati** (tombol "Lewati Pra-Survei"): sistem mengingatkan
  risikonya SATU kali dengan bahasa sederhana, lalu user berangkat
  dengan paket yang sudah di tangan. Sistem TIDAK memblokir.
- **Boleh manual**: user yang sudah menguji sendiri (mis. di SPSS) atau
  memakai instrumen dari penelitian terdahulu menekan "Uji Coba
  Manual" dan MELAMPIRKAN BUKTI (hasil hitungan / keterangan sumber
  instrumen). Sistem mencatat lolos-manual beserta buktinya; tidak
  menghitung ulang.
- Uji instrumen pada DATA UTAMA tetap selalu dijalankan di tahap
  akhir pada semua jalur (itu kewajiban BAB IV, bukan pra-survei).

---

## 9. SIMULASI [TERKUNCI]

### 9.1 Dua keadaan yang sangat berbeda — jangan dicampur
1. **SEBELUM BAYAR — Placeholder**: satu contoh penelitian TETAP
   (model umum skripsi manajemen: 2 X + 1 perantara + 1 Y), data dan
   hasilnya sudah jadi, ditampilkan menarik, WAJIB bertanda jelas
   "contoh tampilan". TANPA mesin, TANPA AI (biaya nol), tidak bisa
   diatur, tidak bisa diunduh untuk dipakai. Gunanya hanya menunjukkan
   bentuk hasil akhir.
2. **SESUDAH BAYAR — Simulasi sungguhan**, bagian dari Paket Olah Data
   (§10.1): dibangun dari MODEL PENELITIAN USER SENDIRI, bisa diatur
   user, hasilnya bisa DIUNDUH dalam format template resmi yang SAMA
   PERSIS dengan template data asli (file simulasi = format file data
   asli), sehingga user bisa mengunggahnya balik lewat jalur resmi
   untuk latihan alur utuh, atau membawanya ke SPSS/SmartPLS.

### 9.2 Aturan simulasi sungguhan
- Jalurnya (kuantitatif/kualitatif) dibaca DARI PETA yang disahkan —
  tidak ditanyakan ulang.
- **TERKUNCI pada model penelitian user sendiri.** Tidak ada mode
  bebas mencoba model lain di EduAi; percobaan bebas adalah wilayah
  Statistik Lab langsung. Ini disengaja (menjaga pembagian dua produk:
  EduAi = ruang kerja resmi, Statistik Lab = laboratorium bebas).
- Bisa diatur: kuantitatif per JALUR dipilih Kuat / Sedang / Lemah /
  Tidak berpengaruh (pengatur menempel di panah diagram, §5.4);
  kualitatif per TEMA dipilih kuat (disebut semua informan) / sebagian
  / bertentangan, plus jumlah informan.
- Pembuat datanya: kuantitatif = MESIN Statistik Lab (terkalibrasi,
  konsisten dengan model); kualitatif = AI (informan fiktif + jawaban
  teks per jenis informan). **AI DILARANG mengarang angka statistik.**
- Kejujuran hasil: pengaruh lemah + sampel kecil bisa terbaca tidak
  signifikan — tampilkan APA ADANYA sebagai bahan belajar; jangan
  dipoles menjadi signifikan.
- Padanan kualitatif pra-bayar tidak ada; satu-satunya placeholder
  adalah contoh kuantitatif tetap di atas.

---

## 10. HARGA [TERKUNCI — angka final, jangan diubah/diimprovisasi]

### 10.1 Paket Olah Data — 30 token, SATU KALI, dibayar di depan
Isinya TIGA: **(1) instrumen** (§6), **(2) simulasi sungguhan** (§9.2),
**(3) olah data asli**. Tidak ada produk simulasi terpisah. Tidak ada
biaya instrumen terpisah. Harga ini SUDAH ada di kode
(`app/config.py`: `4:olah_data` = 30).

### 10.2 Harga per MODEL, bukan per jalur [TERKUNCI]
- Mediasi, moderasi, dan model banyak jalur dalam SATU model = **1×
  paket** (mesin memang menghitung semua jalur dalam satu panggilan).
  Contoh: model mediasi 7 hipotesis tetap 30, BUKAN 2× atau 7×.
- Yang membayar dua kali HANYA **penelitian campuran** (dua JENIS
  penelitian berbeda): olah data kuantitatif 30 + kualitatif 30.
- **Narasi selalu satu kali 30** per BAB IV, termasuk untuk campuran.

### 10.3 Revisi data — skema Kunci Hasil [TERKUNCI]
- Selama dalam SATU penelitian dan data yang SAMA: **revisi data
  (generate ulang) GRATIS 3 KALI**; lewat itu **5 token per sekali
  generate**. Alasan Bos: tanpa batas = Bos menanggung biaya coba-coba
  user; tempat coba-coba resmi adalah simulasi di dalam paket.
- Tombol **Kunci Hasil** membekukan versi hasil yang menjadi dasar
  narasi. Narasi hanya lahir dari hasil TERKUNCI.
- Revisi data sesudah kunci: subbab narasi yang terdampak DITANDAI;
  user memperbaikinya lewat aturan revisi narasi (10.4).

### 10.4 Revisi narasi — ikut aturan lama [TERKUNCI + FAKTA kode]
- Dikerjakan **AI: 1 token per item/bagian** (pola revisi biasa &
  kolaborasi yang sudah berjalan di `app/ai.py` + `app/kuota.py`).
- Dikerjakan **manual oleh user: GRATIS**.
- ⚠️ Yang **2 token per item** adalah aturan KHUSUS revisi per-bagian
  **konversi jurnal** (`app/konversi.py`, putusan Bos 07 Okt 2026) —
  fitur BERBEDA. JANGAN menerapkan 2 token ke BAB IV, dan jangan
  menerapkan 1 token ke konversi jurnal.
- Prinsip umum Bos: untuk situasi baru, PAKAI ULANG aturan/harga yang
  sudah ada; jangan menciptakan skema baru.

### 10.5 Layanan analisa yang sudah ada
`analisa` BAB IV = 30 token SUDAH ada di `app/config.py` sebelum fitur
ini dirancang — jangan diduplikasi dan jangan diubah angkanya. Hubungan
pasti layanan `analisa` dengan "narasi 30" di §10.1/10.2 mengikuti
susunan layanan yang sudah berjalan di `app/kerangka.py`.

---

## 11. JEMBATAN KE STATISTIK LAB — OPSI B [TERKUNCI]

### 11.1 Keputusan bentuk
**OPSI B UNTUK SEMUANYA** (kuantitatif DAN kualitatif), diputuskan Bos
21 Okt 2026. Mekanikanya: **data dikirim → langsung dihitung → hasil
pulang. TIDAK ADA data yang dititipkan/disimpan di Statistik Lab.**
Opsi A (titip data dulu memakai kunci sesi, seperti alur
`/api/diagnosis/*` yang lama) DITOLAK — jangan dibangun.

### 11.2 Paket kerja di Statistik Lab (repo sebelah, satu paket)
1. **Pintu hitung kuantitatif langsung**: endpoint baru tanpa sesi yang
   membungkus fungsi murni `periksa_spss` / `periksa_pls` — menerima
   tabel + penetapan peran dalam SATU panggilan, mengembalikan hasil
   yang sama persis dengan alur lama. Alur lama `/api/diagnosis/*`
   untuk pemakai langsung TIDAK berubah.
2. **Dua pintu kualitatif** (§12.3).
3. **Kunci pengaman antar-layanan** untuk SEMUA pintu baru itu (API
   mesin hari ini publik tanpa kunci). Kunci harus MILIK EduAi
   (kredensial layanan baru) — DILARANG meminjam kredensial/.env
   proyek lain (ATURAN_BATAS). Pembuatan kunci menunggu pengerjaan
   tahap bangun (belum ada, jangan diklaim sudah ada).

### 11.3 Aturan data pada jembatan
- Rumah data = EduAi. Hasil hitung disimpan DI EDUAI.
- Mesin hanya menerima tabel angka/teks yang sudah RAPI dari EduAi
  (parsing & perapian oleh Jev/AI di EduAi). Mesin TIDAK menebak peran
  kolom dari berkas mentah pada jembatan ini.
- Sel kosong dikirim sebagai KOSONG betulan (di SPSS terbaca
  blank/SYSMIS). DILARANG mengisi sel kosong dengan -1 atau 0.
- Batas berkas mengikuti mesin yang ada: unggahan maks 10 MB.
- **[USULAN — belum diputuskan]** batas waktu (timeout) panggilan dan
  perilaku bila mesin sibuk/mati: tanyakan Bos saat tahap bangun.

---

## 12. JALUR KUALITATIF [TERKUNCI]

### 12.1 Dua instrumen analisis — keduanya dipakai, tidak dibuat baru
1. **Analisis Tematik**: temuan per tema dari koding catatan informan,
   diperiksa TRIANGULASI (tema × informan dan tema × teknik).
2. **Analisis SWOT**: faktor internal/eksternal → matriks strategi
   SO/WO/ST/WT → tabel IFAS/EFAS → posisi KUADRAN.
Pemilihan instrumen mengikuti FOKUS penelitian dari peta — user tidak
memilih istilah. Halaman `/kualitatif` Statistik Lab untuk pemakai
langsung TIDAK berubah dan TIDAK digantikan.

### 12.2 Kerangka BAB IV kualitatif
Tulang punggung SAMA untuk semua jalur (juga kuantitatif & campuran):
**4.1 gambaran · 4.2 sajian data · 4.3 pengujian/keabsahan ·
4.4 pembahasan.**
- Tematik: 4.1 lokasi & informan · 4.2 temuan per tema + KUTIPAN ASLI
  informan · 4.3 matriks triangulasi (tema kuat/lemah) · 4.4 pembahasan
  dikaitkan teori BAB II.
- SWOT: 4.1 sama · 4.2 faktor internal/eksternal + tabel IFAS/EFAS ·
  4.3 matriks SWOT + kuadran + strategi SO/WO/ST/WT · 4.4 pembahasan.

### 12.3 Kualitatif lewat API — dua panggilan, tanpa simpan sesi
Hitungan triangulasi + SWOT (matriks, IFAS/EFAS, kuadran) yang hari ini
berjalan di browser DIPINDAH ke server Statistik Lab menjadi endpoint
tanpa sesi; EduAi memanggilnya dua kali:
1. **Koding**: EduAi mengirim catatan informan → server (dengan AI)
   mengembalikan USULAN kode/tema per potongan teks → user
   **mengesahkan/membetulkan di EduAi**. Koding SENGAJA tidak otomatis
   penuh: koding adalah tafsir peneliti, keputusan akhir di user
   (pola lama kita: AI mengusulkan, manusia memutuskan).
2. **Hitungan**: EduAi mengirim koding yang SUDAH disahkan → server
   mengembalikan matriks triangulasi + tema final + kutipan pendukung
   (tematik), ATAU matriks SWOT + IFAS/EFAS + kuadran (SWOT).
Semua panggilan AI tetap lewat **satu pintu 9router** (aturan repo).

### 12.4 Isi sekali di depan — 4.1 & deskriptif [TERKUNCI]
- User TIDAK menginput ulang apa pun untuk mengisi 4.1 dst.
- 4.1 gambaran objek: dari BAB III lewat peta. Profil responden /
  informan: DITABULASI OTOMATIS dari data yang kembali (karena itu
  kolom identitas ada sejak template dibuat, dan daftar informan
  didaftarkan sejak tahap instrumen). Tingkat pengembalian kuesioner:
  target sampel di peta vs jumlah baris yang masuk.
- Statistik DESKRIPTIF ringan (frekuensi, persen, rata-rata, tabulasi
  karakteristik) dihitung **DI EDUAI** dari data milik EduAi sendiri —
  bukan uji statistik, tidak perlu ke mesin. Uji statistik (validitas,
  reliabilitas, regresi/PLS, mediasi, moderasi) SELALU ke mesin
  Statistik Lab lewat jembatan. Jangan tertukar dua hal ini.
- Fakta yang tidak ditemukan di mana pun (naskah, peta, data)
  ditanyakan SEKALI di tahap peta sebagai pertanyaan fakta — tidak
  ditagih ulang saat menulis narasi.

---

## 13. NARASI BAB IV [TERKUNCI]

- Ditulis AI dari: hasil TERKUNCI (§10.3) + isi BAB II & III dari
  naskah user. Sumber angka HANYA hasil mesin — AI dilarang mengarang
  atau membulatkan angka statistik di luar hasil.
- **Narasi menyesuaikan jalan yang benar-benar ditempuh user.**
  Contoh: laporan pra-survei hanya ditulis bila pra-survei benar-benar
  dilakukan (tempatnya di bagian uji instrumen, BUKAN di pembahasan);
  bila dilewati, bagian itu TIDAK muncul sama sekali. Prinsip umumnya:
  sistem TIDAK menulis tentang pemeriksaan/peristiwa yang tidak
  terjadi.
- Struktur mengikuti kerangka §12.2 dan kerangka kuantitatif yang
  sudah ada di `app/kerangka_bab.py` (4.1–4.5 untuk kuantitatif:
  deskripsi objek, deskripsi data, uji prasyarat, uji hipotesis,
  pembahasan — pemetaan ke tulang punggung 4.1–4.4 mengikuti kerangka);
  campuran mengikuti §5.5.
- Hasil narasi masuk editor; per bagiannya berlaku terima/tolak dan
  revisi §10.4, diperiksa Jev seperti bab lain.

---

## 14. LARANGAN & PAGAR (WAJIB DIPATUHI AGEN)

1. **Jangan koding dulu.** Mode saat ini: diskusi/rancangan. Membangun
   hanya setelah Bos memerintahkan mulai.
2. **Pagar repo** (`AGEN_LUAR_ATURAN.md`): dilarang push ke `main`;
   alur = fork → branch `agen/<nama>/<tujuan>` → PR. Berkas TERLARANG
   diubah: `.gitignore`, `Dockerfile`, `jalankan.sh`, `SOT_*.md`,
   `ATURAN_BATAS_PROYEK_03OKT2026.md`, `scripts/periksa_kode.sh`.
   Merge ≠ deploy; deploy hanya keputusan Bos (`bash jalankan.sh`).
   Jalankan `scripts/periksa_kode.sh` sebelum PR dan tempel keluarannya.
3. **Satu pintu AI**: semua panggilan model lewat 9router
   (`app/router9.py` / `app/ai.py`). Dilarang memanggil provider AI lain
   secara langsung.
4. **Jev hanya struktur.** Jev tidak menilai mutu/isi naskah. Penilaian
   isi adalah pekerjaan AI + pengesahan user (§5.2).
5. **Jangan mengarang.** Unsur peta tanpa bukti kalimat = "tidak
   ditemukan". Angka hanya dari mesin. Harga hanya dari §10. Endpoint
   hanya yang tertulis di §3 (sudah ada) dan §11–12 (akan dibangun).
6. **Jangan membuat yang sudah ditolak**: integrasi Google Form (§7),
   opsi titip-data/sesi di jembatan (§11.1), produk simulasi terpisah
   (§10.1), mesin khusus pra-survei (§8.2), pilihan label jargon untuk
   user (§5.3), kata terlarang (§2).
7. **Jangan menumpuk di `app/main.py`** (±3.800 baris). Fitur ini
   dirancang sebagai modul terpisah — **[USULAN nama]**: `app/bab4.py`
   (orkestrasi alur) + `app/jembatan_statistik.py` (klien HTTP ke
   Statistik Lab), didaftarkan sebagai router ke `main.py`.
8. Kredensial: jangan pernah menulis token/kunci ke berkas repo atau
   dokumen. Kunci antar-layanan disimpan sebagai konfigurasi layanan,
   bukan di kode.

---

## 15. YANG BELUM DIPUTUSKAN (jangan diisi sendiri — tanya Bos)

1. Kapan mulai membangun (menunggu perintah Bos; mode sekarang bahas).
2. Cara push/PR branch dokumen ini ke GitHub (PAT sesaat / fork
   kolaborator / lokal saja) — Wulan tidak punya akun fork sendiri.
3. Pembuatan kunci antar-layanan milik EduAi (bagian paket §11.2,
   dikerjakan saat tahap bangun).
4. Timeout & perilaku kegagalan jembatan (§11.3).
5. Rincian kecil tahap bangun: apakah panel pengaturan simulasi selalu
   tampil atau hanya mode lanjutan.

---

## 16. URUTAN BANGUN YANG DIUSULKAN [USULAN Wulan — belum diperintah Bos]

1. Di Statistik Lab: pintu kuantitatif tanpa sesi + dua pintu
   kualitatif + kunci antar-layanan (satu paket, §11.2). Uji kontrak
   dengan data contoh terhadap mesin live; hasil alur baru WAJIB sama
   dengan alur lama untuk data yang sama.
2. Di EduAi: modul peta (§5) → instrumen (§6) → halaman Data Lapangan
   (§7) → pra-survei (§8) → simulasi placeholder lalu sungguhan (§9) →
   Kunci Hasil & penanda revisi (§10.3) → narasi (§13).
3. Jalur kualitatif penuh (§12), lalu campuran (§5.5).
4. Gerbang `scripts/periksa_kode.sh`, uji ujung-ke-ujung di HP
   (mobile-first: user Bos menguji lewat ponsel), baru PR.
