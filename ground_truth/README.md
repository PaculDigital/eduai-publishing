# Paket Label Kebenaran Dasar (Ground Truth) Jev/Hakim v7

Tanggal: 10 November 2026. Kode: branch `agen/wulan/optimalkan-jev-hakim-v5`,
commit `b41392a` (v7). Tidak ada panggilan Jev yang dipakai untuk membangun
paket ini, tidak ada tulis ke database.

## Isi paket

| Berkas | Isi |
|---|---|
| `ground_truth_81.tsv` | 27 baris sengketa fid=81 (Asih): 21 lama + 6 sengketa paragraf baru |
| `ground_truth_112.tsv` | 209 baris sengketa fid=112 (Wulandari kualitatif): 10 lama + 199 baru |
| `ground_truth_115.tsv` | 142 baris sengketa fid=115 (Wulandari PDF resmi): 9 lama + 133 baru |
| `ground_truth_WULAN-1.tsv` | 19 baris sengketa WULAN-1: 3 lama + 16 baru |
| `buat_paket_ground_truth.py` | Skrip pembangun paket ini (bisa diulang, tanpa Jev) |
| `buat_sengketa_paragraf.py` | Skrip pelengkap sengketa paragraf (SUDAH jalan live 10 Nov 2026) |
| `ground_truth_sengketa_paragraf.tsv` | 363 baris sengketa paragraf mentah (sumber gabungan, sebelum digabung) |
| `gerbang_baseline.json` | Baseline gerbang 3-naskah (dari hasil live v7) |
| `ringkasan_paket.json` | Ringkasan jumlah baris per naskah |
| `README.md` | Berkas ini |

Total: **397 baris sengketa** (43 lama sudah berlabel + 354 baris sengketa paragraf baru yang labelnya masih kosong untuk Boss isi).

## Cara mengisi (untuk Boss)

1. Buka satu berkas TSV di spreadsheet (LibreOffice/Excel, pemisah Tab).
2. Untuk tiap baris, baca `teks_baris` beserta `konteks_sebelum` dan
   `konteks_sesudah`, lalu isi kolom `label_benar` dengan SATU kata:
   `bab`, `subbab`, `paragraf`, atau `biasa`.
   - `bab` = judul BAB (mis. BAB III METODOLOGI PENELITIAN).
   - `subbab` = judul subbab (mis. 3.1 Jenis Penelitian).
   - `paragraf` = awal paragraf baru (kalimat pertama sebuah paragraf).
   - `biasa` = baris biasa, bukan awal apa pun (lanjutan kalimat, sitasi,
     nama narasumber, isi tabel, dan sejenisnya).
3. Bila ragu, tulis alasannya di `catatan_boss`, jangan menebak diam-diam.
   Baris yang kosong labelnya dianggap belum diputuskan, bukan salah.
4. Kolom `bukti_run` menjelaskan KENAPA baris ini masuk paket (mis.
   "1.13: biasa | 1.14: paragraf" atau "Hakim curiga di run 1 dan 2").
   Itu bukti sengketa, bukan jawaban — jawabannya dari Boss.

## Jenis sengketa di paket ini

| Jenis | Arti |
|---|---|
| `beda_model_113_114` | Jev 1.13 dan 1.14 memberi label berbeda (hanya fid=81) |
| `bab_hilang` | Judul BAB ada di sebagian run, hilang di run lain |
| `judul_bab_sampah` | Jev melabel satu kalimat utuh sebagai judul BAB |
| `hakim_curiga` | Hakim menandai baris ini mencurigakan (mis. awal sitasi) |
| `hakim_ragu` | Hakim ragu (nilai Jev 0,5–0,7), perlu manusia |
| `sengketa_paragraf` | Label baris ini beda antara run 1 dan run 2 live (10 Nov 2026) |

## Sengketa paragraf (dilengkapi 10 Nov 2026, Gas Boss, 180 panggilan Jev)

`buat_sengketa_paragraf.py` dijalankan live (2 run x 4 naskah) dan menemukan
**363 baris sengketa**: fid=81: 11, fid=112: 201, fid=115: 134, WULAN-1: 17.
Dari 363 itu, 354 masuk sebagai baris baru (label kosong) dan 9 digabung ke
baris lama yang sudah ada (bukti barunya ditempel di kolom `bukti_run`).

**Jujur soal isinya — namanya "sengketa paragraf" tapi isinya lebih luas:**
hanya ~76 baris yang benar-benar soal batas paragraf (paragraf vs biasa 57,
paragraf vs subbab 19). Sisanya: kandidat yang ada di satu run tapi hilang di
run lain (None vs biasa 154, None vs subbab 6), subbab vs biasa 110, dan 4
baris soal label BAB (paragraf vs bab 3, bab vs biasa 1). Jadi goyangnya
bukan cuma batas paragraf — himpunan kandidat dan label subbab ikut goyang
antar run. Itu temuan penting, bukan sekadar jumlah baris.

**Volume:** 354 label kosong itu banyak (fid=112 sendiri 199). Boss tidak
harus mengisi semuanya sekaligus — isi dulu yang paling berdampak (baris
yang melibatkan label `paragraf` dan `bab`), sisanya bisa diisi bertahap
atau diambil sampelnya. Baris yang kosong labelnya dianggap belum
diputuskan, bukan salah.

## Seberapa bisa dipercaya nomor baris di paket ini

- **fid=81 dan WULAN-1: nomor baris = nomor live.** Rekonstruksi tanpa Jev
  di sini SELARAS persis dengan live (fid=81: kandidat 486, buang 720,
  stitch 0 panggilan Jev; WULAN-1: kandidat 427, buang 199).
- **fid=112 dan 115: nomor baris bisa geser.** Stitch di kedua naskah ini
  memakai Jev (49 dan 37 pasangan ragu), jadi tanpa Jev rekonstruksinya
  tidak menyambung dan nomor baris bergeser (terukur: geser 78–1468 baris).
  Teks baris dan konteksnya tetap benar (dicari lewat pencarian teks),
  dan untuk baris Hakim dipakai nomor live `Lxxxxxx` dari log. Jadi
  andalkan TEKS-nya, bukan nomornya, untuk kedua naskah ini.
- Satu bukti tambahan: tanpa stitch Jev, mock menemukan BAB I + BAB VI
  palsu dan kehilangan BAB IV + BAB V di 112/115 — persis alasan kenapa
  paket ini tidak memakai rekonstruksi mock untuk baseline BAB.

## Sesudah Boss mengisi

Label Boss dipakai untuk tiga keputusan:
1. **Skor Jev 1.13** — berapa baris sengketa yang dijawab benar.
2. **Skor Jev 1.14** — sama, untuk 21 baris fid=81 (dan sengketa paragraf
   bila sudah dilengkapi). Ini yang akhirnya memutuskan pindah model atau
   tetap 1.13 sebelum pensiun sekitar 13 Desember 2026.
3. **Gerbang 3-naskah** (`../gerbang_3_naskah.py`) — pemeriksaan otomatis
   sebelum pilot produksi: BAB tidak boleh hilang, subbab tidak boleh
   berubah lebih dari ambang, tidak boleh ada judul BAB sampah.
