# ══════════════════════════════════════════════════════════════
# 🔎 [24 Sep 2026] JEMBATAN `konteks.py` DIBUAT + UJI MUTU POTONGAN (SUDAH DIKERJAKAN)

Melanjutkan temuan di atas ("REVISI SEDIKIT ≈ REVISI BANYAK"). Semua ACC Bos.

## 1) BUG NYATA ke-18 — `awal_isi_naskah()` GAGAL di naskah ber-daftar-isi BERTITIK

**Ditemukan dari naskah WEB (UIR manajemen, 123.062 kar) — BUKAN dari naskah contoh.**
Naskah ini punya DAFTAR ISI di baris-baris paling atas, contoh:
```
BAB I :PENDAHULUAN
1.1 Latar Belakang Masalah ................ 1
```

**AKAR (terukur):** di `app/state.py::awal_isi_naskah()`, pemeriksaan baris
KEDUA hanya berjalan `if not sisa`:
```python
kandidat = sisa if sisa else nxtv     # sisa = ':PENDAHULUAN' → sudah "cukup"
# → baris berikutnya TIDAK PERNAH diperiksa
```
Karena judul menempel di baris yang sama (`BAB I :PENDAHULUAN`), **penanda
daftar isi di baris berikutnya LOLOS**.

**AKIBAT NYATA (bukan teori):** `awal_isi_naskah()` = **7.590** (seharusnya
**14.019**) → daftar isi ikut ke peta → `petakan()` menghasilkan **4 bagian
raksasa** (1.1=51.156 · 5.2=2.764 · 5.3=51.659 · 6.2=3.416).

**PERBAIKAN:** periksa baris berikutnya **SELALU**; tolak bila mengandung
titik-pengarah (`.....`) ATAU ≤5 kata ATAU berakhir angka (nomor halaman).

**HASIL TERUKUR:**
| | sebelum | sesudah |
|---|---:|---:|
| `awal_isi_naskah()` UIR | 7.590 ❌ | **21.613** ✅ |
| jumlah bagian | 4 | **26** |
| bagian terbesar | 42% | **34,7%** |

⚠️ **Pelajaran:** naskah contoh (5 dokumen lama) **TIDAK** menangkap bug ini.
**Naskah dari web menangkapnya.** → LADANG UJI wajib ditambah naskah web.

## 2) 🚨 KESALAHAN WULAN: `docker cp` ke `/app/state.py` — SALAH TEMPAT

Container `eduai-app` menjalankan **`/app/app/state.py`** (paket `app`), **BUKAN**
`/app/state.py`.

```
BERKAS: /app/app/state.py     ← yang BENAR-BENAR dijalankan  ✅
        /app/state.py         ← tempat Wulan menyalin (nyasar) ❌
```

**GEJALA yang menipu:** perbaikan kode **terbukti benar** saat diuji logika
terpisah, tapi hasil fungsi **tidak berubah** — seolah logikanya salah.

**CARA DETEKSI (WAJIB):**
```bash
docker exec -w /app eduai-app python3 -c "
import sys; sys.path.insert(0,'/app'); import app.state as st
print('BERKAS:', st.__file__)"       # → /app/app/state.py
```
**CARA PASTI SEBELUM MENYALIN:**
```bash
docker exec eduai-app python3 -c "import app.X as m; print(m.__file__)"
```
Berkas nyasar di `/app/*.py` **WAJIB dihapus** supaya tidak menipu lagi.

## 3) BUG NYATA ke-19 — KUNCI `petakan()` vs `konteks.py` (0 IRISAN)

```
state.py::petakan()  keluar:  section_id  section_title  isi_teks  char_count  kategori
konteks.py minta    :  nomor       judul          isi
                       ↑ 3 nama ini TIDAK ADA (nol irisan)
```
Disambung apa adanya → `bangun_prompt()` = **338 kar** (GAGAL SENYAP).
**Dan lapis kedua:** `dari_struktur()` hanya mengenal `bab i/i/1/pendahuluan`
→ target `'1.2'` **TIDAK** dianggap anak BAB I → blok "BAB I (konteks)" KOSONG.

