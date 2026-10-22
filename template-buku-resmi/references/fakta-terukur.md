# TEMPLATE BUKU RESMI — FAKTA TERUKUR (22 Okt 2026)

Sumber: `drive.usercontent.google.com/download?id=1RkP3iRj2izBH_tTKgDal7Lg-JZ4qrhV1`
Berkas: 497.163 byte, 25 entri ZIP, `word/document.xml` 131.857 byte
MD5    : 0bb7bc5cdae9a99f489feb87387b64b6
SHA-256: fdd40838829a7f42aa02dbe70fbf5b39b23c774145b56d5ba40ee3b4fec3dfba

**ATURAN BOS:** ini SATU-SATUNYA template buku yang benar dan resmi.
Semua buku mengikuti template ini PERSIS. DILARANG menebak.

Semua angka di bawah DIBACA dari XML (`w:pgSz`, `w:pgMar`, `styles.xml`,
`document.xml`) — bukan perkiraan.

---

## 1. UKURAN HALAMAN (`w:pgSz`)

| Satuan | Lebar | Tinggi |
|---|---|---|
| twip | 7938 | 11340 |
| cm | **14,00** | **20,00** |
| mm | 140 | 200 |
| inch | 5,512 | 7,874 |
| poin | 396,9 | 567,0 |

`w:code="11"` (kode ukuran Word). Konversi: **1 cm = 567 twip**.

## 2. BATAS HALAMAN (`w:pgMar`)

| Sisi | twip | cm | mm |
|---|---|---|---|
| Atas (`top`) | 907 | **1,60** | 16,0 |
| Bawah (`bottom`) | 907 | **1,60** | 16,0 |
| Kiri (`left`) | 578 | **1,02** | 10,2 |
| Kanan (`right`) | 907 | **1,60** | 16,0 |
| Header (`header`) | 720 | 1,27 | 12,7 |
| Footer (`footer`) | 720 | 1,27 | 12,7 |
| Gutter (`gutter`) | 505 | **0,89** | 8,9 |

**LEBAR AREA TEKS** = 7938 − 578 − 907 = **6453 twip = 11,38 cm**
(Template ini memakai *gutter* 505 twip ⇒ batas aman kiri cetak = 578+505 = 1083 twip = 1,91 cm)

## 3. GAYA DASAR DOKUMEN (`docDefaults`)

```
rFonts : minorHAnsi (tema)
sz     : 22 (11 pt)
lang   : en-US
spacing: after=200, line=276, lineRule=auto
```

## 4. GAYA `Normal` (dasar SEMUA paragraf)

```
font  : Times New Roman (ascii, eastAsia, hAnsi, cs)
sz    : 24  -> 12 pt
spacing: after=0, line=240, lineRule=auto  (baris tunggal)
```

## 5. ISI BUKU (paragraf isi — GAYA YANG WAJIB DIPAKAI)

Dibaca dari paragraf isi `Lorem ipsum` (598/948/703/726 karakter):

```
font    : Palatino Linotype   (ascii + hAnsi)
          eastAsia = Calibri
sz      : 20  -> 10 pt
jc      : both  (RATA KANAN-KIRI / justify)
autoSpaceDE : 0
autoSpaceDN : 0
adjustRightInd : 0
lang    : en-ID
```

**Jarak baris paragraf isi:** tidak ditulis di `pPr` ⇒ mewarisi `Normal`
(`line=240 auto` = **baris tunggal**). Ini yang tertulis di XML.

## 6. JUDUL BAB — `Heading1`

```
font   : Trajan Pro  (ascii + hAnsi), cs = Calibri
bold   : YA (w:b)
sz     : 44  -> 22 pt
warna  : 000000 (text1)
spacing: before=100 (beforeAutospacing=1), after=240
garis bawah paragraf : single, sz=4, color=808080 (abu), space=1
autoSpaceDE/DN : 0
outlineLvl : 0
```

## 7. SUB BAB — `Heading2`

