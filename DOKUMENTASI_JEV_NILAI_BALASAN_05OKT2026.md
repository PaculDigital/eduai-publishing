# 🧠 JEV MENILAI BALASAN AI (05 Okt 2026) — PAGAR KE-2 UTK "AI MENGARANG"

> 🚩 **DIPERBARUI 07 Okt 2026 — CARA PAKAI JEV DI SINI SUDAH USANG.**
> Sebagian isi catatan ini dibuat waktu Wulan **belum membaca dokumentasi resmi**,
> jadi ada **klaim yang keliru & berbahaya** (mis. *"skema Jev tertutup / hanya 3 nama"*,
> *"Jev tidak stabil"*, *"hanya 2 tipe sah"*, *"criteria boleh string"*).
> ⇒ **ACUAN TUNGGAL cara pakai Jev sekarang:** `PANDUAN_PAKAI_JEV.md`
>   + skill `typesafe-jev` (dokumentasi RESMI `docs.typesafe.ai`).
> ⇒ Blok lama **TIDAK dihapus** (riwayat) — tapi **DILARANG dipakai sebagai panduan**.
> ⇒ Penjaga: `_gerbang_skema_jev.py` + `_uji_gigi_skema_jev.py`.



<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


**Perintah Bos:** "Kenapa tidak pasangin jev saja disitu? Untuk bantu?" → **A**.
**Status:** ✅ SELESAI & TERUJI JEJAK SUNGGUHAN (belum deploy).

---

## 1. MASALAH YANG DITUTUP

Gerbang uji menangkap **503** berulang di `_uji_publik_komentar` (E1):

```
komentar   : "Perbaiki tata bahasa dan ejaan paragraf"
paragraf   : 336 karakter
balasan AI : 6.094 karakter  → rasio 18×  ← AI MENGARANG naskah baru
```

Pagar `PANJANG_MAKS_KALI = 3.0` (pipa.py) **menolak** balasan itu + token
dikembalikan → **user AMAN**. **TAPI** user **gagal dapat revisi**, padahal
sebagian kasus rasio tinggi itu **SAH** (mis. "perdalam latar belakang" memang
wajar panjang).

## 2. AKAR (terukur, bukan dugaan)

| Temuan | Bukti |
|---|---|
| Pagar lama hitung dari **kotakan** → "perdalam" SELALU ditolak | `_arsip/pre-c7-pascapagar-20260928/pipa.py` |
| Diperbaiki 28Sep26 → hitung dari **paragraf** | `dasar = sum(len(paragraf[i]) for i in idx)` |
| Diperbaiki 29Sep26 → **lintas potongan** | komentar di `pipa.py` baris 385-390 |
| **Justru karena pagar dibetulkan**, balasan ngawur **baru kelihatan** | dulu semua ditolak → bug tersembunyi |

⇒ **503 ini BUKAN bug baru** — bug LAMA yang selama ini **tersembunyi di balik
pagar yang salah hitung**. Itu jawaban "kenapa baru sekarang muncul".

## 3. PEMBAGIAN TUGAS (putusan Bos)

```
AI balas → PAGAR ARITMATIKA (Python, murni) MENYARING
              │  rasio ≤ batas  → LOLOS (tidak pernah sampai jev)
              │  rasio > batas  → JEV DIPANGGIL, MEMUTUSKAN
              ↓
        JEV: "ngawur atau wajar?"  (bukan mengukur ulang)
              │  ngawur / ragu / gagal  → TOLAK (perilaku lama)
              │  wajar & yakin ≥0,80    → LOLOS (user dapat revisi)
```

**Alasan Jev dipakai di sini, bukan sekadar pembanding angka:**
- Aritmatika **murah & tidak bisa mati** → saring dulu
- **"Ngawur atau wajar" = pertimbangan**, bukan hitungan → pekerjaan Jev
- Pola Satpam: **Jev mati → perilaku lama persis** (nol risiko)

## 4. PAGAR BARU (P6–P9)

