# AUDIT WULAN — EduAi & Rencana BAB IV (Backend Statistik Lab)

Tanggal: 21 Oktober 2026
Auditor: Wulan (agen kolaborator, branch `agen/wulan/bab4-statistik-backend`)
Sumber: clone publik `PaculDigital/eduai-publishing` @ c57f5cd (21 Okt 2026),
cek live eduai.bikinaja.id + statistik.bikinaja.id pada hari yang sama.
Status dokumen: AUDIT AWAL — belum ada kode fitur yang diubah.

---

## 1. IDENTITAS REPO (terverifikasi)

- Nama/deskripsi GitHub: "EduAi — platform revisi naskah akademik
  (FastAPI + Jev + OnlyOffice)", repo PUBLIK, dibuat 21 Okt 2026,
  branch default `main`, 3 commit, 2.075 berkas, ±73 MB (di luar .git).
- Produksi LIVE: https://eduai.bikinaja.id → HTTP 200,
  `/health` → `{"ok":true,"layanan":"eduai-publishing"}`.
- Stack: FastAPI 0.115.6 + Uvicorn + Jinja2 + SQLAlchemy,
  Python 3.13-slim (Docker), pypdfium2, PyMuPDF, WeasyPrint, python-docx.
- `app/` = 88 modul Python. Rute utama di `app/main.py` (±3.800 baris,
  puluhan rute: naskah, artikel/konversi, kuota/topup, AddOn, OnlyOffice,
  sesi, pengaturan).
- Layanan pendukung (README): eduai-app 8100→8000, oo-converter 18081,
  satpam-jev 8130 (jembatan Jev/TypeSafe), 9router 20128 (satu pintu AI).

## 2. PAGAR KOLABORASI (sudah dibaca & dipatuhi Wulan)

Dari `AGEN_LUAR_ATURAN.md` + `scripts/gerbang_git.sh`:

- DILARANG push ke `main` (produksi). Alur resmi: fork → clone fork →
  branch `agen/<nama>/<tujuan>` → Pull Request.
- Berkas terlarang diubah agen: `.gitignore`, `Dockerfile`, `jalankan.sh`,
  `SOT_*.md`, `ATURAN_BATAS_PROYEK_03OKT2026.md`, `scripts/periksa_kode.sh`.
