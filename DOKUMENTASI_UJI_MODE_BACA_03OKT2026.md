# DOKUMENTASI UJI MODE BACA ONLYOFFICE — 03Okt2026

<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


**Proyek:** EduAi Publishing (`/opt/data/services/eduai-publishing`)
**Perintah Bos:** *"Ok lakukan uji yang benar"* → *"Ok lanjutkan"* (uji lewat produksi)
**Tujuan:** membuktikan (atau mematahkan) rencana **Pembimbing AI — ALAT SAMA**
SEBELUM satu baris kode ditulis.
**Hari:** 03 Okt 2026 · **Status:** ✅ TUNTAS untuk pertanyaan inti

---

## 1. KENAPA UJI INI ADA

Rencana Pembimbing AI (`RENCANA_PEMBIMBING_AI_SEDERHANA.md`) berdiri di atas 3
andaian yang **belum pernah diuji**:

1. Pembimbing bisa pakai OnlyOffice dengan **tombol mati** (mode baca).
2. Pembimbing tetap bisa **komentar/sorot** (inti fiturnya).
3. Pembimbing **tidak bisa** menembus & menyimpan naskah orang.

Kalau salah satu andaian palsu → rencana harus diubah. Jadi diuji dulu.

---

## 2. HASIL — 8 HAL TERBUKTI

| # | Uji | Hasil | Cara bukti |
|---|---|---|---|
| A1 | mode `edit` → permissions | `edit=true`, `comment=true` | fungsi produksi di container |
| A2 | mode `view` → permissions | `edit=false`, **`comment=FALSE`** ⚠️ | idem |
| A3 | `callbackUrl` (url_simpan) | **SELALU dikirim** OO | idem |
| A4 | token pemilik vs token pembaca | **BERBEDA** | `_token_berkas(fid,uid)` |
| **A5** | **PAGAR SIMPAN di SERVER** | **pemilik → 200 `{'error':1}`** · **pembaca → 403 `'Token tidak valid'`** | **POST via `eduai.bikinaja.id`** |
| A6 | OO hidup | judul `ONLYOFFICE Document Editor`, badan 324.154 aksara | tab CDP langsung |
| A7 | berkas inti OO | index.html · app.js · app.css · sdk-all.js **semua 200** | curl |
| A8 | `semua_permission_ikut_mode_edit` | **TRUE** — 6 permission ikut satu `mode` | fungsi produksi |

### A5 = BUKTI TERKUAT (inilah yang paling penting)

```text
POST https://eduai.bikinaja.id/oo/simpan/{token}
  token PEMILIK  (sah)           → HTTP 200  {'error': 1}
  token PEMBACA  (bukan pemilik) → HTTP 403  {'detail': 'Token tidak valid'}
```

**Artinya:**
- Pagar bekerja **di SERVER**, bukan cuma di tampilan → **tidak bisa ditembus**.
- Pembimbing **tidak bisa** menyimpan naskah orang walau mengganti URL.
- **NOL kode baru** diperlukan untuk pagar ini — sudah otomatis benar.

---

## 3. DUA TEMUAN YANG MENGUBAH RENCANA

### TEMUAN 1 — `mode` DIHITUNG di dalam, BUKAN parameter masukan

```python
# app/onlyoffice.py::konfigurasi_editor()
# parameter masuk : kunci, nama, url_unduh, url_simpan, user_id, user_nama, extensi
# variabel lokal  : dok_tipe, mode, cfg
def konfigurasi_editor(*, kunci, nama, url_unduh, url_simpan, ...):
    dok_tipe, mode = tipe_dokumen(nama)   # ← mode dari EKSTENSI
```

`.docx` → **selalu** `edit`.

**⚠️ KOREKSI PENTING:** catatan awal Wulan *"fungsi TIDAK punya parameter mode"*
= **KURANG TEPAT**. Yang benar: `mode` **ADA** sebagai variabel lokal, tetapi
**bukan parameter masukan**. Wulan hampir menyesatkan diri sendiri.

**⇒ YANG DIBUTUHKAN:** tambah **parameter masukan** (mis. `mode_baca: bool = False`).
Titik sentuh kode **kecil & jelas** — **bukan** mesin mode baru.

### TEMUAN 2 — `mode='view'` MEMATIKAN KOMENTAR

```text
mode='view' → permissions: edit=false, comment=FALSE
                              ^^^^^^^^^^^^^^^^^^^^^^^^
              pembimbing TIDAK BISA komentar
              padahal komentar = INTI fiturnya
```

Terukur (A8): **keenam permission** (`edit`, `review`, `comment`, `fillForms`,
`modifyFilter`, `modifyContentControl`) = `(mode == 'edit')`. Jadi `mode='view'`
mematikan semuanya sekaligus — **termasuk komentar**.

**⇒ SOLUSI BENAR (V2):** pembimbing **bukan** `mode='view'`, melainkan:

```python
mode = 'edit'
document.permissions = {
    'edit': False,                    # ← TULIS MATI
    'comment': True,                  # ← KOMENTAR HIDUP
    'review': True,                   # ← usul perubahan hidup
    'download': True,
    'print': True,
    'copy': True,
    'fillForms': False,
    'modifyFilter': False,
    'modifyContentControl': False,
}
```

**⇒ Andaian awal "matikan semua tombol" SALAH.** Yang benar: matikan **tulis**,
hidupkan **komentar**.

---

## 4. JEBAKAN ALAT UJI (7 lapis, semua terukur — agar tidak terulang)

