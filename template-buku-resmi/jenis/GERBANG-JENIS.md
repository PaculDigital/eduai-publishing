# Gerbang Jenis Buku v1 — Gas Boss 26 Okt 2026

## Masalah yang ditutup

Mesin hanya tahu "bikin buku", bukan "bikin buku apa". Analisa 10
contoh buku 26 Okt 2026 membuktikan: buku ajar/monograf berlabel
"referensi" lolos, panduan praktis berlabel "buku ajar" lolos,
monograf tanpa penelitian/temuan/simpulan lolos.

## Prinsip

**Jenis ditentukan dari isi, bukan dari label.** Spec JSON wajib
menyatakan kolom `jenis`. Tanpa jenis, gerbang gagal — mesin tidak
boleh menebak jenis dari judul.

Jenis yang dikenal: `buku-referensi`, `buku-ajar`, `monograf`,
`buku-umum`, `buku-anak`, `panduan-praktis`, `book-chapter`.

## Unsur wajib per jenis (GAGAL = buku tidak boleh diserahkan)

Semua jenis: judul + penulis terisi, kata pengantar terisi, tentang
penulis terisi, daftar pustaka tidak kosong, minimal 1 bab.

- **Buku referensi** (harus bisa DIRUJUK): indeks subjek ada dan tidak
  kosong, indeks nama ada dan tidak kosong, tabel komparasi /
  perbandingan di TIAP bab, posisi penulis eksplisit.
- **Buku ajar** (tiap bab harus bisa MENGAJAR): TIAP bab dibuka
  TIU/TIK atau Capaian Pembelajaran, dan ditutup latihan, rangkuman,
  dan checklist pemahaman.
- **Monograf** (harus ada PENELITIAN penulis): pernyataan kebaruan /
  novelty, keterbatasan penelitian dinyatakan, metode penelitian
  penulis sendiri (bab "metodologi" yang isinya prinsip umum TIDAK
  cukup), bab hasil/pembahasan ada.
- **Panduan praktis**: contoh + langkah praktis ada.
- **Buku umum / anak**: struktur utuh + daftar pustaka (v1).
- **Book chapter**: section pertama Pendahuluan + tujuan, referensi
  tidak kosong, glosarium tidak kosong, CV penulis ada.

## Peringatan (belum menggagalkan di v1, sengaja)

Glosarium + daftar singkatan (referensi), kunci jawaban + bab
penutup + CPL/CPMK (ajar), pertanyaan penelitian + bab penutup +
indeks (monograf). Ini utang v2 — sengaja belum fatal supaya contoh
yang sudah berjalan tidak patah mendadak oleh satu format.

## Dugaan jenis lain

Jalankan dengan `--dugaan`: kalau jenis yang diklaim gagal tapi
jenis lain lolos penuh, gerbang mencetak "Diduga jenis sebenarnya:
...". Label bisa diperbaiki, bukan sekadar ditolak.

## Cara pakai

```
python3 template-buku-resmi/scripts/periksa_jenis_buku.py spec.json
python3 template-buku-resmi/scripts/periksa_jenis_buku.py --jenis buku-ajar spec.json
python3 template-buku-resmi/scripts/periksa_jenis_buku.py --dugaan spec.json
python3 template-buku-resmi/scripts/uji_gerbang_jenis.py   # uji bergigi
```

## Cara kerja di generator

`buat_buku.py` menjalankan gerbang jenis SEBELUM menulis apa pun,
hanya bila spec menyatakan `jenis`. Spec ber-jenis yang gagal =
ditolak, tidak ada berkas .docx yang ditulis. Spec lama tanpa kolom
`jenis` TIDAK dipatahkan: gerbang dilewati dengan peringatan, supaya
contoh lama tetap jalan. `--tanpa-gerbang` melewati kedua gerbang
(jenis + template), seperti sebelumnya.

## Bukti uji (26 Okt 2026)

- `uji_gerbang_jenis.py`: **15/15 kasus sesuai harapan** — 5 spec
  lengkap lolos, 8 mutasi gagal (tanpa indeks, tanpa posisi penulis,
  tanpa latihan, tanpa keterbatasan, tanpa metode, tanpa jenis,
  tanpa daftar pustaka, jenis asing), 2 salah label gagal (panduan
  diklaim ajar → dugaan "panduan-praktis" benar; ajar diklaim
  monograf → gagal).
- Contoh nyata fase1-ssot (ditambah kolom jenis saja, isi tidak
  diubah): ajar **13 LULUS / 0 GAGAL**, monograf **9 LULUS / 0 GAGAL**,
  referensi **6 LULUS / 3 GAGAL** (tanpa indeks subjek, tanpa indeks
  nama, tanpa komparasi per bab) — bukti gerbang menangkap contoh
  referensi yang memang belum lengkap.
- Wiring: spec referensi yang gagal ditolak generator sebelum
  menulis (tidak ada .docx); spec ajar yang lolos jadi .docx dan
  lolos gerbang template 53/0; spec lama tanpa jenis tetap jadi
  .docx dengan peringatan.

## Yang BELUM dikerjakan (jangan diklaim sudah)

- Gerbang ini memeriksa spec JSON, bukan PDF/DOCX jadi dan bukan
  buku contoh lama yang berbentuk PDF — buku PDF lama tetap harus
  dinilai dari isi seperti analisa 26 Okt 2026.
- Belum di-push (menunggu PAT Boss, seperti pola biasa) dan belum
  di-merge ke main.
- Rekonsiliasi dengan profil fase1-ssot (yang punya unsur_wajib
  sendiri) dilakukan saat fase1-ssot di-rebase — gerbang ini memakai
  aturan yang sama sumbernya, tapi belum membaca profil.json
  secara langsung.
- Menjadikan kolom `jenis` WAJIB untuk semua spec baru (v2) adalah
  keputusan berikutnya, bukan bagian v1 ini.
