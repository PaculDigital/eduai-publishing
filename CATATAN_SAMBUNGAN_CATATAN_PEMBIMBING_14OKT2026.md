<!-- SOT: CATATAN_SAMBUNGAN_CATATAN_PEMBIMBING_14OKT2026 -->

# CATATAN POSISI — SAMBUNGAN CATATAN PEMBIMBING → PETA JEV
### 14 Okt 2026 · status: RANCANGAN SIAP, BELUM DIKODING

> Perintah Bos: "catat dulu, dan saya mau kamu jelaskan mekanismenya dan
> sinkronisasi sistem sekarang. Dan kenapa beda dengan yang sudah ada?"

---

## A. POSISI SEKARANG (apa yang sudah jadi hari ini)

| # | Perkara | Status | Bukti |
|---|---|---|---|
| 1 | Optimasi putaran Jev 3→1 | ✅ TAYANG | 161 dtk → 54 dtk; bab 70 → 80 |
| 2 | Jev tidak dipanggil berulang | ✅ TERBUKTI | 55,6 dtk → 0,0 dtk (uji 6/0) |
| 3 | Naskah rusak tidak bayar Jev | ✅ TAYANG | Rp 111 → Rp 0 (gerbang 15/0) |
| 4 | Rapikan `section_id` catatan | 🟡 RANCANGAN | `RANCANGAN_RAPI_BAB_14OKT2026.md` |

Image produksi: `eduai-app:20261014_071115-sot`
Mundur: `eduai-app:cadangan-pra-sot`

---

## B. MEKANISME SEKARANG — catatan pembimbing (baca dari kode)

### B1. Catatan MANUAL (pembimbing tulis sendiri)
```
Berkas : app/pembimbing.py  →  catat()
Biaya  : Rp 0 — TANPA token
Peta   : TIDAK dipakai (bebas, benar)
Simpan : catatan_pembimbing (section_id = apa yang pembimbing tulis APA ADANYA)
```

### B2. Catatan AI (pembimbing klik "Periksa dengan AI")
```
Berkas : app/kolaborasi.py:155 → asisten.kerjakan()
         app/asisten.py:179   → AI._panggil_router(system=RUBRIK)
Biaya  : 1 Token Revisi (HARGA_TOKEN=1, asisten.py:37)
Naskah : SELURUH teks[:40_000]  (asisten.py:147)
Peta   : TIDAK dipakai
Simpan : simpan_usulan() → catat(), section_id = u['bab'] dari AI (APA ADANYA)
```

### ⚠️ Temuan: 2 jalur ini BELUM SINKRON

| Hal | Catatan MANUAL | Catatan AI |
|---|---|---|
| Pakai peta Jev? | ❌ tidak | ❌ tidak |
| `section_id` seragam? | ❌ tidak (`'bab iii'`, `'BAB 3'`) | ❌ tidak |
| Bisa dicocokkan ke peta? | ⚠️ 6/8 cocok setelah dirapikan | belum diukur |

⇒ **Keduanya berdiri sendiri** — tidak menempel ke peta Jev yang sudah ada.

---

## C. MEKANISME SESUDAH DISAMBUNG (usul Wulan)

```
① Pembimbing beri catatan (manual gratis / AI bayar 1 Token)  [SUDAH ADA]
              ↓
② rapi_bab() : 'bab iii' / 'BAB 3' / 'BAB I'  →  '3' / '1'     [BARU, ±15 baris]
              ↓
③ Cocokkan ke PETA JEV tersimpan (`peta_json`)                 [SUDAH ADA]
   · Rp 0, 0 detik (peta tidak dihitung ulang — PAGAR C2)
   · dapat: judul bab + nomor bab dari peta
              ↓
④ Mahasiswa klik "Revisi pakai AI"                             [SUDAH ADA, ai.py:2449]
   · AI terima: bab itu + TETANGGA + catatan pembimbing
   · `konteks.py` (bangun_prompt) — SUDAH ADA
   · Hemat 91% (terukur 25 Sep)
```

⇒ **Yang baru cuma LANGKAH ②** (±15 baris). Sisanya sudah ada.

---

