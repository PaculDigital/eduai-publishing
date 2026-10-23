# 📄 BOOK CHAPTER — Spesifikasi Buku

> **Sumber:** skill `penelitian-ilmiah/book-chapter` — **diukur dari BAB 7 DOCX
> asli** (referensi Bos) pakai `python-docx`, bukan tebakan.
> **Status:** spesifikasi resmi per 22 Okt 2026.
> **Template induk:** `../templates/template-buku-resmi.docx`
> ⚠️ Book chapter **BUKAN** memakai 14 × 20 cm. Book chapter = **A5, Cambria**.

---

## 1. Identitas jenis

| Hal | Isi |
|---|---|
| Nama resmi | **Book Chapter** |
| ID dokumen | `book_chapter` |
| Definisi | **SATU bab** buku kolaborasi — bukan buku utuh |
| Pembeda utama | **maksimal 15 halaman A5** + glosarium tabel 2 kolom |
| ID alat | Jev/Hakim **MATI** (buku bukan naskah skripsi) |
| Cakupan | HANYA 1 bab sesuai permintaan |

---

## 2. Ukuran & tipografi — ANGKA RESMI (diukur dari DOCX asli)

| Elemen | Nilai | Catatan |
|---|---|---|
| **Ukuran halaman** | **A5 — 5,83″ × 8,27″** (148 × 210 mm) | ❌ tetap |
| **Margin** | **0,79″ = 2,0 cm semua sisi** | ❌ tetap |
| **Font isi (body)** | **Cambria 11 pt** | rata kanan-kiri (justified) |
| **Font judul BAB** | **Cambria 14 pt tebal**, rata tengah | **BUKAN 20 pt** ⚠️ |
| **Font Heading 1 (A–O)** | 14 pt tebal | **TANPA warna** — hitam biasa |
| **Font Heading 2 (1, 2, 3)** | 14 pt tebal | **TANPA warna** — hitam biasa |

### 🚨 KOREKSI PENTING — jangan tertukar

| Yang sering disangka | Yang BENAR |
|---|---|
| Judul BAB 20 pt | **14 pt tebal** |
| Spasi 1,15 | **`None` (default)** — BUKAN 1,15 |
| Heading berwarna #366091 | **hitam biasa, tanpa warna** |
| Space after paragraf 6 pt | **`None` (default)** |
| Judul BAB pakai style Heading | **style Normal**, set `runs[0].font.size.pt = 14` |

> Docstring skill menyebut *"spasi 1.15"* — itu **spasi bawaan dokumen**,
> bukan yang di-set per paragraf. Yang benar: `line_spacing = None`.

---

## 3. Indentasi — ANGKA PERSIS

| Elemen | `left_indent` | `first_line_indent` |
|---|---|---|
| Body paragraf | **0,5 cm** | **+1,0 cm** (menjorok masuk) |
| Learning objectives | **1,3 cm** | — (menjorok lebih dalam) |
| Bullet items | **1,0 cm** | **−0,5 cm** (gantung) |

### Spasi judul

| Elemen | `space_before` | `space_after` |
|---|---|---|
| Heading 1 | **6 pt** | **6 pt** |
| CV Penulis | **24 pt** (sebelum heading CV) | — |

---

## 4. Konversi ke twip (untuk generator `.docx`)

| Item | cm | twip |
|---|---|---|
| Lebar A5 | 14,8 | **8391** |
| Tinggi A5 | 21,0 | **11906** |
| Margin semua sisi | 2,0 | **1134** |
| Area teks (lebar) | 10,8 | **6123** |
| Body left indent | 0,5 | **284** |
| Body first line | 1,0 | **567** |
| Learning obj left | 1,3 | **738** |
| Bullet left | 1,0 | **567** |
| Bullet first line | −0,5 | **−284** |

> Rumus: `twip = cm ÷ 2,54 × 1440` — **pakai `ceil()`**, karena Word membulatkan ke atas.

### Ukuran font dalam setengah-poin (`w:sz`)

| Font | pt | `w:sz` |
|---|---|---|
| Body | 11 | **22** |
| Judul BAB | 14 | **28** |
| Heading 1 & 2 | 14 | **28** |

---

## 5. Struktur — 15 SECTION (A–O)

Book chapter punya **15 bagian berlabel huruf**, bukan bab bernomor:

```
A. Judul Bab (BAB N + judul, 14pt tebal, tengah)
B. Penulis
C. Abstrak
D. Kata Kunci
E. Pendahuluan
F. … (isi bab)
G. …
H. …
I. …
J. …
K. …
L. …
M. …
N. Referensi         ← PAGE BREAK sebelum ini
O. Glosarium         ← PAGE BREAK sebelum ini (TABEL 2 kolom)
```

