# Ringkasan Paket Label Uji 112 Naskah — Tahap 5 (Presisi v11)

Tanggal: 11 November 2026. Branch `agen/wulan/optimalkan-jev-hakim-v5`.
**Nol panggilan Jev** — semua label dibaca dari teks sumber dan hasil run
tersimpan tahap 1 (v10) dan tahap 5 (v11). Skrip gabung + skor:
`_sketsa/gabung_label_uji.py`. Pelabelan per kelompok:
`_sketsa/label_uji_typesafe.tsv` (144) dan `_sketsa/label_uji_openrouter.tsv`
(135).

## Vonis di depan

**v11 TIDAK TERBUKTI lebih presisi dari v10 di naskah uji.** Pada satu-satunya
perbandingan head-to-head yang adil (56 baris, 7 naskah grup 3), v11 benar
29 lawan v10 benar 22, tapi pasangan yang berselisih 21 lawan 14 masih di
dalam noise (McNemar khi-kuadrat 1,4, p sekitar 0,24). Arahnya menguntungkan
v11 di bab dan paragraf, tapi sampelnya terlalu kecil untuk membuktikan.
Kemenangan kebersihan v11 (pemisah/BOM 35/35, judul sampah 64 jadi 51)
tetap berdiri sendiri dan tidak ikut diukur di sini.

## Isi

| Berkas | Isi |
|---|---|
| `ground_truth_uji112.tsv` | 279 baris sengketa, **semua sudah berlabel, 0 ragu** |
| `ringkasan_uji112.json` | Hitungan + skor (mesin) |
| `ringkasan_uji112.md` | Berkas ini |

## Distribusi label (279 baris)

| Label benar | Jumlah |
|---|---|
| biasa | 138 |
| paragraf | 75 |
| subbab | 45 |
| bab | 21 |
| ragu | 0 |

Per jenis sengketa: goyang_subbab 87, goyang_bab 43, judul_bab_sampah 35,
goyang_paragraf_biasa 48 (24 + 24), hakim_ragu 21, beda_bab 21, hakim_curiga
10, beda_paragraf_biasa 7, beda_subbab 6, deterministik_nomor_polos 1.
Per kelompok: TypeSafe 144, OpenRouter 135. Per naskah: 8 baris, kecuali
S2 7 baris.

## Skor v11 pada baris sengketa (bukan presisi keseluruhan)

279 baris ini HANYA baris sulit yang diperselisihkan; baris yang kedua
versi sudah sepakat tidak dilabeli. Jadi angka di bawah adalah akurasi
pada baris sulit, bukan presisi keseluruhan peta (yang pasti lebih tinggi,
tapi tidak bisa dihitung dari paket ini).

| Ukuran | v11 benar / n | Akurasi |
|---|---|---|
| Keseluruhan | 136 / 279 | 0,4875 |
| Berlabel saja (8 baris tanpa label v11 dikeluarkan) | 136 / 271 | 0,5018 |
| TypeSafe (144) | 76 | 0,5278 |
| OpenRouter (135) | 60 | 0,4444 |
| Romawi (247) | 120 | 0,4858 |
| CHAPTER, T3 saja (8) | 2 | 0,25 |
| Arab, AJ-1 saja (8) | 3 | 0,375 |
| Campuran, B4 + AO-2 (16) | 11 | 0,6875 |

Per label benar (v11): bab 12/21 (0,5714), subbab 32/45 (0,7111),
paragraf 43/75 (0,5733), biasa 49/138 (0,3551). Subbab paling kuat,
biasa paling lemah.

Per naskah (v11 benar / 8, kecuali S2 / 7): Q3 7, B4 6, F4 6, L3 6,
AL-2 5, AO-2 5, I4 5, J3 5, M3 5, Y2 5, Z3 5, A4 4, AA3 4, AE2 4, AM-2 4,
AN-1 4, C4 4, H1 4, N3 4, P2 4, S2 4, W3 4, X3 4, AC2 3, AJ-1 3, AP-3 3,
D3 3, E3 3, O3 3, U3 3, AK-3 2, T3 2, AI-2 1, G3 1, R3 1. Tiap naskah
hanya 8 baris, jadi angka per naskah sangat berisik; jangan dipakai
untuk menghakimi satu naskah.

## Head-to-head v10 lawan v11

### Subset ketat (adil): 56 baris, 7 naskah grup 3

Satu-satunya subset yang label v10 per barisnya tersimpan
(`label_penuh` tahap 1). Naskah: W3, X3, Y2, Z3, AA3, AC2, AE2.

| Versi | Benar / 56 | Akurasi |
|---|---|---|
| v10 | 22 | 0,3929 |
| v11 | 29 | 0,5179 |

