# 🔑 PEMBIMBING AI SEDERHANA — EduAi

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> **Berkas ini merekam APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) di dalamnya **wajar berbeda** dari
> keadaan **kini** — itu BUKAN kesalahan, itu memang rekaman.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.

**Tanggal:** 3 Oktober 2026 · **Status:** ✅ LIVE di produksi
**Image:** `eduai-app:20261003_044420-sot` · mundur: `eduai-app:cadangan-pra-sot`
**Putusan Bos:** ACC "Opsi B" (deploy) 03Okt26

> Dokumen ini mencatat **3 pekerjaan besar** sesi 03Okt26:
> (1) pembimbing tanpa akun bisa buka naskah, (2) naskah diringankan saat
> unggah, (3) layar tunggu bermerek EduAi.

---

## BAGIAN 1 — KUNCI TINJAU: pembimbing TANPA AKUN bisa buka OnlyOffice

### Masalah (akar, TERUKUR)

Halaman `/tinjau/{token}` **tidak butuh login** — pembimbing cukup pegang
token dari mahasiswa. Tapi **editor OnlyOffice** selalu tampil **skeleton**
abu-abu, tak pernah terisi.

**AKAR:** kanal dokumen OnlyOffice
(`/oo/aset/<versi>/doc/<KEY>/c/`) dipagari **WAJIB cookie sesi**
(`app/main.py:1713-1724`). Pembimbing tanpa akun → selalu `303 /masuk`.
Aset editor (`/web-apps/`, `/sdkjs/`) tetap 200, jadi toolbar muncul sebagian
tapi dokumennya tak pernah sampai.

**BUKTI AKAR (bukan dugaan):** cache OO
`/var/lib/onlyoffice/documentserver/App_Data/cache/files/data/`
berisi **hanya** kunci mahasiswa (`e26v…`, `e80v…`) — **tidak pernah** `baca…`.

**Jejak langkah pencarian akar (penting, jangan diulang):**

| Dugaan | Hasil | Cara membuktikan |
|---|---|---|
| Naskah 5 MB terlalu besar | ❌ BUKAN | Naskah 0,01 MB pun skeleton |
| `locale/id.js` 404 | ❌ BUKAN | Muncul 1×, bukan dari kode kita |
| Konfigurasi editor salah | ❌ BUKAN | Banding mhs vs pembimbing: beda hanya hak akses |
| `documentServerUrl` kurang | ✅ DIPERBAIKI | Tanpa `'/oo/aset'`, aset 404 → iframe tak lahir |
| **Kanal dokumen butuh login** | ✅ **AKAR SEJATI** | Cookie sah → lolos; tanpa → 303 |

### Putusan Bos (VERBATIM)

> *"Pembimbing yang sah dapat kunci dari mahasiswa, sah melakukan baca dan
> komentar, tapi jika Pembimbing klik pakai Ai dia wajib daftar seperti
> mahasiswa."*

> *"kuncinya akan menempel terus di link undangan mahasiswa. … Walau link
> tersebut di kirim berualang kali tidak berubah. Walau pembimbing tidak punya
> akun tetap bisa pakai."*

**Konsekuensi:**
1. Pembimbing TANPA AKUN → cukup LINK dari mahasiswa (baca + komentar)
2. Daftar HANYA saat klik tombol AI (karena AI butuh dompet atas namanya)
3. Link menempel sampai **expired** atau **mahasiswa cabut hak**
4. Setelah punya akun → naskah SAMA muncul di dashboard pembimbing
   (tombol **"Buka naskah"**, link mentah TIDAK ditampilkan)

### Cara kerja (nol tabel/akun/dompet/jalur baru)

```
1. Pembimbing buka /tinjau/{token}/naskah-baca/{berkas_id}
   → server SET COOKIE 'eduai_tinjau' (path='/oo/aset')
     isi: "bimbingan_id.berkas_id.exp.sidik"
     sidik = hmac-sha256(SECRET_KEY)  ← pola SAMA auth.buat_token
   → cookie otomatis terkirim ke SEMUA /oo/aset/* termasuk polling socket.io

2. Pagar /oo/aset kalau BUKAN login:
   → periksa kunci lewat _kunci_berlaku(db, bimbingan_id, berkas_id)
      syarat: bimbingan HIDUP + belum DICABUT + belum KEDALUWARSA
              + berkas MEMANG milik bimbingan itu
   → lolos; kalau tidak → 303 /masuk (pagar lama UTUH)
```

