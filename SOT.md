# 📌 SOT — EDUAI PUBLISHING (SINGLE SOURCE OF TRUTH)

> **INI PINTU MASUK TUNGGAL.** Baca file ini dulu (2 menit), lalu **BERHENTI**
> membaca dokumen lain — kecuali yang ditunjuk di sini.
> **Cara kerja:** status TIDAK dihafal di dokumen mana pun. Status **DIHITUNG
> dari kode di image** oleh `sot.py`. Dokumen hanya mencatat **keputusan** &
> **pelajaran**.
> 🚩 **Terakhir diperbarui: 17 Okt 2026** (oleh Wulan, atas perintah Bos).

---

## 🟢 SESI TERAKHIR (17 Okt 2026) — BACA INI, LALU BERHENTI

```
1. SOT_LOA_QR_17OKT2026.md      ← ⭐ LoA OTOMATIS + VERIFIKASI QR (LIVE, teruji)
2. PAGAR_MUTU_PETA_DAN_HEMAT_JEV_14OKT2026.md
3. CATATAN_SAMBUNGAN_CATATAN_PEMBIMBING_14OKT2026.md
```

**Yang SELESAI (17 Okt) — LoA OTOMATIS + QR VERIFIKASI ✅ LIVE:**
- **LoA dicetak EduAi sendiri** (OJS tidak punya berkas LoA). Editor "Terima" di
  Tridarma → user klik **"Unduh LoA"** di EduAi → **PDF 1 halaman** + tanda tangan
  asli + **QR verifikasi**. `app/loa.py` · `templates/loa/loa-jemt.html`
- **Halaman verifikasi publik** https://qr.tridarma.id — **KOP SAMA dengan LoA**
  (logo 64px, brand 30px, "Tridarma Journal Publishing", E-ISSN•Terbit•Web•Email
  1 baris tengah, accent bar 4px). Nomor asli ⇒ VALID; palsu ⇒ TIDAK DITEMUKAN.
- **3 SYARAT TERBIT:** status = Diterima · Volume + Nomor ada · WA `0851-7813-8514`.
  Kosong ⇒ LoA TIDAK terbit (pesan jelas). Status = **TOMBOL MANUAL**, bukan otomatis.
- **Ingress:** aturan **no.9** `qr.tridarma.id → localhost:8100`; wildcard
  `*.tridarma.id` (no.10) **TETAP UTUH**. Middleware `HOST_VERIFIKASI` di
  `app/main.py` ⇒ `/` di domain itu = halaman verifikasi, BUKAN beranda EduAi.
- **UJI: 11 LULUS / 0 GAGAL** (HP 390px, `_sketsa/uji_valid_hp.py`) —
  valid/palsu/lebar/overflow/galat JS. Diverifikasi MATA juga.
- **3 JEBAKAN TERUKUR:** ① `async async function` ⇒ SELURUH JS mati (WAJIB
  `node --check` sebelum deploy) ② `@app.middleware` HARUS tepat setelah
  `app = FastAPI(...)` ③ Chrome :9333 dipaksa `innerWidth=698` ⇒ uji HP WAJIB
  **Playwright** + verifikasi mata.
- **Jembatan OJS BENAR:** `https://tridarma.id/mcp` (bukan `ojs-ojs_web-1`,
  bukan `:9027` yang ternyata SSH).
- **Data uji `1.001` DIBERSIHKAN** (`_arsip/pre-bersih-loa-20261017_035810/`);
  `nomor_artikel` = 0 ⇒ LoA asli pertama = `1.001`.
- **SISA:** Tridarma `issues = 0` (belum ada Volume/Nomor ⇒ LoA artikel nyata
  belum bisa terbit) · ✅ nomor WA admin = `6285178138516` (admin EduAi, putusan
  Bos 17 Okt · teruji kirim nyata) ·
  tombol "Unduh LoA" belum diuji dengan akun + artikel Diterima sungguhan.

