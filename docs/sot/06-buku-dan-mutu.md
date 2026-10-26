# 06 — Buku & Mutu Buku

<!-- SOT: Buku & mutu buku EduAi. Diperbarui 26 Okt 2026. Sub-SOT buku yang detail ada di mutu-buku/ — file ini hanya pintu & ringkasannya. -->

## 5 jenis buku (satu identitas per buku, `app/jenis.py`)

Buku ajar, buku umum, monograf, book chapter, buku referensi.
Buku BUKAN skripsi/tesis: Jev & Hakim tidak berlaku untuk buku; buku memakai gerbang mutu buku.

## Flow buku (ringkas)

Pilih 1 dari 5 kartu jenis di halaman `/buku` → siapkan sumber (RPS/naskah, sesuai jenis) → pipeline per jenis → ilustrasi/diagram + tata paragraf → gerbang mutu → DOCX jadi.
Mesin: `app/buku.py`, `app/penyusunan_buku.py`, `app/gambar.py`, `app/brief.py` + `buku_umum_pipeline.py` / `buku_umum_assembly.py` di root.
Standar penulisan buku: `STANDAR_PEMBUATAN_BUKU_20OKT2026.md` (root, dipertahankan).
SOT per fitur buku (root, dipertahankan): `SOT_JEV_BUKU_UMUM_20OKT2026.md` (bentuk naskah buku umum), `SOT_PUBLISH_BUKU_17OKT2026.md` (publish buku).

## SSOT mutu buku — status & batas scope

- Dokumen acuan: `mutu-buku/RENCANA-BANGUN-SSOT.md` (20 barang SSOT buku).
- Sub-SOT buku: `mutu-buku/SOT-INDUK.md`, `mutu-buku/STATUS-RENCANA-SSOT.md`, `mutu-buku/README.md`, plus `mutu-buku/skill-agen-kolaborator/` (skill agen kolaborator + referensinya).
- Status per 23 Okt 2026: **19/20 SELESAI** di cabang `agen/wulan/fase1-ssot` (BELUM ter-push, BELUM merge ke `main` — pekerjaan itu TIDAK disentuh perapihan dokumen 26 Okt ini).
- Keputusan Boss 23 Okt 2026 yang sudah diterapkan di cabang itu: judul referensi TNR 16 SAH; gutter A5/B5 = 0; buku umum pindah B5; gaya gambar umum = infografis 3D kartun (anak tetap flat putih, pendidikan tetap flat).
- Sisa satu-satunya: barang #8 gerbang font di server produksi — menunggu Boss mengunggah font berlisensi lalu menjalankan `periksa_font` di server.
- Larangan: tidak ada berkas font berlisensi/komersial yang masuk ke repo publik ini — dokumentasikan asal font dan sediakan pemeriksa jalur privat.

## Aturan ilustrasi buku (terkunci)

- Ilustrasi AI dibuat TANPA teks (model AI selalu merusak teks); label/judul dipasang sesudahnya di tahap desain.
- Gaya yang disukai Boss untuk isi buku umum: infografis edukasi 3D kartun (bukan line art — line art ditolak Boss 18 Okt 2026).
