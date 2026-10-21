# 📕 STANDAR PEMBUATAN BUKU — ANTI-KAKU

> **Tanggal:** 20 Oktober 2026 · **Oleh:** Wulan · **Revisi 2**
> **Perintah Bos (verbatim):** *"kamu buat Dokumentasi tentang standar pembuatan
> buku agar tidak kaku hasilnya. Saya itu kasih kamu informasi cara standard
> buat buku. Jadi output jadi benar, bukan kaku paragraf panjanggg sekali di
> tengahnya tidak ada variasi point-point."*
> *"update dokumentasi info standar buku dan ukurannya itu, termasuk ukuran
> semua. Jadi tidak ada mengarang lagi atau kaku lagi outputnya. Paham ini
> penting."*
>
> **INI DOKUMEN KERJA** — aturan yang **dipatuhi mesin**, bukan teori.
> Setiap angka punya label: **[BAKU]** = ada di sumber resmi ·
> **[REKOMENDASI]** = anjuran ahli, bukan hukum · **[GAYA KITA]** = keputusan
> internal penerbit ini.

---

## 0. MASALAH YANG HARUS MATI

Buku hasil mesin **kaku**. Tiga penyakit, terbukti dari buku uji
"Ayo Mengenal Cuaca" (20 Okt 2026):

| Penyakit | Bukti terukur |
|---|---|
| Paragraf panjang tak berujung, tanpa indentasi, tanpa pemisah | 115 paragraf, sebagian >8 kalimat |
| **Tidak ada variasi bentuk** di tengah teks | **0** daftar berpoin, 0 nomor |
| Semua diagram bentuknya sama | 3 diagram = kotak bertumpuk + panah ke bawah |

**SASARAN:** setiap 2–3 halaman ada **pergantian bentuk** sehingga mata
pembaca beristirahat. Itu yang membuat buku terasa premium — bukan jenis
hurufnya.

---

## 1. SUMBER (semua nyata, bisa diperiksa)

| Kode | Sumber | Kelas |
|---|---|---|
| **S1** | Chicago Manual of Style 18th ed. (2024), §2.25 & §6.141–6.142 | standar industri buku dunia |
| **S2** | CMOS Shop Talk, "Paragraphing in Manuscripts for Submission" (15 Sep 2020) | penerbit Chicago |
| **S3** | *Ten Simple Rules for Typographically Appealing Scientific Texts*, PLOS Comput Biol 2020, doi:10.1371/journal.pcbi.1008458 | jurnal peer-review |
| **S4** | Panduan Menerbitkan Buku di **UGM Press**, Lampiran **Selingkung** | penerbit universitas Indonesia |
| **S5** | Purdue OWL — "Paragraphing" | universitas |
| **S6** | APA Publication Manual 7th ed. + apastyle.apa.org (lists) | standar akademik |
| **S7** | **Permendikbud No. 8 Tahun 2016** + Lampiran | **hukum Indonesia** |
| **S8** | Keputusan Kepala Badan Bahasa **No. 0424/I/BS.00.01/2022** — EYD Edisi Kelima | **bahasa Indonesia baku** |
| **S9** | Oxford Lifelong Learning — Paragraph Structure | universitas |
| **S10** | ISO 216 (seri A & B) + ukuran UNESCO 15,5×23 cm | dimensi buku |
| **S11** | Pedoman Buku Ajar Dikti / LPPM (UNSED, Medan Area, Deepublish) | ukuran & margin naskah |

---

## 2. LANDASAN MUTU (S7 + S8)

**Permendikbud 8/2016 Pasal (5):** bagian isi buku teks wajib memenuhi
**4 aspek**:
1. **Materi** — kebenaran keilmuan, kemutakhiran, kesesuaian konteks
2. **Kebahasaan** — ejaan, kata, kalimat, **paragraf** tepat/lugas/jelas
3. **Penyajian** — runtut, koheren, sesuai tingkat pembaca
4. **Kegrafikaan** — tata letak, ilustrasi, keterbacaan

**EYD Edisi Kelima (S8)** mengatur huruf, kata, angka, tanda baca —
**termasuk pemerincian**. ⚠️ EYD **TIDAK** mengatur panjang paragraf dan
**TIDAK** mengatur indentasi tipografis.