## 🟢 SESI SEBELUMNYA (arsip) (14 Okt 2026) — BACA INI, LALU BERHENTI

```
1. PAGAR_MUTU_PETA_DAN_HEMAT_JEV_14OKT2026.md      ← ⭐ pagar mutu peta + Jev tidak berulang
2. CATATAN_SAMBUNGAN_CATATAN_PEMBIMBING_14OKT2026.md ← ⭐ catatan pembimbing → peta Jev
3. RANCANGAN_RAPI_BAB_14OKT2026.md                  ← ⭐ rancangan 1 halaman rapi_bab()
```

**Yang SELESAI (14 Okt):**
- **Optimasi putaran Jev 3→1**: 161 dtk → 54 dtk; bab 70 → 80
- **Jev tidak dipanggil berulang**: PAGAR C2 (`sidik_naskah` SHA-256 ==
  `peta_sidik`) ⇒ panggilan-2 = 0,0 dtk, Rp 0
- **Naskah rusak tidak bayar Jev**: `periksa_mutu()` → `rusak_konversi` ⇒
  surveyor Jev dilewati, jalur fallback Rp 0; gerbang 15/0
- **Catatan pembimbing → peta Jev**: `rapi_bab()` di `pembimbing.py` +
  `asisten.py::simpan_usulan()`; gerbang 32/0
- **Tiket Lolos (Lapis 3)** — sudah bayar + bab makna tetap ⇒ elemen `☑ Done`,
  tidak ditanyakan lagi. Jev 1 pertanyaan choice (GRATIS, 0,5 dtk);
  Jev mati ⇒ tiket BATAL. `app/tiket_lolos.py` · uji 25/0 · 7/0 · 12/0
- **Jembatan bab kurang** — bab kurang ⇒ HANYA tombol "Perbaiki";
  bab lengkap ⇒ baru cek mutu. Uji 15/0 · 6/0
- **Image:** `eduai-app:20261016_021214-sot`

**Yang SELESAI (10–13 Okt):** pagar ① FORMAT + ② ISI + ③ MUTU HIDUP di pintu
`/unggah` (`app/_gerbang_pagar_unggah.py` 5/0, BERGIGI) · DB produksi
 dibersihkan (4 user/17 berkas) · `sot.py --periksa` **0 masalah EXIT 0**.
Gerbang: `app/_gerbang_periksa_mutu.py` **27/0** + `app/_gerbang_http_mutu.py`
**14/0**, keduanya **BERGIGI TERBUKTI** (27/0 → 26/1 EXIT 1 saat pesan mengulang
judul disuntik kembali → 27/0). **POTRET + MATA** memverifikasi tata letak rapi.
Uji naskah ASLI: fid=81 Asih sehat (1 huruf tunggal) vs fid=115 PDF
rusak_konversi (4.992 huruf tunggal) ⇒ pemisah terang ⇒ Jev tidak perlu.
**BUG DIPERBAIKI:** `pesan` mesin dulu memuat judulnya sendiri ⇒ layar memasang
judul LAGI ⇒ teks terbaca dua kali. Judul kini dibuang dari `pesan` (4 tingkat).

**⚠️ 2 JEBAKAN GERBANG yang menggigit 10 Okt (jangan ulang):** gerbang
`TestClient` **mencemari DB produksi** ⇒ WAJIB pakai **DB SALINAN** (pola
`_gerbang_unduh_dobel.py`); rute login uji = **`/daftar`+`/masuk`**, bukan
`/api/daftar` (404 ⇒ `/unggah` balas 303 = GAGAL PALSU). Detail: skill
`uji-dalam-kontainer`.

---

## 🗄️ SESI 09 Okt 2026 malam — kronologis lengkap

```
1. SESI_09OKT2026_KRONOLOGIS.md          ← kronologis 1 berkas (awal → putusan)
2. CATATAN_KEPUTUSAN_PETA3_09OKT2026.md  ← 6 aturan + urutan wajib + cara baca
3. TEMUAN_EKSTRAKSI_PDF_TABEL_09OKT2026.md ← mutu file user = akar sisa masalah
```

