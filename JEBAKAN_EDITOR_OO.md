<!-- SOT: akar & cara cepat saat editor OnlyOffice nyangkut -->
# 🚨 JEBAKAN EDITOR ONLYOFFICE EDUAI — CATATAN AKAR & CARA CEPAT

**Dibuat:** 12 Okt 2026
**Untuk:** Bos + sesi Wulan berikutnya
**Status:** Sebagian beres (lihat bagian 5). Sisa 1 akar BELUM tuntas.
**Tujuan berkas ini:** kalau editor OO rusak lagi, **baca ini DULU** —
jangan menebak. Semua daftar di bawah SUDAH DIUKUR, bukan dugaan.

---

## 1. GEJALA YANG SERING MUNCUL

| Gejala di layar | Arti sebenarnya |
|---|---|
| Nyangkut "Naskahmu sedang disiapkan" (terus, tidak hilang) | Loading ditutup oleh event `onDocumentReady` dari OO. Event itu **tidak pernah datang**. |
| Modal "Unduhan gagal" (−4) | OO tidak bisa unduh `Editor.bin` dari app |
| Layar putih / editor kosong | Aset OO gagal dimuat |
| Berputar ~20-40 detik lalu **berhasil** | BUKAN rusak — cuma lambat (normal untuk dokumen besar) |

**PENTING — bedakan LAMBAT vs NYANGKUT:**
- **Lambat** = akhirnya terbuka. Ukur dengan jam, jangan dengan perasaan.
- **Nyangkut** = lebih dari ~3 menit tidak berubah. Baru itu rusak.

---

## 2. CARA UKUR YANG BENAR (JANGAN MENEBAK)

```bash
cd /opt/data/services/eduai-publishing
bash scripts/rawat_potret.sh --mulai          # Chrome CDP :9333
python3 _sketsa/ukur_load.py                  # ukur detik sampai loading hilang
```

`ukur_load.py` mengukur: **dari buka `/edit/9` → sampai `#memuat` hilang atau `#galat` muncul.** Itu satu-satunya ukuran jujur.

**Ukur 2×.** Kalau sekali berhasil sekali tidak = gejala **cache**, bukan bug kode.

---

## 3. 🔴 AKAR YANG SUDAH TERBUKTI (urut dari yang paling sering)

### AKAR A — Cache Cloudflare menyimpan aset OO (SUDAH DIBERESKAN 12Okt26)
- **Bukti:** `api.js` lewat Cloudflare = hash `fc076386` (umur **35.377 detik = 9,8 jam**), OO asli = `884b8d73`. `cf-cache-status: HIT`.
- **Sebab:** Cache Rule `eduai-aset-editor-cache` (dibuat 12Sep26) memakai `edge_ttl: override_origin` = **1 TAHUN**. Aturan itu **mengabaikan** `Cache-Control` dari app.
- **Kapan meledak:** setiap deploy/rebranding yang mengubah berkas di dalam `/oo/aset/` (mis. `api.js`, `About.js`, CSS).
- **⛔ JEBAKAN:** karena TTL 1 tahun, **perubahan TIDAK AKAN PERNAH terlihat** sampai di-purge. Ini bukan bug — ini harga dari `override_origin`.
- **💊 OBAT:** purge cache Cloudflare **setiap habis deploy** yang menyentuh `/oo/aset/`:
  ```bash
  python3 _sketsa/purge_cf_eduai.py
  ```
- **✅ CARA PASTIKAN BERES** (jangan cek status code — cek HASH):
  ```bash
  curl -s "https://eduai.bikinaja.id/oo/aset/web-apps/apps/api/documents/api.js?cb=$RANDOM" \
    | grep -oE '9\.4\.0-[a-f0-9]{8}' | sort -u
  # harus SAMA dengan OO asli:
  docker exec eduai-app curl -s http://oo-converter/web-apps/apps/api/documents/api.js \
    | grep -oE '9\.4\.0-[a-f0-9]{8}' | sort -u
  ```
  **Hash beda = cache basi. Status 200 di dua-duanya = TIDAK BISA dipakai sebagai bukti.**

