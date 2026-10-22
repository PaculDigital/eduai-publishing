# 📗 Template Buku Resmi — Bayana / EduAi Publishing

> **Satu-satunya template buku yang benar dan resmi.**
> Semua buku WAJIB mengikuti template ini **persis**.
> Dilarang menebak, menghalusinasi, atau mengira-ngira angka.

Dokumen ini untuk **agen AI mana pun** yang akan menghasilkan `.docx` buku.
Baca sampai habis sebelum menulis kode.

---

## 1. Berkas template (SUMBER KEBENARAN)

| Hal | Nilai |
|---|---|
| Berkas | `templates/template-buku-resmi.docx` |
| **MD5** | `0bb7bc5cdae9a99f489feb87387b64b6` |
| Ukuran | **497.163 byte** (~486 KB) |
| Isi ZIP | 25 berkas |
| `word/document.xml` | 131.855 byte |
| Teks | 74 paragraf · 16.600 karakter |

⚠️ **Verifikasi MD5 sebelum dipakai.** Kalau beda, berkasnya sudah diubah —
jangan dipakai, cari yang asli.

```bash
md5sum templates/template-buku-resmi.docx
# harus: 0bb7bc5cdae9a99f489feb87387b64b6
```

### Apa saja di dalam berkas

**Gambar (4):**

| Berkas | Ukuran |
|---|---|
| `word/media/image2.png` | 87 KB |
| `word/media/image4.png` | 58 KB |
| `word/media/image3.jpeg` | 6 KB |
| `word/media/image1.emf` | 640 byte |

**Struktur halaman (urut):**

| Bagian | Isi |
|---|---|
| Sampul | `TULIS JUDUL BUKU KAMU DI SINI` · `Tulis Nama Kamu Di Sini` · `Nama Penerbit, 2025` |
| Hak cipta | ISBN `12345` (placeholder) + editor, penyunting, desain sampul, redaksi, alamat, web, e-mail, Facebook, Twitter, WhatsApp |
| Keterangan cetak | `Cetakan Pertama, X 2024` · `X halaman; 14 x 20 cm` · kalimat hak cipta |
| KATA PENGANTAR | 5 paragraf — semua `Lorem ipsum` |
| DAFTAR ISI | KATA PENGANTAR · BAB I · 1.1 · 1.2 · BAB II · 2.1 · TENTANG PENULIS |
| BAB I | `BAB I` + `JUDUL BAB PERTAMA` (**dua baris**) · 1.1 · 1.2 |
| BAB II | `BAB II` + `JUDUL BAB KEDUA` (**dua baris**) · 2.1 · a. · b. |
| TENTANG PENULIS | Nama Penulis + 2 paragraf `Lorem ipsum` + quotes |
| Penutup | garis putus-putus |

**Keterangan gambar di dalam template:** *"Gambar: Editor Capcut"* ·
*"Gambar: Cut to Cut Split"* · *"Gambar: Contoh Penerapan Delete Left"*

**3 paragraf isi nyata** (bukan Lorem ipsum) tentang **CapCut** — jadi template
ini pernah dipakai untuk buku aplikasi editing video.

---

## 2. ANGKA WAJIB — dibaca dari XML, bukan tebakan

Semua angka di bawah diekstrak langsung dari `word/document.xml` dan
`word/styles.xml`. Satuan asli **twip** (1 cm = 567 twip).

### Halaman

| Hal | Twip | cm |
|---|---|---|
| Lebar | 7938 | **14,00** |
| Tinggi | 11340 | **20,00** |

### Batas halaman

| Sisi | Twip | cm |
|---|---|---|
| Atas | 907 | **1,60** |
| Bawah | 907 | **1,60** |
| Kanan | 907 | **1,60** |
| **Kiri** | 578 | **1,02** |
| Header / Footer | 720 | 1,27 |
| Gutter | 505 | **0,89** |

**Area teks = 6453 twip = 11,38 cm**

⚠️ Batas kiri **lebih kecil** dari kanan (1,02 vs 1,60) — ini untuk jilid.
Jangan "diraikan".

### Isi buku (paragraf)

