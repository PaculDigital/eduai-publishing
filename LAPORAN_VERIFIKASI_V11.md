# Laporan Verifikasi Live v11 (Tahap 5)

Tanggal: 11 November 2026. Cabang: `agen/wulan/optimalkan-jev-hakim-v5`.
Kode: `jev-peta-v11`, model diminta `SATPAM/typesafe/jev-1.14`.
Berkas hasil: `hasil_verifikasi_v11.json` (angka lengkap per naskah).
Pelari kelompok OpenRouter: `_verifikasi_v11/jalankan_verifikasi_v11_or.py`
(prosedur sama dengan pelari 18 pertama, hanya probe yang menerima
`typesafe/jev-1.14-20261014` lewat OpenRouter).

## Vonis gabungan (35 naskah: 18 TypeSafe + 17 OpenRouter)

**v11 TIDAK TERBUKTI menaikkan presisi keseluruhan di naskah uji.**
Sebab sederhana: goyang naik sedikit di kedua kelompok (gabungan 2864 ->
2907, +1,5%) dan label bergerak dalam rentang noise; yang terbukti naik
hanya kebersihan artefak (pemisah/BOM) dan kerapian judul bab.
Gelombang OR5 (11 Nov, Gas Boss): E3 + AJ-1 terverifikasi (64 panggilan),
tahap 5 kini **35 dari 36** naskah uji; 1 sisanya AD3 duplikat berkas Y2,
sengaja tidak dihitung ganda. Vonis 33 naskah sebelumnya dipertahankan
dan diperbarui ke 35 di bawah ini; angka 33 naskah tidak diubah.

Koreksi hitung (11 Nov, sesi OR): arah goyang 18 naskah pertama yang
tertulis di laporan ini sebelumnya ("turun 6, naik 9, datar 3") salah
hitung dari tabelnya sendiri; yang benar dari `hasil_verifikasi_v11.json`
adalah **naik 11, turun 7, datar 0**. Agregat 1411 -> 1414 tidak berubah.

## Cakupan

- Terverifikasi live: **35 dari 36** naskah uji (18 TypeSafe + 17 OpenRouter).
- Kelompok OpenRouter (17, semua berhasil, 0 gagal probe): A4, AA3, AC2,
  AE2, AJ-1, AK-3, AN-1, AO-2, AP-3, C4, D3, E3, G3, M3, N3, S2, W3.
  Tiap run dibuktikan probe: yang melayani
  `typesafe/jev-1.14-20261014`, `satpam_penyedia: openrouter`, jejak
  satpam tiap run mencatat resmi `jev-1.14.0` GAGAL HTTP 402 (kredit
  TypeSafe masih habis) lalu OpenRouter DIPAKAI. Jalur
  `model_override` (butir 5, bila TypeSafe terisi lagi) **tidak pernah
  terpicu (0 kali)** — kredit tidak terisi lagi selama run.
  Gelombang OR5 (E3 + AJ-1): 64 panggilan (petakan 60, hakim 2, probe 2),
  pelari `_verifikasi_v11/jalankan_verifikasi_v11_or.py` yang sama,
  tag OR5.
- Belum terverifikasi: **tidak ada lagi** — E3 dan AJ-1 terverifikasi di
  OR5 (Gas Boss 11 Nov 2026).
- **AD3 duplikat berkas Y2** (Y2 sudah terverifikasi di kelompok TypeSafe):
  sengaja tidak dipetakan lagi dan tidak dihitung ganda.
- DB produksi tidak berubah (sidik 28, 108, 235 sebelum dan sesudah tiap
  run; `sidik_berubah: false` di 17/17 run OR; 0 job live jalan/menunggu
  sebelum gelombang OR1).

## Agregat per kelompok (v10 lawan v11)

