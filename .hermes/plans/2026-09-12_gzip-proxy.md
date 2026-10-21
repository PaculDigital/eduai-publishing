# Perbaikan Gzip Proxy OnlyOffice — Implementation Plan

**Tanggal:** 12 Sep 2026
**Status:** 🔄 DIKERJAKAN
**Target:** Editor OnlyOffice termuat 5-8x lebih cepat (27,53 MB → 4,49 MB)

---

## 🎯 Masalah (TERBUKTI DENGAN PENGUKURAN)

Keluhan Bos: *"buka OnlyOffice berat sekali, loading lama."*

**Bos BENAR.** Ini bukti terukur (`scripts/bukti_gzip.py`, dijalankan di container):

| Jalur | Ukuran | Content-Encoding |
|---|---|---|
| A. Langsung ke OO, tanpa gzip | 27,53 MB | (tidak ada) |
| B. Langsung ke OO, **dengan gzip** | **4,49 MB** | ✅ gzip |
| C. **Lewat proxy EduAi** | **27,53 MB** | ❌ **TIDAK ADA** |

**Kesimpulan:** OnlyOffice SUDAH mengirim gzip (4,49 MB), tapi proxy EduAi
**membuang** header `Accept-Encoding` → OO kirim mentah → user terima 27,53 MB.

**Akar masalah:** `app/main.py` baris ~1010-1017, `httpx.request()` hanya
mengirim `User-Agent`, `Content-Type`, `X-Forwarded-*`. **`Accept-Encoding`
tidak diteruskan.**

---

## 📚 Dasar Resmi (bukan karangan)

1. **Repo resmi** `ONLYOFFICE/document-server-package` →
   `common/documentserver/nginx/includes/ds-docservice.conf.m4`
   → `gzip_static on;` (6 tempat)
2. **Config nyata container Bos** →
   `/etc/onlyoffice/documentserver/nginx/includes/ds-common.conf` baris 6-11:
   ```
   gzip on;
   gzip_vary on;
   gzip_min_length 1024;
   gzip_comp_level 5;
   gzip_types text/plain ...
   ```
3. **Dokumentasi resmi** api.onlyoffice.com → *Preloading static resources*
   + `Cache-Control: public, max-age=31536000, immutable`

**Artinya: gzip adalah cara RESMI OnlyOffice.** Kita hanya perlu
meneruskannya, bukan menambah mekanisme baru.

---

## 🔧 Perbaikan (SATU titik, 3 perubahan)

File: `app/main.py`, fungsi `oo_aset()` (baris ~959-1031)

### Perubahan 1 — Teruskan `Accept-Encoding` ke OO
```python
headers={'User-Agent': ...,
         'Accept-Encoding': req.headers.get('accept-encoding', 'gzip'),
         ...}
```

### Perubahan 2 — Minta httpx JANGAN dekompres ⚠️ PALING KRITIS
```python
r = httpx.request(..., headers={...})
# httpx otomatis dekompres kalau tidak dimatikan -> .content jadi 27 MB
# mengembang -> proxy kirim 27 MB lagi -> TIDAK ADA perbaikan!
```
Cara: kirim header `Accept-Encoding` + baca `r.content` **tanpa** dekompresi.
Di httpx: gunakan `httpx.Client()` dengan `headers` dan akses
`r.iter_raw()` / set `Accept-Encoding` manual + `.read()`.

### Perubahan 3 — Teruskan `Content-Encoding` + `Vary` ke browser
```python
hdr = {
    'Content-Encoding': r.headers.get('content-encoding', ''),
    'Vary': 'Cookie, Accept-Encoding',   # <- tambah Accept-Encoding
    'Cache-Control': 'private, max-age=3600',
}
```
**Kenapa `Content-Encoding` wajib:** browser harus tahu isinya terkompresi.
Tanpa itu, browser baca byte gzip sebagai JavaScript → syntax error.

---

## ✅ Uji (WAJIB, jangan lewat)

| # | Uji | Target |
|---|---|---|
| 1 | Ukur lewat proxy | **27,53 MB → ~4,49 MB** |
| 2 | Editor tetap JALAN | Dokumen termuat, bisa edit |
| 3 | WebSocket/socket.io | Tidak rusak (kolaborasi hidup) |
| 4 | Visual HP (CloakBrowser) | Editor siap jauh lebih cepat |
| 5 | Aset non-teks (gambar/font) | Tidak dirusak gzip |
| 6 | E2E transaksi QRIS | 68/68 masih LULUS |

---

## ⚠️ Jebakan (dari pengalaman)

1. **httpx auto-decompress** → perbaikan jadi nol. WAJIB dimatikan.
2. **`Content-Encoding` lupa diteruskan** → browser syntax error.
3. **`Vary` tidak diupdate** → Cloudflare cache respons gzip untuk browser
   yang tidak minta gzip (jarang, tapi bisa).
4. **Aset yang sudah terkompresi** (jpg/png/font) → jangan digzip ulang
   (pemborosan). OO sudah atur ini.
5. **WebSocket** → JANGAN digzip (protokolnya beda). Rute WS terpisah.

---

## 🚨 Aturan Deploy (PELAJARAN 12Sep26)

```
URUTAN WAJIB:  docker build  →  cek image ada  →  docker run
```
`scripts/jalankan.sh` **HANYA docker run**, TIDAK build.
Salah urutan = 502 + container hilang (pernah kejadian).

---

## 📋 Rollback

Kalau bermasalah, balik 3 baris di `oo_aset()`:
- Hapus `Accept-Encoding` dari headers
- Hapus `Content-Encoding` dari `hdr`
- Balik `Vary` jadi `'Cookie'`

Risiko **RENDAH** — perubahan terisolasi di satu fungsi.
