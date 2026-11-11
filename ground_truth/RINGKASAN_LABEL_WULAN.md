# Ringkasan Pengisian Label Kebenaran Dasar oleh Wulan

Tanggal: 10 November 2026. Branch `agen/wulan/optimalkan-jev-hakim-v5`.
Nol panggilan Jev live dipakai. Label diisi dari teks naskah (`_teks/`),
konteks di TSV, dan baseline Oktober fid=81.

## Hasil hitung (43 baris, 0 kosong, 0 ragu)

| Naskah | bab | subbab | paragraf | biasa | total |
|---|---|---|---|---|---|
| fid=81 | 0 | 0 | 11 | 10 | 21 |
| fid=112 | 1 | 0 | 1 | 8 | 10 |
| fid=115 | 1 | 1 | 1 | 6 | 9 |
| WULAN-1 | 0 | 0 | 1 | 2 | 3 |
| **Total** | **2** | **1** | **14** | **26** | **43** |

## Aturan yang dipakai (konsisten di semua naskah)

1. Penanda BAB ("BAB I" dst) = `bab`.
2. Nomor subbab + judul = `subbab` (115 no 6: "2. Manfaat Praktis",
   judul menempel dengan kalimat pertama, diverifikasi di `_teks` baris 427).
3. Awal blok isi = `paragraf`: ganti topik, butir daftar yang berdiri
   sendiri (pertanyaan penelitian, butir indikator, butir kriteria uji t,
   butir informan pertama, kalimat pertama sesudah tabel/foto).
4. Lanjutan kalimat/topik sama = `biasa`: kalimat definisi kedua dengan
   topik sama, ekor kalimat, fragmen sitasi/atribusi dalam kurung,
   fragmen tabel.
5. Tidak ada baris yang Wulan beri `ragu`: semua bisa diputuskan dengan
   aturan di atas. 6 baris keyakinan sedang di bawah sudah diperiksa ulang
   Wulan 11 Nov 2026 (Putaran 3): 5 tetap, 1 berubah (no 11).

## Keyakinan sedang (6 baris fid=81 — sudah diperiksa ulang 11 Nov 2026)

Konteks di TSV terpotong, jadi keputusan memakai aturan ganti topik,
bukan bukti jeda paragraf yang terlihat langsung. Periksa ulang memakai
teks penuh `_naskah_asih.txt` (baris sumber di bawah) dan label run yang
tersimpan:

- 81 no 4: `biasa` — definisi Keberlanjutan Usaha kedua, topik sama.
  TETAP.
- 81 no 8: `biasa` — definisi Digital Marketing kedua, topik sama.
  TETAP.
- 81 no 11: `biasa` — BERUBAH dari `paragraf`. Studi kedua (Clarissa et
  al., baris 369) dalam daftar bukti di bawah pengantar baris 365
  (Hipotesis Kedua); studi pertama (baris 367, Hanaysha) `biasa` menurut
  kedua model, jadi studi kedua ini lanjutan blok yang sama, bukan blok
  baru. Alasan lama (studi berbeda = blok baru) kalah oleh struktur
  daftar: dua butir sejajar di bawah satu pengantar tidak bisa yang satu
  lanjutan dan yang satu blok baru tanpa penanda batas.
- 81 no 12: `biasa` — penjelasan sesudah rumus, lanjutan paragraf sampel.
  TETAP.
- 81 no 13: `biasa` — kalimat sitasi lanjutan, topik sama (uji asumsi).
  TETAP.
- 81 no 17: `biasa` — kalimat koefisien kedua, topik sama. TETAP.

## Keputusan tersulit