**Yang SELESAI:** `peta3_jev.py` md5 **`5a01fcbac64b4d4f8dd07522c04a3231`** · 368 baris
· 6 aturan terpasang & teruji · regresi Asih (bab 5 · subbab 130) **NOL**.
**Yang BERIKUT:** masuk app (`app/peta_halus_jev.py` masih cara lama) · uji
Disertasi 103 · `section_state` + kolom mulai/akhir · sambung Kolaborasi.
**3 PAGAR BARU:** ① uji naskah lewat `app.ai._teks_dari_berkas` ② `grep -c '<w:tab'`=0
sebelum lapor ③ baca `gabung`+`sistematika` dari hasil nyata.

---

## 1️⃣ CARA PAKAI (WAJIB — 2 perintah)

```bash
cd /opt/data/services/eduai-publishing
python3 sot.py              # keadaan NYATA (dihitung dari docker/kode)
python3 sot.py --periksa    # cek dokumen vs kode → EXIT 0 = selaras
```

`--periksa` **BERGIGI** — terbukti bukan gerbang hiasan:

| Uji suntik | Hasil |
|---|---|
| Judul palsu `## 🚦 SESI TERAKHIR … BACA INI DULU` | **EXIT 2** (tertangkap) → dipulihkan EXIT 0 |
| Klaim `Image LIVE` + `21 tabel` + `13 gerbang` palsu | **EXIT 3** → dipulihkan EXIT 0 |
| Klaim `pembimbing_ai.py belum dikode` (padahal ADA) | **EXIT 1** → dipulihkan EXIT 0 |
| **Berkas baru** menyinggung status **tanpa label** | **EXIT 1** → dipulihkan EXIT 0 |
| **Berkas berlabel** lalu **dihapus** | **EXIT 1** → dipulihkan EXIT 0 |

> ⚠️ **Pelajarannya (jujur, 06 Okt 2026):** uji bergigi **pertama** untuk
> gerbang judul **GAGAL PALSU** — Wulan menyuntik teks yang tidak cocok,
> sehingga "EXIT 0" itu **bukan bukti**. Setelah diselidiki, ketemu **bug
> nyata**: judul menyesatkan "diampuni" karena 300 karakter di bawahnya
> memuat kata "riwayat". **Bug dicabut** → gerbang baru benar-benar bergigi.

---

## 2️⃣ KEADAAN SEKARANG — dihitung, bukan diketik

Jalankan `python3 sot.py` untuk angka **terkini**. Terakhir diukur:

| Hal | Nilai |
|---|---|
| Produksi | `https://eduai.bikinaja.id` |
| Container | `eduai-app` |
| Image jalan | `eduai-app:20261016_021214-sot` (16 Okt, jembatan + tiket lolos) |
| Titik mundur | `eduai-app:cadangan-pra-sot` |
| `/health` produksi | 200 |
| Gerbang | **59** (11 di `app/` + 48 di root) · uji **117** |
| Tabel DB | 26 |
| Modul `app/` | 81 berkas `.py` |
| Deploy | `bash jalankan.sh` (build IMAGE) — **IZIN BOS DULU** |

---

## 3️⃣ ATURAN MEMBACA DOKUMEN (biar tidak bingung)

| Tanda | Arti |
|---|---|
| 🚩 **DIPERBARUI / STATUS NYATA** | Keadaan **KINI** — boleh dipercaya |
| 🆕 **\<tgl\> \<jam\> — \<peristiwa\>** | **Catatan PERISTIWA** saat itu. Image/tabel/gerbang di dalamnya **wajar** berbeda dari sekarang — **BUKAN** keadaan kini |
| 🗄️ **RIWAYAT / ARSIP / BASI** | Arsip. Sah sebagai **pelajaran**, ❌ **JANGAN** untuk status |