### AKAR B — cookie kosong pada aset ❌ **HIPOTESIS SALAH (dibuktikan 12Okt26)**
- **Dugaan awal:** aset OO diminta dari dalam iframe = pihak-ketiga, cookie `samesite='lax'` tidak dikirim.
- **⛔ DIBUKTIKAN SALAH.** Uji terisolasi (`_sketsa/uji_samesite_isolasi.py`):
  ```
  asal permintaan aset (initiator) = https://eduai.bikinaja.id/edit/9   ← DOMAIN SAMA
                                     script                              ← dari dalam iframe
  ```
  Chrome **tidak** menganggapnya pihak-ketiga (dokumen & aset satu domain). Dua cookie uji
  (`SameSite=Lax` dan `SameSite=None`) **dua-duanya TIDAK ikut** ⇒ **bukan soal sameSite**.
- **Sebab sebenarnya cookie kosong di uji Wulan:** cookie yang disuntik lewat CDP
  (`Network.setCookie`) **tidak diteruskan Chrome** ke konteks iframe. Itu **keterbatasan
  ALAT UJI**, bukan bug aplikasi.
- **⚠️ PELAJARAN (jangan diulang):** JANGAN ubah `samesite` jadi `none` untuk "memperbaiki"
  ini — itu **menyentuh login SELURUH user** demi hipotesis yang sudah terbukti salah.
- **Cara uji yang BENAR ke depan:** login lewat **rute `/masuk` sungguhan** di browser
  (bukan suntik cookie lewat CDP), baru ukur.

### AKAR E — cookie sesi dari LOGIN lewat domain: BELUM TERBUKTI (sisa yang perlu diuji)
- Fakta: `POST /masuk` di produksi (uji sah) → **401**. Belum ada bukti bahwa
  **user yang benar-benar login** di produksi mendapat cookie yang diterima.
- **Yang perlu diuji (langkah berikutnya):** login sungguhan di browser lewat
  `https://eduai.bikinaja.id/masuk` dengan akun uji → buka `/edit/9` → lihat:
  (1) apakah tetap dilempar `/masuk`? (2) aset bawa cookie? (3) berapa detik load?
- **⛔ JANGAN ubah kode apa pun sebelum uji ini dijalankan.**

### AKAR C — Patch prefix hash (SALAH ARAH, sudah DICABUT)
- Wulan sempat memasang patch yang **membuang prefix hash** dari path aset. **Patch itu salah** dan malah **membuat loop 302** (app mengalihkan path ke dirinya sendiri).
- **⛔ JANGAN PASANG LAGI.** OO **butuh** prefix hash — itu mekanisme cache-busting resmi OO.
- **Sudah dicabut.** Kode sekarang: `url = f'{OO_URL}/{sisa}'`.

### AKAR D — `uvicorn --proxy-headers` (SELESAI 12Okt26)
- `--proxy-headers` menimpa skema jadi `https` dari tunnel → OO minta `Editor.bin` via https padahal port http → `ERR_SSL_PROTOCOL_ERROR` → modal **−4 "Unduhan gagal"**.
- **💊 OBAT yang DIPAKAI:** skema WS diambil dari header **`Origin`** browser (bukan dari forwarded).

---

## 4. ⛔ DAFTAR "JANGAN ULANGI" (semua ini sudah dicoba & GAGAL/menyesatkan)

1. **Jangan** buang prefix hash `/9.4.0-<hash>/` dari path aset. OO butuh itu.
2. **Jangan** pakai `X-Forwarded-Prefix`. Dokumen resmi OO pakai `X-Forwarded-Host` yang berisi prefix (`host/prefix`).
3. **Jangan** cek "sudah beres atau belum" pakai status code HTTP. Dua versi (basi vs baru) **dua-duanya balas 200**. Bandingkan **HASH atau UKURAN**.
4. **Jangan** pakai `curl` dari host Hermes untuk menguji hal yang butuh login — bisa 403 dari Cloudflare WAF, dan itu **bukan** bukti cache/rusak.
5. **Jangan** menuduh kode app dulu. **Cek `cf-cache-status` + `age` DULU.**
6. **Jangan** pakai berkas uji Wulan sendiri sebagai bukti (hash `fc076386` pernah Wulan kejar berjam-jam — ternyata itu hash di **berkas uji Wulan sendiri**, bukan dari sistem).
7. **Jangan** percaya hasil `docker logs` kalau berkas uji hilang saat container di-recreate — `docker cp` ulang tiap kali.
8. **Jangan** uji pakai `TestClient` pada DB produksi.

---

## 5. STATUS SESUAI 12 Okt 2026

