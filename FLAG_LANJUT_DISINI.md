# 🧭 FLAG LANJUT DISINI — EduAi Publishing

<!-- SOT: dokumen INI = PENANDA KEADAAN KINI + lanjutan kerja (diperbarui tiap
     babak). BUKAN sumber kebenaran. Sumber resmi: SOT.md (+ SOT_KONVERSI_JURNAL.md
     + SOT_PETA_NASKAH_SATU_PINTU_08OKT2026.md). Kalau bertentangan ⇒ SOT.md MENANG. -->

<!-- Riwayat update: 16 Okt 2026 — UJI PLAGIARISME LIVE (tab ke-6, mode gratis) -->
<!-- Riwayat update: 17 Okt 2026 — LoA OTOMATIS + QR VERIFIKASI LIVE -->
<!-- Riwayat update: 19 Okt 2026 — BUKU UMUM: pilih jenis + susun naskah LIVE -->

# 🟢 MULAI DARI SINI — 19 OKT 2026

## 📍 POSISI TERAKHIR (19 Okt 2026) — BUKU UMUM: PILIH JENIS + SUSUN NASKAH ✅ LIVE

Image jalan: **`eduai-app:20261019_035552-sot`**
Titik mundur: `eduai-app:cadangan-pra-buku-susun` (image 17 Okt) · juga `cadangan-pra-sot`
Backup DB: `_arsip/pra-sot/20261019_035552-sot`
Produksi: https://eduai.bikinaja.id — `/buku` → 303 → `/masuk` (wajib login) — **SEHAT**

### Apa yang sudah JADI dan HIDUP

Menu Publish Buku sekarang punya **Bidang + "Untuk siapa"** di kartu Buku Umum
(kartu lain tidak disentuh). Pilihan user menentukan SELURUH wajah buku:
ilustrasi, palet infografis, bentuk label, font, dan cara menulis.

Alur lengkap yang sudah tersambung:
`/buku` → pilih **Bidang** + **Untuk siapa** → `POST /buku/mulai` →
`/buku/siapkan` (isi **judul**) → `POST /buku/susun` → `/buku/selesai`

| Jenis | Gaya gambar | Label | Sapaan |
|---|---|---|---|
| Profesional (`umum`) | metafora navy-terracotta | kotak bersudut | "Anda" |
| Anak-anak (`anak`) | clay 3D ceria | kapsul bulat | "kamu" + pertanyaan |
| Pelajar (`pendidikan`) | clay 3D kalem | kapsul tegas | "kamu" + langkah |

### Berkas kunci (SEMUA sudah masuk image)

| Berkas | Peran |
|---|---|
| `app/buku.py` | `BIDANG_UMUM`, `UNTUK_SIAPA` (ikon diverifikasi ke sprite) |
| `app/templates/buku.html` | form Bidang + Untuk siapa (hanya kartu Buku Umum) |
| `app/main.py` | 4 rute: `buku_mulai`, `halaman_buku_siapkan`, `buku_susun`, `halaman_buku_selesai` |
| `app/penyusunan_buku.py` | kuota **DI DEPAN** + token kembali kalau gagal + hasil jadi berkas |
| `app/templates/buku_siapkan.html` | kolom judul + tombol "Susun sekarang" |
| `app/templates/buku_selesai.html` | hasil: jumlah bab, kata, folder |
| `outline_buku.py` | outline **per buku** (pengganti `MASTER_OUTLINE_SEMENTARA`) |
| `penyusun_buku.py` | pembungkus `buku_umum_pipeline` (NOL salinan logika) |
| `buku_umum_pipeline.py` | mesin (dulu tidak ada di image!) |
| `jenis_buku.py` · `tone_menulis.py` · `brief_visual.py` · `label_infografis.py` · `larangan_budaya.py` · `verifikasi_sitasi.py` | rantai impor mesin |

### ⚠️ TIGA JEBAKAN YANG SUDAH DITEMUKAN (jangan diulang)

