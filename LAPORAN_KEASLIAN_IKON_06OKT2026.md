# 🔴 KEJUJURAN IKON + GERBANG ANTI-HALUSINASI (06 Okt 2026)

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> **Berkas ini merekam APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) di dalamnya **wajar berbeda** dari
> keadaan **kini** — itu BUKAN kesalahan, itu memang rekaman.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Bos (verbatim): *"Sebenarnya kita sudah download icon lucide yang benar
> komplit tidak sih? Atau cuma download yang dibutuhkan saja?"*
>
> Lalu: *"kadang kamu masih pakai icon standar, contoh dulu pernah saya suruh
> ganti spark, eh yang kamu pasang spark icon standar setelah saya kasih link
> lucide iconnya baru kamu ganti, itu kan halusinasi kamu, terlalu
> menggampangkan perintah"*

---

## 1. JAWABAN PERTANYAAN BOS: **TIDAK lengkap**

Sprite EduAi = **64 ikon**. Lucide punya **2.102 ikon**.

Sejak awal (16 Sep 2026) sprite memang **pilih-pilih** — skrip
`scripts/bangun_sprite_ikon.py` punya daftar `IKON = {...}` berisi **56 nama**
saja. Tambah 8 dari Wulan = 64.

**Masalah nyata:**
- Paket Lucide lengkap dulu di `/tmp/lucide-x` → **SUDAH HILANG** (VPS
  dibersihkan). Skrip pembangun **tidak bisa dijalankan ulang** — catatan
  jujur ini bahkan tertulis di dalam skripnya.
- Sumber cadangan `_ikon-sumber/` cuma isi **2 ikon** (`bell`, `bell-ring`).
- Jadi tiap butuh ikon baru → unduh manual satu-satu dari unpkg.

---

## 2. WULAN AKUI SALAHNYA

Bos benar. Kejadian `spark` itu **halusinasi**:
- Wulan menulis nama ikon **dari ingatan** → `ikon('spark')`
- `spark` **TIDAK ADA** di Lucide (yang benar `sparkles`)
- Template tetap jalan (tak error) → **tampak "selesai" padahal SALAH**
- Bos baru tahu setelah lihat sendiri + kasih link → baru Wulan ganti

**Itu "menggampangkan perintah"** — Wulan tidak memverifikasi.

---

## 3. HASIL AUDIT JUJUR (dijalankan sekarang)

Wulan bandingkan **seluruh 64 ikon** di sprite lawan **Lucide RESMI**
(unpkg/jsdelivr) — bukan cuma cek "namanya ada", tapi **bentuk path-nya**.

**Hasil: 64 / 64 COCOK.** Nol palsu. Nol beda.

✅ Jadi sprite **saat ini benar** — tapi itu **belum cukup**, karena Wulan
bisa mengulanginya lagi kapan saja. ⇒ Perlu **penjaga permanen**.

---

## 4. GERBANG ANTI-HALUSINASI (BARU)

`_gerbang_ikon_asli.py` — 5 uji:

| Kode | Yang diperiksa |
|---|---|
| A1 | Sprite memuat ≥20 ikon |
| A2 | Setiap ikon yang **dipakai template ADA di sprite** |
| A3 | Bentuk tiap ikon **COCOK** Lucide resmi (banding path) |
| A4 | **TIDAK ada ikon KARANGAN** (nama tak ada di Lucide = 404) |
| A5 | Semua ikon berhasil diperiksa (sumber tersedia) |

**Simpanan** `_ikon-asli/*.txt` (64 berkas, 260 KB) **ikut repo** → gerbang
jalan **offline**; mode `--online` untuk memperbarui.

**UJI BERGIGI TERBUKTI:** Wulan pasang `<symbol id="ik-spark">` + template
`ikon('spark')` (meniru kejadian lama) → gerbang balas:

```
GAGAL  A4 TIDAK ada ikon KARANGAN (nama tidak ada di Lucide)  (karangan: ['spark'])
```

⇒ **Kejadian lama Bos sekarang TERTANGKAP OTOMATIS.**

---

## 5. BUG WULAN SENDIRI saat membangun gerbang (jujur)

Wulan menemukan **4 bug pada gerbang yang baru dibuat** — semuanya diperbaiki:

1. **`re.sub(r'\s+','',isi)`** → `"M20 6 9 17"` jadi `"M206917"` (angka palsu)
   ⇒ bandingkan **per-elemen** path/circle, jangan buang spasi.
2. **`f.result() or ''`** → `None` (KARANGAN) berubah jadi `''` (tak diperiksa)
   ⇒ gerbang **BUTA**. Diperbaiki jadi `f.result()`.
3. **`import urllib.error` tidak ada** ⇒ `except HTTPError` gagal senyap,
   404 tidak terdeteksi. Ditambahkan.
4. **Simpanan ditulis di `/app`** (container) bukan proyek ⇒ hilang saat
   restart. Dipindah ke `_ikon-asli/` proyek.

**Pelajaran:** gerbang baru WAJIB diuji bergigi. Tanpa itu, gerbang buta tetap
"hijau" dan Wulan merasa aman padahal tidak ada yang dijaga.

---

## 📊 BUKTI

| Gerbang | Hasil |
|---|---|
| **10 gerbang** | ✅ **444 LULUS / 0 GAGAL** |
| `periksa_kode.sh` | ✅ LULUS |
| Keaslian ikon | ✅ **64/64 cocok Lucide resmi** |
| Uji bergigi | ✅ `spark` palsu → **A4 GAGAL** |

| Gerbang | Lulus |
|---|---|
| jurnal · jurnal2 · jurnal3 | 21 · 60 · 53 |
| jatah · rute_jurnal | 42 · 62 |
| halaman_ref · kata_ref | 35 · 35 |
| ikon_referensi · ikon_semua | 55 · 76 |
| **ikon_asli (baru)** | **5** |

---

## 6. ⚠️ MASIH TERBUKA — perlu keputusan Bos

**Apakah unduh Lucide LENGKAP (2.102 ikon) ke proyek?**

| | Ukuran perkiraan | Kelebihan | Kekurangan |
|---|---|---|---|
| **A. Unduh lengkap** | ± 1 MB (sprite) | Ke depan tak perlu unduh lagi; tak mungkin hilang | Berkas besar; 2.038 ikon tak terpakai |
| **B. Biarkan 64** | 20 KB | Ringan | Butuh ikon baru = unduh manual |

Wulan **sarankan A** — sekali kerja, disimpan **di dalam proyek** (bukan
`/tmp`), jadi tidak akan hilang lagi saat VPS dibersihkan.

**Belum dikerjakan** — menunggu putusan Bos.

---

## 📁 Berkas

**Baru:** `_gerbang_ikon_asli.py` (5 uji) · `_ikon-asli/` (64 sumber resmi)
**Laporan:** ini + `LAPORAN_SEMUA_IKON_LUCIDE_06OKT2026.md`
**Pelajaran disimpan:** `fact_store` #202 + memory
