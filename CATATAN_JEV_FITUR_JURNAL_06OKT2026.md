# ❓ PERLU JEV DI FITUR JURNAL / WORKSPACE? — JAWABAN (06 Okt 2026)

> 🚩 **DIPERBARUI 07 Okt 2026 — CARA PAKAI JEV DI SINI SUDAH USANG.**
> Sebagian isi catatan ini dibuat waktu Wulan **belum membaca dokumentasi resmi**,
> jadi ada **klaim yang keliru & berbahaya** (mis. *"skema Jev tertutup / hanya 3 nama"*,
> *"Jev tidak stabil"*, *"hanya 2 tipe sah"*, *"criteria boleh string"*).
> ⇒ **ACUAN TUNGGAL cara pakai Jev sekarang:** `PANDUAN_PAKAI_JEV.md`
>   + skill `typesafe-jev` (dokumentasi RESMI `docs.typesafe.ai`).
> ⇒ Blok lama **TIDAK dihapus** (riwayat) — tapi **DILARANG dipakai sebagai panduan**.
> ⇒ Penjaga: `_gerbang_skema_jev.py` + `_uji_gigi_skema_jev.py`.



<!-- 📝 SOT: CATATAN DISKUSI — bukan penentu status -->
> # 📝 CATATAN DISKUSI — BUKAN penentu status proyek.
> Berkas ini merekam **bahan pembicaraan** saat itu. Sebagian bisa sudah
> dikerjakan, sebagian belum. ❌ JANGAN dipakai sebagai keadaan kini.

> ## 🚩 DIPERBARUI 07 Okt 2026 — BACA KOREKSINYA DULU
> Kesimpulan **"Jev TIDAK perlu"** di berkas ini **TERLALU LUAS** dan sudah
> **DIKOREKSI BOS**: *"di mana-mana jev selalu terdepan sebelum mesin dan Ai."*
> ⇒ Lihat **`IDE_PERLUASAN_PERAN_JEV_07OKT2026.md`**.
> **Yang MASIH BENAR di sini:** Jev bukan alat untuk **cari artikel/DOI/relevansi**
> (bidang beda) dan **bukan** untuk menilai **MUTU tulisan** (terbukti gagal).
> **Yang DIKOREKSI:** Jev **DIPERLUAS** ke **BENTUK/STRUKTUR/KEBERADAAN** —
> itu bukan mutu, dan justru di situ Jev berguna.
> 🗄️ RIWAYAT — isi di bawah dipertahankan apa adanya sebagai jejak berpikir.

> Pertanyaan Bos 06 Okt 2026 (verbatim):
> *"Apa perlu peran jev di sini sebagai penanda dan penjaga struktur?"*
>
> Status: **JAWABAN WULAN (terukur dari kode).** Belum diputuskan Bos.

---

## 🎯 JAWABAN: **TIDAK PERLU untuk fitur jurnal. TAPI ada 1 tempat Jev memang relevan.**

Wulan pisahkan **2 hal** — karena jawabannya beda:

| Bagian | Jev perlu? |
|---|---|
| **Fitur jurnal** (cari artikel, tambah manual, unduh, workspace) | ❌ **TIDAK PERLU** |
| **Penanda bab** (artikel ini untuk BAB berapa) | ⚠️ **Menarik — tapi Jev bukan alatnya.** Lihat bawah. |

---

## 📌 APA YANG JEV BENAR-BENAR BISA (terukur `satpam.py`)

Jev **hanya menjawab 4 pertanyaan** — semua soal **STRUKTUR bab**:
| # | Pertanyaan Jev | Jawaban |
|---|---|---|
| 1 | Berapa bab yang BENAR-BENAR ada? | angka |
| 2 | Nomor bab semua pakai romawi sah? | ya/tidak |
| 3 | Bab berurutan tanpa melompat? | ya/tidak |
| 4 | Sedalam apa penomoran bertingkat? | 0/2/3/4/5 |

Bentuk jawabannya (`satpam.py:246`):
```
{'ok', 'keputusan' (lolos/tanya/tolak), 'jumlah_bab', 'jumlah_bab_mesin',
 'confidence', 'romawi_sah', 'berurutan', 'kedalaman'}
```

### ❌ Kenapa Jev TIDAK cocok untuk fitur jurnal
| Jev | Fitur jurnal |
|---|---|
| Menghitung **bab** | Mencari **artikel** di internet |
| Soal **struktur dokumen** | Soal **keaslian & relevansi artikel** |
| Tidak punya alat untuk DOI/Scopus/kata kunci | — |

⇒ Jev **tidak tahu apa pun** soal artikel. Bidangnya beda total.

### ❌ Dan menilai mutu = zona Jev SUDAH TERBUKTI GAGAL
Ini **putusan, bukan opini** (06 Okt 2026):
> Jev **HANYA 1 peran** = `periksa()` PETA BAB. **TIDAK ditambah ke modul lain.**
> `nilai_balasan()` **DICABUT 05 Okt** (3 percobaan GAGAL).
> **8 modul lain** = menilai **ISI/MUTU** → wilayah yang Jev **SUDAH TERBUKTI GAGAL**.
> **ATURAN INDUK:** Jev penjaga **STRUKTUR** saja; **GAGAL menilai mutu tulisan.**