1. **`editor_prompt` dulu tidak menerima `jenis`.** Aturan buku dewasa
   (`Personal >=20% (Anda, kita, pembaca)` + `0 pertanyaan`) bocor ke buku anak.
   Terukur: 4× "Anda", 0 pertanyaan. **Sekarang**: anak wajib "kamu", "Anda"
   DILARANG, pertanyaan diizinkan. Hasil: 39× "kamu", 0× "Anda", 33 pertanyaan,
   6,5 kata/kalimat. → **SEMUA prompt baru WAJIB menerima `jenis`.**
2. **`requests` TIDAK ADA di image.** `requirements.txt` tidak memuatnya; app
   memakai `httpx`. Pipeline `import requests` di baris 9 ⇒ gagal dimuat ⇒
   `siap()` False ⇒ tombol mati. **Solusi**: pembungkus `_RequestsShim` di atas
   httpx. **JANGAN tambah dependency baru.**
3. **`count_citations` salah hitung.** Pola lama `\([A-Z][a-z]+.*?\d{4}\)`
   tidak menghitung `(A, 2019)` dan hanya 1 per baris ⇒ bab berisi 3 sitasi
   dilaporkan 1. **Sekarang** hitung tiap isi kurung yang memuat tahun 4 angka.

### Gerbang (semua HIJAU sebelum deploy)

`gerbang_penyusunan_naskah.py` **82/0** · `uji_kuota_penyusunan.py` **17/0** ·
`uji_penjaga_sitasi.py` **19/0** · `gerbang_menu_buku_umum.py` **30/0** ·
`gerbang_tone_jenis.py` **27/0** · `gerbang_jenis_buku.py` **32/0** ·
`gerbang_buku_anak.py` **26/0** · `gerbang_ilustrasi_2tahap.py` **39/0** ·
`gerbang_larangan_budaya_semua_jalur.py` **16/0** · `_uji_buku_siapkan.py` **43/0**
· `_uji_rute_buku.py` **17/0**

Semua di `/opt/data/`, salinan di `skills/penelitian-ilmiah/buku-umum/scripts/`.

---

## ⬜ YANG BELUM — KERJAKAN BERURUTAN

### 1. 🔴 TERPENTING — `/buku/susun` masih MENUNGGU sampai selesai
Buku 6 bab = **±36 menit** dalam SATU request. Tab ditutup di tengah = proses
tetap jalan di server tapi user tidak tahu apa-apa. Ini yang akan dikeluhkan
user pertama, BUKAN mutu tulisannya.
**Yang benar**: pekerjaan latar + halaman status ("BAB 2 dari 6 sedang ditulis").

### 2. Assembly DOCX belum dipanggil
Hasil masih berkas bab terpisah di `BUKU_DIR` (default `/opt/data/buku_hasil`),
belum satu `.docx` rapi (daftar isi, nomor halaman, daftar pustaka).

### 3. Bidang belum memengaruhi isi tulisan
Bidang baru dipakai sebagai konteks outline. Belum mengubah gaya/kedalaman isi.

### 4. Penjaga sitasi belum pernah menyala pada tulisan ASLI
Dua bab nyata kebetulan sudah punya cukup sitasi (3–5). Yang terbukti menyala
baru uji paksa (`_uji_sitasi_paksa.py`: 1 → 3 sitasi).

### 5. Ilustrasi jalan, infografis label belum otomatis di jalur ini

---

## 🔎 CARA MEMERIKSA ULANG (jangan percaya kata Wulan)

```bash
cd /opt/data
.venv/bin/python gerbang_penyusunan_naskah.py          # harus 82/0
docker exec -w /app eduai-app python -c \
  "import sys; sys.path.insert(0,'/app'); from app import penyusunan_buku as PB; print(PB.siap())"
# harus: (True, '')

cd /opt/data/services/eduai-publishing && bash scripts/periksa_kode.sh   # harus LULUS
bash jalankan.sh                                                          # deploy WAJIB ini
```

**Mundur kalau rusak:**
```bash
docker tag eduai-app:cadangan-pra-buku-susun eduai-app:20261019_035552-sot
# lalu jalankan ulang sesuai prosedur jalankan.sh dengan image titik mundur
```

---

