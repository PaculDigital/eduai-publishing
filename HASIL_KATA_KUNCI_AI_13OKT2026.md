<!-- SOT: HASIL_KATA_KUNCI_AI_13OKT2026.md — hasil kerja kata kunci AI
      (putusan 1A/1b/2A). STATUS: SELESAI, sudah LIVE 13 Okt 2026. -->

# ✅ HASIL — KATA KUNCI AI (13 Okt 2026)

Putusan Bos: **1A** (pesan 0-hasil diperjelas) · **1b** (hapus "TANPA TOKEN")
· **2A** (tombol AI manual, user ubah sendiri).

Status: **SELESAI & TERUJI** — **BELUM DEPLOY** (menunggu izin Bos).

---

## 🎯 AKAR YANG DICABUT (bukan tambalan)

**Gejala:** judul di luar `KAMUS_KONSEP` (25 frasa) → `q_scopus` kosong →
pengaman `cari_semua()` jatuh ke **KATA MENTAH** → hasil **NGAWUR**.

**Bukti terukur (13Okt26):** "Analisis Faktor-Faktor… E-Commerce" →
keluar artikel **AlphaFold, GLOBOCAN Cancer** (tidak nyambung sama sekali).

**Cabut akarnya:** kalau konsep kosong → **BERHENTI** dan bilang jujur
(`belum_dipetakan`). Jalur kata mentah **DIHAPUS**.

---

## 📁 BERKAS YANG DIUBAH

| Berkas | Perubahan |
|---|---|
| `app/pustaka.py` | `kata_kunci_dari_ai()` · `kata_kunci_dari_ai_async()` · `_urai_konsep_ai()` · `_simpulkan()` · `_ai_jalan()` · `_jejak_reset()` · `kata_kunci_ai()` · `kata_kunci_ai_async()` · `kata_kunci_konsep()` · `cari_semua(pakai_ai=)` → pecah ke `cari_semua_dengan_konsep()` |
| `app/jurnal.py` | `cari_untuk_bab(pakai_ai=)` → `_rapikan()` · `cari_untuk_bab_konsep()` |
| `app/rute_jurnal.py` | `/cari-ai` pakai jalur `await` · rute BARU `/kata-kunci-ai` · pesan 0-hasil 2 kasus |
| `app/templates/referensi.html` | hapus lencana "TANPA TOKEN" · tombol "EduAi bantu isi" · chip konsep bisa dibuang · CSS |
| `_gerbang_kata_kunci_ai.py` | **BARU** — gerbang 32/0 + 4 uji gigi |
| `_uji_http_kata_kunci.py` | **BARU** — uji HTTP 11/0 (DB salinan) |
| `_gerbang_hemat_kuota.py` | **USANG diperbaiki** — `search_literature`/`limit` → `citation_graph`/`seeds`/`max_edges` (23/0) |
| `_gerbang_halaman_referensi.py` | **USANG diperbaiki** — tidak lagi menuntut "TANPA TOKEN" (41/0) |

Backup: `_arsip/pre-kata-kunci-ai-20261013-083649/`

---

## 🚨 CACAT NYATA YANG DITEMUKAN GERBANG (2)

1. **`sumber_kata_kunci` salah** — saat kamus gagal, masih dilaporkan
   `'kamus'` (padahal kamus TIDAK menemukan apa pun). ⇒ user dapat info
   salah. **Diperbaiki** (jadi `''`).

2. **🚨 BUG PRODUKSI: `asyncio.run()` di event loop** — rute FastAPI
   jalan di event loop hidup ⇒ `asyncio.run` **SELALU MELEDAK**:
   ```
   [pustaka] kata kunci AI gagal: asyncio.run() cannot be called
             from a running event loop
   ```
   ⇒ **fitur ini akan SELALU gagal di produksi** kalau tidak ketahuan.
   Uji unit lulus, uji HTTP menangkapnya. **Diperbaiki** dengan jalur
   `_async` + `await` (pola resmi proyek, spt `belajar.py:570`).

---

## 🧪 BUKTI TERUKUR

**Gerbang (semua BERGIGI — disuntik rusak ⇒ GAGAL):**

| Gerbang | Hasil |
|---|---|
| `_gerbang_kata_kunci_ai.py` | **32 / 0** |
| `_gerbang_hemat_kuota.py` | **23 / 0** |
| `_gerbang_halaman_referensi.py` | **41 / 0** |
| `_gerbang_jurnal.py` | **21 / 0** |
| `_gerbang_jatah.py` | **42 / 0** |
| `_gerbang_kutipan_scite.py` | **29 / 0** |
| `_gerbang_pagar_artikel.py` | **32 / 0** |
| `_gerbang_ikon_referensi.py` | **53 / 0** |
| `periksa_kode.sh` | **LULUS** |

**Uji gigi (suntik rusak harus EXIT 1):**
- Jalur kata mentah dibalik → **3 GAGAL** (dan 7 artikel ngawur muncul!)
- Urai AI dilonggarkan → **1 GAGAL**
- Lencana "TANPA TOKEN" dibalik → **1 GAGAL**
- Tombol bantu dicabut → **1 GAGAL**
- Alat Scite ke `search_literature` → **pesan jujur + EXIT 1**
- `include_intent`/`include_snippets` dicabut → **2 GAGAL**

**Ukur nyata (sebelum → sesudah):**

| Judul | Dulu | Sekarang |
|---|---|---|
| "Analisis Faktor-Faktor… E-Commerce" | **AlphaFold/GLOBOCAN** ❌ | tanpa AI: 0 + jujur · pakai AI: **15 artikel, 14 verified** ✅ |
| Kalibrasi 10 judul | — | AI memetakan **10/10** · dapat artikel **10/10** · verified **9/10** |

**Uji AI dari event loop:** `dipanggil=True · sumber=ai · galat=''` ⇒ **jalan**.

---

## 📋 ATURAN YANG DIPEGANG

- **🛡️ AI HANYA menyusun KATA KUNCI** — AI **tidak pernah** menyebut
  artikel. Artikel 100% dari 4 mesin NYATA + audit DOI ⇒ kata kunci salah
  = **0 artikel** = user TAHU. Mustahil artikel palsu.
- **KAMUS dulu** (Rp 0, instan) → **AI** hanya kalau kamus gagal.
- **AI gagal ⇒ JUJUR KOSONG**, tidak jatuh ke kata mentah.
- **Keputusan akhir di USER** (tombol manual, bisa ubah/hapus chip).

---

## 🔜 BELUM

- **DEPLOY** — menunggu izin Bos (image masih yang lama).
- **Kotak Teori** (bank teori → grand theory + teori variabel) — tahap
  berikutnya, rancangan sudah ada di `RANCANGAN_KOTAK_TEORI_13OKT2026.md`.
