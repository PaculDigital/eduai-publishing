# 📚 Spesifikasi per Jenis Buku

> **Kenapa folder ini ada:** template buku resmi Bayana (14 × 20 cm, Palatino
> 10 pt) **TIDAK berlaku untuk semua jenis buku**. Buku monograf, referensi,
> dan buku ajar punya ukuran & font **berbeda** — sudah ditetapkan di skill
> masing-masing.
>
> **Disahkan Bos 22 Okt 2026:** *"Berarti harus template berbeda per jenis
> buku yaa."* ⇒ **YA.** Satu template induk, banyak profil jenis.

---

## 1. Perbandingan lengkap — ANGKA RESMI

| Jenis | ID dokumen | Ukuran halaman | Margin | Font isi | Font judul bab | Spasi | Target |
|---|---|---|---|---|---|---|---|
| **Template induk** (Bayana) | — | **14 × 20 cm** | 1,60 / 1,02 cm | Palatino Linotype **10 pt** | Trajan Pro **22 pt** | line 240 | — |
| **Monograf** | `buku_monograf` | **A5** 14,8 × 21,0 | 2,0 cm | Cambria **11 pt** | Cambria **14 pt** tebal | 1,15 | 150–180 hlm |
| **Buku Referensi** | `buku_referensi` | **B5** 17,6 × 25,0 | 2,0 cm | Times New Roman **12 pt** | TNR **16 pt** ⚠️ | 1,15 | 150+ hlm |
| **Buku Ajar OBE** | `buku_ajar` | **B5** default / **A5** pilihan | 2,0 cm | Times New Roman **12 pt** | TNR **16 pt** | 1,15 | — |
| **Buku Umum** | `buku_umum` | **B5** 17,6 × 25,0 | 2,0 cm | Times New Roman **12 pt** | — | 1,15 | 8–12 bab |
| **Book Chapter** | `book_chapter` | **A5** 14,8 × 21,0 | 2,0 cm | Cambria | Cambria | 1,15 | **maks 15 hlm** |
| **Buku Anak** | `buku_umum` (jenis anak) | **14 × 20 cm** | 1,60 / 1,02 cm | Palatino **10 pt** | Trajan Pro **22 pt** | line 240 | — |

> ⚠️ = belum ditetapkan skill, usulan Wulan, **perlu ACC Bos**.

## 2. Ukuran halaman dalam twip (untuk generator `.docx`)

> Rumus: `twip = cm ÷ 2,54 × 1440`
> ⚠️ **Word membulatkan KE ATAS**, jadi 14,0 cm = 7937,008 twip → ditulis
> **7938**. Angka template induk (7938 × 11340) adalah **angka Word yang
> benar**, bukan salah hitung. Untuk profil baru pakai `ceil()`, bukan `round()`.

| Ukuran | cm | Twip (w × h) |
|---|---|---|
| **14 × 20** (template induk) | 14,0 × 20,0 | **7938 × 11340** |
| **A5** | 14,8 × 21,0 | **8391 × 11906** |
| **B5** | 17,6 × 25,0 | **9978 × 14173** |

### Batas halaman (margin) dalam twip

| Profil | Atas | Bawah | Kiri | Kanan |
|---|---|---|---|---|
| **Template induk / anak** | 907 | 907 | **578** | 907 |
| **A5 (monograf, book chapter)** | 1134 | 1134 | 1134 | 1134 |
| **B5 (referensi, ajar, umum)** | 1134 | 1134 | 1134 | 1134 |

### Header / footer / gutter

| Profil | Header | Footer | Gutter |
|---|---|---|---|
| **Template induk** | 720 | 720 | 505 |
| **A5 / B5** | 720 | 720 | 0 (belum ditetapkan) ⚠️ |

### Lebar area teks

| Profil | Lebar area teks |
|---|---|
| Template induk | 11,38 cm (**6453** twip) |
| A5 | 10,8 cm (**6123** twip) |
| B5 | 13,6 cm (**7710** twip) |

---

## 3. Ukuran font dalam setengah-poin (`w:sz`)

Nilai `w:sz` = **2 × pt**.

| Jenis font | pt | `w:sz` |
|---|---|---|
| Palatino Linotype isi (induk) | 10 | **20** |
| Trajan Pro judul (induk) | 22 | **44** |
| Cambria isi (monograf) | 11 | **22** |
| Cambria judul bab (monograf) | 14 | **28** |
| TNR isi (referensi/ajar/umum) | 12 | **24** |
| TNR judul bab (referensi/ajar) | 16 | **32** |
| TNR TIU/TIK (ajar) | 9 | **18** |
| TNR daftar (ajar) | 11 | **22** |

---

## 4. Yang WAJIB SAMA untuk semua jenis

Ini **wajah penerbit** — tidak boleh berbeda:

