# ①c — KALIMAT `criteria` DIUJI 12 KASUS BATAS (09 Okt 2026)

> **Vonis Bos:** *"Buktinya arahnya benar (palsu 0,84→0,73 ⬇️, asli →0,91 ⬆️), tapi
> n=2 belum cukup untuk mengunci… Ukur semuanya dalam 1 fan-out… Uji penyempurnaan
> #1 harus mengukur apakah kalimat yang BAIK MEMBALIK KASUS BATAS DENGAN BENAR,
> bukan sekadar menggeser skor."*

---

## 1. CARA UKUR

- **12 kasus batas**, semua dari **naskah NYATA** & kunci **DIBACA dari naskah**
  (bukan tebakan indeks — pelajaran: indeks baris BERGESER antar-perubahan
  `susun()`; baris dicari lewat ISI-nya).
- **7 kategori:** N baris angka tabel (3) · H kepala kolom/tabel (4) · K
  keterangan tabel (1) · S fragmen sitasi (2) · T judul sah (1) · B butir daftar (1).
- **1 fan-out** per varian kalimat (semua 12 kasus sekali panggilan).
- Ambang vonis: `noul ≥ 0,5` ⇒ JUDUL · `< 0,5` ⇒ BUKAN.

---

## 2. HASIL (3× ulangan)

| Varian kalimat | Ulangan 1 | Ulangan 2 | Ulangan 3 | Sifat |
|---|---|---|---|---|
| **K0** tanpa criteria | 0/12 (0%) | — | — | 📉 tidak berguna |
| **K1** melingkar ("ini judul asli"/"bukan judul asli") | 0/12 (0%) | — | — | ❌ **nol guna** |
| **K2** ciri teramati | 11/12 (92%) | 11/12 | 11/12 | ⚠️ goyang |
| **K3** ciri + pembeda | 9/12 (75%) | — | — | ❌ lebih buruk |
| **K4** ciri diperkuat | 11/12 (92%) | 12/12 | 11/12 | ⚠️ goyang |
| **K5** PEMBEDA TEGAS | **12/12 (100%)** | **12/12** | **12/12** | ✅ **STABIL** |

---

## 3. APA YANG TERBUKTI (vonis Bos tepat)

### ① Kalimat MELINGKAR memang nol guna
```
K1 ("Baris ini judul asli." / "Baris ini bukan judul asli.") → 0/12 (0%)
K0 (tanpa criteria)                                          → 0/12 (0%)
⇒ K1 TIDAK lebih baik dari tidak pakai criteria sama sekali.
```

### ② Kalimat BAIK **MEMBALIK vonis**, bukan geser skor
```
kasus c11 '2. Wawancara' (kunci: BUKAN judul):
   tanpa 0,23 ✅ · melingkar 0,55 ❌ · K2 0,77 ❌ · K3 0,77 ❌ · K4 0,53 ❌
   ⇒ K5 tegas: 0,24 ✅  ← MEMBALIK dari 0,53 → 0,24
kasus c10 '3. Tinjauan Literatur' (kunci: JUDUL):
   tanpa 0,40 ❌ · K5 0,63 ✅  ← MEMBALIK dari bawah ke atas ambang
```

### ③ Bahaya NYATA: criteria yang BURUK bisa MERUSAK
```
c11 '2. Wawancara': tanpa criteria 0,23 (benar) → melingkar 0,55 (SALAH)
⇒ Kalimat melingkar MENAIKKAN skor baris yang seharusnya ditolak.
   Ini bukti criteria bukan hiasan — ia bisa memperburuk.
```

### ④ Semakin bertele-tele ≠ semakin baik
```
K2 (pendek, ciri)   → 92%  ✅
K3 (ditambah frasa)  → 75%  ❌  ← lebih buruk!
⇒ Panjangnya deskripsi bukan jaminan. Yang menentukan: PEMBEDA yang tepat.
```

---

## 4. K5 — KALIMAT PEMENANG (12/12, stabil 3×)

```
instructions:
  "Apakah baris tengah pada jendela ini adalah KEPALA BAGIAN naskah?"

criteria:
  true : "Baris adalah JUDUL BAGIAN dari kerangka naskah. Ciri: berisi NAMA
          TOPIK BAHASAN (bukan nama kegiatan/langkah), nomornya menandai
          kedudukan bagian dalam kerangka tulisan seperti 2.1 atau BAB II atau
          nomor polos tanpa titik yang sejajar dengan judul bab lain di dokumen
          ini, dan baris berikutnya mulai dengan paragraf penjelasan baru."
  false: "Baris adalah SATU LANGKAH KEGIATAN atau SATU BUTIR dari sebuah daftar
          cara kerja, atau bagian lain yang bukan kepala tulisan: deret angka
          di dalam tabel, sel dan kolom, keterangan bernama di atas tabel atau
          gambar, potongan kutipan wawancara, nama sumber, atau sambungan
          kalimat sebelumnya yang belum selesai."
```

**Kunci pembeda yang bekerja:** `NAMA TOPIK BAHASAN` (bukan nama
kegiatan/langkah). Itu yang memisahkan `3. Tinjauan Literatur` (topik) dari
`2. Wawancara` (kegiatan) — padahal bentuk nomornya identik.

---

## 5. PAGAR PENGINGAT (dari Bos — dipatuhi)

> *"skor yang makin tajam jangan sampai menggoda untuk menghidupkan kembali
> gerbang-p. U4b tetap berlaku — p display-only, apa pun ketajamannya."*

⇒ **Dipatuhi.** Skor di dokumen ini **TIDAK dipakai** sebagai saklar keputusan
produksi. `p` tetap **info tampilan**. Yang dipakai surveyor/hakim = **label**
(`sepakat`/`ragu`/`curiga`) sesuai §7c, bukan ambang `p`.

---

## 6. YANG BELUM (jujur)

- ❌ Kalimat K5 **belum dipasang** ke `peta3_jev` / `hakim_peta` — masih uji.
- ❌ **12 kasus** dari 2 naskah; belum naskah ketiga/keempat.
- ⚠️ Kunci jawaban kita **kontrol sendiri** (bukan kunci resmi terverifikasi
  manusia) — walau tiap baris **dibaca dari naskah**.
- ❌ Belum jadi gerbang otomatis (asersi: K5 ≥ 11/12 · K1 ≤ 1/12).
- ⚠️ K5 menang di 1 SET kasus; **belum** diuji pada kandidat judul BAB
  (peran berbeda: kepala bab vs kepala sub-bab).

---

## 7. URUTAN BERIKUTNYA

1. ✅ **① criteria** — pagar dibuka + kalimat terukur (`HASIL_UJI_CRITERIA_NOUL…`
   + dokumen ini)
2. ⬜ Asersi gerbang khusus criteria (objek diterima · string ditolak ·
   tanpa true/false ditolak) — **Bos setuju ini perlu**
3. ⬜ **② Pass-1 stitch + ③④** — ukur recall kandidat (uji L008039)
4. ⬜ **⑤ pensiunkan ambang-`p`** (sinkron U4b)