| Bagian | Status | Bukti |
|---|---|---|
| Aset OO (JS/CSS/sdkjs) dimuat | ✅ SEHAT | Semua 200, hash `884b8d73` cocok dengan OO |
| Loop 302 | ✅ HILANG | ber-hash → 200; no-hash → 302 sekali (normal) |
| Cache Cloudflare | ✅ DI-PURGE | `cf-cache-status: MISS`, hash benar |
| WebSocket `/oo/aset` **dengan cookie** | ✅ TERSAMBUNG | `101 Switching Protocols` |
| Patch resmi OO (`X-Forwarded-Host`) | ✅ TER-DEPLOY | — |
| **Editor PRODUKSI terbuka** | ⚠️ **SEBAGIAN** | `_sketsa/uji_samesite_isolasi.py`: 194 permintaan aset, iframe hidup, judul naskah terbaca — tapi cookie sesi tidak diteruskan di alat uji CDP |
| Editor LOKAL terbuka | ✅ HIDUP | `Editor.bin` 200 OK, dokumen tampil |

**Kesimpulan jujur:** OnlyOffice **TIDAK rusak** dan **TIDAK pernah salah dikonfigurasi**.
Yang bermasalah = **jalur pengiriman di depannya** (cache Cloudflare + cookie lintas-iframe).
Akar A sudah dicabut. **Akar B belum.**

---

## 6. URUTAN DIAGNOSA CEPAT (kalau editor rusak lagi — IKUTI URUTAN INI)

```
1. Ukur: python3 _sketsa/ukur_load.py            → lambat atau nyangkut?
2. Cek cache: bandingkan HASH api.js lewat CF vs OO asli
   → BEDA  => purge CF, selesai
   → SAMA  => lanjut
3. Cek aset masuk: docker logs eduai-app --since 5m | grep oo/aset | wc -l
   → 0     => masalah di DEPAN app (Cloudflare/redirect), bukan app
   → banyak=> lanjut
4. Cek cookie: python3 _sketsa/lacak_cookie.py   → aset bawa cookie?
   → KOSONG=> Akar B (sameSite lintas-iframe)
5. Cek WS: python3 _sketsa/uji_ws_cookie.py      → 101 atau 403?
6. Baru periksa kode app.
```

**Aturan emas:** kalau `/edit/9` MASUK ke app tapi `/oo/aset/*` **0 permintaan**,
berarti masalahnya **di depan app** — jangan ngoprek kode app.

---

## 6b. ⚠️ PELAJARAN UJI (WAJIB DIBACA — ini yang bikin lambat 12Okt26)

1. **Cookie yang disuntik lewat CDP (`Network.setCookie`) TIDAK diteruskan Chrome ke
   konteks iframe.** Akibatnya uji selalu melihat "cookie kosong" walau app benar.
   ⇒ **JANGAN pernah menyimpulkan app rusak dari gejala ini.** Login lewat `/masuk`
   sungguhan di browser, baru ukur.
2. **`httpOnly: True` di `Network.setCookie` → Chrome menolak menyimpan.** Gejalanya
   halaman langsung dilempar ke `/masuk`. Itu **bukan** bukti pagar app rusak.
3. **Selalu uji HIPOTESIS dulu, jangan langsung patch.** 12Okt26 Wulan hampir mengubah
   `samesite` cookie (menyentuh login SELURUH user) atas hipotesis yang **terbukti salah**
   setelah diuji terisolasi. Uji terisolasi memakan ~5 menit; patch salah bisa mematikan
   login semua user.
4. **Jangan sebut "cookie tidak ikut = pihak-ketiga"** sebelum mencetak
   `initiator.url`. Terbukti aset diminta dari `/edit/9` = **domain SAMA**.

## 7. BERKAS RUJUKAN SESI INI

| Berkas | Guna |
|---|---|
| `_sketsa/ukur_load.py` | **Ukur berapa detik** editor terbuka (2×) |
| `_sketsa/purge_cf_eduai.py` | Purge cache Cloudflare zona bikinaja.id |
| `_sketsa/lacak_cookie.py` | Lacak cookie + redirect per permintaan (⚠️ lihat pelajaran 6b) |
| `_sketsa/uji_samesite_isolasi.py` | Uji terisolasi Lax vs None + asal permintaan aset |
| `_sketsa/uji_ws_cookie.py` | Uji WS dengan/tanpa cookie |
| `_sketsa/diag_api_js.py` | Cek api.js termuat, DocsAPI ada, aset gagal |
| `_sketsa/isi_iframe_produksi.py` | Baca ISI iframe OO |
| `scripts/rawat_potret.sh --mulai` | Nyalakan Chrome CDP :9333 |
| `scripts/perbaiki_oo.sh` | WAJIB tiap `oo-converter` restart |