---

## 3. UKURAN BUKU — PILIH SESUAI JENIS (S10, S11)

**Tidak ada satu ukuran wajib.** Yang baku: seri **ISO 216** + **UNESCO**
untuk buku ilmiah. Penerbit besar punya ukuran rumah sendiri.

| Ukuran | Dimensi (l × t) | Dipakai untuk |
|---|---|---|
| A6 | 10,5 × 14,8 cm | buku saku, puisi, refleksi |
| Buku saku | 11 × 18 cm | novel ringan, referensi kecil |
| Novel custom | 13 × 19 · 13,5 × 20 (Gramedia) · 13 × 20 (Mizan) · 14 × 21 (Kompas) | fiksi |
| **A5 (ISO)** | **14,8 × 21 cm** | novel, buku umum, motivasi, monograf ringkas |
| **UNESCO** | **15,5 × 23 cm** | **buku ajar, referensi, monograf, buku ilmiah (Dikti)** |
| **B5 (ISO)** | **17,6 × 25 cm** | buku pelajaran, referensi besar, modul, workbook |
| A4 (ISO) | 21 × 29,7 cm | buku pelajaran besar, modul, laporan, banyak tabel |
| B4 (ISO) | 25 × 35,3 cm | buku gambar/portofolio, jarang untuk teks |
| **Buku anak** | **20 × 20 · 21 × 21 · 20 × 28 cm** | picture book / board book, visual dominan |

### 3.1 Pemetaan jenis buku → ukuran (KEPUTUSAN MESIN)
| `jenis_buku` | Ukuran | Alasan |
|---|---|---|
| **anak** | **20 × 20 cm** | visual dominan, gambar besar |
| **pendidikan** | **B5 17,6 × 25 cm** | banyak tabel & latihan |
| **umum** | **A5 14,8 × 21 cm** | buku umum/nonfiksi populer |
| **akademik / referensi** | **UNESCO 15,5 × 23 cm** | standar Dikti |

⚠️ **TEMUAN 20 Okt 2026:** buku anak yang diuji kemarin memakai ukuran
**UNESCO 15,5×23** — padahal seharusnya **20×20**. Ini yang membuat buku
anak terasa seperti buku pelajaran.

### 3.2 Pagar audit ukuran
- [ ] Ukuran termasuk daftar di atas **atau** ukuran rumah penerbit yang
      dinyatakan tertulis. Di luar daftar tanpa alasan = **temuan**.
- [ ] Ukuran **konsisten** dan tertulis sama di halaman hak cipta/katalog.
- [ ] Pilihan ukuran **sesuai jenis isi**.

---

## 4. MARGIN — DUA REZIM, JANGAN DICAMPUR (S11)

### 4.1 Margin NASKAH (file Word yang dikirim penulis)
Untuk UNESCO 15,5 × 23 cm:
| Sisi | Ukuran |
|---|---|
| Atas | 2,5 cm (ada institusi 3 cm) |
| Kiri / dalam | **3 cm** |
| Bawah | 2 cm |
| Kanan / luar | 2 cm |

⚠️ Selisih antar institusi membuktikan: **margin naskah ditetapkan
penerbit/institusi, bukan angka nasional.**

### 4.2 Margin BUKU CETAK JADI — **CERMIN**
Halaman ganjil & genap **saling bercermin**. Istilahnya bukan kiri/kanan,
tapi **DALAM & LUAR**.

| Sisi | Ukuran |
|---|---|
| Atas | 2 – 2,5 cm |
| Bawah | 2 – 2,5 cm (biasanya ≥ atas, memuat nomor halaman) |
| Luar | ± 2 cm |
| **Dalam (sisi jilid)** | **2,5 – 3 cm — PALING BESAR** |
| Minimum aman semua sisi | 2 cm |
| Bleed (kover/halaman bergambar penuh) | tambah 3–5 mm |
| Header dari tepi atas | ± 1 – 1,25 cm |
| Footer dari tepi bawah | ± 1 – 1,25 cm |

**Contoh hitung bidang teks (UNESCO):**
```
lebar teks  = 15,5 − dalam 2,5 − luar 2      = 11,0 cm
tinggi teks = 23   − atas 2,0  − bawah 2,5   = 18,5 cm
```