- Rahasia tidak ada di repo (.env, .jwt_oo_secret, data/*.db dikecualikan
  .gitignore) — audit Wulan: TIDAK ditemukan berkas rahasia ter-commit.
- PR wajib: jalankan `scripts/periksa_kode.sh` + tempel keluarannya,
  isi apa-diubah / apa-diuji / apa-BELUM / risiko.
- Merge ≠ deploy. Deploy hanya keputusan pemilik (`bash jalankan.sh`).

Hasil `gerbang_git.sh --periksa` pada clone Wulan saat ini:
GAGAL 2 poin — (1) origin masih menunjuk repo pemilik (bukan fork),
(2) awalnya di branch main. Poin 2 sudah diperbaiki (branch kerja di atas).
Poin 1 TIDAK bisa diperbaiki Wulan sendiri: Wulan tidak punya akun GitHub
sendiri untuk fork. Untuk push/PR perlu salah satu dari Bos:
(a) PAT Bos dipakai sesaat via env (pola statistik-lab 19 Okt — WAJIB
    direvokasi sesudahnya), atau
(b) Bos membuatkan fork/akun kolaborator, atau
(c) Wulan kerja lokal saja, Bos yang push branch-nya.
Sampai itu diputuskan: TIDAK ADA push apa pun dari Wulan.

## 3. BATAS PROYEK vs JEMBATAN STATISTIK LAB

- `ATURAN_BATAS_PROYEK_03OKT2026.md`: satu proyek = satu dunia.
  Dilarang pinjam kredensial/.env proyek lain (termasuk statistik-lab).
- TAPI `CATATAN_DISKUSI_BAB4_KONVERSI_08OKT2026.md` §4.2 & §4.4 mencatat
  PUTUSAN BOS 08 Okt 2026 yang TERKUNCI: Statistik Lab BOLEH jadi backend
  khusus EduAi lewat JEMBATAN RESMI (API eksplisit, pola oo-converter),
  dengan 3 kunci:
  1. Rumah data = EduAi. Mesin Statistik Lab hanya hitung, TIDAK menyimpan.
  2. Yang parsing = EduAi (Jev/AI) — data dikirim sudah rapi siap hitung,
     mesin tidak menebak X/M/Y/Z.
  3. Prasyarat 4 hal diatur di EduAi: jenis, desain, model, sampel.
- Jadi rencana BAB IV ini TIDAK melanggar batas proyek, asal jembatannya
  API resmi dan tidak pinjam kredensial.

## 4. YANG SUDAH ADA UNTUK BAB IV (jangan dibangun ulang)

| Bagian | Status di kode |
|---|---|
| Kerangka BAB IV (4.1–4.5) | ADA — `app/kerangka_bab.py`: deskripsi objek, deskripsi data, uji prasyarat, uji hipotesis, pembahasan; butuh 2 tabel + 2 grafik |
| Harga token BAB IV | ADA — `app/config.py`: BAB IV terberat (26,5rb-equiv); DUA layanan terpisah per putusan Bos: `analisa` 30 token, `olah_data` 30 token (`4:olah_data`) |
| Logika harga per layanan | ADA — `app/kerangka.py` susun_rencana(): BAB IV menampilkan 2 layanan (Analisa & pembahasan / Olah data statistik) |
| Cek kelengkapan + peta Jev | ADA — dipakai konversi jurnal (tolak hangat bila bab hasil/simpulan belum ada) |
| Kuesioner / data lapangan / jembatan API ke Statistik Lab | BELUM ADA — tidak ada satu pun panggilan HTTP ke statistik.bikinaja.id / API statistik-lab di `app/*.py` (grep "statistik" hanya menemukan teks, konfigurasi harga, dan catatan) |
| Rute/modul BAB IV khusus | BELUM ADA — BAB IV masih lewat jalur kerangka/revisi umum |

## 5. KEADAAN MESIN STATISTIK LAB (sisi backend, dari catatan Wulan)

- Live: https://statistik.bikinaja.id → 200. API kualitatif menjawab
  terstruktur (POST /api/kualitatif/saran tanpa isi → 400 "Prompt kosong").
- Mesin kuantitatif terbukti benar (audit 16 Okt): regresi, klinik asumsi,
  BUAT DATA; mediasi & moderasi tunggal SUDAH diperbaiki Wulan 19 Okt
  di branch `fix/wulan-audit-2026-10-19` repo statistik-lab
  (BELUM merge & BELUM deploy — status terakhir yang Wulan tahu).
- 9 varian jalur lain (mediasi paralel/berjenjang, moderasi dual, dll)
  waktu itu masih "sedang disiapkan". Kontrak API untuk EduAi HARUS
  hanya memakai kemampuan yang benar-benar live & teruji, bukan varian
  yang masih disiapkan.
- Kualitatif di statistik.bikinaja.id SUDAH live (modul /kualitatif,
  20 Okt) — catatan lama di EduAi ("kualitatif belum bisa") sudah tidak
  sepenuhnya berlaku; perlu diputuskan apakah BAB IV kualitatif ikut
  dijembatani atau tetap ditolak halus dulu.

## 6. ISTILAH YANG PERLU DIPUTUSKAN BOS (penting)

Di kode EduAi (`app/kerangka_bab.py`) penamaannya baku:
BAB III = METODE PENELITIAN, BAB IV = HASIL DAN PEMBAHASAN.
Permintaan Bos 21 Okt menyebut "BAB 4 Metodologi".
Dua kemungkinan maksud:
(a) BAB IV Hasil & Pembahasan — yang memang melibatkan Statistik Lab
    sebagai backend (sesuai catatan 08 Okt), atau
(b) Modul/metode di balik BAB IV (metodologi pengolahan datanya).
Wulan TIDAK menebak — menunggu putusan Bos sebelum koding.

## 7. RANCANGAN JEMBATAN (usulan, belum dikoding)

Kontrak API eksplisit EduAi → Statistik Lab (pola oo-converter):

```
EduAi (Jev baca BAB I–III → jenis/desain/model/sampel)
  → AI EduAi susun kuesioner (bila data belum ada)
  → user unggah data lapangan KE EDUAI (rumah data = EduAi)
  → kode EduAi rapikan: kolom per-item (mis. Kualitas_Produk_1..5),
    peta peran kolom: X1/X2/Z/Y + jalur model
  → POST ke mesin Statistik Lab: {model, jalur, data rapi, n}
    mesin HITUNG SAJA, tidak menyimpan
  → mesin kembalikan: koefisien, t/F, p, R², uji asumsi, tabel siap pakai
  → AI EduAi tafsirkan → draf BAB IV (4.2–4.5) tersimpan di EduAi
  → Jev periksa hasil
```

Yang masih terbuka (dari catatan 08 Okt §6, belum diputuskan Bos):
endpoint & nama layanan jembatan, timeout/batas ukuran, harga AddOn
olah data (token vs AddOn terpisah), alur data keliru + charge perbaikan,
kualitatif ikut atau tidak, siapa mengisi 4 prasyarat bila Jev tidak
menemukannya di naskah (form user?).

## 8. RISIKO & CATATAN AUDIT UMUM

- `app/main.py` sangat besar (±3.800 baris) — fitur BAB IV sebaiknya
  modul + router BARU (pola rute_jurnal/rute_pembimbing), bukan menumpuk
  di main.py.
- Repo memuat 166 berkas .md (banyak catatan riwayat) — SOT yang berlaku:
  SOT_JEV_BUKU_UMUM, SOT_PETA_NASKAH_SATU_PINTU, SOT_KONVERSI_JURNAL,
  SOT_PUBLISH_BUKU, SOT_LOA_QR. Catatan diskusi BUKAN status.
- Ada berkas `.bak` di app/ (ai.py.bak-langkahab) — hutang kebersihan kecil,
  bukan darurat.
- Gerbang produksi hanya jujur di dalam image Docker (prinsip repo
  sendiri) — audit ini di host, jadi klaimnya sebatas struktur & kode,
  bukan bukti produksi per modul.

## 9. LANGKAH BERIKUTNYA (menunggu Bos)

1. Putuskan istilah: BAB IV Hasil (a) atau maksud lain (b).
2. Putuskan cara Wulan push/PR: PAT sesaat / fork kolaborator / lokal saja.
3. Setelah 1–2 jelas: Wulan susun kontrak API jembatan + sketsa alur
   di branch ini, jalankan gerbang, ajukan PR — tanpa menyentuh main.
