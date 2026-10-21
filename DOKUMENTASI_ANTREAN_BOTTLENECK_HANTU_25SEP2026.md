# 🚨 MEKANISME ANTREAN, BOTTLE NECK & PROSES HANTU — EduAi

<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


**Tanggal:** 25 September 2026
**Status:** ✅ SUDAH DEPLOY — image `eduai-app:20260925_092320-sot`
**Domain:** https://eduai.bikinaja.id

---

## 1. RINGKASAN SATU HALAMAN

| Pertanyaan | Jawaban TERUKUR |
|---|---|
| Kenapa revisi mahasiswa lama sekali (420-460 dtk)? | **ANTREAN MACET** karena slot bocor oleh proses hantu |
| Apakah model AI-nya lambat? | **TIDAK** — terbukti 9-47 dtk untuk naskah 55rb kar |
| Apakah 9router/EduAi combo lambat? | **TIDAK** — 15-22 dtk, 4/4 panggilan sukses |
| Apakah fallback OpenRouter (ling-3) tidak mampu? | **TIDAK** — 17,4 dtk, PATUH bentuk pipa |
| Apakah naskah terlalu besar? | **TIDAK** — 55.440 kar diproses 17-47 dtk |
| Apakah batas sabar 180 dtk kurang? | **TIDAK** — 4× lebih lama dari kebutuhan |
| Jadi apa akarnya? | **PROSES HANTU menahan slot antrean** |

**Angka sebelum vs sesudah:**

```
SEBELUM : 420-460 dtk · status=gagal · token_in=0  · kuota hangus
SESUDAH : 31 dtk       · status=selesai · token_in=30.494 · kuota tepat 4
```

---

## 2. CARA KERJA ANTREAN (mekanisme)

```
Mahasiswa tekan tombol revisi
        │
        ▼
POST /api/ai/v1/revisi  →  balas 200 dlm 0,3 dtk (tidak menunggu AI)
        │                  (Cloudflare tidak pernah memutus koneksi)
        ▼
proses_mod.mulai()  →  baris DB status='menunggu'
        │
        ▼
proses_mod.jalankan(kode, kerja)
        │
        ▼
_antre_atau_jalan(kode, kerja)
        │
        ├── _sedang_jalan < KONKUREN_MAKS (8) → LANGSUNG
        │       _sedang_jalan += 1
        │       ubah_tahap(kode, 'Mulai bekerja')
        │       _utas(kode, kerja)     ← utas + event loop sendiri
        │
        └── PENUH → MASUK ANTREAN
                _antrean.append(kode)
                ubah_tahap(kode, 'Menunggu antrean (posisi N dari M)')
                ⚠️ TIDAK ADA yang menjalankannya sampai `_selesai_satu()`
                   dipanggil oleh proses yang SEDANG jalan.
```

### Slot dilepas di mana?

```
_utas() → _bungkus() → finally:
    1. loop.close()
    2. _tutup_bila_menggantung(kode)   ← 🛡️ PENJAGA BARU 25Sep26
    3. _kerja_terdaftar.pop(kode)
    4. _selesai_satu()                 ← kunci antrean maju
```

**Aturan mutlak:** slot WAJIB dilepas di `finally`. Kalau tidak, antrean mandek.

---

## 3. AKAR BOTTLE NECK — PROSES HANTU

### 3.1 Apa itu proses hantu?

Baris DB `proses_ai` dengan `status='jalan'` **TANPA utas hidup** yang menjalankannya.

### 3.2 Bagaimana hantu lahir?

```
Kondisi A: container dimatikan mendadak saat revisi sedang jalan
           → utas ikut mati → baris DB tetap 'jalan' SELAMANYA
Kondisi B: exception di luar try bungkus _utas
Kondisi C: proses induk (uvicorn) di-restart tanpa pembersihan
```

### 3.3 Kenapa hantu MEMATIKAN semuanya?