### 4.3 ⛔ YANG BUKAN MARGIN BUKU
Margin **skripsi/tesis A4** (atas 4 · kiri 4 · bawah 3 · kanan 3) adalah
margin **NASKAH AKADEMIK**, **BUKAN** margin buku. Memakai 4-4-3-3 pada
buku UNESCO/A5 membuat bidang teks sangat sempit dan buku terlihat
tidak profesional.

### 4.4 Pagar audit margin
- [ ] Margin **dalam > luar** (kalau sama/kecil, teks tenggelam ke jilid)
- [ ] Konsisten di semua bab — ukur 3 halaman acak (awal/tengah/akhir)
- [ ] Tidak ada teks/gambar masuk zona <2 cm dari tepi potong
- [ ] Nomor halaman tidak terpotong, posisi konsisten

---

## 5. ATURAN PARAGRAF

### 5.1 Satu sistem saja — JANGAN dua-duanya
Pilih **INDEN** (buku cetak) **atau** **JARAK** (buku modern). Memakai
keduanya = penanda ganda = **terlihat amatir**.

> **⇒ [GAYA KITA] BUKU KITA PAKAI SISTEM INDEN.** Alasan: buku dicetak;
> S1 & S2; hemat halaman.

### 5.2 Angka indentasi — **[BAKU tipografi] 1 em**
> Inden buku cetak = **1 em = sebesar huruf**. Huruf 12 pt ⇒ inden
> **12 pt (± 4,2 mm)**.

| Tahap | Ukuran | Status |
|---|---|---|
| **Manuskrip Word** | 0,5 inci = **1,27 cm** | **[BAKU]** APA 7 & Chicago |
| Pedoman buku ajar Indonesia | 1,25 cm + spasi 1,5 + TNR 12 | **[REKOMENDASI]** |
| **Buku CETAK JADI** | **1 em = ukuran huruf** | **[BAKU tipografi]** |

⚠️ Inden 0,5 inci pada buku cetak **terlalu besar** — itu warisan mesin tik.
⛔ **Jangan pakai spasi/Tab manual** — pakai `First Line Indent` (S6).

### 5.3 Spasi antarparagraf = 0
> **S1:** *"New paragraphs are identified by a first-line indent alone."*

### 5.4 PENGECUALIAN: paragraf pertama setelah judul = rata kiri
> **S1 §2.25:** paragraf pertama setelah judul bab/subbab **tidak
> diinden** — pembaca sudah tahu itu awal baru.

Berlaku juga: paragraf pertama bab · paragraf setelah kutipan blok/gambar/
tabel/daftar (jika lanjutan).

### 5.5 Rata kanan-kiri + widow/orphan
> **S3 Rule 3:** teks isi **justified**; *"no single lines should be
> separated from the rest of a paragraph."*

- [ ] `alignment = JUSTIFY` + hyphenation ON
- [ ] `widowControl = True` (min 2 baris menyatu per halaman)

### 5.6 Panjang paragraf — **[GAYA KITA]**
⚠️ **JUJUR:** tidak ada aturan resmi nasional/internasional yang menetapkan
"maksimal N kalimat per paragraf". Yang ada rekomendasi:

| Sumber | Anjuran |
|---|---|
| **S5 Purdue OWL** | 1 paragraf = 1 gagasan · *"Aim for three to five or more sentences"* |
| **S9 Oxford** | batasi ± 5 kalimat; 8–15 kalimat = masalah umum |
| Pedoman kampus Indonesia | minimal 2 kalimat |

**⇒ AMBANG AUDIT (GAYA KITA, bukan klaim aturan nasional):**

| Ukuran | Ambang | Tindakan mesin |
|---|---|---|
| Ideal | **3–5 kalimat** | lolos |
| **Peringatan** | **> 7 kalimat** ATAU **> 200 kata** | **DIPECAH** |
| Gagal | **1 kalimat** (non-fiksi) | gabung ke tetangga |
| Gagasan | > 1 gagasan | pecah |

### 5.7 Inden gantung daftar pustaka
> **[BAKU]** Daftar pustaka: **hanging indent 0,5 inci** — baris pertama
> rata kiri, baris berikutnya menjorok.

