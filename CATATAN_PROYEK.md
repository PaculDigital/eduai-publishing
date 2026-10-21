# EDUAI PUBLISHING — Catatan Proyek (11-12 Sep 2026)

> 🚨 **3 Okt 2026 — ATURAN KERAS: BATAS PROYEK (PELANGGARAN & PERBAIKAN).**
> Bos (VERBATIM): *"Perbaiki kesalahan yang mengarah ke ojs padahal jelas jelas
> kita project eduai… Jika perlu berhubungan dengan cf, buat sendiri di eduai.
> Jangan pakai project lain untuk mengukur, menganalisa itu salah!!"*
> **Kejadian:** Wulan memakai **token Cloudflare milik proyek OJS**
> (`services/ojs/.cloudflare.json`) untuk membaca aturan cache CF — karena
> `.env` EduAi tidak punya token CF. Bos menegur: itu **BAHAYA** (bisa merusak
> produksi OJS tanpa jejak).
> **ATURAN:** SATU PROYEK = SATU DUNIA. Kerja EduAi → HANYA folder
> `services/eduai-publishing/` + container `eduai-app`/`oo-converter` + domain
> `eduai.bikinaja.id`. **DILARANG** pakai kredensial/token/`.env`/berkas proyek
> lain. Butuh kredensial → **BUAT SENDIRI** di EduAi. Tidak punya akses →
> **BERHENTI + TANYA BOS**. Domain sama ≠ proyek sama.
> **Perbaikan:** skrip salah `_sketsa/baca_aturan_cf.py` **DIHAPUS** · dipindai =
> tidak ada berkas EduAi lain menunjuk proyek lain · **BACA:
> `ATURAN_BATAS_PROYEK_03OKT2026.md`**.
> Dampak: hanya baca (GET), tidak ada perubahan setting — kerusakan NOL, tapi
> risiko nyata.

> 🔑 **3 Okt 2026 — PEMBIMBING AI + NASKAH RINGAN + LAYAR TUNGGU (DEPLOY ✅).**
> Tiga hal LIVE di `eduai-app:20261003_044420-sot` (mundur `cadangan-pra-sot`):
> **(1) Pembimbing TANPA AKUN** kini BISA buka naskah (mode baca + komentar)
> lewat **kunci cookie** `app/kunci_tinjau.py` — kanal dokumen OO
> (`/oo/aset/.../doc/<KEY>/c/`) sebelumnya dipagari login ⇒ editor cuma skeleton.
> **(2) Naskah diringankan saat unggah** (`app/ringankan.py`):
> **5,08 MB → 1,69 MB (−67%)**, HANYA gambar; teks/tabel/layout terbukti
> **tidak berubah** (ukuran gambar di .docx = cm, bukan px).
> **(3) Layar tunggu bermerek EduAi + logo** (bukan skeleton abu-abu), beban NOL.
> **Baca: `DOKUMENTASI_PEMBIMBING_AI_03OKT2026.md`** +
> `FLAG_LANJUT_DISINI.md` (blok 🔑 paling atas).
> ⚠️ Sejak sekarang **DILARANG `docker cp app/...`** — ubah kode WAJIB
> `edit source → bash jalankan.sh` (kalau tidak → "image bohong", hilang saat restart).
> SISA: uji tombol "Periksa dengan AI" + `/daftar?dari=`.

> 🟢 **25 Sep 2026 — BOTTLE NECK ANTREAN DITUTUP & DEPLOY SUKSES.**
> Kenapa revisi lama sekali (420-460 dtk)? **PROSES HANTU menahan slot antrean**
> — BUKAN model, BUKAN 9router. Sesudah obat: E2E domain **31 dtk**.
> Baca: `DOKUMENTASI_ANTREAN_BOTTLENECK_HANTU_25SEP2026.md` +
> `FLAG_LANJUT_DISINI.md` (blok 🟢 paling atas).
> Periksa kapan saja: `bash scripts/periksa_antrean.sh [--bersihkan]`.

> 🌿 **24 Sep 2026 — BACA `PETA_PERCABANGAN_24SEP2026.md` LEBIH DULU.**
> Bos minta progress bercabang dicatat agar SOT tetap sah. Peta itu memuat:
> apa yang selesai (14), **7 cabang menggantung (C1–C7)**, apa yang belum
> dibangun, dan cara membuktikan tiap baris. Penjaga otomatis:
> `bash scripts/periksa_percabangan.sh` (14 asersi, terbukti bergigi).