**KENAPA COOKIE, BUKAN QUERY:** kanal dokumen **dibangun OnlyOffice sendiri**
dari `documentServerUrl` — query string tak bisa ditempel.

| Berkas | Perubahan |
|---|---|
| `app/kunci_tinjau.py` | **BARU** — `kunci_untuk()`, `baca_kunci()`, `batas_exp()` |
| `app/rute_pembimbing_ai.py` | `naskah_baca()` set cookie |
| `app/main.py` | impor `kunci_tinjau` + `_kunci_berlaku()` + pagar `/oo/aset` |
| `app/templates/tinjau_baca.html` | + `documentServerUrl: '/oo/aset'` |

### Bukti (semua lewat domain produksi, bypass cache)

| Uji | Hasil |
|---|---|
| tanpa cookie | **303** ditolak ✅ |
| cookie palsu | **303** ditolak ✅ |
| cookie sah | lolos ✅ |
| kunci naskah A → naskah B | **ditolak** ✅ (tidak bocor) |
| dicabut / kedaluwarsa | **ditolak** ✅ |
| gerbang `uji_kunci_tinjau.py` | **20 LULUS / 0 GAGAL** |
| gerbang `uji_kunci_berlaku.py` | **10 LULUS / 0 GAGAL** |
| MATA (potret CDP) | toolbar OO penuh + **"Memuat dokumen: 29%"** ✅ |
| cache OO | `baca60v1790446608` **MUNCUL** · 2,5 MB → 8,0 MB ✅ |

### 2 jebakan yang ditutup

1. **`TypeError: cannot unpack non-iterable NoneType`** (`main.py:1772`) —
   Wulan menulis `_, _bk = KT.baca_kunci(...)` padahal fungsinya bisa balas
   `None`. **PELAJARAN: fungsi yang bisa balas `None` JANGAN di-unpack langsung.**
2. **Cloudflare CACHE memalsukan uji pagar** — Cloudflare menyajikan balasan
   LAMA (`cf-cache-status: HIT`, `age: 68`) walau header kita sudah
   `private, no-store` + `X-Eduai-Boleh-Edge: 0`.
   **PELAJARAN: uji pagar WAJIB `-H "Cache-Control: no-cache"` + parameter acak.**

---

## BAGIAN 2 — NASKAH DIRINGANKAN SAAT UNGGAH

### Masalah (TERUKUR)

Naskah `SKRIPSI-S1-unmul-fazrigading.docx` = **5,08 MB**, isinya:

```
24 gambar        = 4,84 MB (66% berkas!) — image5.png SENDIRI 1,89 MB
document.xml     = 1,61 MB (4.331 kata · 1.679 paragraf · 22 tabel)
settings.xml     = 430 KB berisi 16.435 penanda w:rsid (sampah Word)
```

⇒ Browser harus mengunduh gambar itu semua → editor OO memuat lama.

### Putusan Bos (VERBATIM)

> *"A. Tapi hanya kompress ukuran image saja kan? Tidak merubah layout atau
> naskah paragraf, tabel, dll."*

⇒ **Opsi A:** kompres **SAAT UNGGAH**, **HANYA isi berkas gambar**.

### Cara kerja — `app/ringankan.py` (BARU)

```python
ringankan_docx(isi, nama) -> (byte_baru, laporan)
```

Aturan:
- Hanya `word/media/*` yang **> 120 KB** disentuh
- Sisi terpanjang maks **1600 px** (LANCZOS)
- JPEG kualitas **82** · **PNG ber-alfa TETAP PNG** (transparansi aman)
- Hasil ≥ aslinya atau gagal → **kembalikan byte ASLI** (pagar)
- Dipasang di `main.py` rute `/unggah` **sebelum** tulis ke disk,
  dibungkus `try/except` → unggahan **tidak pernah** gagal karenanya
- Hanya berkas **BARU** (berkas lama tidak diubah) — putusan Bos
- Kuota dihitung dari ukuran **setelah** diringankan (lebih adil)

### Hasil terukur

```
5,08 MB  →  1,69 MB     TURUN 67%
uji_ringankan.py: 16 LULUS / 0 GAGAL
```

**Bukti naskah TIDAK berubah:**