### 📍 POSISI SEBELUMNYA (17 Okt 2026) — LoA OTOMATIS + VERIFIKASI QR ✅ LIVE

> ⚠️ CATATAN (19 Okt 2026): image di bawah = KEADAAN SAAT ITU, BUKAN yang jalan
> sekarang. Lihat blok paling atas untuk image yang benar-benar jalan.
> Baris ini sengaja dipertahankan sebagai riwayat.

Image saat itu: `eduai-app:20261017_043641-sot`  ← **WA admin = 8516** (17 Okt)
Titik mundur: `eduai-app:cadangan-pra-sot`
SOT lengkap: **`SOT_LOA_QR_17OKT2026.md`** ← BACA INI DULU

**APA YANG JADI (semua TERUJI, 11 LULUS / 0 GAGAL di HP 390px):**
```
Editor "Terima" di Tridarma → user klik "Unduh LoA" di EduAi → PDF 1 halaman
   + QR ke https://qr.tridarma.id/verifikasi-loa?no=...
```

| Pintu | Isi |
|---|---|
| `app/loa.py` | mesin: cek syarat, 15 token, nomor urut, PDF, QR, `terbitkan()`, `cari_loa_nomor()` |
| `app/templates/loa/loa-jemt.html` | template LoA (kop, ttd, blok verifikasi+QR) |
| `app/templates/loa/verifikasi-loa.html` | halaman verifikasi publik (KOP SAMA dengan LoA) |
| `app/templates/loa/tanda-tangan.png` | ttd asli (ekstrak dari SVG Bayana) |
| `app/main.py` | `/verifikasi-loa` · `/api/loa/cek` · unduh LoA · **middleware domain** |
| `app/submit_jurnal.py` | `perbarui_status` simpan volume/nomor; `OJS_BRIDGE` dibetulkan |
| Cloudflare Tunnel | aturan **no.9** `qr.tridarma.id → localhost:8100` (wildcard no.10 UTUH) |

**3 JEBAKAN TERUKUR (JANGAN ULANG):**
1. **`async async function`** di verifikasi-loa.html ⇒ SELURUH JS mati ⇒ tombol diam.
   ⇒ WAJIB `node --check` isi `<script>` sebelum deploy.
2. **`@app.middleware` HARUS tepat setelah `app = FastAPI(...)`** — kalau di bawah,
   FastAPI menolak senyap ⇒ middleware tak terpasang ⇒ `qr.tridarma.id/` tampil beranda EduAi.
3. **Alat ukur menipu**: Chrome :9333 dipaksa `innerWidth=698` walau diminta 390.
   ⇒ UJI HP WAJIB **Playwright** + verifikasi MATA. JANGAN percaya Chrome 9333.

**JEMBATAN OJS — ALAMAT BENAR:** `https://tridarma.id/mcp`
(`ojs-ojs_web-1` = nama container internal ⇒ tak ketemu; `:9027` = SSH, BUKAN HTTP)

**SISA / BELUM:**
- Tridarma `issues = 0` ⇒ belum ada Volume/Nomor ⇒ LoA artikel NYATA belum bisa terbit.
- ✅ **Nomor WA admin SUDAH DIBETULKAN** (17 Okt 2026, image
  `eduai-app:20261017_043641-sot`): `config.EDUAI_WA_ADMIN` = `6285178138516`
  = **admin EduAi** (putusan Bos). Teruji kirim NYATA. Backup
  `_arsip/pre-wa-admin-8516-20261017-043611`.
  🔒 `8516` = admin EduAi · `8514` = admin Tridarma · `6285720505555` DIBUANG.
  ⚠️ Tridarma TIDAK punya nomor admin — notifikasi ke GRUP WA.
- Tombol "Unduh LoA" belum diuji dengan akun user + artikel Diterima sungguhan.
- Data uji `1.001` SUDAH DIBERSIHKAN (cadangan `_arsip/pre-bersih-loa-20261017_035810/`).

**CARA UJI CEPAT:**
```bash
python3 _sketsa/uji_terbitkan30.py     # mesin (3 kasus, folder /tmp)
python3 _sketsa/uji_valid_hp.py        # halaman verifikasi HP (11 asersi)
curl -s "https://qr.tridarma.id/api/loa/cek?no=1.001"
```


