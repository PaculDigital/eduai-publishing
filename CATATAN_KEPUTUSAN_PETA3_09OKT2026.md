# 🔖 PETA3_JEV — KEPUTUSAN TEKNIS 09 OKT 2026 (malam, terkunci)

> Berkas ini mencatat 4 poin yang Bos ajukan setelah membaca `peta3_jev.py`,
> beserta keputusannya. Dibuat supaya sesi berikutnya tidak menebak-nebak.

**Versi kode:** `peta3_jev.py` md5 **`293338ebdbe67d371628059abe6280be`** · 325 baris
**Backup titik ini:** `_arsip/pre-3aturan-09okt26/peta3_jev.FINAL-5aturan-varian.py`
**Sebelum perubahan:** `_arsip/pre-3aturan-09okt26/peta3_jev.SEBELUM-bab1-angket.py`

---

## POIN 1 — Varian "BAB 1" (angka) ✅ TERPASANG
`POLA_BAB` diperluas: `[IVX]+` → `[IVX0-9]+`
```
SEBELUM : re.compile(r'^BAB\s+([IVX]+)\s*$', re.I)
SESUDAH : re.compile(r'^BAB\s+([IVX0-9]+)\s*$', re.I)
```
Alasan: sebagian kampus memakai angka. UJI: `BAB I` ✅ · `BAB 1` ✅ · `BAB 10` ✅ ·
`BAB` (polos) ❌ benar · `BAB I PENDAHULUAN` ❌ benar (bukan bab polos).

## POIN 2 — Sinonim "ANGKET" ✅ TERPASANG
Aturan 3 diperluas:
```
SEBELUM : re.match(r'^\s*KUESIONER\b', s, re.I)
SESUDAH : re.match(r'^\s*(KUESIONER|ANGKET)\b', s, re.I)
```
Alasan: sebagian kampus memakai kata "ANGKET PENELITIAN".
UJI: `ANGKET PENELITIAN` ✅ · `Angket ini disebar` ✅ · `Catatan angket` ❌ benar (bukan awal baris).

## POIN 3 — D1 jangan bergantung label Jev ⚠️→✅ TERPASANG (2 putaran)

**Putaran 1 (SALAH — Wulan):** memakai `POLA_BAB.match()`.
**Bos mengoreksi (09 Okt):** `POLA_BAB` menuntut baris **HANYA** berisi `"BAB I"`
(`\s*$` di akhir) — dan semua baris seperti itu sudah **DISEDOT ke `gabung`**
di `susun()` ⇒ **tidak pernah jadi kandidat**. Sementara penyebutan sistematika
(`"BAB I PENDAHULUAN"`, ada judulnya) **tidak cocok** pola itu.
⇒ Klausa tambahan Wulan = **KODE MATI**; D1 tetap 100% bergantung label Jev.
TERBUKTI (diukur): `POLA_BAB.match('BAB I PENDAHULUAN')` = False ·
`POLA_BAB.match('1. BAB I PENDAHULUAN, bagian ini…')` = False.

**Putaran 2 (BENAR — koreksi Bos):** pakai pola **AWALAN**:
```
_POLA_BAB_TEKS = re.compile(r'^(?:\d+[.)]\s*|[IVX]+[.)]\s*)?BAB\s+[IVX0-9]+\b', re.I)
...
calon = [i for i in sorted(idx_kand)
         if _POLA_BAB_TEKS.match(baris[i].strip()) or label.get(i) == 'bab']
```
Awalan nomor daftar (`1.` `2)` `I.`) ditambahkan karena bentuk NYATA di naskah
Wulandari (PDF Bos) = `"1. BAB I PENDAHULUAN, bagian ini berisikan…"`.

UJI BERGIGI (4 skenario, semua LULUS):
```
A1 Asih, label normal          → [0,2,4,6,8] ✅
A2 Asih, Jev SALAH label       → [0,2,4,6,8] ✅  ← dulu GAGAL DIAM-DIAM
B1 Wulandari, Jev SALAH label  → [0,2,4,6,8] ✅  ← bentuk "1. BAB I PENDAHULUAN"
B2 Wulandari, label normal     → [0,2,4,6,8] ✅
C  2 bab berjauhan             → []           ✅  nol false positive (penjaga blok kerja)
```
VERIFIKASI ASIH: sistematika tetap `[191,195,199,203,207]` ✅ · bab 5 · subbab 130 ✅.

