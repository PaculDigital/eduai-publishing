# SOT — FITUR LoA OTOMATIS + VERIFIKASI QR

<!-- SOT: dokumen ini BUKAN sumber kebenaran. Sumber resmi: SOT.md.
     Status DIHITUNG dari kode oleh sot.py, bukan dihafal di sini.
     Kalau bertentangan dengan SOT.md ⇒ SOT.md MENANG. -->

**Tanggal:** 17 Oktober 2026
**Status:** ✅ LIVE di produksi
**Image:** `eduai-app:20261017_*` (titik mundur `eduai-app:cadangan-pra-sot`)
**Domain verifikasi:** https://qr.tridarma.id

---

## 1. APA YANG DIBANGUN

EduAi mencetak sendiri **Letter of Acceptance (LoA)** dalam bentuk PDF 1 halaman
saat artikel berstatus **Diterima** di Tridarma, lengkap dengan tanda tangan asli
dan QR verifikasi keaslian.

**Alur:**
```
Editor klik "Terima" di Tridarma (OJS)
   ↓
User buka EduAi → Daftar Artikel → status "DITERIMA"
   ↓
User klik tombol "Unduh LoA"
   ↓
EduAi: cek syarat → isi template → cetak PDF → simpan untuk verifikasi
   ↓
PDF 1 halaman + QR ke qr.tridarma.id/verifikasi-loa?no=...
```

---

## 2. BERKAS YANG DIPAKAI

| Berkas | Isi |
|---|---|
| `app/loa.py` | Mesin LoA: cek syarat, isi 15 token, nomor urut, cetak PDF, QR, `terbitkan()`, `daftar_loa()`, `cari_loa_nomor()` |
| `app/templates/loa/loa-jemt.html` | Template LoA (kop, isi, tanda tangan, blok verifikasi + QR) |
| `app/templates/loa/verifikasi-loa.html` | Halaman verifikasi publik |
| `app/templates/loa/tanda-tangan.png` | Tanda tangan asli (ekstraksi dari SVG Bayana, 247×158) |
| `app/main.py` | Rute `/verifikasi-loa`, `/api/loa/cek`, rute unduh LoA, middleware domain |
| `app/submit_jurnal.py` | `perbarui_status` kini menyimpan volume/nomor/tanggal |
| `app/templates/submit_jurnal.html` | Tombol "Unduh LoA" di kartu artikel |

**Data runtime (bind-mount, di dalam container):**
```
/app/data/loa-terbit.json    → daftar LoA yang sudah terbit (kunci = nomor)
/app/data/setelan-loa.json   → volume, nomor_artikel, editor, kontak
```

---

## 3. ATURAN YANG TERKUNCI

1. **LoA dicetak EduAi, BUKAN OJS.** OJS tidak menyimpan berkas LoA.
2. **Status = TOMBOL MANUAL**, bukan otomatis (hemat resource VPS).
3. **Nomor LoA:** `<volume>.<nomor_artikel>`, contoh `1.001`.
4. **Syarat terbit (dua-duanya wajib):**
   - status artikel = **Diterima**
   - **Volume + Nomor** sudah ditetapkan Tridarma
   Kosong ⇒ LoA TIDAK terbit, muncul pesan jelas.
5. **QR:** `https://qr.tridarma.id/verifikasi-loa?no=<nomor>`
6. **Nomor WA admin:** `0851-7813-8516` (format config `6285178138516`).
   🔒 **PUTUSAN BOS 17 Okt 2026 (TERKUNCI): `8516` = admin EduAi · `8514` = admin Tridarma.**
   `app/config.py` dulu salah `6285720505555` (nomor pribadi lama Bos — DIBUANG).
   Tiga pintu serentak: `config.EDUAI_WA_ADMIN` · `wa.alarm_admin()` ·
   `submit_jurnal.nomor_wa_admin()`. **TERUJI KIRIM NYATA** (`alarm_admin()` = True).
   ⚠️ Catatan jujur: `8516` JUGA nomor sesi device pengirim `eduai-wa-8514`,
   jadi EduAi mengirim ke nomornya sendiri — **DISENGAJA**, kotak masuk admin
   ada di HP pemegang `8516`.
7. **Tridarma belum punya Volume/Nomor** ⇒ LoA belum bisa terbit untuk artikel nyata.

---

## 4. KOP LoA (FINAL, ACC Bos)