### 📍 POSISI SEBELUMNYA (16 Okt 2026) — ARSIP, bukan keadaan kini

Image waktu itu (sudah diganti): `eduai-app:20261016_100447-sot`  ← uji plagiarisme
Titik mundur: `eduai-app:cadangan-pra-plagiarisme` (= `20261016_021214-sot`)
Backup DB: `_arsip/pra-sot/20261016_100447-sot` · kode: `_arsip/pre-plagiarisme-20261016-095734/`

### 🆕 BABAK 16 OKT — UJI PLAGIARISME LIVE (tab ke-6)

**Pintu `/plagiarisme`** — 4 lapis SEMUA PEMASANGAN, nol mesin baru:
menu 6 tab · `app/plagiarisme.py` · `templates/plagiarisme.html` · 8 token (`kuota`).

```
Gerbang: _uji_pintu_plag.py   18 LULUS / 0 GAGAL  (DB salinan, container)
         _uji_plagiarisme.py  24 LULUS / 0 GAGAL  (5 lapis, host)
         _uji_stabilo_alami.py 15 LULUS / 0 BERGIGI
```

**⚠️ MODE BERBAYAR BELUM DIAKTIFKAN** — mesin pencari belum ada (Google blokir
VPS); Bos urus pakai API key. Mode **gratis** (mode contoh) jalan penuh.

**2 AKAR saat pemasangan:** ① `similarity_precheck.py` di `/opt/data/scripts` =
DI LUAR image ⇒ `COPY` ke Dockerfile; ② WeasyPrint+PyMuPDF tak ikut image ⇒
masuk `requirements.txt` + apt (pango/harfbuzz). Detail:
`PUTUSAN_UJI_PLAGIARISME_16OKT2026.md` (SOT fitur ini).

### 📌 BABAK 16 OKT — SELESAI SEBELUMNYA

**1. JEMBATAN BAB KURANG LIVE** (`artikel_konversi.html`)
Bab kurang ⇒ HANYA tombol "Perbaiki" (tombol konversi & mutu DISEMBUNYIKAN).
Bab lengkap ⇒ baru cek mutu. Aturan Bos: *"tombol harus salah satu"*.
Bukti: `_uji_jembatan_final.py` **15/0** · `_uji_jembatan_kurang.py` **6/0**.
Dokumen: `PUTUSAN_JEMBATAN_KONVERSI_15OKT2026.md`.

**2. TIKET LOLOS — LAPIS 3 LIVE** (`app/tiket_lolos.py` BARU)
Pertanyaan Bos: *"user sudah bayar & dapat kebutuhannya di bab itu, lalu edit
manual / menambah kalimat yang TIDAK merubah makna — lolos atau tidak?"*
⇒ **LOLOS.** Yang dinilai **MAKNA** (Jev 1 pertanyaan choice), bukan huruf.
- Sidik = **1.500 huruf awal bab** dari naskah asli
- Biaya Jev = **GRATIS** (ditanggung EduAi)
- Elemen bertiket tampil **`☑ Done`** (tanpa checkbox, tidak bisa dibeli 2×)
- Jev mati ⇒ tiket **BATAL** (kegagalan teknis BUKAN pintu gratis)

Bukti: `_uji_tiket_lolos.py` **25/0** · `_uji_tiket_pintu.py` **7/0** ·
`_uji_tiket_layar.py` **12/0** · Jev NYATA 2/2 tepat (0,5 dtk).
Dokumen: `PUTUSAN_TIKET_LOLOS_LAPIS3_16OKT2026.md`.

⚠️ **PELAJARAN KERAS 16 OKT — UJI GIGI JANGAN MERUSAK BERKAS PRODUKSI.**
Uji lama menimpa `artikel_konversi.html` di container hidup; crash di tengah
⇒ judul jadi `XXX-MATI-XXX` TERTINGGAL di produksi. Obat: uji gigi **WAJIB
lewat salinan** (tulis ke `/tmp`, `try/finally`). Wulan hampir menyalahkan kode
padahal itu kerusakan buatannya sendiri. (fact_store id 306)

