# 📌 CATATAN KERJA — FITUR KONVERSI JURNAL (EduAi)

**Dibuat:** 08 Okt 2026 · **Guna:** penanda sesi (A) + bukti kerja (B).
**Aturan:** sesi BARU → BACA BERKAS INI DULU, jangan percaya ringkasan/ingatan.

---

## 🎯 SEDANG DIKERJAKAN

**Fitur Konversi ke Artikel Jurnal** — pintu uang (AddOn Rp100.000 = 1× konversi).

---

## ✅ SUDAH SELESAI & TERUJI

| # | Bagian | Bukti | Berkas |
|---|---|---|---|
| 1 | Mesin AI (`jalankan_konversi`) | **42 LULUS / 0** | `_sambung_konversi_uji.py` |
| 2 | Penulis `.docx` (templat+ZIP) | **36 LULUS / 0** | `_uji_docx_artikel.py` |
| 3 | Rute `POST /artikel/{fid}/konversi` | **10 LULUS / 0** | `_uji_pagar_konversi.py` |
| 4 | **Uji NYATA #1** | HTTP 200 · **55,9 dtk** · 52.926 kar artikel · 56 pustaka | naskah Asih fid=81 |
| 5 | Jev periksa **sebelum** (mata + 18 poin mutu) | ✅ lihat faktur 238 | `konversi.py` |
| 6 | Bahan Jev **v2** (kenali bagian artikel) | skor **0,62 → 0,72** | `_uji_bahan_mutu.py` |
| 7 | Bahan Jev **v3** (3 ujung + jatah menyesuaikan) | skor **0,72 → 0,92** · kurang 0 | `_periksa_fact249.py` |
| 8 | **Jev periksa HASIL** (`periksa_hasil_jev`) | **Uji NYATA #2**: HTTP 200 · 43,3 dtk · skor 0,90 | `main.py:1143` |
| 9 | **Tombol "Mulai Konversi"** | ✅ TERBUKTI MUNCUL (`_uji_tombol_muncul.py`) | `artikel_konversi.html:199` |
| 10 | Pagar kuota (tombol mati bila habis) | ✅ terbukti | `_uji_tombol_konversi.py` |

**Bahan (catatan lawas JANGAN dipakai):**
- `_uji_*.py`, `_sambung_*.py`, `_periksa_*.py` — skrip uji (JALAN DI CONTAINER)

---

## ❌ BELUM SELESAI

| # | Yang belum | Catatan |
|---|---|---|
| 1 | **BELUM DEPLOY** | Masih `docker cp`. Belum masuk image. Container dibuat ulang = **hilang** |
| 2 | Halaman hasil + tombol revisi per-item | Setelah konversi, user belum punya halaman hasil |
| 3 | Gerbang konversi resmi | Belum ada `_gerbang_*.py` untuk konversi |
| 4 | Rapikan skrip uji | Banyak `_*.py` di root proyek & container |
| 5 | **Peta bab pakai Jev (pola resmi)** | `_posisi_dari_jev` SALAH RANCANG — lihat bagian 🔴 di bawah |

---

## 🔴 SEDANG DIPERBAIKI — PETA BAB PAKAI JEV (08 Okt 2026)

### Masalah yang memicu

Jev periksa naskah Asih bilang **kurang**: novelty 0,17 · gap 0,38 · hook 0,30 ·
limitasi 0,23 · rekomendasi 0,19.
**Padahal SEMUA ADA** — terbukti: `celah` (baris 396), judul tabel **"Gap research"**,
`keterbatasan` (4 tempat), `rekomendasi`, `fenomena` (baris 380).

⇒ **Bukan Jev salah — BAHAN yang dikirim cacat.** `_bahan_mutu()` salah memotong
naskah SKRIPSI (jalur yang dipakai masih jalur naskah mentah buta:
awal + `[5000:9000]` + `[-5000:]` → mendarat di LAMPIRAN).

### Akar sebenarnya: bentuk naskah Asih

Naskah Asih `fid=81` (159.909 kar, 2.224 baris) punya bentuk **tak biasa**:

1. **Daftar isi TIDAK pakai `....`** — bentuknya `'BAB I PENDAHULUAN1'`
   (nomor halaman **NEMPEL**), baris 138–234.
