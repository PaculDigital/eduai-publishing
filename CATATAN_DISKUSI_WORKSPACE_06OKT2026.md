# 💬 CATATAN DISKUSI — WORKSPACE / PROJECT (06 Okt 2026)

<!-- 📝 SOT: CATATAN DISKUSI — bukan penentu status -->
> # 📝 CATATAN DISKUSI — BUKAN penentu status proyek.
> Berkas ini merekam **bahan pembicaraan** saat itu. Sebagian bisa sudah
> dikerjakan, sebagian belum. ❌ JANGAN dipakai sebagai keadaan kini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> **STATUS: DISKUSI SAJA.** Belum diputuskan, **DILARANG DIKODING** sampai Bos
> membuka bahasan ini lagi. Isi = arah Bos + hasil CEK KODE (bukan dugaan).

---

## 🎯 ARAH BOS (verbatim, 06 Okt 2026)

> "Nah di app eduai kan ada file dan folder. Tapi saya mau ada **workspace /
> project** juga di dalamnya jadi file dan folder bisa ada dalam satu
> project/workspace. Ini maksud saya user bisa kelompokkan project-projectnya
> sendiri."

> "Misal punya file jurnal, atau file dari fitur belajar, atau hasil download
> artikel, atau Harvest artikel jurnal bisa masuk otomatis di workspace-nya."

> "Mungkin suatu saat saya mau menambahkan fitur **pencarian jurnal** yang
> relevan bisa di-download otomatis ke workspace ini. Atau nanti ada fitur
> **konversi skripsi ke jurnal** hasilnya akan masuk ke workspace ini dengan
> rapi."

### Maksudnya (versi sederhana)
**Satu wadah besar** yang mengelompokkan file + folder berdasarkan
**project/pekerjaan** — bukan hanya folder datar seperti sekarang. Lalu
**hasil fitur lain** (unduh artikel, cari jurnal, konversi skripsi→jurnal,
file dari belajar) **masuk otomatis** ke wadah yang sesuai.

### Kenapa Bos mau ini
- File sekarang berceceran — sulit tahu mana milik project mana.
- Fitur baru (cari jurnal, konversi ke jurnal) akan **menghasilkan file** —
  kalau tidak ada wadah, hasilnya menumpuk tak beraturan.
- Workspace = cara alami mahasiswa bekerja: "skripsi saya", "artikel jurnal
  saya", "bahan bacaan saya".

---

## 🔍 HASIL CEK KODE (06 Okt 2026 — terverifikasi ke image live)

### ✅ SUDAH ADA — jangan dibangun ulang

| Yang sudah ada | Letak | Catatan |
|---|---|---|
| Tabel `folders` (id, user_id, nama, warna, ikon, dibuat) | `app/models.py:125-157` | **ACC Bos 15 Sep26** — sudah dipikirkan |
| Kolom `files.folder_id` (nullable, FK ke folders) | `app/models.py:190-194` | NULL = tanpa folder |
| Rute: `/folder/buat`, `/folder/ubah`, `/folder/hapus`, `/folder/pindah` | `app/main.py:639,670,686,702` | 4 rute, **LIVE** |
| Jatah folder per paket + AddOn (+10 folder) | `app/config.py:346-361`, `jatah_folder()` baris 406 | **Sudah jadi mesin bisnis** |
| Warna + ikon folder | `app/config.py:386-400` | Supaya user "sayang" workspace-nya |
| Hapus folder ≠ hapus berkas (jadi NULL) | komentar `models.py:132` | Pengaman sudah dipikirkan |
| Ukuran folder dihitung ke kuota (berkas + versi) | `Folder.ukuran_bytes` | Sudah konsisten |

### ⚠️ BATAS YANG SUDAH DIPUTUSKAN (di kode, 15Sep26)

- **SATU TINGKAT SAJA — folder TIDAK bersarang.** Alasan tertulis di kode:
  *"user HP mudah bingung"*. ⇒ Workspace bersarang = **melawan putusan lama**.
  Kalau mau bersarang, itu **putusan baru Bos**, bukan pelengkap.

### 📍 TITIK MASUK FILE (tempat "auto masuk workspace" akan menempel)

Cuma **2 tempat** yang membuat `FileBerkas`:
1. `app/main.py:889` — unggah manual user
2. `app/dokumen_baru.py:87` — naskah baru dari fitur (belum set folder)

⇒ Fitur baru (cari jurnal, konversi, belajar) **belum ada kode** yang menulis
berkas, jadi **belum ada yang perlu diubah sekarang** — nanti tinggal set
`folder_id` saat berkas dibuat.

### 📌 Catatan penting — fitur yang Bos sebut belum ada

| Fitur | Status di kode |
|---|---|
| Pencarian & unduh jurnal otomatis | **BELUM ADA** |
| Harvest artikel jurnal | **BELUM ADA** (ada skill di luar app, bukan fitur app) |
| Konversi skripsi → jurnal | **BELUM ADA** |
| File dari fitur Belajar | **BELUM ADA** (Belajar sekarang tidak menghasilkan file) |

⇒ Arah Bos = **rancangan masa depan**, bukan perbaikan yang ada.

---

## ❓ PERTANYAAN TERBUKA (untuk didiskusikan nanti)

1. **Workspace = folder tingkat-1 saja, atau folder bersarang?**
   (kode sekarang: satu tingkat, sengaja — "user HP bingung")
2. **Nama di UI**: tetap "Folder" (sudah dipakai), atau diubah jadi
   "Workspace/Project"? Kalau diubah → menyentuh teks di banyak tempat.
3. **Apakah workspace punya sifat lebih dari folder?** Misal: status
   (aktif/selesai), tenggat, warna judul, ringkasan isi.
4. **Aturan auto-masuk**: kalau hasil fitur masuk ke workspace, workspace mana?
   - dipilih user saat itu,
   - atau ada workspace otomatis per fitur (mis. "Artikel Jurnal"),
   - atau workspace terakhir yang dibuka.
5. **Kuota**: apakah workspace ikut dihitung kuota (seperti folder sekarang),
   dan apakah jatahnya tetap dibatasi per paket?
6. **Berkas yang sama di 2 workspace** — boleh, atau satu berkas satu wadah?
7. **Nasib folder lama**: dikonversi jadi workspace, atau dua-duanya hidup?

---

## 🧠 Ide Wulan (BAHAN DISKUSI — belum diputuskan apa pun)

1. **Titip, jangan bangun baru.** Tabel `folders` sudah punya nama/warna/ikon/
   jatah/AddOn. "Workspace" bisa **identik** dengan folder yang sudah ada —
   cukup ganti **cara menampilkan** (kartu besar + jumlah berkas), **nol tabel
   baru**. Ini sejalan aturan Bos "yang ada bisa sinkron".
2. **Auto-masuk = satu parameter.** Karena `folder_id` sudah nullable di
   `files`, fitur baru tinggal mengisi satu nilai saat menyimpan berkas.
   Tidak perlu mesin baru.
3. **Kalau butuh "jenis" workspace** (skripsi / artikel / bacaan), bisa cukup
   **ikon + warna yang sudah ada** — bukan kolom baru.
4. **Bersarang** hanya kalau Bos memang butuh. Kalau ya, pilihan aman =
   tambah kolom `induk_id` di `folders` (self-FK) — **putusan baru**, dan
   UI-nya harus dijaga tetap sederhana di HP.

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
