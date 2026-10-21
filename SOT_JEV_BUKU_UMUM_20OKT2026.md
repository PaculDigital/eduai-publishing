<!-- 🚪 SOT: Jev Buku Umum = SATU sumber kebenaran bentuk naskah buku. Status ada di sot.py -->
# 📗 SOT JEV BUKU UMUM — Jev Tersendiri, Beda dari Jev Naskah Akademik

> **Tanggal:** 20 Oktober 2026 · **Oleh:** Wulan
> **Perintah Bos (verbatim):** *"Jadi saya mau buat jev untuk buku umum, untuk
> membedakan dengan jev lain. Paham"*
> **Status:** 🟢 **LIVE & TERUJI 20 Okt 2026** — `jev_buku_umum.py` aktif di
> jalur `/buku/susun` lewat `buku_umum_assembly.add_bab()`. Gerbang 175
> LULUS / 0 GAGAL. (Status lama "🔴 BELUM DIKODING" sudah **BASI** — dihapus
> 20 Okt 2026.)

---

## 0. KENAPA HARUS JEV TERSENDIRI — BUKTI UKUR

Wulan mengukur naskah **buku nyata** (`buku_hasil/1792485534-5/bab1/bab1.txt`)
dan membandingkannya dengan naskah akademik yang sudah terbukti:

| Hal | Naskah akademik (Asih) | **Buku umum** | Akibat |
|---|---|---|---|
| Baris | 2.224 | **31** | bahan Jev 70× lebih sedikit |
| Karakter | 159.909 | **2.872** | 1 gelombang, bukan 14 |
| Panjang 1 baris | ~69 kar (potongan Word) | **~93 kar = 1 paragraf utuh** | "baris" ≠ "paragraf" |
| Baris kosong | ada (pemisah) | **tidak ada** | jendela 3-baris ≠ berguna |
| Judul sub-bab | selalu berdiri sendiri | **sering MENEMPEL dengan isi** | pola akademik gagal |
| Tanda bab | `BAB I` Romawi | `## BAB 1. Judul` | pola beda |
| Rata-rata | 1 baris = 1 kalimat | **1 baris = 3–67 kalimat** | harfiah beda |

### 0.1 Bukti paling keras: Jev akademik MENJAWAB SALAH untuk buku

Dijalankan `peta3_jev.petakan_dari_teks()` pada bab 1 buku nyata
(14 kandidat, 1 gelombang, 0,6 detik, 0 gagal):

| Baris | Jev akademik bilang | p | Isi sebenarnya |
|---|---|---|---|
| 15 | `subbab` ✅ | 1.00 | `### 1.1 Matahari, Suhu, dan Bayangan…` |
| 20 | `subbab` ✅ | 1.00 | `### 1.2 Bentuk-Bentuk Awan…` |
| **17** | **`paragraf`** ❌ | 0.56 | **judul 1.1 MENEMPEL + isi** |
| **22** | **`paragraf`** ❌ | 0.49 | **judul 1.2 MENEMPEL + isi** |

**Kesimpulan:** Jev akademik **tidak salah** — ia menjawab pertanyaan
akademik ("awal bab/subbab/paragraf?"). Pertanyaan itu **tidak cocok** untuk
buku, karena di buku judul dan isi bisa berada di baris yang sama.

⇒ **Buku butuh pertanyaannya sendiri. Inilah Jev Buku Umum.**

---

## 1. BATAS PERAN JEV BUKU (HARAM DILANGGAR)

### 1.1 BOLEH (bentuk / struktur / keberadaan)
| # | Pekerjaan | Tipe |
|---|---|---|
| **B1** | Baris ini **judul bagian** atau **isi**? | `choice` 2 pilihan |
| **B2** | Kalau judul — ini judul **apa**? | `choice` (bab / sub-bab / kotak) |
| **B3** | Paragraf ini **narasi** atau **rentetan hal setara**? | `noul` |
| **B4** | Paragraf ini milik **bagian yang mana**? | `choice` dari daftar bagian |

### 1.2 HARAM (sudah terbukti gagal / melanggar aturan resmi)
| Larangan | Alasan |
|---|---|
| Menilai **mutu tulisan** ("bagus/tidak", "menarik/tidak") | Jev = bentuk, BUKAN mutu. Terbukti gagal di 8 modul penilai |
| Menyuruh Jev **menghitung** ("berapa paragraf?") | Kelemahan resmi #2 — *"does not count reliably"* |
| Menyuruh Jev **menulis/menyalin teks** | Kelemahan resmi #9 — Generation. Termasuk **posisi karakter judul** |
| Menyuruh Jev **membandingkan antar baris** | Tiap pertanyaan INDEPENDEN (primitives.md) ⇒ urutan & duplikat = KODE |
| Memberi **daftar larangan** dalam `instructions` | Terukur: 0,844 → 0,32 |
| Memakai **kalimat paling simpel** | Terukur yakin 0,224 (paling buruk) |

---

## 2. PERTANYAAN B1 — JUDUL ATAU ISI (INTI)

### 2.1 Bahan (state) — FAKTA POSITIF, bukan larangan
Kode menyiapkan **jendela + fakta** yang kode TAHU tapi TAK BISA putuskan:

```json
{
  "b7": {
    "sebelum": "Pernahkah kamu berbaring dan melihat langit? …",
    "tengah": "### 1.1 Matahari, Suhu, dan Bayangan di Sepanjang Hari",
    "sesudah": "Matahari, Suhu, dan Bayangan di Sepanjang Hari Pagi tadi, Dinda …",
    "panjang_tengah": 55,
    "jumlah_kalimat_tengah": 1,
    "jumlah_kalimat_sesudah": 67,
    "baris_berikut": 3
  }
}
```

**Kenapa fakta ini:** hukum #1 katalog pertanyaan — Jev butuh **FAKTA POSITIF**
sebut panjang isi (terukur **0,823** 🏆). Tanpa fakta = 0,224 ❌.

### 2.2 Kalimat (WAJIB persis begini — jangan diringkas)
```
Baris `b7.tengah` panjangnya `b7.panjang_tengah` karakter dan memuat
`b7.jumlah_kalimat_tengah` kalimat. Baris `b7.sesudah` setelahnya memuat
`b7.jumlah_kalimat_sesudah` kalimat. Baris tengah ini perannya apa?
```
```python
'type': 'choice',
'criteria': {
    'judul': 'Judul bagian — nama singkat bagian, bukan kalimat',
    'isi'  : 'Isi/paragraf — kalimat yang menguraikan sesuatu',
}
```

### 2.3 1 kandidat = 1 nama = 1 jawaban
Nama pertanyaan = `b{indeks}` (mis. `b7`) — **kunci untuk KODE**, tidak dikirim
ke model. **JANGAN** menumpuk N baris jadi satu pertanyaan (terukur: 131
kandidat SELALU 'belum').

### 2.4 Ambang — IKUT ATURAN RESMI, JANGAN pasang saklar
> docs resmi: *"If all you care about is choosing the best option, just choose
> the option with the highest confidence (rather than setting a threshold)."*

⇒ **Ambil label dengan `p` tertinggi.** `p` hanya **info tampilan**.
Kalau `p` tertinggi < 0,5 (mepet) ⇒ masuk `goyang` ⇒ **jangan dipaksa**, mesin
pakai fallback konservatif (perlakukan sebagai isi).

---

## 3. PERTANYAAN B3 — NARASI ATAU RENTETAN (PAGAR DAFTAR)

