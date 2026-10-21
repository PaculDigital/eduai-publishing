# 🎨 REBRANDING EDUAI — DOKUMENTASI LENGKAP

<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Terakhir diperbarui: **12 September 2026**
> Status: **SELESAI & PERMANEN** ✅

---

## 1. RINGKASAN

EduAi Publishing memakai **OnlyOffice Document Server** (Community Edition)
sebagai mesin editor. Semua atribut OnlyOffice yang terlihat user sudah
diganti dengan identitas **EduAi INOVASI**.

| Bagian | Sebelum | Sesudah |
|---|---|---|
| Judul tab browser | `ONLYOFFICE` | `EduAi INOVASI - Editor` |
| Bar biru editor | logo + teks ONLYOFFICE | 🦜 ikon burung + "EduAi" |
| Dialog About — logo | logo ONLYOFFICE | 🦜 kepala burung besar + "EduAi INOVASI" |
| Dialog About — data | Ascensio System SIA, Latvia | EduAi INOVASI, Bekasi |
| Label email | `surel:` | `email:` |
| Link web | `www.education...` | `eduai.bikinaja.id` (tanpa `www.`) |

---

## 2. MASALAH INTI — `canBranding = false`

OnlyOffice **Community Edition** tidak mengizinkan branding lewat config.
Bukti yang ditemukan:

```
license_file : ""        (tidak ada lisensi)
packageType  : 0         (Community Edition)
API lisensi  : {"error":6}
```

Kode OnlyOffice (`Main.js` ~baris 1809):
```javascript
this.appOptions.canBranding = params.asc_getCustomization();
```

Karena `canBranding = false`, maka **diabaikan**:
- `customization.customer` → data About tidak terpakai
- `customization.logo.visible` → logo tidak disembunyikan

**PELAJARAN:** Ini **bukan** kesalahan config kita. Config kita sudah benar
dan tetap dikirim. OnlyOffice **menolak memakainya** karena lisensi.

**Solusi:** Timpa **file di dalam container** (bukan lewat config).

---

## 3. ARSITEKTUR PERUBAHAN

```
eduai-publishing/
├── oo-branding/                    ← SUMBER PERMANEN (di repo)
│   ├── header/
│   │   ├── dark-logo_s.svg         (31.626 B) logo bar biru — tema gelap
│   │   └── header-logo_s.svg       (31.626 B) logo bar biru — tema terang
│   ├── about/
│   │   ├── About.js                (14.347 B) data About
│   │   └── logo-eduai-about.png    (76.365 B) kepala burung + EduAi INOVASI
│   └── css/                        (suntikan CSS via skrip)
│
└── scripts/
    ├── jalankan_oo.sh              ← jalankan container (+ branding + tab otomatis)
    ├── perbaiki_oo.sh              ← perbaiki nginx + OO (8 bagian) + FLUSH CACHE
    ├── pasang_branding_oo.sh       ← pasang branding saja
    ├── perbaiki_logo_about.py      ← suntik CSS (dipanggil skrip di atas)
    ├── rebrand_about.py            ← tulis data About.js
    ├── rebrand_about2.py           ← tulis label About.js
    ├── ganti_logo_header.py        ← pasang SVG logo header
    ├── buat_logo_header.py         ← bikin SVG logo header
    ├── perbaiki_tab_kolaborasi.py  ← tab Kolaborasi oranye + tab AI shimmer
    ├── perbaiki_tab_ai.py          ← sisip field `tab` ke config plugin AI
    ├── cek_id_stabil.py            ← buktikan ID tab AI acak per-load
    ├── uji_datatitle.py            ← buktikan data-title="AI" stabil
    ├── uji_shimmer_final.py        ← 2 screenshot jeda 1,5s + computed style
    └── purge_cf_aset.py            ← purge cache Cloudflare
```

**Prinsip:** aset disimpan di repo (`oo-branding/`), lalu **disalin** ke
container. Container boleh dihapus kapan saja — branding bisa dipasang ulang.