### Aturan page break

| Bagian | Page break |
|---|---|
| Section **A–L** | ❌ **mengalir natural** (tanpa page break antar section) |
| Section **N (Referensi)** | ✅ **page break SEBELUM** |
| Section **O (Glosarium)** | ✅ **page break SEBELUM** |

> Ini ikut BAB 7 asli: `pbb = None` untuk semua section A–L.

---

## 6. Unsur khas WAJIB

| # | Unsur | Bentuk |
|---|---|---|
| 1 | **Glosarium** | **TABEL 2 KOLOM**: Istilah \| Definisi, header tebal, border single |
| 2 | **Learning objectives** | 11 pt, indentasi 1,3 cm |
| 3 | **CV Penulis** | style `No Spacing`, `space_before = 24 pt` |
| 4 | **Maksimal 15 halaman** | hanya untuk DOCX A5 |
| 5 | **PDF Turnitin** | **A4** — DILARANG diubah ke A5 |

### ⚠️ Dua aturan halaman yang BERBEDA

| Berkas | Ukuran | Batas 15 halaman |
|---|---|---|
| **DOCX book chapter** | **A5** (5,83″ × 8,27″) | ✅ **berlaku** |
| **PDF Turnitin** | **A4** (8,27″ × 11,69″) | ❌ **tidak berlaku** |

> PDF Turnitin **DILARANG** diubah ke A5 — itu standar laporan Turnitin resmi.

---

## 7. Yang DILARANG

| Dilarang | Alasan |
|---|---|
| Judul BAB 20 pt | salah baca, yang benar 14 pt |
| Spasi 1,15 eksplisit | yang benar `None` (default) |
| Heading berwarna (#366091 / #4F81BD) | harus hitam biasa |
| PDF Turnitin diubah ke A5 | standar Turnitin = A4 |
| Membuat buku utuh multi-bab | book chapter = **1 bab** |
| Page break antar section A–L | harus mengalir |
| Memakai template 14×20 cm | **book chapter = A5** |
| Mengklaim "selesai" karena exit code 0 | WAJIB verifikasi hasil |

---

## 8. Perbedaan dengan jenis lain

| Jenis | Ukuran | Font isi | Judul | Pembeda isi |
|---|---|---|---|---|
| **Book chapter** | **A5** | **Cambria 11** | Cambria **14** | **1 bab, maks 15 hlm, glosarium tabel** |
| Monograf | A5 | Cambria 11 | Cambria 14 | satu penelitian + novelty |
| Buku referensi | B5 | TNR 12 | TNR 16 | indeks subjek + nama |
| Buku ajar OBE | B5/A5 | TNR 12 | TNR 16 | TIU/TIK + Latihan |
| Buku umum | B5 | TNR 12 | — | naratif populer |
| Template induk | 14×20 | Palatino 10 | Trajan Pro 22 | wajah penerbit |

> 📌 **Monograf & book chapter paling mirip** (A5, Cambria 11, judul 14 pt).
> Bedanya: monograf 150–180 halaman + novelty; book chapter 1 bab + maks 15 halaman + glosarium tabel.

---

## 9. Yang perlu diuji sebelum dipakai produksi

| # | Uji | Status |
|---|---|---|
| 1 | `periksa_buku_template.py` bisa menerima profil A5 + Cambria | ✅ 23 Okt 2026 (gerbang khusus `periksa_book_chapter.py` C1) |
| 2 | Gerbang memeriksa judul BAB = **14 pt** (bukan 20) | ✅ C2 |
| 3 | Gerbang memeriksa `line_spacing = None` (bukan 1,15) | ✅ C3b |
| 4 | Gerbang memeriksa heading TANPA warna | ✅ C4 |
| 5 | Gerbang memeriksa glosarium = **TABEL 2 kolom** | ✅ C6 |
| 6 | Gerbang memeriksa batas 15 halaman | ✅ C7 (render) |
| 7 | Uji bergigi: judul BAB diubah ke 20 pt → GAGAL | ✅ `uji_bergigi_v6.py` 5/5 |

---

## 10. Catatan jujur

- Angka di sini **diukur dari DOCX BAB 7 asli** — paling terpercaya dari semua jenis.
- **Tapi** buku chapter tidak selalu identik: tiap buku kolaborasi bisa punya template penerbit sendiri. Angka BAB 7 = **acuan default**, bukan hukum mutlak.
- **Batas 15 halaman** bergantung jumlah kata. 15 halaman A5 Cambria 11 pt ≈ **5.000–6.000 kata**. Perlu ukur nyata.
- Template `.docx` book chapter **belum ada berkasnya** — baru spesifikasi.