| Yang diperiksa | Hasil |
|---|---|
| `word/document.xml` | **sidik SHA-256 SAMA** ✅ |
| `word/settings.xml` · `word/styles.xml` | **sidik SAMA** ✅ |
| Jumlah `<w:p>` (1.679) & `<w:tbl>` (22) | **SAMA** ✅ |
| **Seluruh isi `document.xml`** | **IDENTIK byte-per-byte** ✅ |
| Ukuran `<wp:extent>` (cm) & rujukan `r:embed` | **SAMA PERSIS** ✅ |
| Berkas hasil | zip sehat · 24 gambar lengkap ✅ |

⚠️ Hanya 8 dari 24 gambar dikompres (yang >120 KB) — sudah memberi −67%.

**Bukti lewat domain produksi:** unggah 5,08 MB → HTTP 200 ·
kolom `ukuran` DB = 1.771.900 byte = **1,69 MB** ✅

---

## BAGIAN 3 — LAYAR TUNGGU BERMEREK EDUAI

### Putusan Bos

> *"A asal tidak berat saat di load"* · *"Opsi 1 dan foto"*

### Jebakan yang DICARI DULU (jangan diulang)

`customization.loaderLogo` / `loaderName` bawaan OnlyOffice **TIDAK DIPAKAI**.
Alasannya (terukur): OO memindahkan editor ke `index_loader.html` yang
**HANYA ADA di folder `mobile/`** — tidak ada di `main/` (editor desktop).
Memasangnya = risiko editor gagal memuat.

### Yang dipakai: TITIPAN di halaman kita

`app/templates/tinjau_baca.html` + `app/templates/editor.html`:

```
        🦜 (logo /static/ikon-burung-about.png — aset LAMA, 57 KB, ter-cache)
        Naskahmu sedang disiapkan
   Sebentar ya, halaman naskah sedang dibuka.
              ⭕ (berputar halus, CSS murni)
   ┌──────────────────────────────────────┐
   │ Naskah besar bisa butuh sedikit      │
   │ waktu. Halaman ini akan terbuka      │
   │ sendiri.                             │
   └──────────────────────────────────────┘
```

**BEBAN: NOL tambahan** (CSS ~2 KB + logo yang sudah ter-cache).
TIDAK ada nama alat/AI di layar (aturan teks Bos).
Saat OO siap → kotak **larut halus** 0,4 detik, lalu dilepas.

### 🔴 AKAR KEDUA (PENTING untuk lain kali)

Kotak tunggu mula-mula ditaruh **DI DALAM** `#tempat-editor`.
**OnlyOffice MENGGANTI seluruh isi `#tempat-editor`** saat editor dibuat →
kotak tunggu **TERHAPUS**, tak pernah terlihat.

**Bukti dari browser:**
```json
{"sibuk_ada": false, "editor_anak": 0, "iframe_di_dalam_editor": 0}
```

**FIX:** kotak tunggu WAJIB **DI LUAR** `#tempat-editor` + `z-index: 5`.
Pola ini **mengikuti halaman mahasiswa** (`editor.html .lapisan`) yang sudah
terbukti sejak lama.

### Bukti MATA (potret CDP + vision)

| Halaman | Hasil |
|---|---|
| Pembimbing (`/tinjau/.../naskah-baca`) | ✅ logo burung · "Naskahmu sedang disiapkan" · putar · kotak tip · latar putih bersih |
| Mahasiswa (`/edit/{fid}`) | ✅ sama (DOM: `memuat_ada:true, img_ada:true, tampil:flex`) |

---

## DEPLOY

```
Image LIVE  : eduai-app:20261003_044420-sot
Titik mundur: eduai-app:cadangan-pra-sot
Backup DB   : _arsip/pra-sot/20261003_044420-sot
Backup kode : _arsip/pre-deploy-20261003-0443/ (14 berkas + MD5.txt)
```

Gerbang `jalankan.sh`: 54 berkas `.py` di image **IDENTIK** dengan source ✅ ·
`/health` OK 3 dtk ✅ · DB 24 tabel · 5 user · 27 berkas ✅ ·
jaringan bridge + eduai-net ✅ · **GERBANG EDITOR LULUS** ✅

Verifikasi pasca-deploy lewat domain: halaman baca 200 ✅ · layar tunggu + logo
ADA di HTML ✅ · pagar tanpa cookie 303 ✅ · cookie palsu 303 ✅ · `ringankan_docx`
terpasang ✅

