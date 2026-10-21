# UKUR ULANG 19 KASUS — K5 vs K5-BARU vs K5-KETAT (09 Okt 2026)

> **Protokol Bos:** *"tempel definisi → ukur ulang 3 naskah… protokol pengukurannya
> sama ketatnya (12 kasus + validasi silang, bukan tempel-buta)."*
>
> Naskah: `fid=115` (Wulandari). Kasus: 16 terkumpul (12 lama + 4× `N. Informan`)
> · 3 baris lain sudah terverifikasi konteksnya di audit sebelumnya.
> **1 fan-out, 48 pertanyaan, 3 kalimat K5 sekaligus.**

---

## 1. HASIL

| Kalimat | BENAR | Catatan |
|---|---|---|
| **K5-LAMA** (terpasang) | **11/16 (69%)** | gagal 5 |
| **K5-BARU** (+D-A +D-B +D-C disjungtif) | **11/16 (69%)** | gagal 5 — **sama** |
| **K5-KETAT** (anak = syarat PERLU) | **10/16 (62%)** | gagal 6 — **LEBIH BURUK** |

### ✅ CATATAN BOS TERBUKTI PERSIS
```
K5-KETAT: '4. Threats (Ancaman)' (JUDUL, tanpa anak) → noul 0,22 ⇒ GUGUR ❌
K5-BARU : '4. Threats (Ancaman)'                      → lolos ✅
⇒ Bos benar: definisi "anak bernomor" HARUS DISJUNGTIF, bukan syarat perlu.
⇒ Wulan menulisnya disjungtif ⇒ 1 judul terselamatkan.
```

### ⚠️ Yang GAGAL sama di K5-LAMA & K5-BARU (5 kasus)
```
c04 '3. Tinjauan Literatur'            kunci JUDUL   noul 0,12  ❌
c10 '1. Informan (Ulan – …'            kunci JUDUL   noul 0,05-0,07  ❌
c11 '2. Informan (Regina – …'          kunci JUDUL   noul 0,04-0,06  ❌
c12 '3. Informan (Anie – …'            kunci JUDUL   noul 0,04-0,05  ❌
c13 '4. Informan (April – …'           kunci JUDUL   noul 0,05-0,07  ❌
```

---

## 2. WULAN CARI AKARNYA — 3 UJI

### Uji 1: apakah jendela MEMOTONG anaknya? → **TIDAK**
```
Yang DIKIRIM ke Jev:
   L008425| Berikut hasil reduksi data dari 4 (empat) informan yang dipilih :
 >>L008426| 1. Informan (Ulan – Pengelola AyuMeera)
   L008427| a. Strengths (Kekuatan)      ← ANAK TERKIRIM ✅
   L008428| - Memenuhi kebutuhan…
⇒ Jev MELIHAT anaknya, tapi tetap bilang BUKAN. Jendela bukan sebab.
```

### Uji 2: apakah Jev bereaksi pada ISI baris? → **TIDAK (0,32-0,39 semua)**
```
3 varian, isi barisnya diubah, jendela sama:
   A_asli           '1. Informan (Ulan – Pengelola AyuMeera)'  → 0,35 BUKAN
   B_tanpa_informan '1. Pengelola AyuMeera (Ulan)'            → 0,32 BUKAN
   C_temuan         '1. Temuan Penelitian (Ulan…)'            → 0,39 BUKAN
⇒ Bukan karena kata "Informan". Semua varian BUKAN.
```

### Uji 3: apakah alasan sebenarnya = **NAMA JENIS (kegiatan)**, bukan keadaan?
```
Baris ③ '1. Informan (Ulan – …)'  → polanya SAMA dengan '2. Wawancara'
                                     (dua-duanya "nama KEGIATAN bernomor")
Baris ② '6 Sidang Skripsi'        → "nama KEGIATAN bernomor"
⇒ Jev konsisten: nama kegiatan/langkah bernomor = BUTIR. **Konsisten, bukan bug.**
```

