# 📋 STATUS RENCANA BANGUN SSOT — DIUKUR 23 Okt 2026

> **Berkas ini BUKAN rencana.** Ini **hasil pengukuran** atas
> `RENCANA-BANGUN-SSOT.md`. Wulan tidak mencentang apa pun tanpa bukti.
>
> Diukur dari `main` = `1d7ec9d`, bukan dari ingatan.

---

## Ringkasan: 2 dari 20 selesai

| Bagian | Nomor | Selesai | Belum |
|---|---|---|---|
| **A** Sumber Tunggal | 1–3 | 1 | 2 |
| **B** Mesin | 4–8 | 0 | 5 |
| **C** Mutu Tulisan | 9–12 | 0 | 4 |
| **D** Mutu Gambar | 13–15 | 1 | 2 |
| **E** Bukti & Mutu | 16–19 | 0 | 4 |
| **F** Book Chapter | 20 | 0 | 1 |
| **JUMLAH** | **20** | **2** | **18** |

---

## A. SUMBER TUNGGAL (SSOT)

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **1** | Peta SOT | 🟡 **SEBAGIAN** | `mutu-buku/SOT-INDUK.md` **ADA** (dibuat 22 Okt). Tapi **belum** memetakan SETIAP fakta; baru 7 fakta utama. Fakta berumah ganda **belum semua ditandai** — yang baru: `STYLE_BUKU['anak']` |
| **2** | Berkas profil per jenis | 🔴 **BELUM** | `ls jenis/*/profil.json` → **kosong**. Baru ada `SPESIFIKASI.md` (tulisan tangan, bukan profil) |
| **3** | Spesifikasi turunan dari profil | 🔴 **BELUM** | belum ada generator dokumen; `SPESIFIKASI.md` masih **salinan tangan** |

**Yang nyata ada:** 4 `SPESIFIKASI.md` (monograf, referensi, ajar, chapter) — tapi itu **bahan**, bukan profil.

---

## B. MESIN

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **4** | Daftar Pustaka WAJIB | 🔴 **BELUM — UTANG TERBUKTI** | `buat_buku.py:453` → `(['DAFTAR PUSTAKA'] if spec.get('daftar_pustaka') else [])`. Masih **opsional**. Sudah disahkan Bos di `e491fc3` tapi **kode belum menyusul** |
| **5** | Generator menerapkan profil | 🔴 **BELUM** | tidak ada `profil.json`; `buat_buku.py` menyalin template apa adanya, angka **tidak** dibaca dari profil |
| **6** | Gerbang baca profil | 🔴 **BELUM** | `grep -c profil periksa_buku_template.py` = **0**. Masih satu aturan untuk semua jenis |
| **7** | Nomor halaman terukur | 🔴 **BELUM** | `indeks_referensi.py:287 halaman_perkiraan()` masih **360 kata/halaman** — belum pensiun |
| **8** | Gerbang font di server produksi | 🔴 **BELUM** | `periksa_font.py` ada tapi **tidak jalan di produksi**. Diukur: font Trajan di image = **0** |

---

