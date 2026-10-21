<!-- 📌 SOT: Ringkasan 30 detik buku umum. Status HITUNG dari kode (sot.py). Sumber resmi tetap SOT.md + FLAG_LANJUT_DISINI.md -->
# 🧭 FLAG BUKU UMUM — 19 OKT 2026

> **Bos bilang "lanjut buku umum" / "buka flag buku"** ⇒ BACA BERKAS INI DULU,
> lalu `FLAG_LANJUT_DISINI.md` (blok 19 Okt di paling atas).
> Berkas ini = ringkasan 30 detik. Yang resmi tetap SOT + FLAG utama.

---

## ✅ KEADAAN KINI (19 Okt 2026, sudah LIVE)

Image jalan : **`eduai-app:20261019_235826-sot`** (deploy 23:58 UTC — ilustrasi tak dibuang)
Titik mundur: `eduai-app:cadangan-pra-sot` · backup DB `_arsip/pra-sot/20261019_235826-sot`
Produksi    : https://eduai.bikinaja.id — `/health` **200** — SEHAT
Mesin siap  : `(True, '')` — terverifikasi dari DALAM container
Editor      : gerbang OnlyOffice **LULUS** (`/oo/aset` 200, kunci cocok, api.js 200)
Buku latar  : ✅ **LIVE** — `/buku/susun` menitipkan pekerjaan, halaman
              `/buku/proses/{kode}` memantau. Dokumen:
              `DOKUMEN_BUKU_LATAR_19OKT2026.md`

### Alur yang sudah tersambung dan bisa dipakai

```
/buku
  └─ kartu "Buku Umum": pilih BIDANG + UNTUK SIAPA
       └─ POST /buku/mulai      → tentukan gaya (umum | anak | pendidikan)
            └─ /buku/siapkan    → isi JUDUL BUKU, lihat wajah buku
                 └─ POST /buku/susun   → kuota dipotong, bab ditulis
                      └─ /buku/selesai → jumlah bab, kata, folder hasil
```

Kartu lain (Buku Ajar, Monograf, Book Chapter, Referensi) **TIDAK disentuh**.

### Pemetaan pilihan → gaya

| Pilihan user | `kode_jenis` | Gaya gambar | Sapaan |
|---|---|---|---|
| Profesional | `umum` | metafora navy-terracotta | "Anda" |
| Anak-anak | `anak` | clay 3D ceria | "kamu", kalimat pendek, ada pertanyaan |
| Pelajar | `pendidikan` | clay 3D kalem | "kamu", berurutan, istilah dijelaskan |

---

## 🔴 KERJAAN BERIKUTNYA (urut prioritas)

### 0. ✅ SELESAI 19 Okt — ID BUKU + PORSI ALAT + ASSEMBLY DOCX + TABEL `files`

**SEMUA GERBANG LULUS, BELUM DEPLOY.** Detail:
`DOKUMEN_ID_DOKUMEN_PORSI_ALAT_19OKT2026.md` ·
`DOKUMEN_ASSEMBLY_BUKU_ONLYOFFICE_19OKT2026.md`

| Gerbang | Hasil | Bergigi |
|---|---|---|
| `_gerbang_porsi_alat.py` | 138/0 | 3/3 |
| `_uji_id_buku_ke_alat.py` | 55/0 | 3/3 |
| `_gerbang_assembly_buku.py` (host) | 30/0 | 3/3 |
| `_uji_daftar_berkas_buku.py` | 28/0 | 3/3 |
| `_gerbang_salinan_mesin.py` | 25/0 | 1/1 |
| `scripts/periksa_kode.sh` | **LULUS** | — |
| `sot.py --periksa` | **0 masalah** | — |

**4 AKAR RUSAK YANG DITAMBAL (terukur, bukan dugaan):**
1. Assembly ditulis untuk SATU buku — judul/penulis/folder/nama berkas
   HARDCODE "EKONOMI DIGITAL" ⇒ buku user lain keluar identitas buku orang lain.