---

## 3b. 🎨 WARNA TAB OO (13Sep26)

### Tab **Kolaborasi** → oranye `#ffa000` (permanen)

Ditulis ke `app.css` **5 editor** (documenteditor, pdfeditor,
presentationeditor, spreadsheeteditor, visioeditor) + `.gz` masing-masing.

Selektor (dari source OO, **bukan tebakan**):
```css
.toolbar .tabs li.ribtab > a[data-title="Kolaborasi"],
.toolbar .tabs li.ribtab > a#review,
li.ribtab > a#review {
    color: #ffa000 !important;
    font-weight: 700 !important;
}
```
Struktur DOM asli: `section.tabs > ul > li.ribtab > a`.
OO set warna via `.toolbar .tabs li > a` (**class `.tabs`**, BUKAN `.box-tabs`).

### Tab **AI** → oranye + shimmer emas bergerak

**⚠️ INI BAGIAN PALING RUMIT. Tiga jebakan yang terbukti:**

#### Jebakan A — ID tab plugin AI = **GUID ACAK per-load** → jangan dipakai

Terbukti dengan membuka editor 2x:
```
buka ke-1 : 13df42c9-191d-a004-7d41-b1e627f202c1
buka ke-2 : 8fc9852e-b5bc-304f-e853-55b68848d54f   ← BEDA!
```
Selektor `a#eduai-ai` **tidak akan pernah match**.
**YANG STABIL = `data-title`** (isinya teks caption):
```html
<a role="tab" id="<GUID-acak>" data-tab="<GUID-acak>" data-title="AI">AI</a>
```
→ pakai **`a[data-title="AI"]`** ✓

#### Jebakan B — field `tab` di config plugin background **DIABAIKAN OO**

`common/main/lib/controller/Plugins.js`:
```js
collection.each(function (model) {
    if (model.get('isBackgroundPlugin')) {
        me.backgroundPlugins.push(model);
        return;                    // ← plugin AI KELUAR di sini
    }
    if (model.get('tab')) { ... me.toolbar.addCustomControls(tab, [btn]); }
```
Plugin `type: background` **return lebih dulu** → blok `model.get('tab')`
**tidak pernah dieksekusi**. Ini **desain OO**, bukan salah config kita.

#### Jebakan C — DUA hal yang MEMATIKAN animasi shimmer

**1. Shorthand `background:` + `!important` mematikan `background-position`**
```
varian `background: linear-gradient(...) !important` → posisi DIAM ❌
varian `background-image:` (properti spesifik)       → BERGERAK ✓
```
Pakai properti spesifik; `!important` hanya untuk `color` /
`-webkit-text-fill-color`.

**2. `background-size: 220%` bikin teks HILANG sesaat**
Gradien keluar dari area teks → `background-clip:text` tanpa piksel →
teks transparan kosong (dibuktikan dengan vision: huruf "AI" hilang di
satu frame).
**Benar: `background-size: 100% 100%` + `background-repeat: repeat`.**

#### CSS final yang terbukti
```css
a[data-title="AI"] {
    background-image: linear-gradient(90deg, #ffa000 0%, #ffd77a 40%,
                                      #fff3d0 50%, #ffd77a 60%, #ffa000 100%);
    background-size: 100% 100%;
    background-repeat: repeat;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    font-weight: 700 !important;
    animation: eduaiAiShimmer 2.8s linear infinite;
}
@keyframes eduaiAiShimmer {
    0%   { background-position: 0% 0; }
    100% { background-position: 200% 0; }
}
```

#### 🚨 Pembersih blok CSS — prefix collision
`EDUAI-TAB-COLLAB` adalah **PREFIX** dari `EDUAI-TAB-COLLAB-AI`. Kalau
cleaner pakai `s.find(marker)` tunggal → memotong di titik salah → blok
**MENUMPUK (3→4)**.
**Fix:** pembersih **berbasis daftar-blok eksplisit**.
Verifikasi idempoten: jalan 2x → `blok_kolab=1 blok_ai=1`, ukuran identik.
**Cara hitung benar:** marker muncul **2x per blok** (pembuka + penutup).

