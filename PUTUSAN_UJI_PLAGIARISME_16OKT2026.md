# 🔍 UJI PLAGIARISME EduAi (16 Okt 2026) — ✅ **LIVE** (mode gratis)

<!-- SOT: putusan Uji Plagiarisme · 16 Okt 2026 · acuan tunggal untuk:
     (a) peta lapis fitur; (b) harga & jatah; (c) cara watermark hasil gratis;
     (d) jawaban "kenapa hasil 0%" saat cek sungguhan.
     ✅ STATUS 16 Okt 2026: LIVE via image `eduai-app:20261016_100447-sot`.
     Gerbang pintu `_uji_pintu_plag.py` 18/0 lewat PRODUKSI + bukti MATA.
     ⚠️ Mode BERBAYAR sengaja BELUM diaktifkan (mesin pencari belum ada).
     Catatan dibuat karena MEMORI PENUH (3.998/4.000); memory tool menolak. -->

## 🗺️ PETA LAPIS = 4 (semua PEMASANGAN, NOL mesin/tabel/dompet baru)

| # | Lapis | Berkas | Keadaan |
|---|-------|--------|---------|
| ① | Pintu | `app/templates/_menu.html` (5 tab → **6**) + rute `/plagiarisme` di `main.py` | ✅ LIVE |
| ② | Mesin | `app/plagiarisme.py` — **MERAKIT** `similarity_precheck.py` | ✅ LIVE |
| ③ | Layar | `app/templates/plagiarisme.html` (gaya aplikasi) | ✅ LIVE |
| ④ | Token | `kuota.potong_banyak()` (SUDAH ADA — nol dompet baru) | ✅ 8 token |

## ✅ BUKTI PEMASANGAN (16 Okt 2026, lewat PRODUKSI)

```
_uji_pintu_plag.py  →  18 LULUS / 0 GAGAL   (DB SALINAN, container)
_uji_plagiarisme.py →  24 LULUS / 0 GAGAL   (5 lapis, di HOST)
dup gerbang: suntik 3 kerusakan → 5 GAGAL → pulih md5 identik ✅
```

| Uji | Hasil |
|---|---|
| `/plagiarisme` terbuka setelah login | ✅ 200 |
| tab + ikon di menu | ✅ |
| biaya 8 token tampil | ✅ |
| **pagar: naskah MILIK ORANG LAIN ditolak** | ✅ 404 |
| uji gratis → 11 sumber · 11 stabilo | ✅ |
| berkas PDF terunduh | ✅ 200 |
| naskah 38.883 kar → **23 halaman** (>10) | ✅ |
| watermark PRATINJAU semua halaman | ✅ |
| **gratis kedua untuk naskah sama ditolak** | ✅ 409 |
| MATA: stabilo + kotak nomor + DEMO + footer merah | ✅ 4/4 |

## 🚨 2 AKAR TERUKUR SAAT PEMASANGAN (jangan diulang)

| Gejala | Akar | Obat |
|---|---|---|
| `500 No module named 'similarity_precheck'` | script Bos ada di `/opt/data/scripts` = **DI LUAR image** | `COPY similarity_precheck.py ./` di Dockerfile (pola sama seperti `peta3_jev.py`) |
| `500 No module named 'weasyprint'` | WeasyPrint + PyMuPDF **tidak ikut image** | `requirements.txt` += `weasyprint==69.0`, `pymupdf==1.28.0`; Dockerfile apt += libpango, pangoft2, harfbuzz-subset0, libffi-dev, shared-mime-info, fonts-dejavu-core |

**PELAJARAN UJI:** gerbang pintu sempat "GAGAL" 3× karena **salah uji Wulan**, bukan bug:
① berkas uji ditaruh di `/tmp` padahal produksi baca `/app/uploads/<uid>/` → 422 `NASKAH_KOSONG` (pagar bekerja BENAR);
② naskah uji PENDEK → PDF 4 halaman → uji "25 halaman" gagal palsu;
③ jumlah halaman dipaku `== 25` padahal ikut panjang naskah → ubah jadi `> 10`.


## 🔒 PUTUSAN TERKUNCI

| # | Keputusan |
|---|-----------|
| 1 | **Menu: A — di dalam EduAi**, nama fitur **"Uji Plagiarisme"** |
| 2 | **Pembanding: 11 domain** (milik script Bos, SUDAH ADA) |
| 3 | **Harga: 8 token** per cek |
| 4 | **Naskah: A — hanya dari EduAi** (1 gerbang upload; user luar TIDAK bisa tempel teks) ⇒ pagar upload 1 tempat |
| 5 | **Pratinjau gratis: 1× per naskah** |
| 6 | **Hasil gratis = TEMPLATE PERSIS berbayar**, bedanya HANYA watermark |
| 7 | Watermark: **logo EduAi samar + "DEMO" besar di tengah + peringatan di FOOTER** (merah) |
| 8 | **Tolak halus**: naskah sama (sidik) ⇒ tolak → dorong berbayar; **naskah DIUBAH ⇒ lolos gratis** (SHA-256 berubah otomatis) |
| 9 | Masalah mesin pencari (Google blokir VPS) ⇒ **Bos urus pakai API key, NANTI** |

