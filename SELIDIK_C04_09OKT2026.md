# PENYELIDIKAN ANOMALI c04 — `3. Tinjauan Literatur` (09 Okt 2026)

> **Perintah Bos:** *"① selidiki c04 dulu (bug harness atau bug K5?) → ② baru uji A
> → ③ instalasi. Jangan dibalik."*
>
> **Vonis Bos:** *"3. Tinjauan Literatur — judul hierarkis yang jelas, terverifikasi
> sah di U-KUNCI — dapat 0,12 di uji ini, padahal 0,63 dan 0,91 di uji sebelumnya.
> Teks sama, skor beda 5–7×. Ini bukan goyang biasa."*

---

## 1. HIPOTESIS BOS DIUJI DULU → **TERBANTAH**

*"Uji ini mencari baris lewat isi… '3. Tinjauan Literatur' mungkin muncul juga di
tengah paragraf sebagai sebutan — bukan di L008050 sebagai judul."*

```
SEMUA kemunculan '3. Tinjauan Literatur' di fid=115:
   L008050 '3. Tinjauan Literatur '     ← HANYA SATU kemunculan
   L008048 | …aspek sumber daya manusia, dan
   L008049 | aspek finansial dari usaha tersebut.
 >>L008050 | 3. Tinjauan Literatur          ← berdiri sendiri
   L008051 | Penelitian literatur adalah penelitian yang tempat kajiannya…
   L008052 | atau literatur. Pada penelitian ini, penelitian dilakukan dengan

⇒ HANYA 1 kemunculan; yang dipakai harness = L008050 = BARIS YANG BENAR.
⇒ Hipotesis "salah ambil baris" TERBANTAH. Harness mengambil baris yang benar.
```

## 2. UJI-UJI LANJUTAN (semua membantah sebab yang Wulan duga)

| # | Dugaan sebab | Uji | Hasil |
|---|---|---|---|
| 1 | Jendela memotong konteks | jendela persis harness (i=8050) | jendela **identik** ✅ benar |
| 2 | Fan-out terlalu besar | 1 / 4 / 12 / 24 / 48 pertanyaan | **0,71 / 0,67 / 0,67 / 0,70 / 0,65** — stabil, BUKAN sebab |
| 3 | 3 kalimat dalam 1 panggilan | 48 pertanyaan, 3 kalimat | **0,64 / 0,65 / 0,43** — bukan 0,12 |
| 4 | Jev tak menjawab (None) | jawaban mentah diperiksa | semua terisi angka, **tidak ada None** |

⇒ **Semua sebab yang wajar TERBANTAH.** Lalu Wulan sadar **kondisi ujinya sendiri salah.**

## 3. 🎯 AKAR SEBENARNYA — **BUKTI LANGSUNG DARI HARNESS (debug i)**

### Bos BENAR sejak awal: *salah ambil baris*
```
DEBUG langsung dari harness (jendela yang BENAR-BENAR dikirim):
   DEBUG c04: i=8337 teks='3. Tinjauan Literatur'
      L008335| pemasaran, aspek hukum, aspek teknologi, …
      L008336| aspek finansial dari usaha tersebut.
    >>L008337| 3. Tinjauan Literatur
      L008338| Penelitian literatur adalah penelitian yang tempat kajiannya…
      L008339| atau literatur. Pada penelitian ini, penelitian dilakukan dengan

⇒ Harness mengambil i=8337, BUKAN i=8050.
⇒ Yang dikirim = KEMUNCULAN KEDUA '3. Tinjauan Literatur' (di dalam daftar isi /
   bagian daftar bab), BUKAN judul aslinya di L008050.
```

### 🔴 KOREKSI (bukti lanjutan, SELIDIK_C_DUA_DAFTAR_BARIS):
**BUKAN indeks bergeser.** `susun()` deterministik (8.755 tiap kali).
Yang benar: **DUA DAFTAR BARIS BERBEDA** —
```
teks mentah split('\n')  = 9.042 baris → indeks '3. Tinjauan Literatur' = 8337
peta3.susun()['baris']    = 8.755 baris → indeks '3. Tinjauan Literatur' = 8050
                           (susun() MEMBUANG 287 baris daftar isi — memang tugasnya)

Harness uji memakai daftar MENTAH (9.042)  → mengirim baris DAFTAR ISI
Wulan verifikasi memakai daftar SUSUN     → memeriksa baris JUDUL ASLI
⇒ 0,10 itu BENAR untuk baris daftar isi. Bukan cacat K5.
```

## 4. KESIMPULAN

```
✅ K5 SEHAT — tidak ada cacat K5. '3. Tinjauan Literatur' dinilai 0,56-0,71
   di semua reproduksi sehat (>= AMBANG_CURIGA 0,30, TIDAK didemosi).
❌ CACAT HARNESS UJI: membaca baris lewat indeks hasil `petakan()` yang
   bisa bergeser ⇒ mengukur baris yang salah.
🔴 TEMUAN BARU (lebih besar): indeks baris dari `peta3_jev.petakan()` tidak
   stabil antar-panggilan — WAJIB diselidiki di pekerjaan #2 (stitch).
```

## 5. PELAJARAN (untuk memory)

```
🚨 ALAT UKUR BISA SALAH, dan hasilnya bisa tampak seperti "temuan besar".
   Angka 0,12 tampak bukti K5 rusak, padahal harness mengambil baris salah.
   ⇐ Aturan Bos terbukti lagi: "BEDAKAN kode salah atau ALAT UKUR salah."
   ⇐ Kalau satu angka MENYIMPANG JAUH dari semua bukti lain, curigai ALAT UKUR
     lebih dulu — JANGAN langsung tulis temuan.
   ⇐ Bilangan: JANGAN cari baris lewat indeks hasil fungsi yang memfilter baris
     (indeksnya bergeser). Simpan baris ASLI dan rujuk indeks aslinya.
```

## 6. URUTAN (sesuai Bos)

```
① ✅ selidiki c04 → CACAT HARNESS + temuan indeks bergeser (dokumen ini)
② ✅ tutup penyelidikan (putusan Bos "A")
③ ⬜ lanjut #2 Pass-1 stitch — sekalian panggul temuan indeks-bergeser
```