2. **Ada blok "SISTEMATIKA PENULISAN"** (baris ~541–559): memuat judul **SEMUA bab
   berurutan rapat** (BAB I…V), masing-masing hanya 1 paragraf `"Bab ini berisi…"`
   ⇒ **MENUTUPI bab asli** yang jaraknya berjauhan.
3. Bab **ASLI** (terukur, urutan benar):

| Bab | Baris | Panjang |
|---|---|---|
| BAB I PENDAHULUAN | 350–545 | 22.035 kar |
| BAB II TINJAUAN PUSTAKA | 545–735 | 26.874 kar |
| BAB III METODE PENELITIAN | 735–957 | 23.554 kar |
| BAB IV HASIL DAN PEMBAHASAN | 957–1183 | 17.112 kar |
| BAB V PENUTUP | 1183–akhir (2224) | 57.713 kar |

### Kesalahan Wulan (JANGAN DIULANG)

Wulan **5× menambal regex** di `_cari_bab_skripsi()` (aturan "buang penanda rapat",
"batas 12%", "angka di ujung", dst). **Bos menegur:**
> *"Kenapa tidak pakai jev saja untuk melihat, kenapa mesin menebak?"*

⇒ **MELANGGAR PRINSIP INDUK: "Jev selalu terdepan sebelum mesin dan Ai."**
Mesin **tidak boleh menebak bentuk naskah** — Jev yang mengenali.

Dan Wulan **salah tanya Jev 2×** (melanggar dokumentasi resmi):
- ❌ tanya **"berapa bab?"** → kelemahan resmi **#2 Counting** (*Jev tidak menghitung*)
  ⇒ Jev jawab "1", lalu "0", padahal 5 bab.
- ❌ tanya **"sebutkan judul bab"** bertipe `noul` → kelemahan **#9 Generation**
  (Jev **bukan** penulis teks) + `noul` = ya/tidak, bukan teks.

### ✅ CARA YANG BENAR (dari dokumentasi RESMI)

Sumber: skill `typesafe-jev` → `references/cookbook-structure-recovery.md`.
Inti kutipan resmi: *"the model never generates text: it answers **narrow questions**
about the document... and **code does the rendering**"* · *"Blank lines and explicit
markers are read in **code, never sent to the model**"*.

```
① KODE : pecah naskah jadi baris + beri ID  →  "L014| BAB I PENDAHULUAN"
         (penanda eksplisit & baris kosong disaring KODE dulu)
② JEV  : SATU pertanyaan `noul` SEMPIT per kandidat baris:
         "Apakah baris L014 adalah AWAL BAB AKADEMIK yang berisi
          (bukan daftar isi, bukan blok Sistematika Penulisan)?"
         criteria: true="awal bab berisi" / false="daftar isi / sistematika / bukan awal bab"
         ⇒ kirim SEMUA pertanyaan dalam 1 panggilan (nyaris gratis)
③ KODE : baris dengan noul ≥ ambang → jadi penanda bab; rakit peta
         Jev TIDAK PERNAH menyalin/menulis teks
```

**Pelajaran penting dari dokumen resmi:** pertanyaan harus **SEMPIT**. Contoh resmi —
"Are these lines the same paragraph?" SALAH (semua dijawab ya → 12 blok);
"Does this line pick up mid-sentence?" BENAR (17 blok). ⇒ pertanyaan kita harus
menyebut **fakta tersempit** yang memutuskan, bukan kategori luas.

### Sisa kerja

1. Tulis ulang `_posisi_dari_jev()` di `app/konversi.py` mengikuti pola di atas
   (sekarang MASIH salah: tanya jumlah + judul).
2. `_cari_bab_skripsi()` (regex) **JANGAN dibuang** — jadikan **cadangan** bila Jev
   mati (sudah terbukti menemukan 5 bab asli setelah aturan "buang penanda rapat").
3. Uji ulang: `_posisi_dari_jev` harus balik **5 bab** sesuai tabel di atas.
4. Uji ulang `_bahan_mutu` → Jev periksa naskah Asih → skor harus naik di atas 0,75.

### Angka terukur sesi 08 Okt (bahan naskah Asih)

| Tahap | Bahan | Skor Jev |
|---|---|---|
| Awal (jalur buta) | 25.848 kar (16%) | 18 poin · kurang 5 |
| Setelah regex `_cari_bab_skripsi` | 40.319 kar (25%) | **0,75** · kurang 3 |