1. **81 no 4 vs no 5 (definisi berurutan).** No 4 ("Keberlanjutan Usaha
   menurut Widayanti...") Wulan label `biasa` karena kalimat sebelumnya
   juga definisi Keberlanjutan Usaha, topik sama. No 5 ("Pepin et al....
   model bisnis...") Wulan label `paragraf` karena topik berganti ke
   model bisnis. Satu pasang ini menunjukkan aturan ganti topik bekerja.
2. **115 no 6 ("2. Manfaat Praktis...").** Teks terpotong dan konteks
   hilang di TSV, tapi `_teks` baris 427 membuktikan ini subbab bernomor
   di bawah 1.4, dengan kalimat pertama menempel di baris yang sama.
   Label `subbab`.
3. **81 no 9 ("Interaksi dua arah dengan pelanggan").** 1.13 melabel
   `subbab`, 1.14 `biasa`. Wulan setuju 1.14: ini nama indikator dalam
   daftar/tabel, bukan subbab bernomor.

## Temuan jujur: skor 1.13 vs 1.14 di 21 baris fid=81

Diukur dari label Wulan ini (sesudah periksa ulang 11 Nov 2026):
**1.13 benar 9/21, 1.14 benar 12/21.**
Artinya pada subset sengketa ini 1.14 lebih baik, dan itu BERTENTANGAN
dengan vonis lama yang memakai jarak ke baseline Oktober (paragraf 157).

Penjelasan yang jujur: baseline 157 berasal dari pipeline Oktober yang
lebih tua (sebelum perbaikan stitch dan pemisah v5-v7), jadi jarak ke
157 bukan ukuran yang adil untuk kode v7. Label kebenaran dasar inilah
yang seharusnya menjadi wasit, bukan baseline lama. Bila label Wulan
benar, jumlah paragraf sejati fid=81 lebih dekat ke ~185 daripada 157,
dan 1.14 memang lebih sering benar pada baris sengketa.

Tapi Wulan ingatkan: ini hanya 21 baris sengketa, bukan seluruh naskah.
Periksa ulang 11 Nov 2026 mengubah 1 baris (81 no 11: `paragraf` jadi
`biasa`), sehingga skor menyempit dari 13/21 vs 8/21 menjadi 12/21 vs
9/21 — vonis pindah 1.14 TETAP (dan di baris keyakinan tinggi 12/15 vs
3/15), tapi selisihnya kini 3, bukan 5. Sengketa paragraf antar-run v7
sudah masuk paket (354 baris), dan labelnya sudah lengkap.

## Verifikasi

- 43/43 baris terisi, 0 kosong, 0 ragu.
- Konsistensi: subbab 115 no 6 berada di bawah 1.4 Manfaat Penelitian,
  BAB I ada di naskah (OK). Kedua BAB terlabel adalah penanda BAB asli.
- Tidak ada label yang ditebak tanpa aturan; tiap baris punya catatan
  sumber di kolom `catatan_boss` (berawalan "Wulan:").

## Putaran 2 — 354 label sengketa paragraf (10 November 2026 malam)

Diisi empat jalur paralel dari teks naskah (`_teks/` + konteks TSV), nol
panggilan Jev. 354/354 terisi, 0 kosong, 0 ragu. Total paket kini
**397/397 terisi** (bab 6, subbab 41, paragraf 96, biasa 254, ragu 0).

| Naskah | baru terisi | bab | subbab | paragraf | biasa | ragu |
|---|---|---|---|---|---|---|
| fid=81 | 6 | 0 | 0 | 5 | 1 | 0 |
| fid=112 | 199 | 0 | 16 | 28 | 155 | 0 |
| fid=115 | 133 | 4 | 22 | 38 | 69 | 0 |
| WULAN-1 | 16 | 0 | 2 | 11 | 3 | 0 |

Catatan: 45 baris teks kosong di fid=112 dilabel `biasa` (artefak
ekstraksi/jeda halaman/sel tabel, bukan awal blok isi). Naskah fid=115
sendiri salah nomor bab (judul Bab IV tertulis "BAB VI", tetap `bab`).

## Keyakinan sedang — total 20 baris, SELESAI diperiksa ulang 11 Nov 2026

Perintah Boss 11 Nov 2026 08:09 WIB: selesaikan sekaligus, jangan
ditunggu lagi. Wulan periksa ulang ke-20 baris dengan konteks lebar
dari teks sumber (`_naskah_asih.txt` untuk fid=81; `_teks/` untuk
112/115/WULAN-1) dan label run yang tersimpan. Hasil: **19 vonis tetap,
1 berubah** (81 no 11: `paragraf` jadi `biasa`, lihat Putaran 3 di
atas). **0 baris tersisa dengan status menunggu Boss.**

- fid=81: no 4, 8, 11, 12, 13, 17 (putaran 1), no 24, 27 (putaran 2).
- fid=112: no 11, 92, 57, 78, 79, 80, 141, 147, 183.
- fid=115: no 47, 61.
- WULAN-1: no 4.
Kolom `catatan_boss` masing-masing kini berisi vonis akhir +
alasannya, diawali "Wulan (periksa ulang 11 Nov 2026)".

## Skor model 1.13 vs 1.14 dari label (berkas skor_model.json)

Bukti langsung (21 baris `beda_model_113_114` fid=81, satu-satunya baris
yang kedua model diuji di baris yang sama; dihitung ulang dari TSV
11 Nov 2026 sesudah periksa ulang): **1.13 benar 9/21, 1.14 benar
12/21**. Tanpa 6 baris keyakinan sedang: **1.13 benar 3/15, 1.14 benar
12/15** — keunggulan 1.14 justru lebih kuat di baris keyakinan tinggi.
Periksa ulang menyempitkan selisih (dari 13 vs 8 menjadi 12 vs 9)
karena 81 no 11 berbalik ke 1.13, tapi vonis pindah 1.14 TETAP.

Bukti pendukung (354 baris `sengketa_paragraf`, kedua run adalah 1.13):
run 1 benar 172/354 (48,6%), run 2 benar 125/354 (35,3%), tidak ada
yang benar 57/354 (16,1%). Artinya pada baris yang diperselisihkan,
satu run 1.13 saja hanya cocok dengan kebenaran dasar kurang dari
setengah waktu — goyang antar-run itu nyata, dan vonis satu run tidak
bisa dipercaya begitu saja pada baris sengketa.

Perhatian jujur: pengisi label melihat kolom `bukti_run`, jadi ada
risiko bias jangkar ke label yang tercantum duluan (1.13 di baris
beda_model, run 1 di baris sengketa). Bias itu bila ada justru
menguntungkan 1.13/run 1, dan 1.14 tetap menang — vonis pindah ke 1.14
tidak dilemahkan oleh bias ini. Vonis lama "1.14 TIDAK lebih baik"
(yang memakai jarak ke baseline Oktober 157) DICABUT: baseline itu
dari pipeline lama dan bukan wasit yang adil; label kebenaran dasar
inilah wasitnya. **Vonis: PINDAH ke 1.14.** Perubahan MODEL_DEFAULT
tidak dilakukan di sini; diputuskan Boss terpisah.
