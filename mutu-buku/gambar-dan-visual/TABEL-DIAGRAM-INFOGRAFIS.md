# 📊 TABEL, DIAGRAM & INFOGRAFIS — Bagaimana Sebenarnya Dibuat

> **Sumber:** `buku_umum_assembly.py` baris 945–1000 · `diagram_buku.py`
> **Diukur 22 Okt 2026.** Bukan tebakan.

---

## 1. Tiga hal ini BEDA cara membuatnya — jangan dicampur

| Unsur | Dibuat oleh | Biaya | Hasil |
|---|---|---|---|
| **Tabel** | `python-docx` langsung (`add_table`) | **Rp 0** | tabel Word asli, bisa diedit |
| **Diagram** | `diagram_buku.py` → **SVG** → PNG | **Rp 0** | gambar presisi, teks rata tengah |
| **Ilustrasi** | **AI gambar** (`gemini-2.5-flash-image`) | **berbayar** | PNG 782 KB |

> ⚠️ **Diagram BUKAN AI.** Ini penting — banyak yang menyangka diagram dibuat AI.
> Diagram dibuat **kode SVG**, jadi isinya **pasti** sesuai data (tidak mengarang).

---

## 2. TABEL — angka nyata

### Cara dibuat

```python
n_rows = len(rows_data) + 1        # +1 = baris kepala
n_cols = len(headers)
table = doc.add_table(rows=n_rows, cols=n_cols)
table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.CENTER
```

### Gaya

| Elemen | Nilai |
|---|---|
| Style | **`Table Grid`** (garis penuh) |
| Posisi | **rata tengah** |
| Kepala tabel | **tebal**, rata tengah, **10 pt** |
| Isi sel | rata kiri, **10 pt** |
| Judul tabel | `Tabel {id} {judul}` — tebal, rata tengah |
| Jarak judul | `space_before=10`, `space_after=6` |

### 🚨 PAGAR PALING PENTING — tabel tanpa data TIDAK DIBUAT

```python
if not rows_data:
    log.warning('tabel %s DILEWATI — pipeline tidak memberi baris data')
    continue          # ← tabel TIDAK dirakit sama sekali
```

**Kenapa:** versi lama mengisi tabel tanpa data dengan `"..."` (titik-tiga).
Akibatnya pembaca melihat **"tabel bohong"** — ada kotak tabel, tapi isinya
titik-titik. Sekarang: **lebih baik tidak ada tabel** daripada tabel kosong.

### Marker di naskah

Penulis (LLM) menandai tabel dengan:
```
[TABEL 1.1: Judul Tabel - keterangan]
```

---

## 3. DIAGRAM — 8 bentuk, dipilih dari ISI

### Cara dibuat

```
judul + keterangan + tahap
        ↓
  pilih_bentuk()  → pilih 1 dari 8
        ↓
  _PEMBANGUN[bentuk](judul, tahap)  → HTML/SVG
        ↓
  render → diagram_{id}.png
        ↓
  masuk .docx
```

### 8 bentuk yang ADA

| Bentuk | Fungsi | Cocok untuk |
|---|---|---|
| `alur` | `_b_alur` | urutan langkah, proses |
| `siklus` | `_b_siklus` | hal berulang, putaran |
| `pohon` | `_b_pohon` | hirarki, klasifikasi |
| `piramida` | `_b_piramida` | tingkat, prioritas |
| `lapisan` | `_b_lapisan` | susunan bertingkat |
| `batang` | `_b_batang` | perbandingan angka |
| `pai` | `_b_pai` | proporsi bagian |
| `garis` | `_b_garis` | tren, perubahan waktu |

### Aturan gaya (putusan Bos)

| Aturan | Detail |
|---|---|
| Teks **rata tengah** | justify datar = "sangat jelek" |
| Siklus **TANPA panah** | cukup nomor besar — "lebih aman kalo tidak pakai panah" |
| Bentuk **dari ISI** | bukan kotak–panah-bawah terus |
| Latar **PUTIH** | bukan krem |
| Varian `_var1/2/3` | dibuat, tapi **TIDAK masuk** `.docx` — hanya utama |

### Marker di naskah

```
[DIAGRAM 1.3: Judul Diagram - keterangan]
```

> ⚠️ **JEBAKAN TERUKUR:** pola lama mewajibkan `]` penutup. Penulis kadang
> memotongnya (baris 135 karakter tanpa `]`) ⇒ penanda lolos sebagai
> **paragraf biasa** ⇒ **tercetak MENTAH** di `.docx`, gambar hilang.
> Obat: pola "gaduh" (`_POLA_DIAGRAM_GADUH`) yang mengambil sisa baris walau
> `]` tidak ada.

---

## 4. INFOGRAFIS — JUJUR: belum ada mesinnya

| Hal | Status |
|---|---|
| Mesin infografis khusus | ❌ **TIDAK ADA** |
| Yang ada | 8 bentuk diagram (`diagram_buku.py`) |
| Yang ada | ilustrasi AI (`brief_visual.py`) |
| Infografis = gabungan | ⚠️ bisa dibuat manual, **tidak otomatis** |

**Artinya:** kalau buku butuh infografis (grafik + angka + label + ikon
sekaligus), sekarang **harus dibuat di luar** lalu dimasukkan sebagai blok
`gambar`. Generator v2 bisa menempatkannya, tapi **tidak membuatnya**.

---

## 5. Yang perlu diperbaiki (usul urut prioritas)

| # | Hal | Kenapa |
|---|---|---|
| 1 | **Infografis belum ada mesin** | kalau buku butuh, harus manual |
| 2 | Tabel: warna kepala `F2F2F2` belum dipasang | sekarang cuma `Table Grid` polos |
| 3 | Tabel: baris belang (zebra) belum ada | tabel panjang sulit dibaca |
| 4 | Diagram: pemilihan bentuk masih kata kunci | belum pakai Jev |
| 5 | Ilustrasi: biaya per gambar belum diukur | belum ada angka Rp |

---

## 6. Berkas terkait di folder ini

| Berkas | Isi |
|---|---|
| `kode/diagram_buku.py` | 8 bentuk diagram (SVG) — **442 baris** |
| `kode/brief_visual.py` | blok gaya ilustrasi + prompt brief — **836 baris** |
| `kode/jenis_buku.py` | paket gaya per jenis buku — **255 baris** |
| `prompt/bentuk-diagram.md` | kode lengkap 8 bentuk |
| `prompt/blok-gaya-gambar.md` | 5 blok gaya ilustrasi |
| `prompt/prompt-pembuat-brief.md` | prompt yang MENGHASILKAN brief |
| `prompt/larangan-budaya.md` | larangan budaya untuk teks & gambar |

---

*Diukur Wulan 22 Oktober 2026. Angka dari kode, bukan ingatan.*
