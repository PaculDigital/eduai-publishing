# Rancangan Lapisan untuk Naskah Bentuk Lain (BAHAS DULU, belum dibangun)

Tanggal: 11 Nov 2026. Status: rancangan diskusi, menunggu putusan Boss.
Tujuan: Jev/Hakim kini teruji di 3 naskah bentuk mirip (skripsi kuantitatif, BAB bernomor).
Lapisan ini mengantisipasi naskah bentuk lain tanpa merusak yang sudah jalan.

## Masalah yang dijawab
- Bentuk naskah beda-beda: BAB tanpa nomor, BAB Romawi, banyak tabel, sistematika
  di awal, PDF pecah per huruf, naskah berbahasa Inggris, skripsi kualitatif.
- Aturan dan ambang yang disetel untuk satu bentuk bisa salah di bentuk lain
  (contoh nyata: judul BAB sampah dari baris sistematika, sudah ditutup R2-3;
  contoh lain: fid=115 salah nomor bab, "BAB VI" tertulis untuk Bab IV).
- Tanpa lapisan, bentuk tak dikenal dipaksa lewat jalur yang sama dan hasilnya
  diam-diam salah.

## Lapisan yang diusulkan (3 lapis, urut jalan)

### Lapis 1 — Pengenal bentuk (deterministik dulu, tanpa Jev bila bisa)
Dibaca sebelum pemetaan, dari teks naskah saja:
- Penomoran BAB: angka (BAB 1), Romawi (BAB I), tanpa nomor, campuran.
- Sistematika di awal: ada / tidak ada.
- Kepadatan tabel: banyak sel tabel / sedikit.
- Kualitas ekstraksi: teks utuh, pecah per huruf, banyak byte NUL.
- Bahasa: Indonesia / Inggris / campuran.
Keluaran: satu "profil bentuk" (misalnya: bernomor + sistematika + tabel-sedang).
Profil ini memilih: aturan stitch yang dipakai, ambang Hakim, dan apakah
naskah boleh jalan otomatis atau harus ke antrean manusia.

Aturan keras: pengenal bentuk harus deterministik (pola teks, bukan tebakan
model). Bila bentuk tidak dikenali, naskah TIDAK dipaksa, melainkan masuk
Lapis 3 (antrean manusia).

### Lapis 2 — Pendapat kedua (hanya untuk baris goyang)
Bukan tanya ulang semua baris. Hanya baris yang goyang antar-run atau
Hakim ragu/curiga:
- Ditanya ulang dengan sudut berbeda (misalnya: "baris ini awal blok baru
  atau lanjutan blok sebelumnya?" dengan konteks 3 baris sebelum/sesudah).
- Bila tersedia, dibandingkan dengan model kedua (1.13 sebagai pembanding,
  bukan pengganti 1.14).
- Hakim memutuskan dari kedua jawaban + aturan deterministik; bila tetap
  tidak sepakat, baris masuk antrean manusia, bukan dipaksa.
Biaya: hanya baris goyang yang ditanya ulang (puluhan per naskah, bukan
ratusan), jadi biaya terkendali.

### Lapis 3 — Antrean manusia untuk bentuk tak dikenal (sudah ada, dipertegas)
Sudah dirancang di RENCANA_ALUR_USER_JEV_HAKIM.md (layar tinjau sengketa).
Dipertegas di sini: bentuk tak dikenal, naskah berbahasa Inggris, dan
naskah yang kualitas ekstraksinya buruk TIDAK dipetakan otomatis sampai
manusia melihat bentuknya sekali dan memberi profil bentuk baru.

## Yang dibutuhkan sebelum membangun (belum ada)
1. Contoh naskah bentuk lain: minimal 2-3 naskah per bentuk yang mau
   didukung dulu (Boss yang pilih bentuknya).
2. Label kebenaran dasar untuk tiap bentuk baru (seperti paket 397 baris
   yang sudah ada untuk 3 naskah lama).
3. Gerbang per bentuk: baseline gerbang yang ada (v10) hanya berlaku untuk
   bentuk yang sudah teruji; bentuk baru butuh baseline sendiri.

## Risiko yang harus dijaga
- Pengenal bentuk yang salah lebih buruk daripada tidak ada pengenal:
  aturan yang salah dipilih untuk seluruh naskah. Karena itu Lapis 1
  deterministik dan bentuk tak dikenal dilempar ke manusia.
- Lapisan menambah biaya (pendapat kedua = panggilan Jev tambahan) dan
  kerumitan. Biaya dibatasi hanya untuk baris goyang.
- Jangan membangun lapisan untuk bentuk yang belum ada contohnya:
  itu menebak, bukan mengantisipasi.

## Putusan yang ditunggu dari Boss
1. Bentuk naskah apa yang didukung dulu? (misalnya: skripsi template UPB,
   skripsi kampus lain, tesis, naskah tanpa nomor BAB, naskah Inggris)
2. Apakah Boss bisa sediakan 2-3 contoh naskah per bentuk itu?
3. Apakah Lapis 2 (pendapat kedua) boleh memakai 1.13 sebagai pembanding,
   atau cukup tanya ulang 1.14 dengan sudut berbeda?
4. Gas membangun Lapis 1 dulu, atau tunggu contoh naskah terkumpul?
