# 🚀 MULAI — URUTAN KERJA FITUR JURNAL (06 Okt 2026)

<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Kata Bos 06 Okt 2026 (verbatim): *"Saya mau mulai, dimulai dari mana dulu yang baik"*
>
> Status: **MULAI DIKERJAKAN** (izin Bos sudah ada). Tetap: backup dulu, uji bergigi,
> jangan lompat tahap.

---

## 🔎 KEPUTUSAN AWAL: URUTAN YANG WULAN SARANKAN (OPSI A)

**Wulan sarankan mulai dari: penanda artikel per bab + pagar batas 8.**

**Alasan (bukan tebakan — sudah terukur):**

| Keadaan terukur (baru dicek) | Artinya |
|---|---|
| Aplikasi **hidup**, image `eduai-app:20261006_083031-sot` | ✅ aman mulai |
| Titik mundur ada (`cadangan-pra-sot`, 5 image) | ✅ bisa balik |
| **24 tabel** — `folders`, `files`, `users`, `saldo_token`, `section_state` semua **ADA** | ✅ fondasi lengkap |
| `folders` = id, user_id, nama, warna, ikon, dibuat | ✅ cukup untuk workspace satu tingkat |

### Kenapa fondasi/aturan dulu (bukan tampilan)?

```
Tahap 1: ATURAN & DATA  ← MULAI DI SINI
   (penanda artikel per bab + pagar batas 8)
        ↓
Tahap 2-3: MESIN (perbaikan kecil `bangun_isi`)
        ↓
Tahap 4-6: TAMPILAN (tab Referensi, cari manual, unduh)
        ↓
Tahap 7: WORKSPACE (tampilan folder)
```

⇒ **Alasan:** kalau tampilan dibangun dulu, lalu aturan berubah → **tampilan harus
dirombak** = **kerja dua kali** (yang paling Bos benci).
Aturan duluan = **tidak ada yang dibongkar** di belakang.

---

## 🎯 TAHAP 1 — APA PERSIS YANG DIKERJAKAN

### A. Penanda "artikel untuk BAB berapa"
- Setiap artikel punya penanda bab (dari dropdown user, bukan tebakan mesin).
- Perlu: cara menyimpan kaitan artikel ↔ bab.

### B. Pagar batas 8 artikel manual per bab
- Maks **8** artikel manual per bab (putusan Bos: *8 SELALU*).
- Hitungan di **server**, bukan browser.

### C. Sumber artikel manual (2 cara)
- **A. Tempel DOI** → mesin ambil data dari CrossRef.
- **B. Kotak isian terkunci** (kalau tak ada DOI).
- ❌ Upload PDF **DILARANG**.

⚠️ **Wulan belum memutuskan BENTUK TEKNISNYA** — ini keputusan rancangan yang
**butuh izin Bos** sebelum menyentuh kode:
- Kaitan artikel↔bab disimpan **di mana**? (tabel baru? kolom di `files`? titip di
  kolom yang SUDAH ADA?)
- Mengingat aturan Bos **"jangan bangun yang paralel, titipkan di yang sudah ada"**,
  Wulan **akan cari dulu** apakah ada tempat yang sudah cocok.

---

## 📋 URUTAN LENGKAP (7 tahap, usulan Wulan)

| # | Tahap | Perlu? |
|---|---|---|
| 1 | **Aturan & data**: penanda bab + pagar batas 8 + 2 cara masuk artikel | ⭐ **MULAI SINI** |
| 2 | Perbaikan kecil `bangun_isi()` (terima artikel kiriman) | ya |
| 3 | UI **tab 📚 Referensi** (2 bagian: 🤖 AI + 🔎 user) | ya |
| 4 | Pencarian manual + potong token + jatah 2×/minggu | ya |
| 5 | Tambah artikel manual (2 cara) + audit + tampilan ⚠️ | ya |
| 6 | Unduh PDF → workspace + berkas link jurnal | ya |
| 7 | Workspace tampilan (satu tingkat) | ya |

---

## ⚠️ SEBELUM SENTUH KODE — WAJIB (aturan Bos)

1. **Backup dulu**: `_arsip/pre-<topik>-<tgl>/` + MD5.
2. **Cari dulu komponen yang SUDAH ADA** — jangan bangun paralel.
3. **Uji bergigi**: gerbang WAJIB dibuktikan bisa GAGAL (suntik kerusakan).
4. **Deploy** = `bash jalankan.sh` (build image baru), **bukan** `docker cp` untuk kode.
5. **Lapor jujur** apa yang sudah/belum.

---

## 📋 STATUS (diperbarui 06 Okt 2026 malam)
- [x] Bos memberi izin mulai
- [x] Keadaan terukur: app hidup · image `20261006_182106-sot` · 25 tabel · titik mundur ada
- [x] Urutan 7 tahap disusun; **Tahap 1 = aturan & data** (penanda bab + batas 8)
- [x] **Tahap 1 Langkah 1–6 SELESAI, TERUJI & LIVE** (`LAPORAN_TAHAP1_1..5_*`) —
      kolom · `jurnal.py` · jembatan mesin · `jatah.py` · 7 rute API · `referensi.html`
- [x] Tahap 2 (perbaikan `bangun_isi`) ikut selesai di Langkah 3
- [x] **Tahap 1 Langkah 7 SELESAI, TERUJI & LIVE** (06 Okt 21:07, image
      `20261006_210738-sot`): **sambungan unduh PDF → workspace** —
      `/unduh` + `folder_id`, rute `GET /jurnal/folder-pilihan`,
      dropdown + tombol "unduh ke workspace" di `referensi.html`.
      **2 BUG NYATA ikut dicabut:** (1) `/unduh` selalu gagal
      (`hasil.get('berkas')` vs `'isi'`); (2) halaman Referensi mati untuk
      semua akun (`window.DAFTAR_NASKAH` menimpa daftar naskah server).
- [ ] **SISA:** berkas "Link Jurnal.txt" (IDE, belum diputuskan Bos) ·
      potret tanda ⚠️ "isi terbatas" · uji artikel Garuda sungguhan ·
      uji PDF berbayar lewat UI
- [ ] **MENUNGGU PUTUSAN BOS:** unduh Lucide lengkap (2.102 ikon)?
- 📘 Laporan lengkap: `FLAG_LANJUT_DISINI.md` (blok paling atas)
