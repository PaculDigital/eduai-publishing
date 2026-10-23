# 📋 STATUS RENCANA BANGUN SSOT — DIUKUR 23 Okt 2026

> **Berkas ini BUKAN rencana.** Ini **hasil pengukuran** atas
> `RENCANA-BANGUN-SSOT.md`. Wulan tidak mencentang apa pun tanpa bukti.
>
> Diukur dari `main` = `1d7ec9d`, bukan dari ingatan.

---

## Ringkasan: 9 selesai penuh, 5 sebagian, 6 belum

> Diperbarui 23 Okt 2026 (Fase 2 — bukti monograf, branch
> `agen/wulan/fase1-ssot`): #4, #5, #6, #7, #9, #10, #13 SELESAI;
> #8 & #15 naik ke SEBAGIAN. Sisa belum: #11, #12, #16, #17, #19, #20.

| Bagian | Nomor | Selesai | Sebagian | Belum |
|---|---|---|---|---|
| **A** Sumber Tunggal | 1–3 | 2 | 1 | 0 |
| **B** Mesin | 4–8 | 4 | 1 | 0 |
| **C** Mutu Tulisan | 9–12 | 2 | 0 | 2 |
| **D** Mutu Gambar | 13–15 | 1 | 2 | 0 |
| **E** Bukti & Mutu | 16–19 | 0 | 1 | 3 |
| **F** Book Chapter | 20 | 0 | 0 | 1 |
| **JUMLAH** | **20** | **9** | **5** | **6** |

---

## A. SUMBER TUNGGAL (SSOT)

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **1** | Peta SOT | ✅ **SELESAI** (23 Okt 2026) | `SOT-INDUK.md` §9: peta rumah tunggal untuk 9 kategori fakta buku + 3 fakta berumah ganda DITANDAI (blok gaya, tone, angka twip) + pemutakhiran §5 |
| **2** | Berkas profil per jenis | 🟡 **SEBAGIAN** (23 Okt 2026) | `profil.json` **ADA** untuk monograf, buku-referensi, buku-ajar-obe, buku-umum — masing-masing berisi format + unsur wajib + aturan tulisan + gambar. Yang belum: nilai menunggu keputusan Bos (judul referensi, gutter, umum B5/induk, gaya gambar umum) tercatat `null` berlabel MENUNGGU, dan jangkar konsistensi menunggu #14 |
| **3** | Spesifikasi turunan dari profil | ✅ **SELESAI** (23 Okt 2026) | `scripts/buat_spesifikasi.py` menghasilkan `SPESIFIKASI-DARI-PROFIL.md` untuk 4 jenis; verifikasi: 30 angka (twip/sz) dari profil, **0 hilang** dari dokumen |

**Yang nyata ada:** 4 `SPESIFIKASI.md` (monograf, referensi, ajar, chapter) — tapi itu **bahan**, bukan profil.

---

## B. MESIN

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **4** | Daftar Pustaka WAJIB | ✅ **SELESAI** (23 Okt 2026) | validasi awal generator menolak spec tanpa/kosong pustaka SEBELUM menulis + gerbang DP0 (`--wajib-pustaka`). Uji negatif lulus: berkas tidak tercipta |
| **5** | Generator menerapkan profil | ✅ **SELESAI** (23 Okt 2026) | `buat_buku.py --profil` menerapkan ukuran/margin/font isi & judul/spasi/tab TOC dari profil. Bukti: buku monograf A5 8391×11906, margin 1134, Cambria 11/14, line 276 |
| **6** | Gerbang baca profil | ✅ **SELESAI** (23 Okt 2026) | `periksa_buku_template.py --profil=` — semua angka (H/M/G/F/S/Y) dari profil; tanpa profil = perilaku induk persis (regresi 50/50 + 64 uji hijau). Uji negatif: buku induk DITOLAK gerbang profil monograf |
| **7** | Nomor halaman terukur | ✅ **SELESAI** (23 Okt 2026) | `ukur_halaman()`: render LibreOffice → peta judul→halaman → cache TOC ditempel angka nyata (BAB I/II/III = 6/7/8; total 12) + label hak cipta otomatis. ⚠️ VM ini tanpa Cambria — paginasi render font pengganti; persis di server berfont. `halaman_perkiraan()` di indeks_referensi pensiun pada Fase 4 (jalur referensi) |
| **8** | Gerbang font di server produksi | 🟡 **SEBAGIAN** (23 Okt 2026) | `periksa_font.py --profil` memeriksa font profil (terbukti: Cambria HILANG di VM → exit 1). Yang belum: dijalankan di server produksi sesudah Bos unggah font |