### 5.8 Kutipan blok
> Inden kiri **0,5 inci / ±1 cm**, **tanpa tanda petik**, ukuran bisa
> lebih kecil.

---

## 6. ATURAN VARIASI — INTI "ANTI-KAKU"

**Masalah Bos:** *"paragraf panjanggg sekali di tengahnya tidak ada variasi
point-point."*

### 6.1 Wajib ada pergantian bentuk
**⇒ [GAYA KITA] dalam setiap 1.000 kata bab, minimal:**

| Unsur | Min | Maks |
|---|---|---|
| Daftar berpoin | **1** | 3 |
| Daftar bernomor | **1** | 2 |
| Kotak sorotan / "Tahukah kamu" | **1** | 3 |
| Tabel ringkas | 1 | 4 |
| Gambar/diagram/grafik | 1 | 5 |
| **Paragraf naratif berturut** | — | **maks 4** |

**PAGAR:** bila 4 paragraf berturut tanpa variasi ⇒ mesin **mengubah bentuk**
dari isi yang sudah ada. **DILARANG mengarang isi baru.**

### 6.2 Kapan pakai bentuk apa
| Isi | Bentuk BENAR |
|---|---|
| Hal setara, tak berurutan | **daftar berpoin •** |
| Langkah / prosedur / peringkat | **daftar bernomor 1.2.3.** |
| Rincian pendek dalam 1 kalimat | **huruf (a) (b) (c)** |
| Perbandingan angka antar kategori | **tabel** |
| Proporsi dari keseluruhan (%) | **pai / donat** |
| Perubahan terhadap waktu | **grafik garis** |
| Proses berulang / siklus | **diagram melingkar** |
| Langkah satu arah | **alur** |
| Sebab jamak → akibat | **pohon / jaring** |
| Lapisan / bagian dalam | **irisan (cutaway)** |
| Peringkat / kepentingan | **piramida / tangga** |

**PAGAR KERAS:** bentuk dipilih **dari ISI**, bukan acak demi "variasi".
Variasi tanpa alasan = **lebih buruk** daripada seragam.

---

## 7. ATURAN DAFTAR / POIN / NOMOR

### 7.1 Jenis ditentukan MAKNA (S1, S6)
- **1. 2. 3.** → HANYA bila **urutan penting** (langkah, kronologi, peringkat)
- **•** → urutan **tidak** penting
- **(a) (b) (c)** → rincian pendek dalam satu kalimat (**3–5 butir**);
  >5 butir atau panjang ⇒ naikkan jadi daftar vertikal

### 7.2 Pengantar daftar WAJIB
> **S1 §6.141:** *"A vertical list is best introduced by a grammatically
> complete sentence"* + titik dua `:`.

❌ Dilarang: daftar langsung muncul tanpa kalimat pengantar.

### 7.3 Tanda baca butir — SATU GAYA SE-BUKU
| Bentuk butir | Tanda baca |
|---|---|
| **Kalimat lengkap** | Kapital + **titik** |
| **Frasa pendek** | huruf kecil + **tanpa** titik |

❌ Campur keduanya dalam satu daftar = **tidak lolos audit premium**.

### 7.4 Paralel & inden gantung
- [ ] Semua butir **satu bentuk** (semua frasa benda ATAU semua kalimat kerja)
- [ ] **Inden gantung**: nomor/bullet menggantung kiri, teks butir sejajar
- [ ] Baris ke-2 dst. sejajar dengan **awal teks butir**, bukan nomornya
- [ ] Jarak antarbutir konsisten se-buku

### 7.5 Wujud teknis
- Wajib **list asli Word** (`numPr`), **bukan** ketik "•" manual (S3 Rule 6)
- Butir = **1 gagasan**, **maks 2 baris**

### 7.6 Jumlah butir **[GAYA KITA]**
| Jenis | Maks |
|---|---|
| Berpoin | **7** |
| Bernomor | **10** |
| Huruf dalam kalimat | **5** |

---

## 8. PENOMORAN BAB & SUB-BAB (S4, S1)

```
BAB I   PENDAHULUAN
1.1     PERKEMBANGAN KOTA
1.1.1   Kawasan Perkotaan
1.1.1.1 Permukiman Kumuh
```