```
font  : minorHAnsi (tema) / eastAsia Calibri
bold  : YA (w:b, w:bCs)
sz    : 26  -> 13 pt
spacing: before=40
garis bawah paragraf : single, sz=4, color=808080
latar  : shd fill=F2F2F2 (abu sangat muda)
keepNext + keepLines : YA
lang  : en-ID
outlineLvl : 1
```

## 8. DAFTAR ISI — `TOC1` / `TOC2`

```
tabs : right, leader=dot, pos=5938 twip
basedOn : Normal
```

## 9. HIRARKI YANG ADA DI TEMPLATE

| Urutan | Gaya | Contoh isi |
|---|---|---|
| 1 | `Heading1` | KATA PENGANTAR |
| 2 | `Heading1` | DAFTAR ISI |
| 3 | `Heading1` | BAB I + JUDUL BAB PERTAMA |
| 4 | `Heading2` | 1.1. Judul Sub Bab |
| 5 | `Heading2` | 1.2. Judul Sub Bab |
| 6 | `Heading1` | BAB II + JUDUL BAB KEDUA |
| 7 | `Heading2` | 2.1. Judul Sub Bab |
| 8 | `Heading1` | TENTANG PENULIS |

Sub-sub bab (`a.`, `b.`) memakai gaya `ListParagraph` (3 paragraf di template).

## 10. FONT YANG DISEBUT DI TEMPLATE (urut jumlah)

| Jumlah | Font | Dipakai untuk |
|---|---|---|
| 202 | Palatino Linotype | **isi buku** |
| 70 | Calibri | eastAsia / tema |
| 20 | Adobe Garamond Pro | sampul |
| 3 | Times New Roman | gaya Normal |
| 2 | Elephant | sampul/judul besar |
| 2 | Digory Doodles | hiasan |
| 2 | Roboto | lain-lain |
| 1 | Trajan Pro | **judul bab (Heading1)** |
| — | Nyala | gaya Pa2/Pa5 |
| — | Arial | cs gaya Pa2/Pa5 |

## 11. GAYA KHUSUS LAIN

| Gaya | Keterangan |
|---|---|
| `Pa2` | font Nyala, spacing line=361 atLeast |
| `Pa5` | font Nyala, spacing line=301 atLeast |
| `ListParagraph` | paragraf daftar (sub-sub bab) |

## 12. STRUKTUR BERKAS

Sampul → Hak Cipta (ISBN, editor, penyunting, desain sampul, penerbit,
redaksi, alamat, web, e-mail, Facebook, Twitter, WhatsApp) →
Keterangan Cetak (`Cetakan Pertama, X 2024` · `X halaman; 14 x 20 cm`) →
KATA PENGANTAR → DAFTAR ISI → BAB I → BAB II → TENTANG PENULIS.

Gambar di dalam: 4 media (image2.png 87 KB, image4.png 58 KB,
image3.jpeg 6 KB, image1.emf 640 byte) + image5.png 242 KB, image6.jpeg 36 KB.

---

## CATATAN JUJUR

1. **Jarak baris isi tidak tertulis eksplisit** di paragraf isi. Yang tertulis:
   `pPr` paragraf isi TIDAK punya `w:spacing`, jadi mewarisi `Normal`
   (`line=240 auto`). Kalau Bos ingin isi buku berjarak tertentu (mis. 1,15),
   Bos harus menyebut angkanya — Wulan DILARANG menebak.
2. Font **Trajan Pro**, **Palatino Linotype**, **Adobe Garamond Pro**,
   **Elephant**, **Digory Doodles**, **Nyala** adalah font berlisensi/berbayar.
   Kalau tidak terpasang di mesin penghasil .docx, Word akan MENGGANTI diam-diam
   ⇒ bentuk buku berubah. Perlu dipastikan terpasang.
3. Template ini menyebut ukuran **14 × 20 cm** di halaman hak cipta — COCOK
   dengan `w:pgSz` (14,00 × 20,00 cm). Jadi angkanya sahih.
