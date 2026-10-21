# ✅ PUTUSAN LENGKAP — 9 PERTANYAAN DISKUSI JURNAL & WORKSPACE (06 Okt 2026)

<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Jawaban terakhir Bos 06 Okt 2026 (verbatim):
> *"1. A · 6. A max 8 artikel per bab"*
>
> Status: **SEMUA 9 TERJAWAB & TERKUNCI.** Belum dikoding.

---

## 🔒 TABEL PUTUSAN LENGKAP (9/9)

| # | Pertanyaan | Putusan Bos |
|---|---|---|
| 1 | Workspace: satu tingkat atau bersarang? | ✅ **A = SATU TINGKAT** |
| 2 | Artikel ditandai "untuk BAB berapa"? | ✅ **YA** |
| 3 | Porsi 30% dihitung **per bab**? | ✅ **YA** |
| 4 | Auto AI: tampilkan artikel **sebelum bayar**? | ✅ **YA** |
| 5 | "Tambah manual" gratis atau token? | ✅ **OK** |
| 6 | AI gagal total → porsi dilonggarkan? | ✅ **A = DILONGGARKAN, MAKS 8 ARTIKEL per bab** |
| 7 | Artikel belum terverifikasi? | ✅ **DITAMPILKAN + user masukkan DOI-nya** |
| 8 | Artikel dipakai ulang di bab lain? | ✅ **YA** |
| 9 | Sumber artikel manual? | ✅ **HANYA mesin resmi + DOI sendiri** |

---

## 🎯 KONSEKUENSI No.1 — WORKSPACE SATU TINGKAT

Sesuai kode yang **sudah ada** (`models.py`) — **TIDAK ada perubahan model**:
```
📁 Skripsi Saya
   ├── 📄 Bab 1.docx
   ├── 📄 Bab 2.docx
   └── 📄 link-jurnal.txt

📁 Makalah Semester 7
   └── 📄 Bab 1.docx
```
⇒ **Nol tabel baru, nol perubahan skema.** Aturan tertulis di kode *"user HP
mudah bingung"* → **dipertahankan**. Bos **tidak** minta bersarang.

---

## 🎯 KONSEKUENSI No.6 — PORSI ARTIKEL MANUAL (2 aturan)

| Keadaan | Batas artikel manual per bab |
|---|---|
| **AI dapat artikel** (normal) | **30%** dari total |
| **AI GAGAL TOTAL** (0 artikel) | **MAKS 8 artikel** (batas tetap) |

### 🔍 Perlu dicatat: ada "zona tengah" yang Wulan belum tanyakan
Aturan di atas menutup **2 ujung** (normal & gagal total). Tapi ada **zona
tengah**: AI dapat **sedikit** (mis. 2 artikel).

| Keadaan | Aturan mana yang dipakai? |
|---|---|
| AI dapat 12 artikel | 30% → maks ±5 manual |
| AI dapat 2 artikel | 30%?? (2+manual; 30% → ±1) **atau** batas 8? |
| AI dapat 0 artikel | ✅ **batas 8** (putusan Bos) |

⚠️ **Konsekuensi kalau 30% dipakai kaku di zona tengah:**
- AI dapat **2** artikel → maks manual = **1** ⇒ user hampir tidak bisa menambah
- AI dapat **1** artikel → maks manual = **1** (masih ketat)

⇒ **Wulan perlu tanya Bos 1 hal**: apakah **selalu ada lantai (minimum) 8**
atau **semakin sedikit artikel AI, semakin longgar**?

### 💡 Usul Wulan (belum diputuskan) — "aturan bertingkat"
```
AI dapat ≥ 20 artikel  → maks manual = 30%  (±8)
AI dapat 5-19 artikel  → maks manual = 8
AI dapat 0-4 artikel   → maks manual = 8  (lantai tetap)
```
⇒ **Sederhananya: maks manual = 8 SELALU, kecuali 30% lebih kecil** — tapi
kalau 30% lebih kecil, user bisa terkunci.
**ALTERNATIF lebih sederhana: maks manual = 8 selalu** (tidak pakai 30% sama
sekali kalau jumlahnya di bawah).