```
font    : Palatino Linotype
ukuran  : 10 pt (sz 20)
rata    : both (kanan-kiri)
spasi   : warisi Normal (line=240, baris tunggal)
bahasa  : en-ID
```

### Judul bab — `Heading1`

```
font    : Trajan Pro
ukuran  : 22 pt (sz 44)
tebal   : YA
warna   : 000000
spasi   : before=100 · after=240
garis   : bawah paragraf, single, sz=4, warna 808080
```

**PENTING — judul bab DUA BARIS.** Template menulis:

```xml
<w:r><w:t>BAB I</w:t></w:r>
<w:r><w:br/></w:r>
<w:r><w:t>JUDUL BAB PERTAMA</w:t></w:r>
```

`<w:br/>` = pemutus baris. Tampil:

```
BAB I
JUDUL BAB PERTAMA
```

**Dua cara sah membentuknya:**

| Cara | XML | Anjuran |
|---|---|---|
| **A** | satu paragraf Heading1 + `<w:br/>` | ✅ **PALING SETIA** — seperti template |
| B | dua paragraf Heading1 terpisah | boleh, tapi jarak berubah (`before`/`after` dobel) |

### Sub bab — `Heading2`

```
font    : tema (minorHAnsi) / eastAsia Calibri
ukuran  : 13 pt (sz 26)
tebal   : YA (b + bCs)
spasi   : before=40
latar   : shd fill=F2F2F2 (abu sangat muda)
garis   : bawah paragraf, single, sz=4, warna 808080
atribut : keepNext + keepLines
```

### Gaya `Normal` (dasar)

```
font    : Times New Roman 12 pt
```

### Daftar isi — `TOC1` / `TOC2`

```
tab kanan dengan leader titik, posisi 5938 twip
```

### Pengecualian beralasan (BUKAN cacat)

| Kasus | Nilai | Alasan |
|---|---|---|
| Blok kutipan penutup | 16 pt, rata tengah | memang kutipan, bukan isi |
| Halaman administratif | 11 pt | Web / E-mail / Facebook / Twitter / WhatsApp |

---

## 3. Hirarki template

```
Sampul
Hak cipta + keterangan cetak
KATA PENGANTAR                     (Heading1)
DAFTAR ISI                          (TOC1/TOC2, pakai FIELD Word)
BAB I                               (Heading1 + <w:br/>)
    1.1. Judul Sub Bab              (Heading2)
    1.2. Judul Sub Bab              (Heading2)
BAB II                              (Heading1 + <w:br/>)
    2.1. Judul Sub Bab              (Heading2)
        a. Sub Sub Bab              (paragraf)
        b. Sub Sub Bab              (paragraf)
TENTANG PENULIS                     (Heading1)
garis penutup
```
## 4. Skrip — cara pakai

Semua skrip **Python 3 murni**, tanpa dependensi luar (cukup stdlib).

### 4.1 `scripts/baca_template.py` — baca setelan template

```bash
python3 scripts/baca_template.py                        # teks rapi
python3 scripts/baca_template.py --json                 # JSON
python3 scripts/baca_template.py --berkas lain.docx     # berkas lain
```

Gunanya: **melihat** angka sah sebelum menulis kode. Kalau ragu, jalankan ini —
jangan menebak.

### 4.2 `scripts/periksa_buku_template.py` — GERBANG

```bash
python3 scripts/periksa_buku_template.py buku-anda.docx
echo $?      # 0 = LULUS, 1 = GAGAL
```

**WAJIB dijalankan sebelum `.docx` diserahkan.** 20 asersi:

| Kelompok | Asersi |
|---|---|
| Halaman | H1 ukuran 14×20 cm · H2 batas semua sisi · H3 area teks |
| Font isi | F1 font Palatino · F2 ukuran 10 pt · F3 rata both |
| Judul bab | F4 font Trajan Pro · F4b 22 pt · F4c tebal · **J2a SEMUA pakai `<w:br/>`** · **J2b nomor Romawi sah** · **J2c tepat 2 baris** |
| Sub bab | F5 13 pt · F5b tebal |
| Hirarki | J1 minimal 1 Heading1 |