**Kenapa ada:** ini pagar yang mencegah buku anak berubah jadi 170 butir
daftar (cacat terukur 20 Okt 2026). Regex sudah **gagal 4 kali**:
- v1 ambang 14 kata → seluruh buku jadi daftar
- v2 ambang 9 kata → narasi Indonesia tetap lolos
- v3 kata sambung → buku anak tak pakai kata sambung, tetap lolos
- v4 paralelisme kata → masih perlu ditegaskan

### 3.1 Kalimat
```
Paragraf `b12.tengah` memuat `b12.jumlah_kalimat` kalimat dengan panjang
`b12.panjang_karakter` karakter. Apakah paragraf ini merangkai BEBERAPA HAL
YANG SETARA (mis. daftar ciri/langkah/manfaat) sehingga lebih tepat disajikan
sebagai daftar?
```
```python
'type': 'noul'          # ⛔ TANPA criteria
```

### 3.2 Pagar keputusan (KODE yang memutuskan, bukan Jev)
```
p ≥ 0,50  → boleh jadi daftar  (Jev yakin)
p < 0,50  → TETAP paragraf     (ragu = jangan diubah) ← AMAN
```
⚠️ **Bedanya dengan B1:** di sini `p` dipakai sebagai saklar, karena jawabannya
`noul` (1 angka) dan risikonya **merusak isi** kalau salah. Ini **keputusan
sengaja**: lebih baik tidak mengubah apa pun daripada mengubah cerita jadi daftar.

---

## 4. URUTAN KERJA DI PERAKIT BUKU

```
1. KODE  : baca naskah → beri ID baris (b0| teks, b1| teks, …)
           hitung FAKTA: panjang, jumlah kalimat, kalimat sesudah
2. KODE  : buang yang PASTI bukan judul (gratis, 0 biaya Jev):
           · baris kosong → tetap dikirim (informasi!)
           · penanda `[[GAMBAR-…]]` / `[TABEL …]` / penanda diagram
           · `Sumber: …`
           · caption `Tabel x.y` / `Gambar x.y` DAN ≤70 kar
3. JEV   : 1 panggilan · B1 untuk semua kandidat · B3 untuk semua paragraf
4. KODE  : rakit peta ikut jawaban Jev
           · label `judul` → sub_heading (pakai teks APA ADANYA)
           · label `isi`   → paragraf
           · goyang        → perlakukan sebagai isi (konservatif)
5. KODE  : pecah paragraf panjang (tata_paragraf.pecah_paragraf)
6. KODE  : variasi bentuk (tata_paragraf.sisip_variasi) — HANYA memakai
           paragraf yang Jev nilainya boleh-jadi-daftar
7. JEV   : periksa hasil (opsional, 1 panggilan) — apakah bentuknya masuk akal
```

**Penting:** Jev **TIDAK** memotong judul yang menempel. Jev hanya bilang
"baris ini judul" atau "isi". Kalau isinya masih menempel, itu **tugas
PENULIS** membenahi — lihat §6.

---

## 5. BIAYA & KECEPATAN (PERKIRAAN, WAJIB DIUKUR)

| Hal | Perkiraan | Dasar |
|---|---|---|
| Panggilan per bab | **1–2** | 14–31 kandidat < batas 120 tanya |
| Waktu | **0,6–1,5 dtk** | terukur peta3: 0,6 dtk / 14 kandidat |
| Biaya per buku (6 bab) | **< Rp 10** | Jev ≈ Rp 3/panggilan |
| Cache | ronde ke-2 = **0 panggilan** | pola `tahapan_diagram.py` |

⚠️ **Biaya Jev ditanggung aplikasi** (putusan Bos 8 Okt 2026) ⇒ tetap harus
dihemat dengan cache sidik jari sha256(isi bab).

---

## 6. AKAR SEBENARNYA ADA DI HULU (JANGAN DILUPAI)

**Temuan 20 Okt 2026:** bab 1 punya `### 1.1` yang **sudah terpisah**
(baris 15 & 20, Jev p **1.00**). Tapi ada 2 sub-bab yang **menempel**
(baris 17 & 22).

⇒ **Penulis buku menulis tidak konsisten.** Kadang pakai `### `, kadang
menempel. **Ini cacat PROMPT PENULIS, bukan cacat perakit.**

**Perbaikan hulu (nol biaya Jev):** prompt penulis WAJIB menulis judul
sub-bab di **baris sendiri** dengan awalan `### `. Terbukti mesin bisa —
2 dari 4 sub-bab sudah benar.

**Jev di hilir = JARING PENGAMAN**, bukan obat utama.

### 6.1 ✅ AKAR TERBESAR DITEMUKAN — `merge_short_paragraphs()` (20 Okt 2026)

**Temuan terukur:** bab 1 buku anak (6.196 kata) tersimpan sebagai **SATU
baris 8.251 karakter** — bukan paragraf. Akibatnya Jev hanya melihat
**14 blok raksasa**, dan perakit **tak bisa** mengatur inden per paragraf.

**Akar:** ambang ditulis **MATI** di kode:

```python
if wc < 50:                        # ← angka mati
    buffer = ...                   # gabung
    if len(buffer.split()) >= 60:  # ← angka mati lagi
```

Padahal setelan tone buku anak (`tone_menulis.py:43`):
**"25-40 kata, 2-3 kalimat pendek"**.

⇒ **SETIAP** paragraf buku anak (25-40 kata) dianggap "pendek" (karena <50)
lalu **DIGABUNG** sampai ≥60 kata. Berulang sampai satu bab jadi satu baris.

**Bug kedua di fungsi yang sama:** baris kosong **langsung** mengeluarkan
buffer ⇒ paragraf pendek **tak pernah bisa** digabung ⇒ fungsi penggabung
praktis **MATI** untuk naskah yang paragrafnya dipisah baris kosong.
Dua bug yang saling menutupi.

**Obat (bukan tambalan):**

| Sebelum | Sesudah |
|---|---|
| ambang mati `50` / `60` | `_ambang_paragraf_min(jenis)` **dibaca dari `tone_menulis`** |
| baris kosong reset buffer | buffer **ditahan** melewati baris kosong |
| paragraf 25-40 kata digabung | paragraf ≥ ambang tone **TIDAK disentuh** |
| jenis tak dikenal → error | jatuh ke **40**, tidak meledak |

**Bukti terukur:**

| Jenis | Ambang tone | 3 paragraf @30/35/28 kata |
|---|---|---|
| anak | **25** | **4 paragraf** ✅ (terjaga) |
| umum | 60 | 2 paragraf (memang pendek) |