**PERBAIKAN (di `konteks.py` saja — TANPA sentuh `app/ai.py`):** fungsi BARU
`dari_peta(peta, bagian_target)` → terjemahkan nama kunci + cari **BAB INDUK**
dari nomor sub-bab (`'1.2'` → `'1'`) dengan 3 jaring: nomor/romawi · kategori
`babN` · kata kunci judul (pendahuluan/tinjauan/metode/hasil/kesimpulan).
`bangun_prompt()` dapat parameter baru `peta=`.

**HASIL TERUKUR (tesis S2 manajemen):**
```
prompt target '1.2'   : 676 kar  →  4.369 kar
   === KEBENARAN TUNGGAL PENELITIAN ===   155
   === BAB I (konteks) ===              2.028   ← dulu KOSONG
   === BAGIAN SEBELUMNYA (konteks) ===  1.046   ← 1.1 Latar Belakang
   === BAGIAN SESUDAHNYA (konteks) ===    485   ← 1.3 Tujuan
   === ISI BAGIAN YANG DIREVISI ===       410   ← 1.2 target
```

## 4) ✅ UJI MUTU POTONGAN vs PENUH — HASIL (AI NYATA + HAKIM)

Rancangan: 3 naskah (S1/S2/S3) × 2 sisi = 6 tulisan; hakim nilai 1–5 per butir
(sambung makna · konsisten · presisi · natural) + **juri buta** (tak tahu mana
yang penuh/potong). Kriteria Bos verbatim: *"ketersambungan makna, cerita, data
dan konsisten, terhadap kontek global, bab sebelum dan sesudah, sub bab yang
terkait. Intinya adalah presisi, tepat dan Natural berbahasa nya."*

| Naskah | PENUH | POTONG | Hemat | Nilai PENUH | Nilai POTONG |
|---|---:|---:|---:|---:|---:|
| Tesis S2 manajemen | 2 rev | **1 rev** | 2,5× | 5,00 | **5,00** |
| Skripsi S1 UNMUL | 3 rev | **1 rev** | 2,7× | 4,75 | **5,00** |
| Disertasi S3 UNHAS | 3 rev | 2 rev | 1,8× | 3,00 | **3,25** |

**JURI BUTA: POTONG menang 2 · PENUH menang 1 · SERI 0.** Rata-rata 4,42 vs 4,25.

**KESIMPULAN:** potongan **TIDAK kalah** mutunya, malah sedikit lebih baik —
karena AI langsung diberi bab induk + sebelum + sesudah + brief, bukan disuruh
mencari sendiri di 55.000 kar. **Konteks tepat mengalahkan konteks banyak.**

⚠️ **BATAS (jujur):** (a) disertasi S3 nilainya terendah (3,0–3,25) karena
targetnya BAB I utuh **14.013 kar** — jembatan TIDAK memotong target, jadi
target besar tidak banyak ditolong; (b) hakim = model yang SAMA (combo EduAi),
idealnya beda model; (c) baru 3 naskah.

📁 Alat: `_uji_mutu_v2.py` (revisi+simpan), `_hakim_mutu.py` (nilai, tanpa bayar
ulang), `_hakim_mentah.py` (panggil AI mentah), `_sketsa/analisa_harga*.py`.

## 5) 🚨 JEBAKAN TERUKUR — 9router bisa balas `text/event-stream` + `data: [DONE]`

**Gejala:** `json.decoder.JSONDecodeError: Extra data: line 1 column N`
saat memakai `r.json()`.

**AKAR (terukur, Content-Type diperiksa):**
```
HTTP 200 · Content-Type: text/event-stream · 402 byte
{"choices":[…]}data: [DONE]\n\n
                     ↑ penanda stream DITEMPEL di belakang objek JSON
```

