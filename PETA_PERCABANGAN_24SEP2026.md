# 🌿 PETA PERCABANGAN PROYEK EDUAI — SOT (per 24 Sep 2026)

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ PETA/ARSIP LAMA — BUKAN penentu status proyek.
> Berkas ini memetakan keadaan pada **tanggal di namanya**. Banyak isinya
> **sudah berubah**. Sah untuk **pelajaran/jejak**, ❌ **JANGAN** dipakai
> sebagai keadaan kini.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


**KENAPA BERKAS INI ADA.** Permintaan Bos (verbatim, 24Sep26):
> *"Banyak progress yang bercabang jadi belum selesai progress di tengah
> jalan ada cabang yang harus diselesaikan. Laporkan ke saya."*
Lalu: *"Update dulu Dokumentasi, skill, script dan catatan. Agar tetap
menjadi SOT, tentang percabangan ini juga di catat."*

Berkas ini **peta tunggal** untuk menjawab: *"apa yang sudah selesai, apa
yang belum, dan cabang mana yang menggantung"*. Setiap baris **wajib
terbukti dari kode/DB produksi** — bukan dari ingatan.

## 🟢 PEMBARUAN 27Sep26 SORE — ANTI-524 PETA/KERJAKAN ✅

- **Akar**: `/v1/peta/kerjakan` masih sinkron (AI >100 dtk → Cloudflare 524).
- **FIX**: titip latar belakang (pola `/v1/revisi`): balas <1 dtk + kode →
  pantau `/v1/proses/{kode}`. Pagar P2 (token kembali) & C1 tetap hidup.
- **Bukti via domain**: 0,16 dtk → SELESAI → hasil 1.690 kar (deepseek-v4.1-flash).
- Detail lengkap: FLAG blok "ANTI-524 27Sep26 SORE".

---

## 🚦 KEADAAN PRODUKSI (terukur 24 Sep 2026)

| Hal | Nilai nyata |
|---|---|
| Image jalan | `eduai-app:20260924_203800-sot` |
| Container | `eduai-app` — Up, sehat |
| Domain | `https://eduai.bikinaja.id/health` → **200** |
| Host port | `127.0.0.1:8100` → container `8000` |
| DB | 21 tabel · `users=6` · `files=39` |
| Titik mundur | `eduai-app:cadangan-pra-sot` |
| Backup DB terakhir | `_arsip/pra-sot/20260924_203800-sot` |

---

## 1️⃣ SELESAI & TAYANG (terbukti)

| # | Pekerjaan | Bukti nyata |
|---|---|---|
| 1 | Portal dokumen + editor OnlyOffice | tayang |
| 2 | Kuota + Token Revisi (§4.13) | `setelan.token_revisi_per = 10000` |
| 3 | Panel admin `/pengaturan` | `app/templates/pengaturan.html` ada di image |
| 4 | Lonceng notifikasi (selesai + gagal) | `app/proses.py` · uji 5/0 |
| 5 | Antrean + batas konkurensi AI | live, terbukti |
| 6 | Fallback OpenRouter (jalur kedua) | live |
| 7 | Lapis 1 — jenis dokumen | live |
| 8 | Hemat Token **4 → 1** (konteks tetangga) | tesis Bos 29.053 → 7.940 tok |
| 9 | Ingatan Bab (baca + tulis) | `section_state` terisi benar |
| 10 | Tahap 2.3 Log Revisi compact (3 lapis) | tayang |
| 11 | Tahap 2.5 + 2.5b komentar + lampiran | tayang |
| 12 | Tahap 3.1 Sorotan kalimat | `app/sorotan.py` ADA di image |
| 13 | Tahap 3.2 **Revisi Dilewati** ← 24Sep26 | 4 kolom ADA di DB produksi |
| 14 | Etika (Fase 7) | `app/etika.py` dipakai 9× di `app/ai.py` |

---

## 2️⃣ 🔴 CABANG MENGGANTUNG — INI INTI PERMINTAAN BOS

