# 🔧 05 Okt 2026 (lanjutan) — PARSER DIPERBAIKI (C) + GERBANG MERAH PALSU DITUTUP (D1)

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> **Berkas ini merekam APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) di dalamnya **wajar berbeda** dari
> keadaan **kini** — itu BUKAN kesalahan, itu memang rekaman.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


**Perintah Bos:** "C lalu A dan B" → lalu **D1**.
**Status:** C & D1 **SELESAI & TERBUKTI**. A & B **BELUM**.

---

## Bagian 1 — C: 3 CACAT `app/parser.py` DIPERBAIKI

**Akun: benar 9/16 (56%) → 14/16 (88%)** *(ukur: `_uji_parser_salah_tempat.py`, 20 kasus)*

### Akar (terukur, bukan dugaan)
`parser.py` = 448 baris **pencocokan KATA**, **tak pernah membaca naskah**. Ia memilih
bagian dari **KATALOG tetap**, bukan dari isi naskah user. Conf dihitung dari
**PANJANG KATA KUNCI** — panjang kata ≠ keyakinan.

### Cacat 1 — `babasebut` selalu jatuh ke sub-bab PERTAMA
```
"tolong perbaiki bab 4"  → 4.1   (padahal bisa 4.2/4.3/4.5)
"perbaiki kerangka berpikir di bab 2" → 2.1 (padahal 2.3 Kerangka Berpikir)
```
SEBAB: `SECTIONS_CATALOG[kat][0]` — indeks **[0]** = sub-bab pertama bab itu.

### Cacat 2 — intent MENUTUPI ragu tempat (paling berbahaya)
```
conf LAMA = (s_skor + i_skor) / 2
"perbaiki bab 4" → s 0,45 (menebak) + i 0,95 ("perbaiki" yakin)
                 → rata-rata 0,61 → butuh_ai=FALSE → revisi 4.1 TANPA diperiksa
```
**INI akar keluhan Bos: "revisi tempatnya tidak salah yang direvisi."**
Keyakinan NIAT dipakai membenarkan TEBAKAN TEMPAT.

### Cacat 3 — "hasil" tak ada di kamus
`"hasil penelitian belum dibahas"` → **UNKNOWN** padahal 4.5 Pembahasan ADA.

### Perbaikan
| # | Perbaikan | Bukti |
|---|---|---|
| 1 | Bila sebut BAB + ada kata kunci sub-bab → pakai sub-bab itu | `"kerangka berpikir di bab 2"` → **2.3** ✅ |
| 2 | Bila sebut BAB tanpa kata kunci → conf **0,45** (butuh_ai) | `"perbaiki bab 4"` conf **0,61→0,27**, butuh_ai **True** ✅ |
| 3 | `confidence` = niat & tempat **JANGAN dirata-rata** (ambang 0,5, bukan ambang baru) | 12/12 pesan jelas tetap yakin ✅ |
| 4 | Tambah kata kunci: `hasil`, `dibahas`, `membahas`, `temuan` | `"hasil penelitian belum dibahas"` → **4.5** ✅ |

### PAGAR TERUJI
- 12/12 pesan JELAS tetap `butuh_ai=False` (perilaku lama utuh)
- **Pengali harga TIDAK berubah**: `bab 4`=×1 · `ganti metode`=×3 · `seluruh dokumen`=×5
- `butuh_ai` **BELUM disambung** ke jalur mana pun → perbaikan C belum mengubah produksi
- Gerbang kode (`periksa_kode.sh`) **LULUS**

**Backup:** `_arsip/pre-parser-c-20261005-054008/` (sebelum + sesudah + MD5)

### ⚠️ Koreksi JUJUR
4 dari 6 "SALAH" pada uji awal = **kunci uji Wulan yang salah**, bukan aplikasi
(`"perbaiki pembahasan"` → 4.5 itu BENAR). Bukan pola baru — sama seperti
S3 & deteksi judul (18Sep26).

---

## Bagian 2 — D1: GERBANG MERAH PALSU DITUTUP

**Gerbang: 30 grup (1 GAGAL) → 31 grup / 0 GAGAL · EXIT 0**

### Akar (terukur dari DB)
`_uji_publik_komentar` **selalu** "15 LULUS / 5 GAGAL" dengan D1 = **HTTP 402
`kode=KUOTA_HABIS`** — angkanya **tak berubah** walau kode aplikasi diganti.

**Sebab:** `scripts/gerbang_uji.sh` baris 179 & 233 hanya reset **`pemakaian_ai`**,
padahal **402 = SALDO `saldo_token`** (sudah terbukti). Saldo user uji 6 = **0**
→ SETIAP hari kena 402 → **GAGAL PALSU tiap hari**.

**Kenapa berbahaya:** gerbang merah palsu = orang **berhenti percaya gerbang**,
dan **kerusakan nyata bisa tersembunyi** di dalamnya.

### Akar kedua — jangan palsukan buku besar
`saldo_token` = **LEDGER** (`sumber='pakai'` menulis baris `sisa=0`).
Menulis ulang baris lama = **memalsukan sejarah pemakaian user**.
Karena itu baris `pakai` **TIDAK PERNAH disentuh**; dana uji dicatat baris BARU
(`sumber='uji'`, `order_id=''` — mengikuti pola yang SUDAH ADA di DB).

### Perbaikan (2 tempat: reset SEBELUM uji & SESUDAH uji)
Reset kuota + **saldo** user uji (6 & 7) ke 20, dibuktikan baca-ulang DB.

### Bukti
```
_sketsa/uji_reset_gerbang_d1.sh → HASIL: LULUS
  user 6: 0 → 20 ✅   user 7: 16 → 20 ✅   baris 'pakai' user 6 tetap 140 ✅
GERBANG: 31 grup / 0 GAGAL · EXIT 0 · log _arsip/gerbang_D1b.log
```
**Backup:** `_arsip/pre-gerbang-d1-20261005-055837/` (sebelum + sesudah + MD5)

---

## Bagian 3 — TEMUAN TERPISAH: model 9router TIDAK STABIL

Saat run pertama D1, E1 gagal **nyata**:
```
503: 'Balasan AI tidak wajar (jauh lebih panjang daripada bagian yang diganti).'
```
**Perbandingan komentar SAMA di DB:**
| id | komentar | hasil | out |
|---|---|---|---|
| 187 | `"Latar belakang terlalu pendek... Perdalam..."` | **GAGAL** ❌ | 0 |
| 183 | *(sama persis)* | **SELESAI** ✅ | 416 |
| 188 | `"Perbaiki tata bahasa dan ejaan paragraf"` | SELESAI | 760 |
| 184 | *(sama persis)* | SELESAI | **6.094** |

**Kesimpulan:**
1. **Pagarnya BENAR** — `"perbaiki tata bahasa"` dijawab **6.094 kar** itu
   **bahaya nyata** (naskah user dirusak AI); pagar menolak + **kembalikan token** ✅
2. **Model `cb/deepseek-v4.1-flash` tidak konsisten** pada tugas sama
3. **BUKAN cacat kerja C** — run kedua (kode C tetap terpasang) **HIJAU**;
   kalau cacat kode, ia **akan gagal terus**

## 📌 UTANG / BELUM DIKERJAKAN
- **parser.py BELUM di-deploy** (gerbang hijau, menunggu izin Bos)
- **A** = rancangan Jev (peta presisi + penjaga arah revisi) — BELUM
- **B** = koding `app/petugas_struktur.py` — BELUM
- Pantau kestabilan model `cb/deepseek-v4.1-flash`
