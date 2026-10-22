# 📘 BUKU REFERENSI — Spesifikasi Buku

> **Sumber:** skill `penelitian-ilmiah/buku-referensi` (bukan tebakan).
> **Status:** spesifikasi resmi per 22 Okt 2026.
> **Template induk:** `../templates/template-buku-resmi.docx`
> ⚠️ Buku referensi **BUKAN** memakai ukuran template induk. Buku referensi = **B5**.

---

## 1. Identitas jenis

| Hal | Isi |
|---|---|
| Nama resmi | **Buku Referensi** |
| ID dokumen | `buku_referensi` |
| Definisi | Buku rujukan ilmiah: definisi baku, peta teori, posisi penulis, indeks, sitasi terverifikasi |
| Pembeda utama | **INDEKS SUBJEK + INDEKS NAMA — WAJIB** |
| ID alat | Jev/Hakim **MATI** (buku bukan naskah skripsi) |

---

## 2. Ukuran & tipografi — ANGKA RESMI

| Item | Nilai | Sifat |
|---|---|---|
| **Ukuran halaman** | **B5 — 17,6 × 25,0 cm** | ❌ tetap (alternatif A5 ditolak default) |
| **Margin (semua sisi)** | **2,0 cm** | ❌ tetap |
| **Font isi (body)** | **Times New Roman 12 pt** | ⚠️ WAJIB tanya Bos dulu |
| **Spasi baris** | **1,15** | boleh 1,15 |
| **Target halaman** | **150+ halaman** | fleksibel 8–12 bab |

### Konversi ke twip (untuk generator `.docx`)

| Item | cm | twip |
|---|---|---|
| Lebar B5 | 17,6 | **9978** |
| Tinggi B5 | 25,0 | **14173** |
| Margin atas | 2,0 | **1134** |
| Margin bawah | 2,0 | **1134** |
| Margin kiri | 2,0 | **1134** |
| Margin kanan | 2,0 | **1134** |
| Area teks (lebar) | 13,6 | **7710** |

> Rumus: `twip = cm ÷ 2,54 × 1440`. Contoh: 17,6 ÷ 2,54 × 1440 = **9978**.

### Ukuran font dalam setengah-poin (`w:sz`)

| Font | pt | `w:sz` |
|---|---|---|
| Isi (body) | 12 | **24** |

> ⚠️ Font judul bab **tidak ditetapkan** skill buku-referensi. Wulan usul
> **Times New Roman 16 pt tebal** (`w:sz` **32**) — **perlu pengesahan Bos**.

---

## 3. Struktur wajib

```
1. Sampul
2. Halaman Judul
3. Halaman Hak Cipta / ISBN
4. Prakata
5. Daftar Isi
6. Daftar Tabel
7. Daftar Gambar
8. BAB 1 Pendahuluan     — peta buku, ruang lingkup, batasan, istilah kunci
9. BAB 2 … BAB N         — teori & pembahasan sistematis
   └── tiap bab wajib punya sub-bab N.3: TABEL KOMPARASI TEORI
10. BAB terakhir         — sintesis & posisi penulis
11. Daftar Pustaka       — APA 7
12. Glosarium            — dianjurkan
13. Indeks Subjek        — WAJIB
14. Indeks Nama          — WAJIB
15. Tentang Penulis
```

Target bab: **8–12 bab**, minimal **150 halaman**.

---

## 4. Unsur WAJIB yang tidak boleh hilang

| # | Unsur | Kenapa wajib |
|---|---|---|
| 1 | **Indeks Subjek** ber-nomor halaman | pembeda utama buku referensi |
| 2 | **Indeks Nama** ber-nomor halaman | pembeda utama buku referensi |
| 3 | **Tabel komparasi teori per bab** | tokoh, tahun, proposisi inti, kekuatan, keterbatasan |
| 4 | **Posisi penulis** dinyatakan tegas | bukan cuma merangkum |
| 5 | **Sitasi terverifikasi** | dilarang mengarang |
| 6 | **Glosarium** | dianjurkan kuat |

### Mesin indeks sudah ada

`scripts/indeks_referensi.py`:
```
kumpulkan_entri(teks_per_halaman, glosarium, min_muncul=2, maks_halaman=6)
tulis_indeks_subjek(doc, subjek)   # kelompok abjad, nomor rata kanan
tulis_indeks_nama(doc, nama)
```
⚠️ **Nomor halaman = PERKIRAAN** (360 kata/halaman). Cukup untuk digital/pratinjau; **cetak final wajib render Word dulu**.

---

## 5. Yang DILARANG

| Dilarang | Alasan |
|---|---|
| Buku referensi tanpa indeks | gagal definisi sendiri |
| Memakai A4 | bukan ukuran buku |
| Mengarang sitasi | pelanggaran akademik |
| Memakai template 14×20 cm | **referensi = B5** |
| Anekdot pembuka gaya populer | ini buku ilmiah, bukan buku umum |

---

## 6. Perbedaan dengan jenis lain

| Jenis | Ukuran | Font isi | Pembeda isi |
|---|---|---|---|
| **Buku referensi** | **B5** | **TNR 12** | **indeks subjek + nama, tabel komparasi teori** |
| Monograf | A5 | Cambria 11 | satu penelitian + novelty |
| Buku ajar OBE | B5 (default) | TNR 12 | TIU/TIK, Latihan, Checklist |
| Buku umum | B5 | TNR 12 | naratif populer, tanpa indeks |
| Template induk Bayana | 14×20 | Palatino 10 | wajah penerbit |

---

## 7. Yang perlu diuji sebelum dipakai produksi

| # | Uji | Status |
|---|---|---|
| 1 | `periksa_buku_template.py` bisa menerima profil B5 + TNR 12 | ⬜ belum |
| 2 | Gerbang memeriksa indeks subjek & nama ada | ⬜ belum |
| 3 | Gerbang memeriksa tabel komparasi per bab | ⬜ belum |
| 4 | Uji bergigi: B5 diubah → gerbang GAGAL | ⬜ belum |

---

## 8. Catatan jujur

- Spesifikasi **disalin dari skill**. Template `.docx` buku referensi **belum ada berkasnya**.
- Font judul bab **belum ditetapkan** skill → Wulan usul TNR 16 pt, **perlu ACC Bos**.
- Indeks ber-nomor halaman **belum akurat untuk cetak** (masih perkiraan).