## D. KENAPA BEDA DENGAN YANG SUDAH ADA?

| | Yang ADA sekarang | Yang DIUSUL |
|---|---|---|
| **Pembimbing manual** | tulis bebas, `section_id` apa adanya | **TETAP bebas** (tidak diubah) + section_id **dirapikan** |
| **Pembimbing AI** | kirim SELURUH naskah 40rb kar | **tetap sama** (belum diubah di usul ini) |
| **Catatan → peta Jev** | ❌ tidak nyambung | ✅ **nyambung** |
| **Revisi AI mahasiswa** | dapat bab dari teks (`_petakan2`) | dapat bab **dari catatan pembimbing** juga |
| **Mesin baru?** | — | **NOL** — cuma 1 fungsi kecil |
| **Tabel/kolom baru?** | — | **NOL** |
| **Jev dipanggil lagi?** | — | **TIDAK** (peta sudah tersimpan) |
| **Biaya tambahan** | — | **Rp 0** |

**Inti bedanya:** sekarang **2 jalur berdiri sendiri-sendiri** —
catatan pembimbing **tidak tahu** peta Jev, dan revisi mahasiswa
**tidak tahu** apa yang pembimbing komentari.

Sesudah disambung: **SATU rantai** —
pembimbing komentar → catatan punya bab pasti → mahasiswa revisi
**langsung pada bab itu**.

---

## E. HASIL UKUR (Rp 0, data produksi nyata)

Uji: 9 catatan pembimbing produksi → cocokkan ke peta Jev.

| id | pembimbing tulis | cocok ke peta? |
|---|---|---|
| 172, 173 | `BAB I` | ✅ bab 1 PENDAHULUAN |
| 174 | `BAB II` | ✅ bab 2 |
| 175, 177 | `BAB III`, `bab iii` | ✅ bab 3 |
| 176 | `BAB 3` | ✅ bab 3 (persis) |
| 178 | `BAB IV` | ❌ peta cuma punya 3 bab |
| 179 | *(kosong)* | ❌ tidak menunjuk bab |

**⇒ 6 dari 8 cocok (75%).**

**2 yang gagal BUKAN bug:**
- `BAB IV` → naskah itu memang cuma 3 bab
- `''` → catatan itu cuma "perbaiki daftar pustaka", tidak menunjuk bab

**Dan temuan kedua:** dari 9 catatan, **cuma 1 punya `teks_asli`** (8 kosong).
⇒ Jadi **tidak bisa** mencocokkan "kalimat yang disorot" ke peta —
lagi pula peta Jev **tidak menyimpan teks naskah** (cuma bab/judul/masalah).

---

## F. YANG BELUM DIKERJAKAN (jujur)

```
⬜ rapi_bab() + gerbang          ← menunggu izin Bos
⬜ Kalimat di LAYAR: "peta pakai mode hemat" (kotak mutu sudah ada)
⬜ Uji mutu revisi AI: potongan vs penuh (utang dari 25 Sep, dokumen baris 488)
⬜ Asisten pembimbing AI masih kirim SELURUH naskah (asisten.py:147)
⬜ Disk VPS 96% penuh (sisa 3,1 GB) — belum diberesi
```

---

## G. BERKAS TERKAIT

```
RANCANGAN_RAPI_BAB_14OKT2026.md      rancangan 1 halaman (detail kode)
PAGAR_MUTU_PETA_DAN_HEMAT_JEV_14OKT2026.md   hasil hari ini (pagar mutu)
_sketsa/ukur_peta_catatan.py         skrip ukur (Rp 0)
_arsip/usang-10okt26/RENCANA_KOLABORASI_PEMBIMBING_23SEP2026.md  rancangan lama
app/pembimbing.py::catat()           catatan manual
app/asisten.py::simpan_usulan():297  catatan AI
app/ai.py:2449                       revisi AI (konteks.py sudah dipakai)
```

---

## H. KEPUTUSAN YANG DITUNGGU

Bos pilih:
- **A** — pasang `rapi_bab()` sekarang (lapor dulu, deploy tunggu izin)
- **B** — ubah dulu rancangannya
- **C** — simpan, kerjakan lain waktu
