# 📕 MONOGRAF — Spesifikasi Buku

> **Sumber:** skill `penelitian-ilmiah/buku-monograf` (bukan tebakan).
> **Status:** spesifikasi resmi per 22 Okt 2026.
> **Template induk:** `../templates/template-buku-resmi.docx`
> ⚠️ Monograf **BUKAN** memakai ukuran template induk. Monograf = **A5**.

---

## 1. Identitas jenis

| Hal | Isi |
|---|---|
| Nama resmi | **Buku Monograf** |
| ID dokumen | `buku_monograf` |
| Definisi | Buku dari **satu penelitian** (skripsi/tesis/jurnal/laporan riset) — satu topik, satu temuan |
| Pembeda utama | **NOVELTY WAJIB** — harus ada kebaruan yang dinyatakan tegas |
| ID alat | Jev/Hakim **MATI** (buku bukan naskah skripsi) |

---

## 2. Ukuran & tipografi — ANGKA RESMI

| Item | Nilai | Sifat |
|---|---|---|
| **Ukuran halaman** | **A5 — 14,8 × 21,0 cm** | ❌ tetap |
| **Margin (semua sisi)** | **2,0 cm** | ❌ tetap |
| **Font isi (body)** | **Cambria 11 pt** | ❌ tetap |
| **Font judul bab** | **Cambria 14 pt tebal** | ❌ tetap |
| **Spasi baris** | **1,15** | ❌ tetap |
| **Target halaman** | **150–180 halaman** | ✅ fleksibel |

### Konversi ke twip (untuk generator `.docx`)

| Item | cm | twip |
|---|---|---|
| Lebar A5 | 14,8 | **8391** |
| Tinggi A5 | 21,0 | **11906** |
| Margin atas | 2,0 | **1134** |
| Margin bawah | 2,0 | **1134** |
| Margin kiri | 2,0 | **1134** |
| Margin kanan | 2,0 | **1134** |
| Area teks (lebar) | 10,8 | **6123** |

> Rumus: `twip = cm ÷ 2,54 × 1440`. Contoh: 14,8 ÷ 2,54 × 1440 = **8391**.

### Ukuran font dalam setengah-poin (`w:sz`)

| Font | pt | `w:sz` |
|---|---|---|
| Isi (body) | 11 | **22** |
| Judul bab | 14 | **28** |

---

## 3. Struktur wajib

```
1. Sampul
2. Halaman Judul
3. Halaman Hak Cipta / ISBN
4. Prakata
5. Daftar Isi
6. Daftar Tabel (bila ada)
7. Daftar Gambar (bila ada)
8. Daftar Singkatan (bila ada)
9. BAB 1  Pendahuluan        — latar belakang, rumusan, tujuan, manfaat
10. BAB 2 Tinjauan Pustaka   — kerangka teori, penelitian terdahulu
11. BAB 3 Metode Penelitian
12. BAB 4 Hasil dan Pembahasan
13. BAB 5 Simpulan & Saran
14. Daftar Pustaka           — APA 7, indentasi gantung
15. Glosarium                — dianjurkan
16. Indeks                    — dianjurkan
17. Tentang Penulis
18. Sinopsis / Cover Belakang (opsional)
```

Target bab: **8 bab** (bisa 5–8 tergantung isi penelitian).

---

## 4. Unsur WAJIB yang tidak boleh hilang

| # | Unsur | Kenapa wajib |
|---|---|---|
| 1 | **Pernyataan NOVELTY** | pembeda monograf dari laporan biasa |
| 2 | **Kebaruan ditulis tegas** di Bab 4 atau Bab 5 | bukan tersirat |
| 3 | **Daftar Pustaka APA 7** + indentasi gantung | standar akademik |
| 4 | **Keterbatasan penelitian** | kejujuran ilmiah |
| 5 | **Sitasi terverifikasi** | dilarang mengarang |

---

## 5. Yang DILARANG

| Dilarang | Alasan |
|---|---|
| Memakai A4 | bukan ukuran buku |
| Memakai font selain Cambria | standar skill |
| Mengarang sitasi | pelanggaran akademik |
| Novelty kosong / samar | gagal definisi monograf |
| Memakai template 14×20 cm | **monograf = A5** |

---

## 6. Perbedaan dengan jenis lain

| Jenis | Ukuran | Font isi | Pembeda isi |
|---|---|---|---|
| **Monograf** | **A5** | **Cambria 11** | **satu penelitian + novelty** |
| Buku referensi | B5 | TNR 12 | indeks subjek + nama, tabel komparasi teori |
| Buku ajar OBE | B5 (default) | TNR 12 | TIU/TIK, Latihan, Checklist |
| Buku umum | B5 | TNR 12 | naratif populer |
| Template induk Bayana | 14×20 | Palatino 10 | wajah penerbit |

---

## 7. Yang perlu diuji sebelum dipakai produksi

| # | Uji | Status |
|---|---|---|
| 1 | `periksa_buku_template.py` bisa menerima profil A5 + Cambria | ⬜ belum |
| 2 | Gerbang membaca profil per jenis (bukan angka mati) | ⬜ belum |
| 3 | Uji bergigi: ukuran A5 diubah → gerbang GAGAL | ⬜ belum |
| 4 | Uji bergigi: font Cambria diubah → gerbang GAGAL | ⬜ belum |

---

## 8. Catatan jujur

- Spesifikasi ini **disalin dari skill**, bukan diukur dari `.docx` jadi. Template monograf **belum ada berkasnya**.
- Untuk membuat berkas template monograf yang sah, harus dibuat dari template induk + diubah ke A5/Cambria, lalu **diverifikasi gerbang**.
- Nomor halaman di daftar isi monograf 150–180 halaman **lebih panjang** dari template induk — perlu uji tersendiri.
