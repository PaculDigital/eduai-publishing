# Paket Label Kebenaran Dasar (Ground Truth) Jev/Hakim v7

Tanggal: 10 November 2026. Kode: branch `agen/wulan/optimalkan-jev-hakim-v5`,
commit `b41392a` (v7). Tidak ada panggilan Jev yang dipakai untuk membangun
paket ini, tidak ada tulis ke database.

## Isi paket

| Berkas | Isi |
|---|---|
| `ground_truth_81.tsv` | 21 baris sengketa fid=81 (Asih) |
| `ground_truth_112.tsv` | 10 baris sengketa fid=112 (Wulandari kualitatif) |
| `ground_truth_115.tsv` | 9 baris sengketa fid=115 (Wulandari PDF resmi) |
| `ground_truth_WULAN-1.tsv` | 3 baris sengketa WULAN-1 |
| `buat_paket_ground_truth.py` | Skrip pembangun paket ini (bisa diulang, tanpa Jev) |
| `buat_sengketa_paragraf.py` | Skrip pelengkap untuk sengketa paragraf (butuh 2 run live, belum jalan) |
| `gerbang_baseline.json` | Baseline gerbang 3-naskah (dari hasil live v7) |
| `ringkasan_paket.json` | Ringkasan jumlah baris per naskah |
| `README.md` | Berkas ini |

Total: **43 baris sengketa** yang bisa Boss putuskan sendiri.

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

## Yang JUJUR belum ada di paket ini

**Sengketa batas paragraf antar-run v7 tidak ada di sini.** Penyebabnya:
label per baris dari 12 run v7 tidak pernah disimpan — yang tersimpan hanya
hitungan agregat (mis. paragraf fid=81: 166, 173, 173). Jadi Wulan tahu
paragraf bergoyang, tapi tidak tahu baris mana yang bergoyang.

Untuk melengkapinya, pakai `buat_sengketa_paragraf.py`: skrip itu menjalankan
2 run live baru per naskah DENGAN menyimpan label tiap baris, lalu
membandingkan kedua run dan mengeluarkan baris yang beda label. Biayanya
sekitar **180 panggilan Jev** (2 run x 4 naskah, dari angka live v7:
112 ~40, 115 ~36, 81 ~7, WULAN-1 ~7 per run). Skrip ini BELUM dijalankan —
perlu Gas Boss dulu karena biayanya live.

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
