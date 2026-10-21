<!-- SOT: AUDIT_SINKRON_BACKEND_FRONTEND_14OKT2026 -->

# AUDIT SINKRON BACKEND ↔ FRONTEND — 14 Okt 2026

> **STATUS: SELESAI (A + C).** Deploy #10 `eduai-app:20261014_021448-sot` tayang.
> Gerbang `_gerbang_bersih_rute_14okt.py` 5/5 BERGIGI. Mundur:
> `eduai-app:cadangan-pra-bersih-kembar`.
> ✅ Dikerjakan: `/api/ai/v1/addon` dicabut (salinan lama).
> ⏸️ 6 rute hidup tanpa pintu **belum** dikerjakan (daftar di bawah).

---

# 🔴 KOREKSI — BACA INI DULU (14Okt26, sesudah diperiksa lebih dalam)

Dua temuan di bawah **TERBUKTI SALAH**. Yang benar:

### ❌ Koreksi 1: "`/alur/dokumen-baru` = rute MATI (404)" → SALAH

Alamat yang benar: **`POST /api/ai/v1/alur/dokumen-baru`** (router `rute_alur`
dipasang prefix `/api/ai/v1` di `main.py:92`). Bukti produksi: **401 = HIDUP**.

**Yang benar:** rute **HIDUP** tapi **0 panggilan di layar** ⇒ masuk keranjang
**"ada mesin, tak ada pintu"** — kelas yang SAMA dengan Peta Naskah.
(Fungsi "bikin naskah kosong OPSI D — GRATIS", `rute_alur.py:486`, gerbang 42/0.)

### ❌ Koreksi 2: "`/v1/kuota` = KEMBAR dengan `/api/kuota`" → SALAH

| Rute | Urusan |
|---|---|
| `GET /api/kuota` (`main.py:1433`) | kuota **PENYIMPANAN** (MB) — dipakai `mulai.html` |
| `GET /api/ai/v1/kuota` (`ai.py:1303`) | kuota **REVISI AI** (token/ledger) |

Nama mirip, **urusan beda total**. Menghapus salah satu = menghapus fitur.
**TIDAK disentuh.**

### ❌ Koreksi 3: "`/v1/kunci` kembar dengan `/pembimbing/kunci`" → BUKAN kembar

`/pembimbing/kunci` (`rute_bagikan.py:308/326`) = **kunci bimbingan** (pembimbing
mengunci naskah mahasiswa). `/v1/kunci` (`ai.py:3521`) = **cek "dokumen terkunci
karena AI bekerja"**. Beda urusan. `/v1/kunci` memang 0 panggilan, tapi
tugasnya sudah tertutup **2 jalur lain** (`GET /v1/proses` untuk spanduk editor;
Lapis 2 di `/v1/terapkan` yang menolak 409). **Tidak dihapus** (cadangan aman).

### ✅ Yang TERBUKTI benar & SUDAH dikerjakan

**`GET /api/ai/v1/addon` (`ai.py:1315`) = SALINAN LAMA → DIHAPUS 14Okt26.**
Bukti: 0 pemanggil di seluruh proyek; layar memakai `GET /api/addon`
(`main.py:1946`, `_topup_popup.html:563`); versi `main.py` lebih kaya
(`saran`, `qris_aktif`). Diganti catatan penunjuk di `ai.py`.
Backup: `_arsip/pre-bersih-kembar-<stamp>/`.

**Pelajaran:** "kembar" **wajib dibuktikan dengan membandingkan ISI**, bukan
nama rute. 2 dari 3 tuduhan kembar Wulan ternyata salah.

---

**Pertanyaan Bos:** *"Cek dan audit di kode, mana yang sudah ada di kode tapi belum ada pintunya di frontend, dan belum sinkron antara backend dan frontend."*

**Cara kerja (terukur, bukan tebak):**
1. Baca **114 rute backend** nyata (dekorator `@router/@app.get|post`).
2. Baca **42 berkas layar** (`templates/*.html` + `static/*.js`, ~1,05 juta karakter).
3. Cocokkan tiap rute ke jejak layar (fetch / form action / href).
4. **Uji HIDUP** ke produksi (`eduai-app:20261014_013133-sot`): 303/401 = hidup, 404 = mati.
5. Arah sebaliknya: semua `fetch()` di layar → cek 404 (pemanggil yatim).

---

## A. RUTE HIDUP — TIDAK PUNYA PEMANGGIL DI LAYAR

Semua di bawah ini **terbukti hidup** (jawab 401 = butuh login), tapi **nol**
pemanggil di layar:

