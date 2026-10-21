# ✅ JAWABAN BOS — 9 PERTANYAAN DISKUSI JURNAL (06 Okt 2026)

<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Jawaban Bos 06 Okt 2026 (verbatim):
> *"1. Saya tidak paham · 2. Ok · 3. Ok · 4. Ok · 5. Ok · 6. Saya tidak tahu
> maksudnya · 7. Ok ditampilkan dan user bisa masukkin doi nya · 8. Ok ·
> 9. Hanya mesin pencari yang sudah ditetapkan mesin saja. Jika user mau lain
> bisa masukkan doi nya saja, seperti mekanisme yang sudah kita rancang diatas."*
>
> Status: **TERJAWAB (7 dari 9).** No. 1 & 6 perlu penjelasan Wulan dulu.

---

## ✅ PUTUSAN TERKUNCI

| # | Pertanyaan | Putusan Bos |
|---|---|---|
| 1 | Workspace: satu tingkat atau bersarang? | ❓ belum paham → Wulan jelaskan |
| 2 | Artikel ditandai "untuk BAB berapa"? | ✅ **OK — YA** |
| 3 | Porsi 30% dihitung **per bab**? | ✅ **OK — YA** |
| 4 | Auto AI: tampilkan artikel **sebelum bayar**? | ✅ **OK — YA** |
| 5 | "Tambah manual" gratis atau token? | ✅ **OK** |
| 6 | AI gagal total → porsi 30% dilonggarkan? | ❓ belum paham → Wulan jelaskan |
| 7 | Artikel belum terverifikasi? | ✅ **DITAMPILKAN + user bisa masukkan DOI-nya** |
| 8 | Artikel dipakai ulang di bab lain? | ✅ **OK — YA** |
| 9 | Sumber artikel manual? | ✅ **HANYA mesin pencari yang sudah ditetapkan**; kalau mau lain → **masukkan DOI saja** |

---

## 🎯 PUTUSAN No.7 & 9 (paling penting — bentuk pagarnya)

### No. 7 — Artikel belum terverifikasi
```
3. Blog Sumber Tidak Jelas (2019)...    ⚠️ BELUM TERVERIFIKASI
   → DITAMPILKAN (user tahu)
   → user bisa MEMASUKKAN DOI-nya sendiri
        ↓
     mesin audit DOI itu
        ↓
   ✅ lolos → boleh dipakai sebagai sitasi
   ⚠️ gagal → tetap tidak dipakai
```
⇒ **Bagus, Bos** — ini **memutar kelemahan jadi fitur**: user melihat ada yang
belum terverifikasi, lalu **dia sendiri yang melengkapinya**. User jadi
**ikut menjaga mutu**, bukan cuma menerima.

### No. 9 — Sumber artikel manual
| Jalur | Boleh? |
|---|---|
| **Mesin pencari yang sudah ditetapkan** (Garuda, OpenAlex, CrossRef, Scopus) | ✅ **BOLEH** |
| **DOI yang user masukkan sendiri** | ✅ **BOLEH** (lewat audit) |
| Situs lain / upload PDF / jurnal kampus | ❌ **TIDAK** |

⇒ **Tegas & rapi.** Semua jalan masuk **lewat mesin** → **konsisten**.
Tidak ada "pintu belakang" yang bisa merusak mutu.

---

## ❓ NO. 1 — PENJELASAN WULAN (workspace)

**Yang Wulan maksud "satu tingkat atau bersarang":**

### Pilihan A — SATU TINGKAT (keadaan sekarang di kode)
```
📁 Skripsi Saya
   ├── 📄 Bab 1.docx
   ├── 📄 Bab 2.docx
   └── 📄 link-jurnal.txt

📁 Makalah Semester 7
   ├── 📄 Bab 1.docx
   └── 📄 daftar-pustaka.txt
```
⇒ **Tidak ada folder di dalam folder.** Semua di tingkat yang sama.
Alasan tertulis di kode: *"user HP mudah bingung."*

### Pilihan B — BERSARANG (bisa folder dalam folder)
```
📁 Kuliah
   ├── 📁 Semester 7
   │    ├── 📁 Skripsi
   │    │    ├── 📄 Bab 1.docx
   │    │    └── 📄 link-jurnal.txt
   │    └── 📁 Makalah
   │         └── 📄 Bab 1.docx
   └── 📁 Semester 8
        └── ...
```
⇒ **Lebih rapi kalau banyak**, tapi **lebih rumit di HP** (harus klik masuk-keluar).

### 💡 Rekomendasi Wulan
**Pilihan A (satu tingkat)** — cukup, lebih mudah, sudah sesuai kode sekarang.
Kalau nanti user mengeluh "terlalu banyak workspace", **baru** dipertimbangkan
bersarang. **Alasan Wulan:** user HP + fitur baru → **sederhana dulu**.

---

## ❓ NO. 6 — PENJELASAN WULAN (kalau AI gagal total)

**Situasinya begini:**
Porsi aturan Bos = **artikel manual maks 30% dari total**.
Hitung: `30% × (artikel AI + artikel manual)`.

**Kasus ekstremnya:**
```
Skenario: AI TIDAK menemukan satu artikel pun (0 artikel)
          (misal judulnya sangat khusus / sumber sedang error)

   Kalau porsi 30% tetap dipakai:
      maks manual = 30% × (0 + manual)
      → 0,3 × manual = manual  ← mustahil secara matematika
      → artinya user HAMPIR TIDAK BISA menambah apa pun  ❌
```

### Pilihan A — LONGGARKAN (usul Wulan)
Kalau AI gagal total → **beri batas tetap** (misal maks **10 artikel manual**).
**Alasan:** tidak ada "core" dari AI yang bisa diganggu, jadi user **tidak
terkunci**. Nada: *"AI belum menemukan artikel untuk judul ini. Kamu bisa
menambahkan sendiri sampai 10 artikel ya."*

### Pilihan B — TETAP 30% (kaku)
⇒ User yang judulnya khusus **tidak bisa menambah apa pun**. Fiturnya terasa
**mati** justru saat paling dibutuhkan.

### 💡 Rekomendasi Wulan: **Pilihan A** — longgarkan dengan batas tetap.

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **7 putusan terkunci** (No. 2, 3, 4, 5, 7, 8, 9)
- [x] **1 putusan paling penting** No. 9: hanya mesin resmi + DOI sendiri
- [ ] No. 1 (workspace) → menunggu Bos pilih A atau B
- [ ] No. 6 (AI gagal total) → menunggu Bos pilih A atau B
- [ ] DILARANG dikoding sebelum Bos bilang mulai