**Gerbang:** `gerbang_ambang_paragraf.py` — **10 LULUS / 0 GAGAL**, BERGIGI
(ambang dikembalikan ke 50 ⇒ uji #5 GAGAL).

### 6.2 ✅ Prompt penulis — aturan bentuk ditambahkan
Prompt `architect_prompt()` **tidak pernah** memberitahu AI bentuk yang
diharapkan. Sekarang ditambahkan:

```
- BENTUK WAJIB: SATU PARAGRAF = SATU BARIS. Pisahkan tiap paragraf dengan
  SATU BARIS KOSONG. JANGAN menulis seluruh sub-bab jadi satu baris panjang.
- Judul sub-bab TIDAK perlu ditulis (sudah ditangani perakit).
```

### 6.3 🚨 ALAT UJI PERNAH SALAH — pelajaran penting

`uji_docx_jev_buku.py` versi pertama menghitung kalimat dengan `split('.')`.
Terukur SALAH:

| Teks | `split('.')` | Seharusnya |
|---|---|---|
| `(2024).` | 1 kalimat | 0 (tahun) |
| `et al., 2024` | 1 kalimat | 0 (sitasi) |
| `bmkg.go.id` | 2 kalimat | 0 (domain) |

⇒ melaporkan **5 pelanggaran PALSU** (13 kalimat padahal 5).
**Alat uji diperbaiki** memakai `tata_paragraf.pecah_kalimat()` — penghitung
yang SAMA dengan produksi. Sesudah perbaikan: `masih_lewat_setelah_koreksi: 0`.

Pelajaran 15 Okt 2026 berlaku lagi: **PRODUKSI SEHAT, yang rusak ALAT UJI.**
Skrip pemeriksanya: `periksa_alat_uji_docx.py`.

### 6.4 🚨 AKAR SEBENARNYA — TIDAK ADA PEMECAH PARAGRAF (20 Okt 2026)
**Ini temuan paling penting, dan Wulan salah sasaran lebih dulu.**

Setelah ambang diperbaiki, Wulan buat **buku baru dari awal** (1 bab,
2 sub-bab, jenis anak) lewat pipeline produksi. Hasil ukur:

| Bagian | Kata/baris | Status |
|---|---|---|
| Intro | 74 | ✅ wajar |
| Isi 1.1 | **945** | ❌ satu baris 6.565 karakter |
| Isi 1.2 | **887** | ❌ satu baris 6.020 karakter |
| Penutup | 68 | ✅ wajar |

**Kesimpulan:** `merge_short_paragraphs` **hanya MENGGABUNG**, tak pernah
**MEMECAH**. AI menulis satu paragraf 945 kata untuk satu sub-bab, dan
**TIDAK ADA satu pun fungsi di jalur PENULISAN yang memecahnya**.

`tata_paragraf.pecah_paragraf()` **sudah ada** — tapi hanya dipakai **saat
merakit**, bukan **saat menulis**. Jadi naskah tersimpan sudah rusak.

**Obat (pakai yang sudah ada, jangan tulis pemecah baru):**

```python
# post_process() — URUTAN WAJIB
text = pecah_paragraf_panjang(text)     # ← PECAH dulu (fungsi baru,
                                        #   memakai tata_paragraf.pecah_paragraf)
text = merge_short_paragraphs(text)     # ← GABUNG kemudian
```

**Bukti terukur pada naskah NYATA (bab hasil AI):**

| | Sebelum | Sesudah |
|---|---|---|
| Paragraf 945 kata | 1 blok | **12 paragraf** (terpanjang 599 kar / 88 kata) |
| Paragraf 887 kata | 1 blok | **13 paragraf** (terpanjang 666 kar / 97 kata) |
| Seluruh bab | 9 baris, terpanjang 6.565 kar | **31 baris**, terpanjang 666 kar |

**Gerbang:** `gerbang_ambang_paragraf.py` naik jadi **16 LULUS / 0 GAGAL**,
termasuk cek #8 yang memastikan urutan **PECAH sebelum GABUNG** (kalau
terbalik ⇒ paragraf panjang tak akan dipecah).

**Pelajaran:** Wulan dua kali menuduh tempat yang salah — pertama
`merge_short_paragraphs`, padahal akarnya **fungsi yang tak ada**.
Yang menemukan = **uji buku baru dari awal**, bukan membaca kode.

---

## 7. RENCANA UKUR (SEBELUM DIPASANG)

| # | Yang diukur | Naskah | Lulus bila |
|---|---|---|---|
| U1 | B1 pada baris 15 & 20 (judul ASLI) | bab 1 buku nyata | label `judul`, p ≥ 0,8 |
| U2 | B1 pada baris 17 & 22 (judul MENEMPEL) | bab 1 buku nyata | label `judul` ATAU `isi` + masuk goyang (jujur) |
| U3 | B1 pada baris 2/4/6 (isi murni) | bab 1 buku nyata | label `isi`, p ≥ 0,8 |
| U4 | B3 pada paragraf narasi buku anak | bab 1 | `noul` < 0,5 ⇒ TETAP paragraf |
| U5 | B3 pada paragraf rentetan setara | naskah buatan | `noul` ≥ 0,5 ⇒ boleh daftar |
| U6 | Stabilitas 3× berturut | bab 1 | jawaban SAMA |
| U7 | Bab 2 (naskah tak pernah dilihat) | bab 2 | ≥ 80% benar |
| U8 | Biaya & waktu sebenarnya | bab 1+2 | < Rp 10, < 3 dtk |

**Aturan ukur:** pecahan < 80% = belum layak. **JANGAN turunkan ambang supaya lulus.**

---

## 8. BERKAS YANG AKAN DIBUAT (belum ada)

| Berkas | Isi |
|---|---|
| `app/jev_buku.py` | pembungkus — pola sama `app/peta3_jev.py` (importlib, bukan salinan) |
| `jev_buku_umum.py` | inti: `petakan_buku(teks)` → peta bentuk |
| `gerbang_jev_buku.py` | gerbang bergigi (sehat lulus · dibuat sakit gagal) |
| `uji_ukur_jev_buku.py` | 8 ukur U1–U8 |

**NOL mesin baru untuk Jev itu sendiri** — memakai `app/jev.py` (JALAN TOL),
`app/satpam.py` (pagar skema). Yang baru hanya **pertanyaannya**.

---

## 9. HUBUNGAN DENGAN JEV LAIN (JANGAN DICAMPUR)

| Jev | Berkas | Untuk | Jangan dipakai untuk |
|---|---|---|---|
| **Jev buku umum** (INI) | `app/jev_buku.py` | bentuk naskah BUKU | skripsi/tesis |
| Jev naskah akademik | `peta3_jev.py` | bab/sub-bab/paragraf skripsi | buku (terbukti salah) |
| Jev diagram | `tahapan_diagram.py` | jumlah tahap diagram | bentuk naskah |
| Jev konversi jurnal | `app/konversi.py` | bab + 11 elemen mutu | buku |

**Satu jalur, satu peran.** `app/jev.py` tetap SATU-SATUNYA pintu.

---

## 7. 🚨 TABEL BOCOR TOPIK — AKAR & OBAT (20 Okt 2026)

### 7.1 Gejala terukur

Buku anak **"Mengamati Langit: Dari Matahari Hingga Awan"** terbit dengan
2 tabel yang isinya:

```
| Aspek | Ekonomi Tradisional | Ekonomi Digital |
| Aset Utama | Properti fisik & modal mesin | Data & algoritma |
| Platform Interaksi | Pasar fisik & tatap muka | Aplikasi & pasar dua sisi |
```

Padahal penandanya di naskah:
`[TABEL 1.1: Bayangan Tongkat Sepanjang Hari - Waktu, Posisi Matahari, Bayangan]`

⇒ **Buku tentang langit berisi tabel Gojek/Tokopedia.** Ini bocor topik,
bukan sekadar cacat tampilan.

### 7.2 Rantai sebab (6 mata rantai, bukan 1)

