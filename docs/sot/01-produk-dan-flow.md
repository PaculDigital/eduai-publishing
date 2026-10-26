# 01 — Produk & Flow EduAi

<!-- SOT: Produk & flow EduAi. Diperbarui 26 Okt 2026. Sumber: README.md + app/main.py + app/alur_awal.py + cek live 24–26 Okt 2026. -->

## Apa itu EduAi

EduAi Publishing (https://eduai.bikinaja.id) adalah portal dokumen akademik self-hosted + AI bantu penelitian untuk mahasiswa/dosen Indonesia. Bukan generator tulisan dari nol — mesin **merevisi naskah yang sudah ada**.

Di dalamnya hidup 4 bisnis sekaligus — inilah akar kenapa flow terasa kompleks:

1. **Storage dokumen** ala Google Drive (folder, unggah, editor OnlyOffice, sampah 30 hari)
2. **AI skripsi** (peta Jev → revisi → belajar → BAB IV)
3. **Penerbitan buku** (5 jenis buku, lihat `06-buku-dan-mutu.md`)
4. **Jurnal** (cari referensi → konversi artikel → submit → LoA JEMT + QR)

## Jenis dokumen (11, `app/jenis.py`)

Akademik: skripsi (S1), tesis (S2), disertasi (S3), artikel jurnal, proposal, dokumen umum.
Buku: buku ajar, buku umum, monograf, book chapter, buku referensi.
Buku BUKAN skripsi/tesis — Jev & Hakim tidak berlaku untuk buku; buku memakai gerbang mutu buku.

## Flow mahasiswa (garis utama)

```
Daftar / Masuk
  → Onboarding 4 langkah (app/alur_awal.py): Jenjang → Bidang → Mode penelitian → Judul (3 contoh judul)
  → /mulai → /naskah
      ├─ Unggah naskah → PAGAR 3 LAPIS: format → isi → mutu (naskah rusak ditolak sebelum bayar Jev)
      └─ Dokumen baru → dari kerangka / RPS
  → Jev memetakan bentuk (prinsip: Jev → mesin → AI → Jev periksa hasil)
      Jev baca BENTUK (bab/subbab/posisi) → Satpam periksa skema → Hakim nilai ragu/curiga
      → peta disimpan (ProfilDokumen + SectionState = "ingatan dokumen", menempel via file_id)
  → Pilih layanan (semua potong dari 1 dompet token yang sama):
      A. Revisi / Kerangka per BAB (harga per bab di 04-harga-dan-kuota.md)
      B. Mode Belajar (insight isi naskah + simulasi sidang)
      C. Konversi Jurnal (skripsi → artikel, cek 11 elemen → cari jurnal → submit → LoA)
      D. Buku (1 dari 5 kartu jenis → pipeline per jenis → DOCX jadi)
      E. BAB IV (lihat bawah — sudah merge, belum deploy)
  → Proses AI async (tabel ProsesAI) → hasil → TERIMA / TOLAK per bagian → versi tersimpan
  → Unduh — atau — Bagikan ke pembimbing → pembimbing buka /tinjau/<token> (tanpa daftar)
      → baca (OnlyOffice mode baca) + catatan per subbab + lampiran
      → opsional "Periksa dengan AI" (saklar PEMBIMBING_AI_AKTIF)
      → mahasiswa dapat notifikasi (+ WA) → revisi lagi → LOOP
```

## Flow pembimbing

Flow pembimbing BUKAN alur lurus tersendiri — ia menempel di tengah flow mahasiswa lewat `/tinjau/{token}` dan `/pembimbing/*` (bagikan/cabut tautan, kunci bimbingan, arsip catatan 60 hari, notifikasi, WA). Pembimbing = user paket gratis yang dapat 3 token, bebas dipakai sebagai mahasiswa ATAU pembimbing, dompetnya satu.

## BAB IV — status kini (26 Okt 2026)

- Rancangan induk: `DOKUMENTASI_BAB4_RANCANGAN_FINAL_21OKT2026.md` (root, dipertahankan).
- Isi: peta BAB IV disahkan → instrumen (kuesioner.md + template.csv) → data lapangan / simulasi → pra-survei (opsional) → olah data via jembatan Statistik Lab → kunci hasil (draf → terkunci) → narasi kuantitatif / kualitatif (catatan → koding → matriks) / campuran (2 putaran, narasi 1×).
- **Sudah merge ke `main`, BELUM deploy.** Cek live Wulan 24 Okt 01.20 dan 26 Okt 10.44 WIB: `GET /api/bab4/ringkasan` = 404. Sisa langkah: build/deploy image + pasang kunci produksi `EDUAI_STATISTIK_KUNCI` (lihat `05-jembatan-dan-layanan-luar.md`).
- Satu commit yatim terkait BAB IV, `73a7a64` (narasi 4.3 kualitatif, 21 Okt), TIDAK ikut ke `main` — nasibnya masih terbuka, diputuskan Boss (lihat `03-keputusan-terkunci.md`).