## 🔬 TEMUAN TERUKUR (jangan diulang salah)

1. **`check_similarity(teks, mock_mode=True)`** = mode contoh (random 2-5%, 11 sumber hardcode) → **inilah yang dipakai GRATIS**.
2. **`mock_mode=False`** = cek sungguhan 11 domain — **TAPI hasil 0% dari VPS** ⇒ **Google membatasi bot** (konsisten dgn catatan skill `similarity-precheck` pitfall #2). ⇒ **TIDAK boleh dijual sebelum mesin pencari beres** (user bisa bayar 8 token untuk 0% palsu).
3. **`generate_combined_pdf(text, result, path, doc_title)`** = pembuat PDF gaya Turnitin. **Fungsi ini TERPISAH dari hitungan** ⇒ bisa diberi hasil apa pun.
4. Fungsi lain: `generate_html_report()` · `generate_highlighted_doc()` · `run_precheck_full()`.
5. **Sidik naskah SUDAH ADA**: `models.py:627 sidik_jari` (SHA-256, indexed) · `models.py:669 sidik_bab`. Tabel `pencarian_manual` sudah punya kolom jatah + `jenis` 'gratis'/'token'. ⇒ **nol tabel baru**.
6. **WeasyPrint 69.0 ADA** · **PyMuPDF ADA** · logo BENAR: `app/static/logo-about-256.png` (burung utuh).

## ✅ MODUL RESMI SUDAH JADI (16 Okt 2026)

```
app/uji_mirip.py   ← 1 perintah → 1 file PDF (25 halaman)
```

```python
from app import uji_mirip
r = uji_mirip.buat_laporan(teks, judul, keluar)          # ← GRATIS (mock)
r = uji_mirip.buat_laporan(teks, judul, keluar, mock=False)  # ← 8 TOKEN
# → {'pdf', 'indeks', 'jumlah_sumber', 'stabilo', 'halaman'}
```

**Isi 1 file:** cover + naskah+stabilo + laporan (11 sumber) + watermark.

## 📐 LAPORAN = 1 HALAMAN (putusan Bos 16 Okt, TERBUKTI)

| Yang diperbaiki di `scripts/similarity_precheck.py` | Sebab |
|---|---|
| Laporan dipaksa **mulai halaman baru** (`.halaman-baru`) | dulu mulai y=190 → 130 pt kosong, laporan pecah |
| Baris EXCLUDE **jangan** `break-inside:avoid` | dulu terlempar ke hal berikutnya walau sisa 44 pt |
| `table.sources td{padding:0 2px}` + `.src-url{line-height:1.15}` | dulu 2px 2px → sumber ke-9..11 tumpah |

**BUKTI:** 26 hlm → **25 hlm**; hal 25 = `SIMILARITY INDEX` + **11 sumber** + `EXCLUDE QUOTES` **satu halaman** ✅
Cadangan: `_arsip/pre-laporan-1hal-20261016-063400/`.

## ✅ MODUL RESMI SUDAH JADI (16 Okt 2026)

```
app/uji_mirip.py   ← 1 perintah → 1 file PDF (25 halaman)
```

```python
from app import uji_mirip
r = uji_mirip.buat_laporan(teks, judul, keluar)
# r = {pdf, indeks, jumlah_sumber, stabilo, halaman}
```

### 🎨 STABILO — putusan Bos yang TERKUNCI (4× teguran, semuanya BERES)

| # | Putusan Bos (verbatim) | Cara dikerjakan | Bukti |
|---|------------------------|-----------------|-------|
| 1 | *"kotaknya diatas kalimat atau kata Diatas stabillo"* | nomor ditaruh di **`.baris-nomor`** (baris tersendiri DI ATAS kalimat) | zoom 4,4×: kotak di atas ✅ |
| 2 | *"stabilo tidak perlu ditumpuk... cukup stabilo 1 warna sumber"* | **sumber TERPANJANG menang** (pilihan Bos **A**) ⇒ 1 kalimat 1 warna | 1 warna per kalimat ✅ |
| 3 | *"laporan 11 web warna berbeda, kenapa di naskah hanya 3 stabilo"* | **1 sumber = 1 stabilo** (dulu `sim_pct%` kalimat + sumber UNDIAN) | 11/11 ✅ |
| 4 | *"kok jadi 3 sumber semua, harusnya ACAK... se natural mungkin"* | **acak berbobot ~68% 1 sumber · 26% 2 · 6% 3** | 10/1/0 ✅ |
| 5 | Panjang deteksi beda tiap sumber | `rentang_kata` per-sumber (12/20/12 kata) | ✅ |

⚠️ **JEBAKAN WEASYPRINT (terbukti, jangan diulang):**
- `position:absolute` + `top` bertingkat = **KOTAK BERTUMPUK JADI SATU** ("14") — WeasyPrint mengabaikan `top`. **HARAM.**
- Ada **2 CSS kembar**: baris ~632 (dipakai `generate_highlighted_doc`) & ~918 (dipakai `generate_combined_pdf`). **Perbaiki yang 918.**
- Gerbang: **`_uji_stabilo_alami.py`** (15/0, BERGIGI terbukti) · `_uji_nomor_multi.py` (12/0).

### 📌 CARA WATERMARK YANG TERBUKTI (teruji mata 16 Okt, DIREVISI)

### 📦 BERKAS GAMBAR JADI (menyatu — tinggal pakai!)

```
app/static/watermark-uji-mirip.png     ← 2000x1600 px, TRANSPARAN, 284 KB
   isi: 🐦 logo burung bertoga (samar 0,24)
        DEMO besar (tipis) DI BAWAH paruh
        PRATINJAU kecil di bawahnya
```

Pembuat: `_buat_watermark_menyatu.py` · Penempel: `_tempel_watermark_menyatu.py`

**Logo yang BENAR = `app/static/logo-about-256.png`** (497×378, burung utuh).
⚠️ **JANGAN pakai `logo-320.png`** — itu logo PANJANG (320×127, ada tulisan
"EduAi"); dipaksa besar ⇒ terpotong ⇒ muncul "kotak kuning" aneh di tepi.

### Alur lengkap (3 langkah)

```
1. hasil = S.check_similarity(teks, mock_mode=True)
2. S.generate_combined_pdf(teks, hasil, pdf_asli, doc_title)  ← script BOS
3. tempel 1 gambar: hal.insert_image(rect, filename=watermark-uji-mirip.png)
```

**Cukup 1 gambar** (tidak repot 2 lapis logo+teks) — sesuai putusan Bos.

### 🚨 2 JEBAKAN YANG SUDAH KENA (wajib diingat)

- **`insert_textbox(..., fill_opacity=…)` TIDAK BEKERJA** untuk TEKS di PyMuPDF ⇒ "DEMO" tidak muncul. ⇒ pakai **`insert_text()`** + **campur warna ke putih**:
  ```python
  def campur(hex_warna, latar=(1,1,1), alpha=0.30):
      r,g,b = (int(hex_warna[i:i+2],16)/255 for i in (0,2,4))
      return tuple(c*alpha + l*(1-alpha) for c,l in zip((r,g,b), latar))
  ```
- **Logo PNG TIDAK bisa `alpha=` lewat `insert_image`** (hasilnya solid & menutupi sumber #3/#4). ⇒ turunkan alpha lewat **PIL**, kirim sebagai `stream=`:
  ```python
  a = im.split()[3].point(lambda v: int(v*0.10)); im.putalpha(a)
  hal.insert_image(rect, stream=PNG_BYTES, overlay=True)
  ```

**Hasil v2 terbukti**: "DEMO" muncul ✅ · logo samar ✅ · footer merah ✅ · 11 sumber berwarna tetap TERBACA ✅ · halaman 3→3 ✅.

## 🐛 BUG STABILO — SUDAH DIPERBAIKI (16 Okt, script Bos)

**Gejala:** stabilo hanya 2 dari 9 muncul di PDF.
**Akar (terukur, naskah BAB 2 Bos):** `generate_combined_pdf` mencari `chunk`
dengan `escaped_text.find(chunk_esc)` — TAPI `chunk` dibuat dari kalimat yang
sudah dibersihkan `' '.join(...)` (**tanpa baris baru**), sedangkan naskah asli
**punya `\n`** ⇒ `find()` = -1 ⇒ stabilo DILEWATI.

**Obat:** fungsi baru **`cari_chunk_tahan_spasi()`** di
`scripts/similarity_precheck.py` — normalisasi semua rentetan spasi jadi 1
spasi di kedua sisi + telusuri peta posisi. Dipasang di **2 tempat**
(baris ~510 dan ~697, dua-duanya dulu `find()` persis).

**Bukti:** sebelum `2/9` → sesudah **`9/9`** stabilo muncul ✅
Cadangan: `_arsip/pre-stabilo-20261016-042351/`.

## ⏳ SISA TERBUKA

- **Mesin pencari** (Bos: pakai API key) — penghalang utama sebelum fitur bisa dijual
- Angka jatah gratis (usul Wulan 2×/naskah/minggu) — belum diputuskan
- **DEMO di BELAKANG naskah** — belum beres (halaman PDF punya blok putih
  penutup; opsi: rakit ulang halaman / teks sangat pucat / taruh di footer)
- **Pintu fitur** (menu + rute `/plagiarisme` + layar + token 8) — BELUM dipasang
- Ringkas Memori (PENUH 3.998/4.000) ⇒ masukkan intisari berkas ini ke memori

## 🗂️ BERKAS UJI (jangan salah ambil)

| Berkas | Keadaan |
|--------|---------|
| `_buat_watermark_menyatu.py` | ✅ **BENAR** — pembuat gambar menyatu |
| `_tempel_watermark_menyatu.py` | ✅ **BENAR** — penempel ke PDF |
| `_sketsa/watermark-salah-20261016-044652/` | ❌ 6 skrip percobaan (v1–v5) — jangan dipakai |
