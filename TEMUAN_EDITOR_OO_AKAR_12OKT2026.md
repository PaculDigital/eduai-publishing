<!-- SOT: AKAR BUG EDITOR ONLYOFFICE -4 "Unduhan gagal" — TERUKUR 11-12 Okt 2026 -->
# 🔴 AKAR BUG EDITOR ONLYOFFICE `-4 "Unduhan gagal"` — TERUKUR 11-12 Okt 2026

> Ditulis dari BUKTI TERUKUR (log + body callback asli + potret + mata), BUKAN dugaan.
> Dugaan lama di FLAG ("cache OO menyimpan galat lama") **TERBUKTI SALAH** —
> cache sudah dihapus, modal −4 TETAP muncul.

## Kalimat singkat akarnya (1 kalimat)

**OnlyOffice melaporkan `-4 "Unduhan gagal"` PADAHAL unduhan SUKSES 200 OK —
yang gagal adalah callback SIMPAN: app membalas `{"error":0}` untuk `status:1`,
dan OO menerjemahkan balasan itu menjadi galat −4 yang menyesatkan user.**

## Bukti terukur (semua dari sistem hidup)

### 1. Unduhan SEHAT (bukan masalah jaringan/URL) ✅
```
dari dalam eduai-app   : GET /oo/unduh/<token> → HTTP 200, 590.578 byte, isi "PK" (docx sah)
dari oo-converter (publik)  : GET https://eduai.bikinaja.id/oo/unduh/<token> → HTTP 200, 590.578 byte
dari oo-converter (internal): GET http://eduai-app:8000/oo/unduh/<token> → HTTP 200, 590.578 byte
log app: "GET /oo/unduh/22bd1d… HTTP/1.1" 200 OK  (dipanggil dari 172.20.0.2 = oo-converter)
```
⇒ Rute `/oo/unduh` (`main.py:2695`) **SEHAT**. Token benar (`_token_berkas(9,3)`).
Token SALAH → 403 (pagarnya bekerja).

### 2. Cache OO BUKAN penyebab — dugaan lama GUGUR ❌
Cache `e9v1789405536` (1,1 MB, `Editor.bin` + media) **dihapus** → buka `/edit/9` lagi
→ **modal −4 TETAP muncul**. Jadi hipotesis *"OnlyOffice menyimpan galat lama per
document key"* **SALAH** — jangan diulang.

### 3. Callback SIMPAN = akar sebenarnya ✅
Rekam body asli yang OO kirim ke `/oo/simpan/<token>` (patch perekam sementara):
```json
{"key":"e9v1789405536","status":1,"users":["3"],"actions":[{"type":1,"userid":"3"}],"token":"..."}
```
⚠️ **TIDAK ADA field `url`.** Hanya `status: 1` (= user sedang mengedit).

Uji balasan app untuk tiap status (permintaan tiruan):
```
status 1 → HTTP 200 {"error":0}     ← OO baca ini sebagai GALAT "Unduhan gagal"
status 2 → HTTP 200 {"error":1}     ← karena `url` tidak ada (body tiruan)
status 6 → HTTP 200 {"error":1}
```
⇒ Perilaku OO: **callback pertama = `status:1` (aksi `type:1` = connect)** dan
balasan `error:0` dari app **memicu** OO menampilkan −4 *"Unduhan gagal"*.
Pesan −4 itu milik app (`#galat` di `editor.html`), dipicu event OO.

### 4. Lapis-2 penguncian BUKAN penyebab (dibuktikan) ✅
`yang_sedang_jalan(db, 3)` → **0 proses** (semua `selesai`/`gagal`, tidak ada
`menunggu`/`jalan`). Jadi jalur `if _jalan: return {'error':-4}` (`main.py:2827`)
**tidak aktif** — meski kodenya memang salah kaprah (lihat di bawah).

## 🐛 DUA MASALAH NYATA yang ditemukan

### Masalah A — `error:0` salah arti untuk callback `status:1`
`main.py:2798`:
```python
if not aksi['harus_simpan']:
    # status 1 = sedang diedit; status 4 = ditutup tanpa perubahan.
    return JSONResponse({'error': 0})
```
OnlyOffice **memakai `error:0` pada callback `status:1` sebagai penanda GAGAL**
(bukan "tidak ada yang perlu dikerjakan"), sehingga editor menampilkan
−4 *"Unduhan gagal"*. Perlu diperiksa balasan yang benar untuk aksi
connect/`type:1` (rujukan resmi OO: `{"error":0}` hanya sah untuk callback
yang diselesaikan, sedangkan untuk `status:1` OO tidak butuh `url`).

### Masalah B — `error:-4` sebagai "pesan ramah" itu MENYESATKAN
`main.py:2827` (Lapis-2 penguncian) sengaja membalas `{'error': -4}` dengan
alasan *"supaya user tidak melihat editor error mentah"*. **Akibatnya user
melihat `-4 "Unduhan gagal"` — pesan yang salah total** (unduhan sehat; yang
ditolak itu SIMPAN karena AI sedang jalan). Niatnya baik, hasilnya menyesatkan.
⇒ Perlu dipilih kode/pesan yang benar.

## ⚠️ JEBAKAN UJI (jangan ulang)
1. **User 7 TIDAK ADA di DB** (`users` = 3, 5, 8, 9) ⇒ token user 7 selalu
   ditolak ⇒ semua uji editor jadi **GAGAL PALSU** (halaman jadi `/masuk`).
   Uji `/edit/9` WAJIB pakai **user 3** (pemilik fid 9).
2. **`/mulai` atau `/edit/…` tanpa login = halaman MASUK.** Selalu cetak
   `document.title` untuk memastikan halaman yang diuji BENAR.
3. `PUT /json/close/<id>` balas **isi kosong** ⇒ `json.loads('')` meledak.
4. Kerangka uji editor SIAP PAKAI: `_sketsa/uji_editor_oo.py`
   (set cookie via CDP → buka `/edit/9` → tunggu 60 dtk → lapor modal + PNG).

## Berkas terkait
- `app/main.py:2262` `url_unduh_publik` (`PUBLIC_BASE_URL` = https) — pemetaan lama: browser butuh HTTPS, server butuh internal.
- `app/main.py:2695` rute `/oo/unduh` (`FileResponse`) — **SEHAT**.
- `app/main.py:2789` rute `/oo/simpan` — **DI SINI masalahnya** (`error:0` & `error:-4`).
- `app/onlyoffice.py:190` `parse_callback()` — `harus_simpan` = status 2/6.
- `app/onlyoffice.py:211` catatan bug resmi OO #2822 (`{"error":1}` untuk forcesave).
- `app/templates/editor.html:490` `#galat` / `#galat-pesan` — modal −4 milik app.
- Bukti: `_sketsa/editor-oo.png` (potret layar galat, MATA memverifikasi).
