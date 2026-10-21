# 📋 RINGKASAN DISKUSI — FITUR JURNAL & WORKSPACE EDUAI (06 Okt 2026)

> **Sesi diskusi dengan Bos — TIDAK ADA KODING.** Semua materi = rancangan.
> Isi sesi: workspace/project, harvest jurnal, 2 jalur pencarian, pagar token,
> tambah artikel ke bab, peran Jev.
> Rincian tiap topik ada di **22 berkas terpisah** (daftar di bagian akhir).

---

## 1️⃣ WORKSPACE / PROJECT — "BISA"

**Arah Bos:** user bisa mengelompokkan file & folder jadi satu project/workspace.
Hasil fitur lain (unduh artikel, jurnal, konversi skripsi→jurnal) masuk otomatis.

**Hasil cek kode (TERUKUR):**
| Hal | Kenyataan |
|---|---|
| Tabel `folders` | ✅ **SUDAH ADA** (`models.py:124`) — nama, warna, ikon, jatah, 4 rute hidup |
| `files.folder_id` | ✅ **SUDAH ADA** → berkas bisa ditunjuk "milik workspace mana" |
| Jumlah folder di produksi | **0 folder** · 51 berkas tanpa folder |
| Aturan tertulis di kode | *"SATU TINGKAT saja (tidak bersarang) — user HP mudah bingung"* |
| Bisa banyak workspace? | ✅ **BOLEH** (`Folder.user_id`) — user bebas punya banyak |

**Kesimpulan Wulan:** **BISA**, pondasinya sudah berdiri. Butuh **1 keputusan Bos**
(bersarang atau satu tingkat). **Nol tabel baru.**

---

## 2️⃣ HARVEST JURNAL — "SUDAH JALAN"

**Nama aslinya:** `app/pustaka.py` — **LIVE**, bukan rencana.

| Sumber | Status (uji nyata) |
|---|---|
| Scopus | ⚠️ kunci API belum ada → dilewati |
| OpenAlex | ✅ jalan |
| Garuda (jurnal Indonesia) | ✅ jalan |
| CrossRef | ✅ jalan |

Alur: ambil tema → kata kunci 2 bahasa → cari 4 sumber → buang duplikat →
**audit DOI ke CrossRef** → saring relevansi → jadi daftar.
**Bukti uji:** 35 hasil mentah → **1 lolos** (saringan sangat ketat).

**Link nyata ADA:** `pustaka.py:719` sudah membentuk link Garuda
(`garuda.kemdiktisaintek.go.id/documents/detail/...`).
⇒ **TIDAK benar** kalau dikatakan mesin "tidak tahu alamat webnya".

---

## 3️⃣ UNDUH ARTIKEL KE WORKSPACE — "TERBUKTI BISA"

Wulan **uji langsung di server produksi**:
```
status: 200
content-type: application/pdf
ukuran: 406.375 byte
awalan isi: b'%PDF-1.5'   ← PDF SUNGGUHAN
```
⇒ Server **sanggup** mengunduh PDF artikel — rencana Bos **bukan khayalan**.

**Aturan pagar:** server **menguji dulu** → dapat `%PDF` = 🟢 gratis;
dapat halaman berbayar = 🔒 berlangganan (jujur, kasih link saja).
**Hak cipta:** artikel berbayar **tidak ditembus** (sejalan prinsip Bos sendiri).

---

## 4️⃣ DUA JALUR PENCARIAN — "TEGASAN BOS, WULAN SETUJU"

| | 🤖 **Auto AI** | 🔎 **Manual (user)** |
|---|---|---|
| Siapa tentukan | **AI** (dari judul naskah) | **User** (ketik sendiri) |
| Waktu | saat dokumen baru/kosong | kapan saja |
| Gunanya | **MENULIS bab** (bahan → bab) | **MENCARI bahan** untuk dibaca |
| Keluaran | **bab baru** + daftar pustaka | **daftar artikel** (link) |

⇒ **Tidak bentrok** — beda **waktu** (sebelum vs sesudah ada judul) dan beda
**pekerjaan** (menulis vs mencari).

**Hasil cek kode:**
- **Auto AI: ✅ SUDAH JALAN** — `kerangka.py:178` + `ai.py:4092` +
  tombol `mulai.html:249` ("Susun kerangka BAB I").
- **Manual: ❌ BELUM ADA UI** — mesinnya (`pustaka.cari_semua`) sudah lengkap.

**Temuan penting:** "AI rekomendasi judul" yang Bos bayangkan = **⚠️ SETENGAH**.
Yang ada = `contoh_judul()` (`alur_awal.py:377`) — **daftar statis per bidang**,
**BELUM pakai AI** (tidak membaca judul user).

---

## 5️⃣ PAGAR PENCARIAN MANUAL — **PUTUSAN BOS (TERKUNCI)**