| Rute | Lokasi | Gunanya | Bukti |
|---|---|---|---|
| `POST /api/ai/v1/peta/mulai` | `ai.py:4277` | **Peta naskah** (bab/sub-bab/paragraf) — fitur PUTUSAN BOS 08Okt26 | 0 panggilan `peta` di seluruh layar |
| `POST /api/ai/v1/peta/kerjakan` | `ai.py:4421` | Jalankan peta | idem |
| `POST /api/ai/v1/kunci` | `ai.py:3521` | Cek dokumen **sedang dikunci** AI (modal skeleton) | hanya fungsi lokal `kunciTombol()` di `tinjau.html` (soal lain) |
| `GET /api/ai/v1/addon` | `ai.py:1315` | Daftar AddOn + boleh beli | layar pakai `/api/addon` (rute **BERBEDA** di `main.py:1946`) |
| `GET /api/ai/v1/kuota` | `ai.py:1303` | Sisa kuota (widget progress bar) | layar pakai `/api/kuota` (`main.py`) — **rute berbeda** |
| `POST /api/ai/v1/kerangka/rencana` | `ai.py:4043` | Rencana kerangka (versi lama) | **0 jejak sama sekali** |

### 🔴 TEMUAN PALING PENTING: **DUPLIKAT RUTE**

Ada **TIGA pasang rute kembar** — satu di `main.py`, satu di `ai.py`, untuk
fungsi yang SAMA. Layar memakai yang di `main.py`; versi di `ai.py` jadi
**kode menganggur** (hidup, tapi tak pernah dipanggil):

| Fungsi | Versi DIPAKAI layar | Versi MENGANGGUR |
|---|---|---|
| Daftar AddOn | `GET /api/addon` (`main.py:1946`) | `GET /api/ai/v1/addon` (`ai.py:1315`) |
| Kuota | `GET /api/kuota` (`main.py`) | `GET /api/ai/v1/kuota` (`ai.py:1303`) |
| Kunci dokumen | `/pembimbing/kunci` | `POST /api/ai/v1/kunci` (`ai.py:3521`) |

⚠️ **Ini bahaya SUNGGUHAN:** dua rute kembar = dua tempat yang harus diubah
kalau aturannya berubah. Kalau nanti Wulan/Bos mengubah yang `ai.py` (karena
kirain itu yang dipakai), **layar tidak berubah** — dan sebaliknya. Ini akar
"perbaikan tidak terasa" yang mungkin pernah terjadi.

---

## B. RUTE MATI (404) YANG MASIH TERTULIS DI KODE

| Rute | Lokasi | Sebab |
|---|---|---|
| `POST /alur/dokumen-baru` | `rute_alur.py:486` | Router didaftarkan prefix `/api/ai/v1` (`main.py:92`), tapi rute ini **tidak diawali `/v1/`** ⇒ alamat akhirnya tak cocok ⇒ **404** |

Fungsi "Bikin naskah kosong (OPSI D) — GRATIS" (`rute_alur.py:486`) **sudah
ditulis lengkap tapi MUSTAHIL dipanggil**. 0 jejak di layar juga.

---

## C. PEMANGGIL YATIM — 8 kandidat, **SEMUA PALSU** ✅

Layar memanggil `/edit/`, `/artikel/X`, `/tinjau/`, `/pembimbing/arsip/`,
`/api/ai/v1/jurnal/` → semua **404** di uji pertama.

**Sebabnya bukan bug** — semuanya **konkatenasi** yang benar:

```js
window.location.href = '/edit/' + S.fileId;          // mulai.html:461
var rc = await fetch('/pembimbing/log/' + idc);      // naskah.html:1677
const r = await fetch('/api/ai/v1/jurnal/' + jalur, opsi);  // referensi.html:329
```

⇒ Alat ukur Wulan yang salah (memotong URL sebelum id terpasang).
**Kesimpulan: NOL pemanggil yatim.** Sisi ini sehat.

---

## D. YANG SEHAT (tidak perlu disentuh)

- 86 rute **terpakai** dengan panggilan nyata di layar.
- Panel Asisten AI (`editor.html`) sudah tersambung lengkap: `proses`, `baca`,
  `bab`, `hitung`, `mundur`, `petunjuk`, `revisi`, `terapkan`, `versi`.
- Alur pembimbing (`/tinjau/*`) tersambung penuh (11 titik).
- Konversi artikel (`/artikel/{fid}/konversi|revisi`) tersambung (`artikel.html`).

---

## RINGKASAN 1 KALIMAT

Ada **6 rute hidup tanpa pintu** (terbesar: **Peta Naskah** — putusan Bos
08Okt26 yang mesinnya sudah ada tapi pintunya belum pernah dibuat), **1 rute
mati** (`/alur/dokumen-baru` — salah prefix), dan **3 pasang rute kembar**
(`addon`, `kuota`, `kunci`) yang berbahaya karena perbaikan bisa masuk ke
salinan yang salah.

**TIDAK ADA** pemanggil yatim di layar.