2. `add_kata_pengantar()` + `add_bio()` MENULIS MATI ⇒ buku "Petualangan di
   Laut" keluar pengantar & biografi ekonomi digital / "Syahrul Alim".
   **Keduanya ditemukan GERBANG, bukan dari membaca kode.**
3. `python-docx` **TIDAK ADA** di image (EduAi selalu WeasyPrint/PDF) ⇒ rakit
   mustahil di produksi. Ditambah `python-docx==1.2.0`.
4. Berkas mesin buku tidak ikut `COPY` Dockerfile ⇒ rute jalan, rakit gagal.

**YANG DIPASANG:** `siapkan()`/`rakit()` per buku (global dipulihkan di
`finally`) · assembly disambung ke `/buku/susun` · `.docx` didaftarkan ke tabel
`files` (pola SAMA `dokumen_baru.py:87`) · halaman selesai menampilkan dokumen
+ tombol **Edit dokumen** → `/edit/{fid}` (dengan cek pemilik & bukan sampah) ·
`_gerbang_salinan_mesin.py` (host ↔ proyek wajib identik) · image uji
`eduai-app:uji-assembly-19okt` terbangun & diuji.

**JEBAKAN BARU (semua menggigit Wulan):** ① nama fungsi di KOMENTAR = gerbang
PALSU. ② uji "judul 400 karakter harus gagal" PALSU karena kode MEMOTONG judul.
③ SQLite TIDAK menegakkan panjang kolom (nama 400 kar masuk tanpa galat).
④ uji cek "fungsi ada" bukan "dipanggil" ⇒ pendaftaran dimatikan tidak
tertangkap. ⑤ berkas uji tertinggal di `/tmp` ⇒ gerbang ANTI-BIKIN-BARU
MENOLAK deploy.

**BELUM:** deploy · uji buku 6 bab nyata · tekan `/edit/{fid}` ke OnlyOffice
hidup (baru diuji syarat rutenya) · `render_html_to_png()` masih stub ·
**percepatan paralel + orkestrator belum disentuh**.

### 1. ✅ SELESAI 19 Okt — BUKU DIKERJAKAN DI LATAR (LIVE)
### 1b. ✅ SELESAI 19 Okt — RINGKASAN BAB TANPA PANGGILAN AI (LIVE)

**Akar:** `generate_bab` memanggil AI KELIMA hanya untuk meringkas ULANG seluruh
bab dari teks mentah, padahal tiap sub-bab SUDAH punya ringkasan sendiri.
Akibat: (a) ±8 detik terbuang per bab; (b) **DUA ringkasan bab berbeda beredar**
— ringkasan sub-bab dipakai penulis (`rolling`), ringkasan bab dipakai pembuat
brief gambar ⇒ ilustrasi bisa bercerita lain dari alur bab.

**Perbaikan:** ringkasan bab DISUSUN dari `ringkasan_subs` (gabungan ringkasan
sub-bab) ⇒ **0 panggilan AI**, dan pasti konsisten. Kalau ringkasan sub-bab
kosong → turun ke cadangan 1 panggilan AI (tidak mengarang).

**Gerbang:** `_gerbang_ringkasan_bab.py` **14/0**, bergigi 2/2 (kembalikan
perilaku lama → 1 GAGAL; hapus pengumpulan → 2 GAGAL). Terdaftar di
`scripts/periksa_kode.sh` dan TERBUKTI ikut jalan (bukan gerbang hiasan).

**⚠️ JUJUR SOAL MANFAAT:** hemat terukur **±1 menit per buku (±2,5%)**, BUKAN
30%. Nilai sesungguhnya = **mutu** (satu ringkasan, tidak bisa bertentangan),
bukan kecepatan. Angular ukur: `_ukur_waktu_sub_bab.py` (99% waktu di AI;
Architect 42,8 dtk = 39% — tahap terberat).