```
1 hantu  → menahan 1 slot  (dari 8)   → masih jalan
...
8 hantu  → slot HABIS (_sedang_jalan = 8 = KONKUREN_MAKS)
         → SEMUA permintaan baru masuk _antrean
         → 'Menunggu antrean' muncul di layar mahasiswa
         → TIDAK PERNAH dilayani, karena _selesai_satu() hanya dipanggil
           oleh proses YANG SEDANG JALAN — dan tidak ada yang jalan!
         → ⛔ ANTREAN MACET TOTAL
         → mahasiswa tunggu 180 dtk (jalur 1) + 240 dtk (jalur 2)
         → 420-460 dtk → HTTP 503 → K U O T A   H A N G U S
```

### 3.4 BUKTI NYATA dari DB produksi (25Sep26)

```
Proses 118 (yxYpSle2GqaWsim6gcrZLw)
   dibuat   : 2026-09-25 08:52:26
   status   : 'jalan'
   diperiksa: 1 JAM kemudian → MASIH 'jalan'
   utas hidup: TIDAK ADA                           ← HANTU ✅ TERBUKTI

Pola proses gagal (113/115/117):
   112 selesai 07:43:36 → 113 gagal 07:43:39  (3 dtk kemudian)
   114 selesai 08:02:48 → 115 gagal 08:02:51  (3 dtk kemudian)
   116 selesai 08:13:28 → 117 gagal 08:13:30  (2 dtk kemudian)
   Semua gagal: token_in=0, durasi 420-460 dtk
```

---

## 4. CARA DIAGNOSA (resep yang terbukti)

### 4.1 Urutan ukur yang BENAR (dari yang paling murah)

```
1. Uji LANGSUNG fungsi AI      ← WAJIB pakai SYSTEM_REVISI penuh!
      app.ai._panggil_9router / _panggil_openrouter
   → kalau SEHAT (9-47 dtk), JANGAN tuduh AI-nya.

2. Uji E2E fungsi _revisi_kerja langsung (tanpa HTTP)
   → kalau SEHAT (20 dtk), JANGAN tuduh logika revisinya.

3. Uji E2E lewat HTTP endpoint SUNGGUHAN + sadap httpx
   → BARU ketemu masalah antrean/worker di titik ini.

4. BACA DB: proses_ai.token_in
   → token_in = 0  ⇒  AI TAK PERNAH DIPANGGIL
   ⇒ waktu habis SEBELUM AI  ⇒  masalah ANTREAN / MAKET / UTAS
   ⇒ BUKAN masalah model, BUKAN masalah provider.
```

### 4.2 Tanda-tanda khas (hafalkan)

| Gejala | Arti |
|---|---|
| `token_in = 0` + durasi ~420-460 dtk + status gagal | **ANTREAN MACET / hantu** — bukan AI |
| Durasi ~420 dtk = **180 + 240 PERSIS** | batas jalur 1 + batas jalur 2 habis berturut-turut |
| `status='jalan'` di DB > 10 menit tanpa panggilan AI | **HANTU** |
| Antrean bilang "posisi N dari M" padahal M kecil & tak maju | slot bocor |
| `_sedang_jalan` turun ke 0 tapi ada status 'jalan' di DB | hantu (utas sudah mati) |

### 4.3 Alat diagnosa yang dibuat (di `_sketsa/`)

```
ukur_waktu_http.py     → jalur HTTP sungguhan + sadap httpx + urutan waktu
tangkap_jejak_utas.py  → rekam tandai_gagal + rekam _revisi_kerja
tangkap_hasil_kerja.py → lihat NILAI BALIK _revisi_kerja di jalur latar
bukti_slot_macet.py    → buktikan slot bocor naik & tak turun
uji_status_utas.py     → UJI 2 ARAH: gagal → ditutup? sukses tanpa tandai → hantu?
bersihkan_slot_bocor.py→ bersihkan + buktikan antrean kembali normal
e2e_latar_httpx.py     → E2E endpoint + log httpx
ukur_bottleneck.py     → pecah ukuran tiap blok user_msg (cari blok raksasa)
e2e_domain.py          → E2E lewat DOMAIN PRODUKSI (bukti akhir)
```

### 4.4 ⚠️ JEBAKAN ALAT UJI (jangan terulang)

