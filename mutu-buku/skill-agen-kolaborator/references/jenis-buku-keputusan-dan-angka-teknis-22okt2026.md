# 📐 JENIS BUKU: KEPUTUSAN BOS + ANGKA TEKNIS (22 Okt 2026)

Lanjutan `template-vs-jenis-buku-22okt2026.md`. Di dokumen itu Wulan menulis
**tiga pertanyaan terbuka** untuk Bos. **Hari itu juga Bos menjawabnya.**
Dokumen ini mengunci jawaban + angka teknis yang turun dari jawaban itu.

---

## 1. ✅ PUTUSAN BOS — template BERBEDA per jenis

**Verbatim:** *"Berarti harus template berbeda per jenis buku yaa. Kalo begitu
saya butuh kamu push skill monograf, buku referensi, buku ajar obe, saja ke
repo untuk dijadikan template. Dan keterangan ukuran buku masing masing font
dll. Yang lengkap yang resmi ada A5,"*

⇒ Jawaban atas pertanyaan #1 & #3 dokumen sebelumnya: **BUKAN satu ukuran
untuk semua.** Yang dijawab "ya" adalah **pertanyaan #2** — Bos setuju skill
jenis boleh punya angka sendiri, dan minta spesifikasinya **dipush ke repo**.

Yang diminta Bos, tepat: **spesifikasi ukuran + font + margin tiap jenis**,
lengkap, resmi, termasuk **A5**. Bukan berkas template jadi.

### Apa yang Wulan push (repo `eduai-publishing`, `main` `a0746bc`)

```
template-buku-resmi/jenis/
├── README.md                       192 baris — perbandingan 7 jenis
├── monograf/SPESIFIKASI.md         134 baris
├── buku-referensi/SPESIFIKASI.md   144 baris
└── buku-ajar-obe/SPESIFIKASI.md    158 baris
```

⚠️ **Yang dipush = SPESIFIKASI (MD), bukan berkas `.docx` A5/B5.** Jangan
sampai agen berikutnya membaca "template sudah ada" lalu memakai generator
14×20 untuk monograf.

---

## 2. Angka resmi per jenis (dari SKILL.md tiap skill, bukan tebakan)

| Jenis | ID | Ukuran | Margin | Font isi | Font judul bab | Spasi | Target |
|---|---|---|---|---|---|---|---|
| Template induk | — | 14 × 20 | 1,60/1,02 | Palatino **10** | Trajan Pro **22** | line 240 | — |
| Monograf | `buku_monograf` | **A5** 14,8 × 21 | 2,0 | **Cambria 11** | Cambria **14** | 1,15 | 150–180 hlm |
| Buku referensi | `buku_referensi` | **B5** 17,6 × 25 | 2,0 | **TNR 12** | TNR **16** ⚠️ | 1,15 | 150+ hlm |
| Buku ajar OBE | `buku_ajar` | **B5** / A5 | 2,0 | **TNR 12** | TNR **16** | 1,15 | — |
| Buku umum | `buku_umum` | **B5** | 2,0 | **TNR 12** | — | 1,15 | 8–12 bab |
| Book chapter | `book_chapter` | **A5** | 2,0 | **Cambria** | Cambria | 1,15 | maks 15 hlm |
| Buku anak | `buku_umum` | **14 × 20** | 1,60/1,02 | Palatino **10** | Trajan Pro **22** | line 240 | — |

⚠️ = skill tidak menetapkan; Wulan usul TNR 16 pt, **belum ACC Bos**.

### Detail khas buku ajar OBE (dari assembly, sudah putusan Bos 17 Agu 2026)
```
TIU/TIK  : TNR 9 pt miring        (w:sz 18)
body     : TNR 12 pt              (w:sz 24)
judul bab: TNR 16 pt              (w:sz 32)
daftar   : TNR 11 pt, before/after 3pt, line 1,15   (w:sz 22)
hanging  : left_indent=0,6cm  first_line_indent=−0,6cm
```
⚠️ Ada **dua angka berbeda** di skill (TIU 9pt vs daftar 11pt) — keduanya sah
untuk keperluan berbeda. Jangan disamakan.

---

## 3. 🚨 JEBAKAN: cm → twip WAJIB `ceil`, bukan `round`

```
twip = cm ÷ 2,54 × 1440
```

Wulan hitung 14,0 ÷ 2,54 × 1440 = **7937**, lalu template asli menunjukkan
**7938**. Wulan hampir menuduh template salah.

**Ternyata Word membulatkan KE ATAS** (7937,008 → 7938). Template asli
**BENAR**.

⇒ Saat membuat `profil.json` baru, pakai **`math.ceil()`**. Kalau pakai
`round()`, gerbang akan GAGAL pada template yang sebenarnya sehat — gagal
palsu yang akan memakan waktu berjam-jam untuk dilacak.

| Ukuran | cm | Twip (w × h) |
|---|---|---|
| 14 × 20 | 14,0 × 20,0 | **7938 × 11340** |
| A5 | 14,8 × 21,0 | **8391 × 11906** |
| B5 | 17,6 × 25,0 | **9978 × 14173** |

