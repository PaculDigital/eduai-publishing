# SELIDIK C — BUKTI: DUA DAFTAR BARIS BERBEDA (09 Okt 2026)

> **Pilihan Bos: C** — selidiki dulu tanpa ubah kode.
> Pertanyaan: apakah indeks baris bergeser antar-panggilan? **JAWABAN: BUKAN.**
> Yang benar: **ada DUA daftar baris yang berbeda**, dan harness kita memakai
> daftar yang satu sementara Wulan memverifikasi di daftar yang lain.

---

## 1. BUKTI ANGKA NYATA (tanpa panggil Jev)

| Naskah | teks mentah (`split('\n')`) | `peta3.susun()['baris']` | selisih | indeks `3. Tinjauan Literatur` |
|---|---|---|---|---|
| **fid=115** (PDF) | **9.042** | **8.755** | **−287** | mentah **8.337** · susun **8.050** |
| fid=81 (Asih) | 2.224 | 1.874 | −350 | tidak ada di keduanya |
| fid=104 (Disertasi) | 26.065 | 25.055 | −1.010 | tidak ada di keduanya |

**⇒ `peta3.susun()` MEMBUANG 287 baris** (daftar isi, penanda, dll) —
dan itu **benar** (memang tugasnya). **Tidak ada indeks bergeser antar-panggilan.**

## 2. 🔴 AKAR c04 — SALAH DAFTAR, BUKAN SALAH INDEKS

```
Keliru Wulan tulis di SELIDIK_C04 bagian 3: "petakan() mengembalikan baris
BERINDEKS BERBEDA tiap panggilan" ⇒ SALAH. Bukti: susun() deterministik
(8.755 setiap kali).

Yang SEBENARNYA terjadi di harness `uji_19kasus_k5baru.py`:

   baris_fid(fid)  →  ai._teks_dari_berkas(...).split('\n')   ← DAFTAR MENTAH 9.042
        ↓
   cari '3. Tinjauan Literatur'  →  indeks 8.337                ← baris MENTAH
        ↓
   jendela dikirim ke Jev dari DAFTAR MENTAH (9.042 baris)

   Sementara Wulan VERIFIKASI manual lewat
   peta3.petakan()['baris']  →  DAFTAR SUSUN 8.755, indeks 8.050

⇒ 8.337 ≠ 8.050 = BUKAN indeks bergeser; DUA DAFTAR yang panjangnya beda.
⇒ Yang dikirim harness = '3. Tinjauan Literatur' versi DAFTAR ISI
   (di dalam 287 baris yang sudah dibuang susun()).
⇒ Jev menjawab 0,10 dengan BENAR: baris di daftar isi memang BUKAN judul (itu
   entri daftar isi).
```

**Tambahan bukti:** `kandidat_sambung` di fid=115 = **7.632** baris, sedangkan
`_pegangan peta3` hanya **8755**. Di fid=104: **0** kandidat (dokumen itu tak
punya baris pendek berdempet). ⇒ **tiap jalur melihat naskah dengan bentuk berbeda.**

## 3. KESIMPULAN

```
✅ K5 SEHAT — 0,10 itu benar untuk baris DAFTAR ISI.
❌ CACAT HARNESS WULAN: mengambil baris dari daftar MENTAH, bukan daftar
   `susun()` yang dipakai peta3/Jev. ⇒ mengukur baris yang salah.
🔴 TEMUAN NYATA (tetap berharga, tapi lebih kecil dari duga semula):
   ada **3 cara berbeda** membaca naskah di proyek ini:
      (a) `ai._teks_dari_berkas().split('\n')`  → MENTAH (9.042)
      (b) `peta3.susun()['baris']`              → SUSUN (8.755)   ← dipakai peta
      (c) `konversi._pecah_blok().lines`        → BLOK tersambung ← dipakai konversi
   ⇒ indeks dari satu cara TIDAK SAH dipakai di cara lain.
   ⇒ WAJIB satu acuan; untuk sementara: **UJI WAJIB baca lewat `susun()`**,
     karena itu yang mewakili apa yang dilihat Jev di jalur peta.
```

## 4. PELAJARAN (memory)

```
🚨 Dua "indeks baris" di proyek ini berbeda panjang (mentah vs susun).
   JANGAN mencampur: `peta3.susun()['baris']` ≠ `teks.split('\n')`.
   Uji yang mencari baris lewat ISI wajib memakai daftar yang SAMA dengan
   yang dipakai jalur produksi yang diukur.
🚨 "susun()" mengembalikan DICT {'baris','kand','gabung','buang','awal','akhir'},
   BUKAN list. Wulan salah pakai di percobaan pertama (KeyError: 0).
```

## 5. URUTAN

```
① ✅ selidiki c04 → SALAH DAFTAR (dokumen ini)
② ✅ tutup penyelidikan (putusan Bos)
③ ⬜ #2 Pass-1 stitch: SATUKAN cara baca naskah
   → pilih: peta3 pakai `_pecah_blok` (blok) ATAU tetap dua jalur + batas tegas
   → MENUNGGU putusan Bos (tidak dikerjakan sendiri)
```