| # | Akar | Bukti terukur |
|---|---|---|
| ① | Prompt contohnya sendiri memakai **ekonomi digital** | `architect_prompt` lama: `[TABEL 1.1: Judul Tabel - Aspek, Ekonomi Tradisional, Ekonomi Digital]` ⇒ AI MENIRU contoh |
| ② | Prompt menaruh `Baris1:` **di luar** kurung siku, parser memotong di `]` | `rows: []` untuk semua tabel buku langit |
| ③ | `tables[tid] = {..., 'rows': []}` **MENIMPA** hasil loop di atasnya | tambalan pertama Wulan (memasukkan `_row` sebelum baris ini) **tidak berpengaruh sama sekali** |
| ④ | `TABEL_DATA_FALLBACK` = **12 tabel CONTOH ekonomi digital**, selalu jadi titik awal `load_tabel_data()` | id `1.1`/`1.2` nyata dipakai buku langit ⇒ contoh ekonomi masuk |
| ⑤ | Perakit **selalu** membuat tabel walau `rows` kosong, diisi `"..."` | pembaca melihat "tabel" tanpa data |
| ⑥ | `add_glosarium(doc, {})` tetap membuat tabel **1 baris × 2 kolom** | halaman GLOSARIUM berisi tabel header saja |

### 7.3 Obat AKAR (bukan tambalan)

| # | Berkas | Perubahan |
|---|---|---|
| ① | `buku_umum_pipeline.py` `architect_prompt` | contoh tabel **tentang cuaca** (bukan ekonomi); bentuk WAJIB semua di dalam `[ ]`; larangan "JANGAN pakai contoh dari buku lain" |
| ②③ | `buku_umum_pipeline.py` `parse_tabel_marker` | **DITULIS ULANG: satu fase, satu penulis.** Regex tidak memotong di `]`; `tables[tid]` dibuat SEKALI; Fase 2 hanya MENAMBAH. Mendukung 2 bentuk (di dalam & setelah penanda) |
| ④ | `buku_umum_assembly.py` `load_tabel_data` | entri `rows: []` **DIBUANG**; kalau semua kosong ⇒ `return {}`; fallback contoh **hanya** kalau pipeline kosong total |
| ⑤ | `buku_umum_assembly.py` `add_bab` | `if not rows_data: continue` — tabel tanpa baris **tidak dirakit**; cabang `"..."` **dihapus** |
| ⑥ | `buku_umum_assembly.py` `add_glosarium` | `kosong=True` ⇒ halaman ada, tabel **tidak** dibuat, diganti keterangan |

### 7.4 Bukti (buku baru dari awal, AI sungguhan, 410 detik)

| | Sebelum | **Sesudah** |
|---|---|---|
| Tabel 1.1 | Aspek/Ekonomi Tradisional/Ekonomi Digital | **Waktu/Posisi Matahari/Bayangan** + 3 baris |
| Tabel 1.2 | Pilar Ekonomi/Tradisional/Digital | **Bentuk Awan/Warnanya/Pesannya** + 4 baris |
| Tabel glosarium | 1×2 kosong | **tidak ada** (keterangan jujur) |
| `rows` di JSON | **0** | **3 dan 4** |
| Paragraf isi | — | 94 · median **26 kata** · terpanjang 50 · **0** >7 kalimat |

Isi tabel sekarang: `Pagi, Rendah di timur, Panjang sekali` ·
`Tipis seperti rambut, Putih, Cuaca cerah` — **sesuai topik buku**.

### 7.5 Gerbang bergigi

| Gerbang | Asersi | Bergigi? |
|---|---|---|
| `gerbang_tabel_buku.py` | **11/0** | ✅ suntikan akar ④ ⇒ 1 GAGAL |
| `uji_parser_tabel.py` | **11/0** | ✅ bentuk A & B keduanya diuji |

Keduanya masuk `scripts/gerbang_uji.sh` grup 10.

### 7.6 Pelajaran

1. **Tambalan pertama Wulan CACAT** — memasukkan `_row` ke `rows` SEBELUM
   baris yang menimpa `tables[tid]`. Nol pengaruh. Ketahuan karena DIUJI,
   bukan karena dibaca.
2. **Prompt contoh = sumber tiruan.** Menaruh contoh ekonomi di prompt
   membuat AI menulis ekonomi — meski instruksinya "jangan".
3. **Fallback contoh HARAM dipakai saat naskah punya data.** Lebih baik
   tidak ada tabel daripada tabel salah topik.

---

## 8. 📐 PARAGRAF TERLALU PENDEK — ANGKA TONE, BUKAN MESIN BARU (20 Okt 2026)

### 8.1 Keluhan Bos (verbatim)

> "Jumlah satu paragraf sangat sedikit… paling tidak 2-3 paragraf sekarang
> bisa di gabung jadi satu paragraf saja."

### 8.2 Akar

Mesin perakit **sudah benar** — ia hanya mengikuti `tone_menulis.py`. Yang
salah adalah **angkanya**: target tone buku anak `25-40 kata`, padahal
paragraf buku anak wajar 55–85 kata.

### 8.3 Obat — ubah ANGKA, jangan tambah mesin merge

| Berkas | Sebelum | Sesudah |
|---|---|---|
| `tone_menulis.py` anak | 25–40 kata | **55–85 kata, 4–5 kalimat** |
| `tone_menulis.py` pendidikan | 40–70 kata | **55–80 kata** |
| larangan | >70 kata | **>90 kata** |

### 8.4 Bukti terukur

| Ukuran | Sebelum | Sesudah |
|---|---|---|
| Jumlah baris | 75 | **35** |
| Median kata/paragraf | — | **64** |
| Uji buku nyata (1 bab) | — | median **68**, 31 paragraf, 13 @55–85 |

⚠️ Urutan wajib di `post_process`: **PECAH dulu, baru GABUNG**; `jenis`
WAJIB diteruskan (toleransi pecah = 2× tone).

---

## 9. 🎨 DIAGRAM — 8 BENTUK DIPILIH DARI ISI (20 Okt 2026)

### 9.1 Keluhan Bos (verbatim)

> "Diagram Masih gunakan diagram lama, kotak garis, panah ke bawah. =
> Jelek! Dan rata kanan kiri flat sangat jelek untuk diagram."

### 9.2 Akar

`_GAYA_DIAGRAM` di `buku_umum_pipeline.py` hanya punya **satu bentuk**
(kotak → ▼ → kotak), plus cacat tata letak: `.susun{align-items:center}`,
`.tahap{width:100%}`, `.kartu{width:720px}` ⇒ melebar penuh & rata kiri-kanan.

### 9.3 Obat — modul `diagram_buku.py` (8 bentuk, dipilih dari isi)

| Isi naskah | Bentuk |
|---|---|
| daur / siklus / berulang | siklus |
| langkah / cara / tahap | alur |
| hierarki / tingkat / piramida | piramida |
| proporsi / persen / bagian | pai |
| tren / tahun / naik-turun | garis |
| jenis-jenis / golongan | pohon |
| lapisan / susun | lapisan |
| perbandingan / lebih dari | batang |

Aturan tampilan (dikunci Bos): lebar kartu **520px (72%)**, teks **rata
tengah**, **bukan** justify dan **bukan** full width.

### 9.4 🚨 SIKLUS — 4× GAGAL, AKHIRNYA LABEL KELUAR DARI SVG

Cacat berulang: label terpotong (`"mengalr"`) atau tertimpa nomor.

**Akar:** label digambar **di dalam SVG** padahal panjang teks tidak
diketahui saat menggambar — berapa pun `clamp()` ditambah, tetap bisa
meleset.

**Obat:** SVG **hanya cincin + nomor besar**; label jadi **daftar HTML di
bawah gambar** ⇒ mustahil terpotong. **PANAH DIBUANG** (putusan Bos:
*"Kurang pas panah nya"*) — arah dibaca dari urutan nomor berwarna.

Bukti: `diag_siklus_v5.png` (46.743 B), terverifikasi mata.

### 9.5 Piramida