**PERBAIKAN:** JANGAN `r.json()`. Ambil `r.text` mentah → buang
`data: [DONE]` → buang awalan `data:` per baris → baru `json.loads`.
(`app/ai.py` produksi SELAMAT — dia memakai `r.text` + `_urai_jawaban()`,
bukan `r.json()`.)

## 6) 📏 PELAJARAN: `python3 -c` dengan kutip bersarang = ALAT UJI RUSAK

Wulan 2× gagal di titik sama karena menulis JSON ber-kutip di dalam
`python3 -c "…"`. **ATURAN:** skrip uji → tulis ke **BERKAS `.py`** → `docker cp`
→ `docker exec python3 berkas.py`. Jangan pernah `-c` untuk perintah ber-JSON.

## 7) 📁 DOKUMEN UJI BARU (dari web — repository kampus)

Unduh DOCX repository kampus: **DOCX utuh LANGKA** (7 repository diperiksa;
`eprints.unm.ac.id` kena 403 Cloudflare). **PDF per-bab = NORMA.**
`digilib.uin-suka.ac.id` menerima unduhan via `curl` + UA Chrome.

Berkas baru: `_uji_web/` + `/app/_uji_webtxt/` — antara lain
`uir_manajemen.txt` (123.062 kar, **25 baris bergaya `1.1.`** — SATU-SATUNYA
naskah web yang memakai gaya titik kedua, dan yang menyingkap bug ke-18),
`ub_bab3.txt`, `uin_bab1/bab2.txt`, `unj_bab3.txt`.

## 8) 💰 ANALISA HARGA §4.13 — 10.000 TIDAK TERLALU MURAH (jawaban resmi)

**PERTANYAAN BOS:** *"apakah nilai 10.000 token itu terlalu murah? Perlu di
turunkan biar saya gak rugi."* Lalu: *"saya beli dengan diskon. Coba kalo harga
dari provider asli."*

**HARGA RESMI DEEPSEEK** (api-docs.deepseek.com/quick_start/pricing, 24Sep26)
— per **1 JUTA** token, `deepseek-flash` (= yang dipakai):
| | off-peak | peak |
|---|---:|---:|
| input cache-miss | $0,15 | $0,30 |
| input cache-hit | $0,003 | $0,006 |
| output | $0,60 | $1,20 |

`deepseek-v4-pro`: input $0,66–1,32 · output $1,98–3,96.
**Peak = 2× off-peak**, jam peak **08.00–11.00 & 13.00–17.00 WIB**
(= jam kerja mahasiswa → banyak kena PEAK). Off-peak semua jam lain + weekend.

**HASIL (kurs Rp 16.300/USD, AddOn +30 Token = Rp 50.000 → Rp 1.667/Token):**
| Kasus | Biaya nyata | Jual | Margin |
|---|---:|---:|---:|
| flash peak, cara LAMA (4 rev) | Rp 294 | Rp 6.667 | **95,6%** |
| flash peak, POTONG | Rp 57–112 | Rp 1.667–3.333 | **96,3–96,7%** |
| flash peak, skripsi FULL 36 rev | Rp 2.425 | Rp 60.000 | **96,0%** |
| **v4-pro peak, skripsi FULL** | **Rp 9.894** | Rp 60.000 | **83,5%** ⚠️ |

**KESIMPULAN: pembagi 10.000 TIDAK terlalu murah — margin 95–97%.** Yang perlu
dijaga BUKAN pembaginya, tapi (a) pagar biaya untuk naskah raksasa + model kelas
atas, (b) menyelesaikan jembatan konteks (biaya turun 2–3× → margin NAIK).

⚠️ **KOREKSI PENTING:** tarif **Rp 0,0155915/token** di `MASTER_PLAN §4.13`
(= **Rp 15.600/1jt**) adalah **harga farming/diskon**, **22× lebih MAHAL** dari
harga resmi DeepSeek flash peak (Rp ~4.890/1jt). Analisa margin yang memakai
angka itu **terlalu konservatif** — masih aman, tapi bukan gambaran sebenarnya.
⇒ Kalau menghitung margin, **pakai tarif provider ASLI**, bukan tarif farming.

---
