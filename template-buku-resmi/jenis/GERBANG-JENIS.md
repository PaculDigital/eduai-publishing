# Gerbang Jenis Buku v1.1 — Gas Boss 26 Okt 2026, diperbaiki atas temuan agen Boss

## v1.1: menutup celah "cari kata" (temuan agen Boss, terverifikasi Wulan)

Celah v1 yang terbukti di cabang `047cc4d`:
- Buku ajar palsu (satu kalimat "Capaian pembelajaran latihan rangkuman
  checklist", nol isi ajar) = **9 LULUS / 0 GAGAL**.
- Buku-umum sampah total (semua kolom `"-"`) = **5 LULUS / 0 GAGAL**.
- Akar: cek v1 hanya `substring in teks` dan `len(...) > 0`.

Aturan anti-palsu v1.1 (di `periksa_jenis_buku.py`):
1. **Isi bermakna, bukan sekadar ada.** `"-"` / `"..."` / `"x"` bukan
   isi. Judul/penulis harus mengandung huruf; kata pengantar dan
   tentang penulis minimal 10 kata; tiap entri daftar pustaka minimal
   4 kata; tiap entri indeks/glosarium harus punya isi.
2. **Unsur berdiri sendiri.** Tiap unsur wajib harus ada di paragraf
   yang BERBEDA dan cukup panjang (minimal 10 kata). Satu paragraf
   yang menumpuk semua kata kunci hanya dihitung untuk SATU unsur.
3. **Posisi.** Tujuan harus muncul SEBELUM latihan di bab yang sama
   (tujuan di awal, latihan di akhir); latihan yang muncul sebelum
   tujuan = gagal.
4. **Buku-umum/anak bukan lagi pintu belakang.** Tiap bab minimal
   30 kata bermakna + judul bermakna.
5. **Tabel komparasi harus nyata** (kolom >= 2 dan baris berisi),
   bukan sekadar judul tabel.

Kalibrasi ambang (diukur dari contoh nyata fase1-ssot, bukan tebak):
sub-bab buku ajar nyata 35-89 kata, bab monograf nyata 88-133 kata,
kata pengantar nyata 35-80 kata — jadi ambang 10 kata per unsur dan
30 kata per bab umum TIDAK mematahkan contoh nyata, tapi membunuh
kalimat palsu 5 kata dan isi `"-"`.

## Bukti uji v1.1 (26 Okt 2026)

- `uji_gerbang_jenis.py`: **21/21 kasus sesuai harapan** — 15 kasus
  v1 (diperbarui ke format paragraf terpisah) + 6 kasus baru: 3
  serangan (ajar palsu, umum sampah, monograf palsu — semuanya
  GAGAL), ajar latihan-sebelum-tujuan GAGAL (cek posisi), umum bab
  pendek GAGAL, umum lengkap LOLOS.
- Serangan lama di v1.1: ajar palsu **3 LULUS / 6 GAGAL** (hanya
  U1/U5 dan satu unsur yang lolos, sisanya gagal — cukup untuk
  menolak), umum sampah **1 LULUS / 5 GAGAL**.
- Contoh nyata fase1-ssot (hanya ditambah kolom jenis, isi tidak
  diubah): ajar **13/0 LOLOS**, chapter **4/0 LOLOS**, referensi
  **6/3 GAGAL** (tanpa indeks + tanpa komparasi per bab — memang
  belum lengkap, sama seperti v1).
- **KOREKSI atas laporan v1:** contoh monograf fase1-ssot di v1.1
  menjadi **8/1 GAGAL** (M3 metode). Penyelidikan Wulan: satu-satunya
  kemunculan frasa "metode penelitian" di spec itu ada di JUDUL
  DAFTAR PUSTAKA ("Rahman, A. (2021). Metode penelitian manajemen"),
  bukan di isi bab mana pun — spec itu memang tidak punya paragraf
  metode sama sekali (babnya hanya Pendahuluan, Tinjauan, Hasil).
  Jadi klaim v1 "monograf contoh 9/0 lolos" adalah **false pass**
  dari celah yang sama, dan v1.1 memperbaikinya dengan benar:
  contoh monograf itu perlu ditambah paragraf metode sebelum boleh
  disebut monograf. Wulan TIDAK melemahkan gerbang supaya contoh
  mainan itu lolos — itu justru akan membuka lagi celahnya.

## Yang BELUM di v1.1 (jujur, jangan diklaim sudah)

- Gerbang memeriksa spec JSON, bukan PDF/DOCX jadi.
- Belum di-push (commit v1.1 masih lokal di cabang yang sama) dan
  belum di-merge — merge dilakukan sesudah Boss setuju atas v1.1 ini.
- Rekonsiliasi dengan profil.json fase1-ssot dan menjadikan kolom
  `jenis` WAJIB untuk semua spec baru tetap menjadi langkah
  berikutnya (v2), bukan bagian v1.1.

---

# Gerbang Jenis Buku v1 — Gas Boss 26 Okt 2026 (arsip, digantikan v1.1 di atas)

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