⇒ Ini **perlu keputusan Bos** — Wulan tidak memutuskan sendiri.

---

## 📊 PUTUSAN LENGKAP SESI (rekap dari awal sampai akhir)

### 🏗️ Workspace
| Hal | Putusan |
|---|---|
| Bisa? | ✅ BISA — `folders` sudah ada |
| Bentuk | ✅ **A = SATU TINGKAT** (tidak bersarang) |

### 📚 Harvest Jurnal
| Hal | Putusan |
|---|---|
| Mesin | ✅ `pustaka.py` sudah live (4 sumber + audit DOI) |
| Unduh PDF | ✅ terbukti bisa (uji nyata: 406 KB `%PDF`) |
| Link | ✅ ada link nyata (Garuda/DOI) |

### 🔎 Pencarian MANUAL
| Hal | Putusan |
|---|---|
| Harga | ✅ 1 token per pencarian |
| Gratis | ✅ 2× per minggu |
| Siklus | ✅ sejak awal pemakaian |
| Takaran | ✅ 1 pencarian = 1 judul/keyword |
| Yang dihitung | ✅ manual saja |

### 🤖 Auto AI
| Hal | Putusan |
|---|---|
| Biaya | ✅ GRATIS sampai kerangka |
| Kapan | ✅ saat tombol ditekan |
| Jatah 2×/minggu | ✅ TIDAK (mekanisme sendiri) |
| Tampilkan artikel sebelum bayar | ✅ YA |

### 📝 Artikel Manual
| Hal | Putusan |
|---|---|
| Masuk daftar pustaka | ✅ YA (asal lolos audit) |
| Dipakai sitasi | ✅ YA |
| Bentuk masuk | ✅ 2 cara (mesin resmi + DOI sendiri) |
| Upload PDF liar | ❌ DILARANG |
| Porsi | ✅ 30% per bab; gagal total → maks 8 |
| Penanda bab | ✅ YA |
| Pakai ulang | ✅ YA |
| Belum terverifikasi | ✅ ditampilkan + user isi DOI |

### 🧭 Jev
| Hal | Putusan |
|---|---|
| Di fitur jurnal | ❌ TIDAK PERLU (bidang beda + zona gagal) |
| Di struktur naskah | ✅ sudah jalan (`ai.py:2350`) |

---

## ❓ SATU HAL YANG MASIH PERLU KEPUTUSAN BOS

**Zona tengah porsi artikel manual** (No.6 lanjutan):
AI dapat **sedikit** artikel (1-4) — pakai 30% (bisa terkunci) atau **lantai 8**?

| Pilihan | Artinya |
|---|---|
| **A. Lantai 8 selalu** | maks manual = 8, kecuali 30% lebih besar ⭐ (usul Wulan) |
| **B. 30% kaku** | AI dapat 2 → maks manual 1 (ketat) |
| **C. Bertingkat** | ≥20 artikel AI → 30%; kurang dari itu → 8 |

---

## 📁 BERKAS
Semua di `/opt/data/services/eduai-publishing/` — **24 berkas**:
- **Ringkasan:** `RINGKASAN_DISKUSI_JURNAL_06OKT2026.md`
- **9 pertanyaan:** `JAWABAN_BOS_9_PERTANYAAN_06OKT2026.md`
- **Putusan (5):** `PUTUSAN_*_06OKT2026.md`
- **Catatan (6):** `CATATAN_*_06OKT2026.md`
- **IDE (11):** `IDE_*_06OKT2026.md`
- **Jawaban (2):** `JAWABAN_*_06OKT2026.md`

---

## ⚠️ STATUS
- **9/9 PUTUSAN TERKUNCI** ✅
- **DILARANG DIKODING** — menunggu perintah Bos
- **Nol baris kode** ditulis dari sesi diskusi ini