| # | Unsur |
|---|---|
| 1 | Urutan bagian: sampul → hak cipta → pengantar → daftar isi → bab → daftar pustaka → tentang penulis |
| 2 | Judul bab **dua baris**: `BAB I` + `<w:br/>` + judul |
| 3 | Nomor bab **angka Romawi** (I, II, III) |
| 4 | Daftar isi: **titik pemimpin literal** + nomor halaman rata kanan |
| 5 | Blok tabel: garis abu `808080`, kepala tabel latar `F2F2F2` |
| 6 | Gambar + keterangan `Gambar: …` rata tengah |
| 7 | **DAFTAR PUSTAKA wajib ada** (putusan Bos 22 Okt 2026) |
| 8 | Daftar pustaka pakai **indentasi gantung** |

## 5. Yang BOLEH BEDA per jenis

| # | Unsur | Contoh |
|---|---|---|
| 1 | Ukuran halaman | 14×20 / A5 / B5 |
| 2 | Margin | 1,60-1,02 / 2,0 semua sisi |
| 3 | Font & ukuran isi | Palatino 10 / Cambria 11 / TNR 12 |
| 4 | Font judul bab | Trajan Pro 22 / Cambria 14 / TNR 16 |
| 5 | Jarak baris | line 240 / 1,15 |
| 6 | Unsur isi khas | indeks, TIU/TIK, novelty |

---

## 6. Unsur isi khas per jenis — JANGAN DICAMPUR

Format cuma separuh. **Kalau format benar tapi isi salah, hasilnya buku umum berlabel monograf.**

| Jenis | Unsur khas WAJIB |
|---|---|
| Buku umum | naratif populer, tanpa sitasi wajib |
| **Monograf** | **pernyataan NOVELTY**, kebaruan tegas, keterbatasan penelitian |
| **Buku referensi** | **indeks subjek + indeks nama**, tabel komparasi teori tiap bab, posisi penulis |
| **Buku ajar OBE** | **TIU + TIK + Latihan + Checklist** tiap bab, diturunkan dari RPS OBE |
| **Book chapter** | **maks 15 halaman**, glosarium tabel 2 kolom |
| Buku anak | "kamu", kalimat pendek, ilustrasi banyak, larangan budaya ketat |

---

## 7. Ide pemasangan: SATU gerbang, BANYAK profil

**Jangan** membuat gerbang terpisah per jenis. Itu 6 gerbang untuk dipelajari.

**Yang benar:**

```
template-buku-resmi.docx  (INDUK — struktur & gaya dasar)
        ↓  dibaca profil
   jenis/<nama>/profil.json   → ukuran, margin, font, spasi
        ↓
periksa_buku_template.py --profil jenis/monograf/profil.json
        ↓
   57 asersi yang sama, angka dibaca dari profil
```

**Kenapa:** satu gerbang = satu pelajaran. Kalau ada bug, diperbaiki sekali. Kalau ada jenis baru, cukup tambah `profil.json`.

---

## 8. Status — apa yang SUDAH dan BELUM

| Hal | Status |
|---|---|
| Berkas template induk (14×20) | ✅ **ADA** — `../templates/template-buku-resmi.docx` |
| Generator v2 (57 asersi) | ✅ **ADA & LIVE di `main`** |
| Spesifikasi monograf | ✅ **ADA** (berkas ini) |
| Spesifikasi buku referensi | ✅ **ADA** |
| Spesifikasi buku ajar OBE | ✅ **ADA** |
| **Berkas template A5** | ⬜ **BELUM** |
| **Berkas template B5** | ⬜ **BELUM** |
| **`profil.json` per jenis** | ⬜ **BELUM** |
| **Gerbang baca profil** | ⬜ **BELUM** |
| **Uji bergigi per profil** | ⬜ **BELUM** |

### Arti jujur dari tabel di atas

Spesifikasi sudah **tertulis resmi**, tapi **mesinnya belum bisa membuat** buku A5/B5.
Kalau sekarang generator dijalankan untuk monograf, hasilnya akan **tetap 14×20 cm** — dan itu **salah untuk monograf**.

---

## 9. Urutan kerja yang Wulan usulkan

| # | Langkah | Kenapa urutan ini |
|---|---|---|
| 1 | Buat **berkas template A5** dari induk (monograf) | Jenis paling beda font (Cambria) |
| 2 | Buat **`profil.json`** untuk 4 jenis | tanpa ini gerbang tidak bisa baca |
| 3 | Ubah gerbang baca profil (bukan angka mati) | satu gerbang, banyak profil |
| 4 | Uji bergigi: ubah angka profil → gerbang GAGAL | buktikan tidak hiasan |
| 5 | Ulangi untuk B5 (referensi, ajar, umum) | paling akhir karena paling mirip |
| 6 | Uji 1 buku nyata per jenis | bukti akhir |

---

## 10. Yang perlu keputusan Bos

| # | Pertanyaan | Usulan Wulan |
|---|---|---|
| 1 | Font judul bab buku referensi = TNR 16 pt? | **Ya** |
| 2 | Gutter untuk A5/B5 = 0 atau 0,89 cm? | **0** (tanpa jilid) |
| 3 | Book chapter ikut dibuatkan? | **Ya**, nanti |
| 4 | Buku umum tetap B5 (bukan 14×20)? | ✅ sudah di skill |
| 5 | Buku **anak** pakai 14×20 (template induk)? | **Ya** — sudah begitu |

---

*Terakhir diperbarui: 22 Oktober 2026 — Wulan*