### 1. ✅ SELESAI 19 Okt — BUKU DIKERJAKAN DI LATAR (LIVE)
`/buku/susun` **tidak menunggu** lagi: pekerjaan dititipkan ke `app/proses.py`
(jalur yang SUDAH dipakai revisi), user dialihkan ke `/buku/proses/{kode}`
yang memantau TAHAP NYATA. **Boleh tutup tab.**
Gerbang `_gerbang_buku_latar.py` **25/0**, bergigi 3 suntikan, sudah masuk
`periksa_kode.sh`. Dokumen: `DOKUMEN_BUKU_LATAR_19OKT2026.md`.
**Kecepatan BELUM berubah** (6 bab masih ±36 menit) — yang berubah: user tidak
perlu menunggu di layar.

### 1c. ✅ SELESAI 19 Okt — LAPIS 3: BAB BERSAMAAN (LIVE)

**TERUKUR: 2,00× — bukan janji.** `_ukur_percepatan_bab.py` (AI palsu, jeda
tetap): berurutan 8,45 dtk vs bersamaan 4,22 dtk untuk 2 bab.

**Cara kerja (yang BENAR, setelah 3× salah):**
`buku_umum_pipeline` memakai `OUT_DIR`/`VISUAL_DIR`/`CKPT_FILE` GLOBAL di 20
titik. Percobaan 1 (kunci global) **TERBUKTI NOL percepatan** (`aktif maks = 1`)
— kunci menahan seluruh bab. Percobaan 2 (subclass `str` + `__fspath__`)
**GAGAL**: `os.path.join()` TIDAK memanggil `__fspath__` untuk turunan `str`.

**Yang akhirnya benar:** `_FOLDER_UTAS` = peta `utas → folder bab`, plus fungsi
`folder_bab()`, `lepas_folder()`, `folder_ini()`, `visual_ini()`. Tujuh titik
`os.path.join(OUT_DIR/VISUAL_DIR, ...)` diganti jadi sadar-utas. **Nol kunci**
⇒ bab benar-benar bersamaan.

**Gerbang:** `_gerbang_lapis3_bab_bersamaan.py` **18/0**, bergigi 2/2 (buang
`folder_bab` → 5 GAGAL; `_BATAS_BAB=1` → 2 GAGAL). Terdaftar di
`scripts/periksa_kode.sh`, TERBUKTI ikut jalan. Batas 2 bab di
`penyusun_buku.py:41`.

**⚠️ RISIKO MASIH TERBUKA:** `prev_summary` kini diganti jangkar dari outline
(`outline[n]['subs']` — kunci `points` TIDAK ADA, lihat `outline_buku.py:39`).
**Isi antarbab bisa berulang.** Pemeriksa mutu isi (Lapis 3c) **BELUM dibuat**.
Belum diuji dengan buku nyata.

### 1d. ✅ SELESAI 19 Okt — LAPIS 3c: PENJAGA MUTU ISI (LIVE)

**Kenapa:** sejak bab dikerjakan bersamaan, bab 2 tidak lagi menerima ringkasan
bab 1 ⇒ isi antarbab **bisa berulang**. Tanpa penjaga, buku berulang dilaporkan
"selesai" (kerusakan SUNYI).

**Modul:** `mutu_isi_buku.py` — **NOL panggilan AI** (Rp 0, cepat):
1. kemiripan kosakata antarbab ≥ **25%** → MASALAH
2. **kalimat disalin** (kemiripan ≥80% per kalimat) → MASALAH
3. bab < 300 kata → MASALAH
4. sub-bab tidak dibahas (<60% kata judul muncul) → CURIGA
5. sitasi < 2 per bab → CURIGA

**Tersambung:** `penyusun_buku.susun_buku()` memanggilnya setelah semua bab jadi
dan mengembalikan `mutu_lolos` / `mutu_masalah` / `mutu_curiga`.
`Dockerfile` menyalin `mutu_isi_buku.py` (tanpa ini image gagal impor).