**Kenapa aturan ini ada:** 06 Okt 2026 Bos bilang *"saya bingung… jangan
berbagai informasi sendiri-sendiri"*. Akarnya ketemu: FLAG punya judul besar
**"SESI TERAKHIR: 16 Sep 2026 — BACA INI DULU"** padahal sesi terakhir 06 Okt.
Siapa pun yang membuka file langsung percaya judul itu. **Sudah diperbaiki.**

---

## 4️⃣ PERAN SETIAP DOKUMEN (siapa menulis apa — tidak boleh tumpang tindih)

| Berkas | Peran | Status |
|---|---|---|
| **`SOT.md`** (file ini) | ⭐ Pintu masuk tunggal | 🚩 BERLAKU |
| **`sot.py`** | ⭐ Mesin SOT — hitung dari kode | 🚩 BERLAKU |
| **`FLAG_LANJUT_DISINI.md`** | Status terkini (blok 🆕 teratas) + riwayat peristiwa | 🚩 BERLAKU |
| **`MASTER_PLAN.md`** | Rencana & keputusan terkunci (§4/§5b) | 🚩 BERLAKU |
| **`CATATAN_PROYEK.md`** | Aturan keras proyek + catatan sesi (riwayat) | 🚩 BERLAKU |
| **51 berkas lain** (LAPORAN_* · PETA_* · RENCANA_* · IDE_* · PUTUSAN_* · DOKUMENTASI_* · CATATAN_DISKUSI_* · ATURAN_*) | **Di luar pengawasan** — tiap berkas **WAJIB ber-penanda** `<!-- … SOT: … -->` di kepalanya | 🗄️/⛔/✅ LABEL |

**Kenapa ada label di 51 berkas itu?** Putusan Bos **Opsi A** (06 Okt 2026):
satpam memeriksa 3 dokumen induk. Berkas lain yang **menyinggung status**
tapi tak terdaftar = **titik buta**. Tiap berkas itu diberi label:

| Label | Arti |
|---|---|
| 🗄️ **LAPORAN/BUKTI** | Rekaman peristiwa — angka wajar beda dari kini |
| 🗄️ **PETA/ARSIP LAMA** | Peta pada tanggalnya — banyak sudah berubah |
| ⏸️ **RENCANA / RANCANGAN** | Menunggu keputusan Bos — belum dijalankan |
| ⛔ **IDE** | **DILARANG dikoding** sampai Bos bilang "mulai" |
| ✅ **PUTUSAN BOS** | Keputusan terkunci — rujukan, bukan status |
| 📝 **CATATAN DISKUSI** | Bahan bicara — sebagian sudah, sebagian belum |
| 📏 **ATURAN** | Pedoman format/sitasi — bukan soal status |

**Satpam menjaga label ini 2 arah:**
- Berkas **baru** menyinggung status **tanpa label** → **protes** ✅ bergigi
- Berkas **berlabel** lalu **hilang** → **protes** ✅ bergigi

**Aturan:** satu hal ditulis di **satu** tempat. Dokumen lain **MENUNJUK** ke
sana — tidak menyalin. Ada info baru? Tulis di tempat yang berhak, yang lain
cukup menunjuk.

---

## 5️⃣ YANG LIVE (dibuktikan ke kode)

```
Fase 1–7 revisi AI        ✅   konsistensi · citation_validator · etika
Dukungan PDF              ✅   27 Sep (pypdfium2 05 Okt), uji 97 naskah
Pembimbing + Pembimbing AI ✅   03 Okt (pembimbing.py · pembimbing_ai.py)
Alat sama (OnlyOffice)    ✅   pembimbing = mode BACA, tombol mati (server)
Jurnal + Workspace L1–7   ✅   06 Okt (rute_jurnal.py 9 rute)
Cegah unduh dobel         ✅   06 Okt 21:30 (penanda berkas_id)
"Link Jurnal.txt"         ✅   06 Okt 21:55 (putusan Bos A1/B2/C/D)
Mode Belajar · Peta Halus ✅   belajar.py · peta_halus.py
Kelompok catatan per BAB  ✅   kelompok_catatan.py
Lonceng + antrean AI      ✅   17 Sep
Maintenance OnlyOffice    ✅   27 Sep (sesi_latar.py tiap 300 dtk)
Kuota + QRIS + transaksi  ✅   (webhook masih sandbox)
```

