# Laporan Verifikasi Live v11 (Tahap 5)

Tanggal: 11 November 2026. Cabang: `agen/wulan/optimalkan-jev-hakim-v5`.
Kode: `jev-peta-v11`, model diminta `SATPAM/typesafe/jev-1.14`.
Berkas hasil: `hasil_verifikasi_v11.json` (angka lengkap per naskah).
Pelari kelompok OpenRouter: `_verifikasi_v11/jalankan_verifikasi_v11_or.py`
(prosedur sama dengan pelari 18 pertama, hanya probe yang menerima
`typesafe/jev-1.14-20261014` lewat OpenRouter).

## Vonis gabungan (33 naskah: 18 TypeSafe + 15 OpenRouter)

**v11 TIDAK TERBUKTI menaikkan presisi keseluruhan di naskah uji.**
Sebab sederhana: goyang naik sedikit di kedua kelompok (gabungan 2660 ->
2697, +1,4%) dan label bergerak dalam rentang noise; yang terbukti naik
hanya kebersihan artefak (pemisah/BOM) dan kerapian judul bab.
Langkah berikut: ~60-66 panggilan Jev lagi untuk E3 + AJ-1 bila Boss
menyetujui anggaran tambahan; tanpa itu, vonis di atas sudah didukung
33 dari 36 naskah uji.

Koreksi hitung (11 Nov, sesi OR): arah goyang 18 naskah pertama yang
tertulis di laporan ini sebelumnya ("turun 6, naik 9, datar 3") salah
hitung dari tabelnya sendiri; yang benar dari `hasil_verifikasi_v11.json`
adalah **naik 11, turun 7, datar 0**. Agregat 1411 -> 1414 tidak berubah.

## Cakupan

- Terverifikasi live: **33 dari 36** naskah uji (18 TypeSafe + 15 OpenRouter).
- Kelompok OpenRouter (15, semua berhasil, 0 gagal probe): A4, AA3, AC2,
  AE2, AK-3, AN-1, AO-2, AP-3, C4, D3, G3, M3, N3, S2, W3.
  Tiap run dibuktikan probe: yang melayani
  `typesafe/jev-1.14-20261014`, `satpam_penyedia: openrouter`, jejak
  satpam tiap run mencatat resmi `jev-1.14.0` GAGAL HTTP 402 (kredit
  TypeSafe masih habis) lalu OpenRouter DIPAKAI. Jalur
  `model_override` (butir 5, bila TypeSafe terisi lagi) **tidak pernah
  terpicu (0 kali)** — kredit tidak terisi lagi selama run.
- Belum terverifikasi: **E3 dan AJ-1** (anggaran kelompok OR habis; v10
  30 dan 32 panggilan, dua yang termahal; butuh ~60-66 panggilan lagi
  termasuk probe + hakim).
- **AD3 duplikat berkas Y2** (Y2 sudah terverifikasi di kelompok TypeSafe):
  sengaja tidak dipetakan lagi dan tidak dihitung ganda.
- DB produksi tidak berubah (sidik 28, 108, 235 sebelum dan sesudah tiap
  run; `sidik_berubah: false` di 15/15 run OR; 0 job live jalan/menunggu
  sebelum gelombang OR1).

## Agregat per kelompok (v10 lawan v11)

| Ukuran | TypeSafe 18 | OpenRouter 15 | Gabungan 33 * |
|---|---|---|---|
| Panggilan Jev (petakan) | 299 -> 292 (-2%) | 227 -> 219 (-4%) | 526 -> 511 (-3%) |
| Goyang dalam-run | 1411 -> 1414 (+3) | 1249 -> 1283 (+34) | 2660 -> 2697 (+37) |
| Judul bab sampah | 49 -> 39 (-20%) | 15 -> 11 (-27%) | 64 -> 50 (-22%) |
| Subbab (total) | 1253 -> 1266 | 1068 -> 1041 | 2321 -> 2307 |
| Paragraf (total) | 1985 -> 2041 | 1955 -> 1997 | 3940 -> 4038 |
| Hakim sepakat / ragu / curiga | 1104 / 184 / 5 | 878 / 181 / 5 | 1982 / 365 / 10 |
| Pendapat kedua (Lapis 2) jalan | 0 kali | 0 kali | 0 kali |
| Masuk antrean manusia | 0 dari 18 | 0 dari 15 | 0 dari 33 |