**CATATAN BOS (WAJIB ditegakkan):** kalau suatu hari Jev melabel penyebutan
sistematika sebagai `'subbab'` (bukan `'bab'`), D1 **tetap menandainya** ⇒
**penampil HTML WAJIB menghormati tag sistematika APA PUN labelnya**
(jangan hanya cek `label == 'bab'`). Status: `_saji_asih_utuh.py` sudah cek
`i in sis` (himpunan sistematika) — TERPENUHI ✅.

## POIN 4 — Ronde Jev beda pendapat → `'biasa'` 🔒 KEPUTUSAN BOS: **A (tetap konservatif)**
```
SEKARANG (dan TETAP): kalau putaran Jev beda pendapat (2 vs 1) ⇒ label 'biasa'
                      + baris itu MASUK daftar GOYANG (tercatat untuk audit).
ALASAN: Jev TIDAK YAKIN ⇒ lebih aman TIDAK memberi label daripada salah label.
        Selaras prinsip Bos: "RAGU ⇒ JANGAN dipaksa, tanyakan/tandai".
DITOLAK: (B) majority vote 2-vs-1 [risiko: label goyang terpakai fitur ⇒ AI salah potong];
         (C) majority vote + putaran 3→5 [biaya Jev naik 67%].
CATATAN: goyang 25 dari 491 kandidat (5%) — kecil, tidak mendesak.
```

## CATATAN KECIL (belum dikerjakan — sengaja, bukan terlupa)
Di `petakan()`, nama `_t` dipakai DUA peran: **fungsi konteks** (dari `susun()`)
lalu **variabel loop** (`for i, _t in kand`). TIDAK merusak (urutan aman),
tapi membingungkan pembaca berikutnya. Perbaikan = ganti nama 1 baris.
BELUM dikerjakan karena manfaat nol & risiko menyentuh kode sehat.

---

## URUTAN REGRESI (cara pakai)
```
docker cp peta3_jev.py eduai-app:/app/
docker exec -w /app eduai-app python3 _banding_baseline.py 81 ASIH
```
HASIL setelah 4 poin (bab 5 · subbab 130 · paragraf 160 · kandidat 491 · buang 720):
```
bab     : 5   → 5     ✅
subbab  : 130 → 130   ✅
paragraf: 156 → 160   🟡 (+4, goyang Jev biasa)
kandidat: 491 → 491   ✅
buang   : 720 → 720   ✅
⇒ "TIDAK ADA REGRESI — aman lanjut."
```

## POIN 6 & 7 (BARU, 09 Okt malam — temuan dari naskah #2) ✅ TERPASANG

**Latar:** Bos menjalankan `peta3_jev.py` ke skripsi kualitatif Wulandari (PDF).
Hasil: 4 BAB asli ketemu (merge bekerja, termasuk typo "BAB VI" setia),
tapi **89 dari 109 SUB-BAB PALSU (82%)** — baris fragmen PDF dilabel judul.
Bos menemukan akarnya: **BUKAN Jev, tapi EKSTRAKSI TEKS (hulu).**
Bukti: 4.047 baris, median 15 kar, 2.707 baris ≤20 kar (bandingkan Asih: 1.221 baris utuh).
Turunan: 94 nomor halaman jadi kandidat (2 dilabel BAB: "30","65") · 38 sub-bab + 78
paragraf diawali huruf kecil (aturan abadi dilanggar massal) · butir daftar jadi sub-bab.

### ATURAN 5 — baris diawali HURUF KECIL ⇒ KOREKSI LABEL (bukan buang)
```
koreksi_kecil = []
for i, _t in kand:
    if i in sistematika:
        continue                      # blok sistematika jangan disentuh
    t = baris[i].strip()
    if label.get(i) in ('bab', 'subbab') and t[:1].islower():
        label[i] = 'biasa'
        koreksi_kecil.append(i)
```
Sifat: KOREKSI LABEL, seperti Aturan 2/4. Deterministik, nol risiko buang.
Terukur: Wulandari-PDF 51 koreksi · Wulandari-DOCX 6 koreksi · **ASIH 0 (tidak merusak)**.
⚠️ PENTING: blok `sistematika` DILEWATI — kalau tidak, D1 dan Aturan 5 bisa bentrok.
⚠️ URUTAN WAJIB: D1 (`_tandai_sistematika`) dijalankan **SEBELUM** Aturan 5,
karena Aturan 5 butuh `sistematika` sebagai pengecualian. (Bug terukur lalu diperbaiki.)

### ATURAN 6 — baris NOMOR HALAMAN murni ⇒ BUANG (di `dibuang()`)
```
if re.match(r'^\s*\d{1,4}\s*$', s):
    return True
```
Baris angka-murni ("14","30","65") tidak pernah judul — nol risiko.
Terukur: Wulandari-PDF buang 12→106 (+94 = persis 94 nomor halaman); BAB palsu hilang.

