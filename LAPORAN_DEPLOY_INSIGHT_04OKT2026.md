# 🚀 DEPLOY MESIN MINI INSIGHT — 04 Okt 2026

## HASIL

```text
Image LIVE   : eduai-app:20261004_130812-sot
Titik mundur : eduai-app:cadangan-pra-sot
Backup DB    : _arsip/pra-deploy-insight/20261004_130747/eduai.db
               (ab2e7449981afcdc6743940cea29700f · 24 tabel · 5 user · 27 berkas)
URL          : https://eduai.bikinaja.id   (host 127.0.0.1:8100)
```

## UJI PRODUKSI (bypass cache CF: `Cache-Control: no-cache` + `?cb=acak`)

| Rute | Balasan | Arti |
|---|---|---|
| `/` | 200 | sehat |
| `/masuk` | 200 | halaman masuk hidup |
| `/belajar` | 303 | BENAR (belum login → dialihkan) |
| `/doc/` | 404 | BENAR (tanpa berkas) |

```text
Data produksi UTUH: 24 tabel · 5 user · 27 berkas
belajar_naskah: 0 baris (BENAR — belum ada user yang mengaktifkan Mode Belajar)
kode baru ikut image: belajar_insight.html punya "kolom-kanan" (2×) ✅
                      belajar.py punya "teks_bab" (2×) ✅
Gerbang editor OO : LULUS (oo-converter OK · /oo/aset 200 · kunci COCOK)
Gerbang jaringan  : bridge eduai-net ✅
```

## ⚠️ CATATAN JUJUR — berkas UJI ikut ke image

```text
5 berkas ada di image /app/app/:
  _uji_insight_belajar.py · _siapkan_data_uji.py · _siapkan_uji_belajar.py
  _lihat_user_belajar.py · _uji_alur_belajar.py
(+ _gerbang_visual.py, _gerbang_deteksi_bab.py — gerbang, disengaja)

SEBAB: berkas ada di SOURCE `app/` dan `Dockerfile` = `COPY app ./app`.
       BUKAN sisa `docker cp` (sudah dicek: berkas di source memang ada).
RISIKO: RENDAH — sudah diperiksa: TIDAK ADA satu pun yang punya rute
        (@app / @router) → tidak bisa diakses dari web.
KEBIASAAN LAMA: gerbang `_gerbang_deteksi_bab.py` juga begitu sejak 03Okt26.
```

**Usul (menunggu putusan Bos):** pindahkan berkas UJI ke `app/_uji/` dan
kecualikan di Dockerfile (`.dockerignore` atau `COPY` selektif). **Belum
dikerjakan** — jangan ubah Dockerfile tanpa izin.

## YANG HIDUP BARU

```text
Mode Belajar → pita tab ke-3 "🎓 Belajar"
  ├─ halaman /belajar         : panel skor + 3 kartu tahap (LANGKAH 1)
  └─ halaman /belajar/insight : MESIN MINI INSIGHT per bab (LANGKAH 2)
       · klik "Buat Pemahaman BAB I" → AI baca bab dari naskah → 3 butir
         tema + penjelasan + KUTIPAN ASLI dari naskah
       · tersimpan permanen (belajar_naskah.insight_json) → buka lagi 0 token
       · Opsi C: 2 kolom desktop · pita mendatar di HP
```

## PERBAIKAN LAIN DI DEPLOY INI

```text
1. KALIMAT dihaluskan (permintaan Bos): "tidak hangus, tidak perlu bayar ulang"
   → "tersimpan permanen untuk naskah ini — bisa kamu buka kapan saja."
   (2 tempat: belajar.html + belajar_insight.html)
2. KOTAK PUTIH di header (temuan Bos) → akar: kelas `kanan` dipakai 2 tempat
   (.atas .kanan = header · .kanan{background:#fff} = kartu konten)
   FIX: kartu konten → .kolom-kanan
3. GERBANG VISUAL BARU: app/_gerbang_visual.py + scripts/gerbang_visual.sh
   (ukur yang dilihat mata via CDP, bukan tebak CSS — TERBUKTI BERGIGI)
```

## JEBAKAN BARU (catat)

```text
· versi.ambil_bab() balas SELURUH NASKAH kalau label tak ketemu → AI halusinasi
· ambang "isi >85% naskah" SALAH untuk naskah PROPOSAL (1 bab = 87% naskah)
· _aktif_untuk() kuncinya 'status', bukan 'aktif'
· _siapkan_data_uji.py WAJIB: salin DB → user → naskah+berkas → section_state → belajar_naskah
· pkill tidak ada → baca /proc/*/cmdline + os.kill
· `bash skrip | tail` → $? itu exit tail, BUKAN skrip
· CDP mati → laporan gerbang visual "bersih" itu PALSU
```