#### Cara verifikasi shimmer (bukan `getComputedStyle` saja)
`getComputedStyle` tidak selalu update `background-position` saat
`background-clip:text`. **Bukti terkuat = 2 screenshot jeda 1,5s + banding piksel:**
```python
from PIL import Image, ImageChops
diff = ImageChops.difference(Image.open('a.png').convert('RGB'),
                             Image.open('b.png').convert('RGB'))
print(diff.getbbox())   # None = TIDAK bergerak; ada bbox = BERGERAK ✓
```
Plus baca `background-position` tiap 0,7s → nilai unik >1 = bergerak.

---

## 4. FILE YANG DIUBAH DI DALAM CONTAINER

Container: **`oo-converter`** · Root DS: `/var/www/onlyoffice/documentserver`

### 4.1 Logo bar biru (header)

```
web-apps/apps/common/main/resources/img/header/
├── dark-logo_s.svg      31.626 B  (dari 2.975 B)
├── dark-logo_s.svg.gz   23.949 B
├── header-logo_s.svg    31.626 B  (dari 2.975 B)
└── header-logo_s.svg.gz 23.954 B
```

**Isi SVG:** ikon burung + teks "EduAi" (di-embed sebagai PNG base64).
**Ukuran:** viewBox `49×20` — sesuai CSS OnlyOffice `max-height: 20px`.

> ⚠️ **JEBAKAN UKURAN:** percobaan pertama pakai viewBox `150×20` →
> teks terpotong jadi `Edu... IN` dan menabrak tab "Halaman Depan".
> Kontainer hanya **122×28 px**. Ukuran `49×20` yang benar.

### 4.2 Dialog About — data

```
web-apps/apps/common/main/lib/view/About.js      14.347 B
web-apps/apps/common/main/lib/view/About.js.gz    3.079 B
```

5 field yang diganti:

| Field | Nilai |
|---|---|
| `publishername` | `EduAi INOVASI` |
| `publisheraddr` | `Jl. Raya Bekasi KM 32 - Bekasi` |
| `publisherurl` | `http://eduai.bikinaja.id/` |
| `supportemail` | `eduai@bikinaja.id` |
| `phonenum` | `+6281-000-000` |

> ⚠️ **Copyright AGPL (baris 2 & 13) DIBIARKAN** — komentar
> `Ascensio System SIA` **wajib** tetap ada. Wulan sudah verifikasi:
> keduanya hanya komentar, **tidak tampil ke user**.

> 📌 Nama field yang benar adalah **`supportemail`** dan **`phonenum`**,
> BUKAN `publishermail`/`publisherphone` (tidak ada di About.js).

### 4.3 Dialog About — label locale

```
web-apps/apps/common/main/resources/*/id.json   (3 berkas)
```

Label `"surel:"` → `"email: "`. **Kenapa perlu?** Karena `About.js:296`
sudah `email:` tapi **`locale/id.json` menimpanya**.

> ⚠️ Harus 3 berkas + `.gz` masing-masing. Ganti salah satu saja = gagal.

### 4.4 Dialog About — logo + CSS

```
web-apps/apps/common/main/resources/img/about/logo-eduai-about.png  76.365 B
```

CSS disuntik ke **5 file** `app.css` (satu per editor):

```
web-apps/apps/documenteditor/main/resources/css/app.css
web-apps/apps/spreadsheeteditor/main/resources/css/app.css
web-apps/apps/presentationeditor/main/resources/css/app.css
web-apps/apps/pdfeditor/main/resources/css/app.css
web-apps/apps/visioeditor/main/resources/css/app.css
```

Suntikan (ditandai `/* EDUAI-ABOUT-FIX */`):