\* Agregat gabungan MENCAMPUR dua ID model (18 naskah dilayani
`jev-1.14.0` resmi + 15 naskah dilayani
`openrouter/typesafe/jev-1.14-20261014`). Bobot fallback belum terbukti
identik dengan jev-1.14.0 resmi, jadi selisih kelompok OR bisa berasal
dari model, bukan dari lapisan v11. Vonis memakai agregat per kelompok;
gabungan hanya ringkasan. Peringatan: kelompok TypeSafe sendiri juga
tidak menunjukkan perbaikan goyang (+3), jadi vonis tidak bergantung
pada kelompok OR.

Arah goyang per naskah: TypeSafe naik 11, turun 7, datar 0; OpenRouter
naik 9, turun 4, datar 2 (AP-3, C4); gabungan naik 20, turun 11, datar 2.

## Per naskah, kelompok TypeSafe 18 (v10 -> v11)

| Kode | Panggilan | Goyang | Bab | Subbab | Paragraf | Bab_semua | Sampah |
|---|---|---|---|---|---|---|---|
| AI-2 | 24->22 | 95->102 | 2->1 | 132->134 | 143->161 | 11->10 | 4->4 |
| AL-2 | 14->12 | 55->38 | ?->1 | 60->62 | 52->57 | 6->7 | 1->2 |
| AM-2 | 14->12 | 114->102 | 4->0 | 32->39 | 157->153 | 9->5 | 0->0 |
| B4 | 38->38 | 170->171 | ?->0 | 160->157 | 188->198 | 5->5 | 0->0 |
| F4 | 10->10 | 61->56 | 10->0 | 46->49 | 103->96 | 20->5 | 0->0 |
| H1 | 40->40 | 167->168 | ?->2 | 219->211 | 187->196 | 8->10 | 2->3 |
| I4 | 13->13 | 42->50 | ?->0 | 42->43 | 58->50 | 7->7 | 0->0 |
| J3 | 8->7 | 32->37 | 11->0 | 44->38 | 80->94 | 22->5 | 0->0 |
| L3 | 25->24 | 58->43 | 10->0 | 91->94 | 122->125 | 20->5 | 0->0 |
| O3 | 20->20 | 67->70 | 4->2 | 50->48 | 71->87 | 15->9 | 10->5 |
| P2 | 13->14 | 59->68 | 1->2 | 56->57 | 58->54 | 7->7 | 2->3 |
| Q3 | 14->14 | 51->60 | ?->0 | 30->32 | 53->51 | 5->5 | 0->0 |
| R3 | 16->16 | 131->140 | 3->1 | 68->71 | 166->185 | 17->12 | 6->6 |
| T3 | 10->10 | 68->85 | 19->9 | 91->89 | 116->116 | 35->11 | 15->6 |
| U3 | 12->12 | 70->55 | 6->0 | 14->15 | 122->126 | 16->7 | 1->1 |
| X3 | 6->6 | 22->19 | 9->0 | 26->26 | 66->51 | 9->5 | 0->0 |
| Y2 | 10->10 | 22->26 | 5->0 | 14->21 | 62->59 | 5->5 | 0->0 |
| Z3 | 12->12 | 127->124 | 8->9 | 78->80 | 181->182 | 23->24 | 8->9 |

Tanda `?` = angka bab tidak tercatat di skema v10 naskah itu (grup 4).
Kolom Bab v11 = label `bab` saja; judul bab deterministik v11 tercatat di
`gabung`, sehingga Bab 0 bukan berarti bab hilang (contoh Y2: 5 judul Romawi
ada di gabung, bersih).

## Per naskah, kelompok OpenRouter 15 (v10 -> v11)

Model yang melayani di semua 15 run: `typesafe/jev-1.14-20261014`
(OpenRouter). Kolom Bab = label `bab` saja, sama seperti tabel di atas.