### 4.3 `scripts/uji_bergigi.py` — bukti gerbang bisa GAGAL (format)

```bash
python3 scripts/uji_bergigi.py     # 8/8 harus tertangkap
```

Menyuntik 8 kerusakan ke **salinan** (template asli tidak disentuh):

| # | Kerusakan |
|---|---|
| D1 | halaman 14×20 → 16×24 |
| D2 | batas kiri 1,02 → 2,0 cm |
| D3 | batas atas 1,6 → 2,54 cm |
| D4 | font isi Palatino → Cambria |
| D5 | ukuran isi 10 → 12 pt |
| D6 | judul bab Trajan Pro → Arial |
| D7 | judul bab 22 → 18 pt |
| D8 | isi rata both → kiri |

### 4.4 `scripts/uji_bergigi_j2.py` — bukti gerbang bisa GAGAL (judul bab)

```bash
python3 scripts/uji_bergigi_j2.py  # 3 LULUS / 0 GAGAL
```

| # | Kasus | Harapan |
|---|---|---|
| A | template asli | J2 LULUS |
| B | `<w:br/>` dibuang → judul menyatu | J2 **GAGAL** |
| C | `BAB I` → `BAB 1` (bukan Romawi) | J2 **GAGAL** |

---

## 5. Hasil uji terakhir (22 Okt 2026)

```
template asli                        → 20 LULUS / 0 GAGAL
uji_bergigi.py    (8 suntikan format) →  8/8 tertangkap
uji_bergigi_j2.py (2 suntikan judul)  →  2/2 tertangkap
periksa --wajib-lebih=1               →  EXIT 1  (terbukti bisa gagal)
```

---

## 6. 🪤 JEBAKAN — WAJIB DIBACA (semua sudah kena)

Ini bukan teori. Semua di bawah ini **benar-benar menjatuhkan Wulan** dan
membuat kesimpulan palsu. Agen lain: jangan ulangi.

### J1. Regex `<w:t[^>]*>(.*?)</w:t>` BOCOR

`(.*?)` menyeberang tag. `<w:t>Web</w:t></w:r><w:r>...<w:t>Facebook` terbaca
`"Web</w:r><w:r>...<w:t>Facebook"`.

Akibat: **2× menuduh template rusak padahal sehat.**

```python
# ❌ SALAH
re.findall(r'<w:t[^>]*>(.*?)</w:t>', xml, re.S)

# ✅ BENAR
re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', xml)
```

### J2. `<w:br/>` HILANG saat ekstraksi → judul bab terlihat menyatu

Ekstraksi `<w:t>` membuang `<w:br/>`, jadi `BAB I` + `JUDUL` terbaca
`"BAB IJUDUL"`. Akibat: **2× salah menyimpulkan template menyatu.**

```python
# Ganti DULU sebelum ekstraksi:
p2 = re.sub(r'<w:br\s*/>', '<w:t>«BR»</w:t>', p)
```

### J3. Daftar Isi memakai FIELD Word

Paragraf TOC punya `w:fldChar` / `w:instrText`. Kalau tidak dibuang, terbaca
sebagai "isi buku" → gerbang menuduh fontnya salah (**gagal palsu**).

### J4. Ukuran halaman ada di `w:pgSz`, bukan di teks

Template menyebut "14 x 20 cm" di teks DAN di `pgSz`. Ambil dari `pgSz`.

### J5. Menyaring daftar dengan regex VALIDASI = gerbang buta

```python
# ❌ SALAH — judul RUSAK justru TERBUANG, tak pernah dihakimi:
bab = [(t, p) for t, p in peta if ROMAWI.match(t)]

# ✅ BENAR — kumpulkan SEMUA berawalan BAB, BARU hakimi:
bab = [(t, p) for t, p in peta if t.upper().startswith('BAB')]
```

Ini kelas **gerbang hiasan** — sama seperti asersi yang selalu `[]`.

### J6. "ADA MINIMAL SATU" bukan "SEMUA"

`ok(..., bool(ada_br), ...)` lulus kalau **satu** judul benar → satu bab sehat
menutupi bab lain yang rusak. WAJIB `not tanpa_br`.

