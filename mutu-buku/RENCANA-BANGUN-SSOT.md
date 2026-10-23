# 🔒 RENCANA BANGUN SSOT BUKU — DOKUMEN ACUAN TERKUNCI

> **Status:** TERKUNCI oleh Bos, 23 Oktober 2026 (side chat "Cek kecocokan
> skill template buku"). Daftar ini adalah acuan tunggal pekerjaan membangun
> sistem buku berbasis satu sumber kebenaran (single source of truth).
> **Isi daftar ini hanya boleh berubah atas persetujuan Bos.**
>
> **Cara menagih:** setiap nomor dinyatakan selesai HANYA dengan bukti
> (hasil uji / berkas nyata / render), bukan klaim. Nomor yang belum
> berbukti = belum selesai.
>
> **Dasar diskusi:** commit `e491fc3` (Daftar Pustaka wajib), `a0746bc`
> (spesifikasi per jenis), `53f9efb` (book chapter), `a5ecf74` (mutu buku —
> agen kolaborator), `e99478e` + `1d7ec9d` (gambar, visual & SOT blok gaya).

---

## SUDAH ADA — dipakai lagi, TIDAK dibangun ulang

- Generator inti (`scripts/buat_buku.py`) — salinan template + isi dari JSON
- Gerbang dasar 57 asersi (`scripts/periksa_buku_template.py`)
- Penulisan aman/atomik (gagal = tidak ada berkas rusak tertulis)
- Titik pemimpin literal di cache daftar isi (terlihat di penampil HP)
- Cek XML well-formed sebelum menulis
- Template induk 14 × 20 cm (`templates/template-buku-resmi.docx`)

---

## A. SUMBER TUNGGAL (SSOT)

- [x] **1. Peta SOT** — `mutu-buku/SOT-INDUK.md` diperluas: setiap fakta
  tercatat SATU rumahnya; fakta yang berumah ganda ditandai untuk disatukan.
  ✅ 23 Okt 2026: §9 peta fakta per kategori + 3 rumah ganda ditandai
  (branch `agen/wulan/fase1-ssot`).
- [ ] **2. Berkas profil per jenis** — satu berkas untuk monograf, buku
  referensi, buku ajar, buku umum/anak. Isi tiap profil EMPAT hal:
  (a) angka format, (b) unsur isi wajib, (c) aturan tulisan,
  (d) prompt gambar + jangkar konsistensi.
- [x] **3. Dokumen spesifikasi turunan** — SPESIFIKASI per jenis DIHASILKAN
  dari profil (bukan salinan tangan), supaya tidak bisa menyimpang lagi.
  ✅ 23 Okt 2026: `scripts/buat_spesifikasi.py` + 4 SPESIFIKASI-DARI-PROFIL.md;
  verifikasi 30 angka profil, 0 hilang dari dokumen.

## B. MESIN

- [ ] **4. Penegakan Daftar Pustaka WAJIB** di generator + gerbang
  (menutup utang: sudah disahkan Bos di `e491fc3`, di kode masih opsional).
- [ ] **5. Generator menerapkan profil** — ukuran halaman, margin, huruf,
  spasi diganti dari profil; agen memanggil dengan menyebut jenisnya.
- [ ] **6. Gerbang membaca profil yang sama** — aturan pemeriksaan per
  jenis, bukan satu aturan untuk semua.
- [ ] **7. Nomor halaman terukur** — daftar isi dan indeks mengambil nomor
  dari render buku jadi; perkiraan 360 kata/halaman PENSIUN.
- [ ] **8. Gerbang font di server produksi** — font berlisensi yang Bos
  unggah diperiksa terpasang sebelum produksi jalan.

## C. MUTU TULISAN (dari `a5ecf74`)

- [ ] **9. Aturan tulisan per jenis di profil** — tone, larangan budaya
  untuk TEKS, aturan sitasi jenis itu.
- [ ] **10. Gerbang tulisan terukur** — sitasi dua arah tanpa yatim
  (entri pustaka tak dirujuk = gagal; sitasi tanpa entri pustaka = gagal),
  kata larangan budaya tidak muncul di teks, bagian wajib tulisan hadir
  (posisi penulis / novelty).
- [ ] **11. Gate cek plagiarisme** sebelum buku final.
- [ ] **12. Alur verifikasi sitasi 3 lapis** untuk peninjau — referensi
  benar ada, atribusi benar, makna tidak dipelintir — dibantu bukti dari
  kwitansi (nomor 16), bukan mulai dari nol.

## D. MUTU PROMPT GAMBAR (dari `e99478e` + analisa 23 Okt 2026)

- [ ] **13. Prompt pembuat brief baru** — brief BERSLOT (subjek + aksi,
  latar, komposisi, warna per benda, suasana) + 2–3 contoh brief bagus
  sebagai pola tiruan; untuk mode konseptual (umum) dan literal (anak).
- [ ] **14. Blok gaya baru POSITIF-DULU** — deskripsi jelas di depan,
  larangan dipangkas pendek di ekor, + jangkar konsistensi (frasa gaya
  dan deskripsi tokoh yang SAMA untuk semua gambar dalam satu buku).
- [ ] **15. Pemeriksaan isi gambar** — gambar hasil dibandingkan dengan
  brief-nya; meleset = dibuat ulang. Bukan cuma cek lebar.

## E. BUKTI & MUTU KESELURUHAN

- [ ] **16. Kwitansi mutu otomatis** menyertai tiap buku: versi profil,
  hasil semua gerbang (format, isi, tulisan, gambar), hasil plagiarisme,
  status sitasi & font.
- [ ] **17. Buku emas per jenis** — contoh baku; setiap mesin berubah,
  buku emas dirender ulang dan dibandingkan (uji regresi).
- [ ] **18. Uji bergigi untuk semua gerbang baru** — setiap pemeriksa
  baru wajib dibuktikan BISA gagal.
- [ ] **19. Buku contoh nyata per jenis + gambar uji nyata** — bukti
  ujung-ke-ujung tiap jenis sebelum dinyatakan selesai.

## F. BOOK CHAPTER (terakhir, mode sendiri — BUKAN buku utuh)

- [ ] **20. Profil + mode rakit book chapter** — satu bab, 15 section
  A–O, glosarium tabel 2 kolom, maksimal 15 halaman A5; PDF Turnitin
  tetap A4, tidak disentuh; gerbangnya sendiri.

---

## URUTAN KERJA

1. **A** dulu (peta + profil).
2. **B untuk monograf** sebagai bukti pertama — di dalam bukti itu
   **C nomor 9–10** dan **D nomor 13–15** ikut dibangun untuk monograf.
3. **E** menyusul (kwitansi, buku emas, uji).
4. Pola disalin ke buku referensi, buku ajar, buku umum/anak.
5. **F (book chapter)** terakhir.

## KEPUTUSAN YANG MENUNGGU BOS

| # | Keputusan | Usulan Wulan |
|---|---|---|
| 1 | Judul bab buku referensi = TNR 16 pt? | Ya |
| 2 | Gutter A5/B5 = 0? | Ya |
| 3 | Buku umum: setelan induk 14×20 atau B5? | B5 (ikut skill) — kecuali Bos putuskan lain |
| 4 | Gaya gambar buku umum: flat atau 3D kartun edukasi? | Ikut selera Bos (3D kartun) — perlu kata Bos |

## PRINSIP YANG MENGIKAT SELURUH DAFTAR

- Skill MEMUTUSKAN, profil MENYIMPAN, mesin MEMBACA, dokumen MENJELASKAN.
- Angka yang tercetak harus DIUKUR, bukan ditebak.
- LULUS butuh bukti; TOLAK dengan alasan; uji harus BISA gagal.
- Mesin kemarin DIPAKAI — yang dibangun adalah tambahan di atasnya,
  bukan penggantinya.

---

*Dikunci 23 Oktober 2026 atas perintah Bos. Agen yang mengerjakan daftar
ini wajib mencentang nomor hanya setelah bukti ada.*
