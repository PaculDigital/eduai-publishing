# 🎨 GAMBAR & VISUAL BUKU — Ilustrasi Anak vs Umum

> **Untuk Bos perbaiki.** Semua isi di sini **diambil langsung dari kode**, bukan
> ditulis ulang dari ingatan. Kalau ada yang salah, salahnya ada di kode — dan
> itulah yang perlu Bos betulkan.
>
> Diukur 22 Oktober 2026.

---

## 1. Dua wajah buku, dua gaya gambar

| | **Buku ANAK** | **Buku UMUM (dewasa)** |
|---|---|---|
| Gaya | `anak` | `premium-konseptual` (default) |
| Mode brief | **`literal`** | **`konseptual`** |
| Yang digambar | **adegan nyata** dari bab | **metafora** dari gagasan bab |
| Latar | **PUTIH murni** `#FFFFFF` | **PUTIH murni** `#FFFFFF` |
| Garis tepi | **outline gelap tegas** | garis tipis tajam |
| 3D / fotorealistis | **DILARANG** | **DILARANG** |
| Teks di gambar | **DILARANG** | **DILARANG** |

---

## 2. Buku ANAK — blok gaya lengkap

```text
Children's educational illustration, clean flat cartoon style,
clear dark outlines around every shape, simple rounded forms,
cheerful but controlled colors, on a clean PURE WHITE background
(hex #FFFFFF), no cream, no beige, no blue tint,
no gradient background, no vignette, no paper texture, no grain,
no shadows on the background, no gradients on objects,
no 3D render, no photorealism,
no text, no words, no letters, no numbers, no watermark.
SCENE — illustrate EXACTLY this moment, nothing else: {brief}.
The scene above is the SUBJECT; keep every object named in it
```

**518 karakter.** Punya `{brief}`: **YA** ✅

### Kenapa begitu — riwayat nyata

Versi lama menulis `light blue background` + `smiling sun character` + `3D render`.
Akibatnya **terukur**:

| Masalah | Akibat |
|---|---|
| `light blue background` | PNG **biru bergradasi**, tanpa outline |
| `smiling sun character` | matahari berwajah muncul di **SETIAP** gambar |
| `3D render` | terlihat seperti plastik, bukan buku anak |

Lalu diubah atas **perintah Bos (verbatim)**:
> *"Gambar ilustrasi background putih saja ada outline, daripd sekarang
> background coklat muda, seperti buku kuno/lawas dan terlihat kotor atau
> background abu abu muda / halus"*

---

## 3. 🚨 AKAR PALING BERBAHAYA — `.format()` membuang brief TANPA ERROR

Ini **jebakan yang sudah benar-benar terjadi**. Wajib dibaca sebelum Bos ubah apa pun.

### Kejadian nyata (20 Okt 2026)

```
brief yang BENAR : "anak menongkat bayangan dengan kapur"
PNG yang KELUAR  : "anak membayar di kasir toko"   ← KARANGAN
```

**Prompt tetap jadi. Gambar tetap keluar. QC lolos. Biaya normal. Isinya karangan.**

### Kenapa

```python
prompt = blok.format(brief=brief)
```

Kalau `blok` **tidak punya** `{brief}`, Python **membuang** argumen `brief`
**tanpa melempar error**. Variabel `brief` hilang diam-diam.

### Pagar yang sekarang menjaga

`gerbang_placeholder_brief` — **20 asersi**:
1. Setiap blok gaya **wajib** mengandung `{brief}`
2. Prompt final **wajib** memuat isi brief

> ⚠️ **Kalau Bos menambah blok gaya baru, WAJIB ada `{brief}` di dalamnya.**
> Tanpa itu, AI akan mengarang isi gambar.

---

## 4. Buku UMUM — 5 pilihan gaya

| Gaya | Karakter | Mode brief |
|---|---|---|
| **`premium-konseptual`** ← default | metafora cerdas, palet navy + terracotta | konseptual |
| `editorial-lineart` | garis tipis elegan, tinta navy | konseptual |
| `woodcut` | garis tebal gaya cukil kayu | (bawaan) |
| `flat-editorial` | bidang datar, palet terbatas | (bawaan) |
| `anak` | kartun anak (lihat §2) | literal |

