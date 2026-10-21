# 🌙 SESI 09 OKT 2026 (malam) — KRONOLOGIS LENGKAP

> **BACA INI DULU kalau sesi baru dan Bos tanya "lanjut dari mana".**
> 1 berkas, urut waktu, dari titik masalah sampai putusan.

---

## 0. TITIK MULAI
Bos membaca `peta3_jev.py` sendiri, lalu mengajukan **4 poin** + 1 catatan kode.
Yang diminta: perbaikan kecil-kecil, **jangan borongan**, jangan sentuh jalur lama.

## 1. 4 POIN BOS (semua SELESAI, terpasang di `peta3_jev.py`)

| # | Poin | Status | Bukti |
|---|---|---|---|
| 1 | `POLA_BAB` terima angka (`BAB 1`) | ✅ | :31 `[IVX0-9]+` |
| 2 | `ANGKET` sinonim `KUESIONER` | ✅ | `^(KUESIONER\|ANGKET)\b` |
| 3 | D1 jangan bergantung label Jev | ✅ (2 putaran) | lihat §2 |
| 4 | Ronde beda ⇒ 'biasa' — **konservatif?** | ✅ **A** (putusan Bos) | + masuk daftar goyang |

## 2. POIN 3 BUTUH 2 PUTARAN (pelajaran penting)

```
PUTARAN 1 (WULAN SALAH): pakai `POLA_BAB.match(baris[i])`
  ⇒ Bos mengoreksi: POLA_BAB menuntut baris HANYA "BAB I" (^\s*$ di akhir).
     Semua baris begitu SUDAH disedot ke `gabung` di `susun()` ⇒ tak pernah kandidat.
     ⇒ klausa itu KODE MATI. WULAN UKUR: terbukti klausa tak pernah True. BOS BENAR.

PUTARAN 2 (KOREKSI BOS, TERPASANG):
  _POLA_BAB_TEKS = re.compile(r'^(?:\d+[.)]\s*|[IVX]+[.)]\s*)?BAB\s+[IVX0-9]+\b', re.I)
  calon = [... if _POLA_BAB_TEKS.match(baris[i].strip()) or label.get(i) == 'bab']
  ⇒ pola AWALAN (bukan baris-penuh). Uji bergigi 4/4 LULUS, nol false positive.
```

## 3. ATURAN 5 & 6 (BARU, dari temuan naskah #2)
Bos: *"urutan dampak"* → **ATURAN 5** dan **ATURAN 6** ditambahkan.

```
ATURAN 5 — baris diawali HURUF KECIL ⇒ KOREKSI LABEL (bukan buang)
   for i, _t in kand:
       if i in sistematika: continue      # WAJIB: jangan sentuh blok D1
       if label.get(i) in ('bab','subbab') and baris[i].strip()[:1].islower():
           label[i] = 'biasa'
Terukur: Wulandari-PDF 51 koreksi · ASIH 0 (tidak merusak).

ATURAN 6 — baris ANGKA MURNI (nomor halaman) ⇒ BUANG, di `dibuang()`
   if re.match(r'^\s*\d{1,4}\s*$', s): return True
Terukur: buang 12→106 (+94 = persis 94 nomor halaman); BAB palsu ("30","65") HILANG.

⚠️ URUTAN WAJIB di petakan(): D1 (`_tandai_sistematika`) HARUS SEBELUM Aturan 5.
⚠️ D1 varian-2: blok sistematika bisa "bagian ini" ATAU "Bab ini", dan frasanya
   bisa ADA DI DALAM baris itu sendiri (bukan baris pengikut).
   ⇒ `_FRASA_SISTEMATIKA` (search, bebas posisi) + `_PENGIKUT_SISTEMATIKA` (awal baris).
```