## Identitas
- **Nama**: EduAi Publishing
- **Domain**: `eduai.bikinaja.id` (portal) + `oo.bikinaja.id` (OnlyOffice, **tertutup**)
- **Fungsi**: Portal dokumen client (ala Google Drive) self-hosted
- **Pemilik**: Bos (Jizenji T Wirastomo / PaculDigital)
- **Tujuan**: Meninggalkan Google Drive & Word (beban OAuth)

## Model Bisnis (ACC Bos 11Sep26)
| Paket | Kuota | Harga |
|---|---|---|
| Gratis | 30 MB | Rp 0 |
| Paket 1 | 100 MB | Rp 50.000 |
| Paket 2 | 300 MB | Rp 100.000 |
| Paket 3 | 1 GB | Rp 300.000 |

- Pembayaran: **Pakasir QRIS** (project `wa-marketing`, masih **sandbox**)
- Top-up otomatis via polling 5 detik (webhook belum diuji)

## Arsitektur (terverifikasi 12Sep26)
- Container **sendiri** (steril dari project lain) — sesuai aturan Bos
- Database: SQLite
- Editor: **OnlyOffice DocumentServer** (`oo-converter`)
- Storage: disk server (+ opsi backup R2)
- **TIDAK ada `docker compose`** di server ini → semua `docker run` via skrip

### Topologi
```
eduai.bikinaja.id  -> tunnel -> localhost:8100 -> eduai-app:8000 (172.17.0.8)
oo.bikinaja.id     -> tunnel -> localhost:18081 -> oo-converter:80 (172.17.0.7)
                                  + Cloudflare Access (manusia DITOLAK)
```

### Alur aset editor (PENTING)
```
Browser --/oo/aset/...--> eduai-app --+service token--> oo.bikinaja.id
                         (bawa X-Forwarded-Proto/Host/Prefix)
```
Service token Cloudflare Access **TIDAK PERNAH sampai browser**.

---

## ⚠️ PELAJARAN PENTING — WAJIB DIBACA

### 1. JWT OnlyOffice: WAJIB set env, kalau tidak akan ganti tiap restart
Skrip resmi `run-document-server.sh` baris 121:
```
JWT_SECRET=${JWT_SECRET:-$(pwgen -s 32)}
```
Tanpa env → **secret acak baru tiap container nyala** → editor MATI DIAM-DIAM.
**SOLUSI:** `bash scripts/jalankan_oo.sh` (kirim `JWT_SECRET` dari `.jwt_oo_secret`).

### 2. Tunnel JANGAN pakai IP container — IP BERUBAH
IP container berubah saat dibuat ulang (172.17.0.9 → 172.17.0.8 → **502**).
**PAKAI `localhost:<port-host>`** yang tidak berubah.

### 3. Setelan nginx di DALAM oo-converter HILANG saat container dibuat ulang
CORS, tutup endpoint, header WebSocket — semua di `/etc/nginx/includes/`.
**SOLUSI:** `bash scripts/jalankan_oo.sh` (otomatis panggil `perbaiki_oo.sh`).

### 4. `@app.get` + `@app.websocket` digabung = `Depends` DILUPAKAN
Aset editor jadi terbuka publik walau ada `wajib_login`. **PISAHKAN rutenya.**

### 5. socket.io butuh POST — bukan cuma GET
Rute proxy WAJIB `@app.api_route(methods=['GET','POST',...])` + `async def`.
Kalau cuma `@app.get`: GET 200, POST **405** → editor tampil tapi TIDAK bisa edit.
Fungsi harus **`async`** karena `await req.body()`.

### 6. `Cache-Control: public` di Cloudflare menyembunyikan bug
Cloudflare menyimpan halaman login 24 jam → aset "terbuka" padahal bukan.
**Pakai `private, max-age=3600` + `Vary: Cookie`.**

### 7. WebSocket proxy Python = titik rapuh
Lebih baik teruskan lewat **nginx** (native). Proxy Python menambah 1 jembatan.

### 8. `docker kill` ≠ crash — restart policy TIDAK berlaku
`docker stop`/`kill` = stop manual → `unless-stopped` hormati niat admin.
Uji benar: bunuh proses **di dalam** container.

### 9. OnlyOffice butuh header `Upgrade`/`Connection` di nginx
Tanpa itu → socket.io gagal naik WebSocket (walaupun ada fallback polling).