Per baris berpasangan: hanya v11 benar 21, hanya v10 benar 14, keduanya
benar 8, keduanya salah 13. McNemar khi-kuadrat 1,4, p sekitar 0,24,
tidak signifikan pada 0,05. Per label (subset ketat): bab v10 4/14 lawan
v11 7/14; subbab 2/5 lawan 3/5; paragraf 6/16 lawan 10/16; biasa 10/21
lawan 9/21. Jadi v11 naik di bab, subbab, paragraf, dan turun tipis di
biasa — semuanya di sampel kecil.

### Subset luas: 84 baris (ketat + cocok persis judul bab v10)

v10 27/84 (0,3214) lawan v11 34/84 (0,4048). Subset ini BIAS: 28 baris
tambahannya adalah judul bab v10 yang cocok persis, kebanyakan judul
sampah yang benarnya biasa, jadi v10 dirugikan oleh konstruksi. Jangan
pakai subset luas sebagai vonis; vonis memakai subset ketat.

## Pola salah v11 (matriks kebingungan, 279 baris)

| Benar \ v11 | bab | subbab | paragraf | biasa | tanpa label |
|---|---|---|---|---|---|
| bab (21) | 12 | 1 | 0 | 0 | 8 |
| subbab (45) | 2 | 32 | 3 | 8 | 0 |
| paragraf (75) | 0 | 17 | 43 | 15 | 0 |
| biasa (138) | 42 | 26 | 21 | 49 | 0 |

Dua pola utama. Pertama, v11 terlalu sering melabeli baris biasa sebagai
bab: 42 dari 138 baris biasa dilabeli bab, kebanyakan salinan
sistematika/daftar isi (R3, AI-2, O3) dan fragmen titik-dua. Kedua, 8
baris bab asli tidak punya label di `label_penuh` v11 (W3 BAB II; AA3
BAB II, BAB III; AE2 BAB I, PENDAHULUAN; AC2 BAB III, GAMBARAN UMUM
OBYEK PENELITIAN; N3 BAB III) — tapi kedelapan judul itu ADA di
`bab_gabung` v11, jadi ini celah representasi label per baris, bukan bab
yang hilang dari peta. Bila skor dihitung di tingkat judul gabungan,
kedelapan baris itu benar.

## Batas dan catatan jujur

- Label v10 per baris hanya tersimpan untuk 7 dari 35 naskah uji
  (grup 3). Untuk 28 naskah lain, tidak ada head-to-head yang mungkin
  dari data tersimpan; label_v10 di sana hanya diketahui bila teksnya
  cocok persis dengan judul bab v10.
- 20 sengketa bab tidak terlabeli karena batas 8 baris per naskah:
  Z3 12, T3 4, R3 1, AI-2 1, O3 1 (TypeSafe) dan AA3 1 (OpenRouter).
  Kebanyakan blok salinan daftar isi. Tidak dilabeli tanpa dibaca.
- Sampel bentuk non-Romawi kecil sekali: CHAPTER 8 baris (T3 saja),
  Arab 8 baris (AJ-1 saja). Jangan generalisasi dari situ.
- Kelompok OpenRouter dilayani model fallback
  `typesafe/jev-1.14-20261014` yang bobotnya belum terbukti identik
  dengan jev-1.14.0 resmi; selisih akurasi antar kelompok (TypeSafe
  0,5278 lawan OpenRouter 0,4444) bisa berasal dari naskah, model,
  atau keduanya, dan tidak dipisahkan di sini.
- Metode label_v10 dihitung ulang seragam di skrip gabung (metode teks
  untuk grup 3, cocok persis judul bab untuk lainnya). 46 nilai agen
  berubah dalam penggabungan: 27 baris mendapat v10='bab' dari cocok
  persis judul bab v10 (R3 7, H1 3, T3 5, U3 1, AL-2 1, O3 6, P2 1,
  AN-1 1, AJ-1 2), 18 baris grup 3 OpenRouter dikoreksi dari indeks
  mentah ke metode teks (di antaranya AA3 no 9 dan 11: 'bab' jadi
  'paragraf'; AA3 no 13 dan 16: 'bab' jadi 'biasa'; AC2 no 25: null
  jadi 'bab'), dan AN-1 no 51 'bab' jadi null (hanya cocok sebagian
  judul gabung, bukan cocok persis). Label v11 terverifikasi 0 selisih
  lawan `label_penuh` v11. Ruang indeks terverifikasi: jumlah baris
  teks bersih v10 sama dengan jumlah baris `baris_teks` v11 di 7
  naskah grup 3 (2429, 360, 830, 781, 658, 530, 2083).
- Teks sama di posisi beda dipertahankan sebagai baris terpisah bila
  labelnya beda (mis. H1 `BAB V` baris 300 biasa/daftar isi lawan
  baris 478 bab/badan; T3 `TABLE OF CONTENS` di dua posisi).
