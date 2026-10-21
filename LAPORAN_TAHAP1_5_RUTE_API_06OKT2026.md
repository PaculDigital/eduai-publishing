# ✅ TAHAP 1 LANGKAH 5 — RUTE API + DOMPET TOKEN + UNDUH PDF (06 Okt 2026)

> Lanjutan izin Bos. Langkah 5 = **pintu API** fitur jurnal (6 rute).

---

## ✅ SELESAI & TERUJI

### 1. Berkas baru `app/rute_jurnal.py` (6 rute, prefix `/api/ai/v1/jurnal`)
| Rute | Guna | Tarif |
|---|---|---|
| `GET /lihat` | Daftar artikel + jatah | **GRATIS** |
| `POST /cari` | Pencarian **manual** user | 2× gratis/7hari, lalu **1 token** |
| `POST /cari-ai` | Pencarian **otomatis AI** | **GRATIS** (jatah manual tak terpakai) |
| `POST /tambah-manual` | Tempel DOI / kotak isian terkunci | gratis (batas **8*/bab) |
| `POST /hapus` | Buang 1 artikel | gratis |
| `POST /unduh` | PDF open-access → workspace | gratis |

### 2. `app/jurnal.py` — 3 fungsi tambahan
`data_kosong()` · `bab_terisi()` · `audit_isi_manual()` (audit DOI manual)

### 3. `app/pustaka.py` — **3 fungsi tambahan** (mesin, tidak diubah perilaku lama)
`link_garuda()` · `pdf_terbuka()` · `unduh_pdf()`
⇒ **Hanya open-access**: kalau bukan PDF → jawab jujur + beri **LINK**
(sesuai prinsip Bos: *"jangan download artikel, kasih daftar LINK"*).

### 4. `app/main.py` — rute didaftarkan (1 baris + 1 impor)

---

## 📊 BUKTI (bukan klaim)

| Gerbang | Kode benar | Dirusak |
|---|---|---|
| `_gerbang_jurnal.py` (kolom) | ✅ 21/0 | ✅ 3 GAGAL |
| `_gerbang_jurnal2.py` (modul) | ✅ 60/0 | ✅ 6 GAGAL |
| `_gerbang_jurnal3.py` (jembatan) | ✅ 53/0 | ✅ 8 GAGAL |
| `_gerbang_jatah.py` (jatah) | ✅ 42/0 | ✅ 15 GAGAL |
| **`_gerbang_rute_jurnal.py`** (API) | ✅ **62/0** | ✅ **7 & 14 GAGAL** |
| `scripts/periksa_kode.sh` | ✅ LULUS | — |
| **Rute di produksi** | ✅ **401** (pagar auth jalan) | — |

### Uji API **sungguhan** (FastAPI TestClient — rute, pagar, token benar-benar jalan)
```
LULUS  R2a tanpa login → ditolak (303)
LULUS  R3d lihat TIDAK memotong token
LULUS  R4c cari-ai TIDAK mencatat jatah manual
LULUS  R4e artikel AI tersimpan (asal=ai)
LULUS  R5d setelah jatah habis → token
LULUS  R6 0 hasil → token DIKEMBALIKAN
LULUS  R7d pesan hangat (tanpa kata keras)
LULUS  R8a tepat 8 artikel manual masuk
LULUS  R8b ke-9 ditolak
LULUS  R8e pesan hangat
LULUS  R9a tanpa DOI → TIDAK terverifikasi (user tak bisa akali)
LULUS  R10d siap dikirim ke bangun_isi (tanpa kunci internal)
LULUS  R12c pesan jujur + menawarkan tautan
LULUS  R13b rute TIDAK memanggil httpx langsung (lewat mesin)
LULUS  R14a potong token lewat kuota (satu pintu)
```

### Bukti pagar "user tidak bisa mengaku-aku terverifikasi"
```
LULUS  R9a tanpa DOI → TIDAK terverifikasi (user tak bisa akali)
```
Uji mengirim `doi_status='verified'` dari sisi user → **DITOLAK**; status
hanya datang dari audit mesin. ⇒ Pagar anti-halusinasi bekerja.

---

## 🚨 BUG NYATA YANG WULAN TEMUKAN & PERBAIKI (3 buah)

| # | Bug | Akar | Akibat kalau lolos |
|---|---|---|---|
| 1 | `AttributeError: 'int' has no attribute 'strip'` | Wulan panggil `.strip()` pada kolom **angka** (`year`) | **Rute tambah-manual 500** — fitur manual mati total |
| 2 | `AttributeError: 'list' has no attribute 'items'` | Rute kirim **list** ke `layak_sitasi()`, padahal minta **data** | **Rute lihat 500** — tab Referensi tak bisa dibuka |
| 3 | `TypeError: kembalikan_banyak() unexpected 'sumber'` | Wulan kirim parameter yang **tidak ada** (aslinya `jenis_addon`) | **Token TIDAK kembali** saat pencarian gagal — **user rugi token** |

⇒ Bug #3 paling berbahaya: kalau lolos, user **dibayar 1 token untuk pencarian
yang gagal**. Gerbang R6-lah yang menemukannya.

**Pelajaran:** ketiga bug tertangkap karena gerbang dijalankan **berurutan
sampai ulang** — bukan sekali jalan. Gerbang yang dijalankan 1× bisa lolos bug
yang muncul hanya saat ada sisa data.

---

## 🚨 PELAJARAN UJI (Wulan catat)

1. **Uji bergigi butuh `prompts/`** — salinan `/tmp` tanpa folder `prompts/`
   gagal (`FileNotFoundError`), bukan karena kode. ⇒ Salin `/app/app` +
   `/app/prompts` + `/app/data`.
2. **Jangan buang `stderr`** — Wulan sempat pakai `2>/dev/null` → output GAGAL
   hilang, hampir menyimpulkan "bergigi tidak jalan".
3. **Jalankan gerbang 2×** untuk mendeteksi bug sisa-data (bug #3 hanya muncul
   di jalan ke-2, karena data uji jalan ke-1 tertinggal).

---

## ⚠️ CATATAN JUJUR

1. **Belum ada UI** — rute API hidup, tapi **belum ada halaman** yang
   memanggilnya (tab Referensi = langkah berikutnya).
2. **Belum deploy ke image produksi** — masih `docker cp`. Menunggu izin Bos.
3. **`unduh_pdf()` belum diuji unduh nyata** — diuji bentuk balikannya
   (tanpa tautan → jawab jujur). Unduh nyata butuh URL PDF dari mesin, dan
   `pustaka.py` belum menyertakan `pdf_url` per artikel. ⇒ Perlu langkah
   tambahan kalau Bos mau unduh sungguhan.
4. **Uji bergigi di `/tmp`** — hanya untuk uji, bukan produksi.

---

## 📋 STATUS
- [x] Langkah 1: kolom + migrasi ✅ (21/0)
- [x] Langkah 2: `app/jurnal.py` ✅ (60/0)
- [x] Langkah 3: jembatan mesin ✅ (53/0)
- [x] Langkah 4: jatah 2×/7hari ✅ (42/0)
- [x] **Langkah 5: rute API 6 pintu ✅ (62/0, bergigi terbukti)**
- [ ] Langkah 6: UI tab Referensi (halaman HTML)
- [ ] Unduh PDF sungguhan (perlu `pdf_url` per artikel)
- [ ] Deploy (menunggu izin Bos)
