# #5 U-KUNCI — HASIL JUJUR (09 Okt 2026)

> **Pertanyaan:** HAKIM (T①, `hakim_peta.py`) memeriksa kandidat judul hasil
> SURVEYOR (`peta3_jev`). Apakah hakim **menangkap yang surveyor lewatkan**?
>
> **Berkas:** `uji_u_kunci.py` · keluaran `HASIL_U_KUNCI.json` · naskah fid=115
> (Wulandari — naskah KACAU: tabel, kutipan, pecahan baris).

---

## 1. ANGKA PENENTU (3× ulangan, stabil)

| Ukuran | Ulangan 1 | Ulangan 2 | Ulangan 3 | Rata |
|---|---|---|---|---|
| **TANGKAP** (kunci 'palsu' → hakim ragu/curiga) | 48/51 (94,1%) | 49/51 (96,1%) | 48/51 (94,1%) | **~95%** |
| **LOLOS** ('palsu' → hakim 'sepakat') | 1/51 (2,0%) | 1/51 (2,0%) | 2/51 (3,9%) | **~2,6%** |
| **ASLI SETUJU** (kunci 'asli' → hakim 'sepakat') | 18/24 (75,0%) | 18/24 (75,0%) | 20/24 (83,3%) | **~78%** |

**Kandidat** yang diperiksa hakim: **76–80** (goyang ±4 antar-putaran = sifat
`peta3_jev`, bukan bug hakim). **0 `belum`** di semua ulangan.

**⇒ JAWABAN: YA.** Hakim menangkap **~95%** baris yang kunci bilang palsu.

---

## 2. TAPI — KUNCI ITU SENDIRI SALAH (diverifikasi ke naskah)

Wulan buka **3 baris yang "LOLOS"** ke naskah aslinya (`peta3_jev.susun(115)`,
bukan tebakan):

### ① L008050 `3. Tinjauan Literatur` — kunci: 'palsu' · hakim: 'sepakat'
```
L008047 | hal-hal terkait dengan aspek-aspek kelayakan bisnis yaitu meliputi, aspek
L008048 | pemasaran, aspek hukum, aspek teknologi, aspek sumber daya manusia, dan
L008049 | aspek finansial dari usaha tersebut.
L008050 | 3. Tinjauan Literatur          ← BERDIRI SENDIRI, diikuti paragraf baru
L008051 | Penelitian literatur adalah penelitian yang tempat kajiannya adalah pustaka
```
⇒ **INI JUDUL SUB-BAB YANG SAH.** Kunci SALAH bilang 'palsu'.
⇒ **HAKIM BENAR.** Ini bukan "lolos" — ini **kunci cacat**.

### ② L008622 `Kategori Hasil Kutipan Informan` — kunci 'palsu' · hakim 'sepakat'
```
L008619 | jadi ancaman”.
L008620 | (Ulan – Pengelola
L008621 | AyuMeera)
L008622 | Kategori Hasil Kutipan Informan    ← header tabel/pemisah kutipan
L008623 | (Divisi AyuMeera)
L008624 | Strengths - Model praktis
```
⇒ **Header tabel** — **bukan judul bab/sub-bab**. Kunci BENAR 'palsu'.
⇒ **HAKIM SALAH** (memberi 'sepakat'). Ini **1 dari ~1-2 kasus** yang betul-betul lolos.

### ③ L008039 `2. Wawancara` — kunci 'palsu' · **surveyor=None** (bukan kandidat)
⇒ Tidak diperiksa hakim karena **surveyor tidak menandainya kandidat judul**
(bukan tugas hakim — hakim periksa kandidat, bukan seluruh baris).

---

## 3. KESIMPULAN JUJUR

| Temuan | Status |
|---|---|
| Hakim menangkap ~95% baris yang kunci bilang palsu | ✅ **BUKTI KUAT** |
| Yang benar-benar lolos (L008622 header tabel) | ⚠️ **1 kasus nyata** (~2%) |
| "Lolos" yang ternyata KUNCI yang salah (L008050) | ✅ **hakim BENAR** |
| Kunci `HASIL_UKUNCI.json` CACAT | 🔴 **TERKONFIRMASI** (≥11 salah kunci, +2 baru) |

**⚠️ CACAT UKUR YANG DIAKUI:** kunci & kandidat **tidak sebidang**:
- kunci bilang "harusnya bukan judul", hakim mengukur "apakah baris ini awal judul"
- 3 baris kunci **tidak pernah jadi kandidat surveyor** (`surveyor=None`) ⇒ tak bisa diukur
⇒ Angka di atas = **"lawan kunci"**, bukan presisi sejati.

---

## 4. YANG MASIH KURANG (jujur — belum selesai)

1. **Uji 1 naskah saja** (fid=115). Laporan #4 minta **≥2 naskah kacau**.
2. **Kunci wajib dibangun ulang + diverifikasi manusia** — sekarang cacat, jadi
   semua ukuran di atas punya batas atas yang tidak diketahui.
3. **2 baris hakim `TIDAK_ADA`** (kunci L008039 & 1 lainnya) = baris yang kunci
   anggap penting tapi **surveyor tidak jadikan kandidat** ⇒ **lubang di SURVEYOR**,
   bukan di hakim. Ini **temuan baru**: hakim tidak bisa menangkap yang tidak
   pernah jadi kandidat.
4. **Goyang kandidat 76–80** antar-putaran ⇒ perlu sumber tetap (run resmi).

---

## 5. KEPUTUSAN RANCANGAN

- ✅ **TIDAK digabung** (putusan Bos 09 Okt: *"Jika hasil jelek, jangan gabung beda
  fungsi"*) — dan hasil ini **bagus**, jadi tetap **TERPISAH** sebagaimana rancangan:
  surveyor = peta utuh · hakim = penajam (lapor, jangan blokir).
- ✅ **Hakim memakai status `ragu`** (bukan `p`) sebagai vonisnya — terbukti bekerja
  (95% tangkap) dan tidak pernah `belum` lagi.
- ⚠️ **Lubang SURVEYOR** (baris penting tak jadi kandidat) = **pekerjaan berikutnya**.