| Kode | Panggilan | Goyang | Bab | Subbab | Paragraf | Bab_semua | Sampah |
|---|---|---|---|---|---|---|---|
| A4 | 7->7 | 28->30 | 6->0 | 72->63 | 63->65 | 13->9 | 0->0 |
| AA3 | 12->12 | 86->84 | 4->4 | 45->45 | 85->92 | 8->8 | 2->2 |
| AC2 | 8->8 | 51->56 | 7->5 | 46->44 | 74->84 | 11->10 | 0->0 |
| AE2 | 23->23 | 131->122 | 2->0 | 69->70 | 169->156 | 6->5 | 0->0 |
| AK-3 | 14->12 | 57->75 | ?->0 | 54->54 | 121->121 | 6->6 | 0->0 |
| AN-1 | 12->10 | 61->75 | 6->9 | 30->27 | 115->132 | 11->14 | 3->3 |
| AO-2 | 14->12 | 86->89 | ?->0 | 27->28 | 118->117 | 5->5 | 0->0 |
| AP-3 | 13->11 | 56->56 | ?->0 | 57->55 | 90->94 | 5->5 | 0->0 |
| C4 | 13->13 | 72->72 | 9->0 | 68->66 | 145->137 | 18->5 | 0->0 |
| D3 | 26->26 | 119->115 | 10->0 | 61->59 | 214->222 | 20->5 | 0->0 |
| G3 | 10->10 | 73->81 | 4->4 | 51->48 | 149->152 | 13->14 | 8->4 |
| M3 | 12->12 | 108->115 | 10->0 | 154->137 | 193->205 | 20->5 | 0->0 |
| N3 | 16->16 | 55->67 | 1->1 | 128->129 | 51->50 | 8->7 | 1->1 |
| S2 | 26->26 | 71->75 | 10->0 | 78->80 | 127->130 | 20->5 | 0->0 |
| W3 | 21->21 | 195->171 | ?->1 | 128->136 | 241->240 | 5->6 | 1->1 |

Catatan per naskah OR: C4/D3/M3/S2 bab_semua 18-20 -> 5 (judul ganda
akibat BOM runtuh, seperti F4/J3/L3 di kelompok TypeSafe). AN-1
bab_semua 11 -> 14 (bertambah: duplikat daftar isi `Bab I : PENDAHULUAN`
dan kawan-kawan masuk gabung). W3 bab_semua 5 -> 6 (tambah label bab
`Tinjauan Pustaka`, judul BAB II tanpa awalan BAB). A4: BAB I isi tidak
ada di gabung v11 (hanya `Bab I` daftar isi) — sama seperti v10 yang
juga tidak punya judul BAB I isi; bukan regresi v11.

## 4 klaim v11 (diperbarui dengan kelompok OR)

### (a) Naskah Romawi tanpa kata BAB: TERBUKTI SEBAGIAN, kini 3 kasus

Y2 (TypeSafe): v10 ternyata sudah mendeteksi 5 judul Romawi sebagai bab
(bukan 0 seperti dugaan tahap 4). v11 tetap 5, kini deterministik di
`gabung` tanpa Jev, dan BOM di judul pertama terkelupas
(`I. PENDAHULUAN` bersih). Y2 tetap satu-satunya kasus Romawi-tanpa-BAB
yang deterministik.

W3 (OR, profil `romawi` — memakai kata BAB, bukan romawi-tanpa-bab):
gabung v11 memuat 5 judul BAB utuh (BAB I-V) sama seperti v10; label bab
Jev tambah 1 (`Tinjauan Pustaka`). Goyang turun 195 -> 171, satu-satunya
penurunan goyang besar di kelompok OR.

AA3 (OR): 8 bab_semua di v10 maupun v11; 4 judul Romawi tanpa kata BAB
tetap dilabel bab, TAPI 1 dari 4 berganti (v10: `III. KOMISI PERTANIAN
DAN PANGAN`; v11: `IV. KOMISI TRANSPORTASI DAN INFRASTRUKTUR`) — label
Romawi goyang antar versi, bukan stabil. `BAB II` dan `BAB III` tanpa
judul masih sampah di kedua versi.

### (b) Naskah CHAPTER Inggris: TERBUKTI SEBAGIAN, belum bersih, tanpa kasus baru

T3: judul bab 35 -> 11, sampah 15 -> 6. Lima judul isi kini tergabung bersih
di `gabung` (`CHAPTER I INTRODUCTION` dan seterusnya, tanpa BOM, tanpa
pecah `CHAPTER I` + `INTRODUCTION` seperti di v10). Sisa: 5 duplikat halaman
daftar isi (`CHAPTER I: INTRODUCTION` dan kawan-kawan) + `TABLE OF CONTENS`
masih dilabel `bab` oleh Jev. T3 satu-satunya naskah CHAPTER di daftar uji;
tidak ada naskah CHAPTER di kelompok OR.

### (c) Artefak pemisah/BOM: TERBUKTI PENUH (33/33)

0 baris pemisah dilabel bab, 0 karakter BOM tersisa di baris maupun gabung,
di 18 naskah TypeSafe maupun 15 naskah OR (A4 bom profil 3, AC2 4, C4 5,
D3 5, M3 5, S2 5, AE2 1 — semuanya bersih di baris hasil). Judul ganda
akibat BOM runtuh: F4 20 -> 5, J3 22 -> 5, L3 20 -> 5, U3 16 -> 7, X3 9 -> 5
(TypeSafe); C4 18 -> 5, D3 20 -> 5, M3 20 -> 5, S2 20 -> 5 (OpenRouter).