Versi kotak bertumpuk terbaca **"terbalik"**. Diganti **trapesium SVG
bertingkat** (level terbawah paling lebar). Terverifikasi mata.

---

## 10. 🖼️ ILUSTRASI — 4 AKAR, SATU DI ANTARANYA SENYAP (20 Okt 2026)

### 10.1 Keluhan Bos (verbatim)

> "background putih saja ada outline… daripada sekarang background coklat
> muda, seperti buku kuno/lawas dan terlihat kotor atau background abu abu
> muda / halus"

### 10.2 Empat akar (bukan satu)

| # | Akar | Sifat | Bukti |
|---|---|---|---|
| ① | `brief_visual` mengimpor **2 fungsi yang TIDAK ADA** (`_gambar_inferhub`, `gambar_dari_prompt`) | `ImportError` — mati total | 0 berkas dihasilkan |
| ② | Model `cb/gemini-2.5-flash-image` = **CodeBuddy**, kreditnya habis | galat **14018** "Credits exhausted" | saldo InferHub **$7,57 utuh**; 1 dari 9 model hidup: `gemini-2.5-flash-image` **tanpa `cb/`** |
| ③ | Gaya `anak`/`pendidikan` di `jenis_buku.py` masih `light blue background` + `3D clay render` | latar & gaya salah | PNG biru bergradasi, tanpa outline |
| ④ | **Blok gaya TANPA placeholder `{brief}`** ⇒ `blok.format(brief=…)` membuang brief **tanpa error** | **SENYAP** | brief benar ("anak menongkat bayangan"), PNG keluar **kasir toko** |

### 10.3 Akar ④ = yang paling berbahaya

`.format()` **tidak error** walau placeholder tak ada. Prompt tetap jadi,
gambar tetap keluar, QC lolos — tapi isinya **karangan**. Baru ketahuan
**dilihat mata**.

### 10.4 Obat

1. `_gambar_inferhub(prompt, simpan, ukuran, seed, timeout)` — **pintu
   tunggal** ke InferHub, memakai inti kode `generate_ilustrasi_api` yang
   **sudah ada** (bukan mesin baru).
2. `GAMBAR_MODEL = "gemini-2.5-flash-image"` (**tanpa `cb/`**).
3. Gaya `anak` + `pendidikan` dirombak: **PURE WHITE `#FFFFFF`** + outline
   gelap tegas + `no text/letters/numbers`.
4. **`{brief}` WAJIB ada** di setiap blok gaya (3 tempat).

### 10.5 Bukti (mata)

| Yang diminta | v1 | **v3** |
|---|---|---|
| Latar putih | ❌ biru gradasi | ✅ putih murni |
| Outline | ❌ shading 3D | ✅ garis hitam tegas |
| Tanpa teks | ❌ ada "1000" | ✅ nol |
| Sesuai isi bab | ❌ kasir/panen | ✅ anak menongkat + bayangan |

---

## 11. 🚨 PENANDA `[DIAGRAM]` JADI TEKS MENTAH — JE V KELEWATAN `]` (20 Okt 2026)

### 11.1 Gejala terukur

Naskah memuat **2 penanda diagram**, `.docx` hanya memuat **1** gambar
diagram. Diagram 1.1 **TERCETAK MENTAH**:

```
[DIAGRAM 1.1: Perjalanan Matahari dan Bayanganmu - Gambar matahari
bergerak dari timur ke barat, dengan tongkat di tenga
```

`visual_hilang: []` — **kosong**, karena PNG-nya memang ADA di disk.
Cacat ini **SENYAP**.

### 11.2 Akar (satu, bukan tiga)

`jev_buku_umum._POLA_DIAGRAM` **mewajibkan `]` penutup**:

```python
_POLA_DIAGRAM = re.compile(r'\[\s*DIAGRAM\s+\d+\.\d+[^\]]*\]', re.I)
```

Penulis (LLM) **memotong** tanda itu — baris 135 karakter tanpa `]`. Maka
`_pecah_penanda` tidak mengenalinya, dan penanda lolos jadi `paragraf`.

**Jalur regex (`parse_bab_file`) BENAR** — ia sudah punya
`_POLA_PENANDA_GADUH`. **Jev belum.** Itulah sebabnya **hanya jalur Jev**
yang kehilangan diagram.

### 11.3 Obat

Pola cadangan `_POLA_TABEL_GADUH` / `_POLA_DIAGRAM_GADUH` yang mengambil
**sisa baris** bila `]` tidak ada. Pola utama dicoba **dulu**; cadangan
hanya bila pola utama tidak menemukan apa pun di baris itu.

⚠️ **Menggunakan pola yang SUDAH TERUJI** di `buku_umum_assembly`
(`_POLA_PENANDA_GADUH`) — **bukan mekanisme baru**.

### 11.4 Bukti

| Pemeriksaan | Sebelum | Sesudah |
|---|---|---|
| Blok `diagram_marker` dari Jev | **1** | **2** |
| `Counter` Jev | 26 paragraf, 1 diagram | 26 paragraf, **2 diagram**, 2 tabel |
| Teks mentah `[DIAGRAM` di `.docx` | **1** | **0** |
| Gambar di `.docx` | **2** | **3** (679 + 33 + 42 KB) |
| `Detik rakit` | — | 1,2 |

### 11.5 Akar sampingan: `rakit()` menimpa `VISUAL_DIR` buta

`rakit()` hanya menunjuk `bab{n}/visual/` kalau folder itu ada — kalau
tidak, `VISUAL_DIR` **warisan**. Obat: **jatuh ke folder visual akar**
(`OUT/visual/`) bila folder bab tidak ada.

### 11.6 🚨 UJI BERGIGI WULAN 3× GAGAL PALSU

Uji bergigi versi awal melaporkan **"0 BERGIGI, 3 HIASAN"** — Wulan
hampir menyalahkan kode yang **sehat**. Ternyata **alat ujinya** rusak:

**Menyalin `jev_buku_umum.py` ke `/tmp` TIDAK PERNAH dibaca.** Buktinya
dicetak langsung:

```
MODUL: /app/jev_buku_umum.py
POLA : \[\s*DIAGRAM\s+\d+\.\d+[^\]\n]*$
```

Walau `sys.path` diarahkan ke `/tmp`, `jev_buku_umum` **sudah terimpor**
lewat rantai impor `/app` ⇒ modul `/app` yang menang.

**OBAT: rusak DI MEMORI (`sys.modules`), bukan lewat berkas.** Hasil:
**4 BERGIGI / 0 HIASAN**.

> Pelajaran 15 Okt berlaku lagi: *"PRODUKSI SEHAT, yang rusak ALAT UJI."*

---

## 12. GERBANG BUKU — DAFTAR & HASIL (20 Okt 2026)

| Gerbang | Hasil | Bergigi |
|---|---|---|
| `gerbang_tabel_buku` | 11/0 | ✅ |
| `uji_parser_tabel` | 11/0 | ✅ |
| `gerbang_ambang_paragraf` | 21/0 | ✅ |
| `gerbang_verifikasi_sitasi` | 8/0 | ✅ |
| `gerbang_jev_buku` | 28/0 | ✅ |
| `gerbang_tata_paragraf` | 37/0 | ✅ |
| `gerbang_keluhan_20okt` | **27/0** | ✅ 5/5 |
| `gerbang_placeholder_brief` | **20/0** | — |
| `gerbang_penanda_jadi_gambar` | **12/0** | ✅ 4/4 |
| **Total** | **175 LULUS / 0 GAGAL** | |

