# 🔄 DOKUMENTASI & MEMORI DISINKRONKAN DENGAN KODE (06 Okt 2026)

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> **Berkas ini merekam APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) di dalamnya **wajar berbeda** dari
> keadaan **kini** — itu BUKAN kesalahan, itu memang rekaman.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Perintah Bos: *"Update Dokumentasi, skill, script, catatan dan memori berdasar kode app EduAi"*

---

## 🎯 APA YANG DICEK (bukan tebak — langsung ke kode)

| Yang diperiksa | Cara | Hasil |
|---|---|---|
| Kode host vs container | `md5sum` per berkas `app/*.py` | ✅ **IDENTIK semua** (tidak ada kode basi) |
| Image live | `docker ps` | `eduai-app:20261006_182106-sot` |
| Deploy terakhir | diff 2 image | 17:25 → 18:21 mengubah `referensi.html` + `rute_jurnal.py` |
| Tabel DB | `docker exec … sqlite3` | **25 tabel** · 8 user · 54 berkas |
| Gerbang 06Okt | `ls _gerbang*.py` | **13 gerbang** (12 lama + `_gerbang_anti_bikin_baru.py` BARU) |
| Dokumen 06Okt | `ls *06OKT2026.md` | **41 berkas** (+ `FLAG`, `FITUR_PLAN`, 5 `LAPORAN_TAHAP1_*`) |

---

## 🚨 TEMUAN: 4 DOKUMEN BASI (sudah diperbaiki)

| # | Dokumen | Basi-nya | Perbaikan |
|---|---|---|---|
| 1 | `FLAG_LANJUT_DISINI.md` | Blok teratas masih bilang fitur jurnal **"BELUM DIKODING"** dan posisi di image 08:30 — padahal **2 deploy sudah lewat** | Blok baru di ATAS: image `20261006_182106-sot` · jurnal L1–6 LIVE · 13 gerbang · ikon · terbuka |
| 2 | `FITUR_PLAN_JURNAL_WORKSPACE_06OKT2026.md` | Header: *"BELUM DIKODING"* + *"DILARANG dikoding"* | Header → **SEBAGIAN SUDAH DIKODING & LIVE** + rujuk laporan per langkah |
| 3 | `MULAI_URUTAN_KERJA_JURNAL_06OKT2026.md` | Status: *"MENUNGGU izin + jawaban bentuk teknis"* padahal sudah selesai | Status → L1–6 SELESAI/LIVE · sisa Langkah 7 |
| 4 | `references/rencana-jurnal-workspace-06okt2026.md` (SKILL) | Sama: *"BELUM DIKODING · DILARANG"* | Header → status kode per 06Okt malam |

**AKAR kenapa basi (pola yang Bos marah-marahi):** sesi panjang, blok lama
**tetap di atas**, sesi berikutnya percaya yang lama. ⇒ Ini persis akar
*"2 minggu gak kelar"* yang sudah tercatat di FLAG. **Aturan FLAG: blok lama
TIDAK dihapus, tapi yang basi WAJIB ditandai.**

---

## ✅ YANG SUDAH DIDOKUMENTASIKAN DI BERBAGAI TEMPAT

### Laporan (sudah ada, dipakai sebagai rujukan)
| Berkas | Isi |
|---|---|
| `LAPORAN_DEPLOY_06OKT2026.md` | deploy 17:25 + temuan `jalankan.sh` lupa salin `_ikon-asli` |
| `LAPORAN_TAHAP1_1..5_*06OKT2026.md` | kolom · modul · jembatan · jatah · rute API |
| `LAPORAN_JUJUR_POTRET_TANDA_06OKT2026.md` | pengakuan pelanggaran + status tanda ⚠️ |
| `LAPORAN_SEMUA_IKON_LUCIDE_06OKT2026.md` | 0 emoji · sprite 56→64 |
| `LAPORAN_KEASLIAN_IKON_06OKT2026.md` | audit 64/64 cocok Lucide + gerbang anti-halusinasi |
| `LAPORAN_IKON_KATA_PLACEHOLDER_06OKT2026.md` | kata "jatah/gratis" → "tanpa Token" |

### Catatan / putusan / IDE (41 berkas `*_06OKT2026.md`)
Semua **sudah ada & lengkap** — Wulan TIDAK menulis ulang. Yang ditambahkan
hanya **penunjuk status** supaya sesi baru tidak salah baca.

---

## 📁 BERKAS YANG DIUBAH DI SESI INI