⚠️ **PELAJARAN KEDUA:** uji yang MEMAKSA variabel template = **UJI PALSU**.
Uji lama bilang 27/0 padahal jalur rute mengirim data dari tempat lain.
⇒ Uji WAJIB lewat **rute nyata** (`TestClient`) atau fungsi yang benar-benar
dipakai rute.

### 📍 RIWAYAT — BABAK 15 OKT (siang) (arsip, bukan acuan)

Image ketika itu: `eduai-app:20261015_112244-sot` ← hemat token + PAGAR 2 LIVE.

### 🗄️ RIWAYAT — BABAK 15 OKT (siang): SELESAI & TERBUKTI DENGAN AI SUNGGUHAN

**1. Gerbang setelan produksi (`_gerbang_setelan_produksi.py`) — BARU, LIVE**
Alat uji WAJIB memakai setelan produksi (`enable_thinking: False`). **8 pemeriksa,
terpasang di `scripts/periksa_kode.sh` ⇒ ikut MENOLAK DEPLOY.** Terbukti bergigi
(candik disuntik → deploy ditolak). 4 alat uji yang lupa diperbaiki. Pelajaran:
`references/alat-uji-wajib-setelan-produksi-15okt2026.md` (skill `test-gate-design`).

**2. UJI HIDUP pagar 2 — LULUS, 2 operasi AI nyata (~Rp 4)**
Naskah uji 31.140 kar, DB SALINAN (`EDUAI_DATA_DIR=/tmp/live_uji`).
Log produksi berbicara sendiri:
- catatan *"perbaiki ejaan"* → `konteks DIPAKAI: bagian ke-1/5 (BAB 1) → kirim 9.144 kar | hemat 71%` ✅
- catatan *"ubah alur seluruh naskah"* → `PAGAR: permintaan menyeluruh → kirim naskah UTUH 31140 kar` ✅

**3. UJI HULU-HILIR (naskah BERISI KESALAHAN SENGAJA) — LULUS**
AI memberi **8 usulan nyata** + menangkap 3 cacat yang ditanam: sig 0,023 tapi
disimpulkan H0 diterima (AI: *"semestinya H0 DITOLAK"*) · 120 sampel dari 120 populasi
disebut *purposive* (AI: *"lebih tepat sampling jenuh"*) · tujuan "self efficacy" vs
rumusan "motivasi". **8/8 kutipan ADA di naskah** (anti-karangan terbukti).
Alat: `_uji_hulu_hilir.py` · `_periksa_kutipan.py` · `_uji_hidup_ai.py`.

⚠️ **JEBAKAN ALAT UKUR (2× Wulan salah 15 Okt):**
- (a) folder DB uji KOSONG → tabel `setelan` hilang → fallback utuh → hasil TIDAK SAH.
  **OBAT: `cp /app/data/eduai.db` ke folder uji.**
- (b) bandingkan kutipan APA ADANYA = salah; naskah punya ENTER, AI salin jadi SPASI.
  **OBAT: `re.sub(r'\s+',' ',teks)` dulu.**
- (c) kalimat uji jangan dikarang — ambil DARI daftar aturan (`parser._KATA_ALUR`).

### 💰 HEMAT TOKEN ASISTEN PEMBIMBING — LIVE 15 OKT (putusan Bos: "A")

Naskah 40.000 kar UTUH → **1 bab + tetangga** ⇒ **hemat 90,0%** (16 naskah asli:
1.127.792 → 112.528 kar). Gerbang `_uji_hemat_asisten.py` **30/0** (hemat + pagar) ·
`_uji_pembimbing.py` **76/0** · `_uji_c7_dompet.py` **15/0**.