### J7. Pola suntikan harus SPESIFIK satu run

`'>BAB I<'` juga mengenai `'>BAB II<'` → `BAB II` jadi `BAB 1I` (kerusakan
berbeda dari yang dimaksud). Pakai `'<w:t>BAB I</w:t>'`.

### J8. Uji suntikan wajib `assert n > 0`

Pola yang tidak ditemukan = tidak ada yang disuntik = gerbang lulus wajar →
lalu disimpulkan "gerbang buta" padahal gerbangnya **benar**.
Selalu `assert n > 0` **dan** cetak jumlah suntikan.

---

## 7. Font berlisensi — PERINGATAN

Font berikut **berbayar** dan kemungkinan **tidak terpasang** di mesin
penghasil `.docx`:

`Trajan Pro` · `Palatino Linotype` · `Adobe Garamond Pro` · `Elephant` ·
`Digory Doodles` · `Nyala`

⚠️ Kalau tidak terpasang, **Word mengganti diam-diam**. Gerbang XML tetap
LULUS, tapi **bentuk buku berubah**.

⇒ Gerbang ini memeriksa **XML, bukan hasil cetak**. Untuk cetak, tetap
perlu diperiksa mata.

---

## 8. 🤖 Jev — pembagian tugas (jangan tertukar)

Jev = model System One. **Bukan LLM, tidak menulis teks, tidak menghitung.**

```
XML  (periksa_buku_template.py) : halaman, batas, font, ukuran, spasi, perataan
JEV  (makna / peran)            : peran blok, jenis dokumen, sifat struktur
KODE (python biasa)             : nomor, jumlah, batas bagian, urutan
```

### Jev TERBUKTI berguna (terukur 22 Okt 2026, 8 pertanyaan 1 panggilan)

| Pertanyaan | noul / choice | yakin |
|---|---|---|
| blok 16 pt rata tengah = kutipan, bukan isi | 0,92 | 0,84 |
| `BAB I` + judul **menyatu satu baris** | 0,96 | 0,92 |
| nomor bab **Romawi** | 0,94 | 0,88 |
| sub bab **bernomor bertingkat** | 0,98 | 0,96 |
| ada KATA PENGANTAR | 0,99 | 0,98 |
| ada TENTANG PENULIS | 0,99 | 0,98 |
| ada data penerbitan (ISBN dll) | 0,96 | 0,92 |
| jenis dokumen | **`buku`** | **conf 1,00** |

### Jev DILARANG untuk

- ❌ Menghitung nomor paragraf / jumlah bab / jumlah kata
- ❌ Menyalin atau menyebut teks
- ❌ Membandingkan dua baris mana lebih tepat (tiap pertanyaan **independen**)
- ❌ Menentukan font / ukuran / margin

### Bukti kenapa dilarang

| Cara bertanya | Hasil |
|---|---|
| ❌ "Isi buku mulai paragraf 44?" (menyebut **nomor**) | **0,04 / 0,02 / 0,17** — salah 3× |
| ❌ "Hirarki bab 22pt > sub bab 13pt?" (dua hal digabung) | **0,45** — ragu |
| ✅ Atomik + `criteria {true,false}` + fakta positif | **0,94–0,99** |

### Cara benar memanggil Jev

```python
# noul BOLEH criteria objek {true, false} — dokumentasi resmi 22 Okt 2026
{'ada_kata_pengantar': {
    'type': 'noul',
    'instructions': 'Naskah memuat bagian berjudul KATA PENGANTAR.',
    'criteria': {'true': 'Ada bagian berjudul KATA PENGANTAR',
                 'false': 'Tidak ada bagian KATA PENGANTAR'},
}}
```

Bentuk lain **ditolak**: `criteria` string, atau objek tanpa kunci `true`/`false`.

Fan-out banyak pertanyaan dalam **satu panggilan** — dokumentasi resmi:
11,5× lebih murah, 9,6× lebih cepat, jawaban sama.
---

## 9. Untuk agen AI — langkah kerja yang BENAR