**Semua 5 punya `{brief}`** ✅

### Contoh `premium-konseptual`

```text
Premium conceptual editorial illustration for a bestselling non-fiction book,
single clever visual metaphor, modern flat vector style, limited palette of
deep navy and warm terracotta, on a clean PURE WHITE background (hex #FFFFFF),
no cream, no beige, no brown tint anywhere, crisp thin dark outlines around
every shape, one central focal subject with generous negative space,
minimalist elegant composition, smooth flat surfaces with no paper texture,
no grain, no stains, no vignette, no gradients, no photorealism, no 3D,
no clutter, no text, no words, no letters, no watermark. Scene: {brief}
```

---

## 5. Model gambar — angka nyata

| Hal | Nilai |
|---|---|
| Model | **`gemini-2.5-flash-image`** |
| ⚠️ Prefix `cb/` | **SALAH** — itu jalur CodeBuddy, kredit terpisah |
| Biaya 1 gambar | **782 KB PNG**, berbayar (Rp belum diukur) |
| Gerbang QC | lebar ≤ area teks |

### 🚨 JEBAKAN MODEL (`cb/`)

```
cb/gemini-2.5-flash-image  →  HTTP 429 code 14018 "Credits exhausted"
gemini-2.5-flash-image     →  200, PNG 782 KB  ✅ HIDUP
```

Saldo InferHub **$7,57 UTUH** — yang habis kredit CodeBuddy, **bukan** saldo InferHub.

Diuji **9 nama model**: **HANYA 1 HIDUP**. 8 lainnya 404.

> **Aturan:** model WAJIB dibaca dari `GET /v1/models`, **BUKAN dikarang**.

---

## 6. Prompt pembuat brief — dua mode

| Mode | Dipakai | Menghasilkan |
|---|---|---|
| **`literal`** | buku anak | adegan **nyata** yang bisa dilihat |
| **`konseptual`** | buku umum | **metafora** dari gagasan |

Brief dibuat AI **dulu**, baru masuk ke blok gaya sebagai `{brief}`.

```
bab → PROMPT_BRIEF → brief (2-3 kalimat Inggris)
                         ↓
                    blok gaya + {brief}
                         ↓
                    prompt final → model gambar
```

Isi lengkap: `prompt/prompt-pembuat-brief.md`

---

## 7. Larangan budaya — berlaku TEKS **dan** GAMBAR

| Dilarang | Alasan |
|---|---|
| **babi** | mayoritas pembaca |
| **alkohol** | larangan budaya |
| **rokok** | larangan budaya |
| **agama** | sensitif |
| **lambang** | simbol negara/partai |
| **tanda `$`** | kesan kapitalis asing |

Isi lengkap daftar kata: `prompt/larangan-budaya.md`

---

## 8. Isi folder ini

```
gambar-dan-visual/
├── README.md                       ← berkas ini
├── TABEL-DIAGRAM-INFOGRAFIS.md     ← tabel, 8 diagram, infografis (jujur)
├── kode/                           ← salinan PERSIS dari mesin
│   ├── brief_visual.py             (836 baris)
│   ├── diagram_buku.py             (442 baris)
│   └── jenis_buku.py               (255 baris)
└── prompt/                         ← diekstrak dari kode, siap Bos edit
    ├── blok-gaya-gambar.md
    ├── bentuk-diagram.md
    ├── prompt-pembuat-brief.md
    └── larangan-budaya.md
```

---

## 9. Kalau Bos mau memperbaiki — urutan yang aman

| # | Langkah | Berkas yang disentuh |
|---|---|---|
| 1 | Ubah blok gaya | `kode/brief_visual.py` → `STYLE_BUKU` |
| 2 | ⚠️ **Pastikan `{brief}` masih ada** | (jebakan §3) |
| 3 | Ubah paket jenis | `kode/jenis_buku.py` → `PAKET` |
| 4 | Uji 1 gambar nyata | lihat hasilnya, bukan percaya prompt |
| 5 | Jalankan `gerbang_placeholder_brief` | 20 asersi harus LULUS |