---

## 6️⃣ YANG BELUM (dicek ke kode 06 Okt — jujur)

| Fitur | Keterangan |
|---|---|
| **Tahap 3.4** penyaring tanda saat unduh | `/unduh/{fid}` (`main.py:920`) kirim berkas **apa adanya** |
| **Tahap 3.3** arsip otomatis >60 hari | kunci naskah ada, arsipnya belum |
| **Langkah 4** Agent Penilai Revisi | `grep penilai` = kosong |
| **Langkah 6** Telegram/WA | menunggu **5 putusan Bos** |
| **Langkah 7** Agentic penuh | belum |
| **Login Google · OTP/nokos** | belum |
| **Mode Belajar FASE A** | modul ada, isi belum |
| **Pemicu notifikasi kuota** | kalimat ada, pemicu belum |
| **Backup R2** | `boto3` tidak dipakai di `app/` |
| **Tahap 5** dua pembimbing | kolom disiapkan, fitur belum |
| **Ingatan Bab PENUH** | baru per sub-bab |
| `AI_MAX_NASKAH_KARAKTER=60000` | **angka mati** (`ai.py:40` cuma import) |
| **Bug 5** revert `app/versi.py` | menunggu putusan Bos |
| Sisa P3 | 404 CB · 27 import unused |

---

## 7️⃣ ATURAN INDUK (JANGAN DILANGGAR)

1. **BACKUP DULU** sebelum ubah berkas (`_arsip/pre-<topik>-<tgl>/` + `MD5.txt`).
   ⚠️ **CEK ISI BACKUP sebelum menimpakan** — Wulan pernah memulihkan dari
   backup **sebelum** perbaikan, 6 perbaikan hilang. (06 Okt 2026)
2. **JANGAN PERCAYA daftar "BELUM" di dokumen lama — CEK KODE DI IMAGE.**
   MASTER_PLAN pernah lebih basi dari FLAG (tertinggal 12 hari).
3. **JANGAN bikin baru** — titipkan di yang **sudah ada**. Tawarkan versi yang
   membuang lebih banyak. Sederhana > lengkap.
4. **Deploy = IZIN BOS DULU.** Jalur resmi `bash jalankan.sh` (build image),
   **bukan** `docker cp`.
5. **Gerbang WAJIB bisa GAGAL** — aturan tertulis tidak cukup.
6. **Merapikan dokumentasi ≠ kode** → tidak perlu deploy.
7. **Agen/deploy:** `docker cp` **WAJIB** disusul `docker restart`.
8. **SATU PROYEK = SATU DUNIA.** Kerja EduAi → hanya folder
   `services/eduai-publishing/` + container `eduai-app`/`oo-converter` +
   domain `eduai.bikinaja.id`. **DILARANG** pakai kredensial proyek lain.

---

## 8️⃣ CARA BALIK CEPAT (sesi berikutnya)

```
1. BACA file ini (SOT.md)                    ← MULAI DI SINI
2. python3 sot.py --periksa                  ← wajib EXIT 0
3. FLAG_LANJUT_DISINI.md — blok 🧭 STATUS NYATA (paling atas)
4. MASTER_PLAN.md §0.0 (aturan akar) + §7 (status)
5. Skill: eduai-publishing (bagian GERBANG UJI WAJIB)
```

**Kalau `--periksa` protes:** jangan langsung sunting dokumen. **Cek dulu —
kode salah, atau dokumennya basi?** Kalau dokumen basi → tandai
`🗄️ RIWAYAT`. Kalau memang kode berubah → perbarui angka.