Uji LAYAR (banding V1 vs V2) **belum tuntas** karena alat uji CDP cacat:

| # | Jebakan | Pelajaran |
|---|---|---|
| 1 | `potret_cdp.tab_baru()` **TIDAK menavigasi** | pemanggil WAJIB `Page.navigate` sendiri |
| 2 | Browser uji **tak punya internet keluar** | `fetch` domain GAGAL → layani berkas dari server sendiri |
| 3 | iframe OO minta `/documenteditor/main/index.html` | jalur benar `/web-apps/apps/documenteditor/main/index.html` |
| 4 | OO **302** ke jalur **berversi** `/<cap>/web-apps/...` | ikuti redirect (`fetch` `redirect:'follow'`) |
| 5 | **Beda asal** `127.0.0.1:8099` vs `172.17.0.3` | Chrome tolak `contentDocument` → halaman uji WAJIB **satu asal** |
| 6 | Jalur berversi = **VIRTUAL** (nginx), bukan folder | halaman statis ditaruh di `/var/www/onlyoffice/documentserver/web-apps/` |
| 7 | Asal `172.17.0.3` bukan hostname sah → **editor stuck skeleton** | **BELUM tertembus** → uji layar harus lewat produksi |

**Catatan penting:** jebakan 1–7 adalah **cacat alat uji Wulan**, **BUKAN** cacat
produk. Bukti: produksi sehat (beranda 200), OO hidup (judul + 324.154 aksara),
semua berkas inti 200.

---

## 5. CARA UJI YANG DISARANKAN (pelajaran utama)

> **Uji pagar TIDAK PERLU halaman uji.**

Cukup **POST ke rute yang sudah ada** (`/oo/simpan/{token}`) lewat domain.
Keuntungan terbukti:
- **Nol berkas** ditambahkan ke produksi.
- Asal **sah** (domain asli) → hasilnya berlaku untuk produksi.
- Tidak perlu membangun apa pun.

Ini menggantikan rencana awal *"taruh halaman uji sementara di produksi"* —
**lebih aman dan lebih jujur**.

---

## 6. YANG BELUM TERBUKTI (jujur)

```text
1. Banding VISUAL V1 vs V2 di layar (tombol benar-benar mati? komentar hidup?)
```

**Mengapa belum:** alat uji CDP cacat (jebakan 1–7). **Mengapa tidak mendesak:**
A8 sudah membuktikan keenam permission ikut **satu nilai `mode`** — jadi perilaku
V2 sudah dapat dipastikan dari data, bukan dari gambar.

**Kapan dikerjakan:** saat fitur benar-benar dikode (uji penerimaan).

---

## 7. ARTI HASIL INI BAGI RENCANA

| Pertanyaan Bos | Jawaban berbukti |
|---|---|
| Pembimbing bisa tembus & ubah naskah orang? | **TIDAK** — 403 di server ✅ |
| Alat sama (OnlyOffice) bisa buat pembimbing? | **BISA** — cukup 1 parameter ✅ |
| Apakah mode baca mematikan komentar? | **YA kalau `mode='view'`** → pakai `edit=False+comment=True` ⚠️ |
| Perlu mesin/tabel/jalur baru? | **TIDAK** — cukup 1 parameter ⚠️ |
| Klaim "nol kode" masih sah? | **BATAL** — ada 1 titik sentuh kecil, jujur ✅ |

---

## 8. BERKAS TERKAIT

**Skrip uji:**
- `_sketsa/uji_mode_baca.py` — uji dalam container (TERBUKTI, 5 pemeriksaan)
- `_sketsa/uji_lewat_produksi.py` — **uji lewat domain (TERBUKTI)**
- `_sketsa/layar_uji_host.py` — halaman uji 2 varian (macet di jebakan 7)
- `_sketsa/siapkan_uji_satu_asal.py` — halaman uji satu-asal
- `_sketsa/potret_lama_oo.py` · `bukti_oo_hidup.py` · `tanya_editor.py` — penyelidik

**Dokumen:**
- `RENCANA_PEMBIMBING_AI_SEDERHANA.md` §12b (hasil uji)
- `FLAG_LANJUT_DISINI.md` (blok uji di paling atas)
- skill `eduai-publishing` → `references/pembimbing-ai-alat-sama-02okt2026.md`

**Cadangan:** `_arsip/pre-uji-dokumen-20261003-0125/` + `_arsip/pre-alat-sama-20261002-1511/`

**Kode yang diselidiki (TIDAK diubah):**
- `app/onlyoffice.py` ~73 (`konfigurasi_editor`), ~96–104 (dict permissions), ~1553 (`_token_berkas`)
- `app/main.py` 1986 (`/oo/unduh`), 2080 (`/oo/simpan`) — pagar baris 2088–2093

---

## 9. ATURAN KESELAMATAN YANG DIPATUHI

```
✅ Backup dulu sebelum ubah berkas (_arsip/pre-uji-dokumen-20261003-0125/ + MD5)
✅ Produksi TIDAK disentuh — nol berkas uji, nol perubahan kode
✅ Nol deploy
✅ Kredensial tidak pernah dicetak (token hanya dipotong __16__ di luar container)
✅ Container eduai-app & oo-converter: running, restart=0
✅ Setelah uji: halaman uji dihapus, proses dibersihkan, tab CDP dikosongkan
```

---

**Kesimpulan:** andaian inti rencana Pembimbing AI **SAH**, dengan **2 koreksi**
(parameter mode + komentar tidak boleh mati). Fitur **bisa dikode** tanpa mesin baru.