## C. MUTU TULISAN

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **9** | Aturan tulisan per jenis di profil | 🔴 **BELUM** | `tone_menulis.py` hanya kenal **umum/anak/pendidikan**. Monograf & ajar **tidak punya tone** — jatuh ke `umum` ("Anda") |
| **10** | Gerbang tulisan terukur | 🔴 **BELUM** | sitasi dua arah **tidak ada**; larangan budaya di **brief gambar** ada, di **teks** belum jadi gerbang |
| **11** | Gate cek plagiarisme | 🔴 **BELUM** | tidak ada modul plagiarisme untuk buku. Yang ada cuma `_uji_pintu_plag.py` (uji), bukan mesin |
| **12** | Verifikasi sitasi 3 lapis | 🔴 **BELUM** | belum ada; menunggu kwitansi (#16) |

---

## D. MUTU PROMPT GAMBAR

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **13** | Prompt brief BERSLOT | 🔴 **BELUM** | `PROMPT_BRIEF_LITERAL`/`KONSEPTUAL` **ada** tapi **tidak berslot** dan **tanpa contoh brief bagus**. Belum diubah |
| **14** | Blok gaya POSITIF-DULU | 🟡 **SEBAGIAN** | Blok anak **sudah** positif-dulu (`clean flat cartoon style` di depan, larangan di ekor) — itu hasil 20 Okt. Tapi **jangkar konsistensi** (frasa gaya + tokoh SAMA antar gambar) **BELUM ADA** |
| **15** | Pemeriksaan isi gambar | 🔴 **BELUM** | sekarang hanya cek **lebar** gambar, bukan **isi vs brief** |

---

## E. BUKTI & MUTU KESELURUHAN

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **16** | Kwitansi mutu otomatis | 🔴 **BELUM** | tidak ada mesin. `kwitansi` hanya muncul di `app/jenis.py` sebagai nama dokumen, bukan kwitansi mutu |
| **17** | Buku emas per jenis | 🔴 **BELUM** | hanya 1 `contoh_buku.json` (buku umum). Belum ada buku emas per jenis |
| **18** | Uji bergigi semua gerbang baru | 🟡 **SEBAGIAN** | gerbang **lama** bergigi (v1–v4, j2, placeholder, penanda = semua terbukti). Gerbang **baru** (#4–#16) belum ada, jadi belum bisa bergigi |
| **19** | Buku contoh nyata per jenis | 🔴 **BELUM** | 0 buku nyata per jenis. Yang ada: 1 buku umum 479.118 byte |

---

## F. BOOK CHAPTER

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **20** | Profil + mode rakit chapter | 🔴 **BELUM** | tidak ada kode book chapter. Baru ada `SPESIFIKASI.md` (dokumen) |

---

## 🎯 YANG PALING MENDESAK — 3 utang nyata

| Prioritas | Nomor | Kenapa mendesak |
|---|---|---|
| **1** | **#4 Daftar Pustaka WAJIB** | Bos sudah putuskan, kode belum ikut. **Buku tanpa pustaka bisa terbit** |
| **2** | **#2 Profil per jenis** | tanpa ini #5, #6, #9, #20 **semua buntu** |
| **3** | **#5 + #6 profil di mesin & gerbang** | monograf sekarang keluar **14×20 (SALAH)** |

---

## ⚠️ 4 keputusan yang MASIH menunggu Bos

| # | Keputusan | Usulan Wulan |
|---|---|---|
| 1 | Judul bab buku referensi = TNR 16 pt? | Ya |
| 2 | Gutter A5/B5 = 0? | Ya |
| 3 | Buku umum: 14×20 atau B5? | **B5** (ikut skill) |
| 4 | Gaya gambar buku umum: flat atau 3D kartun? | perlu kata Bos |

---

## 4 fakta yang Wulan TEMUKAN saat mengukur (di luar daftar)

| # | Temuan | Dampak |
|---|---|---|
| 1 | `periksa_font.py` **tidak pernah jalan di produksi** | produksi bisa menerbitkan buku dengan font hilang tanpa tahu |
| 2 | Font Trajan di image = **0** | konsisten dengan 0/9 — bukan bug, memang belum diunggah |
| 3 | `halaman_perkiraan()` masih **360 kata/halaman** | daftar isi & indeks bisa meleset |
| 4 | `tone_menulis` hanya 3 jenis | monograf/ajar akan menulis dengan nada **"Anda" profesional** — salah untuk karya akademik |

---

## Aturan yang Wulan pegang

| Aturan | Arti |
|---|---|
| **Tidak mencentang tanpa bukti** | hasil uji / berkas nyata / render |
| **Ukur dulu, klaim kemudian** | semua angka di atas dari `grep`/`ls`/`python` |
| **Angka turun itu JUJUR** | asersi 20→19 karena entri dihapus, bukan pagar melemah |
| **Mesin kemarin DIPAKAI** | tidak ada yang dibangun ulang |

---

*Diukur Wulan 23 Oktober 2026 dari `main` = `1d7ec9d`. Bukan klaim.*
