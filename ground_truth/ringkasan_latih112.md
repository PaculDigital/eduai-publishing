# Ringkasan Paket Label Latih 112 Naskah — Tahap 3

Tanggal: 11 November 2026. Branch `agen/wulan/optimalkan-jev-hakim-v5`.
**Nol panggilan Jev** — semua label dibaca dari teks mentah dan hasil run
tersimpan tahap 1. Skrip pembangun: `_sketsa/bangun_tsv_latih112.py`.

## Isi

| Berkas | Isi |
|---|---|
| `ground_truth_latih112.tsv` | 254 baris sengketa, **semua sudah berlabel** |
| `ringkasan_latih112.json` | Hitungan per bidang, per jenis, per label (mesin) |
| `ringkasan_latih112.md` | Berkas ini |

## Distribusi label (254 baris)

| Label | Jumlah |
|---|---|
| biasa | 140 |
| paragraf | 68 |
| subbab | 39 |
| bab | 6 |
| ragu | 1 |

Satu-satunya `ragu` adalah no 132 (B3, "Bab I Pendahuluan" berulang sebagai
kepala berjalan; dari konteks itu tak dapat dipastikan mana pembuka Bab I
yang asli). Tidak ada label yang ditebak.

## Per bidang (41 dari 42 bidang terwakili)

| Bidang | Baris |
|---|---|
| Administrasi Negara | 7 |
| Administrasi Niaga | 7 |
| Akuntansi | 7 |
| Bahasa Inggris | 7 |
| Bimbingan Konseling | 7 |
| Ekonomi Pembangunan | 7 |
| Hukum | 7 |
| Hukum Perdata | 7 |
| Hukum Pidana | 7 |
| Informatika Multimedia | 7 |
| Kimia | 7 |
| Manajemen | 7 |
| Matematika | 7 |
| Pendidikan Agama Islam | 7 |
| Pendidikan Elektro | 7 |
| Skripsi ESP Syariah | 7 |
| Skripsi Kebidanan | 7 |
| Teknik Industri | 7 |
| campuran | 7 |
| ekonomi | 7 |
| ekonomi-manajemen | 7 |
| informatika | 7 |
| pendidikan-bhs-arab | 7 |
| pendidikan-biologi | 7 |
| perbankan-syariah | 7 |
| psikologi | 7 |
| teknik-mesin | 7 |
| teknik-sipil | 7 |
| teknik-telekomunikasi | 7 |
| tesis | 7 |
| fisika | 6 |
| ilmu-tanah | 5 |
| peternakan | 5 |
| ppkn | 5 |
| hukum-tata-negara | 4 |
| pendidikan-bahasa-inggris | 4 |
| bimbingan-konseling | 3 |
| komunikasi | 3 |
| pendidikan-bahasa-indonesia | 3 |
| pendidikan-ekonomi | 3 |
| perhotelan | 3 |

Catatan nama: `Bimbingan Konseling` (R1, R2) dan `bimbingan-konseling`
(AF1) adalah dua entri bidang yang berbeda di `pembagian.json` dan
`naskah_utuh.md`, jadi dihitung terpisah apa adanya, bukan digabung diam-diam.

**teknik-pertanian: 0 baris.** Satu-satunya naskah belajarnya (Y1) adalah
grup 3 dan ketujuh kandidatnya berbasis idx yang ditunda (lihat bawah), jadi
tidak ada baris yang lolos ke paket.

## Per jenis sengketa

| Jenis | Jumlah |
|---|---|
| hakim_ragu | 87 |
| goyang_bab | 67 |
| goyang_subbab | 54 |
| hakim_curiga | 37 |
| deterministik_daftar_isi | 4 |
| deterministik_pemisah | 3 |
| deterministik_nomor_polos | 2 |

## Kejujuran soal isi TSV

- **130 baris memakai baris mentah utuh** sebagai `teks_baris`, karena
  cuplikan run hanya fragmen/ekor judul (mis. "dalam Kegiatan Produksi"
  dari "1.4.3.3 Kewajiban Zakat dalam Kegiatan Produksi"). Fragmen aslinya
  dicatat di `bukti_run`. 124 baris memakai cuplikan apa adanya.
- **15 butir konteksnya kosong di paket** (no 11, 20, 26, 63, 65, 66, 100,
  105, 169, 170, 183, 184, 189, 225, 253); konteksnya diisi bertarget dari
  teks mentah lewat jangkar (lihat `JANGKAR` di skrip pembangun) dan ditandai
  di `bukti_run`. Dua di antaranya rawan salah jangkar dan dicatat di sini:
  no 184 ("2.42 Kesimpulan yang") punya 3 kemunculan identik di E1, diambil
  yang pertama; no 169/170 memakai sistematika A2 (baris 298/311).
- **2 baris tanpa nomor baris** (`baris_no` kosong): no 133 (B3) dan no 186
  (E1), keduanya di dekat awal berkas. Konteksnya tetap ada.
- **12 baris tanpa konteks sebelum, 3 tanpa konteks sesudah**: wajar, baris
  di dekat awal/akhir berkas atau diapit baris kosong (X2 no 154-156).
- **738 kandidat idx grup 3 TERTUNDA**, tidak ditebak dan tidak masuk paket
  ini (tersimpan di `_sketsa/kandidat_idx_grup3_tertunda.json`). Alasan:
  baris live grup 3 (stitch pakai Jev) tidak selaras dengan rekonstruksi
  tanpa stitch, hanya 40/107 judul bab cocok di idx yang sama. Pemetaan
  ulang butuh tahap 5 (live).
- Label diisi Wulan dari teks, bukan Boss. Bila Boss memeriksa ulang dan
  tidak setuju, label di TSV ini yang diganti (dengan nama berkas baru,
  jangan ditimpa).

## Tahap 5 (verifikasi live) — TERTUNDA

Anggaran panggilan sesi sudah terlewati di tahap 1 (2.431 tercatat).
Verifikasi live 36 naskah uji pasca-dedup diperkirakan ~540 panggilan
(36 x ~15; pra-dedup 37 x ~15 = ~555). Belum ada klaim presisi naik.