⇒ "Artikel ini relevan/nyata?" = **menilai mutu** = **zona yang Jev gagal 3×.**
Memaksakan Jev di sini = **mengulang kesalahan yang sudah dibayar mahal.**

---

## ⚠️ SOAL "PENANDA BAB" (yang Wulan usulkan kemarin)

Wulan usulkan artikel ditandai *"untuk BAB berapa"*. **Apakah itu pekerjaan Jev?**

**TIDAK.** Alasannya:
| Penanda bab untuk artikel | Kerja Jev |
|---|---|
| **User** yang memilih bab dari **dropdown** | Jev **menghitung** bab yang ada |
| Keputusan **manusia**, bukan taksiran | Keputusan **mesin**, dengan keyakinan |
| Tidak butuh AI sama sekali | Panggil AI (jev-1.13 via 9router) |

⇒ **Penanda bab = user memilih (1 klik), bukan Jev menaksir.** Kalau pakai Jev
untuk menebak "artikel ini cocoknya di bab berapa", itu **zona mutu** — Jev gagal.

### 💡 Kalau memang mau "menebak bab" — pilihan yang lebih baik
Kalau Bos ingin mesin **menyarankan** artikel cocoknya di bab berapa:
| Pilihan | Biaya | Risiko |
|---|---|---|
| **Aturan sederhana** (kata kunci bab vs judul artikel) | Rp 0 | Sedang (bisa salah, tapi jujur) |
| **AI biasa** (bukan Jev) | murah | Sedang |
| **Jev** | murah | ❌ **Zona yang sudah terbukti gagal** |
| **User pilih sendiri** ⭐ | Rp 0 | **Nol** |

⇒ Wulan **sangat** sarankan **user pilih sendiri** — dan mesin boleh **menyarankan**
(sebagai saran, bukan penentu). Saran salah = user tinggal ganti.

---

## ✅ DI MANA JEV MEMANG BERGUNA (kaitannya dengan pekerjaan ini)

Jev **relevan** kalau ada **masalah STRUKTUR** — dan itu **SUDAH ada**
pekerjaannya di EduAi:

| Skenario | Jev berguna? |
|---|---|
| Ada fitur baru yang **membaca bab naskah** untuk cari referensi per bab | ⚠️ **Mungkin** — tapi `state.petakan()` sudah melakukan ini dan **SUDAH TERBUKTI**. Jev = lapis tambahan, manfaat kecil. |
| **Cek artikel nyata** | ❌ pakai `audit_doi()` |
| **Cek artikel nyambung** | ❌ pakai `_nyambung()` |
| **Pecah judul jadi variabel** | ❌ pakai `konsep_dari_judul()` |
| **Nilai mutu hasil pencarian** | ❌ zona Jev gagal |
| **Cek naskah punya bab lengkap?** | ✅ **INI kerja Jev** — dan **SUDAH JALAN** (`ai.py:2350`) |
| **Cek struktur naskah sebelum ditulis** | ✅ **INI kerja Jev** — sudah jalan |

⇒ Jadi: **Jev sudah dipakai di tempat yang benar.** Jangan ditambah ke sini.

---

## 📊 RINGKASAN

| Pertanyaan | Jawaban |
|---|---|
| Jev untuk **fitur jurnal**? | ❌ **TIDAK** — bidangnya beda, dan mutu = zona gagal |
| Jev untuk **penanda bab artikel**? | ❌ **TIDAK** — itu keputusan user (dropdown), bukan taksiran |
| Jev untuk **struktur naskah**? | ✅ **YA — dan SUDAH JALAN** (`ai.py:2350`) |
| Alat yang tepat untuk artikel | `audit_doi()` + `_nyambung()` + `konsep_dari_judul()` |

### 🔑 Prinsip induk (jangan dilanggar)
> **Jev = penjaga STRUKTUR (berapa bab, bab mana).**
> **JANGAN dipakai menilai mutu/isi.** Sudah terbukti gagal 3× di wilayah itu.

---

## ⚠️ WULAN WAJIB SEBUT JUJUR

1. Wulan **sudah** pernah **salah** dengan Jev — `nilai_balasan()` 3× gagal
   (05 Okt), dan Wulan pernah salah menyambungkan Jev ke Moda Belajar (ditegur
   Bos). ⇒ Wulan **tidak** mau mengulang kesalahan yang sama.
2. **Risikonya kalau tetap dipaksa:** biaya token keluar, hasilnya tetap perlu
   diperiksa manual, dan **waktu terbuang** — sementara jawabannya (dropdown bab)
   **lebih murah dan lebih akurat**.
3. Kalau Bos punya **alasan lain** yang Wulan belum lihat (mis. ada masalah
   struktur naskah yang belum tertangani), **tolong Bos sebutkan** — Wulan akan
   cek kodenya, bukan langsung menolak.

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] Jawaban: **Jev tidak perlu** di fitur jurnal (bidang beda + zona gagal)
- [x] Penanda bab = **keputusan user (dropdown)**, bukan taksiran Jev
- [x] Jev yang **sudah jalan** (`ai.py:2350`) tetap dipakai untuk **struktur naskah**
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