> 🚨 **PELAJARAN DEPLOY:** DILARANG `docker cp app/...` ke container.
> Itu membuat **"image bohong"** — kode jalan hari ini, **hilang saat restart**.
> Cara BENAR: edit source → `bash jalankan.sh`.

---

## SISA (belum dikerjakan)

1. Tombol **"Periksa dengan AI"** + alur `/daftar?dari=` — BELUM DIUJI
2. Uji waktu muat di **browser manusia** (bukan browser uji di server)
3. Aturan **Cloudflare** untuk `/doc/` perlu ditinjau (cache rule terlalu luas)
4. Naskah LAMA (sudah terunggah sebelum fitur) tidak ikut diringankan

---

## ✅ PEMBARUAN 15 OKT 2026 — KOLABORASI & PEMBIMBING AI SUDAH BERES

> Ditambahkan atas teguran Bos: *"Sepertinya sudah diperbaiki masalah Kolaborasi dan
> pembimbing ai ini kemarin. Dokumen saja belum update sepertinya."* → **BOS BENAR.**

**Bukti (dijalankan ULANG 15 Okt 2026 di dalam container `eduai-app`):**

| Gerbang | Hasil | Bukti |
|---|---|---|
| `_uji_pembimbing.py` (Tahap 1) | **76 LULUS / 0 GAGAL** | dijalankan ulang 15 Okt, isi DB uji dibersihkan sendiri |
| `_uji_c7_dompet.py` (dompet pembimbing) | **15 LULUS / 0 GAGAL** | DB SALINAN `/tmp/c7_uji` (patuh aturan) |

**Rute hidup di produksi (diperiksa 15 Okt):**

| Rute | Berkas | Keadaan |
|---|---|---|
| `POST /kolaborasi/asisten/{id}` | `app/kolaborasi.py:133` | ✅ LIVE (303 = pagar login normal) |
| `POST /tinjau/{token}/periksa-ai` | `app/rute_pembimbing_ai.py:72` | ✅ ada di kode |
| `GET /tinjau/{token}/naskah-baca/{berkas_id}` | `app/rute_pembimbing_ai.py:163` | ✅ ada di kode |

**Riwayat perubahan berkas (bukti tanggal):**

| Berkas | Terakhir diubah | Keterangan |
|---|---|---|
| `app/kolaborasi.py` | 29 Sep 2026 12:28 | Tab 2 Kolaborasi (T5) |
| `app/rute_pembimbing_ai.py` | 03 Okt 2026 03:39 | pembimbing tanpa akun (kunci tinjau) |
| `app/kunci_tinjau.py` | 03 Okt 2026 03:38 | cookie tanda-sah |
| `app/pembimbing.py` | 14 Okt 2026 18:07 | `rapi_bab()` — catatan pembimbing → peta Jev |

**Jadi:** pekerjaan 27 Sep → 14 Okt **SUDAH TAYANG semua**. Yang Wulan sebut "utang"
sebelumnya sudah tidak ada. Lihat juga `CATATAN_SAMBUNGAN_CATATAN_PEMBIMBING_14OKT2026.md`.

**SISA YANG BENAR-BENAR MASIH (bukan Kolaborasi):**

⚠️ `app/asisten.py:39` `NASKAH_MAKS = 40_000` + baris 147 `teks[:NASKAH_MAKS]` —
Asisten pembimbing masih kirim naskah **40.000 huruf UTUH** ke AI. Alat hemat token yang
**sudah ada** (`app/konteks.py`, terbukti hemat 91% terukur 25 Sep) **BELUM disambungkan**
ke jalur asisten. Ini **pemborosan token nyata** — belum dikerjakan.

---

## Berkas uji (sketsa)

| Skrip | Isi |
|---|---|
| `_sketsa/uji_kunci_tinjau.py` | uji modul kunci (20/0) |
| `_sketsa/uji_kunci_berlaku.py` | uji `_kunci_berlaku` di DB nyata (10/0) |
| `_sketsa/uji_ringankan.py` | uji kompres gambar (16/0) |
| `_sketsa/akar_pagar_kanal.py` | bukti logika pagar benar |
| `_sketsa/banding_konfigurasi.py` | banding cfg mahasiswa vs pembimbing |
| `_sketsa/potret_loader_cepat.py` | potret layar tunggu |
| `_sketsa/tanya_kanal_oo.py` | tanya kanal dokumen OO langsung |
| `_sketsa/arahkan_ke_kecil.py` | uji ukuran naskah (bukan akar) |