| Aturan | Status |
|---|---|
| Pilih SATU gaya: `BAB I` atau `Bab 1`, jangan campur | **[BAKU]** |
| Maksimal **3 tingkat** desimal | **[REKOMENDASI kuat]** |
| UGM Press mencontohkan **4 tingkat** (1.1.1.1) | **[BAKU Indonesia]** |
| **⇒ [GAYA KITA]**: 4 tingkat DIIZINKAN hanya bila terpaksa, dan sediakan turun ke poin | keputusan |
| ❌ **Tidak boleh ada 1.1 tanpa 1.2** — kalau dipecah minimal 2 | **[BAKU struktur]** |
| Judul bernomor **tidak diakhiri titik** | **[BAKU]** |
| Kapital judul konsisten (Title Case ATAU Sentence case) | **[BAKU]** |
| Nomor & judul di Daftar Isi **PERSIS** sama dengan isi | **[BAKU]** |

---

## 9. PENOMORAN HALAMAN (S7 Lampiran)

| Bagian | Angka | Dicetak mulai |
|---|---|---|
| **Awal** (halaman judul, hak cipta, kata pengantar, daftar isi) | **Romawi kecil** i, ii, iii | sejak **Kata Pengantar** |
| Halaman judul & hak cipta | dihitung, **nomornya TIDAK dicetak** | — |
| **Isi + akhir** | **Arab** 1, 2, 3 | **bersambung terus**, tanpa putus antar bab |

Posisi nomor halaman **konsisten se-buku** (pilih satu: bawah-tengah,
atas-kanan, dst).

---

## 10. PENOMORAN TABEL & GAMBAR

- Format: **Tabel 3.1 / Gambar 3.2** (bab.nomor) — pilih satu gaya, konsisten
- **Judul tabel di ATAS tabel**; **keterangan gambar di BAWAH gambar**
- Tabel/gambar **wajib dirujuk di teks** dan masuk **Daftar Tabel / Daftar Gambar**
- Wajib ada **`Sumber: …`** di bawahnya (S4)
- Posisi: **di atas halaman** bila muat, **tidak memotong paragraf** (S3 Rule 7)

---

## 11. ATURAN GAMBAR / DIAGRAM

### 11.1 Proporsi — TIDAK full lebar
**Bos:** *"tidak lebar full kanan kiri, proporsi saja, dengan ukuran buku."*

| Unsur | Aturan |
|---|---|
| Lebar maksimum | **70–80%** lebar teks (bukan 100%) |
| Posisi | **tengah** |
| Pai/diagram persegi | maks **8 cm** |
| Grafik batang/garis | maks **11 cm** (dari 11,9 cm teks) |
| Gambar kecil (≤ 6 cm) | boleh mengapit teks |

### 11.2 Tulisan di dalam gambar
**Bos:** *"tidak perlu dihapus tulisannya jika memang perlu, kalo ada
tulisan sederhana saja."*

**⇒ ATURAN (TERUKUR 20 Okt 2026):**
- **Teks di dalam gambar DILARANG ditulis AI gambar** — AI buta huruf
  (bukti: "Tahu naga?", "menutabi 71% Bum!!", "Manafat", nomor 1-3-5-4-2-1)
- **Teks ditulis MESIN** di atas ilustrasi AI (bukti: 9/10, nol salah eja)
- **Maks 6 kata per label**, huruf **≥ 9 pt** saat dicetak
- Ilustrasi **wajib sesuai konteks bab** — diambil dari ISI bab, bukan judul

### 11.3 Grafik dari data nyata
Grafik/pie **WAJIB dari angka yang ADA di naskah**. Kalau tidak ada angka ⇒
**jangan** paksa grafik; pakai alur/siklus.

---

## 12. GRAFIKA PREMIUM — ANGKA TEKNIS

### 12.1 Huruf
| Unsur | Ukuran | Status |
|---|---|---|
| Isi | 10,5 – 12 pt serif/sans terbaca | **[REKOMENDASI]** |
| Judul bab | ± 16 pt | **[REKOMENDASI]** |
| Subbab | ± 14 pt | **[REKOMENDASI]** |
| **⇒ [GAYA KITA] mesin** | isi **12 pt** · bab **16 pt** · subbab **14 pt** | keputusan |

