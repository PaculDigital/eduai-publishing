# 🔒 PUTUSAN FINAL — PAGAR PENCARIAN JURNAL MANUAL (06 Okt 2026)

<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Jawaban Bos 06 Okt 2026 (verbatim):
> *"1. Ya manual · 2. Ya · 3. Sejak awal pemakaian · 4. 1. Pencarian = 1 judul /
> keyword manual user tulis"*
>
> Status: **PUTUSAN TERKUNCI — siap dikoding (menunggu perintah Bos).**

---

## ✅ ATURAN LENGKAP (FINAL, tidak ada yang menggantung)

| # | Hal | Putusan Bos |
|---|---|---|
| 1 | Yang dihitung | **Pencarian MANUAL user saja** (Auto AI tidak dihitung) |
| 2 | Harga token | **1 token per pencarian** |
| 3 | Hitungan minggu | **SEJAK AWAL PEMAKAIAN user** (bukan Senin) |
| 4 | Takaran | **1 pencarian = 1 judul / keyword manual yang user tulis** |

---

## 📊 CARA KERJANYA (lengkap)

```
Hari ke-0 (user pertama kali pakai):
        ↓
┌──────────── SIKLUS 7 HARI MILIK USER ────────────┐
│  Pencarian manual ke-1  →  GRATIS                │
│  Pencarian manual ke-2  →  GRATIS                │
│  ───────────────────────────────────────────     │
│  Pencarian manual ke-3  →  1 TOKEN               │
│  Pencarian manual ke-4  →  1 TOKEN               │
│  dst. → token                                    │
└──────────────────────────────────────────────────┘
        ↓ genap 7 hari sejak pemakaian pertama
   JATAH SEGAR: 2× gratis lagi
```

**Contoh nyata:**
| Kejadian | Hitungan |
|---|---|
| User mulai pakai 6 Okt | siklus: 6 Okt → 12 Okt |
| 6 Okt cari manual 2× | gratis dua-duanya |
| 7 Okt cari manual 1× | **1 token** |
| 13 Okt (siklus baru) cari lagi | **gratis 2× lagi** |

---

## 🔒 PAGAR PENDUKUNG (tetap wajib)

| # | Pagar | Alasan |
|---|---|---|
| 1 | Hitungan **di SERVER (DB)**, bukan browser | Hapus cookie ≠ jatah baru |
| 2 | Hitungan **per USER** | Bikin 10 workspace ≠ 20 gratis |
| 3 | **Titik awal** dicatat: `tanggal_mulai` + `jumlah_dipakai` | Siklus 7 hari mulai dari SANA |
| 4 | Jatah **tidak menumpuk** | Tidak dipakai → hangus, bukan jadi 4 |
| 5 | **Jejak audit**: siapa · kapan · judul/kata kunci | Kalau pola aneh, Bos bisa lihat |
| 6 | Nada **hangat** (aturan notifikasi EduAi) | *"Jatah coba minggu ini sudah dipakai. Tersedia lagi tanggal 13 ya 😊"* |

---

## 🎯 CONTOH TAMPILAN (usul Wulan)

**Saat masih gratis:**
```
🔎 Cari Referensi                          [ 1 token ] ← harga selalu tampak
   [ kualitas produk, brand image           ]
   [ 🔍 Cari ]

   💚 Kamu masih punya 1 pencarian gratis
   (jatah gratis diperbarui 13 Okt 2026)
```

**Saat jatah habis:**
```
🔎 Cari Referensi                          [ 1 token ]
   [ kualitas produk, brand image           ]
   [ 🔍 Cari ]  ← memotong 1 Token Revisi

   Sisa Token Revisimu: 5
```

⇒ Harga **selalu tampak di depan** — user tahu sebelum menekan. **Tidak ada kejutan.**

---

## ⚠️ CATATAN WULAN

1. **"Sejak awal pemakaian" punya satu kelemahan** yang Wulan wajib sebut:
   siklus **tiap user berbeda tanggalnya** (user A tanggal 6, user B tanggal 20).
   ⇒ Ini **bukan masalah** (server yang hitung), tapi **lebih sulit diaudit mata**
   daripada "semua mulai Senin". Wulan tetap ikut putusan Bos; hanya mencatat
   ini supaya sadar konsekuensinya.
2. **"Awal pemakaian" perlu didefinisikan pastinya**: apakah (a) saat user
   **daftar akun**, atau (b) saat user **pertama kali mencoba pencarian**?
   Wulan condong **(b)** — kalau pakai (a) dan user baru daftar lalu tidak pakai
   3 bulan, siklusnya sudah "kadaluarsa" berkali-kali (tidak masalah, tapi aneh).
3. **Semua ini BELUM ADA di kode** — `pustaka.py` belum punya konsep tiket,
   siklus mingguan, atau token pencarian.

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **PUTUSAN LENGKAP & TERKUNCI** (4 pertanyaan Wulan sudah dijawab Bos)
- [ ] Satu klarifikasi kecil: "awal pemakaian" = saat daftar atau saat coba pertama?
- [ ] DILARANG dikoding sebelum Bos bilang mulai
