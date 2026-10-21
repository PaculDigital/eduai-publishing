# 🧹 RAPI BERKAS UJI — 04 Okt 2026 (Opsi B, putusan Bos)

<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> **Berkas ini merekam APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) di dalamnya **wajar berbeda** dari
> keadaan **kini** — itu BUKAN kesalahan, itu memang rekaman.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


## HASIL

```text
Image LIVE   : eduai-app:20261004_131357-sot
Titik mundur : eduai-app:cadangan-pra-sot
Backup DB    : _arsip/pra-rapi/20261004_131345/eduai.db
               (ab2e7449981afcdc6743940cea29700f · 24 tabel · 5 user · 27 berkas)
Backup berkas: _arsip/pre-rapi-uji-20261004/ (8 berkas + Dockerfile + MD5.txt)
```

## MASALAH YANG DIPERBAIKI

5 berkas UJI + gerbang ikut ke image produksi karena Wulan menaruhnya di `app/`
(alasan Wulan waktu itu keliru: "Dockerfile cuma `COPY app ./app`, jadi taruh
di app/ supaya ikut"). Padahal itu justru **SEBAB** berkas ikut ke image.

## AKAR & CARA BENAR (kebiasaan project yang SUDAH ADA)

```text
✅ Tempat BENAR berkas uji = ROOT proyek
   — ada 87 berkas `_uji_*.py` di root; root TIDAK di-COPY ke image.
✅ scripts/gerbang_uji.sh: docker cp <berkas root> eduai-app:/app/
   → disalin SEMENTARA saat uji, hilang saat container dibangun ulang.
```

## YANG DIKERJAKAN

```text
1. Pindahkan 8 berkas `app/_*.py` → ROOT proyek:
     _gerbang_deteksi_bab.py · _gerbang_visual.py · _lihat_user_belajar.py
     _siapkan_data_uji.py · _siapkan_uji_belajar.py · _uji_alur_belajar.py
     _uji_belajar.py · _uji_insight_belajar.py
2. Tambah `.dockerignore` SEMPIT — hanya:
     **/__pycache__/ · **/*.pyc · **/*.pyo · **/*~ · **/.DS_Store
     app/*.bak · app/*.bak-* · app/**/*.bak · app/**/*.bak-*
     app/*.log
3. ⚠️ SENGAJA TIDAK dikecualikan: `app/data/` & `app/uploads/`
     → tidak ada di source (bind-mount container); menulis polanya berisiko.
4. ⚠️ `app/ai.py.bak-langkahab` (58 KB, 16 Sep) — berkas versi lama, TIDAK
     dihapus (belum ada izin), hanya dikecualikan dari image.
```

## BUKTI

```text
SEBELUM: ls /app/app/ | grep -cE "^_uji|^_siapkan|^_lihat|^_gerbang" → 6
SESUDAH: ls /app/app/ | grep -cE "^_uji|^_siapkan|^_lihat|^_gerbang" → 0 ✅
Berkas produksi di image: 59

VERIFIKASI pola .dockerignore (python fnmatch):
  app/ai.py                 → ikut image ✅
  app/ai.py.bak-langkahab   → DIKECUALIKAN ✅
  app/main.py · app/belajar.py · app/templates/belajar_insight.html
  app/static/logo-320.png · app/config.py → ikut image ✅ (semua)

UJI SESUDAH PINDAH:
  mesin insight (naskah nyata)  → 21 LULUS / 0 GAGAL
  gerbang deteksi bab           → 27 LULUS / 0 GAGAL
  periksa_kode.sh               → LULUS
  gerbang editor OO             → LULUS (oo-converter OK · /oo/aset 200)
  produksi: / =200 · /masuk =200 · /belajar =303 · /kolaborasi =303
  data produksi: 24 tabel · 5 user · 27 berkas — UTUH
  kode baru masih ikut image: belajar_insight.html (kolom-kanan ×2) ·
                              belajar.py (teks_bab ×2) ✅
```

## PELAJARAN (buat skill)

```text
❌ SALAH: "Dockerfile COPY app ./app → taruh berkas di app/ supaya ikut uji."
✅ BENAR: berkas uji di ROOT; `docker cp` saat uji; `.dockerignore` sempit.

⚠️ `.dockerignore` BISA MEMATIKAN PRODUKSI kalau polanya salah. SEBELUM
   menambah pola: grep -rn "<pola>" app/*.py → pastikan tak ada kode
   produksi yang membacanya. Kasus nyata: `app/data/`&`app/uploads/`
   dibaca produksi (`/app/uploads/<uid>/<nama>`) TAPI itu bind-mount,
   bukan dari image — jadi TIDAK perlu (dan berbahaya) dikecualikan.
```

## SISA (belum dikerjakan)

```text
· 3 AddOn dijual tapi mesin belum ada (Mode Belajar 75rb · Konversi Jurnal
  100rb · Publish Jurnal 500rb) — belum diputuskan Bos
· Bank Soal 4 level (LANGKAH 3) · Simulasi Sidang (LANGKAH 4)
· `app/ai.py.bak-langkahab` — hapus atau simpan? (butuh izin Bos)
· 56 volume Docker menganggur (~25 GB) · backup ke R2
```