```css
/* matikan logo OnlyOffice bawaan */
.about-dlg .asc-about-office:before {
  content: none !important; display: none !important; height: 0 !important;
}
/* logo burung kita, BESAR */
.about-dlg .asc-about-office {
  background-image: url(".../img/about/logo-eduai-about.png") !important;
  background-size: contain !important;
  background-position: center !important;
  background-repeat: no-repeat !important;
  width: 260px !important; height: 230px !important;
  margin: 0 auto 10px auto !important;
}
```

> ⚠️ **AKAR MASALAH TUMPANG-TINDIH:** CSS bawaan OnlyOffice punya
> `.about-dlg .asc-about-office:before { content: url('.../logo_s.svg') }`
> yang menggambar **logo OnlyOffice**. Kalau hanya `background-image` yang
> ditimpa, logo OnlyOffice tetap muncul di belakang → tumpang-tindih.
> **WAJIB matikan `:before`.**

---

## 5. CARA PAKAI

### 5.1 Jalankan container OO (sehari-hari)

```bash
bash scripts/jalankan_oo.sh
```

Otomatis: cek JWT → cek nginx → **cek branding** → pasang kalau hilang.

### 5.2 Cek status saja

```bash
bash scripts/jalankan_oo.sh --status
```

### 5.3 Pasang / pulihkan branding

```bash
bash scripts/pasang_branding_oo.sh --cek
```
```bash
bash scripts/pasang_branding_oo.sh
```

### 5.4 Perbaiki semua setelan OO (nginx + branding)

```bash
bash scripts/perbaiki_oo.sh --cek
```
```bash
bash scripts/perbaiki_oo.sh
```

### 5.5 Purge cache Cloudflare (WAJIB setelah ubah aset)

```bash
python3 scripts/purge_cf_aset.py
```

---

## 6. ⚠️ JEBAKAN YANG SUDAH TERBUKTI

### 6.0 🚨 JEBAKAN TERBESAR: proxy buang `Location` → aset 404 (13Sep26)

**GEJALA YANG DILAPORKAN BOS:**
> "Tab kolaborasi tidak pernah jadi orange dan masih branding onlyoffice
> belum berubah"

Padahal **semua cek server hijau**: file CSS benar, blok Kolaborasi+AI ada,
`.gz` sinkron, purge CF `success: True`, uji CloakBrowser LULUS. Tapi
**browser Bos selalu melihat versi LAMA**.

**AKAR MASALAH — DUA BUG bertumpuk di `eduai-app`:**

#### BUG #1 — proxy membuang header `Location` pada 302

nginx OnlyOffice **SELALU** membalas 302 untuk path aset tanpa versi:

```
GET /oo/aset/web-apps/apps/documenteditor/main/resources/css/app.css
  → 302 → /9.4.0-<cache_tag>/web-apps/apps/.../app.css
```

Redirect itu **mekanisme cache-busting resmi OO**. Kalau `cache_tag` berubah,
browser dipaksa mengambil aset baru. Kode LAMA di `app/main.py` (akhir
`oo_aset()`) **tidak menyalin `Location`**:

```python
# ❌ LAMA — 302 tanpa tujuan
hdr = {'Vary': 'Cookie, Accept-Encoding'}
if enc:
    hdr['Content-Encoding'] = enc
return Response(content=isi, media_type=tipe, headers=hdr, status_code=stat)
```

Browser menerima **"302 tanpa tujuan"** → bingung → **jatuh ke cache lama**.

#### BUG #2 — `documentServerUrl` tidak di-set

`app/templates/editor.html`:

```js
// ❌ LAMA
editor = new DocsAPI.DocEditor('tempat-editor', cfg);
```

DocsAPI lalu memakai path **RELATIF** dari halaman (`/edit/9`), sehingga
iframe OO meminta aset lewat `/web-apps/...` (**tanpa** prefix `/oo/aset`)
→ **404**.

#### ✅ PERBAIKAN (3 lapis — semuanya sudah terpasang di `v3-redirectfix`)

**Lapis 1 — teruskan `Location`** (`app/main.py`, akhir `oo_aset()`):

