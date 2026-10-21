# 🚨 TEMUAN: "KEKABURAN MENULAR" — BATAS JUMLAH KANDIDAT PER PANGGILAN JEV

> Ditemukan saat memperbaiki harness uji (perintah Bos: "perbaiki harness → uji
> wajib lewat susun()"). Sebab c04 akhirnya **bukan satu, tapi DUA**.

---

## 1. Sebab pertama (SUDAH diketahui): penggaris beda

```
Harness lama: baris dari `teks.split('\n')` (MENTAH, 9.042) → indeks 8.337 = DAFTAR ISI
Diperbaiki : baris dari `P.susun(115)['baris']` (SUSUN, 8.755) → indeks 8.050 = JUDUL
⇒ ✅ SUDAH DIPERBAIKI di harness (debug membuktikan i=8050 benar sekarang)
```

## 2. Sebab kedua (BARU DITEMUKAN): **KEKABURAN MENULAR**

Setelah indeks benar (i=8050), skor **MASIH 0,12**. Wulan uji dengan
mengubah **hanya** jumlah kandidat berbeda dalam satu panggilan:

```
c04 (L008050, JUDUL ASLI) — jumlah kandidat BERBEDA dalam 1 panggilan:
   1 kandidat berbeda   → 0,70  ✅
   2 kandidat berbeda   → 0,69  ✅
   4 kandidat berbeda   → 0,65  ✅
   8 kandidat berbeda   → 0,50  ⚠️  MELEWATI AMBANG 0,60
  16 kandidat berbeda   → 0,49  ❌  DIDEMOSI
```

**Kontrol:** bila jendela SAMA diulang 16× → 0,62 (tetap tinggi).
⇒ Penyebab **BUKAN** panjang bahan, **BUKAN** jumlah pertanyaan, **BUKAN**
kata di instructions — tapi **JUMLAH JENDELA YANG BERBEDA-BEDA**.

## 3. Apa artinya

```
Jev menilai satu kandidat, tapi BAHAN-nya bercampur dengan 7-15 jendela lain
yang isinya BUTIR/PECAHAN ⇒ jawabannya "tertular" keraguan ⇒ judul ASLI
yang seharusnya 0,70 turun ke 0,49 ⇒ DIDEMOSI jadi 'curiga'.

⇒ Ini bukan goyang acak. Ini SISTEMATIS: makin banyak kandidat, makin turun.
   Fungsinya monoton: 0,70 → 0,69 → 0,65 → 0,50 → 0,49
```

## 4. DAMPAK KE PRODUKSI (kenapa ini penting)

```
⚠️ Harness uji kita mengirim 16 kandidat × 3 kalimat = 48 pertanyaan
   ⇒ SEMUA angka uji K5 (11/16, 12/16, dst) DIUKUR DALAM KONDISI TERKABUR
   ⇒ Angka sebenarnya bisa LEBIH BAIK kalau kandidat dikirim lebih sedikit!

⚠️ Di PRODUKSI hakim_peta T① mengukur 74-77 kandidat dalam 1 fan-out
   ⇒ 77 kandidat = kondisi paling kabur.
   ⇒ Inilah kemungkinan sebabnya L007929 ('3.1 Jenis dan Waktu Penelitian',
     judul ASLI) 2× jatuh ke 'ragu' di uji 3-putaran!

📌 PELAJARAN LAMA kita (08 Okt) TERTULIS DI MEMORY:
   "503 = panjang STATE" → ternyata bukan hanya panjang, tapi JUMLAH JENDELA
   BERBEDA. Aturan lama "bahan Jev menumpuk = bahaya" TERBUKTI LAGI di sini.
```

## 5. JUJUR — yang BELUM diuji

```
❌ Apakah efeknya hanya pada 'noul' atau juga 'choice'? BELUM diuji.
❌ Apakah 'menular' karena jendela berisi baris yang mirip, atau semua jenis? BELUM.
❌ Batas aman berapa kandidat per panggilan? BARU terukur turun di 8.
   Belum diuji 5, 6, 7.
❌ Apakah gelombang BERURUTAN (gal) menolong — mis. 4 kandidat per panggilan?
⚠️ Uji ini pakai criteria PANJANG (K5 asli). Dengan criteria PENDEK
   ("Baris adalah JUDUL BAGIAN…") skor lebih rendah LAGI (0,25) — jadi
   criteria panjang itu PERLU, bukan hiasan.
```

## 6. USUL WULAN (belum dikerjakan — menunggu putusan)

```
A. PECAH panggilan jadi gelombang kecil (mis. maks 4 kandidat/panggilan)
   ⇒ biaya naik (panggilan lebih banyak) tapi presisi terjaga.
   ⇒ jalur SUDAH ADA: `_GAL_KAND = 120` di konversi.py (per jendela) — pola
     gelombang SUDAH dipakai Pass-1 stitch! Tinggal bilangan galnya diperkecil.

B. UKUR dulu batas aman (5, 6, 7 kandidat) — murah, 3 panggilan, dapat angka pasti.

C. ABAIKAN (kalau ambang 0,60 memberi ruang cukup) — RISIKO: judul asli bisa
   didemosi saat kandidat banyak. Terbukti di L007929.

Wulan sarankan B dulu (ukur batas), baru A. TIDAK B (abaikan).
```

## 7. URUTAN

```
① ✅ harness diperbaiki (susun()) — sesuai perintah Bos
② ✅ sebab c04 ketemu 2 lapis: (a) penggaris beda [sudah], (b) kekaburan menular [baru]
③ ⬜ Bos putuskan: ukur batas (B) → pecah gelombang (A)?
④ ⬜ sesudahnya: uji Opsi A (4× Informan) + instalasi
```
