# 📋 STATUS RENCANA BANGUN SSOT — DIUKUR 23 Okt 2026

> **Berkas ini BUKAN rencana.** Ini **hasil pengukuran** atas
> `RENCANA-BANGUN-SSOT.md`. Wulan tidak mencentang apa pun tanpa bukti.
>
> Diukur dari `main` = `1d7ec9d`, bukan dari ingatan.

---

## Ringkasan: 19 selesai penuh, 1 sebagian, 0 belum

> Diperbarui 23 Okt 2026 (Fase 4 — penyebaran ke semua jenis, branch
> `agen/wulan/fase1-ssot`): #14 & #19 SELESAI; sesudahnya Bos
> MENGESAHKAN keempat keputusan — #2 pun SELESAI. Sisa sebagian: #8
> (menunggu font di server produksi). Sisa belum: #20 (Fase 5).

| Bagian | Nomor | Selesai | Sebagian | Belum |
|---|---|---|---|---|
| **A** Sumber Tunggal | 1–3 | 3 | 0 | 0 |
| **B** Mesin | 4–8 | 4 | 1 | 0 |
| **C** Mutu Tulisan | 9–12 | 4 | 0 | 0 |
| **D** Mutu Gambar | 13–15 | 3 | 0 | 0 |
| **E** Bukti & Mutu | 16–19 | 4 | 0 | 0 |
| **F** Book Chapter | 20 | 1 | 0 | 0 |
| **JUMLAH** | **20** | Book chapter mode sendiri | ✅ **SELESAI** (23 Okt 2026) | profil + generator + gerbang chapter DIKOREKSI mengikuti berkas nyata BAB 10 dari Bos (struktur berhuruf, tujuan di Pendahuluan, tanpa abstrak/penulis di kepala, CV sesudah glosarium; gerbang lulus 13/13 pada CONTOH dan pada BERKAS ASLI Bos sendiri); bergigi v6 6/6; emas chapter |

---

## A. SUMBER TUNGGAL (SSOT)

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **1** | Peta SOT | ✅ **SELESAI** (23 Okt 2026) | `SOT-INDUK.md` §9: peta rumah tunggal untuk 9 kategori fakta buku + 3 fakta berumah ganda DITANDAI (blok gaya, tone, angka twip) + pemutakhiran §5 |
| **2** | Profil per jenis | ✅ **SELESAI** (23 Okt 2026) | 4 profil final: semua nilai DIPUTUSKAN Bos (judul referensi TNR 16; gutter A5/B5 = 0; umum B5; gaya umum 3D kartun) & diterapkan — daftar menunggu_keputusan semua profil kosong; keempat jenis lulus gerbang dari profilnya (53/57/53/57) |
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
| **11** | Gate cek plagiarisme | ✅ **SELESAI** (23 Okt 2026) | `cek_kemiripan.py`: paragraf ganda/nyaris sama + irisan 8-gram vs korpus lokal (ambang 5%). JUJUR: kemiripan LOKAL, bukan Turnitin. Bergigi di uji v5 |
| **12** | Verifikasi sitasi 3 lapis | ✅ **SELESAI** (23 Okt 2026) | `verifikasi_sitasi.py`: lapis 1–2 Crossref langsung (DOI Bandura 1977 TERBUKTI; DOI karangan 404 TIDAK-DITEMUKAN); lapis 3 makna = daftar kalimat pemakai untuk peninjau. Entri fiktif jujur PERLU-MANUAL |

---