### 12.1 Tiga gerbang gagal-palsu yang SUDAH diperbaiki

| Gerbang | Gagal palsu karena | Obat |
|---|---|---|
| `gerbang_keluhan_20okt` | cari kata `justify` ⇒ tertangkap `justify-content:center` | regex `text-align\s*:\s*justify` |
| `gerbang_keluhan_20okt` | pola hex `#f…` ⇒ `#ffffff` (PUTIH) dianggap krem | **hitung RGB**: hangat kalau `R−B ≥ 12` & `R ≥ 200` |
| `uji_gigi_penanda` | salin berkas ke `/tmp` tak terbaca | rusak **di memori** |

### 12.2 Aturan yang lahir hari ini

1. Gerbang **WAJIB bisa GAGAL** — kalau suntikan tak menggigit, itu HIASAN.
2. Suntikan **DI MEMORI**, bukan lewat salinan berkas.
3. Asersi harus **spesifik** (`text-align:justify`, bukan `justify`).
4. Warna diperiksa **secara hitungan** (RGB), bukan pola teks.
5. **`{brief}` WAJIB** di setiap blok gaya — dijaga gerbang.
6. Jumlah penanda di naskah **==** jumlah gambar+tabel di `.docx`.

---

## 13. YANG BELUM SELESAI (jujur, diperbarui 21 Okt 2026)

| # | Yang belum | Status |
|---|---|---|
| 1 | ~~**Belum deploy**~~ | ✅ **SELESAI 21 Okt** — `eduai-app:20261021_014708-sot`, produksi 200 |
| 2 | **Uji buku baru 1 bab** | belum multi-bab sesudah semua perbaikan |
| 3 | **Ilustrasi belum diuji di buku >1 bab** | baru 1 bab |
| 4 | **`gerbang_placeholder_brief` belum bergigi** | belum ada uji suntikan |
| 5 | **Belum diuji lewat rute** `/buku/susun` | baru lewat skrip |
| 6 | **`_gambar_inferhub` biaya per gambar belum diukur** | — |
| 7 | **Pengingat pensiun Jev 1.13** (≈13 Des 2026) | 🟡 **RENCANA, ditunda Bos** — §17 |

---

## 14. LARANGAN (HARAM DILANGGAR)

1. **JANGAN menambal di hilir** — cari penulis/penyebabnya.
2. **JANGAN bikin mesin gambar/tabel/diagram KEDUA** — pakai yang ada.
3. **JANGAN menggambar label di dalam SVG** untuk teks yang panjangnya
   tak diketahui — pakai daftar HTML di luar gambar.
4. **JANGAN pakai model ber-prefix `cb/`** untuk gambar — itu jalur
   CodeBuddy, kreditnya terpisah dan sering habis.
5. **JANGAN hapus `{brief}`** dari blok gaya — brief akan hilang **tanpa
   error**.
6. **JANGAN uji bergigi dengan menyalin berkas** — rusak di memori.
7. **JANGAN percaya `visual_hilang: []`** sebagai bukti gambar masuk —
   hitung media di dalam `.docx`.
8. **JANGAN percaya gerbang hijau sebagai bukti produksi sehat** —
   modul yang dipakai produksi WAJIB dibuktikan dengan
   `docker exec <c> python3 -c "import <modul>"` (§15).
9. **JANGAN andalkan `log.warning` sebagai penjaga** — peringatan "Jev gagal,
   pakai jalur regex" ADA (`buku_umum_assembly:756`), tapi tidak ada yang
   membacanya dan hasilnya tetap wajar. Penjaganya = gerbang yang bertanya
   langsung ke image (§15.4 Lapis 2), bukan log.
10. **JANGAN pakai alias model Jev** (`jev-latest` / `jev-preview`) — ia
    berpindah sendiri saat rilis baru, dan ambang kita (0,80 / 0,95) jadi
    tidak sah tanpa ada yang mengubahnya. **Selalu pin versi** (§16.10).
11. **JANGAN naikkan versi model Jev karena klaim vendor** — TypeSafe menyebut
    1.14 "perbaikan di semua hal" dengan **nol angka**. Naik hanya setelah
    **diukur** pada naskah kita sendiri (§16.3).

---

## 15. 🚨 GERBANG HIJAU ≠ PRODUKSI SEHAT — TIGA MODUL HILANG DARI IMAGE (21 Okt 2026)

### 15.1 Kejadian (terukur, bukan dugaan)

Sesudah deploy, Wulan memeriksa modul dari **dalam container hidup**:

```
docker exec eduai-app python3 -c "import jev_buku_umum"
→ ModuleNotFoundError: No module named 'jev_buku_umum'
```

Tiga modul **inti** ternyata **tidak pernah ada** di dalam image:

| Modul | Fungsi | Akibat bila hilang |
|---|---|---|
| `jev_buku_umum.py` | Jev pembaca BENTUK naskah buku | Jev **mati** — jatuh ke jalur regex lama |
| `diagram_buku.py` | penggambar 8 bentuk diagram | diagram balik ke template lama |
| `tata_paragraf.py` | pemecah & penggabung paragraf | **perakit buku gagal total** |

Ketiganya **tidak pernah ada di `Dockerfile`**. Bukan terhapus — **tidak pernah ditulis** dari awal.

### 15.2 Kenapa ini paling berbahaya

Cacatnya **SENYAP bagi USER** — tapi **TIDAK bisu di log**. Rantainya:

1. `buku_umum_assembly:744` mengimpor `jev_buku_umum` di dalam `try/except`.
2. Di container impor **gagal**, `except Exception` menangkap, lalu menulis
   satu baris `log.warning('[buku] Jev bentuk GAGAL (...) — pakai jalur regex')`
   (`buku_umum_assembly:756`).
3. Perakit **jatuh ke jalur regex lama** (`parse_bab_file`).
4. Buku **tetap terbit**. Isinya "mirip benar", hanya tanpa Jev dan tanpa
   8 bentuk diagram.

Jadi **tidak ada gejala yang dilihat user**. Yang rusak bukan hasilnya —
yang rusak **mutunya**, dan itu tak terlihat dari layar.

⚠️ **KOREKSI (21 Okt, terukur):** Wulan sempat menulis di draf bahwa impor ini
"bisu tanpa satu baris ke log". **Itu SALAH** — `log.warning` ADA di baris 756.
Yang benar: peringatannya ada, **tetapi tidak ada yang membacanya**, karena:
- log container tidak dipantau rutin,
- peringatannya `WARNING`, bukan `ERROR`,
- hasilnya tetap wajar sehingga tak ada alasan memeriksa log.

**Pelajaran:** "ada log" ≠ "cacat kelihatan". Cacat seperti ini hanya tertangkap
oleh **gerbang yang bertanya langsung ke image** (15.4 Lapis 2), bukan oleh log.

### 15.3 Kenapa 142 gerbang TIDAK menangkapnya

Semua gerbang buku dijalankan **di host** dengan `sys.path` menunjuk folder
proyek. Di host ketiga berkas itu **ADA**. Jadi semua gerbang hijau.

> **Gerbang yang mengimpor dari folder kerja TIDAK membuktikan modul ikut
> ke image.**

Satu-satunya yang membuktikan:

```bash
docker exec eduai-app python3 -c "import <modul>"
# atau, untuk image yang BELUM dipasang:
docker run --rm --entrypoint python3 <image>:<tag> -c "import <modul>"
```

### 15.4 Obat (3 lapis, bukan tambalan)

**Lapis 1 — Dockerfile.** Tambah tiga baris `COPY`:

