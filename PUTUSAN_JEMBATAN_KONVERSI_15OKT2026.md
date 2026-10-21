# 🌉 PUTUSAN JEMBATAN KONVERSI JURNAL (15 Okt 2026) — LIVE

<!-- SOT: putusan jembatan konversi + harga mutu bertingkat · 15 Okt 2026 ·
     acuan tunggal untuk: harga elemen (2/3/5), tombol bab kurang,
     jaminan sudah-bayar. Jangan salin isinya ke dokumen lain — TUNJUK ke sini. -->

**Status: ✅ LIVE** — image `eduai-app:20261016_021214-sot`
(pertama tayang `20261016_011600-sot`, 16 Okt 2026).

## Masalah yang dijawab

`cek_kelengkapan()` **SUDAH** menghitung bab kurang, TAPI **tidak dipakai**
di layar (grep 'kelengkapan' di `artikel_konversi.html` & `artikel.html` =
KOSONG) ⇒ tidak ada jembatan dari "bab kurang" ke perbaikan.

## Putusan Bos — 2 jalur, TOMBOL HARUS SALAH SATU

> *"kalo dua duanya muncul user akan bingung dan sistem app EduAi akan kacau
> dalam mengidentifikasi naskah tersebut, bisa error atau salah pilih"*
> — Bos, 15 Okt 2026

| Keadaan | Yang tampil |
|---|---|
| **Bab kurang** | HANYA tombol **"Perbaiki"** → `/kolaborasi`. Tombol mutu & konversi **DISEMBUNYIKAN** |
| **Bab lengkap, mutu kurang** | **"Tambah elemen (n token)"** + **"Lanjut apa adanya"** |
| **Semua lengkap** | **"Mulai Konversi"** |

Alasan: **BAB = fondasi · MUTU = hiasan.**

## Harga tambah elemen mutu — BERTINGKAT

> *"harga bisa saya variasi tidak seragam 2 token, karena beban kerja ai juga
> lebih banyak"* — Bos, 15 Okt 2026

| Tingkat | Token | Elemen |
|---|---|---|
| **BERAT** | **5** | State of Art · Diskusi Komparatif |
| **SEDANG** | **3** | Gap · Novelty · Findings · Analisis Kritis · Kaitan Teori |
| **STANDAR** | **2** | Hook · Limitasi · Rekomendasi · Implikasi |
| **Bagian artikel** | **2** | (seragam, tidak bertingkat) |

Satu sumber: `konversi.py` → `TOKEN_ELEMEN` + `token_elemen()` + `tingkat_elemen()`.

## JAMINAN: sudah bayar = harus lolos

> *"Jangan sampai user sudah bayar mutu tetapi saat konversi masih tidak
> lolos... Ini masalah tingkat kredebilitas"* — Bos, 15 Okt 2026

| Keadaan | Token | Konversi |
|---|---|---|
| AI berhasil + Jev ≥0,50 | dipotong | **LOLOS** |
| AI berhasil + Jev <0,50 | dipotong | **TETAP LOLOS** (user sudah bayar) |
| Gagal **trouble** server/AI | **TIDAK** dipotong | beri tahu lembut, coba lagi |
| Gagal naskah rusak | TIDAK dipotong | beri tahu cara perbaiki |

## Aturan tampil elemen mutu

```
nilai ≥ 0,50            → tidak ditanyakan
nilai < 0,50 + DIBAYAR  → tidak ditanyakan  (elemen Done)
nilai < 0,50 + BELUM    → DITANYAKAN
```

Ambang: `AMBANG_ADA = 0,50` · `AMBANG_RAGU = 0,35` (`konversi.py`)
Catatan Jev **TIDAK** ditampilkan kalau elemen sudah dibayar (jangan bikin ragu).

## Bukti uji (16 Okt 2026)

| Uji | Hasil |
|---|---|
| `_uji_jembatan_final.py` | **15 / 0** |
| `_uji_jembatan_kurang.py` | **6 / 0** |
| `_gerbang_konversi_revisi.py` | **42 / 0** |
| `_gerbang_revisi.py` | **51 / 0** |

⚠️ **PELAJARAN UJI (16 Okt):** JANGAN uji dengan merusak berkas produksi —
kalau crash, kerusakan **tertinggal** di container hidup (pernah terjadi:
judul jadi `XXX-MATI-XXX`). Uji gigi WAJIB lewat **salinan**.

## Sambungan berikutnya

Lapis 3 (Tiket Lolos) = `PUTUSAN_TIKET_LOLOS_LAPIS3_16OKT2026.md`.