## 4. NASKAH #2 (WULANDARI) — PELAJARAN TERBESAR MALAM INI
```
Naskah SAMA, 4 cara simpan, hasil BEDA-BEDA:
  fid=112 PDF   → dibuat dari /tmp/skw.txt       (SKRIP HOST WULAN) ❌ SALAH
  fid=113 DOCX  → dibuat dari /tmp/skw_docx.txt  (SKRIP HOST WULAN, XML BOCOR) ❌
  fid=114 DOCX  → dari `app.ai._teks_dari_docx`  ✅ BENAR (0 XML)
  fid=115 PDF   → dari `app.ai._teks_dari_berkas` (pypdfium2) ✅ BENAR

🚨 WULAN 2× MENYALAHKAN EKSTRAKTOR padahal ekstraktornya SUDAH BENAR.
   Yang salah = WULAN jalan di luar sistem (skrip sendiri di host).

⇒ PAGAR BARU: uji naskah WAJIB lewat `app.ai._teks_dari_berkas`.
⇒ PAGAR BARU: sebelum lapor "berhasil", `grep -c '<w:tab' <hasil>` WAJIB 0.
⇒ TIDAK perlu tambah PyMuPDF: `pypdfium2` SUDAH ADA di produksi & SUDAH BENAR
   (PDF → "BAB I/II/III/VI" BERDIRI SENDIRI 4/4).
```

## 5. SISA MASALAH NYATA = MUTU FILE USER (bukan kode kita)
```
· PDF ber-TABEL → pypdfium2 pecah jadi baris 1 huruf (`'a'`,`'m'`,`'i'`)
  ⇒ batas alat, bukan bug. Tak ada pustaka PDF gratis yang andal merekonstruksi tabel.
· DOCX hasil `pdf2docx` (konverter LUAR) → "13 BAB I PENDAHULUAN" (nempel),
  "58 BAB III METODOLOGI PENELITIAN 3.1 Jenis…" (judul+sub-bab nyatu)
  ⇒ `_teks_dari_docx` kita membaca APA ADANYA (benar!) — file-nya yang rusak.
USUL KEBIJAKAN (BELUM diputuskan): deteksi PDF ber-tabel saat unggah (>10% baris
  ≤2 karakter) → beri tahu user "silakan unggah .docx aslinya" (TIDAK memblokir).
```
Detail: `TEMUAN_EKSTRAKSI_PDF_TABEL_09OKT2026.md`

## 6. ANGKA FINAL (terukur, jalur RESMI)
```
ASIH (kuantitatif, fid=81)       : BAB 5 · subbab 130 · paragraf 157 · NOL REGRESI
WULANDARI-DOCX RESMI (fid=114)   : BAB 3 · subbab 34 · paragraf 71 · kandidat 430
WULANDARI-PDF RESMI (fid=115)    : BAB 4/4 berdiri sendiri, TAPI 9.042 baris
                                    (pipeline TIMEOUT — perlu dipecah per-bab)
```

## 7. PUTUSAN BOS MALAM INI
```
① Poin 4 → A (konservatif, ronde beda ⇒ 'biasa', tetap masuk daftar goyang)
② Temuan ekstraksi → A (catat sebagai temuan resmi, tanpa ubah kode)
③ Tutup sesi → C (susun berkas kronologis + update dokumentasi + pasang flag)
```

## 8. YANG BELUM (agenda berikut)
```
1. `peta3_jev.py` BELUM MASUK APP — `app/peta_halus_jev.py` masih cara lama (menuju Kolaborasi)
2. Uji naskah #3 (Disertasi 103) — gerbang validasi 3-naskah belum genap
3. Simpan `section_state` + kolom mulai/akhir (bug `CatatanPembimbing.mulai`=0)
4. Sambung Kolaborasi: komentar pembimbing → tunjuk sub-bab → AI revisi potongan itu
5. `_rapikan_baris.py` — gagal 3×; kemungkinan TIDAK PERLU (Aturan 5 sudah menutup)
6. Profil kampus YAML — tunggu ≥2 kampus terukur
7. Sisa: `_t` dua peran (kosmetik) · gabung() tak tampil di HTML sajian
```

## 9. ⏰ CATATAN SEASON RESET
```
session_reset.at_hour: 4 (UTC) = 11.00 WIB ⇒ sesi baru, konteks lama HILANG.
YANG TETAP: memory + fact_store + skill. YANG HILANG: riwayat percakapan.
⇒ BACA: `MULAI_DARI_SINI.md` → `CATATAN_KEPUTUSAN_PETA3_09OKT2026.md` → berkas INI.
```