**Gerbang:** `_gerbang_mutu_isi_buku.py` **10/0**, bergigi 2/2 (penjaga selalu
bilang lolos → 6 GAGAL; sambungan ke `susun_buku` diputus → 1 GAGAL).
Terbukti bisa diimpor DARI DALAM container produksi.

**⚠️ BELUM:** `mutu_lolos=False` saat ini **hanya dilaporkan**, belum memicu
perbaikan-otomatis bab (rancangan 3c: perbaiki 1× lalu lapor jujur). Juga belum
diuji dengan buku nyata.

### 1e. ✅ SELESAI 19 Okt — AMBANG MUTU DIKALIBRASI BUKU NYATA (LIVE)

**Uji nyata (AI 9router sungguhan, DB & folder sementara, token 0):**
judul "Awan dan Hujan", 2 bab, **441,7 dtk (7,4 menit)**, **7.531 kata**,
**37 sitasi**, 2 folder bab dibuat **bersamaan** ✅.

**TEMUAN — ambang lama SALAH, buku sehat dituduh berulang:**
kemiripan kosakata mentah bab1 vs bab2 = **31,6%** (ambang lama 25%) padahal
**0 kalimat disalin** dan isinya beda total (bab 1 = pembentukan awan, bab 2 =
proses hujan). Penyebabnya kata wajar: `adalah`, `akan`, `anda`, `angin`,
`atmosfer`. ⇒ **Jaccard mentah tidak layak jadi ambang.**

**PERBAIKAN (terkalibrasi data nyata):**
- `_kata()`: minimal **5 huruf** + buang **120 kata wajar** (`KATA_UMUM`)
- `AMBANG_MIRIP` 0,25 → **0,60** (jaring pengaman kasar saja)
- `AMBANG_TUMPANG` = **0,15** (porsi kalimat berulang)
- Penentu utama = **kalimat disalin**, termasuk **1 kalimat utuh (≥10 kata)**

Setelah kalibrasi: buku nyata **LOLOS** (kemiripan 27,1%, 0 kalimat disalin).

**Gerbang:** `_gerbang_mutu_isi_buku.py` **10/0**, bergigi 2/2 — termasuk suntik
"matikan deteksi kalimat pendek" → **1 GAGAL**.

**⚠️ MASIH TERBUKA:** `mutu_lolos=False` hanya DILAPORKAN, belum memicu
perbaikan-otomatis bab. Gambar ilustrasi **dilewati** karena brief ditolak QC
("tidak ada BENDA metafora") — perlu diperiksa terpisah.

### 1f. ✅ SELESAI 19 Okt — ILUSTRASI TIDAK LAGI DIBUANG (LIVE)

**Cacat terukur (buku nyata 2 bab):** bab 1 **dilewati tanpa ilustrasi**
("brief ditolak QC: tidak ada HUBUNGAN/GAGASAN"), bab 2 berhasil. Satu bab
tanpa gambar = buku terasa cacat, padahal brief yang ditolak biasanya cuma
kurang satu kata kunci.

**AKAR:** `brief_visual()` menyerah setelah 3 percobaan dan mengembalikan
brief **KOSONG** ⇒ jalur gambar melewati bab itu.

**PERBAIKAN (`brief_visual.py`):**
- Simpan **brief TERBAIK** (paling sedikit alasan tolak) selama 3 percobaan
- Semua percobaan habis → **PAKAI brief cadangan** (jangan buang ilustrasi)
- Penanda jujur `cadangan_dipakai` + `generik=True` (tidak menyembunyikan
  bahwa brief itu tidak lolos QC)
- **PAGAR:** brief yang melanggar **budaya** atau <12 kata **TETAP DIBUANG**