```
┌────────────────────────────────────────────────────────────┐
│ [strip gradient navy→orange 10px]                          │
│  LOGO     TRIDARMA.ID                    [← Beranda Jurnal]│
│  64px     Jurnal Ekonomi dan Manajemen Tridarma (JEMT)      │
│            Tridarma Journal Publishing        (tengah)      │
│      E-ISSN: 3163-608X • Terbit 6 kali • Web • Email        │
│ [accent bar 4px gradient orange]                            │
└────────────────────────────────────────────────────────────┘
```

**Kop halaman verifikasi = KOP SAMA dengan LoA** (diputuskan 17 Okt 2026).
Sebelumnya header verifikasi dibuat terpisah (logo 56px, brand 19px, tanpa
"Tridarma Journal Publishing", tanpa baris meta, tanpa accent bar) ⇒ diperbaiki.

---

## 5. TANDA TANGAN

- **Sumber:** `/opt/data/services/bayana-web/public/tanda-tangan-bayana.svg`
- **Masalah:** SVG memuat gambar via `<image href="data:image/png;base64,...">` —
  **WeasyPrint TIDAK mencetak** gambar embedded dalam SVG (keluar hanya teks `alt`).
- **Solusi:** ekstrak PNG dari SVG → `app/templates/loa/tanda-tangan.png`
  (harus di `templates/loa/`, karena `base_url` WeasyPrint mencari di situ).
- Posisi: **di atas nama**, rata kanan, **tanpa bintang**.

---

## 6. INFRASTRUKTUR

**Ingress Cloudflare Tunnel** (`qr.tridarma.id`):
```
  9. qr.tridarma.id   → http://localhost:8100   ← BARU (EduAi)
 10. *.tridarma.id    → https://localhost:443   ← wildcard Tridarma TETAP UTUH
 11. tridarma.id      → https://localhost:443
```

**Middleware domain** (`app/main.py`, WAJIB tepat setelah `app = FastAPI(...)`):
```python
HOST_VERIFIKASI = {'qr.tridarma.id'}

@app.middleware('http')
async def arahkan_domain_verifikasi(request, call_next):
    host = (request.headers.get('host') or '').split(':')[0].lower()
    if host in HOST_VERIFIKASI and request.url.path in ('/', ''):
        return templates.TemplateResponse('loa/verifikasi-loa.html',
                                          {'request': request})
    return await call_next(request)
```
⇒ `qr.tridarma.id/` = halaman verifikasi, **bukan** beranda EduAi.
⚠️ FastAPI **menolak** `@app.middleware` bila didaftarkan setelah app melayani
permintaan — karena itu posisinya harus di atas.

---

## 7. JEMBATAN OJS (PENTING)

```
SALAH (lama): http://ojs-ojs_web-1/mcp     ← nama container INTERNAL
BENAR       : https://tridarma.id/mcp      ← lewat domain HTTPS
```
`app/submit_jurnal.py::OJS_BRIDGE` sudah dibetulkan.

Jembatan: `/var/www/html/mcp/article_status.php` · `submit_article.php` · `register_user.php`

---

## 8. HASIL UJI (TERUKUR)

### Mesin LoA (`_sketsa/uji_terbitkan30.py`)
| Kasus | Hasil |
|---|---|
| Status Antrean | ✅ DITOLAK — "belum dinyatakan diterima" |
| Diterima, Volume kosong | ✅ DITOLAK — "Tridarma belum menetapkan Volume/Nomor" |
| Lengkap | ✅ LoA TERBIT — `1.001/LOA/JEMT/X/2026`, PDF 103 KB, **1 halaman**, QR ada |

### Halaman verifikasi — tampilan HP 390px (`_sketsa/uji_valid_hp.py`)
**11 LULUS / 0 GAGAL**
| # | Asersi | Hasil |
|---|---|---|
| 1 | Kotak "LoA VALID — Dokumen Asli" muncul (nomor 1.001) | ✅ |
| 2 | Judul artikel tampil | ✅ |
| 3 | Penulis tampil | ✅ |
| 4 | ID Submission terisi (bukan `undefined`) | ✅ |
| 5 | Tidak ada teks `undefined` | ✅ |
| 6 | Nomor palsu 9.999 ditolak | ✅ |
| 7 | WA `0851-7813-8514` tampil | ✅ |
| 8 | `innerWidth` = 390 | ✅ |
| 9 | `scrollWidth` ≤ 390 (tidak geser samping) | ✅ |
| 10 | 0 elemen meluber | ✅ |
| 11 | Tanpa galat JavaScript | ✅ |

Diverifikasi **mata** (vision) juga: kop utuh, form muat, 3 kartu bertumpuk,
footer rapi — tidak ada yang terpotong.