### 10. Verifikasi definisi variabel, bukan cuma pemakaian
`'HEADER_ACCESS' in src` = True karena **dipakai**, padahal **tidak didefinisikan**
→ `NameError` saat runtime. Cek `'HEADER_ACCESS = {}' in src`.

### 11. 🔴 WAJIB kirim `X-Forwarded-Proto`/`-Host`/`-Prefix` ke OnlyOffice
**Sumber:** dokumentasi + community resmi OnlyOffice (thread #13150).
**Gejala tanpa header ini:** editor TAMPIL (toolbar ada) tapi
`DocumentInfo: no logic document`, canvas kosong, **dokumen tidak termuat**.

OnlyOffice menghitung skema URL aset dari header ini. Lihat
`/etc/onlyoffice/documentserver/nginx/includes/http-common.conf`:
```nginx
map $http_cloudfront_forwarded_proto:$http_x_forwarded_proto $the_scheme {
     default $scheme;                      # <-- tanpa header = http!
     "~^:https?$" $http_x_forwarded_proto;
}
map $http_x_forwarded_prefix $the_prefix { default $http_x_forwarded_prefix; }
```
- Tanpa `X-Forwarded-Proto: https` → URL aset ber-skema **http** → browser
  **BLOKIR Mixed Content** → aset tidak termuat.
- Tanpa `X-Forwarded-Prefix: /oo/aset` → URL aset **kehilangan prefix**
  (`/cache/files/...` bukan `/oo/aset/cache/files/...`) → **404**.

**FIX (terpasang di `app/main.py`, 2 tempat: proxy HTTP + proxy WebSocket):**
```python
headers={'X-Forwarded-Proto': 'https',
         'X-Forwarded-Host': host_publik,
         'X-Forwarded-Prefix': '/oo/aset', ...}
```

### 12. 🔴 DUA SECRET secure_link HARUS SAMA (ini bikin 403)
OnlyOffice hitung `md5` untuk URL `/cache/files/...` pakai `storage.fs.secretString`
(di `local.json`). nginx verifikasi pakai `$secure_link_secret` (di `ds.conf`).
**Kalau BEDA → SELALU 403** → `Editor.bin` tidak bisa diambil → dokumen gagal render.

Cek:
```bash
docker exec oo-converter sh -c "grep -oP 'secure_link_secret \K[A-Za-z0-9]+' /etc/nginx/conf.d/ds.conf"
docker exec oo-converter sh -c "grep -oP 'secretString\"\s*:\s*\"\K[^\"]+' /etc/onlyoffice/documentserver/local.json"
```

**JEBAKAN:** skrip resmi `/usr/bin/documentserver-update-securelink.sh` menulis ke
**`/etc/onlyoffice/documentserver/nginx/ds.conf` (TEMPLATE)**, padahal nginx
membaca **`/etc/nginx/conf.d/ds.conf` (AKTIF)** → skrip resmi **TIDAK EFEKTIF**.

**FIX:** samakan manual ke file AKTIF:
```bash
SECRET="<nilai dari local.json>"
docker exec oo-converter sh -c "sed -i 's|set \$secure_link_secret .*|set \$secure_link_secret ${SECRET};|' /etc/nginx/conf.d/ds.conf"
docker exec oo-converter sh -c "supervisorctl restart ds:docservice ds:converter; nginx -s reload"
```

### 13. HTTP 403 dari WebSocket = nama cookie SALAH
WebSocket **tidak bisa pakai `Depends(wajib_login)`** → validasi cookie manual.
Kalau nama cookie salah (`'sesi'` alih-alih `SESSION_COOKIE='eduai_session'`),
**SEMUA** WebSocket ditolak 403 → socket.io tak tersambung → `no logic document`.
Cek: `ws.cookies.get(SESSION_COOKIE)` — **jangan** string literal.

### 10. Batas JUMLAH berkas ≠ batas KUOTA (MB)
Batas MB saja tidak cukup: user bisa unggah ratusan berkas KEcil sehingga
inode disk penuh walau kuota MB masih sisa. Batasi juga JUMLAH berkas
(`MAX_FILE_USER`, default 50). Cek pakai `SELECT COUNT(*)` sebelum simpan.

### 11. `DateTime` tanpa `timezone=True` -> TypeError saat hitung selisih
SQLite mengembalikan datetime **NAIVE**. `datetime.now(timezone.utc) - nilai_naive`
melempar `can't subtract offset-naive and offset-aware datetimes`.
Selalu pakai `DateTime(timezone=True)` **dan** helper `_sadar()` yang
menambahkan `tzinfo=UTC` kalau kosong (bug 12Sep26).

### 12. `pagehide` + `sendBeacon` SALAH untuk menutup sesi
Percobaan pertama: editor kirim `sendBeacon('/api/sesi/tutup')` saat
`pagehide`. Akibatnya setiap kali user **pindah dokumen**, sesi lama ikut
tertutup -> batas 3 dokumen tidak pernah tercapai (selalu tersisa 1).
Penutupan sesi hanya lewat tombol (disengaja) atau pembersihan otomatis
sesi basi setelah `SESI_IDLE_MENIT`.

### 13. `forcesave` error 1 & 4 = JANGAN dianggap gagal (bug resmi #2822)
OnlyOffice sering jawab `{"error":1}` ("dokumen tidak ditemukan") padahal
dokumen ADA dan callback status 6 TETAP datang.
Sumber: https://github.com/ONLYOFFICE/DocumentServer/issues/2822
Reproduksi di issue: request `{"error":1}` -> callback `{"status":6}` ✅.
Juga `error 4` = dokumen sudah tidak ada di server (sesi hantu / OO restart)
-> tidak ada yang bisa disimpan, jadi sesi kita BOLEH ditutup.
Kalau keduanya dianggap gagal, user TIDAK PERNAH bisa menutup dokumen.

### 14. Bersihkan sesi "hantu" sebelum uji
Kalau uji berhenti di tengah, baris `sesi_edit` tertinggal dan menahan
kuota -> uji berikutnya **palsu-gagal** (dokumen ditolak bukan karena bug).
Pakai `scripts/bersihkan_sesi.sh` (hapus langsung dari DB) di awal uji.

### 15. `page.on('response')` TIDAK menangkap request dari iframe
Untuk melacak request editor (di dalam cross-origin iframe), **pakai CDP**:
`page.context.new_cdp_session(page)` + `Network.enable` +
`cdp.on('Network.responseReceived', ...)`.

### 7. Jangan periksa elemen sebelum editor SIAP
Memeriksa `iframe[src*='documenteditor']` terlalu awal menghasilkan
`canvas=0` (salah baca). Tunggu **adaptif** sampai `logicDoc=True`.

### 8. 🔴 JANGAN hapus folder aset sebelum cek Dockerfile & CSS
Pelajaran 12Sep26 saat cleanup:
- **Dockerfile** masih `COPY assets/logo-asli.png ...` padahal folder `assets/`
  dihapus → **build GAGAL**: `file not found in build context`.
  **Cek dulu:** `grep -n "COPY" Dockerfile`
- **CSS** `app/static/eduai.css` merujuk `url('/assets/hero-bg.svg')` tapi CSS
  disajikan dari `/static/` → **404 permanen** (bug lama, ketemu saat cleanup).
  **Cek dulu:** `grep -rn "/assets/" app/templates/ app/static/`
- **Verifikasi akhir WAJIB di browser** (bukan cuma `curl`): rekam respons >=400
  dan periksa `img.complete && img.naturalWidth > 0`.

### 9. 🔴 Cloudflare cache 4 jam menyembunyikan perbaikan CSS/aset
`cf-cache-status: HIT` + `cache-control: max-age=14400` → file yang SUDAH
diperbaiki di server tetap disajikan **versi lama** ke browser.
**FIX:** purge cache per-file:
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZID/purge_cache" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  --data '{"files":["https://eduai.bikinaja.id/static/eduai.css"]}'
```
Bedakan: **file di container** sudah benar ≠ **yang diterima browser** benar.

---

## 🔒 Keamanan (terverifikasi 12Sep26)

| Endpoint | Status |
|---|---|
| `oo.bikinaja.id` (semua) | **403** (Cloudflare Access) ✅ |
| `oo.bikinaja.id` + service token | **200** ✅ |
| `oo.bikinaja.id` + token palsu | **403** ✅ |
| `/welcome/`, `/healthcheck`, `/info/info.json` | **403** ✅ |
| `api.js` (via proxy, tanpa login) | **303 → login** ✅ |
| `/oo/unduh/*` (dokumen client) | **403** ✅ |
| `/docs`, `/openapi.json`, `/redoc` | **404** ✅ |
| `ConvertService.ashx` tanpa token | HTTP 200 + **error di body** (JWT lindungi) ✅ |

- **Cloudflare Access**: app `cf6f906c-a055-4535-a2c8-8601792a95ef`, policy
  `non_identity` (service token saja)
- Service token: `EDUAI_OO_CF_ACCESS_ID` + `EDUAI_OO_CF_ACCESS_SECRET` di `.env` (600)
- **Service token TIDAK pernah sampai browser** — proxy server yang bawa

---

## 📜 Skrip

### Produksi (dipakai sehari-hari)
| Skrip | Fungsi |
|---|---|
| `scripts/jalankan.sh` | jalankan `eduai-app` |
| `scripts/jalankan_oo.sh` | jalankan `oo-converter` (**JWT permanen** + auto-perbaiki nginx) |
| `scripts/jalankan_oo.sh --status` | cek JWT permanen |
| `scripts/perbaiki_oo.sh` | pulihkan setelan nginx OO (idempoten) |
| `scripts/perbaiki_oo.sh --cek` | cek tanpa ubah |
| `scripts/pasang_access.py` | pasang Cloudflare Access (idempoten) |
| `scripts/pasang_tunnel.py` | pasang DNS + tunnel |

### Uji
| Skrip | Fungsi | Hasil |
|---|---|---|
| `scripts/uji_access.py` | uji Cloudflare Access | **3/3** ✅ |
| `scripts/uji_bencana.sh` | 6 skenario bencana | **6/6** ✅ |
| `scripts/uji_keamanan_lengkap.py` | uji keamanan menyeluruh | LULUS ✅ |
| `scripts/uji_qris.py` | uji QRIS Pakasir | **13/13** ✅ |
| `scripts/uji_oo_proxy.py` | uji aset editor lewat proxy | **7/7** ✅ |
| `scripts/cek_websocket.py` | cek kanal WebSocket | ✅ |

### Diagnosa editor (setelah cleanup 12Sep26)
| Skrip | Fungsi |
|---|---|
| `scripts/diagnosa_adaptif.py` | **UTAMA** — pantau pemuatan dokumen sampai `logicDoc=True` |
| `scripts/lacak_cdp.py` | rekam SEMUA request (termasuk iframe) via CDP |
| `scripts/cek_cepat.sh` | **6 titik cek** dalam satu perintah (container, secure_link, JWT, WS, 4xx, X-Forwarded) |

> **Cleanup 12Sep26:** 10 skrip mati DIHAPUS PERMANEN (ACC Bos):
> `cari_api_oo.py`, `diagnosa_edit.py`, `diagnosa_muat.py`, `diagnosa_browser.py`,
> `lacak_gagal.py`, `lacak_gagal2.py`, `uji_simpan_e2e.py`, `uji_simpan_v4.py`,
> `hapus_sparkle_v2.py`, `siapkan_logo.py`.
> Folder `assets/` (duplikat md5-identik) juga dihapus + 12 logo varian tak terpakai.
> **Sisa: 17 skrip** (semua fungsional).

---

## Status (15Sep26)

### Selesai & TERBUKTI LIVE (15Sep26)
- [x] Batas per berkas **5 MB** (ACC Bos 15Sep26, skripsi 2,1 MB, tesis 3,4 MB)
- [x] Timeout AI **420 detik** (sinkron `.env` + `app/config.py`)
- [x] Teks batas berkas dinamis `{{ max_mb }}` (hardcode 25 MB dibuang)
- [x] Gerbang storage HTTP 413 terbukti E2E browser nyata (input file)
- [x] Gerbang folder: teks dibedakan per paket (gratis → upgrade, bayar → addon)
- [x] Ikon Lucide SVG sprite
- [x] Deploy SOT 5 langkah (`jalankan.sh`) + verifikasi md5 image vs source
- [x] Dokumen editor termuat (`logicDoc=True`)

### Sedang Berjalan (Fokus Sekarang)
- [ ] **Pondasi Ingatan Dokumen**: tabel `profil_dokumen` + `section_state`
- [ ] **Role 1 (Pengenal)**: AI baca 1x teliti → klasifikasi 4 kategori
- [ ] **Role 2 (Revisi)**: potong per-bab (bukan potong buta 55rb kar)
- [ ] **Onboarding Terarah (Kasus 2)**: Jenjang → Bidang → Mode → 3 Pilihan Judul
- [ ] **Pola emas `penelitian-bot`**: Ethics Checker + Section Parser

### Belum Selesai (Menyusul)
- [ ] Simpan hasil edit OnlyOffice (`modified=false` perlu verifikasi simpan)
- [ ] Mode Belajar FASE A
- [ ] QRIS production
- [ ] Kolaborasi Dosen ↔ Mahasiswa (tabel `berbagi`)

### 🐛 Temuan Bug Ditunda (catat 15Sep26 — kerjakan SETELAH Tahap 1–3)
- [ ] `folder.buat()` pesan tolakan selalu sebut "AddOn Storage & Folder" walau user **GRATIS** (tak boleh beli AddOn)
- [ ] route `/folder/buat` menambah `&addon=storage` **tanpa cek** `boleh_beli_addon(u.paket)`
- [ ] `naskah.html` `pemicuDariURL()` tidak pernah panggil `tawarkanAddon()` → user gratis hanya lihat banner galat, **tanpa tombol upgrade**
- [ ] Dua banner bertumpuk (pink galat + kuning statis) = redundan
- [ ] `versi.py` deteksi bab (perbaikan Wulan) sedang LIVE → perlu uji komparasi dgn naskah multi-bab utuh; keputusan revert/pertahankan belum diambil

## 🧪 C7 — UJI PUBLIK: KEADAAN SEBENARNYA (25Sep26)

**KEPUTUSAN BOS: C7 DITUTUP APA ADANYA (opsi 1).**

### Kenapa TIDAK dinyatakan "lulus"
Uji `_uji_publik_komentar.py` pakai `file_id=47` sebagai bahan. TERBUKTI:
    · `versi_dokumen` file 47 isinya = **JAWABAN AI** (`sumber='ai'`), bukan
      naskah mahasiswa → AI menolak merevisi ("ini bukan draf tulisan Anda")
    · Naskah ASLI file 47 (65.826 kar) ada di `section_state`, TAPI berkas
      fisik unggahannya HILANG
⇒ Uji tidak sahih untuk menyatakan aplikasi lulus/gagal.

### YANG TETAP BERHARGA dari C7
1. 🛡️ **Pagar C10 TERBUKTI BEKERJA di produksi** — `proses_ai` id 98-101
   jadi `gagal` + pesan jujur, dan `v57` tetap `terpakai` = naskah TIDAK RUSAK.
2. 🐛 **6 cacat UJI ketemu & diperbaiki** (bukan bug aplikasi):
   a. `docker` tidak ada di dalam container → `kuota_reset_berat` & P1 gagal.
   b. User uji berat tidak punya baris `pemakaian_ai` → 403 "bukan member".
   c. User uji berat salah ORANG (id 5 = paket GRATIS) → 403.
   d. Sandi user berat salah → login gagal.
   e. Batas tunggu 180/240/300/420/600 terlalu pendek (proses nyata 73–615 dtk).
   f. `naskah` kosong & `file_id` salah tetap dilaporkan 403, bukan 400/404.
3. ⚠️ **1 KANDIDAT BUG NYATA (BELUM dibedah):** `proses_ai` id 102
   (`in6p-nnzeDYDUz006OXrgA`) → `IndexError: list index out of range`
   di jalur `naskah` LANGSUNG (skenario N3). Belum pasti bug app atau cacat uji.

### Yang dikerjakan untuk menutup
· `_uji_publik_komentar.py` diberi **PENJAGA**: `E2E_SAYA_SETUJU=1` wajib
  (exit 77 = DILEWATI bila tidak). Alasan: uji ini memakai kuota + menulis DB.
· `file_id=47` **DIHAPUS** (versi 4 · section 1 · revisi 12 · proses 72 · file 1).
· Naskah aslinya **DISELAMATKAN** → `_contoh-dokumen/skripsi-s1/NASKAH-ASLI-file47-65826kar.txt`.
· Hasil uji terakhir: **36 LULUS / 12 GAGAL** — 12 gagal berasal dari bahan uji
  yang tidak sahih (bukan aplikasi).

### Sisa pekerjaan (SESI LAIN)
· Bedah `IndexError` jalur `naskah` langsung (id 102).
· Skenario O1 (kuota habis) — baca/set kuota belum jalan.
· Skenario P (gangguan provider) — WAJIB dijalankan DARI HOST, bukan container.
