# Lapisan Bentuk v11 (11 November 2026)

Dibangun di tahap 4 latihan Jev/Hakim 112 naskah, branch
`agen/wulan/optimalkan-jev-hakim-v5`, commit tahap 4. `RULE_VERSION`
naik v10 -> v11. **Nol panggilan Jev** (semua dari teks dan hasil run
tersimpan). Verifikasi live (tahap 5) TERTUNDA, jadi **tidak ada klaim
presisi naik**.

## Yang dibangun (di `peta3_jev.py`)

### Lapis 1 — `profil_bentuk(teks)` (deterministik, tanpa Jev)
Dihitung dari teks mentah sebelum stitch. Isi: penomoran BAB
(arab/romawi/campuran/chapter/romawi_tanpa_bab/tidak_ada), daftar BAB,
judul Romawi yang cocok kosakata, sistematika, tabel padat (>20 baris
pipa), rasio Inggris (ambang 0,02), KTI D3, empat bab, pemisah gabungan,
BOM, NUL, huruf berspasi. Satu-satunya saklar aturan yang dipilih profil:
deteksi judul Romawi tanpa kata BAB.

### Aturan baru di susun (v11)
- **BOM dibuang** (66/112 teks; BOM menempel di judul bab).
- **Pemisah gabungan dibuang** (`===== ... =====`, 117 baris di 50 teks,
  semuanya pagar nama berkas; sempat terlabel bab di AM-2/AO-1).
- **CHAPTER polos dikenali** (`CHAPTER II` + judul baris berikut; 4
  naskah T1/T2/T3/AH1). Bentuk satu baris `CHAPTER I: ...` SENGAJA tidak
  dipakai: satu-satunya kemunculan terukur ada di daftar isi (T2).
- **Judul Romawi tanpa kata BAB dikenali** (`I. PENDAHULUAN`, dst; 6
  entri Y1/Y2/AD1/AD2/AD3/AG1) — HANYA bila profil bilang bentuknya
  memang begitu; judul harus sama persis dengan kosakata judul BAB
  terukur (sitasi `VI. Pp. 1187-1196.` dan `III. TABLE: ...` tidak kena).

### Lapis 2 — `pendapat_kedua(idx, teks, suara, p, jawaban_kedua=None)`
Murni deterministik. Jawaban kedua DISUNTIK pemanggil (tanya ulang live
atau model 1.13 sebagai pembanding); fungsi ini tidak pernah memanggil
Jev. Putusan: tetap / berbalik (minoritas + lebih yakin) /
antrean-manusia (tanpa jawaban, tidak yakin, atau tiga suara berbeda).
Aturan suara teratas SAMA dengan `_hitung_label` (confidence tertinggi,
seri -> suara pertama). Dikaitkan ke `_petakan_dari_hasil` lewat
parameter opsional `pendapat_kedua_fn`; tanpa fn, perilaku sama persis
dengan v10. Cache dilewati bila fn disuntik.

### Lapis 3 — antrean manusia
`profil_bentuk` menandai `antrean_manusia` + alasan bila: tidak ada
penanda BAB/CHAPTER/judul Romawi, atau NUL > 50 (ambang dari fid=112:
103 NUL). Hasil `petakan` membawa `profil_bentuk`, `antrean_manusia`,
`alasan_antrean`, `pendapat_kedua_jml/berbalik/antrean`. Peta tetap
dihitung (untuk ditinjau manusia), tapi ditandai tidak boleh dipakai
otomatis. Bahasa Inggris HANYA dilaporkan, tidak mengantrekan: ke-4
naskah Inggris terukur terpetakan lewat CHAPTER; usulan antrean Inggris
di RENCANA_LAPISAN_BENTUK.md menunggu putusan Boss (no 1-4).

## Bukti offline
- `python3 tests/test_jev_hakim.py` — **247 lulus, 0 gagal** (termasuk
  35 pemeriksaan v11 baru; uji lama tetap lulus).
- `python3 _sketsa/verifikasi_v11_offline.py` — keluar 0: profil cocok
  112/112 dengan profil terukur di `_sketsa/tabel_latih112.json`; susun
  benar di 6 naskah Romawi, 4 naskah CHAPTER, 2 naskah pemisah, 1 naskah
  BOM.

## Koreksi catatan lama (ditemukan saat verifikasi)
- Klaim "CHAPTER I-V terdeteksi 5 tiap naskah" menghitung sebutan daftar
  isi: **T2 hanya punya 4 CHAPTER polos di badan** (I-IV); CHAPTER V
  hanya ada di daftar isi, badan Bab V dibuka judul polos `CONCLUSION
  AND SUGGESTION` tanpa penanda. Aturan v11 tidak memaksa CHAPTER V T2.
- Hitungan pemisah: analisis tahap 1 memakai pola SEMPIT (BAB saja: 74
  baris, 15 teks); aturan v11 memakai pola LUAS (117 baris, 50 teks) —
  semuanya pagar nama berkas, nol isi asli (98 baris unik diperiksa).