**Jev 0,75 — 3 kurang + 1 ragu (INI BAHAN JUALAN BOS, 2 token/item):**
`abstrak 0,05` · `pernyataan keterbatasan 0,13` · `hook 0,29` · 🟡 `rekomendasi 0,46`.
Yang sudah bagus: pendahuluan 0,99 · metode 0,99 · kesimpulan 0,99 · gap 0,93 ·
pembanding 0,97 · implikasi 0,97.

⚠️ **CATATAN PENTING:** nilai `abstrak 0,05` mencurigakan (abstrak JELAS ADA) —
mungkin masih cacat bahan. **Uji balik dulu sebelum dijual** (pola: Jev tuduh kurang
⇒ 4× ternyata BAHAN cacat, baru 1× Jev benar).

---

## 🔑 MEKANISME REVISI (SUDAH ADA di mesin, BELUM ada pintunya)

Bos bertanya 08 Okt: *"kalau user setuju perbaiki, bayar 4 token (2 novelty + 2 gap);
atau pilih satu (gap saja) = 2 token. Apakah sudah ada mekanisme ini?"*

**JAWABAN: MESINNYA SUDAH ADA LENGKAP** (`app/konversi.py`):

| Fungsi | Baris | Guna |
|---|---|---|
| `TOKEN_PER_REVISI = 2` | :70 | 2 token per item |
| `ELEMEN_REVISI` | — | 11 elemen mutu, TERMASUK **`gap`** & **`novelty`** |
| `BAGIAN_REVISI` | — | 8 bagian artikel |
| `daftar_revisi(artikel)` | :1283 | buat daftar pilihan untuk user |
| `hitung_biaya_revisi(pilihan)` | :1303 | `{'jumlah': n, 'token': n*2, 'per_item': 2}` |
| `susun_pesan_revisi(...)` | :1315 | AI revisi HANYA item yang dipilih |

Terbukti hitung: `novelty+gap` → 4 token · `gap saja` → 2 token ✅ **PERSIS** yang Bos mau.

**YANG BELUM (pintunya):**
1. Rute `POST` revisi artikel — **grep `main.py` = KOSONG**, belum ada.
2. Halaman hasil + kotak centang per item (belum ada).
3. Sambungan **nilai Jev → daftar centang** (Jev bilang novelty 0,17 → muncul kotak).
4. Pemanggilan `kuota.potong_banyak()` dari rute revisi.

⇒ Persis pola "tombol konversi": **mesin siap, pintu belum dipasang**.

---

## 📖 CARA LANJUT (untuk sesi baru)

### 🚦 STATUS NYATA (terukur 08 Okt 2026, ~11:00)

| Hal | Nilai |
|---|---|
| Container `eduai-app` | **Up** (image `eduai-app:20261007_154044-sot`) |
| `/health` | **200** |
| `app/konversi.py` host | md5 `0a275148f6e521ce53b89b10ee662b6d` |
| `app/konversi.py` container | md5 `0a275148f6e521ce53b89b10ee662b6d` ✅ **SAMA** |
| Perubahan sesi ini | ADA DI CONTAINER saja (`docker cp`) — **belum masuk image** |
| Image terakhir | `20261007_154044-sot` (9 jam lalu) |

⚠️ **Kalau container dibuat ulang (`bash jalankan.sh`) sebelum deploy → perubahan sesi
ini HILANG.** Container dibuat ulang = kode kembali ke `20261007_154044-sot`.

### Langkah pertama sesi baru

```bash
cd /opt/data/services/eduai-publishing

# 1. Cek status
docker ps --filter name=eduai-app --format "{{.Status}} | {{.Image}}"
docker exec -w /app eduai-app python3 -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=10).status)"

# 2. CEK: apakah perubahan sesi 08 Okt masih ada di container?
docker exec eduai-app md5sum /app/app/konversi.py     # harus 0a275148f6e521ce53b89b10ee662b6d
docker exec -w /app eduai-app python3 -c "import sys; sys.path.insert(0,'/app'); from app import konversi as K; print('ada _posisi_dari_jev:', hasattr(K,'_posisi_dari_jev'))"

# 3. Uji bahan Jev naskah Asih (fid=81) — harus skor >= 0,75
docker cp _ukur_kekurangan_asih.py eduai-app:/app/
docker exec -w /app eduai-app python3 -u _ukur_kekurangan_asih.py

# 4. Uji bahan Jev ARTIKEL hasil (harus skor 0,92)
docker cp _uji_jev_artikel.py eduai-app:/app/
docker exec -w /app eduai-app python3 -u _uji_jev_artikel.py
```

