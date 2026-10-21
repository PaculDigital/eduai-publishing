# 🚩 FLAG 24 Sep 2026 — TAHAP 3.1 TAYANG + TEMUAN TOKEN

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ PETA/ARSIP LAMA — BUKAN penentu status proyek.
> Berkas ini memetakan keadaan pada **tanggal di namanya**. Banyak isinya
> **sudah berubah**. Sah untuk **pelajaran/jejak**, ❌ **JANGAN** dipakai
> sebagai keadaan kini.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> **Ringkas, untuk sesi baru.** Rincian lengkap: `/opt/data/FLAG_OBROLAN.md`
> dan `FLAG_LANJUT_DISINI.md` (blok teratas).

## ✅ SELESAI HARI INI (24 Sep 2026)
- **TAHAP 3.1 SOROTAN KALIMAT — DEPLOY 02:29 UTC.** Image
  `eduai-app:20260924_022958-sot` · `https://eduai.bikinaja.id` **200** ·
  `/health` 200 · SOT bersih (33 .py image == source, md5 sorotan cocok,
  `docker diff` bersih) · DB 19 tabel / users=5 / files=39.
- **STANDAR BARU (ACC Bos):** `docker cp` **WAJIB** + `docker restart`.
  Pakai **`bash scripts/salin_restart.sh eduai-app app/berkas.py`**.
  ⚠️ `eduai-app` TIDAK punya healthcheck → ukur **`/health`**, bukan
  `.State.Health.Status`.
- **TEMUAN "revisi ringan ≈ berat":** aturan §4.13 **BENAR, tanpa bug**;
  penyebabnya **`app/konteks.py` (176 baris, 15 Sep) belum disambung** ke
  `app/ai.py` → seluruh naskah dikirim → `token_in` ±34.000 → selalu 4–6
  Token Revisi. Bukti DB: id83 `in=34.804 out=1.721 rev=4` · id84
  `in=32.397 out=24.342 rev=6`. → `TEMUAN_REVISI_RINGAN_VS_BERAT_24SEP2026.md`

## ⏸️ MENUNGGU KEPUTUSAN BOS (belum dikerjakan)
1. Sambungkan `app/konteks.py` → `app/ai.py` (**WAJIB ACC Bos** — `ai.py`)
2. Pagar "ubah alur" tetap seluruh dokumen
3. Uji banding mutu: potongan vs penuh (**titik kritis: tetap NYAMBUNG**)
4. Perbaiki label `ai.py:1332` (`§4.10` → `§4.13`)
5. Bahas: 2 bagian berurutan = ±2× waktu

## 👁️ BELUM DIPERIKSA MATA
`_potret/t31prod/01.png` (potret produksi 150.233 byte) — **periksa ini dulu.**

## ⚠️ CATATAN
- `memory` **terkunci** sepanjang sesi 24 Sep → simpan dari
  `_CATATAN_MEMORY_24SEP2026.md`; ada 2 duplikat + 1 entri usang.
- Sisa uji `_uji_publik_komentar.py` bervariasi 36/1 ↔ 37/0 (AI nyata);
  M2 sudah konsisten hijau.