| # | Pagar |
|---|---|
| **P6** | ARITMATIKA SELALU DULU — Jev tidak dipanggil kalau rasio wajar |
| **P7** | Jev ragu / gagal / balas sampah → **TOLAK** (pagar tetap kuat) |
| **P8** | Rasio > **batas keras 10×** → tolak **tanpa memanggil jev** |
| **P9** | Jev tidak menyentuh naskah — hanya memutuskan potongan itu |

## 5. BUKTI UJI

**A. 10 asersi (`_uji_jev_nilai_balasan.py`, 9router DIPALSUKAN) — 10 LULUS / 0 GAGAL**

Termasuk: jev dimatikan → tetap TOLAK (perilaku lama persis).

**B. JEJAK SUNGGUHAN (`_sketsa/uji_jev_nilai_nyata.py`) — 2/2 BENAR**

| Kasus | Rasio | Jev | Keyakinan |
|---|---|---|---|
| NGAWUR (BAB I & II baru) | 4,27× | **tolak** ✅ | **1,00** |
| SAH (perdalam 1 paragraf) | 2,71× | **lolos** ✅ | **0,81** |

## 6. JEBAKAN TERUKUR (jangan diulang)

1. 🚨 **BENTUK `questions` JEV WAJIB PUNYA `type`** = `'noul'` | `'choice'` | `'score'`.
   Tanpa `type` → OpenRouter HTTP 400 `invalid_union` → 9router 502 → app 503.
   **Bukan jev rusak — `questions` yang salah bentuk.**
2. 🚨 **`_urai_balasan` bisa kembalikan DUA bentuk**: `{jumlah_bab: …}` ATAU
   `{"answers": {jumlah_bab: …}}`. Kode WAJIB tahan dua-duanya
   (`if isinstance(jawab.get('answers'), dict): jawab = jawab['answers']`).
3. ⚠️ **Konstanta modul dimuat saat IMPORT** — mengubah `PERTANYAAN_NILAI` di
   berkas TIDAK berlaku sampai proses di-restart (Wulan hampir salah vonis).
4. ⚠️ **`log` TIDAK ADA di `pipa.py`** — dipakai patch → NameError → pagar bisa
   pecah. Ditambahkan `import logging` + `log = logging.getLogger(__name__)`.
5. ⚠️ Uji harus menirukan **SEMUA 3 pertanyaan** jev, bukan hanya satu.
6. ⚠️ Bentuk balasan jev NYATA = **bentuk AKAR** `{jumlah_bab: …}` (terbukti
   lewat `_sketsa/uji_jejak_jev_nyata.py`) → **satpam live AMAN**.

## 7. CATATAN JUJUR

- **Satpam live TIDAK cacat** — dibuktikan dengan panggilan nyata (keyakinan 0,84),
  bukan dari membaca kode.
- Peran `nilai_balasan()` **BELUM PERNAH dipakai produksi** — baru 2 jam dibangun.
  Kalau ragu/gagal, ia **tunduk ke pagar lama** (tolak), jadi nol risiko.
- Model `cb/deepseek-v4.1-flash` **tetap tidak stabil** (kadang 416 kar, kadang
  6.094 kar, kadang kosong). Jev **tidak memperbaiki model** — ia memutuskan
  nasib balasan yang sudah keluar.
- **Model #1 combo (`ds/deepseek-flash`) kredensial MATI** (1.509× gagal/24 jam)
  → urusan **panel 9router**, lihat `LAPORAN_PANEL_9ROUTER_05OKT2026.md`.

## 8. BERKAS

| Berkas | Keterangan |
|---|---|
| `app/satpam.py` | +`PERTANYAAN_NILAI`, +`nilai_balasan()`, +pagar P6–P9 |
| `app/pipa.py` | pagar panjang memanggil jev; +`import logging` |
| `_uji_jev_nilai_balasan.py` | 10 asersi (9router dipalsukan) |
| `_sketsa/uji_jev_nilai_nyata.py` | jejak sungguhan (2 kasus nyata) |
| `_sketsa/uji_jejak_jev_nyata.py` | pembuktian bentuk balasan jev |
| `_sketsa/cari_bentuk_questions.py` | pembuktian 4 bentuk `questions` diterima |
| `_sketsa/baca_galat_jev.py` | alat bongkar galat jev berlapis |
| `_arsip/pre-pagar-jev-<tgl>/` | backup + MD5 |