### 12.2 Spasi baris
- Buku cetak jadi: **leading ±120–145%** ukuran huruf
- ⚠️ **Spasi 1,5 adalah aturan MANUSKRIP**, bukan hasil cetak
- **⇒ [GAYA KITA]** 1,15–1,2

### 12.3 Lebar baris
- Maks **± 70 karakter** per baris (nyaman baca)

---

## 13. HALAMAN YANG WAJIB ADA (S7 + S4)

| # | Halaman | Status mesin |
|---|---|---|
| 1 | Halaman judul | ✅ ada |
| 2 | Halaman hak cipta / penerbitan | ✅ ada |
| 3 | Kata Pengantar (romawi) | ✅ ada |
| 4 | **Daftar Isi + NOMOR HALAMAN** | 🔴 **ADA, NOMORNYA KOSONG** |
| 5 | Daftar Tabel | ❌ belum |
| 6 | Daftar Gambar | ❌ belum |
| 7 | Isi buku | ✅ ada |
| 8 | Glosarium | ✅ ada |
| 9 | Daftar Pustaka | ✅ ada |
| 10 | Indeks | ❌ belum |
| 11 | Tentang Penulis | ✅ ada |

🔴 **TEMUAN 20 Okt 2026:** `add_daftar_isi()` di `buku_umum_assembly.py:371`
membuat tab + dot leader, tetapi **tidak pernah menulis nomor halaman**.
Bukti dari kode: setiap entri berakhir `r2 = p.add_run("\t")` lalu **habis** —
tidak ada `add_run` nomor.

---

## 14. STATUS MESIN (setelah 20 Okt 2026)

| Aturan | Status | Berkas |
|---|---|---|
| Inden 1 em | ✅ **LIVE** | `buku_umum_assembly.py` (`inden_otomatis`) |
| Spasi antarparagraf 0 | ✅ **LIVE** | `space_before=0, space_after=0` |
| Paragraf pertama setelah judul rata kiri | ✅ **LIVE** | `baru_setelah_judul` |
| Pecah paragraf > 7 kalimat | ✅ **LIVE** | `tata_paragraf.pecah_paragraf()` |
| Paragraf → daftar (variasi) | ✅ **LIVE** | `tata_paragraf.jadikan_daftar()` |
| Daftar = list asli Word | ✅ **LIVE** | `_tulis_daftar()` |
| Widow control | ✅ **LIVE** | `pf.widow_control = True` |
| Judul sub-bab bernomor dikenali | ✅ **LIVE** | `_baris_judul_bernomor()` |
| Ukuran buku per jenis | 🔴 belum | — |
| Margin cermin | 🔴 belum | — |
| Daftar isi bernomor | 🔴 belum | — |
| Daftar Tabel/Gambar/Indeks | 🔴 belum | — |
| Nomor halaman Romawi→Arab | 🔴 belum | — |
| Lebar gambar 70–80% | 🔴 belum | — |

---

## 15. JEBAKAN YANG SUDAH TERBUKTI (jangan diulang)

