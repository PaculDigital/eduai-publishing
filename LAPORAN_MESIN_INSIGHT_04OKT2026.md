# 🎓 MODE BELAJAR — LANGKAH 2: MESIN MINI INSIGHT (SELESAI, siap deploy)

Tanggal: 04 Okt 2026 · Putusan Bos: Q1=A (biaya ditanggung paket) · Q2=A (sumber = naskah) · Bentuk = Opsi C

## ✅ YANG DIBANGUN

| Berkas | Isi |
|---|---|
| `app/belajar.py` (+330 baris) | `teks_bab()`, `hitung_insight()`, `baca_insight()`, `_urai_butir()`, `naskah_milik()`, `naskah_sudah_aktif()`, `PROMPT_INSIGHT` |
| `app/main.py` | rute `GET /belajar/insight/{fid}` + `POST /belajar/insight/{fid}` + 3 pagar |
| `app/templates/belajar_insight.html` (BARU) | halaman hasil — Opsi C: 2 kolom desktop, 1 bab + pita mendatar di HP |
| `app/templates/belajar.html` | tombol "Mulai Belajar" → tautan ke insight |

## 🧪 UJI (semua LULUS)

```text
_uji_insight_belajar.py   → 21 LULUS / 0 GAGAL
periksa_kode.sh           → LULUS
Uji lewat HALAMAN nyata   → POST 200 (3,2 dtk) · 3 kartu · kutipan asli dari naskah
Potret DESKTOP 1200px     → 2 kolom, 3 kartu hijau, rapi ✅
Potret HP 414px           → daftar bab jadi baris mendatar, kartu rapi ✅
```

**Bukti isi insight (naskah Goras, topik kualitas kerja/efikasi diri):**
- Tema: "Teknologi ubah dunia kerja" · kutipan: *"kemampuan beradaptasi telah bergeser dari sekadar kompetensi pelengkap menjadi prasyarat utama"*
- Tema: "Ada celah kesiapan digital" · kutipan: *"25,93% responden menyatakan ragu-ragu, angka keraguan tertinggi"*

## 🚨 JEBAKAN YANG DIMAKAN (catat!)

1. **`versi.ambil_bab()` balas SELURUH NASKAH kalau label tak ketemu** (baris `return '', teks, ''`).
   Akibat: label palsu (BAB 9) → insight dibuat dari dokumen UTUH → **HALUSINASI topik** (sempat muncul "penyakit kelapa sawit" padahal naskahnya lain).
   FIX: periksa label benar-benar ADA dulu (`_deteksi_bagian` + `deteksi_bab`), pola sama dengan `ai._label_ada`.

2. **Ambang 85% "kebesaran" SALAH.** Naskah PROPOSAL cuma punya BAB I → isinya WAJAR 87% naskah! Ambang buta 85% membuang bab yang sah.
   FIX: cek label ada/tidak (poin 1) + pengaman "isi ≈ seluruh naskah" (beda < 50 kar).

3. **`_aktif_untuk()` kuncinya `'status'`, BUKAN `'aktif'`.** Wulan menebak → `naskah_sudah_aktif()` selalu False.

4. **Sandi user uji WAJIB `app.auth.hash_password` (PBKDF2)** — sha256 → login 401.

5. **`section_state` HARUS ikut pindah** saat naskah dipindah ke user uji. Kalau tidak, `bab_sudah_direvisi()` kosong → syarat terbuka gagal.
   `_siapkan_data_uji.py` (BARU) melakukan urutan benar: salin DB → user uji → naskah+berkas → `section_state` → `belajar_naskah`.

6. **Berkas fisik naskah harus DIPERIKSA ADA** sebelum memilih naskah uji (Wulan sempat pilih naskah yang berkasnya tidak ada → uji menuduh "mesin rusak").

7. **`belajar_naskah.file_id` UNIK** → hapus baris lama sebelum insert.

## 📊 HASIL UKUR

```text
Model  : combo `EduAi` (9router) — nama model ASLI belum dicatat (⚠️ jujur)
Waktu  : 3,2–3,9 detik untuk 1 bab
Prompt : PROMPT_INSIGHT + isi bab (potong maks 12.000 kar)
Token  : klik ke-2 bab yang sama = 0 token (TERBUKTI di uji)
Kutipan: 3/3 butir menyertakan kutipan asli dari naskah (guardrail §4.8)
```