Progress terbelah: **mesin selesai, layar belum**. Akar: Wulan bekerja
**dari dalam ke luar** (sudah ditegur Bos: *"yang ini sudah tapi dipakai
yang lain belum nyambung"*).

| # | Cabang | Keadaan | Yang KURANG (langkah penutup) |
|---|---|---|---|
| ~~C1~~ | ~~Tahap 3.1 Sorotan kalimat~~ | ✅ **DITUTUP 27Sep26** — potret HP 390px via CDP + MATA: badge `keadaan-utuh ✅` + tombol "Lihat di naskah" tampil; tata letak rapi. Temuan sampingan: `lebar_dok 539px > 390px` (teks placeholder panjang melebar) → dicatat sebagai perbaikan layout HP terpisah. Bukti: `_potret/c1-c2-tinjau/04-06.png` |
| ~~C2~~ | ~~Tahap 3.2 Revisi Dilewati~~ | ✅ **DITUTUP 27Sep26** — klik NYATA via CDP: toast "Revisi ini ditandai dilewati..." + lencana "Revisi Dilewati" muncul di kartu (MATA ✅); DB `dilewati=1` (id 11); "Buka lagi" = hak pembimbing via `/tinjau/{token}/aktifkan-lagi` — API `aktifkan_lagi` ✅ "sudah diminta lagi ke mahasiswa". **BONUS: bug akar ditemukan & diperbaiki** — `kbLewati` dulu kirim `daftar[0].id` (bimbingan salah saat mahasiswa punya >1 pembimbing) → kini kirim `_kbLogId` (bimbingan yang sedang dilihat). Bukti: `_potret/c2-lewati/02b-lewati-nyata.png` |
| ~~C3~~ | ~~Log Revisi — tata letak~~ | ✅ **DITUTUP 24Sep26 (opsi A)** — lihat bagian C3 di bawah |
| ~~C4~~ | ~~Bug `/api/ai/v1/bab`~~ | ✅ **DITUTUP 24Sep26** — lihat bagian C4 di bawah |
| ~~C5~~ | ~~Label `§4.10` salah~~ | ✅ **DITUTUP 24Sep26** — 3 label diperbaiki (2 berkas); CATATAN SEMULA SALAH (ai.py:1332 tak memuat label); lihat bagian C5 |
| **C6** | ✅ **Fallback AI kini dipicu GALAT *dan* LAMBAT** | SELESAI 25Sep26 | `AI_TIMEOUT_DETIK=420` di `app/config.py:114` |
| ~~C7~~ | ~~`_uji_publik_komentar` 1 gagal~~ | 🚨 **KOREKSI 25Sep26 — BUKAN soal timeout!** Yang dilaporkan dulu ("batas 300 dtk vs nyata 583 dtk") **SALAH**. Penyebab nyata = **C9 masih hidup**: uji ini menembak endpoint revisi SUNGGUHAN pada **file 47**, AI balas hasil KOSONG, versi 0-kar tersimpan jadi `terpakai=1`. Uji menemukan **bug produksi**, bukan kekurangan dirinya. Juga: `buka()` default **300 dtk**, tapi pemantauan pakai `E2E_TUNGGU` default **420** — jadi 583 dtk TIDAK pernah jadi akar. Larangan jalan sampai pagar C9 di `versi.py` terpasang — lihat bagian **C7** di bawah |
| ~~C8~~ | ~~Gerbang uji: 20 LULUS / 5 GAGAL~~ | ✅ **DITUTUP 25Sep26** — `_uji_fase5_jalur` kini **15 LULUS / 0 GAGAL**. Akar terkoreksi: **bukan** `profil_dokumen=0`, melainkan uji memakai **berkas USER** (`/app/uploads/3/9c5d...docx` = PROPOSAL, hanya 1 bagian BAB). Kini memakai **`_contoh-dokumen/`** (6 dokumen uji) + `state.petakan()` langsung. Lihat bagian C8 di bawah |

### ✅ C5 — DITUTUP 24Sep26

**DICATAT SEMULA BEGINI:** "label §4.10 salah (ai.py:1332) → harusnya §4.13".

**🚨 CATATAN ITU TERBUKTI SALAH — dan Wulan hampir merusak kode yang BENAR.**
Karena aturan Bos "baca kode sebelum bilang bug", Wulan membaca `ai.py:1332`:
baris itu isinya `if file_id is not None and not naskah:` — **tidak ada label
§4.10 di situ sama sekali.** Labelnya di tempat lain.

**FAKTA (dibaca dari `MASTER_PLAN.md`, bukan tebakan):**
| Bagian | Judul |
|---|---|
| **§4.10** | SISTEM KUOTA & CREDIT AI (ACC 13Sep26) — komponen #6 = `GET /api/ai/kuota` |
| **§4.13** | SISTEM TOKEN REVISI (ACC 15Sep26 — KUNCI HARGA & MESIN UANG) |

Jadi `ai.py:825` ("Sisa kuota AI user (MASTER_PLAN §4.10 komponen #6)")
**SUDAH BENAR** — kalau Wulan ikuti catatan lama, Wulan justru MERUSAK rujukan
yang sah. Aturan lama benar: baca kode dulu.

**YANG BENAR-BENAR SALAH (2 buah, ketemu dari pemeriksaan menyeluruh):**
1. `app/ai.py:1399` — `# ── KUOTA (MASTER_PLAN §4.10) — potong SEBANYAK BAGIAN`
   Membahas **pemotongan Token Revisi** → seharusnya **§4.13**. DIPERBAIKI.
2. `app/main.py:1432` — `(MASTER_PLAN §4.10 / langkah #2)`
   Label "langkah #2" **tidak ada di MASTER_PLAN** → diganti keterangan nyata.
3. (temuan tambahan) `app/ai.py:1` docstring `(13Sep26, langkah #2)` — label
   "langkah #2" juga tidak ada di MASTER_PLAN. DIPERBAIKI.

**PERBAIKAN:** 3 tempat di 2 berkas (`ai.py`, `main.py`). **Rumus §4.13 TIDAK
disentuh** — hanya label rujukannya.

**UJI BARU `_uji_c5_label.py` (7 asersi, masuk gerbang §2):**
| Asersi | Isi |
|---|---|
| A | Tidak ada rujukan §4.10 yang isinya soal Token Revisi |
| B | Label "langkah #2" tidak ada lagi (ai.py & main.py) |
| C | Kode memakai `TOKEN_REVISI` (berarti §4.13) |
| D | **Bergigi**: pemeriksa MENOLAK yang salah, MENERIMA yang benar |

**BUKTI 2 ARAH (bukan klaim):**
```
SEHAT (image produksi)        → 7 LULUS / 0 GAGAL   ✅
Dirusak (§4.10 dikembalikan)  → 6 LULUS / 1 GAGAL   ✅ tepat sasaran
Dipulihkan                    → 7 LULUS / 0 GAGAL   ✅
```
Deploy: `eduai-app:20260925_001159-sot` · `/health` 200 · `§4.13` ada 5×.

**PELAJARAN (masuk skill):** catatan cabang bisa **salah tulis baris**. Wajib
BACA baris yang disebut SEBELUM memperbaiki — kalau tidak, kita merusak kode
yang sudah benar dan menambah kerusakan baru.

### ✅ C3 — DITUTUP 24Sep26 (opsi A, ACC Bos)

**MASALAH (temuan Bos):** "*Memang munculnya revisi Pembimbing diatas header
dashboard mahasiswa? Apakah sudah layak seperti itu? Tidak bisakah lebih rapi?*"
Kotak Log Revisi **terkurung di dalam panel "Bagikan ke Pembimbing"** — panel itu
isinya FORM membagi tautan. Akibatnya mahasiswa harus menekan "Bagikan" hanya
untuk **MELIHAT** catatan. Dua maksud berbeda dijejalkan di satu tempat.

**PILIHAN:** Wulan buat 3 sketsa (`_sketsa/c3_sketsa_tataletak.html`,
potret `_potret/c3/sketsa-3-usul.png`) → **Bos pilih A**.

**PERBAIKAN (opsi A):**
1. Kotak `#kb-log` **DIPINDAH** dari dalam panel → jadi **kartu mandiri
   "Catatan Pembimbing"** di dashboard (setelah kartu kuota, sebelum pengunggah).
2. `kbMuatLog()` **dipanggil saat halaman dibuka** (`DOMContentLoaded`),
   tidak lagi menunggu panel "Bagikan" dibuka.
3. **Kalau tidak ada catatan → kartu HILANG TOTAL** (aturan Bos: ringkas,
   jangan tumpuk blok kosong).
4. Tambahan: lencana jumlah di kepala kartu + tombol lipat + tautan
   "Undang / kelola pembimbing →" (memisahkan "lihat catatan" dari "bagikan").

**🚨 CACAT NYATA YANG IKUT DITUTUP (ketemu saat membaca kode):**
`kbMuatLog()` dulu memakai `d0.daftar[0].id` = **bimbingan PERTAMA**.
Kalau bimbingan pertama belum punya catatan, kartu **SELALU tersembunyi**
walaupun bimbingan lain punya banyak catatan → mahasiswa tidak pernah tahu.
**TERUKUR 24Sep26:** bimbingan id 5 (`X`) tanpa catatan menutupi bimbingan 65
(`Prof. Uji Bab`, 9 catatan). Kini: periksa SEMUA bimbingan, pakai yang
catatannya paling banyak.

**BUKTI MATA (bukan klaim):**
| Hal | Hasil |
|---|---|
| Kartu "Catatan Pembimbing" di dashboard | ✅ ADA — 8 catatan, **7 menunggu** |
| Ikon aksi tiap baris | ✅ bintang kuning · pensil hijau · X merah |
| Tumpang tindih | ✅ TIDAK ADA — vision bilang "sangat rapi" |
| Tautan "Undang / kelola pembimbing →" | ✅ ADA di kaki kartu |
| **BERGIGI** (panggilan `kbMuatLog()` dimatikan) | ✅ kartu **HILANG TOTAL** |
| Deploy | `eduai-app:20260925_000326-sot` · `/health` 200 |
| Potret | `_potret/c3/21-kartu-setelah-deploy.png` |

**CATATAN JUJUR:** di sketsa A kartu digambar **tepat di bawah "Naskah Saya"**;
di hasil nyata ia duduk **setelah tombol kuota** (masih di dalam kartu "Naskah
Saya", sebelum zona unggah). Hasilnya tetap sesuai maksud (selalu terlihat),
tapi **tidak persis sama** dengan gambar sketsa — supaya Bos tahu.

### ✅ C4 — DITUTUP 24Sep26 (ACC Bos "tahap 1, c4 bug /bab")

**MASALAH:** `app/ai.py` endpoint `/api/ai/v1/bab` memakai `deteksi_bab(teks)`
yang **hanya** mengenal judul "BAB I / BAB II". Padahal UI mahasiswa memilih
**SUB-BAB** (`1.1`, `1.2`, `3.4`) dan mesin revisi (`versi.ambil_bab`) sudah
lama bisa sub-bab → anak dropdown **tidak cocok** dengan yang bisa dikerjakan
mesin → **hemat Token 4→1 tidak terasa di layar**.

**PERBAIKAN (1 baris keputusan, TIDAK membangun mesin baru):**
```python
dari_bagian = _deteksi_bagian(teks)
daftar = dari_bagian if dari_bagian else deteksi_bab(teks)   # pagar ke jalur lama
```
`_deteksi_bagian()` **sudah ada** di `app/versi.py` (dipakai BUG-20), memakai
`state.petakan()`. Bentuk hasil **identik** ({label, judul, posisi, akhir, isi}).
`panjang` kini dihitung dari `len(isi)` — karena `deteksi_bab` pakai kunci
`panjang`, sedangkan `_deteksi_bagian` pakai kunci `isi`.

**BUKTI (terukur, bukan klaim):**
| Hal | Nilai |
|---|---|
| `deteksi_bab()` label | `['BAB I', 'BAB II']` ← cara lama |
| `_deteksi_bagian()` label | `['1.1','1.2','1.3','2.1']` ← cara baru |
| Panjang `1.2` | **86 kar** vs `BAB I` = 350 kar (naskah uji) |
| `bagian` untuk `1.2` | **1** → cukup **1 Token Revisi** |
| Uji fungsi `_uji_c4_bab.py` | **12 LULUS / 0 GAGAL** |
| Uji HTTP `_uji_c4_bab_http.py` | **6 LULUS / 0 GAGAL** |
| **BERGIGI** (kode dikembalikan ke `deteksi_bab`) | **10 LULUS / 2 GAGAL** — tepat sasaran |
| Deploy | `eduai-app:20260924_210336-sot` · `/health` 200 |
| Kedua uji | **masuk gerbang uji** (§2) |

**PELAJARAN UJI (dicatat supaya tidak berulang):** versi PERTAMA uji Wulan
**TIDAK BERGIGI** — ia hanya `grep` teks `ai.py`, sehingga dirusak pun tetap
LULUS. Perbaikannya: (a) **replika baris keputusan** endpoint lalu periksa
label yang KELUAR; (b) buang komentar dulu (`re.sub(r'#[^\n]*','')`) sebelum
memeriksa kode, karena kata yang dicari ada di komentar → lulus palsu.

**SISA YANG BELUM (jujur):** tampilan dropdown di **layar mahasiswa**
belum diperiksa MATA (aturan penutup cabang). Mesin + jalur data sudah
terbukti; bukti mata menyusul bersama C1/C2.

### 🔎 C8 — RINCIAN 5 GAGAL GERBANG (diperiksa 24Sep26, satu per satu)

**Ditemukan saat menutup pekerjaan SOT 24Sep26.** Gerbang `bash scripts/gerbang_uji.sh`
→ **20 grup LULUS / 5 GAGAL**. Setiap satu sudah dibedah akarnya:

| Uji | Akar NYATA (terukur) | Jenis |
|---|---|---|
| `_uji_kelompok_bab.py` | Sendirian **37 LULUS / 0 GAGAL**. Di gerbang gagal karena **data uji di DB berubah** (user uji + `VersiDokumen` sumber `uji` dibersihkan 24Sep26) | ⚠️ data uji |
| `_uji_presisi_dropdown_http.py` | `TypeError: argument should be str/PathLike, not 'NoneType'` — butuh `file_id` yang sudah tidak ada | ⚠️ data uji |
| `_uji_fase5_jalur.py` | 13 OK / **1 GAGAL**: *"peta nyata >0 bagian"* — tabel `profil_dokumen` **0 baris** | ⚠️ data uji |
| `_uji_ingatan.py` | 9 LULUS / **2 GAGAL**: *"I3b model TERCATAT di riwayat"* + *"I3c token >0 — in=0"* | ⚠️ **butuh proses AI nyata** |
| `_uji_publik_komentar.py` | timeout **300 dtk** vs proses nyata **583 dtk** (model `cbcn/deepseek-v4.1-flash` 5× lebih lambat) | ⚠️ cacat UJI |

**KESIMPULAN JUJUR:** kelimanya **bukan bug aplikasi**. Aplikasi produksi
sehat (`/health` 200, kode identik source). Yang rusak = **kesiapan data
uji** + **2 cacat skrip uji** (batas waktu terlalu pendek).

**CARA MENUTUP C8 (usul, tunggu ACC Bos):**
1. Pulihkan data uji: jalankan `_sketsa/siapkan_uji_25.py` + isi `profil_dokumen`
   untuk berkas uji (jangan sentuh data user nyata — hanya berkas uji).
2. `_uji_publik_komentar.py`: naikkan batas tunggu **300 → 700 dtk**
   (proses nyata 583 dtk) — atau jalankan sebagai uji BERAT (di luar gerbang harian).
3. `_uji_ingatan.py`: tandai asersi I3b/I3c sebagai **butuh AI** → pindahkan
   ke bagian uji berat (sama seperti N/O/P/Q yang sudah dipisah).

**ATURAN YANG DIPELAJARI:** gerbang uji bergantung pada **data uji** —
membersihkan data uji di DB **membuat gerbang gagal PALSU**. ⇒ Kalau
membersihkan data, siapkan ulang **di waktu yang sama**.


---

## 3️⃣ ⬜ BELUM DIBANGUN (tahap lanjutan)

| # | Tahap | Catatan |
|---|---|---|
| T3.3 | **Kunci Naskah + arsip >60 hari** | belum ada kode (grep: nol) |
| T3.4 | **Penyaring tanda di SELURUH naskah saat unduh** | `app/tulis_docx.py:105-118` baru sebagian |
| T4 | **Akun pembimbing + AI + dompet token global** | diskusi selesai, belum koding |
| T5 | **2 pembimbing** | disengaja nanti |
| — | ~~**PDF didukung**~~ | ✅ 27Sep26 — `_teks_dari_berkas` + pypdf 6.19.0 (catatan lama BASI) |
| — | ~~**Fase 6 Sitasi**~~ | ✅ ADA `app/citation_validator.py` (348 baris, dipakai `ai.py:80`) — catatan lama BASI, diperiksa 27Sep malam |
| — | **"Ingatan Bab PENUH"** | baru per sub-bab |
| — | **Agentic + Telegram/WA** | rencana tersimpan `RENCANA_AGENTIC_TELEGRAM_WA.md` |

---

## 4️⃣ ATURAN PENUTUP CABANG (supaya tidak berulang)

1. **SATU cabang ditutup dulu sebelum buka tahap baru.** Cabang yang
   "hampir selesai" lebih murah ditutup daripada membuka tahap baru.
2. **Tiap cabang wajib punya langkah penutup yang BISA DIBUKTIKAN** —
   bukan "sudah dikoding" tapi "sudah dilihat mata / sudah diklik".
3. **Jangan lapor "selesai" untuk cabang yang belum diuji di layar.**
   Cukup bilang: *kode selesai, belum terbukti di layar*.
4. Kalau menutup cabang ternyata membuka cabang baru → **sebut di sini**,
   jangan diamkan.

---

## 5️⃣ CARA VERIFIKASI BERKAS INI (jangan percaya, buktikan)

```bash
cd /opt/data/services/eduai-publishing

# keadaan produksi
docker ps --filter name=eduai-app --format '{{.Image}} | {{.Status}}'
curl -s -o /dev/null -w '%{http_code}\n' https://eduai.bikinaja.id/health

# C4 — bukti bug /bab MASIH ADA
docker exec eduai-app sed -n '966p' /app/app/ai.py   # → deteksi_bab(teks)

# C13 — bukti kolom baru ADA di DB produksi
docker exec eduai-app python3 -c "import sqlite3;c=sqlite3.connect('/app/data/eduai.db');\
print([d[1] for d in c.execute('pragma table_info(catatan_pembimbing)')])"

# T3.3 / T3.4 — bukti BELUM ada
grep -rln 'kunci_naskah' app/ ; ls app/sitasi.py 2>&1
```

---

**Terakhir diperbarui:** 05 Okt 2026 · oleh Wulan
**Catatan 05Okt26:** Satpam Jev (app/satpam.py) ditambahkan — penjaga keputusan di depan mesin deteksi bab, lewat 9router (satu pintu). Kategori BAB besar diperbaiki di akar (state.kategori_bab_besar): 'bab' → 'bab1'..'bab5'.
**Berkas terkait:** `FLAG_LANJUT_DISINI.md` (blok teratas) ·
`MASTER_PLAN.md` · `RENCANA_KOLABORASI_PEMBIMBING_23SEP2026.md`

### ✅ C9 — DITUTUP 25Sep26 (BUG NYATA, bukan cacat uji)

**DITEMUKAN SAAT MENGERJAKAN C8.** Wulan membaca `proses_ai` & `versi_dokumen`
di DB produksi, bukan menebak.

**FAKTA (file 47, DB produksi):**
```
versi_dokumen v57 | model=cbcn/glm-5.3-flash | 4.522 kar | terpakai=0
versi_dokumen v58 | model=''                |     0 kar | terpakai=0
versi_dokumen v59 | model=''                |     0 kar | terpakai=1  ← NASKAH JADI KOSONG
```
Prosesnya berstatus **'selesai'** + notifikasi **"berhasil"** → **SUKSES PALSU**.
Bukti waktu: proses id 90/91 selesai dalam **1,2 detik** dengan token **0**
(padahal id 86–89 butuh 74–562 detik & 34.000+ token).

**RANTAI BUG (terbaca dari kode, tiap titik dibuktikan):**
| # | Tempat | Masalah |
|---|---|---|
| 1 | `ai.py` `_valid()` | Gerbang LOLOS kalau AI cuma MENYALIN naskah (ada `[PROFIL]`, blok `[Kn]` panjang) |
| 2 | `ai.py` `bersihkan_jawaban_ai()` | Buang salinan → hasil 0 kar (memang disengaja) |
| 3 | `ai.py` `_revisi_kerja()` | Gabung hasil → `konten` KOSONG tanpa diperiksa |
| 4 | `ai.py` `simpan_versi(isi='')` | Versi KOSONG disimpan → langsung `terpakai=1` |
| 5 | `ai.py` | `token_revisi = token_revisi_nyata or len(info_potong)` → lapor 4 padahal token nyata 0 |
| 6 | `proses.py` `tandai_selesai()` | `status='selesai'` + notifikasi "berhasil" |

**BUKTI LANGSUNG** (dijalankan di container, bukan dugaan):
```
jawaban AI: "[PROFIL] x\n[K1]\n" + naskah (SALINAN PERSIS)
_valid() lama → None     ← LOLOS
bersihkan    → 0 kar     ← KOSONG
```

**PERBAIKAN (ACC Bos "1") — 3 PAGAR:**
1. `_valid()` menolak jawaban yang setelah dibersihkan < 40 kar (`_MIN_HASIL_REVISI`,
   ambang SAMA dengan `_banyak_blok_kosong()` — konsisten, bukan angka karangan).
   Naskah pembanding dititipkan lewat `_NASKAH_BANDING` oleh `_revisi_dengan_failover()`
   → percobaan ke-2 dijalankan. **FAIL-SAFE**: tanpa pembanding → JANGAN menolak.
2. `_revisi_kerja()`: hasil bagian kosong → `log.error` + **kembalikan kuota** +
   **raise HTTPException 503** (bukan menyimpan versi kosong).
3. `token_revisi` **tanpa** `or len(info_potong)` — di DUA tempat (kembalian
   `_revisi_kerja` + `catat_revisi`). Dulu hanya 1 yang dilihat.

**UJI `_uji_c9_kosong.py` — 16 asersi, BERGIGI 3 arah:**
```
SEHAT                → 16 LULUS / 0 GAGAL
cabut pagar 1        → 3 GAGAL (1a, 4a tepat sasaran)
cabut pagar 2 & 3    → 4 GAGAL (2a,2b,2c,2e,3a,3c)
pulih                → 16 LULUS / 0 GAGAL
```
**PELAJARAN UJI (tercatat):** asersi `'teks' in KODE` **TIDAK BERGIGI** —
waktu `if not (konten...):` diubah jadi `if False:`, teks pemeriksanya masih
ada → uji tetap lulus. **Wajib** `re.search` pola + cek URUTAN posisi, dan
**cari SEMUA** kemunculan pola (`or len(info_potong)` ada 2, dulu diperiksa 1).

**TAYANG:** image `eduai-app:20260925_004725-sot` · `/health` 200 ·
uji C9 **16/0 di image produksi**.

⚠️ **SISA (butuh ACC Bos — sentuh data produksi):** versi `terpakai=1` di file 47
masih menunjuk **v59 (0 kar)**. Pemulihan (kembalikan ke v57) **BELUM dikerjakan**
karena itu menyentuh DB produksi.

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

### ✅ C8 — DITUTUP 25Sep26 (akar terkoreksi: uji pakai BERKAS USER)

**AKAR SEBENARNYA (terukur, bukan warisan catatan):** `_uji_fase5_jalur.py`
memakai **berkas MILIK USER** `/app/uploads/3/9c5d6f0e79c4cbf6.docx` sebagai
bahan uji. Berkas itu isinya **PROPOSAL** (halaman judul + BAB I panjang +
BAB II–V hanya 1 paragraf sistematika) → `versi._deteksi_bagian()` = **1 bagian**
→ asersi "peta >0 bagian" gagal.

```
versi._deteksi_bagian()    → 5 bagian (BAB I–V) ✅  ← pada DISERTASI
state.deteksi_bab_besar()  → 5 bagian            ✅
_brief_dan_peta(db, 9, …)  → 1 bagian            ← sebab: section_state
                                                      file 9 HANYA berisi 1 baris ('1.2')
```

**Catatan lama `profil_dokumen=0` TERBUKTI BUKAN akarnya** — dibuktikan dengan
menjalankan `petakan()` pada `_contoh-dokumen/` yang menghasilkan **5 bagian**.
Sebab `_brief_dan_peta()` = apa adanya kalau `section_state` SUDAH ada (itu
memang desainnya: peta dari ingatan revisi).

**PERBAIKAN:** uji memakai **`_contoh-dokumen/`** (6 dokumen uji yang MEMANG
disiapkan) + `state.petakan()` langsung, TIDAK `_brief_dan_peta()`.

**HASIL:** `_uji_fase5_jalur.py` **15 LULUS / 0 GAGAL**.

**PELAJARAN:** **JANGAN pakai berkas milik user sebagai bahan uji.** Berkas user
bisa berubah kapan saja (dan bentuknya beda dengan yang diasumsikan uji).
Pakai `_contoh-dokumen/` yang dikelola khusus untuk uji.

### 🚨 C7 — DIBUKA ULANG 25Sep26: "TIMEOUT" ADALAH SALAH TUDUH

**Yang dilaporkan dulu:** "cacat uji, batas 300 dtk vs proses nyata 583 dtk".
**Terbukti SALAH.** Uji dijalankan apa adanya → hasil `31 LULUS / 6 GAGAL`,
dan yang gagal **BUKAN timeout**:

```
proses_ai id 92 & 93 : status 'selesai' · galat KOSONG · hasil 0 kar · 1 DETIK
versi_dokumen file 47: v60 & v61 = 0 kar · v61 terpakai=1
                       v57 (4.522 kar) & v58 → DIHAPUS oleh "gear"
```

⇒ **BUG C9 MASIH HIDUP.** Uji ini **menemukan bug produksi**, bukan kekurangan
dirinya. Setiap kali dijalankan, uji ini **merusak data nyata** (naskah hilang).

**DUA LUBANG YANG DILEWATKAN PAGAR C9 RONDE-1:**

| # | Tempat | Cacat |
|---|---|---|
| A | `versi.py:369-370` | `for v in lama: v.terpakai = False` dijalankan **SEBELUM** ada isi baru |
| B | `versi.py:401-402` | `if not tersimpan: return []` — versi lama **sudah terlanjur dimatikan**, tidak ada yang mengembalikan |
| C | `versi.py:426-429` | "gear" **MENGHAPUS** versi lama (`db.delete`) → naskah berisi **LENYAP permanen** |
| D | `ai.py:1918-1926` | Kalau `_pisah_blok_komentar()` kosong → `simpan_versi(isi=konten)` **tanpa cek kosong** |

**AKAR METODE (ini yang paling penting):** pagar C9 ronde-1 dipasang di **layer
yang salah** — di loop penggabungan `hasil_bagian.append()` di `ai.py`, padahal
`konten` **sudah kosong sebelum sampai situ**. Yang benar: pagar di **pintu
masuk `versi.simpan_versi*()`** — tempat yang MENULIS ke DB.

**ATURAN BARU (wajib, dari pelajaran ini):**
> Pagar "jangan simpan hasil kosong" dipasang di **FUNGSI TULIS**, bukan di
> pemanggil. Kalau dipasang di pemanggil, jalur LAIN bisa melewatinya.

**PEMULIHAN DATA (pola aman, TERBUKTI):** `_sketsa/pulihkan_file47.py` —
pindahkan penanda `terpakai`, **JANGAN hapus**. Versi kosong dibiarkan sebagai
bukti. Backup DB dulu: `backup_sampah/eduai.db.pre-pulih47`.
⚠️ Kalau versi berisi sudah dihapus "gear", pemulihan harus dari **backup DB**
(`_arsip/pra-sot/<stamp>/`), bukan dari `versi_dokumen`.

### ✅ C10 — DITUTUP 25Sep26 (BUG NYATA: naskah mahasiswa jadi KOSONG)

**BAGAIMANA KETEMU:** saat mengerjakan C7, uji `_uji_publik_komentar.py`
MENEMBAK endpoint nyata (`POST /api/ai/v1/revisi`) — bukan tiruan. Hasilnya
file 47 tersimpan v60 & v61 = **0 karakter**, v61 `terpakai=1` → NASKAH KOSONG,
padahal status `selesai` dan galat kosong. Lebih buruk: v57 (4.522 kar) sudah
**DIHAPUS** oleh "gear" sehingga tidak ada lagi yang bisa dipulihkan.

**MENGAPA C9 TIDAK CUKUP:** pagar C9 dipasang di loop penggabungan
(`hasil_bagian.append`). `konten` sudah KOSONG **sebelum** sampai situ, jadi
pagar itu tidak pernah dilewati. Uji C9 (16/0) HIJAU karena ujinya MENIRUKAN
jalur dengan kode sendiri — bukan menembak pintu aslinya.

**AKAR (3 pintu, terbaca dari kode):**
1. `versi.py simpan_versi_per_komentar()` — `for v in lama: v.terpakai = False`
   dijalankan **SEBELUM** tahu ada isi baru; kalau semua blok kosong →
   `return []` tanpa mengembalikan `terpakai` → versi lama MATI, tak ada pengganti.
2. `versi.py simpan_versi()` — `isi=''` ikut tersimpan + `terpakai=True`.
3. "Gear" memakai `db.delete(v)` → versi berisi HILANG PERMANEN.

**PERBAIKAN (ACC Bos "1+2+3"):**
* **Pagar 1** — `simpan_versi_per_komentar()`: periksa `layak` (ada isi bukan
  spasi) **DI DEPAN**; kalau tidak ada → `return []` tanpa menyentuh versi lama.
* **Pagar 1b** — `simpan_versi()`: tolak `isi` kosong → `return None`.
  Pemanggil `ai.py:1936` diperiksa (`if v is not None`).
* **Pagar 2** — `ai.py _revisi_kerja()`: `konten` kosong → log.error +
  HTTPException 503 (Token Revisi dikembalikan), TIDAK menyentuh versi_dokumen.
* **Pagar 3** — Gear **mengarsipkan** (`diarsipkan=True`), bukan `db.delete()`.
  Kolom `diarsipkan` ditambahkan lewat migrasi aditif yang SUDAH ADA di
  `models.py _migrasi_kolom()` (DEFAULT 0 → versi lama tetap "aktif").
  `daftar_versi(..., dengan_arsip=False)` menyaring arsip secara bawaan;
  `hapus_versi_file()` memakai `dengan_arsip=True` supaya arsip tidak jadi yatim.

**YANG TIDAK DIUBAH:** rumus §4.13, kuota, alur proses, kuota pengembalian.

**UJI `_uji_c10_versi_kosong.py` — 23 asersi, BERGIGI 5 arah:**
```
SEHAT                         → 23 LULUS / 0 GAGAL
RUSAK 1 (pagar "layak")       → 21/2  (2b, 2c GAGAL) ✅
RUSAK 2 (pagar isi kosong)    → 16/7  (1a-1d, 2c, 5e, 5e2 GAGAL) ✅
RUSAK 3 (gear menghapus)      → 21/2  (5b, 5b2 GAGAL) ✅
RUSAK 4 (daftar_versi arsip)  → 21/2  (4a, 4b GAGAL) ✅
RUSAK 5 (pagar ai.py)         → 22/1  (5f GAGAL) ✅
pulih                         → 23/0
```

**🚨 PELAJARAN UJI PALING PENTING (2× gagal di sesi ini):**
Asersi yang mencari **TEKS** tidak bisa melihat pagar yang **DIMATIKAN** —
mencabut pagar dengan `if False:` menyisakan teksnya tetap terbaca. Dua bentuk:
* asersi lama 5f mencari `if not (konten or '').strip():` + `raise HTTPException(503)`
  → pola itu JUGA cocok dengan pagar C9 LAMA → tidak bergigi.
* setelah diperbaiki jadi mencari penanda `C10`, tetap tidak bergigi — `if False:`
  di depan tidak mengubah teks.
⇒ **Yang benar: POTONG potongan pagarnya, JALANKAN, dan pastikan ia benar-benar
melempar.** Diimplementasikan di `_periksa_pagar_c10.py` (di jalankan di dalam
container; dedent JANGAN dilakukan — blok pagar sudah ber-indentasi 4).

**🚨 PELAJARAN DATA/UJI:**
* Uji yang menembak **endpoint nyata** MERUSAK data produksi. Wajib BACKUP DB
  sebelum menjalankan. Wulan lalai → v57 (4.522 kar) terhapus, dipulihkan dari
  `_arsip/pra-sot/20260925_010845-sot/eduai.db`.
* `_periksa_pagar_c10.py` dijalankan di DALAM container — `docker` TIDAK ada di
  dalam image, jadi jangan panggil `subprocess.run(['docker', ...])` dari sana.

**PEMULIHAN DATA:** `_sketsa/pulihkan_file47_dari_backup.py` → v57 (4.522 kar)
kembali & jadi `terpakai=1`. Versi kosong v59/v60/v61 DIBIARKAN sebagai jejak.

**TAYANG:** image `eduai-app:20260925_021902-sot` · `/health` 200 ·
uji C10 23/0 · C9 16/0 · C6 20/0 di image produksi.
