# ✅ BUKU JALUR LAYAR — TERBUKTI UTUH

> **Tanggal:** 20 Oktober 2026 · **Oleh:** Wulan
> **Putusan Bos:** A — uji layar → buktikan editor → bersihkan buku uji

## 🚨 AKAR BUG BESAR YANG DITEMUKAN (dan dibunuh)

**Gejala:** buku ditulis sempurna (2.078 + 2.155 kata, diagram Jev, tabel,
ilustrasi) lalu **dibuang** dengan pesan:
`RuntimeError: tidak satu pun berkas bab tersimpan`

**Akar** — `app/penyusunan_buku.py::susun()`:

```python
# SALAH (lama):
os.path.exists(os.path.join(keluar, b['file']))     # → …/bab1.txt
# padahal susun_buku() menyimpan di:
#                                     …/bab1/bab1.txt
```

`b['file']` cuma **NAMA**, bukan path. Pemeriksaan mencari di akar folder
buku ⇒ **tidak pernah ketemu** ⇒ buku yang sudah jadi dibuang, token
dikembalikan. **Salah ALAMAT, bukan mesin rusak.**

**Perbaikan** — `_path_bab()` coba **DALAM folder bab dulu**, lalu bentuk lama,
dan simpan `hasil['bab'][n]['path']` **LENGKAP** supaya pemanggil tidak menebak.

## 🧪 BUKTI (jalur layar sungguhan, DB salinan)

| Periksa | Hasil |
|---|---|
| BAB 1 | 2.372 kata, 10 sitasi |
| BAB 2 | 2.166 kata, 10 sitasi |
| Waktu | 556,6 detik (9,3 menit) |
| `.docx` | **3.096 KB** — dirakit & terdaftar (`file_id` terisi) |
| Gambar di `.docx` | **5** |
| Tabel di `.docx` | **6** |
| Paragraf | 115 · caption 8 |
| Diagram Jev | 3 PNG "ber-tahap dari jev", **0 gagal** |

**Semua media utama MASUK** (dibuktikan md5, bukan perkiraan):

```
MASUK  diagram_1.1.png      ← word/media/image2.png
MASUK  diagram_1.2.png      ← word/media/image3.png
MASUK  diagram_2.2.png      ← word/media/image5.png
MASUK  ilustrasi_bab1.png   ← word/media/image1.png
MASUK  ilustrasi_bab2.png   ← word/media/image4.png
TIDAK  ilustrasi_bab1_var1/2/3.png   ← BENAR (varian ekstra tak dipakai)
```

## 🎨 Isi diagram nyata (dibaca dari DALAM .docx)

**Diagram 1.1 — Perjalanan Matahari Sehari** (4 tahap dari Jev):
1. matahari tampak terbit di timur
2. naik makin tinggi di langit saat siang
3. turun dan terbenam di barat
4. bayangan tongkat berubah: panjang → pendek → panjang lagi

**Bukan** template KONSEP/IMPLEMENTASI.

## 🖥️ BUKTI EDITOR (OnlyOffice)

| Periksa | Hasil |
|---|---|
| `/edit/{fid}` | **200** |
| `api.js` | **200**, 65.363 byte, berisi `DocsAPI` |
| Konfigurasi `cfg` | `fileType: docx`, `mode: edit`, `key: e122v…`, `callbackUrl: /oo/simpan/…` |
| Judul tampil | "Ayo Mengenal Cuaca di Sekitar Kita.docx" |
| `/oo/unduh/<sha>` | **200**, 3.096 KB |
| md5 unduh vs disk | **SAMA** (`82aa2f1c35f9`) |
| **oo-converter ambil sendiri** | **200, 3.170.107 byte, header `PK`** |
| Callback simpan | **`{"error":0}`** |

`PK` = tanda .docx sah. Jadi server OnlyOffice benar-benar menerima dokumen
utuh, bukan halaman kosong.

## 🛡️ GERBANG BARU: `gerbang_jalur_buku.py`

**7 lulus / 0 gagal** — dan **BERGIGI**:
alamat lama dipulihkan ⇒ **7 dari 7 GAGAL**, pesan galat **sama persis**
dengan bug nyata.

Yang diperiksa: `susun()` selesai tanpa galat · bab dilaporkan ada · path ADA
di disk · path **di dalam** folder bab · isi = teks bab · `.docx` dirakit &
ada · jalur sukses tidak menyentuh pengembalian token.

## ⚠️ JEBAKAN YANG SUDAH KENA (jangan diulang)

1. **Suntikan uji lewat `python - <<PY` GAGAL SENYAP** — kutipnya kacau, kode
   tak berubah, jadi "uji bergigi" sebenarnya menguji kode ASLI. **Suntikan
   WAJIB berkas `.py` utuh**, dan harus MENOLAK jalan kalau pola tak ketemu.
2. **DB salinan lama tak punya tabel `files`** ⇒ siapkan salinan **SEGAR** dari
   `/app/data/eduai.db`. App produksi baca DB **PRODUKSI**, jadi `/edit/{fid}`
   balas 404 kalau berkas hanya didaftarkan di DB salinan.
3. **`/tmp` kosong setelah container diganti** ⇒ gerbang harus ada di proyek,
   bukan hanya di `/tmp`.
4. **Nama jenis buku**: yang sah `umum` / `anak` / `pendidikan` — BUKAN
   `buku-umum` (`outline_buku.BAB_PER_JENIS`).

## 🧹 PEMBERSIHAN

- Buku uji `fid 122` dihapus lewat **`cascade.hapus_berkas()`** (jalur resmi,
  bukan SQL mentah): baris DB hilang, berkas di disk hilang, 0 anak yatim.
- `/edit/122` → **404** (benar) · `/naskah` → **200**, nama "Cuaca" **tidak**
  muncul lagi.
- Folder buku uji yang GAGAL (`1792484509-5`) dibuang.

## 📌 STATUS AKHIR

| | |
|---|---|
| Image | `eduai-app:20261020_072903-sot` |
| Titik mundur | `eduai-app:cadangan-pra-gambar-jev` + backup DB |
| Gerbang | jalur buku **7/0** · cache Jev **13/0** · salinan mesin **26/0** |
| Kode proyek = container | **sha256 identik** (`d11de3aa5d16`) |
| Cache Jev | `/app/data/_jev_tahapan.json` (partisi tetap) |

## ⏳ BELUM

- **2 diagram bab 2 jatuh ke template** (naskah tak menulis daftar tahap jelas)
- **5 diagram template** di buku lama (2.1, 4.1, 4.3, 5.2, 6.1)
- Bentuk diagram masih **alur lurus**; siklus sebaiknya melingkar
- Biaya Jev 1 buku 6 bab: **12 panggilan, ≈Rp 4** (terukur, bukan perkiraan)