---

## 3. TEMUAN JUJUR — DEFINISI ③ BERTABRAKAN DENGAN K5

```
K5 (terpasang, diukur 12/12 di 3 naskah):
   'nama KEGIATAN bernomor' ⇒ BUTIR      ← TERUKUR 12/12

Putusan Bos ③:
   '1. Informan (Ulan – Pengelola AyuMeera)' ⇒ JUDUL (karena menaungi anak a.)

⇒ KEDUANYA BENAR pada datanya sendiri, tapi SALING BERTABRAKAN:
   · 'Informan' secara KAMUS = nama KEGIATAN/langkah (mewawancarai orang)
   · Tapi secara STRUKTUR = menaungi anak (a., b., c.)
```

**3 pilihan (Bos putuskan — Wulan TIDAK memutuskan sendiri):**

- **A. Terima bahwa ③ butuh sinyal BARU, bukan tambahan kalimat.**
  K5 sekarang menilai dari **isi baris + jendela**. Untuk ④③ (Informan),
  sinyal yang membedakan hanyalah **"punya anak atau tidak"** — dan itu
  **bisa diputuskan KODE** (regex `^[a-h][.)]`), bukan Jev.
  ⚠️ Tapi aturan Bos: *"jangan andalkan regex untuk MENGENALI bentuk naskah"* —
  **kecuali** ini **FAKTA yang kode tahu tapi tak bisa putuskan** (pola SAH
  terbukti: peta bab pakai "panjang isi" sebagai fakta). Calon: kirim fakta
  **`punya_anak_bernomor: ya/tidak`** ke Jev sebagai bagian `state`.
  ⇒ UJI DULU: apakah menambah fakta ini menaikkan ③ tanpa memerosotkan 12 kasus lama?

- **B. Terima keputusan Bos apa adanya** dan catat 4× Informan sebagai
  **kasus janggal yang DIBIARKAN** (kunci dibangun ulang akan memuat
  pengecualian ini secara eksplisit, bukan lewat K5).

- **C. Balik definisi**: baris bernomor yang menaungi anak = judul **HANYA JIKA
  topiknya bukan nama kegiatan**. ③ Informan gugur ⇒ bertentangan dengan putusan Bos.
  (**Wulan TIDAK sarankan** — melawan putusan Bos.)

---

## 4. CATATAN KETAT — KEJUJURAN PENGUKURAN

```
⚠️ K5-BARU TIDAK LEBIH BAIK dari K5-LAMA pada 16 kasus ini (11/16 vs 11/16).
   ⇒ Perbaikan D-A/D-B BELUM TERBUKTI MENGUBAH APA PUN di set ini
     (D-A & D-B memang sudah ditangani K5-LAMA dengan benar).
   ⇒ satu-satunya kemenangan terukur = DISJUNGTIF (menyelamatkan '4. Threats')
     yang terbukti lewat K5-KETAT (10/16, gugur 1 judul).

⚠️ 19 kasus → 16 terkumpul ('2. Wawancara' & '2000' tidak ketemu lewat
   pencarian ISI di fid=115 versi sekarang; indeks bergeser).
⚠️ 12 kasus LAMA baru diuji ulang di 1 naskah (fid=115), bukan 2 seperti aslinya.
⚠️ '3. Tinjauan Literatur' (c04) → 0,12 di sini, padahal 0,63 di naskah Asih.
   ⇒ NASKAH BEDA, JAWABAN BEDA ⇒ belum bisa disimpulkan K5 salah.
```

---

## 5. URUTAN BERIKUT

1. ✅ definisi ditulis (dokumen terpisah)
2. ✅ ukur ulang 16 kasus × 3 kalimat — hasil di atas
3. ⬜ **Bos putuskan A / B / C** untuk tabrakan ③ (Informan)
4. ⬜ kalau A: uji "fakta punya anak" sebagai `state` (pola sah terukur)
5. ⬜ tempel ke `CRITERIA_K5` + perbarui gerbang