```python
if 300 <= stat < 400:
    loc = masuk.headers.get('location', '')
    if loc:
        from urllib.parse import urlsplit
        pu = urlsplit(loc)
        path_redirect = pu.path + (('?' + pu.query) if pu.query else '')
        if not path_redirect.startswith('/oo/aset'):
            path_redirect = '/oo/aset' + path_redirect
        hdr['Location'] = path_redirect
    hdr['Cache-Control'] = 'no-store'   # redirect JANGAN di-cache
```

⚠️ **WAJIB tulis ulang ke prefix publik kita.** `Location` asli menunjuk host
internal `oo.bikinaja.id` yang **DITUTUP dari publik** — kalau diteruskan
mentah, browser diarahkan ke host yang tidak bisa diakses.

**Lapis 2 — set `documentServerUrl`** (`app/templates/editor.html`):

```js
editor = new DocsAPI.DocEditor('tempat-editor', cfg,
                               { documentServerUrl: '/oo/aset' });
```

**Lapis 3 — rute jaring pengaman** (`app/main.py`, SEBELUM `oo_aset`):

```python
@app.api_route('/web-apps/{sisa:path}', methods=[...])
@app.api_route('/sdkjs/{sisa:path}', methods=[...])
@app.api_route('/sdkjs-plugins/{sisa:path}', methods=[...])
@app.api_route('/fonts/{sisa:path}', methods=[...])
async def oo_aset_polos(req: Request):
    sisa = req.url.path.lstrip('/')
    raise HTTPException(302, headers={'Location': f'/oo/aset/{sisa}'})
```

Supaya SELALU jalan, apa pun konfigurasi DocsAPI-nya.

#### 🚨 PELAJARAN UJI — jangan lewat jalur ber-tag saja

Menguji lewat `/oo/aset/9.4.0-<tag>/...` (path ber-tag) **SELALU 200 OK**,
sehingga verifikasi terlihat LULUS — padahal browser memakai jalur LAIN
yang 404. **SELALU uji jalur yang BROWSER pakai:**

```bash
curl -sL -b cookie.txt -H 'Accept-Encoding: gzip' -D - -o out.raw \
  "https://eduai.bikinaja.id/web-apps/apps/documenteditor/main/resources/css/app.css"
# HARUS: 302 → 302 → 200, dan isinya punya marker CSS terbaru
```

**Diagnosa berjenjang (3 titik):**

| Titik uji | Sebelum fix | Sesudah fix |
|---|---|---|
| nginx container | 302 + Location ✓ | sama ✓ |
| `eduai-app` | **404** ❌ | 302 + Location ✓ |
| domain publik (polos) | **404**, cf-cache HIT ❌ | 302 → 200 ✓ |

Cek cepat OO dari dalam container (kalau ini 302, berarti OO BENAR dan yang
salah adalah proxy kita):

```bash
docker exec oo-converter sh -c "curl -s -o /dev/null -w '%{http_code} → %{redirect_url}' \
  -H 'Host: eduai.bikinaja.id' \
  http://127.0.0.1/web-apps/apps/documenteditor/main/resources/css/app.css"
```

#### ⚠️ Kenapa ini memblokir SEMUA rebranding

Semua aset OO (CSS 5 editor, `About.js`, logo SVG, `api.js`, `sdkjs`) lewat
jalur yang **sama**. Selama bug ini ada, **rebranding + tab oranye TIDAK
PERNAH terlihat user** walau file di server sudah benar.

👉 **Kalau Bos lapor "belum berubah" padahal cek server hijau — curigai INI
dulu, bukan cache browser.**

#### 🐛 BONUS: `cache_tag` tidak berubah = browser tetap cache lama

OO menyajikan aset lewat path `9.4.0-<cache_tag>`. Kalau `cache_tag` tidak
berubah setelah ganti aset, browser/CF tetap pakai versi lama. Ada skrip
**resmi OO**:

