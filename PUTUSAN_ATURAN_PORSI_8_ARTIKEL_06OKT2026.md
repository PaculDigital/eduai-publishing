# 🔒 ATURAN PORSI ARTIKEL MANUAL — FINAL (06 Okt 2026)

<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Putusan Bos 06 Okt 2026 (verbatim):
> *"Ok lantai 8 selalu dan max 8 artikel saja"*
>
> Status: **TERKUNCI & FINAL.** Belum dikoding.

---

## ✅ ATURAN SEDERHANA (satu angka, tidak berubah-ubah)

```
MAKS ARTIKEL MANUAL = 8 PER BAB   ← SELALU, tanpa kecuali
```

**Kenapa ini bagus:**
| Kalau pakai 30% | **Kalau pakai 8 selalu** ⭐ |
|---|---|
| Angka **berubah** tergantung jumlah artikel AI | Angka **tetap** — mudah dipahami |
| AI dapat 2 → maks manual **1** (terkunci) | **8 selalu** — user tidak pernah terkunci |
| User bingung "kok tadi 5, sekarang 1?" | User selalu tahu: **"maks 8"** |
| Rumit dihitung | **Satu angka, satu sumber** |

⇒ **Lebih sederhana** dari 30% — dan **sesuai prinsip Bos** (user tidak dibuat bingung).
⇒ Nada ke user: *"Kamu bisa menambahkan sampai 8 artikel untuk bab ini."*

### Catatan: 30% TETAP berlaku sebagai "pengaman tambahan"
Supaya artikel manual **tidak mendominasi** bab yang artikel AI-nya sedikit:
```
maks manual = 8, TAPI kalau 30% × total ternyata LEBIH KECIL → pakai 30%
```
⚠️ **Wulan TIDAK memutuskan ini** — Bos bilang *"lantai 8 selalu dan max 8
artikel saja"* → **Wulan baca: 8 adalah aturan tunggal.**
Kalau Bos mau 30% tetap jadi pengaman tambahan, tinggal bilang. (Wulan
**tidak** menambahkannya sendiri — hemat prinsip "jangan bikin yang tak diminta".)

---

## 📊 CONTOH NYATA (8 selalu)

| AI dapat | Maks manual | Total artikel bab |
|---|---|---|
| 20 artikel | **8** | 28 |
| 12 artikel | **8** | 20 |
| 5 artikel | **8** | 13 |
| 2 artikel | **8** | 10 |
| **0 artikel** (gagal total) | **8** | 8 |

⇒ **Konsisten** di semua keadaan. **Tidak ada zona tengah yang aneh.**
⇒ Di bab dengan artikel AI sedikit, artikel manual **bisa mendominasi** — tapi
itu **wajar & disengaja** (kalau AI memang tidak dapat, user harus bisa menambal).

---

## 🎯 PUTUSAN LENGKAP SESI DISKUSI (10/10 TERKUNCI)

| # | Hal | Putusan |
|---|---|---|
| 1 | Workspace bentuk | **SATU TINGKAT** (tidak bersarang) |
| 2 | Artikel ditandai per bab | **YA** |
| 3 | Porsi dihitung per bab | **YA** |
| 4 | Tampilkan artikel sebelum bayar | **YA** |
| 5 | Tambah manual | **OK** |
| 6 | Batas artikel manual | **8 SELALU per bab** |
| 7 | Artikel belum terverifikasi | **ditampilkan + user isi DOI** |
| 8 | Artikel dipakai ulang | **YA** |
| 9 | Sumber artikel | **hanya mesin resmi + DOI sendiri** |
| 10 | Sudah lewat proses AI | (Auto AI live) |

---

## 📁 BERKAS DISKUSI (semua di `/opt/data/services/eduai-publishing/`)

**Ringkasan & putusan:**
- `RINGKASAN_DISKUSI_JURNAL_06OKT2026.md`
- `JAWABAN_BOS_9_PERTANYAAN_06OKT2026.md`
- `PUTUSAN_LENGKAP_9_PERTANYAAN_06OKT2026.md`
- `PUTUSAN_ATURAN_PORSI_8_ARTIKEL_06OKT2026.md` ← **berkas ini**

---

## ⚠️ STATUS
- ✅ **SEMUA PUTUSAN TERKUNCI** (workspace, harvest, 2 jalur, pagar token,
  artikel manual, porsi, Jev)
- 🚫 **DILARANG DIKODING** — menunggu perintah Bos
- ✅ **Nol baris kode** ditulis dari sesi diskusi ini
- 📌 Cara lanjut: Bos bilang **"mulai"** → Wulan baca berkas ringkasan + putusan
  di atas → baru kerjakan