| Ukuran | TypeSafe 18 | OpenRouter 17 | Gabungan 35 * |
|---|---|---|---|
| Panggilan Jev (petakan) | 299 -> 292 (-2%) | 289 -> 279 (-3%) | 588 -> 571 (-3%) |
| Goyang dalam-run | 1411 -> 1414 (+3) | 1453 -> 1493 (+40) | 2864 -> 2907 (+43) |
| Judul bab sampah | 49 -> 39 (-20%) | 15 -> 12 (-20%) | 64 -> 51 (-20%) |
| Subbab (total) | 1253 -> 1266 | 1187 -> 1155 | 2440 -> 2421 |
| Paragraf (total) | 1985 -> 2041 | 2197 -> 2240 | 4182 -> 4281 |
| Hakim sepakat / ragu / curiga | 1104 / 184 / 5 | 977 / 196 / 5 | 2081 / 380 / 10 |
| Pendapat kedua (Lapis 2) jalan | 0 kali | 0 kali | 0 kali |
| Masuk antrean manusia | 0 dari 18 | 0 dari 17 | 0 dari 35 |

\* Agregat gabungan MENCAMPUR dua ID model (18 naskah dilayani
`jev-1.14.0` resmi + 17 naskah dilayani
`openrouter/typesafe/jev-1.14-20261014`). Bobot fallback belum terbukti
identik dengan jev-1.14.0 resmi, jadi selisih kelompok OR bisa berasal
dari model, bukan dari lapisan v11. Vonis memakai agregat per kelompok;
gabungan hanya ringkasan. Peringatan: kelompok TypeSafe sendiri juga
tidak menunjukkan perbaikan goyang (+3), jadi vonis tidak bergantung
pada kelompok OR.

Arah goyang per naskah: TypeSafe naik 11, turun 7, datar 0; OpenRouter
naik 10, turun 5, datar 2 (AP-3, C4); gabungan naik 21, turun 12, datar 2.
Dua naskah OR5: AJ-1 goyang turun 5 (115 -> 110), E3 naik 11 (89 -> 100).

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

## Per naskah, kelompok OpenRouter 17 (v10 -> v11)

Model yang melayani di semua 17 run: `typesafe/jev-1.14-20261014`
(OpenRouter). Kolom Bab = label `bab` saja, sama seperti tabel di atas.
Dua baris terakhir (AJ-1, E3) adalah gelombang OR5.

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
| AJ-1 | 32->30 | 115->110 | 2->4 | 73->70 | 109->102 | 7->11 | 0->1 |
| E3 | 30->30 | 89->100 | 10->0 | 46->44 | 133->141 | 20->5 | 0->0 |

Catatan per naskah OR: C4/D3/M3/S2 bab_semua 18-20 -> 5 (judul ganda
akibat BOM runtuh, seperti F4/J3/L3 di kelompok TypeSafe). AN-1
bab_semua 11 -> 14 (bertambah: duplikat daftar isi `Bab I : PENDAHULUAN`
dan kawan-kawan masuk gabung). W3 bab_semua 5 -> 6 (tambah label bab
`Tinjauan Pustaka`, judul BAB II tanpa awalan BAB). A4: BAB I isi tidak
ada di gabung v11 (hanya `Bab I` daftar isi) — sama seperti v10 yang
juga tidak punya judul BAB I isi; bukan regresi v11.
**OR5:** E3 bab_semua 20 -> 5 (tepat 5 judul bersih BAB I-V lewat gabung;
v10 20 entri berantakan: fragmen ber-BOM, judul telanjang, duplikat).
AJ-1 bab_semua 7 -> 11: v11 menambah 1 sampah baru (`: Hasil dan
Pembahasan`, fragmen titik-dua dilabel `bab` oleh Jev) plus entri gabung
telanjang `Bab 4`/`Bab 5` yang tidak dihitung pengklasifikasi sampah.

## 4 klaim v11 (diperbarui dengan kelompok OR)

### (a) Naskah Romawi tanpa kata BAB: TERBUKTI SEBAGIAN, kini 4 kasus

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

E3 (OR5, profil `romawi` — BAB+Romawi, bukan romawi-tanpa-bab):
bab_semua v10 20 entri berantakan (fragmen ber-BOM, judul telanjang
tanpa nomor, duplikat) menjadi v11 tepat 5 judul bersih (BAB I
PENDAHULUAN s.d. BAB V PENUTUP) lewat gabung deterministik; label `bab`
Jev 10 -> 0, semua judul bab kini dari gabung. Profil BOM 5, 0 tersisa
di baris maupun gabung.

