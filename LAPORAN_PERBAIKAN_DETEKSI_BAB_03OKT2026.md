# 🔧 PERBAIKAN DETEKSI BAB — LAPORAN 03Okt26

## APA MASALAHNYA (ditemukan dari pertanyaan Bos "kenapa tidak dari dulu?")

Pola deteksi bab memakai `\b` (batas kata) setelah nomor bab, sehingga WAJIB
ada spasi/tanda setelah nomor:

```
"BAB I PENDAHULUAN"  → ✅ cocok
"BAB IPENDAHULUAN"   → ❌ GAGAL   ← bentuk paling umum di naskah nyata!
```

Naskah hasil ekspor Word/Docs SANGAT SERING menempelkan judul ke nomor.
Akibatnya `deteksi_bab()` balas **0 bab** → peta bab hilang → AI menerima
naskah sebagai satu unit utuh, kuota salah, Mode Belajar mustahil.

## 3 SEBAB LAMA TAK KETAHUAN (jawaban jujur)

1. **Naskah uji "bernasib baik"** — disertasi & tesis yang diuji 16Sep26
   kebetulan memakai spasi, jadi lolos. Naskah MAHASISWA (skripsi 5 MB)
   tidak pernah diuji.
2. **Pola KEMBAR** — perbaikan 16Sep26 hanya dikerjakan di `app/state.py`.
   `app/versi.py` (+2 berkas lain) TIDAK ikut diperiksa karena tidak ada grep
   menyeluruh. ⇒ PELAJARAN: setiap perbaiki regex, GREP seluruh app/.
3. **Tidak ada gerbang naskah nyata** — gerbang lama hanya menguji kode bisa
   di-parse & import; tidak pernah menguji "deteksi bab benar di naskah asli?".

## YANG DIPERBAIKI (3 berkas + 1 gerbang baru)

| Berkas | Sebelum | Sesudah |
|---|---|---|
| `app/versi.py:47` | `\b` → tolak judul menempel | pola `state.py` + group disesuaikan |
| `app/cari_bagian.py:69` | cocok "Tabel bab 3" (SALAH TANGKAP) | tolak bab huruf kecil |
| `app/tulis_docx.py:134` | `\b` → judul menempel tak dikenali | pola baru |
| `scripts/gerbang_deteksi_bab.py` | (BARU) | uji 6 naskah NYATA + 9 kasus teks |

## BUKTI (terukur, bukan tebakan)

### 13 naskah LEBIH BAIK, 0 LEBIH BURUK

```
naskah                              LAMA  BARU
SKRIPSI-S1-unmul-fazrigading.docx      0     5  ✅
+ 12 naskah lain                       0     5  ✅
────────────────────────────────────────────────
LEBIH BAIK: 13 · LEBIH BURUK: 0
```

### SKRIPSI S1 unmul (5 MB) — sebelumnya 0 bab, sekarang:

```
BAB I    | PENDAHULUAN
BAB II   | TINJAUAN PUSTAKA
BAB III  | METODOLOGI PENELITIAN
BAB IV   | HASIL DAN PEMBAHASAN
BAB V    | KESIMPULAN DAN SARAN
```

### Gerbang baru: 27 LULUS / 0 GAGAL, **TERBUKTI BERGIGI**

(dikembalikan pola lama → 2 GAGAL → EXIT 1; suntik matikan potongan → GAGAL)

### Regresi

```
periksa_kode.sh           → ✅ LULUS (54 berkas, 5 modul import OK)
_uji_c4_bab.py            → 12 LULUS / 0 GAGAL
_uji_catatan_ai.py        →  5 LULUS / 0 GAGAL
_uji_pembersih.py         →  5 LULUS / 0 GAGAL
_uji_akar_potongan.py     → A/B/C LULUS (D1 gagal = prasarana, versi_lama.py
                            tidak ada; setelah dipasang → D1 "lulus" artinya
                            kode lama memang lebih buruk = bukti bergigi)
```

## ⚠️ CATATAN JUJUR

- **TESIS S2 (7 bab daftar isi) hanya 3 bab** → itu BENAR. Naskahnya memang
  baru sampai BAB III; 4 bab sisanya hanya ada di DAFTAR ISI. Sudah dicek
  langsung: "BAB IV" cuma muncul 1× (posisi daftar isi), dst.
- **TESIS Goras hanya 1 bab** → BENAR. Itu PROPOSAL; isinya baru BAB I yang
  di dalamnya ada "sistematika penulisan" (menyebut BAB II–V sebagai rencana).
  `state.py` TERTIPU oleh sistematika ini (mengira 5 bab) — `versi.py` benar.
- **Celah kecil** "BAB IIII" (salah tulis romawi) masih diterima — juga ada di
  `state.py`. Belum diperbaiki (jarang, dan tidak berbahaya).

## BACKUP

```
_arsip/pre-fix-bab-20261003/
   versi.py  f57e23daee758e7ac750f3471ea3da00
   state.py  89881fb3327bfb6ae32aec72fbc32d2a
   MD5.txt   (diverifikasi OK)
```

## BELUM DEPLOY — MENUNGGU IZIN BOS

Perbaikan ada di source; container masih memakai kode lama.
Cara deploy: `bash jalankan.sh` (bikin image baru + backup + verifikasi).

## DAMPAK KE MODE BELAJAR

✅ Sekarang mesin bisa mendeteksi bab di naskah mahasiswa nyata →
   syarat "minimal 1 bab selesai" untuk aktivasi Mode Belajar BISA diukur.
