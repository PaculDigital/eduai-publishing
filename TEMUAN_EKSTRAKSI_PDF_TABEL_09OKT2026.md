<!-- TEMUAN (RIWAYAT) — SOT: bukan sumber status. Status peta naskah ada di SOT.md §SESI TERAKHIR -->

# 🔍 TEMUAN EKSTRAKSI NASKAH — PDF ber-tabel vs DOCX (09 Okt 2026)

> Ditemukan saat uji naskah #2 (Skripsi Wulandari A. Parmata, 112110566 — kualitatif SWOT).
> Status: **TEMUAN RESMI**, belum ada perubahan kode. Menunggu keputusan kebijakan.

## KESIMPULAN SATU BARIS
**Ekstraktor kita SUDAH BENAR. Yang menentukan mutu peta adalah MUTU FILE yang
diunggah user.** Naskah yang sama bisa menghasilkan peta bagus atau kacau
tergantung bentuk file sumbernya.

## 3 SUMBER FILE, 3 CACAT BERBEDA (naskah SAMA)

| sumber | cara baca | BAB | cacat |
|---|---|---|---|
| **PDF** (asli, 1,1 MB) | `pypdfium2` (RESMI, ada di produksi) | **4/4 berdiri sendiri** ✅ | teks ber-tabel pecah jadi **baris 1 huruf** ❌ |
| **DOCX asli penulis** (311 KB) | `_teks_dari_docx` (ET.parse) | menempel ❌ | XML bersih, tapi judul+halaman nyatu |
| **DOCX hasil pdf2docx** | `_teks_dari_docx` | menempel ❌ | nomor halaman + judul + isi MENYATU |

## BUKTI TERUKUR

### PDF via pypdfium2 (JALUR RESMI) — BAB sempurna, isi pecah
```
[L00000] 'BAB I'      ✅       total 9.042 baris
[L00471] 'BAB II'     ✅       <w:tab = 0
[L07927] 'BAB III'    ✅
[L08141] 'BAB VI'     ✅
```
⚠️ CACAT: sampel tiap 800 baris → `L01600 'a'` · `L02400 'a'` · `L03200 'm'` ·
`L04000 'a'` · `L04800 'i'` · `L06400 'i'` · `L07200 'n'`
⇒ PDF ini berisi **tabel besar** (matriks SWOT, IFAS/EFAS, tabel perbandingan).
`pypdfium2` membaca per-baris-halaman → teks dalam sel tabel pecah per karakter.

### DOCX via `_teks_dari_docx` (JALUR RESMI) — XML bersih, judul menempel
```
panjang : 142.464 kar · baris : 1.241 · <w:tab : 0 ✅
[0182] '13 BAB I PENDAHULUAN'                  ← nomor halaman MENEMPEL di depan
[0390] '30 BAB II'                             ← nomor halaman MENEMPEL
[0840] '58 BAB III METODOLOGI PENELITIAN 3.1 Jenis dan Waktu Penelitian 3.1.1…'
                                               ← judul BAB + sub-bab 3.1 MENYATU
[0961] '65 BAB VI HASIL PENELITIAN DAN PEMBAHASAN'
```

## AKAR (bukan tebakan)
```
1. `pypdfium2` & `pypdf` & `fitz` membaca PDF PER-BARIS HALAMAN.
   ⇒ Teks di dalam TABEL tidak punya struktur → pecah per potongan visual.
   ⇒ Ini BATAS ALAT, bukan bug kode kita. Tak ada pustaka PDF gratis yang
     merekonstruksi tabel dengan andal.

2. `pdf2docx` (konverter LUAR, bukan milik kita) menghasilkan .docx yang
   menempelkan nomor halaman ke judul ("13 BAB I PENDAHULUAN").
   ⇒ `_teks_dari_docx` kita membaca APA ADANYA (benar!) — yang rusak file-nya.
```

## ⛔ KESALAHAN WULAN SAAT UJI (jangan diulang)
```
Wulan 2× MENYALAHKAN EKSTRAKTOR padahal ekstraktornya benar:
  · fid=112 dibuat dari /tmp/skw.txt      → skrip HOST, bukan jalur resmi
  · fid=113 dibuat dari /tmp/skw_docx.txt → skrip HOST, XML BOCOR ❌
  · fid=114 dari `_teks_dari_docx`        → BARU BENAR
  · fid=115 dari `_teks_dari_berkas` (pypdfium2) → BARU BENAR

⇒ ATURAN: uji naskah WAJIB lewat `app.ai._teks_dari_berkas` (jalur resmi),
  JANGAN skrip sendiri di host. Selisihnya besar (XML bocor vs bersih).
⇒ PAGAR sebelum lapor: `grep -c '<w:tab' <hasil>` WAJIB 0.
```

## USUL KEBIJAKAN (menunggu putusan Bos)
```
DETEKSI otomatis saat unggah: kalau PDF → banyak baris 1–2 huruf
  (mis. >10% baris dengan ≤2 karakter) ⇒ artinya PDF ber-tabel/berkolom.
⇒ PESAN JUJUR ke user:
  "PDF ini sepertinya hasil cetak dari Word yang banyak tabelnya. Supaya
   peta naskah lebih presisi, silakan unggah berkas .docx aslinya."
⇒ TIDAK memblokir (user boleh lanjut), hanya memberi tahu.
```

## CATATAN TEKNIS
- `fitz` (PyMuPDF) **TIDAK ADA** di image produksi. Yang ada: `pypdfium2` saja.
  ⇒ TIDAK perlu menambah PyMuPDF: hasilnya sama (sama-sama baca per-baris).
- BERKAS UJI: fid 112 (PDF skrip-host, salah) · 113 (DOCX skrip-host, salah) ·
  114 (DOCX resmi) · 115 (PDF resmi, timeout di 9.042 baris).
- Naskah #2 = Skripsi Wulandari A. Parmata (112110566), analisis SWOT
  kelayakan usaha Accessories Hijab Tape AyuMeera, PT. Saitec Prima Mandiri.