**PAGAR 2 — permintaan MENYELURUH kirim UTUH (15 Okt, LIVE):** kalau pembimbing
menulis *"ubah alur seluruh naskah"* → asisten kirim **naskah utuh**, TIDAK dipotong.
Memakai `ai._boleh_konteks()` (ai.py:1931) lewat `parser.pilih_pengali` — aturan
TIDAK disalin. Bukti bergigi: dengan pagar 25.080 kar (utuh), tanpa pagar 8.161 kar.
⚠️ Pemicu = `parser._KATA_ALUR` (ubah/ganti/rombak alur, ubah paradigma…);
*"perbaiki alur"* **bukan** pemicu (rancangan lama, BUKAN bug — dikunci G4e).
Gagal apa pun → naskah utuh (tinjauan tak pernah gagal). Catatan:
`CATATAN_HEMAT_TOKEN_ASISTEN_15OKT2026.md`

### 🔬 UJI WORDCRAFT — SELESAI 15 OKT (putusan Bos: "A", NOL perubahan produksi)

**HASIL: WordCraft = ALAT BANTU WULAN (baca/lihat/periksa naskah), BUKAN pengganti OnlyOffice.**
- CLI jalan: `/opt/data/services/wordcraft-uji/bin/wordcraft-cli` (73 MB, v0.7.0)
- TERBUKTI: baca 0,14–0,56 dtk · PDF 0,5–2 dtk (**10× lebih cepat dari OO**) · RAM 94 MB (**50× lebih ringan**)
- ❌ PDF belum sama: halaman beda **+3 s/d +7** (WordCraft salah tangani `<w:titlePg/>` + `<w:vAlign>` ⇒ halaman kosong)
- ⇒ OnlyOffice **TETAP** mesin PDF produksi. Laporan lengkap: `LAPORAN_UJI_WORDCRAFT_15OKT2026.md`

### ✅ YANG TAYANG (14–15 Okt 2026)

| # | Fitur | Bukti | Image |
|---|---|---|---|
| 1 | **Optimasi putaran Jev 3→1** | 161 dtk → 54 dtk; bab 70 → 80 | `20261014_055505-sot` |
| 2 | **Jev tidak dipanggil berulang** | 55,6 dtk → 0,0 dtk (uji 6/0) | `20261014_055505-sot` |
| 3 | **Naskah rusak tidak bayar Jev** | fid 115 fallback Rp 0 (gerbang 15/0) | `20261014_071115-sot` |
| 4 | **Catatan pembimbing → peta Jev** | `rapi_bab()` + gerbang 32/0 | `20261014_184545-sot` |
| 5 | **Bug batas bab (disertasi 7 bab)** | `BATAS_BAB=20`, gerbang 55/0 | `20261015_002535-sot` |

### 📁 DOKUMEN RESMI YANG BERLAKU (SOT / terbaru)

- `SOT.md`
- `SOT_KONVERSI_JURNAL.md`
- `SOT_PETA_NASKAH_SATU_PINTU_08OKT2026.md`
- `MASTER_PLAN.md`
- `FLAG_BUKU_UMUM_19OKT2026.md` ⭐ **19 Okt — flag ringkas babak Buku Umum**
- `RENCANA_SAMBUNG_PENYUSUNAN_18OKT2026.md` ⭐ 18–19 Okt (rencana 5 lapis)
- `PAGAR_BATAS_BAB_15OKT2026.md` ⭐ baru 15 Okt
- `CATATAN_HEMAT_TOKEN_ASISTEN_15OKT2026.md` ⭐ 15 Okt
- `RINGKASAN_BABAK_15OKT2026_SIANG.md` ⭐ baru 15 Okt (ringkasan babak)
- `UJI_MUTU_JURNAL_15OKT2026.md` ⭐ baru 15 Okt (MUTU JURNAL TERBUKTI — jangan uji ulang)
- `PAGAR_MUTU_PETA_DAN_HEMAT_JEV_14OKT2026.md` ⭐ 14 Okt
- `CATATAN_SAMBUNGAN_CATATAN_PEMBIMBING_14OKT2026.md` ⭐ 14 Okt
- `RANCANGAN_RAPI_BAB_14OKT2026.md` ⭐ 14 Okt

### ⬜ BELUM / LANJUTAN