```
❌ Wulan memanggil `_revisi_kerja` LANGSUNG (tanpa pembungkus `_kerja`)
   → `tandai_selesai` tak pernah dipanggil
   → penjaga hantu menutupnya jadi 'gagal' (padahal SUKSES!)
   → WULAN HAMPIR MELAPORKAN INI SEBAGAI BUG #13 di produksi.

✅ CEK DULU kode produksi: `app/ai.py:2749` SUDAH memanggil
   `proses_mod.tandai_selesai(...)` dengan benar di dalam `_kerja`.
   Yang kurang: HANYA di skrip uji Wulan.
```

**ATURAN:** sebelum menuduh aplikasi · pastikan KASUS UJINYA sah, bukan cacat skrip.

---

## 5. PERBAIKAN (2 lapis, bukan tambalan)

### Lapis 1 — penjaga di `finally` utas (`app/proses.py`)

```python
def _utas(kode, kerja):
    def _bungkus():
        ...
        finally:
            loop.close()
            #  🛡️ PENJAGA HANTU
            try:
                _tutup_bila_menggantung(kode)
            except Exception:
                log.exception('[proses] penjaga hantu gagal (kode=%s)', kode)
            _kerja_terdaftar.pop(kode, None)
            _selesai_satu()
```

`_tutup_bila_menggantung(kode)`: kalau status masih `'jalan'`/`'menunggu'`
→ tandai gagal + **KEMBALIKAN KUOTA** + pesan jujur ke mahasiswa.

### Lapis 2 — pembersih saat start-up (`app/main.py`)

```python
@app.on_event('startup')
def _startup():
    init_db()
    from .proses import bersihkan_hantu
    n = bersihkan_hantu()      # tutup hantu sesi sebelumnya + kuota balik
```

`bersihkan_hantu()`: tutup SEMUA baris `'jalan'` yang utasnya tak ada,
lalu **hitung ulang `_sedang_jalan` dari utas HIDUP** (bukan sisa angka lama)
dan kosongkan `_antrean`.

### Kenapa 2 lapis?

```
Lapis 1 : utas MATI MENDADAK saat app masih hidup
Lapis 2 : app/container DI-RESTART (utas semua mati bersamaan)
```

---

## 6. UJI PENJAGA (2 ARAH — WAJIB)

`_uji_hantu.py` — 8 LULUS / 0 GAGAL:

```
A. SISI SEHAT
   A1 kerja sukses + tandai_selesai → status 'selesai' ✅
   A2 kerja gagal (lempar)          → status 'gagal'   ✅

B. SISI RUSAK (inti AKAR #12)
   B1 kerja sukses TANPA tandai → PENJAGA menutup jadi 'gagal' ✅
      (kalau penjaga dibuang → status tetap 'jalan' = HANTU ❌)
   B1b pesan galat menyebut "kuota dibatalkan/dikembalikan" ✅
   B2 bersihkan_hantu() pada hantu buatan ✅
   B2b slot dihitung ulang dari utas hidup ✅
   B3 _sedang_jalan kembali 0 setelah semua utas selesai ✅
   B3b tak ada utas proses-ai tertinggal ✅
```

**BUKTI BERGIGI (suntik kerusakan):**

```
penjaga UTUH    → 8 LULUS / 0 GAGAL  ✅
penjaga DIBUANG → 6 LULUS / 2 GAGAL  ❌ (B1 & B1b gagal)
⇒ gerbang ini NYATA, bukan gerbang pura-pura
```

---

## 7. HASIL SESUDAH PERBAIKAN (bukti produksi)

### E2E lewat HTTP langsung (dalam container)

```
t+ 0,14s · MULAI: tekan tombol (HTTP POST)
t+ 0,40s · HTTP BALAS 200 · kode=qO9taA7tgYZ6va1NSZN79A
t+10,4s · status=jalan · "Menulis bagian ke-2 dari 2"
t+30,4s · status=SELESAI · model=cb/deepseek-v4.1-flash
```

### E2E lewat DOMAIN PRODUKSI (sesudah deploy)

