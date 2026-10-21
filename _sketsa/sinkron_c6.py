import pathlib

BLOK = """
### ✅ C6 — DITUTUP 25Sep26 (fallback dipicu LAMBAT, bukan cuma GALAT)

**AKARNYA (terbaca dari kode, bukan dugaan):** `app/ai.py` `_panggil_router()`
hanya memindahkan ke jalur 2 (OpenRouter) kalau jalur 1 MELEMPAR GALAT. Kalau
jalur 1 NYANGKUT (lambat tanpa galat), tidak ada yang memindahkan → mahasiswa
menunggu `AI_TIMEOUT_DETIK` (420 dtk / 7 MENIT) lalu dapat "Layanan AI tidak
tersedia", padahal jalur 2 sehat.

**BUKTI KODE (sebelum):**
```
ai.py:684  try: panggil_9router(user_msg, timeout)   # timeout = 420
ai.py:686  except Exception -> fallback              # TIDAK ADA cek waktu
```
Tidak ada: batas "sudah terlalu lama", batas waktu terpisah per jalur, atau cek
"lambat" sebelum memanggil jalur 2.

**PERBAIKAN (ACC Bos "1") — BATAS SABAR:**
* `config.py`: `BATAS_SABAR_JALUR1 = float(os.getenv('EDUAI_AI_SABAR', '180'))`
* `.env`: `EDUAI_AI_SABAR=180`
* `ai.py` `_panggil_router()`: `jalur1_timeout = min(timeout, BATAS_SABAR_JALUR1)`
  → jalur 1 dibatalkan kalau lewat batas sabar → pindah jalur 2.
* Sisa waktu jalur 2 = `timeout` DIKURANGI waktu terpakai jalur 1, minimal
  `_MIN_SISA_JALUR2 = 30` detik.
* Log MEMBEDAKAN "LAMBAT" vs "gagal" supaya jejak jujur & bisa diaudit.

**ANGKA 180 DARI DATA NYATA** (bukan karangan): proses revisi yang SUKSES di
produksi tercatat **74 – 562 detik**. Batas 120 dtk akan MEMBUNUH proses yang
sebenarnya sehat (mis. proses tersingkat 74 dtk + waktu tunggu antrian).

**YANG TIDAK BERUBAH:** jalur 1 cepat → tetap jalur 1 · jalur 1 galat → tetap
pindah (perilaku lama) · rumus §4.13, kuota, alur — TIDAK disentuh.

**UJI `_uji_c6_sabar.py` — 20 asersi, BERGIGI 2 arah:**
```
SEHAT (image produksi)       → 20 LULUS / 0 GAGAL
pagar DICABUT (min() dibuang) → 17 LULUS / 3 GAGAL (1d, 1e, 5a)
   ↳ 1e membuktikan: tanpa pagar, mahasiswa menunggu 6,52 dtk untuk uji tiruan
pulih                         → 20 LULUS / 0 GAGAL
```
Ujinya MENGGANTI `_panggil_9router` dengan tiruan yang sengaja TIDUR, lalu
memanggil `_panggil_router()` SUNGGUHAN — jadi yang diuji perilaku nyata, bukan
teks kode. (Tanpa jaringan.)

⚠️ **CATATAN JUJUR:** uji ini TIDAK membuktikan jalur 2 benar-benar hidup di
produksi (butuh OpenRouter nyata). Yang dibuktikan: **perilaku pindah jalur**
benar. Kesiapan OpenRouter (`FALLBACK_AKTIF`) belum diuji ulang di sini.

**TAYANG:** image `eduai-app:20260925_010845-sot` · `/health` 200 ·
uji C6 20/0 di image produksi.
"""

PETA = pathlib.Path('PETA_PERCABANGAN_24SEP2026.md')
s = PETA.read_text()
if 'C6 — DITUTUP 25Sep26' not in s:
    # tandai tabel: C6 dari "tunggu ACC" -> selesai
    s = s.replace('| **C6** | Fallback AI dipicu GALAT bukan LAMBAT | dicatat, tunggu ACC |',
                  '| **C6** | ✅ **Fallback AI kini dipicu GALAT *dan* LAMBAT** | SELESAI 25Sep26 |',
                  1)
    anchor = '\n## 🧭 CARA MEMBUKTIKAN TIAP BARIS'
    s = s.replace(anchor, BLOK + anchor, 1) if anchor in s else s.rstrip() + '\n' + BLOK
    PETA.write_text(s)
    print('PETA: C6 ditutup')
else:
    print('PETA: sudah ada')

FLAG = pathlib.Path('FLAG_LANJUT_DISINI.md')
s = FLAG.read_text()
if 'C6' not in s:
    s = s.rstrip() + ('\n| **C6** | ✅ **DITUTUP 25Sep26** — fallback dulu HANYA dipicu GALAT; '
        'kalau jalur 1 nyangkut mahasiswa menunggu 420 dtk lalu gagal, padahal OpenRouter sehat. '
        'Kini ada BATAS SABAR `EDUAI_AI_SABAR=180` (dari data nyata: proses sehat 74-562 dtk), '
        'sisa waktu jalur 2 = timeout - terpakai (min 30 dtk). Uji `_uji_c6_sabar.py` 20/0 BERGIGI. '
        'Image `eduai-app:20260925_010845-sot`. |\n')
    FLAG.write_text(s)
    print('FLAG: C6 ditambah')

MP = pathlib.Path('MASTER_PLAN.md')
s = MP.read_text()
if 'C6 — BATAS SABAR' not in s:
    s = s.rstrip() + ('\n\n### C6 — BATAS SABAR jalur 1 (DITUTUP 25Sep26)\n\n'
        '`_panggil_router()` dulu hanya pindah ke jalur 2 kalau jalur 1 MELEMPAR GALAT. '
        'Kalau jalur 1 NYANGKUT, tidak ada yang memindahkan → mahasiswa menunggu `AI_TIMEOUT_DETIK` '
        '(420 dtk) lalu dapat "Layanan AI tidak tersedia" padahal jalur 2 sehat.\n\n'
        '**Perbaikan:** `BATAS_SABAR_JALUR1` (`config.py`, dari `EDUAI_AI_SABAR=180`) → jalur 1 '
        'dibatasi lewat `min(timeout, BATAS_SABAR_JALUR1)`; sisa waktu jalur 2 = `timeout` dikurangi '
        'waktu terpakai, minimal `_MIN_SISA_JALUR2=30` dtk. Angka 180 dipilih dari DATA NYATA '
        '(proses sukses produksi 74-562 dtk). Rumus §4.13/kuota TIDAK disentuh.\n\n'
        '**Uji:** `_uji_c6_sabar.py` 20/0 BERGIGI (tiruan jalur 1 tidur → wajib pindah). '
        'Tayang `eduai-app:20260925_010845-sot`.\n')
    MP.write_text(s)
    print('MASTER_PLAN: C6 ditambah')
