# 📌 SOT INDUK — BUKU EduAi

> **SINGLE SOURCE OF TRUTH.** Kalau ragu soal buku, baca berkas ini dulu.
> Berkas ini hanya **menunjuk** ke tempat yang benar — tidak menyalin isinya
> (supaya tidak lahir sumber kedua).

**Diukur & disahkan:** 22 Oktober 2026 · `main` = `e99478e`

---

## 1. PETA — mana yang BENAR, mana yang MATI

| Pertanyaan | Jawaban BENAR | Berkas |
|---|---|---|
| Ukuran & font buku 14×20 | **template induk** | `template-buku-resmi/templates/` |
| Ukuran & font monograf/referensi/ajar/chapter | **spesifikasi per jenis** | `template-buku-resmi/jenis/*/SPESIFIKASI.md` |
| Cara merakit `.docx` | **generator + gerbang 57 asersi** | `template-buku-resmi/scripts/` |
| Blok gaya ilustrasi | **`jenis_buku.PAKET[jenis]["ilustrasi"]`** | **`gambar-dan-visual/SOT-BLOK-GAYA.md`** |
| Bentuk diagram | **`diagram_buku.py`** (8 bentuk SVG) | `gambar-dan-visual/TABEL-DIAGRAM-INFOGRAFIS.md` |
| Cara review/mutu | **skill agen kolaborator** | `skill-agen-kolaborator/SKILL.md` |
| Nilai angka twip | **tabel di README jenis** | `template-buku-resmi/jenis/README.md` §3 |

---

## 2. 🗑️ YANG SUDAH DIBUANG — jangan dipakai lagi

| Yang dibuang | Tanggal | Pengganti |
|---|---|---|
| `brief_visual.STYLE_BUKU['anak']` (518 char) | 22 Okt 2026 | `jenis_buku.PAKET['anak']['ilustrasi']` (571 char) |
| Folder `template-buku-resmi/` di branch `fase4-rapi` | 22 Okt 2026 | `main` (sudah merge) |
| Branch `agen/wulan/template-buku-generator` | 22 Okt 2026 | `main` (`f1da9bf` sudah merge) |

> ⚠️ **`STYLE_BUKU['anak']` JANGAN ditambahkan kembali.** Gerbang
> `gerbang_placeholder_brief` sekarang 19 asersi karena entri itu sudah tidak ada.

---

## 3. ✅ 4 GAYA di `STYLE_BUKU` — JANGAN dibuang

| Gaya | Dipakai untuk |
|---|---|
| `premium-konseptual` | **buku umum (default)** |
| `editorial-lineart` | pilihan gaya lain |
| `woodcut` | pilihan gaya lain |
| `flat-editorial` | pilihan gaya lain |

> 4 gaya ini **HIDUP**. Hanya `anak` yang dibuang. Membuang semuanya = buku umum
> tidak punya gaya sama sekali.

---

## 4. ATURAN TETAP — 5 hal yang tidak boleh dilanggar

| # | Aturan | Kenapa |
|---|---|---|
| **1** | Blok gaya ditulis **di satu tempat**: `jenis_buku.PAKET[jenis]["ilustrasi"]` | dua salinan = sumber kebingungan |
| **2** | Setiap blok gaya **WAJIB** punya `{brief}` | tanpa itu AI mengarang isi gambar |
| **3** | Angka cm → twip pakai **`ceil()`**, bukan `round()` | Word membulatkan ke atas |
| **4** | DAFTAR PUSTAKA = **WAJIB** (putusan Bos) | template resmi DILENGKAPI |
| **5** | Font berlisensi: **0/9 = JUJUR**, bukan bug | Bos punya lisensi, akan unggah |

---

## 5. Status jujur — apa yang BELUM

| # | Belum | Akibat kalau dipakai sekarang |
|---|---|---|
| 1 | **Berkas template A5** | monograf & chapter tetap keluar 14×20 (**SALAH**) |
| 2 | **Berkas template B5** | referensi, ajar, umum tetap keluar 14×20 |
| 3 | **`profil.json` per jenis** | gerbang belum bisa baca angka per jenis |
| 4 | **Spesifikasi buku-umum** (termasuk tone anak) | belum ada di repo |
| 5 | **Font terpasang** | tampilan bergeser di mesin tanpa font |
| 6 | **Infografis** | tidak ada mesinnya |
| 7 | **Tone monograf/ajar** | tidak ada — jatuh ke tone `umum` ("Anda") |

---

## 6. Alur produksi yang BENAR

```
naskah (md/txt/json)
        ↓
   generator v2  ←── gerbang 57 asersi
        ↓
    .docx
        ↓
   periksa_font.py (9 font)
        ↓
   mata manusia
```

**Generator TIDAK menulis isi.** Dia merakit. Yang menulis isi = mesin buku
(`buku_umum_pipeline.py`, ~138 panggilan AI, ~36 menit).

---

## 7. Struktur repo — di mana mencari apa

```
template-buku-resmi/
├── README.md                  ← template induk 14×20 (angka wajib)
├── templates/*.docx           ← berkas template ASLI
├── scripts/                   ← generator + gerbang 57 asersi + uji bergigi
├── references/                ← fakta terukur + catatan Jev
└── jenis/                     ← ⬇️ per jenis buku
    ├── README.md              ← tabel perbandingan + angka twip
    ├── monograf/              ← A5, Cambria 11
    ├── buku-referensi/        ← B5, TNR 12
    ├── buku-ajar-obe/         ← B5/A5, TNR 12, TIU/TIK
    └── book-chapter/          ← A5, Cambria 11, maks 15 hlm

mutu-buku/
├── SOT-INDUK.md               ← ⬅️ BERKAS INI
├── README.md                  ← cara kerja review (6 langkah)
├── skill-agen-kolaborator/    ← skill lengkap (26 berkas)
└── gambar-dan-visual/
    ├── SOT-BLOK-GAYA.md       ← ⬅️ SOT blok gaya ilustrasi
    ├── README.md              ← ilustrasi anak vs umum
    ├── TABEL-DIAGRAM-INFOGRAFIS.md
    ├── kode/                  ← salinan persis 3 modul
    └── prompt/                ← blok gaya, 8 diagram, brief, larangan
```

---

## 8. Ringkas satu kalimat

> **Template: `template-buku-resmi/`. Jenis: `jenis/*/SPESIFIKASI.md`.
> Blok gaya ilustrasi: `jenis_buku.PAKET`. Mutu: `skill-agen-kolaborator/`.
> Yang sudah dibuang: `STYLE_BUKU['anak']`.**

---

*SOT induk dibuat Wulan 22 Oktober 2026. Semua angka dari kode hidup.*
