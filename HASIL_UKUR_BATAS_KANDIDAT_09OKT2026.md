# HASIL UKUR BATAS AMAN KANDIDAT (09 Okt 2026)

> **Perintah Bos:** *"B — ukur batas aman (5, 6, 7 kandidat; 3 panggilan murah)"*
> Naskah: fid=115 · kandidat uji: c00 = **L008050 `3. Tinjauan Literatur`** (JUDUL ASLI)

---

## 1. HASIL UTAMA — **bukan "makin banyak makin turun"**

```
A. c00 SENDIRIAN (tanpa penular), 5× ulang:
      0,70  0,69  0,73  0,70  0,75     rata = 0,71   ✅ STABIL
B. c00 + 4 PENULAR (total 5 kandidat), 5× ulang:
      0,59  0,52  0,52  0,54  0,42     rata = 0,52   ⚠️ TURUN + GOYANG
```

**⇒ Yang benar: SEKALI ada kandidat lain, langsung jatuh (~0,71 → ~0,52).**
Bukan bertahap. Lompatan terjadi di kandidat ke-2.

## 2. UKUR 5/6/7/8 KANDIDAT (yang diminta Bos)

```
 5 kandidat → 0,56 0,54 0,50  rata 0,53  ⚠️ ragu
 6 kandidat → 0,59 0,64 0,56  rata 0,60  ⚠️ ragu (tepat di ambang)
 7 kandidat → 0,51 0,59 0,55  rata 0,55  ⚠️ ragu
 8 kandidat → 0,64 0,54 0,59  rata 0,59  ⚠️ ragu
16 kandidat → rata 0,49  ❌ curiga (didemosi)
```

⇒ **Antara 2 dan 16 tidak ada "batas aman"** — semuanya jatuh ke zona ragu.
⇒ Yang menentukan **BUKAN jumlah**, tapi **ADA-TIDAKNYA kandidat lain**.

## 3. PENULAR MANA YANG MERUSAK? — **SEMUA SAMA**

```
c00 sendirian = 0,71
+ '2020' (angka)                      → 0,50 ⬇️
+ '(Khoironi, 2023)' (sitasi)         → 0,52 ⬇️
+ '2. Wawancara' (butir)              → 0,61
+ '6 Sidang Skripsi' (butir)          → 0,57 ⬇️
+ 'Kekuatan (Strength)' (kepala tabel)→ 0,53 ⬇️
+ 'Kategori Hasil…' (header tabel)    → 0,52 ⬇️
+ '1. Informan (Ulan…)' (butir+anak)  → 0,56 ⬇️
+ 'Tabel 4. 1 …' (caption)            → 0,58 ⬇️
+ '4. Threats (Ancaman)' (judul)      → 0,54 ⬇️
```

⇒ **Tidak ada penular khusus.** Bahkan **judul ASLI lain** (`4. Threats`) ikut
menularkan! ⇒ Ini **bukan** soal isi kandidat, tapi soal **Jev menilai banyak
konteks sekaligus** — perhatiannya terbagi.

## 4. ARTI SEBENARNYA (jujur)

```
Jev menilai SATU kandidat dengan BAIK bila bahannya bersih (0,71 stabil).
Begitu ada 2+ kandidat, ia menjawab dengan "ragu" (~0,52) — karena ia
menimbang seluruh bahan, bukan satu baris.

⇒ INI SIFAT JEV (resmi: "Each answer is independent... one question's answer
   is not hidden context for another"), TAPI BUKTI KITA: bahan yang bercampur
   TETAP menurunkan skornya. Bukan "hidden context" tapi "perhatian terbagi".
```

## 5. KONSEKUENSI — angka uji kita selama ini SALAH UKUR

```
🚨 SEMUA uji K5 (11/16, 12/16) dikirim 48 pertanyaan dalam 1 panggilan
   ⇒ diukur dalam kondisi "perhatian terbagi" ⇒ angka LEBIH BURUK dari asli
   ⇒ Skor sebenarnya K5: **0,71 pada judul asli** (bukan 0,53/0,59)

🚨 Di PRODUKSI hakim_peta T① mengirim 74-77 kandidat sekaligus
   ⇒ kondisi paling terbagi ⇒ judul asli dinilai ~0,49-0,55
   ⇒ TERBUKTI L007929 ('3.1 Jenis dan Waktu Penelitian', judul ASLI) 2× 'ragu'
   ⇒ RISIKO NYATA: judul asli didemosi di produksi!
```

## 6. USUL (untuk putusan Bos — langkah A)

```
A. PECAH gelombang: kirim kandidat satu per satu? → presisi maksimal (0,71)
   tapi panggilan = jumlah kandidat (74× = mahal + lambat) ❌

B. KIRIM 2 KANDIDAT/panggilan + c00 SELALU tanpa penular?? → tidak bisa,
   kandidat tidak boleh diistimewakan (nol tebakan di kode)

C. ⭐ AMBANG BERBEDA per kondisi:
      kalau panggilan memuat ≤2 kandidat → pakai ambang 0,60 (Jev jernih)
      kalau ≥3 kandidat → Jev memang menjawab 'ragu' untuk SEMUA,
      ⇒ jangan pakai skor untuk memutuskan judul/curiga;
        pakai skor hanya sebagai PEMBANDING RELATIF antar-kandidat
        (judul asli 0,71 vs butir 0,30 → TERPISAH jelas) ✅

D. Tambah KONTEKS PEMISAH di bahan: penanda tegas antar kandidat supaya
   Jev tidak mencampur (mis. garis pemisah + label "kandidat 1 dari 74")
   ⇒ BELUM diuji, murah untuk dicoba.
```

## 7. YANG BELUM DIUJI (jujur)

```
❌ Apakah skor RELATIF masih valid saat bercampur (uji C) — belum diuji nyata
❌ Apakah pemisah tegas (uji D) menolong — belum
❌ Efek pada tipe `choice` (produksi pakai choice) — belum
❌ Batas jumlah untuk tipe `choice` — belum
```