### KOREKSI CARA BACA (pelajaran penting)
`r['label']` **HANYA berisi KANDIDAT**. Baris `"BAB I"` polos **TIDAK PERNAH jadi
kandidat** — disedot ke `gabung` di `susun()` (baris 193-207). ⇒ **Wulan 2× salah baca**
menyimpulkan "BAB hilang / BAB=10" padahal:
```
BAB ASLI = len(r['gabung']) + jumlah label 'bab' YANG BUKAN sistematika
```
Hasil benar: **ASIH 5 · Wulandari-PDF 5 · Wulandari-DOCX 5** ✅

### ✅ URUTAN ATURAN FINAL di `petakan()`
```
1. label mentah dari Jev
2. goyang (beda pendapat ⇒ 'biasa')                 [poin 4/A]
3. ATURAN 2  : subbab >300 kar → paragraf
4. ATURAN 4  : header SPSS → 'biasa'
5. D1        : _tandai_sistematika()                ← HARUS sebelum Aturan 5
6. ATURAN 5  : diawali huruf kecil → 'biasa' (kecuali sistematika)
```

### 📌 PRIORITAS BERIKUT (Bos: urut dampak)
1. **Perbaiki `_teks_dari_berkas` (HULU, dampak terbesar)** — gabung fragmen baris
   pendek jadi baris logis + buang nomor halaman/running head **sebelum** pipeline.
   "Selama makanan mentah, Jev tidak bisa dimasak benar."

### 🚨 KOREKSI BESAR (09 Okt, 02:45) — HULU SUDAH BENAR; MASALAHNYA MUTU FILE
Bos menuduh ekstraktor gagal (259 `<w:tab`). Setelah diaudit: **ekstraktor kita
SUDAH BENAR** (`_teks_dari_docx` pakai `ET.parse`; `pypdfium2` untuk PDF).
Yang salah = **Wulan menyalin naskah ke DB pakai SKRIP HOST-nya sendiri**
(`/tmp/skw*.txt`), bukan lewat `app.ai._teks_dari_berkas`.

Bukti: jalur resmi → `<w:tab = 0` · PDF `pypdfium2` → "BAB I/II/III/VI" BERDIRI
SENDIRI 4/4. ⇒ **fid 112 & 113 = file buatan Wulan (salah) · 114 & 115 = jalur resmi (benar).**

⇒ **ATURAN BARU (wajib):** uji naskah HARUS lewat `app.ai._teks_dari_berkas`.
JANGAN skrip sendiri di host. Pagar sebelum lapor: `grep -c '<w:tab'` WAJIB 0.
⇒ **TIDAK perlu tambah PyMuPDF** (`fitz`): `pypdfium2` sudah ada & sudah benar.

Sisa masalah NYATA = **mutu file user**, bukan kode kita:
· PDF ber-tabel → `pypdfium2` pecah jadi baris 1 huruf (batas alat, bukan bug)
· DOCX hasil `pdf2docx` (konverter LUAR) → "13 BAB I PENDAHULUAN" (nempel)
Detail lengkap → `TEMUAN_EKSTRAKSI_PDF_TABEL_09OKT2026.md`.

## AGENDA BERIKUT (roadmap, BUKAN malam ini)
- Lapis 2: `profil/kampus-*.yaml` — TUNGGU ≥2 kampus terukur (jangan rancang dulu).
- Regression corpus Asih — SUDAH JADI (`BASELINE_PETA3.json` + `_banding_baseline.py`).
- Uji Tesis 78 · Disertasi 103 · naskah kualitatif (Wulandari, fid=112).
- Simpan peta ke `section_state` + kolom mulai/akhir (bug `mulai`=0).
- Sambung fitur Kolaborasi.

## 🎓 PELAJARAN PROFILER POLA (09 Okt 2026)

1. **ANGKA STABIL vs GOYANG — pilih sumber yang STABIL.**
   BAB dari `gabung` (kode murni) = STABIL (5/4/5 antar-run).
   subbab dari label Jev = GOYANG (ASIH 130–138 antar-panggilan).
   ⇒ Kalau butuh angka yang tak boleh berubah, ambil dari KODE, bukan label Jev.

2. **ANGKA WAJIB DILABELI RUN-NYA.** (pelajaran fid=112 diperluas)
   Setiap angka di laporan harus menyebut "run ke berapa" — karena label Jev
   bisa goyang 3% terukur. Tanpa itu, laporan menipu pembaca masa depan.