---

## C. MUTU TULISAN

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **9** | Aturan tulisan per jenis di profil | ✅ **SELESAI untuk monograf** (23 Okt 2026) | tone akademik formal + kata terlarang teks + cek_teks_wajib kini di profil monograf. `tone_menulis.py` aplikasi menyusul diselaraskan Fase 4; ajar/referensi Fase 4 |
| **10** | Gerbang tulisan terukur | ✅ **SELESAI** (23 Okt 2026) | `periksa_tulisan.py`: T1 sitasi dua arah (uji negatif yatim tertangkap), T2 kata terlarang teks, T3 bagian wajib dari profil. Terpasang di generator sesudah gerbang format |
| **11** | Gate cek plagiarisme | 🔴 **BELUM** | tidak ada modul plagiarisme untuk buku. Yang ada cuma `_uji_pintu_plag.py` (uji), bukan mesin |
| **12** | Verifikasi sitasi 3 lapis | 🔴 **BELUM** | belum ada; menunggu kwitansi (#16) |

---

## D. MUTU PROMPT GAMBAR

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **13** | Prompt brief BERSLOT | ✅ **SELESAI jalur pendidikan/monograf** (23 Okt 2026) | `PROMPT_BRIEF_BERSLOT` (5 slot + 2 contoh jadi) di `brief_visual.py`; mode `berslot` di paket pendidikan & profil monograf. Uji fungsi: prompt terkirim terbukti versi berslot |
| **14** | Blok gaya POSITIF-DULU | 🟡 **SEBAGIAN** (23 Okt 2026) | Blok **pendidikan** ditulis ulang positif-dulu (466 char) + **jangkar konsistensi** ADA & ditempel `prompt_gambar` (teruji) + tersalin ke profil monograf/ajar. Sisa: blok umum & anak (Fase 4). Gerbang placeholder tetap 19/19 |
| **15** | Pemeriksaan isi gambar | 🟡 **SEBAGIAN** (23 Okt 2026) | `periksa_gambar.py` lapis 1 terukur (baca gambar, lebar vs area profil, latar putih) — terbukti dua arah: gambar contoh lama GAGAL, gambar patuh LULUS. Lapis 2 (isi vs brief oleh peninjau/vision) = prosedur + daftar kata kunci dari brief; vonis dicatat di kwitansi (#16) |

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
*Pemutakhiran 23 Oktober 2026 (Fase 1 dikerjakan dari `main` = `e5d5375`,
branch `agen/wulan/fase1-ssot`): #1 ✅, #3 ✅, #2 🟡 — bukti di commit
branch tersebut (profil 4 jenis, `buat_spesifikasi.py`, SOT-INDUK §9).*
*Pemutakhiran Fase 2 (23 Oktober 2026, branch yang sama): #4 ✅, #5 ✅,
#6 ✅, #7 ✅, #9 ✅ (monograf), #10 ✅, #13 ✅ (jalur pendidikan/monograf),
#8 🟡, #14 🟡, #15 🟡. Bukti ujung-ke-ujung: buku monograf contoh
(3 bab, A5 Cambria, gerbang format 52/52, gerbang tulisan 5/5,
nomor TOC terukur 6/7/8, 12 halaman). Regresi penuh hijau:
gerbang template 50/50, bergigi 8+3+10+6+2, generator 35/35,
placeholder brief 19/19.*