```dockerfile
COPY jev_buku_umum.py ./jev_buku_umum.py
COPY diagram_buku.py  ./diagram_buku.py
COPY tata_paragraf.py ./tata_paragraf.py
```

**Lapis 2 — gerbang baru `gerbang_modul_di_image.py`.**
Menanyakan **langsung ke image** (bukan host). 15 modul mesin buku wajib bisa
diimpor. Hasil akhir: **20 LULUS / 0 GAGAL** pada container hidup.

**Lapis 3 — urutan gerbang dipindah.**
Gerbang itu **tidak bisa** dinilai di Langkah 0 karena image-nya belum
dibangun. Dulu ia dipanggil di Langkah 0 sehingga membaca **container lama**
⇒ deploy dibatalkan padahal image baru sehat (terjadi **1×** hari ini).
Sekarang ia dijalankan di **Langkah 4** `jalankan.sh`, setelah `docker build`,
sebelum ganti container. Gagal ⇒ `exit 1`, container **tidak** diganti.

### 15.5 Bukti (hasil nyata)

```
=== setelah deploy 20261021_014708-sot ===
jev_buku_umum      → /app/jev_buku_umum.py
diagram_buku       → /app/diagram_buku.py
tata_paragraf      → /app/tata_paragraf.py
buku_umum_assembly → /app/buku_umum_assembly.py
buku_umum_pipeline → /app/buku_umum_pipeline.py
gerbang_modul_di_image: {"lulus": 20, "gagal": 0}
eduai.bikinaja.id: 200 · /health: 200 · DB 26 tabel · users=6 · files=23
```

### 15.6 ATURAN INDUK BARU (WAJIB, di luar proyek buku)

1. **Gerbang hijau di host BUKAN bukti produksi.** Setiap modul yang dipakai
   jalur produksi wajib dibuktikan dengan `docker exec`/`docker run`.
2. **`Dockerfile` = daftar putih.** Berkas `.py` baru yang dipanggil produksi
   **wajib** ditambahkan `COPY`-nya. Tanpa itu ia hidup di host, mati di image.
3. **`try/except ImportError` tanpa log = penyembunyi cacat.** Impor yang
   gagal harus **berteriak** (minimal `log.error`), bukan diam lalu jatuh ke
   jalur lama.
4. **Gerbang yang butuh build diletakkan SESUDAH build**, bukan sebelum.

### 15.7 Pelajaran alat uji (ketiga kali)

Wulan **2× salah** hari ini saat menegakkan gerbang ini:

- **Pertama:** gerbang dipanggil di Langkah 0 ⇒ menilai container lama ⇒
  deploy dibatalkan padahal image baru sehat.
- **Kedua:** Wulan kira cukup mengubah `sys.path` untuk menguji image lain.
  Ternyata **`sys.modules` menang** atas `sys.path` — modul yang sudah
  terimpor lewat rantai `/app` tidak bisa diganti begitu saja.

Obat yang terbukti: **rusak di memori** (`setattr(modul, ...)`), atau
**jalankan proses baru di dalam image** (`docker run --rm`). Menyalin berkas
ke `/tmp` **tidak pernah** dibaca.

Ini pola yang sama dengan pelajaran 15 Okt 2026: **PRODUKSI SEHAT, YANG RUSAK
ALAT UJI.** Sebelum menuduh kode, periksa dulu alat ukurnya.

---

## 16. 🧪 JEV 1.14 — DIUJI, TIDAK DINAIKKAN (21 Okt 2026)

### 16.1 Kenapa diperiksa

TypeSafe merilis **`jev-1.14.0`** pada 14 Okt 2026. Kode kita masih memakai
`jev-1.13`. Klaim resmi: *"small, subtle improvements to everything"*, dengan
keunggulan terbesar **dukungan multibahasa** — dan itu sangat relevan karena
naskah kita berbahasa Indonesia.

**TypeSafe TIDAK memberi satu angka pun** dan sendiri menyarankan: uji dulu
pada kasus sendiri sebelum pindah.

### 16.2 Nama model — WAJIB BENAR (terukur)

| Nama | Hasil |
|---|---|
`typesafe/jev-1.14` | ✅ **HIDUP** — balasan menyebut `typesafe/jev-1.14-20261014` |
`typesafe/jev-1.13` | ✅ hidup — `typesafe/jev-1.13-20260917` |
`SATPAM/typesafe/jev-1.13` | ✅ hidup (yang sekarang tertanam) |
`Byn/jev-1.14.0` | ❌ **400** — muncul di `/v1/models` 9router tapi ditolak upstream |
`typesafe-ai/jev-1.14.0` | ❌ **400** — nama Vercel AI Gateway, bukan di sini |

⚠️ **`jev-1.14.0` TIDAK terdaftar di katalog OpenRouter publik** (dicek 21 Okt,
468 model; hanya ada `typesafe/jev-router`). 1.14 hidup **lewat jembatan 8130**
kita, bukan jalur OpenRouter langsung.

⚠️ **Selalu catat `model` dari BALASAN**, bukan dari yang kita kirim.

### 16.3 Hasil uji A/B — 34 pertanyaan, 3 naskah Indonesia

| Naskah | Panjang | Pertanyaan | Sama | Beda | Δ noul rata |
|---|---|---|---|---|---|
Buku bab 1–3 (mudah) | 1.960 kar | 13 | **13/13** | 0 | 0,005 |
Buku kias bab 4–5 (sulit) | 2.862 kar | 9 | **9/9** | 0 | 0,018 |
Artikel jurnal | 2.580 kar | 12 | **12/12** | 0 | 0,001 |

**34/34 jawaban IDENTIK.** Yang sengaja diuji sebagai jebakan:
- Kritik tersirat tanpa kata "kritik" → 0,93 vs 0,89 (sama-sama menangkap)
- Hal yang **TIDAK ADA** di naskah → 0,01 vs 0,01 (dua-duanya benar menolak)
- Membedakan kesimpulan bab vs klaim yang dibantah → sama

### 16.4 Kestabilan — 1.14 TIDAK LEBIH STABIL

| Model | Naskah mudah (3×) | Naskah sulit (5×) |
|---|---|---|
`jev-1.13` | 5/13 berubah | **3/9** |
`jev-1.14` | **3/13** | **5/9** |

Rentang goyangan kecil (0,01–0,09), tetapi arahnya jelas: **di naskah sulit
1.14 lebih goyah** daripada 1.13. Ini **tidak diberitakan** TypeSafe.

### 16.5 Biaya & waktu

| | Token | Biaya | Waktu |
|---|---|---|---|
1.13 | 1.597–1.701 | **identik** | 0,75–0,98 dtk |
1.14 | 1.597–1.701 | **identik** | 0,77–5,82 dtk |

Biaya **sama persis** (sesuai dokumentasi resmi). Waktu **tidak bisa diklaim
lebih cepat** — beda 5,82 vs 0,98 dtk itu variasi jaringan, bukan model.

### 16.6 PUTUSAN: kode produksi TETAP `jev-1.13`

5 alasan terukur:
1. **Nol perbaikan** pada 34 pertanyaan naskah Indonesia nyata
2. **Tidak lebih stabil** — justru lebih goyah di naskah sulit (5/9 vs 3/9)
3. Ambang 0,80 (satpam) / 0,95 (ragu) **tetap sah** — tidak perlu disetel ulang
4. `jev-1.13.0` masih hidup **60 hari** sejak 14 Okt (≈13 Des 2026)
5. Naik = risiko tanpa imbalan terukur

