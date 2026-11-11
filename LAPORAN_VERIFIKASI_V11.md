# Laporan Verifikasi Live v11 (Tahap 5)

Tanggal: 11 November 2026. Cabang: `agen/wulan/optimalkan-jev-hakim-v5`.
Kode: `jev-peta-v11`, model `jev-1.14.0` (bukti probe tiap run).
Berkas hasil: `hasil_verifikasi_v11.json` (angka lengkap per naskah).

## Vonis

**v11 TIDAK TERBUKTI menaikkan presisi keseluruhan di naskah uji.**
Sebab sederhana: goyang tidak turun dan label bergerak dalam rentang noise,
yang terbukti naik hanya kebersihan artefak (pemisah/BOM) dan kerapian judul bab.
Langkah berikut: isi ulang kredit TypeSafe, lalu verifikasi 18 naskah sisa
dengan probe yang sama sebelum memutuskan pilot.

## Cakupan

- Terverifikasi live: **18 dari 36** naskah uji.
- Gagal probe: **12 naskah** (W3, AA3, AE2, AC2, AK-3, AO-2, AN-1, D3, E3, S2,
  C4, M3) — penyedia resmi TypeSafe mengembalikan HTTP 402 kredit habis,
  satpam jatuh ke OpenRouter (`typesafe/jev-1.14-20261014`), probe menolak
  karena bukan `jev-1.14.0` persis. 24 panggilan probe terbuang, 0 petakan.
- Belum dicoba: **6 naskah** (AD3 duplikat berkas Y2, AJ-1, A4, G3, N3, AP-3).
- DB produksi tidak berubah (sidik 28, 108, 235 sebelum dan sesudah tiap run).

## Agregat 18 naskah (v10 lawan v11)

| Ukuran | v10 | v11 |
|---|---|---|
| Panggilan Jev | 299 | 292 (-2%) |
| Goyang dalam-run | 1411 | 1414 (identik) |
| Judul bab sampah | 49 | 39 (-20%) |
| Hakim sepakat / ragu / curiga | - | 1104 / 184 / 5 |
| Pendapat kedua (Lapis 2) jalan | - | 0 kali |
| Masuk antrean manusia | - | 0 dari 18 |

## Per naskah (v10 -> v11)

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

## 4 klaim v11

### (a) Naskah Romawi tanpa kata BAB: TERBUKTI SEBAGIAN, premis awal salah

Y2: v10 ternyata sudah mendeteksi 5 judul Romawi sebagai bab (bukan 0 seperti
dugaan tahap 4). v11 tetap 5, kini deterministik di `gabung` tanpa Jev, dan
BOM di judul pertama terkelupas (`I. PENDAHULUAN` bersih). Hanya 1 kasus
Romawi independen yang terverifikasi live; W3 (5 judul) dan AA3 (8 judul)
terblokir 402.

### (b) Naskah CHAPTER Inggris: TERBUKTI SEBAGIAN, belum bersih

T3: judul bab 35 -> 11, sampah 15 -> 6. Lima judul isi kini tergabung bersih
di `gabung` (`CHAPTER I INTRODUCTION` dan seterusnya, tanpa BOM, tanpa
pecah `CHAPTER I` + `INTRODUCTION` seperti di v10). Sisa: 5 duplikat halaman
daftar isi (`CHAPTER I: INTRODUCTION` dan kawan-kawan) + `TABLE OF CONTENS`
masih dilabel `bab` oleh Jev. T3 satu-satunya naskah CHAPTER di daftar uji.

### (c) Artefak pemisah/BOM: TERBUKTI PENUH (18/18)

0 baris pemisah dilabel bab, 0 karakter BOM tersisa di baris maupun gabung.
Judul ganda akibat BOM runtuh: F4 20 -> 5, J3 22 -> 5, L3 20 -> 5,
U3 16 -> 7, X3 9 -> 5 judul bab.

### (d) Antrean manusia: TIDAK TERUJI live

0 dari 18 naskah uji masuk antrean. Aturan antrean hanya teruji offline.

## Yang tidak naik

- Goyang: 1411 -> 1414, identik. Turun di 6 naskah, naik di 9, datar di 3.
- Panggilan: 299 -> 292, hanya -2%.
- Label subbab/paragraf bergerak dua arah dalam rentang noise; tidak ada arah
  sistematis. Perbandingan per baris (grup 3: X3, Y2, Z3) didominasi geser
  indeks akibat stitch dan tukar paragraf/biasa (X3 30, Y2 18, Z3 54),
  bukan perbaikan searah.
- Judul bab sampah masih 39, tersebar di 8 dari 18 naskah (Z3 9, R3 6, T3 6,
  O3 5, AI-2 4, H1 3, P2 3, AL-2 2). Sumber terbesar: fragmen daftar isi
  berawalan `:`, `BAB` tanpa judul, deskripsi sistematika, dan nomor halaman
  daftar isi (`????...`).
- Lapis 2 (`pendapat_kedua`): 0 kali jalan di 18 run live, jadi tidak teruji
  live sama sekali (pelari tidak menyuntikkan jawaban kedua).

## Skor teks lawan label manusia: TIDAK MUNGKIN

`ground_truth_latih112.tsv` berisi 254 baris dari 63 naskah LATIH dan 0 baris
dari 36 naskah UJI, sesuai rancangan tahap 3 (tanpa kebocoran). Vonis di atas
memakai agregat + cek deterministik, bukan skor presisi lawan label manusia.

## Anggaran dan biaya

Total panggilan tahap 5 sesi ini: **408 dari batas ~600** (sisa 192 tidak
terpakai karena pemblokir 402, bukan karena anggaran habis). Rincian: pilot
12, gelombang gagal sebelum perbaikan pelari ~28, smoke test 12, gelombang
A 164, gelombang B 166, gelombang C2 gagal probe 24, konfirmasi C3 2.
Perkiraan biaya **Rp3.000-Rp4.100** (metode jangkar `ukur_biaya_3_naskah`:
~Rp10 per panggilan, batas atas chars/4, $0,042/1 juta token, kurs
Rp18.100/USD, output gratis; Jev tidak mengembalikan pemakaian token).

## Pemblokir dan pilihan lanjut

TypeSafe resmi: HTTP 402 "Your organization has no available TypeSafe API
credits" sejak gelombang C2 (~04:15 WIB), dikonfirmasi masih 402 pada
percobaan ulang AC2. Pilihan: (1) isi ulang kredit TypeSafe, lalu jalankan
18 naskah sisa dengan probe `jev-1.14.0` yang sama; (2) Boss menyetujui
fallback OpenRouter `typesafe/jev-1.14-20261014` sebagai setara 1.14
(keputusan eksplisit; bobot belum terbukti identik, dan hasil campuran dua
ID model akan mengotori perbandingan v10 lawan v11).