| # | Jebakan | Akibat terukur |
|---|---|---|
| **J1** | `Pt(size)` padahal `size` sudah objek `Pt` | inden jadi 1.935.480.000 EMU = 152.400 pt (tak bermakna) |
| **J2** | Ambang butir 14 kata | **seluruh buku** jadi daftar (24 butir, 0 paragraf) |
| **J3** | Ambang butir 9 kata | narasi Indonesia (8–9 kata/kalimat) tetap jadi daftar |
| **J4** | `.pt` pada objek `Twips` | dilaporkan 152400 padahal 12 pt — uji GAGAL PALSU |
| **J5** | Tulis `11` di alat uji padahal `FONT_SIZE = Pt(12)` | uji GAGAL PALSU |
| **J6** | Judul hanya `### ` | judul `1.1 Judul` dianggap paragraf ⇒ inden salah |
| **J7** | `baru_setelah_judul = False` di dalam loop | paragraf pertama malah berinden |
| **J8** | Ambang `merge_short_paragraphs()` **ditulis mati 50/60 kata** | tone buku anak 25–40 kata ⇒ **SEMUA** paragraf digabung ⇒ 1 bab jadi **1 baris 8.251 karakter** |
| **J9** | Baris kosong **reset buffer** di penggabung paragraf | penggabung praktis **MATI** untuk naskah berparagraf ⇒ dua bug J8+J9 saling menutupi |
| **J10** | Alat uji hitung kalimat dengan `split('.')` | `(2024).` · `et al.` · URL · desimal dihitung kalimat ⇒ **5 pelanggaran PALSU** |
| **J11** | Kunci dict hasil JSON dibaca sebagai `int` | JSON memaksa kunci jadi `str` ⇒ `.get(1)` **selalu None** ⇒ pagar Jev mati **tanpa error** |
| **J12** | Cabut penanda setelah pecah judul | `[TABEL 1.1: …]` ikut jadi paragraf ⇒ **tabel HILANG** dari .docx |
| **J13** | Blok 2-elemen saat 1 baris jadi >1 blok | `boleh_daftar` hilang karena indeks bergeser ⇒ narasi jadi 49 butir daftar |
| **J14** | **Tidak ada PEMECAH paragraf** di jalur penulisan — hanya penggabung | AI menulis 1 paragraf **945 kata / 6.565 kar** per sub-bab; naskah tersimpan sudah rusak sebelum dirakit |
| **J15** | `verify_text_citations` menutup dengan `re.sub(r'\s{2,}', ' ', …)` | `\s{2,}` **juga cocok `\n\n`** ⇒ paragraf digabung balik; pemecah paragraf dibatalkan |
| **J16** | `post_process()` memanggil pemecah & penggabung **tanpa `jenis`** | keduanya pakai bawaan `umum` (ambang 60) ⇒ paragraf 43 kata buku anak **digabung balik** jadi 85 |
| **J17** | Batas `maks_kata=50` saja di pemecah | pemecah mengecek "kalimat berikutnya akan lewat" ⇒ praktis 4-5 kalimat; yang mengikat = **batas KALIMAT** |

**PENANDA NARASI vs BUTIR (J2/J3) — pagar final yang dipakai:**
Panjang kalimat **bukan** penanda. Yang dipakai = **kemandirian kalimat**:
butir daftar berdiri sendiri (tanpa kata sambung antarkalimat `yang`,
`ini`, `itu`, `tersebut`, `kemudian`, `lalu`, `sehingga`, …), narasi
hampir selalu memakai kata sambung itu.

---

## 16. RINGKAS — ANGKA YANG HARUS DIPATUHI

| Unsur | Nilai | Label |
|---|---|---|
| Ukuran buku anak | **20 × 20 cm** | [GAYA KITA] |
| Ukuran buku pendidikan | **B5 17,6 × 25 cm** | [GAYA KITA] |
| Ukuran buku umum | **A5 14,8 × 21 cm** | [GAYA KITA] |
| Ukuran akademik/referensi | **UNESCO 15,5 × 23 cm** | [BAKU Dikti] |
| Margin dalam (jilid) | **2,5 – 3 cm** | [BAKU tipografi] |
| Margin luar | **± 2 cm** | [BAKU tipografi] |
| Margin atas | 2 – 2,5 cm | [BAKU tipografi] |
| Margin bawah | 2 – 2,5 cm | [BAKU tipografi] |
| Badan huruf | **12 pt** serif | [GAYA KITA] |
| **Inden baris pertama** | **1 em = 12 pt** | [BAKU tipografi] |
| Spasi antarparagraf | **0** | [BAKU Chicago] |
| Jarak baris | 1,15–1,2 | [GAYA KITA] |
| Lebar baris | maks ±70 karakter | [REKOMENDASI] |
| Paragraf ideal | **3–5 kalimat** | [REKOMENDASI] |
| Paragraf maksimum | **7 kalimat / 200 kata** | [GAYA KITA] |
| Butir berpoin | maks **7** | [GAYA KITA] |
| Butir bernomor | maks **10** | [GAYA KITA] |
| Lebar gambar | **70–80%** teks | [GAYA KITA] |
| Caption | **Tabel 3.1 / Gambar 3.2** + `Sumber:` | [BAKU] |
| Halaman awal | Romawi kecil | [BAKU Permendikbud] |
| Halaman isi | Arab bersambung | [BAKU Permendikbud] |
