# 💡 IDE WULAN — "FILE LINK JURNAL" DI SETIAP WORKSPACE (06 Okt 2026)

<!-- ⛔ SOT: IDE — DILARANG DIKODING -->
> # ⛔ IDE / USULAN — **DILARANG dikoding** sampai Bos bilang "mulai".
> Isi berkas ini = **gagasan menunggu putusan Bos**, BUKAN keadaan kini dan
> BUKAN rencana kerja aktif. ❌ JANGAN dibaca sebagai status proyek.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Menjawab arah Bos: *"saya mau ada 1 halaman/file yang berisi link jurnal dari
> masing-masing workspace. Jadi tiap workspace selalu mempunyai file/halaman
> link download artikelnya."*
> Status: **BAHAN DISKUSI.** Belum diputuskan. DILARANG dikoding.

---

## 🎯 IDE INTI (sederhana & masuk akal)

**Setiap workspace punya SATU berkas bernama `Link Jurnal.txt`.**

Berisi daftar link artikel untuk workspace itu — rapi, berkelompok per topik.
Berkas ini **berkas biasa** di dalam workspace, jadi:
- muncul di daftar berkas (seperti naskah & PDF lain),
- bisa **dibuka & diedit** (OnlyOffice sudah dukung `.txt`),
- bisa **diunduh**,
- ikut aturan yang sudah ada (tong sampah, kuota, pindah folder) — **nol aturan baru**.

**Kenapa BUKAN "halaman"**: halaman = UI baru + rute baru + mesin baru.
Berkas = **nol mesin baru**, dan langsung dapat semua fitur yang sudah ada
(buka, unduh, hapus, pindah). Ini sejalan aturan Bos *"pakai yang sudah ada"*.

---

## ✅ BUKTI KODE — semua bahannya SUDAH ADA (06 Okt 2026)

| Yang dibutuhkan | Sudah ada? | Bukti terukur |
|---|---|---|
| Wadah (workspace) | ✅ | tabel `folders` + `files.folder_id` (ACC 15Sep26) |
| Berkas `.txt` boleh diunggah | ✅ | `config.py:51` `EKSTENSI_DIIZINKAN` memuat `'.txt'` |
| `.txt` bisa DIBUKA user | ✅ | `onlyoffice.py:40` → `'.txt': 'word'` (tipe word) |
| Pola "fitur membuat berkas" | ✅ | `app/dokumen_baru.py:87` — tulis disk → daftar `files` → set `folder_id` |
| Sumber link | ✅ | `app/pustaka.py` — `doi` + `garuda_id` (+ link pembentuk di baris 719-721) |

⇒ **NOL tabel baru. NOL kolom baru. NOL halaman baru.**

---

## ⚠️ CATATAN PENTING — .md vs .txt

`'.md'` **BELUM** ada di `EKSTENSI_DIIZINKAN`, dan **tidak ada pratinjau** untuk
`.md`. Kalau pakai `.txt`, **sudah pasti bisa** tanpa menambah apa pun.
⇒ **Pakai `.txt`** — jangan `.md`.

---

## 🔄 CARA KERJA YANG WULAN BAYANGKAN (alur)

```
User buka workspace "Skripsi Saya"
   → di dalamnya sudah ada berkas: "Link Jurnal.txt"
   → tekan "Cari artikel" (mesin pustaka yang SUDAH ADA)
   → hasil (judul + penulis + tahun + jurnal + link) DITAMBAHKAN
     ke dalam berkas itu, berkelompok per tanggal/topik
   → user klik link → buka di tab baru → unduh PDF kalau publik
```

Bentuk isi berkas (sederhana, enak dibaca di HP):

```
LINK JURNAL — Skripsi Saya
Diperbarui: 06 Okt 2026

═══ Topik: Kualitas Produk → Keputusan Pembelian ═══
1. Yusnia, Burhanudin AY (2020). Customer Experience, Diferensiasi
   Produk, dan Kualitas Produk terhadap Keputusan Pembelian.
   Jurnal Ilmiah Edunomika.
   🟢 PDF gratis : https://garuda.kemdiktisaintek.go.id/documents/detail/1662547
   🔒 DOI        : https://doi.org/10.29040/jie.v4i01.900
```

---

## 🧠 KENAPA IDE INI MASUK AKAL

1. **Sesuai kebiasaan user.** Mahasiswa sudah paham "folder berisi berkas".
   Tidak perlu belajar konsep baru ("workspace punya lampiran khusus").