---

## ⚠️ ATURAN KERAS (semua salah Wulan 08Okt26)

1. **SEBELUM bilang "belum ada / tidak ada / rusak"** → BUKA BERKAS DULU
2. **Angka WAJIB dari cetakan uji**, bukan ingatan
3. **Tiap patch → cek lint** (Wulan pernah hapus docstring 2× → SyntaxError)
4. **Ragu ⇒ BILANG RAGU**, jangan menebak yakin
5. **`docker cp` → WAJIB `docker restart`**; JANGAN `docker run -v` untuk uji kode host (mount tak nyambung)

## 🔑 NAMA BENAR (JANGAN DIKARANG)

| Barang | Nama BENAR | Wulan pernah salah tulis |
|---|---|---|
| Model konversi | `models.KonversiNaskah` (:497) | ~~`KonversiPakai`~~ |
| Sesi DB | `models.SessionLocal` | ~~`app.db.SessionLocal`~~ |
| Login endpoint API | `auth.wajib_login_api` (401) | ~~pakai `wajib_login` (303)~~ |
| Bagian judul | `'KESIMPULAN'` (huruf besar) | ~~`'Kesimpulan'`~~ |
| Kuota | `kuota.jatah_konversi()` · `potong_konversi()` | — |

---

## 🔢 ANGKA TERUKUR (jangan ukur ulang)

| Hal | Angka |
|---|---|
| Uji nyata #1 | 55,9 dtk · 52.926 kar · `cb/deepseek-v4.1-flash` |
| Uji nyata #2 | 43,3 dtk · Jev-hasil skor 0,90 · 0,57 dtk |
| Bahan Jev v3 | 40.938 kar (77% dari 52.926) · Jev 1,33 dtk |
| Skor Jev artikel | keterbatasan 0,98 · rekomendasi **0,99** · pembanding 0,98 · analisis 0,81 · state 0,77 · **TOTAL 0,92** |
| User uji | `asih.susanti@eduai.test` id=8 · naskah fid=81 · jatah_paket 2 |

---

## 🆕 16 OKT 2026 — JEMBATAN + TIKET LOLOS (LIVE)

**SOT:** `SOT_KONVERSI_JURNAL.md` **Bagian Q** + `FLAG_LANJUT_DISINI.md`.
Dokumen rinci: `PUTUSAN_JEMBATAN_KONVERSI_15OKT2026.md` ·
`PUTUSAN_TIKET_LOLOS_LAPIS3_16OKT2026.md`.

| Hal | Keadaan |
|---|---|
| Image LIVE | `eduai-app:20261016_021214-sot` |
| Jembatan bab kurang | ✅ LIVE (uji 15/0 · 6/0) |
| Harga mutu 2/3/5 | ✅ LIVE (gerbang 42/0 · 51/0) |
| **Tiket Lolos Lapis 3** | ✅ LIVE (`app/tiket_lolos.py` BARU · uji 25/0 · 7/0 · 12/0) |

### 🔖 TIKET LOLOS — ringkas

- **Pertanyaan Bos:** user sudah bayar + dapat kebutuhan di bab itu, lalu edit
  manual / tambah kalimat yang **tidak merubah makna** ⇒ **LOLOS**.
- Yang dinilai **MAKNA** (Jev 1 pertanyaan `{sama/beda}`), **BUKAN huruf**.
- Sidik = **1.500 huruf awal bab** dari **naskah asli** · biaya Jev **GRATIS**.
- Elemen bertiket tampil **`☑ Done`** (tanpa checkbox, tak bisa dibeli 2×).
- ⚠️ **Jev mati ⇒ tiket BATAL** (kegagalan teknis BUKAN pintu gratis).

### ⚠️ Alat uji pensiun (cacat, bukan selesai)
- `_uji_jembatan_bab.py` → **27/0 PALSU** (memaksa variabel template)
- `_uji_gigi_jembatan.py` → **menimpa berkas produksi** (kerusakan tertinggal)
- Keduanya di `_sketsa/uji-pensiun-16okt2026/` (+ README alasan).
- **Pelajaran:** skill `test-gate-design` →
  `references/tiga-pola-uji-merusak-16okt2026.md`.