**BUKTI BUKU NYATA (AI sungguhan, sesudah perbaikan):**
**2 bab → 2/2 BERGAMBAR** (3 varian @1,5 MB per bab), 428,2 dtk, 6.368 kata,
23 sitasi, `mutu_lolos: True`.

**TEMUAN SAMPINGAN (cacat lebih serius, ikut ditutup):**
`larangan_budaya.py` SELURUHNYA Bahasa Inggris ⇒ brief Indonesia
"susunan botol alkohol dan gelas anggur" **LOLOS** penjagaan. Ditambah 60+
kata + 10 frasa Indonesia, dan `brief_visual` kini pakai QC **dua bahasa**
(`bahasa_brief()`, akar kata supaya "mengalir/aliran/dialirkan" ikut cocok).

**Gerbang:** `_gerbang_qc_brief_dua_bahasa.py` **16/0** (bergigi 3/3) ·
`_gerbang_ilustrasi_tak_dibuang.py` **12/0** (bergigi 2/2 — cadangan dibuang
→ 5 GAGAL; pagar budaya jebol → 3 GAGAL). Keduanya **terdaftar dan terbukti
jalan** di `periksa_kode.sh`.

### 2. PARALEL 4 SUB-BAB + ORKESTRATOR — belum disentuh (nol baris)
Ini yang memotong 36 menit → ±10 menit. Bos pilih kerjakan SETELAH latar.
Perkiraan 4 lapis: (1) pisahkan state global per-bab, (2) penulis paralel,
(3) pemeriksa mutu + orkestrator, (4) sambung ke jalur latar yang baru.
⚠️ Risiko: `OUT_DIR`/`VISUAL_DIR`/`CKPT_FILE` global = tabrakan antar-bab.

### 2b. `/buku/susun` masih MENUNGGU 36 MENIT — ✅ SUDAH DIPERBAIKI (lihat 1)

### 2. Assembly DOCX
Hasil sekarang berkas bab terpisah. Belum satu `.docx` (daftar isi, nomor
halaman, daftar pustaka). Mesin `buku_umum_assembly.py` sudah ada — tinggal
disambungkan. ⚠️ `render_html_to_png()` di sana **masih stub**.

### 3. Bidang → isi tulisan
Sekarang bidang hanya konteks outline. Belum mengubah gaya/kedalaman.

### 4. Infografis berlabel otomatis di jalur `/buku/susun`
Ilustrasi sudah jalan (3 varian). Label infografis belum dipasang di jalur ini.

### 5. Penjaga sitasi pada tulisan asli
Belum pernah menyala alami; baru terbukti lewat uji paksa.

---

## ⚠️ JEBAKAN — WAJIB INGAT (semua sudah menggigit)

| # | Jebakan | Akibat terukur | Obat |
|---|---|---|---|
| 1 | Prompt baru TIDAK menerima `jenis` | Aturan dewasa bocor ke buku anak: 4× "Anda", 0 pertanyaan | Teruskan `jenis` ke SEMUA prompt, termasuk `editor_prompt` |
| 2 | `requests` tidak ada di image | `siap()` False ⇒ tombol mati | Pembungkus `_RequestsShim` di atas `httpx`. JANGAN tambah dependency |
| 3 | `count_citations` pola lama | 3 sitasi dilaporkan 1 | Hitung tiap isi kurung bertahun 4 angka |
| 4 | Modul mesin tidak di-COPY ke Dockerfile | Rute ada, tombol gagal saat ditekan | Gerbang bagian K menolak deploy |
| 5 | Ikon dikarang (`briefcase`, `smile`, `clock`, `pen-line`, `plus`) | Ikon kosong | Selalu `grep id="ik-<nama>"` di `app/static/ikon/lucide.svg` |
| 6 | Potret template via Jinja + autoescape | `ikon()` SVG jadi TEKS, vision bilang "ikon rusak" | Bungkus `markupsafe.Markup`; ganti `/static/` → `file://` |
| 7 | `MASTER_OUTLINE_SEMENTARA` dipakai saat `outline` kosong | Topik "Siklus Hujan" keluar isi Ekonomi Digital (11× ekonomi, 17× digital) | Selalu oper `OB.ke_teks(outline)` |
| 8 | Global pipeline tidak dipulihkan | Buku berikutnya memakai outline buku sebelumnya | `P.architect_prompt = _architect_asli` di `finally` |
| 9 | Folder hasil berbenturan (`folder_buku` = detik+user) | Uji "berkas tidak tersimpan" lulus PALSU | Kosongkan folder per uji |
| 10 | Gerbang cuma cek NAMA fungsi | Kuota tidak dipotong tetap 62/0 | Cek `info = kuota.potong_banyak(` — hasilnya DIPAKAI |