### (b) Naskah CHAPTER Inggris: TERBUKTI SEBAGIAN, belum bersih, tanpa kasus baru

T3: judul bab 35 -> 11, sampah 15 -> 6. Lima judul isi kini tergabung bersih
di `gabung` (`CHAPTER I INTRODUCTION` dan seterusnya, tanpa BOM, tanpa
pecah `CHAPTER I` + `INTRODUCTION` seperti di v10). Sisa: 5 duplikat halaman
daftar isi (`CHAPTER I: INTRODUCTION` dan kawan-kawan) + `TABLE OF CONTENS`
masih dilabel `bab` oleh Jev. T3 satu-satunya naskah CHAPTER di daftar uji;
tidak ada naskah CHAPTER di kelompok OR.

### (c) Artefak pemisah/BOM: TERBUKTI PENUH (35/35)

0 baris pemisah dilabel bab, 0 karakter BOM tersisa di baris maupun gabung,
di 18 naskah TypeSafe maupun 17 naskah OR (A4 bom profil 3, AC2 4, C4 5,
D3 5, M3 5, S2 5, AE2 1, E3 5 — semuanya bersih di baris hasil; AJ-1 1
baris pemisah, 0 dilabel bab). Judul ganda akibat BOM runtuh: F4 20 -> 5,
J3 22 -> 5, L3 20 -> 5, U3 16 -> 7, X3 9 -> 5 (TypeSafe); C4 18 -> 5,
D3 20 -> 5, M3 20 -> 5, S2 20 -> 5, E3 20 entri berantakan -> 5 judul
bersih (OpenRouter).

### (d) Antrean manusia: TIDAK TERUJI live

0 dari 35 naskah uji masuk antrean. Aturan antrean hanya teruji offline.
Hakim curiga 5 kali di kelompok OR (W3 2 butir-bertanya, S2 2
nomor-loncat, AE2 1 awal-sitasi), semuanya log saja, tanpa antrean.
E3 dan AJ-1: 0 curiga.

## Yang tidak naik

- Goyang: gabungan 2864 -> 2907 (+1,5%); naik di kedua kelompok
  (TypeSafe +3, OpenRouter +40). Turun hanya di 12 dari 35 naskah
  (terbesar W3 -24, AE2 -9, AJ-1 -5); naik di 21, datar di 2.
- Panggilan: gabungan 588 -> 571, hanya -3%.
- Label subbab/paragraf bergerak dua arah dalam rentang noise; tidak ada arah
  sistematis (gabungan subbab 2440 -> 2421, paragraf 4182 -> 4281).
  Perbandingan per baris (grup 3 OR: W3, AA3, AE2, AC2) didominasi geser
  indeks akibat stitch dan tukar paragraf/biasa (W3 415, AA3 195, AE2 71,
  AC2 57), bukan perbaikan searah.
- Judul bab sampah masih 51, tersebar di 15 dari 35 naskah (terbesar Z3 9,
  R3 6, T3 6, O3 5, AI-2 4, G3 4, H1 3, P2 3, AN-1 3, AA3 2, AL-2 2,
  AJ-1 1, N3 1, U3 1, W3 1). Sumber terbesar: fragmen daftar isi berawalan `:`,
  `BAB` tanpa judul, deskripsi sistematika, dan nomor halaman daftar isi
  (`????...`). Catatan jujur: v11 menambah 1 sampah baru di AJ-1
  (`: Hasil dan Pembahasan`) plus entri gabung telanjang `Bab 4`/`Bab 5`
  yang tidak dihitung pengklasifikasi sampah.
- Lapis 2 (`pendapat_kedua`): 0 kali jalan di 35 run live, jadi tidak teruji
  live sama sekali (pelari tidak menyuntikkan jawaban kedua).

## Skor teks lawan label manusia: TIDAK MUNGKIN

`ground_truth_latih112.tsv` berisi 254 baris dari 63 naskah LATIH dan 0 baris
dari 36 naskah UJI, sesuai rancangan tahap 3 (tanpa kebocoran). Vonis di atas
memakai agregat + cek deterministik, bukan skor presisi lawan label manusia.