| # | Hal | Putusan |
|---|---|---|
| 1 | Yang dihitung | pencarian **MANUAL** saja (Auto AI tidak) |
| 2 | Harga | **1 token per pencarian** |
| 3 | Jatah gratis | **2× per MINGGU** |
| 4 | Siklus | **sejak awal pemakaian** user |
| 5 | Takaran | **1 pencarian = 1 judul/keyword** |
| 6 | Lewat 2× | **kena token** |

**6 pagar pendukung:** hitungan **di server** (bukan browser) · **per user**
(bukan per workspace) · jatah **tidak menumpuk** · ada **jejak audit** ·
nada **hangat** · harga **selalu tampak** sebelum ditekan.

---

## 6️⃣ AUTO AI — **PUTUSAN BOS (TERKUNCI)**

| # | Hal | Putusan |
|---|---|---|
| 1 | Biaya | **GRATIS sampai kerangka**; token hanya saat **menulis bab** |
| 2 | Kapan jalan | saat **tombol ditekan** (bukan otomatis) |
| 3 | Masuk jatah 2×/minggu? | **TIDAK** — mekanisme sendiri |
| 4 | Pagar gagal | ✅ **SUDAH ADA** (`ai.py:4166`): gagal → token dikembalikan |

⚠️ Poin **3 diskusi (tampilkan daftar artikel sebelum bayar)** = belum diputuskan.

---

## 7️⃣ SAMBUNGAN AUTO → MANUAL — "BISA, TIDAK RUMIT"

**Temuan:** pagar untuk ini **SUDAH DIPUTUSKAN BOS 26 Sep** (`kerangka.py:11-15`):
> **Q3. Artikel <5 = JUJUR + 3 PILIHAN (ubah kk / lanjut / batal)**

Wulan usul **tambah 1 pintu** → jadi 4:
```
(a) 🔄 Ubah kata kunci — coba lagi (GRATIS)
(b) ➕ Cari sendiri / tambah manual   ← ⭐ sambungan ke manual
(c) ➡️  Lanjut saja pakai artikel ini (bayar token)
(d) ❌ Batal
```
**Kenapa tidak rumit:** mesin Auto AI & Manual **SUDAH SATU**
(`pustaka.cari_semua` + `audit_doi` + `daftar_pustaka_apa7`) → **cuma soal tampilan**.

---

## 8️⃣ ARTIKEL MANUAL MASUK DAFTAR PUSTAKA? — "YA"

**Temuan kunci** (`pustaka.py:696`): syarat masuk daftar pustaka =
**status verifikasi, BUKAN asal artikel.**
```python
if r.get('doi_status') not in ('verified', 'no_doi'): continue
```
⇒ Artikel manual **BISA masuk** — asal **lolos audit yang sama**.

⚠️ **Temuan penting:** `bangun_isi()` (`kerangka.py:354`) masih **cari ulang
sendiri** → belum menerima artikel kiriman. **Perlu 1 perbaikan kecil.**

---

## 9️⃣ FLEKSIBEL TAPI DI DALAM PAGAR — "WULAN SETUJU 100%"

**Arah Bos:** user boleh menambah artikel ke pembahasan bab, **tapi HANYA lewat
mekanisme mesin** — **tidak boleh upload artikel liaran**, demi konsistensi.

**Bentuk yang Wulan usulkan — "2 cara masuk, 1 pintu audit":**
```
A. TEMPEL DOI/LINK  ─┐
                     ├─→ AUDIT DOI ─→ ✅ lolos → masuk naskah + daftar pustaka
B. KOTAK ISIAN      ─┘             └→ ⚠️ tidak lolos → ditampilkan jujur, TIDAK dipakai
```
**Yang DILARANG: upload PDF/berkas liaran.** Tidak ada tombol unggah artikel.

**3 ide Wulan:**
1. ⭐ **"Tempel DOI, mesin urus sisanya"** (pakai `cari_crossref` yang sudah ada)
2. **Kotak isian terkunci** (kalau tidak ada DOI) — bentuk ditentukan mesin
3. 🚨 **Pagar "pengaruh terbatas"** — artikel manual maks **30%**

**Kunci aman:** `doi_status` **hanya hasil audit** — user **tidak bisa mengisi**.
⇒ Artikel manual **tidak bisa mengaku-aku terverifikasi**.

---

## 🔟 PORSI 30% + TAMBAH ARTIKEL DI TENGAH BAB — **PUTUSAN BOS**

| Hal | Putusan |
|---|---|
| Porsi artikel manual | **MAKS 30% per bab** |
| Alasan Bos (verbatim) | *"agar tidak mengganggu core utama pembahasan bab"* |

**Jawaban Wulan:** ✅ **HARUS BISA** — mahasiswa **memang kerja per bab**
(Bab II butuh teori, Bab III butuh metode, Bab IV butuh pembanding).
Mesin per-bab **sudah ada**: `kerangka_bab.py`, `susun_rencana(bab=)`, `petakan()`.