```bash
docker exec oo-converter bash /usr/bin/documentserver-flush-cache.sh
docker exec oo-converter nginx -s reload
```

Sudah **otomatis** di `perbaiki_oo.sh` (baris "Flush cache aset OO").

#### 🐛 BONUS: `jalankan_oo.sh` melewatkan pemasangan CSS tab

Bug lama: blok "5. Setelan nginx" hanya memanggil `perbaiki_oo.sh` **kalau
`PERLU=1`** (ada setelan nginx hilang). Container yang nginx-nya lengkap →
**SKIP** → CSS tab tidak pernah dipasang saat rebuild.

**Fix:** blok baru **"5b. Warna tab Kolaborasi + AI"** yang cek **TERPISAH**
dari nginx (lihat `scripts/jalankan_oo.sh`).

#### Hasil verifikasi (13Sep26)

```
Image : eduai-app:v3-redirectfix (77e42c026fbc)
Backup: eduai-app:v2-ai-backup-13sep26

path polos /web-apps/.../app.css → 302 → 302 → 200 ✓
ukuran 625.196 B · marker Kolaborasi=4 · AI=2 · keyframes=1
data-title="AI"=9 · ffa000=6 · background-size:100% ✓

Regression (semua SEHAT):
  edit/9 200 · api.js 200 · sdk-all.js 200 · plugins.json 200
  themes.json 200 · beranda 200 · masuk 200 · naskah 200
```

---

### 6.1 `.gz` WAJIB ikut diganti

nginx OnlyOffice pakai `gzip_static on`. Kalau `.js`/`.svg` diganti tapi
`.gz` lama tetap ada → **yang diserve versi LAMA**.

**Aturan:** setiap ganti file, ganti juga `.gz`-nya.

### 6.2 Cache Cloudflare menyajikan versi lama

File di container sudah benar (14.347 B), tapi Cloudflare menyajikan
14.395 B. **Setiap perubahan aset `/oo/aset` WAJIB purge CF.**

### 6.3 Test dari dalam container, bukan dari host

- `localhost:8100` tak reachable dari host → pakai `172.17.0.1:8100`
- curl dari host **tidak** membaca header Cloudflare → harus
  `urllib` **di dalam** container
- OO dari host: `127.0.0.1:18081` → `000`; `172.17.0.7:80` → `403`
  kecuali pakai header `Host: localhost` → `302`

### 6.4 Aktifkan `about` di config

`app/onlyoffice.py`:
```python
'about': True,
'customer': {
    'name': 'EduAi INOVASI',
    'address': 'Jl. Raya Bekasi KM 32 - Bekasi',
    'mail': 'eduai@bikinaja.id',
    'phone': '+6281-000-000',
    'www': 'http://eduai.bikinaja.id/',
    'logo': URL_LOGO_ABOUT,
},
```

Config ini **tetap dikirim** (benar) walau CE mengabaikannya — berguna
kalau kelak pakai lisensi berbayar.

### 6.5 Tombol About `disabled` saat editor loading

Skrip uji harus **tunggu tombol aktif** dulu (bukan langsung klik):
```javascript
const b = document.querySelector('#left-btn-about');
b.disabled = false; b.classList.remove('disabled');
b.dispatchEvent(new MouseEvent('click', {bubbles: true}));
```

### 6.6 Klik `<symbol>` SVG gagal

Dispatch event + `click()` pada **BUTTON** `#left-btn-about`, bukan pada
elemen `<symbol>` di dalamnya.

---

## 7. VERIFIKASI (CARA CEK SENDIRI)

### 7.1 Cek isi file di container

```bash
docker exec oo-converter sh -c '
D=/var/www/onlyoffice/documentserver/web-apps/apps
printf "logo header   : "; stat -c %s \$D/common/main/resources/img/header/dark-logo_s.svg
printf "About.js      : "; stat -c %s \$D/common/main/lib/view/About.js
printf "About EduAi   : "; grep -c "EduAi INOVASI" \$D/common/main/lib/view/About.js
printf "Copyright AGPL: "; grep -c "Ascensio System SIA" \$D/common/main/lib/view/About.js
printf "CSS fix       : "; grep -l "EDUAI-ABOUT-FIX" \$D/*/main/resources/css/app.css | wc -l
printf "logo about    : "; stat -c %s \$D/common/main/resources/img/about/logo-eduai-about.png
'
```