## Anggaran dan biaya

Sesi kelompok OpenRouter ini: **316 panggilan Jev** (2 probe awal +
OR1 38 + OR2 57 + OR3 74 + OR4 81 + OR5 64; gelombang OR1-OR4 sendiri
250, ditambah OR5 64 untuk E3 + AJ-1). Rincian per gelombang: petakan
279, hakim 18, probe 17. Perkiraan biaya sesi ini **~Rp3.160**
(rentang Rp2.275-Rp3.160; metode jangkar `ukur_biaya_3_naskah`: ~Rp10
per panggilan, batas atas chars/4, $0,042/1 juta token, kurs
Rp18.100/USD, output gratis; Jev tidak mengembalikan pemakaian token).

Tahap 5 keseluruhan: **724 panggilan** (408 sesi 18 pertama + 316 sesi
OR), perkiraan biaya **~Rp7.240**.

## Pemblokir dan pilihan lanjut

TypeSafe resmi: HTTP 402 "Your organization has no available TypeSafe API
credits" sejak gelombang C2 (~04:15 WIB), dikonfirmasi MASIH 402 di
setiap probe kelompok OR (jejak satpam tiap run). Kredit tidak terisi
lagi selama run, jadi butir 5 (tetap pakai fallback OpenRouter bila
kredit terisi) tidak pernah terpicu — kelompok OR seluruhnya dilayani
satu ID model, `openrouter/typesafe/jev-1.14-20261014`.

Sisa: **tidak ada lagi** — E3 dan AJ-1 terverifikasi di gelombang OR5
(64 panggilan, Gas Boss 11 Nov 2026), tahap 5 kini 35 dari 36 naskah
uji; 1 sisanya AD3 duplikat berkas Y2, sengaja tidak dihitung ganda.
TypeSafe resmi masih 402 di setiap probe OR5; jalur `model_override`
tetap tidak pernah terpicu.

## Pelabelan naskah uji dan skor presisi (11 Nov 2026, Gas Boss)

279 baris sengketa di 35 naskah uji dilabeli manusia (0 ragu, 0 panggilan
Jev): `ground_truth/ground_truth_uji112.tsv` + `ringkasan_uji112.md`.
Label benar: biasa 138, paragraf 75, subbab 45, bab 21.

Akurasi v11 pada baris sengketa saja (bukan presisi keseluruhan peta):
136/279 (0,4875). Per label: subbab 32/45 (0,7111), paragraf 43/75
(0,5733), bab 12/21 (0,5714), biasa 49/138 (0,3551). Per kelompok:
TypeSafe 76/144 (0,5278), OpenRouter 60/135 (0,4444). Per bentuk:
Romawi 120/247 (0,4858), CHAPTER 2/8, Arab 3/8, campuran 11/16.

Head-to-head adil (subset ketat, 56 baris, 7 naskah grup 3 — satu-satunya
yang label v10 per barisnya tersimpan): v10 22/56 (0,3929) lawan v11
29/56 (0,5179). Pasangan berselisih 21 lawan 14, McNemar khi-kuadrat 1,4,
p sekitar 0,24, tidak signifikan. **Vonis: v11 TIDAK TERBUKTI lebih
presisi dari v10.** Arahnya menguntungkan v11 di bab dan paragraf, turun
tipis di biasa pada subset ketat. Subset luas (84 baris, + cocok persis
judul bab v10): v10 27/84 lawan v11 34/84, tapi bias karena diperkaya
judul sampah, bukan vonis.

Pola salah terbesar v11: 42 baris biasa dilabeli bab (kebanyakan salinan
sistematika/daftar isi). 8 baris bab asli tanpa label di `label_penuh`
v11, tapi kedelapan judulnya ada di `bab_gabung` v11 (celah representasi
per baris, bukan bab hilang). 20 sengketa bab tidak terlabeli (batas
8/naskah: Z3 12, T3 4, R3 1, AI-2 1, O3 1, AA3 1).
Skor lengkap di kunci `skor_presisi_uji112` dan `vonis_presisi_uji112`
pada `hasil_verifikasi_v11.json` (angka 35 naskah tidak berubah).