| Hal | cm | twip |
|---|---|---|
| Margin 2,0 (A5/B5 semua sisi) | 2,0 | **1134** |
| Indentasi gantung (buku ajar) | 0,6 | **340** |
| Margin kiri template induk | 1,02 | **578** |
| Margin atas/bawah/kanan induk | 1,60 | **907** |
| Header/footer induk | 1,27 | **720** |
| Gutter induk | 0,89 | **505** |

**Lebar area teks:** induk **6453** twip (11,38 cm) · A5 **6123** (10,8 cm) ·
B5 **7710** (13,6 cm)

### `w:sz` = 2 × pt
```
9→18   10→20   11→22   12→24   14→28   16→32   22→44
```

---

## 4. Pembagian WAJIB SAMA vs BOLEH BEDA

### WAJIB SAMA (wajah penerbit — tidak boleh beda per jenis)
1. Urutan: sampul → hak cipta → pengantar → daftar isi → bab → **daftar pustaka** → tentang penulis
2. Judul bab **dua baris** (`BAB I` + `<w:br/>` + judul)
3. Nomor bab **Romawi**
4. Daftar isi: titik pemimpin **literal** + nomor halaman rata kanan
5. Blok tabel: garis `808080`, kepala latar `F2F2F2`
6. Gambar + keterangan `Gambar: …` rata tengah
7. **DAFTAR PUSTAKA wajib ada**
8. Daftar pustaka pakai indentasi gantung

### BOLEH BEDA (dari profil)
Ukuran halaman · margin · font & ukuran isi · font judul · jarak baris ·
unsur isi khas (indeks, TIU/TIK, novelty)

---

## 5. Arsitektur yang disepakati: SATU gerbang, BANYAK profil

```
template-buku-resmi.docx   (INDUK: struktur, gaya, penomoran)
        ↓
jenis/<nama>/profil.json    → ukuran, margin, font, spasi
        ↓
periksa_buku_template.py --profil jenis/monograf/profil.json
        ↓
   57 asersi yang SAMA — angka dibaca dari profil
```

**Kenapa bukan 6 gerbang terpisah:** satu gerbang = satu pelajaran. Ada bug →
diperbaiki sekali. Tambah jenis baru → cukup tambah `profil.json`. Enam gerbang
= enam tempat bug bisa bersembunyi.

---

## 6. 🔴 STATUS JUJUR — apa yang BELUM

| Hal | Status |
|---|---|
| Spesifikasi 3 jenis (MD) | ✅ ADA & sudah di `main` |
| Berkas template induk 14×20 | ✅ ADA |
| Generator + gerbang 57 asersi | ✅ ADA |
| **Berkas template A5** | ⬜ **BELUM** |
| **Berkas template B5** | ⬜ **BELUM** |
| **`profil.json` per jenis** | ⬜ **BELUM** |
| **Gerbang baca profil** | ⬜ **BELUM** |
| **Uji bergigi per profil** | ⬜ **BELUM** |

**Kalimat yang WAJIB diucapkan ke Bos:** *"Kalau sekarang generator dijalankan
untuk monograf, hasilnya TETAP 14×20 cm — dan itu SALAH untuk monograf."*

Jangan pernah bilang "sudah bisa" hanya karena spesifikasinya tertulis.
Spesifikasi ≠ mesin.

---

## 7. Pertanyaan yang masih terbuka untuk Bos

| # | Pertanyaan | Usulan Wulan |
|---|---|---|
| 1 | Font judul bab buku referensi = **TNR 16 pt**? | Ya (skill tidak tetapkan) |
| 2 | Gutter A5/B5 = **0** atau 0,89 cm? | **0** (tanpa jilid) |
| 3 | Book chapter dibuatkan juga? | Ya, nanti |

---

## 8. Urutan pengerjaan (yang Wulan sarankan ke Bos)

| # | Langkah | Alasan urutan |
|---|---|---|
| 1 | Buat **berkas template A5** dari induk (monograf) | beda font paling jelas (Cambria) |
| 2 | Buat **`profil.json`** untuk 4 jenis | tanpa ini gerbang tak bisa baca |
| 3 | Ubah gerbang baca profil (bukan angka mati) | satu gerbang, banyak profil |
| 4 | Uji bergigi: ubah angka profil → gerbang GAGAL | buktikan bukan hiasan |
| 5 | Ulangi B5 (referensi, ajar, umum) | paling mirip induk, paling akhir |
| 6 | Uji 1 buku nyata per jenis | bukti akhir |

---

## 9. Pelajaran cara menyampaikan ke Bos

Saat Bos bertanya *"bagaimana templatenya, apakah disamakan atau ada
perbedaan?"* — **jangan jawab "disamakan" atau "dibedakan" saja.** Yang benar:

1. **Tabel 6 jenis berdampingan** (ukuran, margin, font isi, font judul)
2. **Tunjukkan konfliknya**: template resmi bilang "semua buku persis ini",
   tapi 5 skill lain punya angka sendiri
3. **Sebut apa yang rusak** kalau dipaksa satu (tabel komparasi teori pecah di
   14×20, batas 15 halaman book chapter hilang)
4. **Baru usulkan** satu-induk-banyak-profil
5. **Tutup dengan pertanyaan** yang bukan hak Wulan putuskan

Jangan langsung ngoding profil. Bos yang memutuskan standar penerbit.