✅ **KOLABORASI + PEMBIMBING AI = SUDAH BERES** (dibuktikan ulang 15 Okt: gerbang
`_uji_pembimbing.py` **76/0** · `_uji_c7_dompet.py` **15/0** · rute `/kolaborasi/asisten`
LIVE). Jangan diusulkan "perbaikan" lagi. Rincian: `DOKUMENTASI_PEMBIMBING_AI_03OKT2026.md`
bagian "PEMBARUAN 15 OKT 2026".

- ✅ **Asisten pembimbing HEMAT TOKEN — SUDAH LIVE** (15 Okt, image
  `eduai-app:20261015_112244-sot`): naskah 40.000 kar utuh → **1 bab + tetangga**,
  **hemat 90,0%** (terukur 16 naskah asli: 1.127.792 → 112.528 kar). Gerbang
  `_uji_hemat_asisten.py` **30/0** (hemat + pagar) · `_uji_pembimbing.py` **76/0** ·
  `_uji_c7_dompet.py` **15/0**. Alat: `app/konteks.py` (SUDAH ADA) + giliran di tabel
  `setelan` (nol tabel baru). ⚠️ JANGAN kirim beberapa bagian sekali jalan — terukur
  cuma hemat 2,8%. **PAGAR 2:** permintaan menyeluruh → kirim UTUH (lihat blok atas).
  Catatan: `CATATAN_HEMAT_TOKEN_ASISTEN_15OKT2026.md`
- ✅ **Uji mutu revisi AI: potongan vs penuh** — SELESAI 15 Okt (alat ukur diperbaiki
  dulu; hasil: PENUH 3,83 vs POTONG 4,00, praktis sama; juri buta masih bias urutan
  ⇒ belum sah)
- ⬜ Disk VPS 94% penuh (sisa 4,2 GB)
- ⬜ Kalimat layar "peta pakai mode hemat" (kotak mutu sudah ada)
- ⬜ Satukan 6 penulis romawi (terukur SEPAKAT I–X; beda jangkauan saja)
- ⬜ Juri buta belum sah — perlu ACAK urutan + 2 juri (opsi B utang lama)
- ⬜ Bab otomatis dari komentar (12 rekomendasi `/peta/mulai`)

### ✅ MUTU JURNAL — TERBUKTI BENAR (15 Okt 2026, putusan Bos: "Opsi A")

Mesin mutu ARTIKEL (`konversi.periksa_hasil` + `periksa_hasil_jev`) **SUDAH JADI &
SUDAH BENAR** — jangan uji ulang. Bukti: artikel lengkap skor **0,89–0,99** · artikel
cacat **0,05–0,1** (skor total 0,52, **8 kurang** tertangkap). Lapis 1 (mesin Rp 0)
**bergigi**: 5 cacat sengaja tertangkap semua. 3 gerbang lama: 29/0 · 14/0 · 15/0.
⚠️ **TEMUAN KECIL (SUDAH DIBANTAH 15 Okt — bukan masalah):** Wulan sempat melapor artikel
bagus dapat peringatan "hook" karena ambang 0,95. **ITU SALAH UKUR WULAN** — ambang
sebenarnya **0,50** (`AMBANG_ADA`), dan **uji ulang: 18/18 ADA, 0 ragu.** Rincian:
`UJI_MUTU_JURNAL_15OKT2026.md`. ⇒ **ambang TIDAK diubah.**
⚠️ Nama jangan tertukar: `periksa_mutu.py` = naskah MASUKAN · `konversi.periksa_hasil` =
ARTIKEL JADI.

### 🔬 WORDCRAFT (15 Okt 2026)

CLI dipasang `/opt/data/services/wordcraft-uji/bin/wordcraft-cli` (78 MB) = **alat bantu
Wulan** baca + lihat naskah (10× cepat, RAM 94 MB). **BUKAN pengganti OnlyOffice** (PDF
melenceng 3–7 hlm). MCP tidak dipakai. Laporan: `LAPORAN_UJI_WORDCRAFT_15OKT2026.md`.

---

## RIWAYAH FLAG (untuk arsip, BUKAN acuan kerja)

*Lihat `_arsip/` untuk snapshot lama. Dokumen di root yang tidak ditandai ⭐ di atas adalah arsip diskusi; rujuk SOT jika bertentangan.*