## D. MUTU PROMPT GAMBAR

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **13** | Prompt brief BERSLOT | ✅ **SELESAI jalur pendidikan/monograf** (23 Okt 2026) | `PROMPT_BRIEF_BERSLOT` (5 slot + 2 contoh jadi) di `brief_visual.py`; mode `berslot` di paket pendidikan & profil monograf. Uji fungsi: prompt terkirim terbukti versi berslot |
| **14** | Blok gaya POSITIF-DULU | ✅ **SELESAI** (23 Okt 2026) | pendidikan ditulis ulang Fase 2; umum (premium-konseptual) ditulis ulang Fase 4; anak sudah positif-dulu. JANGKAR konsistensi ada di ketiga paket & ditempel prompt_gambar — teruji umum/anak/pendidikan; placeholder tetap 19/19 |
| **15** | Pemeriksaan isi gambar | ✅ **SELESAI** (23 Okt 2026) | lapis 1 terukur (`periksa_gambar.py`) + lapis 2 peninjau terprosedur; terbukti ujung-ke-ujung pada gambar uji nyata monograf (lihat #19) |

---

## E. BUKTI & MUTU KESELURUHAN

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **16** | Kwitansi mutu otomatis | ✅ **SELESAI** (23 Okt 2026) | `buat_kwitansi.py` → `<buku>.kwitansi.md`: hasil semua gerbang yang dijalankan + statistik isi + status peninjau jujur. Contoh terbit untuk buku monograf |
| **17** | Buku emas per jenis | ✅ **SELESAI untuk monograf & induk** (23 Okt 2026) | `emas/{monograf,induk}.json` sidik jari struktural SHA-256 + `uji_regresi_emas.py` (SEMUA SAMA). Jenis lain menyusul Fase 4 |
| **18** | Uji bergigi semua gerbang baru | ✅ **SELESAI** (23 Okt 2026) | `uji_bergigi_v5.py` **11/11**: kontrol + suntikan untuk #4, #6, #8, #10, #11, #15, #17 |
| **19** | Buku contoh nyata per jenis | ✅ **SELESAI** (23 Okt 2026) | monograf (52+5), ajar (52+7), referensi (56+5), umum (57+3) — semua dari profil masing-masing + emas regresi 4 jenis SEMUA SAMA + gambar uji nyata monograf. Indeks referensi = tahap perakitan (modul indeks_referensi, nomor terukur dari render — fungsi baru petakan_istilah_terukur) |

---

## F. BOOK CHAPTER

| # | Nomor | Status | Bukti / Alasan |
|---|---|---|---|
| **20** | Book chapter mode sendiri | ✅ **SELESAI** (23 Okt 2026) | profil + generator + gerbang chapter DIKOREKSI mengikuti berkas nyata BAB 10 dari Bos (struktur berhuruf, tujuan di Pendahuluan, tanpa abstrak/penulis di kepala, CV sesudah glosarium; gerbang lulus 13/13 pada CONTOH dan pada BERKAS ASLI Bos sendiri); bergigi v6 6/6; emas chapter |

---

## 🎯 YANG PALING MENDESAK — 3 utang nyata

| Prioritas | Nomor | Kenapa mendesak |
|---|---|---|
| **1** | **#4 Daftar Pustaka WAJIB** | Bos sudah putuskan, kode belum ikut. **Buku tanpa pustaka bisa terbit** |
| **2** | Profil per jenis | ✅ **SELESAI** (23 Okt 2026) | 4 profil final: semua nilai DIPUTUSKAN Bos (judul referensi TNR 16; gutter A5/B5 = 0; umum B5; gaya umum 3D kartun) & diterapkan — daftar menunggu_keputusan semua profil kosong; keempat jenis lulus gerbang dari profilnya (53/57/53/57) |
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
*Pemutakhiran Fase 3 (23 Oktober 2026): #11 ✅, #12 ✅, #15 ✅, #16 ✅,
#17 ✅ (monograf & induk), #18 ✅ (uji v5 11/11), #19 🟡 (monograf lengkap:
buku + gambar uji nyata). Tersisa: #20 (Fase 5) + sebagian #2, #8, #14, #19
(Fase 4 & produksi).*
*Pemutakhiran Fase 4 (23 Oktober 2026): #14 ✅, #19 ✅. Temuan diperbaiki
di perjalanan: cek_teks_wajib sempat dua rumah (disatukan ke
aturan_tulisan); gerbang TB1/TB4 kini membaca profil & generator
menskalakan lebar tabel ke area profil; contoh induk diperbaiki
4 sitasi yatim pustaka (tertangkap gerbang tulisan sendiri);
indeks_referensi dapat jalur halaman TERUKUR dari render.
Regresi penuh hijau: bergigi 8+3+10+6+2+11, generator 35/35,
emas 4 jenis SEMUA SAMA, template 50/50, placeholder 19/19.*

*Pemutakhiran keputusan (23 Oktober 2026): Bos menyetujui keempat
usulan Wulan — diterapkan & terverifikasi: gutter 0 menaikkan asersi
gerbang (monograf/ajar 53, referensi 57); buku umum terbit sebagai
B5 (emas umum ditambahkan; emas induk 14x20 tetap sebagai warisan);
gambar uji umum 3D kartun sesuai brief. Tersisa hanya #8 (font di
server produksi, sisi Bos) dan #20 book chapter (Fase 5).*

*Pemutakhiran Fase 5 (23 Oktober 2026): #20 ✅ — rencana 20 barang
TUNTAS kecuali #8 yang menunggu tindakan di server produksi (font
berlisensi diunggah Bos lalu periksa_font dijalankan di sana).*