```
1. Baca README ini sampai habis.
2. Verifikasi MD5 template.
3. Jalankan `baca_template.py` — lihat angka sah dengan mata sendiri.
4. Tulis kode penghasil .docx memakai angka di §2.
   · Isi buku  : Palatino Linotype 10 pt, rata both
   · Judul bab : Heading1 Trajan Pro 22 pt tebal + <w:br/>
   · Sub bab   : Heading2 13 pt tebal, latar F2F2F2
5. Jalankan GERBANG: `periksa_buku_template.py hasil.docx`
6. Kalau GAGAL → perbaiki kode, JANGAN melonggarkan gerbang.
7. Kalau LULUS → periksa mata (font berlisensi bisa diganti Word).
```

### 🔴 DILARANG

| Larangan | Alasan |
|---|---|
| Mengubah template asli | itu satu-satunya acuan |
| Melonggarkan gerbang agar lulus | menipu diri sendiri |
| Menebak angka font/margin | baca §2 atau jalankan `baca_template.py` |
| Memakai Jev untuk menghitung | Jev tidak bisa menghitung |
| Menyimpulkan "gerbang buta" tanpa `assert n > 0` | uji suntikan bisa tidak menyuntik |

---

## 10. Berkas rujukan

| Berkas | Isi |
|---|---|
| `references/fakta-terukur.md` | semua angka + catatan jujur per temuan |
| `references/jev-template-buku-22okt2026.md` | hasil ukur Jev lengkap (ronde gagal & berhasil) |

### Skill Hermes terkait

| Skill | Isi |
|---|---|
| `publishing/template-buku-resmi` | salinan skill (versi agen) |
| `automation/typesafe-jev` | dokumentasi resmi Jev + salinan `docs.typesafe.ai` |
| `automation/typesafe-pertanyaan` | katalog kalimat pertanyaan yang terbukti menang/gagal |
| `buku-umum` · `buku-referensi` · `buku-ajar-obe` · `buku-monograf` · `book-chapter` | mesin buku yang WAJIB memakai angka ini |

---

## 11. Status & yang BELUM dikerjakan

### ✅ Sudah selesai (22 Okt 2026)

- Template asli disimpan + MD5 terverifikasi
- Semua angka diekstrak dari XML (nol tebakan)
- Gerbang 20 asersi + 2 uji bergigi (10 suntikan total)
- Jev dibaca ulang dari `docs.typesafe.ai` → 2 koreksi dokumentasi
- Judul bab dua baris diperiksa otomatis (J2a/J2b/J2c)

### ⬜ BELUM

| Item | Catatan |
|---|---|
| Sambung gerbang ke mesin buku | `buku-umum`, `buku-referensi`, dll belum memanggil `periksa_buku_template.py` |
| Font berlisensi | belum diperiksa apakah terpasang di mesin produksi |
| Template halaman sampul otomatis | sampul masih perlu diisi manual |
| Daftar isi otomatis | TOC memakai FIELD Word, belum digenerate mesin |

---

## 12. Riwayat versi

| Tanggal | Perubahan |
|---|---|
| **22 Okt 2026** | Versi pertama. Template diunduh, angka diekstrak, gerbang dibuat, Jev dioptimalkan menurut dokumentasi resmi. Judul bab diputuskan **dua baris** (sesuai template). |

### Koreksi yang tercatat

| # | Klaim salah | Kenyataan |
|---|---|---|
| 1 | "Template rusak, ada sisa XML" | Regex pembaca bocor; template sehat |
| 2 | "Judul bab menyatu jadi satu baris" | Template sudah dua baris pakai `<w:br/>` |
| 3 | "Gerbang J2 buta" | Uji suntikan tidak menyuntik (pola salah) |
| 4 | "noul tidak boleh pakai criteria" | Dokumentasi resmi: **boleh**, opsional |

---

## 13. Lisensi & kepemilikan

Template dan skrip ini milik **Bayana / EduAi Publishing**.
Template asli disediakan oleh pemilik proyek dan **tidak boleh diubah**.

---

*Dibuat oleh Wulan · 22 Oktober 2026*
*Repo: `PaculDigital/eduai-publishing` → `template-buku-resmi/`*