**Tidak ada satu baris kode produksi yang diubah.** `app/jev.py` dan
`app/satpam.py` tetap `'SATPAM/typesafe/jev-1.13'`.

### 16.7 KAPAN MENAIKKAN (syarat, bukan tanggal)

- Ada naskah **Inggris / Arab / Mandarin** yang perlu diproses — klaim
  multibahasa mungkin menang di situ. **Uji dulu dengan skrip yang sama.**
- Butuh tipe **`box`** (letak tanda tangan, posisi gambar scan, cari bagian
  di naskah pindai) — `box` HANYA ada di 1.14
- `jev-1.13.0` mendekati pensiun (≈13 Des 2026)

### 16.8 Tipe `box` — fitur nyata satu-satunya

Terbukti jalan di 1.14, **ditolak 1.13** (HTTP 400 `Invalid request`).
Mengembalikan 4 sisi (0–1) + `confidence`; **selalu** mengembalikan kotak
(tidak ada jawaban "tidak ditemukan" ⇒ pasangkan dengan `noul`).
Butuh header `TypeSafe-Danger-Zone-Images: true`.
**Belum dipakai di EduAi.**

### 16.9 Alat uji (jangan dibuang)

- `_sketsa/uji_ab_jev_1_14.py` — ronde 1, naskah mudah, 13 pertanyaan
- `_sketsa/uji_ab_jev_ronde2.py` — ronde 2, naskah sulit, 21 pertanyaan
- Bukti: `/opt/data/bukti_jev_ab_21okt2026.json`
- Biaya satu putaran penuh **≈ $0,0004** (di bawah Rp 10)

⚠️ **JANGAN panggil 9router langsung** untuk Jev — `app/jev.py` menolak keras
`:20128`. Selalu lewat jembatan **8130**.

### 16.10 Aturan induk baru

**JANGAN pakai alias `jev-latest` / `jev-preview`.** Ambang kita disetel untuk
satu versi; alias berpindah sendiri ⇒ ambang jadi tidak sah tanpa ada yang
mengubahnya. Resmi: *"pin that version's ID instead of the alias."*

**Klaim vendor BUKAN bukti.** TypeSafe menyebut "perbaikan di semua hal" tapi
memberi nol angka. Yang mengikat = hasil ukur pada naskah kita sendiri.

---

## 17. 📋 RENCANA — PENGINGAT PENSIUN JEV 1.13 (BELUM DIKERJAKAN)

**Status: 🟡 RENCANA, ditunda atas putusan Bos 21 Okt 2026.**
**DILARANG dikerjakan sampai Bos membuka lagi** (pola sama dengan RUANG MANOVA).

### 17.1 Masalah yang mau ditutup

TypeSafe merilis 1.14 pada **14 Okt 2026** dan memberi **60 hari** pemberitahuan
sebelum `jev-1.13.0` dipensiunkan ⇒ **≈13 Des 2026**.

Risiko: kalau tanggal itu **terlupa**, EduAi mati mendadak — dan Jev adalah
**tulang punggung app** (putusan Bos 8 Okt 2026), bukan fitur tambahan.

### 17.2 Usulan Bos (21 Okt 2026)

> *"Lebih baik typesafe/jev-1.14 jadi auto fallback, jika nanti lupa bahwa 60
> hari kemudian jev lama akan mati, jadi tidak berdampak."*

### 17.3 Jawaban Wulan — kenapa fallback SAJA tidak cukup

**Fallback otomatis mengubah "mati total" menjadi "hidup tapi diam-diam
kurang presisi".** Yang kedua lebih berbahaya untuk app yang Jev-nya tulang
punggung.

Alasan terukur (dari §16.4):
- `jev-1.14` **lebih goyah** di naskah sulit — 5/9 pertanyaan berubah antar
  panggilan, sedangkan 1.13 hanya 3/9
- Artinya saat fallback aktif, ambang **0,80 (satpam) / 0,95 (ragu) jadi tidak
  sah** — tanpa ada yang tahu
- TypeSafe **memberi 60 hari** justru supaya migrasi dilakukan **terukur**;
  fallback otomatis membuang jendela itu

### 17.4 Tiga lapis yang diusulkan (belum dipilih Bos)

**Lapis 1 — Gerbang pengingat sisa hari** *(disarankan Wulan, risiko nol)*
Gerbang yang menghitung sisa hari sampai ≈13 Des 2026:
- sisa **> 30 hari** → senyap
- sisa **≤ 30 hari** → peringatan di keluaran gerbang (tidak menahan)
- sisa **≤ 7 hari** → **deploy DITAHAN** (`exit 1`)
Ini yang benar-benar menutup risiko "lupa", tanpa mengubah perilaku Jev.

**Lapis 2 — Fallback berjejak** *(kalau Bos tetap mau)*
Syarat wajib, mengikuti pola fallback peta yang sudah diputuskan 14 Okt
(`peta_dari: jev|fallback`) — **jangan bikin pola baru**:
- Hanya aktif saat 1.13 **mati keras** (HTTP 4xx / model tidak ada / timeout),
  **BUKAN** saat 1.13 cuma ragu
- **Log terang** + penanda `model_dipakai` di balasan
- **Notifikasi ke Bos** saat fallback aktif (tidak boleh senyap)
- **Ambang diturunkan** selama fallback (0,80 → 0,75), karena 1.14 lebih goyah

**Lapis 3 — Migrasi terukur** *(yang sebenarnya benar)*
Saat mendekati pensiun, ukur ulang ambang dengan skrip yang **sudah ada**
(`_sketsa/uji_ab_jev_1_14.py` + `uji_ab_jev_ronde2.py`). Biaya 1 putaran penuh
**≈ $0,0004**, waktu beberapa menit.

### 17.5 Titik pemasangan yang SUDAH dipetakan (kalau nanti dikerjakan)

| Berkas | Peran |
|---|---|
`services/satpam-jev/jembatan.py:145-152` | **titik fallback paling tepat** — jembatan yang memilih model; satu tempat, tidak menyentuh app |
`services/satpam-jev/jembatan.py:68` | model bawaan dibaca dari DB 9router (`defaultModel`), cadangan `typesafe/jev-1.13` |
`services/satpam-jev/jembatan.py:118-126` | `/v1/models` — laporkan model yang **benar-benar** dipakai |
`app/jev.py:81` | `MODEL_DEFAULT` app (semua pemanggil lewat sini) |
`app/satpam.py:39` | `MODEL` satpam (bisa ditimpa `EDUAI_SATPAM_MODEL`) |

**Catatan penting:** semua pemanggil Jev di app lewat **satu titik**
(`app/jev.py`). Jadi fallback di jembatan **tidak perlu menyentuh app sama
sekali** — cukup satu berkas.

### 17.6 Yang WAJIB dijaga kalau dikerjakan

1. **Jangan pakai alias** `jev-latest` / `jev-preview` (§16.10)
2. **Jangan fallback saat ragu** — hanya saat mati keras
3. **Jangan senyap** — fallback tanpa notifikasi = bahaya tersembunyi
4. **Ambang harus ikut turun** saat fallback aktif
5. **Uji bergigi wajib**: matikan 1.13 secara buatan → harus terbukti pindah
   ke 1.14 DAN meninggalkan jejak

### 17.7 Cara membuka kembali

Bos bilang **"kerjakan pengingat Jev"** atau **"pasang fallback Jev"** ⇒
baca §17 ini, lalu tentukan lapis mana (1 / 2 / 3) sebelum menulis kode.