### Kop halaman verifikasi = kop LoA
| Bagian | LoA | Verifikasi |
|---|---|---|
| Strip atas 10px | ✅ | ✅ |
| Logo 64px | ✅ | ✅ |
| `TRIDARMA.ID` 30px | ✅ | ✅ |
| Sub JEMT 15px | ✅ | ✅ |
| `Tridarma Journal Publishing` | ✅ | ✅ |
| E-ISSN•Terbit•Web•Email 1 baris tengah | ✅ | ✅ |
| Accent bar 4px | ✅ | ✅ |
| Tombol Beranda Jurnal sejajar logo | — | ✅ |

---

## 9. JEBAKAN YANG SUDAH DITUTUP

1. **`async async function`** — Wulan menyisipkan `async` dua kali di
   `verifikasi-loa.html` ⇒ seluruh JavaScript gagal ⇒ tombol Verifikasi diam.
   Obat: cek dengan `node --check` pada isi `<script>` sebelum deploy.
2. **Middleware terlalu bawah** — `@app.middleware` setelah app melayani = error.
   Harus tepat setelah `app = FastAPI(...)`.
3. **`qr.tridarma.id/` menampilkan beranda EduAi** — akar `/` tidak tahu beda
   domain. Obat: middleware `HOST_VERIFIKASI`.
4. **`d.submission_id` vs `id_ojs`** — halaman minta kunci yang tidak ada ⇒
   muncul `undefined`. Obat: baca kunci yang benar-benar dikirim.
5. **Alamat jembatan salah** (`ojs-ojs_web-1` / `:9027`) — harus
   `https://tridarma.id/mcp`. Port 9027 ternyata **SSH**, bukan HTTP.
6. **Kop HP meluber** — `.kop-row` butuh 697px pada layar 390px (kop LoA dibuat
   untuk kertas A4). Obat: `@media(max-width:640px)` ⇒ kop bertumpuk.
7. **Alat ukur menipu** — Chrome di port 9333 dipaksa `innerWidth = 698` walau
   diminta 390 ⇒ hampir salah vonis "halaman rusak". Pakai **Playwright**
   (terbukti patuh 390px) + verifikasi mata.
8. **WeasyPrint tidak mencetak `<image>` di dalam SVG** — lihat §5.
9. **`.page{min-height:297mm}` + `.footer{margin-top:auto}`** — footer & tanda
   tangan terlempar ke halaman 2. Obat: hapus `min-height`, padatkan antar-blok.

---

## 10. YANG BELUM / CATATAN

- **Tridarma `issues = 0`** ⇒ belum ada Volume/Nomor ⇒ LoA artikel nyata belum
  bisa terbit. Tombol akan menolak dengan pesan jelas sampai editor mengisi.
- ✅ **Nomor WA admin: SUDAH DIBETULKAN 17 Okt 2026.** `app/config.py`
  `EDUAI_WA_ADMIN` = `6285178138516` (= admin EduAi, putusan Bos).
  Teruji kirim NYATA. Image `eduai-app:20261017_043641-sot`.
  Backup: `_arsip/pre-wa-admin-8516-20261017-043611`. Lihat §3.6 di atas.
- **Tridarma TIDAK punya nomor admin.** `ojs-mcp/main.py` hanya punya GRUP WA
  (`120363428747857547@g.us`) + kirim-ke-diri-sendiri `6285178138514` sebagai
  log audit (baris 484 & 564). Tidak ada nomor admin pribadi di kode Tridarma.
- **Tombol "Unduh LoA"** sudah terpasang tapi **belum diuji dengan akun user
  nyata** (belum ada artikel Diterima sungguhan).
- **Data uji sudah dibersihkan** 17 Okt 2026 03:58 (cadangan:
  `_arsip/pre-bersih-loa-20261017_035810/`). `nomor_artikel` = 0 ⇒ LoA asli
  pertama = `1.001`.

---

## 11. CARA BALIK

```bash
cd /opt/data/services/eduai-publishing

# titik mundur image
docker images | grep cadangan-pra-sot

# cadangan data LoA
ls _arsip/pre-bersih-loa-*/

# uji mesin LoA (pakai folder uji, tidak menyentuh produksi)
python3 _sketsa/uji_terbitkan30.py

# uji halaman verifikasi di HP
python3 _sketsa/uji_valid_hp.py

# cek API dari domain nyata
curl -s "https://qr.tridarma.id/api/loa/cek?no=1.001"
```