---

## 🧪 GERBANG — jalankan sebelum menyentuh apa pun

```bash
cd /opt/data
.venv/bin/python gerbang_penyusunan_naskah.py    # 82/0  ← paling lengkap
.venv/bin/python uji_kuota_penyusunan.py         # 17/0  (kuota palsu, Rp 0)
.venv/bin/python uji_penjaga_sitasi.py           # 19/0
.venv/bin/python gerbang_menu_buku_umum.py       # 30/0
.venv/bin/python gerbang_tone_jenis.py           # 27/0
.venv/bin/python gerbang_jenis_buku.py           # 32/0
.venv/bin/python gerbang_buku_anak.py            # 26/0
.venv/bin/python gerbang_ilustrasi_2tahap.py     # 39/0
.venv/bin/python gerbang_larangan_budaya_semua_jalur.py  # 16/0
.venv/bin/python _uji_buku_siapkan.py            # 43/0
.venv/bin/python _uji_rute_buku.py               # 17/0
```

**Deploy WAJIB:**
```bash
cd /opt/data/services/eduai-publishing
bash scripts/periksa_kode.sh     # GAGAL = JANGAN DEPLOY
bash jalankan.sh                 # BUKAN docker cp app/...
```

**Mundur:**
```bash
docker tag eduai-app:cadangan-pra-buku-susun eduai-app:20261019_035552-sot
```

---

## 📁 BERKAS PENTING

**Di `/opt/data/` (sumber mesin):**
`outline_buku.py` · `penyusun_buku.py` · `buku_umum_pipeline.py` ·
`jenis_buku.py` · `tone_menulis.py` · `brief_visual.py` ·
`label_infografis.py` · `larangan_budaya.py` · `verifikasi_sitasi.py`

**Di `services/eduai-publishing/`:**
`app/buku.py` · `app/penyusunan_buku.py` · `app/main.py` (4 rute buku) ·
`app/templates/buku.html` · `buku_siapkan.html` · `buku_selesai.html` ·
`Dockerfile` (COPY 9 modul mesin)

**Skill:** `penelitian-ilmiah/buku-umum` (bagian "Penyusunan naskah") —
salinan skrip di `skills/penelitian-ilmiah/buku-umum/scripts/`

**Dokumen:**
`RENCANA_SAMBUNG_PENYUSUNAN_18OKT2026.md` ·
`TEMUAN_SYSTEM_PROMPT_VS_QC_18OKT2026.md`

---

## 🎯 BATAS JUJUR

- **Tone anak TERBUKTI bekerja** (2 bab nyata): 39× "kamu", 0× "Anda",
  33 pertanyaan, 6,5 kata/kalimat.
- **Sitasi terverifikasi** 3–5 per bab dari OpenAlex/Crossref nyata.
- **Kuota aman**: dipotong di depan; kalau gagal teknis dikembalikan utuh
  (diuji 17/0 dengan kuota palsu — tidak menyentuh saldo siapa pun).
- **BELUM**: pekerjaan latar, DOCX utuh, bidang→isi, infografis berlabel.
- **Belum pernah satu buku penuh 6 bab dijalankan** — baru per bab.