3. **REGEX TIDAK BISA MEMISAHKAN JUDUL vs KALIMAT AKADEMIK.** (2× gagal terukur)
   Panjang (60 kar) → 12 salah tuduh · Jumlah kata (≥6) → 29 salah tuduh.
   Judul & kalimat akademik sama-sama panjang & sama-sama berisi kata biasa.
   ⇒ Sisa HANYA 2 sinyal pasti: `awal-sitasi` '(Nama, thn)' & `butir-bertanya` '1. …?'.
   ⇒ Kelas "kalimat-dianggap-judul" = TUGAS JEV (kode sediakan fakta → Jev menimbang),
     BUKAN regex. JANGAN coba regex lagi.

4. **PRESISI > RECALL untuk HAKIM.** Hakim = reviewer, bukan pemburu.
   Lebih baik DIAM daripada menuduh judul SAH (rusak kepercayaan).
   Akibat yang diakui: L000149 'kalimat-dianggap-judul' tidak lagi tertangkap.

5. **CEK "TITIK AKHIR" & "AMBANG PANJANG" TIDAK BERGUNA di naskah nyata:**
   100% baris tak berakhir titik (baris ≠ kalimat); p50 Wulandari = 1 kar (PDF hancur).

6. **PROFILER = PEMBACA, BUKAN PENEBAK.** `nomor_terakhir={}` di ASIH & DISERTASI
   = jawaban BENAR (memang tak bernomor bertingkat), bukan bug.

## 🚨 PELAJARAN U4b — ANGKA DI ATAS DEFINISI GOYANG (09 Okt, Bos menegur)

**KESALAHAN WULAN:** menulis *"18 baris MEMANG JUDUL ASLI"* padahal **7 di
antaranya anotasinya sendiri bilang BUKAN judul** (pecahan tabel · butir daftar).
⇒ **Persis dosa kunci lama:** angka yang **terlihat pasti** padahal **definisinya
goyang**. Bos: *"itu justru mengulangi dosa kunci lama."*

**KOREKSI:** 18 dipisah **dua kelompok jujur** —
(a) **7 KUNCI BENAR** (fragmen/butir ⇒ kunci `palsu` BENAR, Jev yang salah) ·
(b) **11 KUNCI SALAH** (judul asli dikunci palsu) · **+1 batas KABUR** (`L008480`,
ditandai jujur, tidak dipaksa masuk kotak).

**ATURAN BARU (diri sendiri):**
```
SEBELUM menulis "N baris salah/benar", BACA ULANG anotasi TIAP baris.
JANGAN biarkan satu label panjang menelan fakta yang anotasinya bilang beda.
Kalau ada batas kabur → TANDAI, JANGAN dipaksa masuk kotak.
```

**KONSEKUENSI YANG DIPATUHI:** **X DITANGGUHKAN** (jangan kutip "51 palsu (68%)");
X baru dihitung **setelah kunci dibangun ulang dari run resmi + verifikasi
manusia**. Recall `8/51` ditandai **angka sementara** (penyebutnya cacat).

**YANG MENYELAMATKAN:** karena `p` **bukan input keputusan** (§7c — ambang
dibubarkan), **cacat kunci TIDAK merusak produksi**. Keputusan "bubarkan ambang"
membuat fondasi **tahan terhadap kunci yang cacat** — dan itu bukti arsitekturnya benar.

**BUKTI ARSITEKTUR:** `p` mengukur **"Jev ragu"**, bukan "baris palsu". Judul asli
`'2.1.1 Pengertian Analisis SWOT'` bisa `p=0,20`. ⇒ Ambang apa pun yang jadi
**saklar** = salah sasaran. **Ini bukan masalah kalibrasi, ini salah alat ukur.**

---

## ⚠️ JEBAKAN SAAT VERIFIKASI (09 Okt, makan waktu)
- **Tes Jev pakai pesan bebas ('hi') ⇒ 9router MENGUNCI akun 30 detik.**
  Jev = PIPA JSON: `{"state": "...", "questions": {...}}`. Tes salah = kunci akun,
  panggilan SAH berikutnya ikut gagal ⇒ TERLIHAT seperti gangguan luar. Hati-hati!
- **503 BISA DARI 3 SEBAB BERBEDA:** (a) gangguan sesaat, (b) kunci habis limit,
  (c) 9router mengunci akun karena tes salah. Cek LOG 9router, jangan tebak.
- **`judul_curiga` tanda tangan salah** (`for i, t in subbabs`) ⇒ ValueError
  saat item 3-kolom. Fungsi yang TIDAK DIPANGGIL dari mana pun = uji buta.
