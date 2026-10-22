# 📗 BUKU AJAR OBE — Spesifikasi Buku

> **Sumber:** skill `penelitian-ilmiah/buku-ajar-obe` (bukan tebakan).
> **Status:** spesifikasi resmi per 22 Okt 2026.
> **Template induk:** `../templates/template-buku-resmi.docx`
> ⚠️ Buku ajar **BUKAN** memakai ukuran template induk. Buku ajar = **B5 default / A5 pilihan**.

---

## 1. Identitas jenis

| Hal | Isi |
|---|---|
| Nama resmi | **Buku Ajar berbasis OBE** |
| ID dokumen | `buku_ajar` |
| Definisi | Buku ajar dari **RPS OBE** — ada TIU/TIK, Latihan, Checklist |
| Pembeda utama | **TIU/TIK per bab + Latihan + Checklist** |
| ID alat | Jev/Hakim **MATI** (buku bukan naskah skripsi) |

---

## 2. Ukuran & tipografi — ANGKA RESMI

| Item | Nilai | Sifat |
|---|---|---|
| **Ukuran halaman** | **B5 default** (17,6 × 25,0 cm) · **A5** bila dominan teks | ⚠️ **WAJIB A5 atau B5 — DILARANG A4** |
| **Margin (semua sisi)** | **2,0 cm** | ❌ tetap |
| **Font isi (body)** | **Times New Roman 12 pt** | ❌ tetap |
| **Font TIU/TIK** | **TNR 9 pt miring** | ❌ tetap |
| **Font judul bab** | **TNR 16 pt** | ❌ tetap |
| **Spasi baris** | **1,15** | dari assembly |
| Indentasi gantung (daftar) | `left_indent=0,6 cm`, `first_line_indent=−0,6 cm` | putusan Bos 17 Agu 2026 |
| Font daftar | TNR **11 pt**, `space_before/after=3pt`, `line_spacing=1,15` | dari assembly |

### Aturan memilih ukuran

| Ukuran | Kapan dipakai |
|---|---|
| **B5** (default) | buku **banyak tabel/gambar/diagram** — lebih aman |
| **A5** | buku **dominan teks naratif**, minim visual |

> Bos bisa override: *"pakai A5"* atau *"pakai B5"*.

### Konversi ke twip (untuk generator `.docx`)

| Item | cm | twip |
|---|---|---|
| Lebar B5 | 17,6 | **9978** |
| Tinggi B5 | 25,0 | **14173** |
| Lebar A5 | 14,8 | **8391** |
| Tinggi A5 | 21,0 | **11906** |
| Margin semua sisi | 2,0 | **1134** |
| Area teks B5 | 13,6 | **7710** |
| Area teks A5 | 10,8 | **6123** |
| Indentasi gantung | 0,6 | **340** |

> Rumus: `twip = cm ÷ 2,54 × 1440`.

### Ukuran font dalam setengah-poin (`w:sz`)

| Font | pt | `w:sz` |
|---|---|---|
| Isi (body) | 12 | **24** |
| Judul bab | 16 | **32** |
| TIU/TIK | 9 | **18** |
| Daftar | 11 | **22** |

---

## 3. Struktur wajib

```
1. Sampul
2. Halaman Judul
3. Halaman Hak Cipta / ISBN
4. Prakata
5. Daftar Isi
6. Daftar Tabel / Gambar
7. CAPAIAN PEMBELAJARAN LULUSAN (CPL)
8. CAPAIAN PEMBELAJARAN MATA KULIAH (CPMK)
9. BAB 1 … BAB N
   └── tiap bab WAJIB punya:
       · TIU (Tujuan Instruksional Umum)   — TNR 9pt miring
       · TIK (Tujuan Instruksional Khusus) — TNR 9pt miring
       · Uraian materi
       · LATIHAN
       · CHECKLIST
       · RANGKUMAN
10. Daftar Pustaka
11. Glosarium
12. Indeks (dianjurkan)
13. Tentang Penulis
```

---

## 4. Unsur WAJIB per bab

| # | Unsur | Gaya |
|---|---|---|
| 1 | **TIU** | TNR 9 pt miring |
| 2 | **TIK** | TNR 9 pt miring |
| 3 | **Uraian materi** | TNR 12 pt |
| 4 | **Latihan** | daftar bernomor |
| 5 | **Checklist** | daftar centang |
| 6 | **Rangkuman** | paragraf isi |

### Hubungan dengan RPS OBE

Buku ajar **diturunkan dari RPS OBE**:
```
RPS OBE  →  outline bab  →  approve Bos  →  generate bab  →  .docx
```
⚠️ Tanpa RPS, ini bukan buku ajar OBE — itu buku umum.

---

## 5. Yang DILARANG

| Dilarang | Alasan |
|---|---|
| Memakai **A4** atau ukuran lain | aturan skill tegas |
| Bab tanpa TIU/TIK | gagal definisi buku ajar |
| Bab tanpa Latihan | gagal definisi buku ajar |
| Memakai template 14×20 cm | **buku ajar = A5/B5** |
| Menjanjikan gambar/foto otomatis | jujur soal batasan |

---

## 6. Perbedaan dengan jenis lain

| Jenis | Ukuran | Font isi | Pembeda isi |
|---|---|---|---|
| **Buku ajar OBE** | **B5/A5** | **TNR 12** | **TIU/TIK + Latihan + Checklist, dari RPS** |
| Monograf | A5 | Cambria 11 | satu penelitian + novelty |
| Buku referensi | B5 | TNR 12 | indeks subjek + nama |
| Buku umum | B5 | TNR 12 | naratif populer, tanpa TIU/TIK |
| Template induk Bayana | 14×20 | Palatino 10 | wajah penerbit |

---

## 7. Yang perlu diuji sebelum dipakai produksi

| # | Uji | Status |
|---|---|---|
| 1 | `periksa_buku_template.py` bisa menerima profil B5/A5 + TNR 12 | ⬜ belum |
| 2 | Gerbang memeriksa TIU + TIK ada di tiap bab | ⬜ belum |
| 3 | Gerbang memeriksa Latihan + Checklist ada | ⬜ belum |
| 4 | Gerbang memeriksa indentasi gantung 0,6 cm | ⬜ belum |
| 5 | Uji bergigi: TIU dihapus → gerbang GAGAL | ⬜ belum |

---

## 8. Catatan jujur

- Spesifikasi **disalin dari skill + koreksi assembly**. Template `.docx` buku ajar **belum ada berkasnya**.
- Skill menyebut `TIU/TIK 9 pt miring` tapi assembly menyebut daftar `TNR 11 pt` — **dua angka berbeda**, keduanya sah untuk keperluan berbeda (TIU/TIK vs daftar isi bab). Jangan disamakan.
- Hanging indent 0,6 cm adalah **putusan Bos 17 Agu 2026** — jangan diubah tanpa ACC.