**Nilai benar:**

| Item | Nilai |
|---|---|
| logo header | `31626` (>20000 = bukan bawaan) |
| About.js | `14347` |
| About EduAi | `1` |
| Copyright AGPL | `2` ← **harus ada, jangan hapus** |
| CSS fix | `5` |
| logo about | `76365` |

### 7.2 Cek visual (CloakBrowser)

```bash
/opt/data/services/cloakbrowser/.venv/bin/python3 scripts/diagnosa_logo_about.py
```

Cek yang benar:

```json
{
  "ada": true,
  "box": {"w": 260, "h": 230},
  "bgImage": "url(\".../img/about/logo-eduai-about.png\")",
  "before": {"content": "none", "display": "none"}
}
```
```
[status gambar] {"status": 200, "type": "image/png", "len": 76365}
```

---

## 8. UJI TAHAN GEMPA (HASIL NYATA)

Wulan **merusak sengaja** 4 hal, lalu jalankan `pasang_branding_oo.sh`:

| # | Dirusak | Terdeteksi | Dipulihkan |
|---|---|---|---|
| 1 | SVG logo header → `<svg/>` (6 B) | ✅ ✗ | ✅ 31.626 B |
| 2 | About.js → `Ascensio System SIA` | ✅ ✗ | ✅ EduAi |
| 3 | CSS fix dihapus (5 editor) | ✅ 0/5 | ✅ 5/5 |
| 4 | `logo-eduai-about.png` dihapus | ✅ ✗ | ✅ 76.365 B |

**Hasil: `BRANDING TERPASANG ✓` — pulih 100%.**

Diuji juga **idempoten** (dijalankan 3×, hasil sama).

---

## 9. ROLLBACK

Kalau perlu kembali ke tampilan OnlyOffice asli:

```bash
# 1. Hapus branding dari container
docker exec oo-converter sh -c '
D=/var/www/onlyoffice/documentserver/web-apps/apps
rm -f \$D/common/main/resources/img/about/logo-eduai-about.png
for e in documenteditor spreadsheeteditor presentationeditor pdfeditor visioeditor; do
  sed -i "/EDUAI-ABOUT-FIX/d" \$D/\$e/main/resources/css/app.css
done
'
# 2. Recreate container (ambil file asli dari image)
bash scripts/jalankan_oo.sh
# 3. Purge CF
python3 scripts/purge_cf_aset.py
```

**Backup aset asli:** `_arsip/oo-header-asli/`, `_arsip/oo-about-asli/`,
`_arsip/pre-rebrand-20260912-104358/`

---

## 10. HAK LEGAL

- OnlyOffice Documentserver **9.4.0** — setelah teguran FSF, klausa wajib
  menampilkan logo sudah **tidak ada**.
- Copyright AGPL di `About.js` baris 2 & 13 **dipertahankan** (kepatuhan).
- Merek dagang "OnlyOffice" **tidak dipakai** di tampilan user.

---

## 11. STATUS AKHIR

| # | Item | Status |
|---|---|---|
| 1a | Judul tab browser | ✅ |
| 1d | Logo bar biru (burung + "EduAi") | ✅ |
| 2 | About data EduAi + `email:` + tanpa `www.` | ✅ |
| 2b | Logo besar di About (260×230) | ✅ |
| 3 | Permanenkan (repo `oo-branding/` + skrip otomatis) | ✅ |
| 4 | Dokumentasi | ✅ (dokumen ini) |
| — | ⏳ Judul iframe (internal) | tidak dikerjakan |
| — | ⏳ Favicon | tidak dikerjakan |