| Berkas | Perubahan |
|---|---|
| `FLAG_LANJUT_DISINI.md` | +blok status 06Okt malam di paling atas (88 baris) |
| `FITUR_PLAN_JURNAL_WORKSPACE_06OKT2026.md` | header status basi → benar |
| `MULAI_URUTAN_KERJA_JURNAL_06OKT2026.md` | status → L1–6 selesai |
| `DOKUMENTASI_SINKRON_KODE_06OKT2026.md` | **berkas ini** |
| skill `eduai-publishing` | SKILL.md + 1 reference baru |
| `memory` + `fact_store` | fakta 06Okt malam |

**Backup sebelum ubah:** `_arsip/pre-dokumentasi-20261006-184956/` (+ `MD5.txt`)

---

## 🔍 TEMUAN TAMBAHAN SAAT VERIFIKASI (jujur, belum diperbaiki)

### 1. Celah kecil gerbang ikon: `▸` (U+25B8) tidak diperiksa
`_gerbang_ikon_semua.py` memakai regex rentang emoji yang **TIDAK memuat**
`U+25B8` (`▸`), dan `▸` juga **tidak ada di daftar `DIIZINKAN`**. Akibatnya
pemeriksaan **melewatkannya** — padahal `▸` **tampil ke user** sebagai panah
folder di `naskah.html` (2×) dan `editor.html`.
- **Bukan emoji** (tidak berwarna) → tidak melanggar perintah Bos "jangan pakai
  standar/emoji", tapi **belum konsisten** dengan 64 ikon Lucide.
- **Wulan TIDAK mengubah gerbang/tampilan** — memperluas regex bisa memicu
  GAGAL PALSU pada `→`/`★` yang sudah disetujui Bos, dan mengubah panah folder
  = perubahan tampilan yang **belum diminta**. ⇒ **Dilaporkan, menunggu keputusan.**
- Karakter `═` (192×) **AMAN** — semuanya di dalam **komentar Jinja** `{# … #}`
  (tidak terkirim ke browser).

### 2. Aturan jalankan gerbang — SUDAH DIKOREKSI (lihat catatan #6 di atas)
Ini kesalahan Wulan sendiri di sesi ini, ketemu **karena verifikasi dijalankan**
(bukan karena percaya catatan). ⇒ **Verifikasi wajib, bukan formalitas.**

---

## ⚠️ CATATAN JUJUR

1. **TIDAK ada satu baris kode aplikasi diubah** di sesi ini — murni dokumentasi
   + memori. Tidak perlu deploy.
2. **Tanda ⚠️ "isi terbatas" MASIH belum dilihat mata** (halaman `/referensi`
   balas 303 di browser uji). Kode & data terbukti benar lewat gerbang + HTTP.
3. **`pdf_url` per artikel belum ada** → tombol unduh PDF belum berfungsi penuh.
4. **Keputusan menunggu Bos:** unduh Lucide lengkap (2.102 ikon) — Wulan sarankan A.
5. **Gerbang `_gerbang_anti_bikin_baru.py` (18:16) — SUDAH DIUJI di sesi ini:**
   bersih → **7 LULUS / 0 GAGAL (EXIT 0)** · dirusak (skrip potret palsu di root)
   → **6/1 (EXIT 1)** ⇒ **BERGIGI TERBUKTI**.
   ⚠️ **PELAJARAN BARU:** menjalankan gerbang dengan `python3 _gerbang_x.py | tail`
   **MENUTUPI EXIT CODE** → terlihat `EXIT=0` padahal GAGAL. Gerbang WAJIB
   dijalankan **tanpa pipe** lalu periksa `$?` (atau `> file; echo $?`).

6. 🚨 **KOREKSI PENTING (Wulan salah tulis, lalu ditemukan sendiri saat
   verifikasi):** gerbang `_gerbang_*.py` **WAJIB dijalankan DI DALAM container**
   `eduai-app` — **BUKAN dari host**. Wulan awalnya menulis aturan KEBALIK.
   Bukti terukur: `httpx` **ADA di container** (0.28.1, dibutuhkan `TestClient`)
   tapi **TIDAK ADA di host**; gerbang juga membaca `/app/data/eduai.db`.
   Dari host → `ModuleNotFoundError: httpx` / `FileNotFoundError` (EXIT 1, tanpa
   menguji apa pun). Dari container → `ikon_semua` 76/0 · `jurnal3` 53/0 ·
   `jatah` 42/0 · `rute_jurnal` 62/0 · `pagar_artikel` 32/0 (EXIT 0).
   ⇒ **Cara benar:**
   ```bash
   docker cp _gerbang_x.py eduai-app:/app/ && docker exec -w /app eduai-app python3 _gerbang_x.py
   docker exec eduai-app rm -f /app/_gerbang_*.py      # bersihkan sesudah
   ```