2. **Bisa dipakai tanpa fitur pencarian.** Kalau nanti pencarian jurnal
   belum jadi, user tetap bisa **tempel link sendiri** ke berkas itu. Fitur
   pencarian tinggal **menambah** — bukan syarat.
3. **Bertambah terus, tidak hilang.** Karena berkas, riwayat pencarian
   menumpuk rapi (dengan tanggal). Beda kalau halaman — biasanya hanya
   menampilkan hasil terakhir, yang lama hilang.
4. **Aman dari masalah hukum.** Yang disimpan hanya **link/alamat**, bukan
   file artikelnya. Sejalan prinsip Bos: *"JANGAN download artikel, kasih
   daftar LINK."*
5. **Sekali bangun, semua fitur kebagian.** Konversi skripsi→jurnal, hasil
   Belajar, unduhan lain — semuanya bisa **menulis ke berkas ini** atau
   berkas serupa di workspace yang sama.

---

## ❓ YANG MASIH PERLU DIPUTUSKAN BOS

1. **Satu berkas per workspace** (selalu dibuat otomatis saat workspace
   dibuat), atau **dibuat saat user menekan tombol** pertama kali?
2. **Nama berkasnya**: "Link Jurnal.txt" / "Daftar Pustaka.txt" / "Bacaan.txt"
   / nama lain?
3. **ASCII/simbol**: pakai 🟢🔒 atau teks biasa ("Gratis"/"Berlangganan")?
   (simbol bagus di HP, tapi berkas .txt lebih aman dengan teks biasa)
4. **Satu berkas untuk semua topik**, atau **satu berkas per topik**
   (mis. "Link - Kualitas Produk.txt")?
5. **Kalau user hapus berkasnya** — dibuat ulang otomatis, atau dibiarkan
   hilang (hak user)?
6. **Apakah hasil pencarian juga tetap disimpan di dalam app** (biar bisa
   tampil rapi), atau **cukup di berkas** saja?

---

## ✅ PUTUSAN BOS (06 Okt 2026, 21:5x) — SIAP DIKODING

| # | Pertanyaan | **PUTUSAN BOS** |
|---|---|---|
| A | Berkas = cetakan atau tempat menyimpan? | **A1 — CETAKAN (turunan).** Sumber tetap `jurnal_json`. Berkas ditulis ULANG dari data itu tiap kali dibuka/ditekan ⇒ SATU sumber, tidak bisa beda. |
| B | Dibuat kapan? | **B2 — Saat user menekan tombol** (user yang tak butuh tidak dipaksa). |
| C | Satu berkas atau per topik? | **C — SATU BERKAS untuk semua topik.** |
| D | Kalau dihapus user? | **D — DIBUAT ULANG OTOMATIS** (tidak hilang). |

**Status: ✅ DISETUJUI — dikoding 06 Okt 2026.**

**Konsekuensi teknis putusan ini:**
1. **A1** ⇒ `/referensi` (atau halaman workspace) punya tombol "Buat/tampilkan Link
   Jurnal" yang **meng-generate ulang** isi berkas dari `jurnal_json`
   (`jurnal.semua_artikel`) tiap kali ditekan. **TIDAK ada penulisan balik** dari
   berkas ke database (bukan dua arah) ⇒ tidak ada risiko dua sumber.
2. **B2** ⇒ berkas **tidak** dibuat saat folder dibuat (`folder.buat()` TIDAK
   disentuh). Hanya dibuat saat tombol ditekan.
3. **C** ⇒ satu nama tetap, mis. `Link Jurnal.txt`, di dalam workspace terpilih.
4. **D** ⇒ karena A1 (cetakan), berkas yang dihapus **mudah dibuat lagi** —
   tombol yang sama cukup menekan ulang; **tidak perlu logika khusus**.
   Bonus: tidak bisa "hilang" karena sumbernya masih ada.
5. **Nol tabel baru · nol kolom baru · nol halaman baru** — tiru pola
   `dokumen_baru.buat_dokumen_baru()` (`app/dokumen_baru.py:52`), ganti templat
   `.docx` jadi teks awal `.txt`.

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] Kode diperiksa (bahan: semua SUDAH ADA)
- [x] **DIPUTUSKAN Bos: A1 · B2 · C(satu) · D(otomatis)** — 06 Okt 2026
- [ ] Selesai dikoding