### ⚠️ 3 hal yang WAJIB diingat saat memperbaiki

| # | Hal | Kenapa |
|---|---|---|
| 1 | **Blok gaya ada di DUA tempat, dan ISINYA SUDAH BERBEDA** | lihat §11 — ini **cacat nyata**, bukan cuma risiko |
| 2 | **`{brief}` wajib** | tanpa itu AI mengarang isi gambar |
| 3 | **Uji gambar NYATA** | prompt benar ≠ gambar benar |

---

## 10. Yang Wulan usul diperbaiki (untuk Bos putuskan)

| # | Hal | Alasan |
|---|---|---|
| 1 | **Blok gaya ganda** — disatukan | sekarang 2 salinan, mudah lupa perbaiki salah satu |
| 2 | **Biaya per gambar belum diukur** | perlu angka Rp supaya bisa dipakai di paket harga |
| 3 | **Infografis belum ada mesin** | sekarang 8 diagram saja, infografis manual |
| 4 | **Tabel: kepala belum berwarna** | masih `Table Grid` polos |
| 5 | **Diagram: pemilihan bentuk masih kata kunci** | belum pakai Jev (padahal aturan Bos: Jev dulu) |

---

## 11. 🔴 CACAT NYATA — dua salinan blok gaya sudah BERBEDA

**Diukur 22 Okt 2026, bukan dugaan.** Ini temuan baru saat Wulan menyusun folder ini.

### Dua salinan, dua isi

| Lokasi | Panjang | Dipakai produksi? |
|---|---|---|
| `jenis_buku.PAKET['anak']['ilustrasi']` | **571 char** | ✅ **YA — MENANG** |
| `brief_visual.STYLE_BUKU['anak']` | **518 char** | ❌ hanya cadangan |

### Siapa menang — dari kode

```python
# brief_visual.py baris 692-696
if jenis is not None:
    import jenis_buku as JB
    pkg  = JB.paket(jenis)
    gaya = pkg["gaya_gambar"]
    blok = pkg["ilustrasi"] or STYLE_BUKU.get(gaya) or STYLE_BUKU[GAYA_DEFAULT]
    #      ↑ INI MENANG
```

**Artinya:** kalau Bos memperbaiki `brief_visual.STYLE_BUKU['anak']`,
hasilnya **TIDAK akan berpengaruh** — yang dipakai `jenis_buku`.

### Beda isinya

| Kalimat | `jenis_buku` (yang dipakai) | `brief_visual` (cadangan) |
|---|---|---|
| Gaya dasar | `clean flat cartoon style` | `clean flat cartoon style with clear dark outlines around every shape` |
| `clear dark outlines around every shape` | ✅ ada (kalimat sendiri) | ✅ ada (menyatu) |
| `no 3D render` | ✅ ada | ✅ ada |
| `no text/words/letters/numbers` | ✅ ada | ✅ ada |

### Kenapa ini berbahaya

1. **Memperbaiki salah satu = kerja sia-sia** — tidak ada efek
2. **Dua sumber kebenaran** — nanti makin jauh berbeda
3. **Tidak ada gerbang** yang memeriksa keduanya sama

### Usul Wulan (perlu keputusan Bos)

| Pilihan | Cara | Risiko |
|---|---|---|
| **A** | Hapus `STYLE_BUKU['anak']`, sisakan `jenis_buku` saja | sedang — `brief_visual` masih rujuk |
| **B** | `STYLE_BUKU['anak'] = PAKET['anak']['ilustrasi']` (satu sumber, impor) | **rendah** ← Wulan sarankan |
| **C** | Tambah gerbang: kedua salinan WAJIB identik | nol, tapi masih dua salinan |

**Wulan sarankan B**: `jenis_buku` jadi **satu-satunya sumber**, `brief_visual`
mengimpornya. Satu tempat, tidak bisa lupa.

---

*Diukur Wulan 22 Oktober 2026 — angka dari kode, bukan ingatan.*