### (d) Antrean manusia: TIDAK TERUJI live

0 dari 33 naskah uji masuk antrean. Aturan antrean hanya teruji offline.
Hakim curiga 5 kali di kelompok OR (W3 2 butir-bertanya, S2 2
nomor-loncat, AE2 1 awal-sitasi), semuanya log saja, tanpa antrean.

## Yang tidak naik

- Goyang: gabungan 2660 -> 2697 (+1,4%); naik di kedua kelompok
  (TypeSafe +3, OpenRouter +34). Turun hanya di 11 dari 33 naskah
  (terbesar W3 -24, AE2 -9); naik di 20, datar di 2.
- Panggilan: gabungan 526 -> 511, hanya -3%.
- Label subbab/paragraf bergerak dua arah dalam rentang noise; tidak ada arah
  sistematis (gabungan subbab 2321 -> 2307, paragraf 3940 -> 4038).
  Perbandingan per baris (grup 3 OR: W3, AA3, AE2, AC2) didominasi geser
  indeks akibat stitch dan tukar paragraf/biasa (W3 415, AA3 195, AE2 71,
  AC2 57), bukan perbaikan searah.
- Judul bab sampah masih 50, tersebar di 14 dari 33 naskah (terbesar Z3 9,
  R3 6, T3 6, O3 5, G3 4, AI-2 4, AN-1 3, H1 3, P2 3, AA3 2, AL-2 2,
  U3 1, W3 1, N3 1). Sumber terbesar: fragmen daftar isi berawalan `:`,
  `BAB` tanpa judul, deskripsi sistematika, dan nomor halaman daftar isi
  (`????...`).
- Lapis 2 (`pendapat_kedua`): 0 kali jalan di 33 run live, jadi tidak teruji
  live sama sekali (pelari tidak menyuntikkan jawaban kedua).

## Skor teks lawan label manusia: TIDAK MUNGKIN

`ground_truth_latih112.tsv` berisi 254 baris dari 63 naskah LATIH dan 0 baris
dari 36 naskah UJI, sesuai rancangan tahap 3 (tanpa kebocoran). Vonis di atas
memakai agregat + cek deterministik, bukan skor presisi lawan label manusia.

## Anggaran dan biaya

Sesi kelompok OpenRouter ini: **252 panggilan Jev** (2 probe awal +
OR1 38 + OR2 57 + OR3 74 + OR4 81; gelombang OR1-OR4 sendiri 250,
tepat di batas ~250, lewat 2 karena 2 probe awal). Rincian per gelombang:
petakan 219, hakim 16, probe 15. Perkiraan biaya sesi ini **~Rp2.520**
(rentang Rp1.814-Rp2.520; metode jangkar `ukur_biaya_3_naskah`: ~Rp10
per panggilan, batas atas chars/4, $0,042/1 juta token, kurs
Rp18.100/USD, output gratis; Jev tidak mengembalikan pemakaian token).

Tahap 5 keseluruhan: **660 panggilan** (408 sesi 18 pertama + 252 sesi
OR), perkiraan biaya **~Rp6.600**.

## Pemblokir dan pilihan lanjut

TypeSafe resmi: HTTP 402 "Your organization has no available TypeSafe API
credits" sejak gelombang C2 (~04:15 WIB), dikonfirmasi MASIH 402 di
setiap probe kelompok OR (jejak satpam tiap run). Kredit tidak terisi
lagi selama run, jadi butir 5 (tetap pakai fallback OpenRouter bila
kredit terisi) tidak pernah terpicu — kelompok OR seluruhnya dilayani
satu ID model, `openrouter/typesafe/jev-1.14-20261014`.

Sisa: **E3 dan AJ-1** belum terverifikasi karena anggaran kelompok OR
habis (bukan karena probe gagal). Butuh ~60-66 panggilan Jev lagi
(petakan v10 30+32, ditambah probe + hakim). Pilihan: (1) Boss
menyetujui anggaran tambahan ~65 panggilan, lalu jalankan E3 + AJ-1
dengan pelari OR yang sama; (2) isi ulang kredit TypeSafe dan jalankan
keduanya dengan probe `jev-1.14.0` — tapi hasilnya lalu tidak sekelompok
dengan 15 naskah OR; (3) terima vonis 33 naskah sebagai cukup dan
tutup tahap 5.
