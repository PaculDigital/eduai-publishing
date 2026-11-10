# Ringkasan Pengisian Label Kebenaran Dasar oleh Wulan

Tanggal: 10 November 2026. Branch `agen/wulan/optimalkan-jev-hakim-v5`.
Nol panggilan Jev live dipakai. Label diisi dari teks naskah (`_teks/`),
konteks di TSV, dan baseline Oktober fid=81.

## Hasil hitung (43 baris, 0 kosong, 0 ragu)

| Naskah | bab | subbab | paragraf | biasa | total |
|---|---|---|---|---|---|
| fid=81 | 0 | 0 | 12 | 9 | 21 |
| fid=112 | 1 | 0 | 1 | 8 | 10 |
| fid=115 | 1 | 1 | 1 | 6 | 9 |
| WULAN-1 | 0 | 0 | 1 | 2 | 3 |
| **Total** | **2** | **1** | **15** | **25** | **43** |

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
   aturan di atas, tapi 6 baris keyakinan sedang (di bawah) mohon Boss
   periksa ulang.

## Keyakinan sedang (6 baris fid=81, mohon Boss periksa ulang)

Konteks di TSV terpotong, jadi keputusan memakai aturan ganti topik,
bukan bukti jeda paragraf yang terlihat langsung:

- 81 no 4: `biasa` — definisi Keberlanjutan Usaha kedua, topik sama.
- 81 no 8: `biasa` — definisi Digital Marketing kedua, topik sama.
- 81 no 11: `paragraf` — studi terdahulu berbeda (Clarissa et al.),
  pola kalimat pembuka paragraf.
- 81 no 12: `biasa` — penjelasan sesudah rumus, lanjutan paragraf sampel.
- 81 no 13: `biasa` — kalimat sitasi lanjutan, topik sama (uji asumsi).
- 81 no 17: `biasa` — kalimat koefisien kedua, topik sama.

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

Diukur dari label Wulan ini: **1.13 benar 8/21, 1.14 benar 13/21.**
Artinya pada subset sengketa ini 1.14 lebih baik, dan itu BERTENTANGAN
dengan vonis lama yang memakai jarak ke baseline Oktober (paragraf 157).

Penjelasan yang jujur: baseline 157 berasal dari pipeline Oktober yang
lebih tua (sebelum perbaikan stitch dan pemisah v5-v7), jadi jarak ke
157 bukan ukuran yang adil untuk kode v7. Label kebenaran dasar inilah
yang seharusnya menjadi wasit, bukan baseline lama. Bila label Wulan
benar, jumlah paragraf sejati fid=81 lebih dekat ke ~185 daripada 157,
dan 1.14 memang lebih sering benar pada baris sengketa.

Tapi Wulan ingatkan: ini hanya 21 baris sengketa, bukan seluruh naskah,
dan 6 di antaranya keyakinan sedang. Vonis pindah model tetap butuh
Boss memeriksa 6 baris itu, plus sengketa paragraf antar-run v7 yang
belum ada di paket ini (butuh Gas ~180 panggilan Jev).

## Verifikasi

- 43/43 baris terisi, 0 kosong, 0 ragu.
- Konsistensi: subbab 115 no 6 berada di bawah 1.4 Manfaat Penelitian,
  BAB I ada di naskah (OK). Kedua BAB terlabel adalah penanda BAB asli.
- Tidak ada label yang ditebak tanpa aturan; tiap baris punya catatan
  sumber di kolom `catatan_boss` (berawalan "Wulan:").