```
health : 200
TEKAN TOMBOL : 200 dalam 0,29 dtk
   t+10,7s · Menulis bagian ke-1 dari 2
   t+20,9s · Menulis bagian ke-2 dari 2
   t+31,1s · SELESAI ✅

status       : selesai
durasi       : 31,1 dtk
model_ai     : cb/deepseek-v4.1-flash
token_in     : 30.494   (SEBELUMNYA 0!)
token_out    : 4.223
token_revisi : 4        ← TEPAT sesuai MASTER_PLAN §4.13
galat        : (kosong)
```

---

## 8. JEBAKAN OPERASIONAL

| Hal | Arti |
|---|---|
| Teks **"Menunggu antrean"** | **BUKAN error** — perilaku normal, mahasiswa dipindah ke FIFO |
| **HTTP 402 KUOTA_HABIS** | Kuota user uji habis, bukan bug → `UPDATE pemakaian_ai SET jumlah_revisi=0 WHERE user_id=N` (kolom `bulan`, BUKAN `periode`) |
| **`token_in = 0`** | AI tidak pernah dipanggil → cek ANTREAN dulu |
| **Durasi ~420 dtk** | = 180 (jalur 1) + 240 (jalur 2) PERSIS → dua-duanya habis |
| **_sedang_jalan = 8** | slot habis → cek hantu lewat DB vs `threading.enumerate()` |

### Perintah diagnosa cepat (produksi)

```bash
# 1. Ada hantu?
docker exec eduai-app python3 -c "
import sys; sys.path.insert(0,'/app')
from app import proses as P
print('slot :', P._sedang_jalan, '· antrean:', P.statistik_antrean())
"

# 2. Hantu di DB?
docker exec eduai-app python3 -c "
import sqlite3
c=sqlite3.connect('/app/data/eduai.db')
for r in c.execute(\"SELECT id,kode,dibuat,tahap FROM proses_ai WHERE status IN ('jalan','menunggu')\"):
    print(r)
"

# 3. Bersihkan (aman, kuota dikembalikan)
docker exec eduai-app python3 -c "
import sys; sys.path.insert(0,'/app')
from app.proses import bersihkan_hantu
print('ditutup:', bersihkan_hantu())
"
```

---

## 9. PELAJARAN INDUK

```
1. PINDAI SEMUA TITIK sebelum menuduh. Model → provider → prompt → naskah
   → antrean → DB. Wulan 2× menuduh model sebelum cek antrean — SALAH.

2. `token_in = 0` adalah PETUNJUK TERKUAT. Kalau AI tidak dipanggil,
   masalahnya di SISTEM, bukan di AI.

3. UJI 2 ARAH WAJIB. Gerbang yang tak bisa gagal = tidak menjaga apa pun.
   Bukti: penjaga dibuang → 6/2 GAGAL.

4. CACAT ALAT UJI ≠ CACAT APLIKASI. Cek dulu apakah kode produksi sudah
   memanggil fungsi dengan benar (ai.py:2749 BENAR).

5. SKRIP UJI BISA MEMBUAT MASALAH PRODUKSI. Hantu 118/120/122 lahir dari
   skrip uji Wulan sendiri. Jalankan di sesi terpisah + bersihkan sesudahnya.

6. PROSES BERSTATUS = PROSES HIDUP? TIDAK. Status di DB hanyalah CATATAN.
   Yang menentukan: apakah ada UTAS yang menjalankannya.
```

---

## 10. BERKAS TERKAIT

```
app/proses.py          — _utas, _tutup_bila_menggantung, bersihkan_hantu
app/main.py            — pembersih hantu di startup
app/ai.py              — _kerja (pembungkus yang memanggil tandai_selesai :2749)
_uji_hantu.py          — gerbang 2 arah (8/0, terbukti bergigi)
_sketsa/ukur_waktu_http.py    — diagnosa jalur HTTP
_sketsa/e2e_domain.py         — E2E domain produksi
_sketsa/bersihkan_slot_bocor.py — pembersih + bukti
_arsip/pre-deploy-20260925/   — backup 4 berkas + MD5
```

**Titik mundur:** image `eduai-app:cadangan-pra-sot` · DB `_arsip/pra-sot/20260925_092320-sot`