**IDE terpenting Wulan:** 🚨 **"Artikel punya SEBAB"** — setiap artikel ditandai
**dipakai di BAB berapa** (dropdown, bukan ketik bebas).
⇒ Tanpa ini, **"30%" tidak jelas 30% dari apa**, dan artikel Bab II bisa nyasar ke Bab IV.

---

## 1️⃣1️⃣ PERAN JEV — "TIDAK PERLU"

**Pertanyaan Bos:** perlu Jev sebagai penanda & penjaga struktur?

**Jawaban: TIDAK.** Alasan (terukur):
1. **Bidang beda total** — Jev cuma jawab 4 pertanyaan soal **bab**
   (`satpam.py`: jumlah bab, romawi sah, berurutan, kedalaman). Ia **tidak tahu
   apa pun** soal artikel/DOI/Scopus.
2. **Menilai mutu = zona Jev SUDAH TERBUKTI GAGAL** (putusan 06 Okt:
   *"Jev HANYA 1 peran = `periksa()` PETA BAB. TIDAK ditambah ke modul lain"*
   · `nilai_balasan()` DICABUT 05 Okt · 8 modul lain = zona gagal).
3. **Alat lebih baik sudah ada** — `audit_doi()`, `_nyambung()`,
   `konsep_dari_judul()`.
4. **Penanda bab = keputusan USER (dropdown)**, bukan taksiran mesin.

⇒ **Jev sudah dipakai di tempat yang benar** (`ai.py:2350`, struktur naskah).
**Jangan ditambah ke sini.**

---

## 📊 PETA: APA YANG SUDAH ADA vs BELUM

| Fitur | Mesin | UI/Tampilan |
|---|---|---|
| Workspace (`folders`) | ✅ ada | ✅ 4 rute hidup |
| Harvest jurnal (`pustaka.py`) | ✅ ada | ❌ **belum ada halaman** |
| Auto AI (kerangka bab) | ✅ ada | ✅ **LIVE** |
| Cari manual + token | mesin ada | ❌ **belum ada** |
| Unduh PDF ke workspace | ✅ terbukti bisa | ❌ belum ada |
| Tambah artikel manual (2 cara) | audit ada | ❌ belum ada |
| Penanda artikel per bab | ❌ **belum ada** | ❌ belum ada |
| `bangun_isi()` terima kiriman | ❌ **perlu 1 perbaikan** | — |

---

## ❓ YANG MASIH MENUNGGU KEPUTUSAN BOS

1. Workspace: **satu tingkat** atau **bersarang**?
2. Auto AI: **tampilkan daftar artikel sebelum bayar** token?
3. "Tambah manual" saat artikel AI kurang: **gratis** atau **kena token**?
4. Artikel **⚠️ tidak terverifikasi**: ditampilkan atau ditolak?
5. Kalau **AI gagal total (0 artikel)**: porsi 30% **dilonggarkan** atau tetap?
6. Artikel ditandai **"untuk bab berapa"** — setuju?
7. Artikel boleh **dipakai ulang** di bab lain tanpa hitung dobel?
8. Sumber artikel manual yang diizinkan: **hanya Garuda/CrossRef/Scopus**, atau
   boleh situs jurnal kampus juga?

---

## 📁 22 BERKAS DISKUSI (semua di `/opt/data/services/eduai-publishing/`)

**Putusan (4):** `PUTUSAN_PAGAR_TIKET_2X` · `PUTUSAN_PAGAR_2X_PER_MINGGU` ·
`PUTUSAN_FINAL_PAGAR_PENCARIAN` · `PUTUSAN_AUTO_AI`

**Catatan (6):** `CATATAN_DISKUSI_WORKSPACE` · `CATATAN_DISKUSI_HARVEST_JURNAL` ·
`CATATAN_2_JALUR_PENCARIAN` · `CATATAN_AUTO_AI_HARVEST` ·
`CATATAN_JEV_MESIN_PENCARI` · `CATATAN_JEV_FITUR_JURNAL`

**IDE (11):** `IDE_HARVEST_UNDUH_KE_WORKSPACE` · `IDE_FILE_LINK_JURNAL_PER_WORKSPACE` ·
`IDE_TAB_REFERENSI_DUA_JALUR` · `IDE_MESIN_PENCARI_2_JALUR` ·
`IDE_PENCARIAN_JURNAL_BERBAYAR` · `IDE_PENCARIAN_PER_VARIABEL` ·
`IDE_PAGAR_TIKET_COBA_ULANG` · `IDE_2_KASUS_PENCARIAN` ·
`IDE_SAMBUNGAN_AUTO_KE_MANUAL` · `IDE_FLEKSIBEL_DALAM_PAGAR` ·
`IDE_TAMBAH_ARTIKEL_PER_BAB`

**Jawaban (1):** `JAWABAN_ARTIKEL_MANUAL_SITASI`

---

## ⚠️ STATUS
- **DISKUSI SELESAI** (kata Bos: *"Saya rasa cukup untuk diskusi kita"*)
- **DILARANG DIKODING** — menunggu perintah Bos
- Belum ada satu baris kode pun yang ditulis dari sesi ini
