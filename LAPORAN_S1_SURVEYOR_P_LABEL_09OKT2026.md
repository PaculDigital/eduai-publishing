<!-- LAPORAN (RIWAYAT) — bukan SOT status -->
# 📐 LAPORAN S1 — SURVEYOR KELUARKAN `p` PER LABEL

> **Perintah Bos:** pilih **B** (09 Okt 2026) dari 4 opsi urutan kerja.
> **Dasar:** `RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md` §3 **S1**.
> **Berkas diubah:** `peta3_jev.py` (+`'p'` di keluaran `petakan()`).
> **Sasaran:** hakim hanya periksa kandidat **RAGU** ⇒ hemat biaya.

---

## 1. 🎁 TEMUAN BESAR — S1 **NOL BIAYA TAMBAHAN**

Wulan periksa dulu (aturan: cari yang sudah ada). Hasilnya:

```
Jev SUDAH mengirim confidence di SETIAP balasan:
   {"c0": {"type":"choice", "choice":"subbab",
           "probabilities": {...}, "confidence": 1.0}}      ← SUDAH ADA!

Tapi `petakan()` HANYA mengambil `choice` → `confidence` DIBUANG.
```

**Bukti terukur (2 panggilan uji nyata):**
```
c0 'L000620| 1.3. Tujuan Penelitian'  → choice='subbab'   confidence=1,00  YAKIN
c1 'maka penulis menyimpulkan'        → choice='paragraf' confidence=0,40  RAGU
```

⇒ **S1 TIDAK menambah panggilan Jev sama sekali.** Cukup **mengambil** angka
yang sudah dikirim. Rancangan §3 mengira butuh kerja baru — **ternyata tidak.**

---

## 2. APA YANG DIPASANG

| # | Perubahan di `peta3_jev.py` |
|---|---|
| 1 | wadah `conf = {i: [] for i, _t in kand}` (sejajar `semua`) |
| 2 | saat mengumpulkan jawaban: simpan `jw_i.get('confidence')` bila `int/float` |
| 3 | hitung `p_label[i] = round(sum(cs)/len(cs), 3)` — **rata semua putaran** |
| 4 | keluaran `petakan()` menambah kunci **`'p'`** |

**Sumber `p` (pagar S2):** langsung **confidence Jev** — **bukan** kesepakatan
antar-putaran (itu terbukti **SELALU 1,00**, tak punya daya pisah — hasil U4).

---

## 3. HASIL UJI NYATA (jalur resmi `peta3_jev.petakan`, putaran=1)

### 3a. `p` terisi penuh & punya daya pisah
```
ASIH fid=81 (9 dtk):  kandidat 491 · p terisi 491 (100%)

   label      n     p: min   rata   maks
   bab        5     0,97    0,98   1,00   ← Jev YAKIN
   subbab   132     0,29    0,91   1,00   ← yakin
   paragraf 169     0,28    0,59   0,89   ← ragu (batas paragraf memang samar)
   biasa    185     0,15    0,79   0,99
```

### 3b. ⚠️ TEMUAN PENTING — periksa **JUDUL saja**, bukan semua baris
```
Kalau SEMUA baris dihitung: p<0,85 = 259/491 (53%) ⇒ BUKAN penghematan (senada U4b)

Tapi hakim hanya memeriksa JUDUL (bab+subbab):

NASKAH       judul   ragu(p<0,85)     ambang 0,50   ambang 0,70   ambang 0,90
ASIH           140       27 (19%)          5            11            40
WULANDARI       77       47 (61%)         19            36            56
```

### 3c. ⭐ BUKTI DAYA TANGKAP — judul paling ragu memang baris BERMASALAH
```
ASIH:
   p=0,25  'Menurut Lumpkin & Dess (1996) dalam (Ramadanti e'   ← KALIMAT ✅
   p=0,29  'Tabel 4.3 memperlihatkan bahwa setiap item perny'   ← KALIMAT ✅
   p=0,35  'Digital Marketing (X1)'                             ← judul (ambang)
   p=0,48  'Gap research'                                       ← judul campur bahasa
WULANDARI:
   p=0,23  'UMKM.'                                ← potongan kalimat ✅
   p=0,29  '4. Threats (Ancaman)'                 ← judul, Jev ragu
   p=0,31  '(Mahardhani,2023)'                    ← SITASI ✅
   p=0,32  '4.1.4 Struktur Organisasi'            ← judul SAH tapi Jev ragu ⚠️
   p=0,33  '(Regina – Div AyuMeera)'              ← pecahan tabel ✅
```
⇒ `p` **memisahkan** yang bermasalah dari yang bersih — **persis bahan yang
dibutuhkan hakim.** (Catatan jujur: `'4.1.4 Struktur Organisasi'` = judul SAH
tapi p rendah ⇒ **p bukan vonis**, itu pekerjaan hakim.)

---

## 4. ✅ VERIFIKASI

```
GERBANG S1 (_gerbang_s1.py)      : 9 LULUS / 0 GAGAL · EXIT 0
  UJI BERGIGI (buang confidence) : 8 LULUS / 1 GAGAL · EXIT 1 ✅ TERTANGKAP
NOL REGRESI (fid=81):
   LABEL   {subbab:133, paragraf:169, biasa:184, bab:5}
   BAB ASLI = 5 ✅ (tetap)
   kunci keluaran: 'p' MASUK · sisanya tak berubah
```

---

## 5. 🔻 YANG **BELUM** (jujur)

1. **Ambang belum dikalibrasi** (U4b). Terukur: 0,85 menangkap 19% (Asih) &
   61% (Wulandari). Angka 0,50 terlihat lebih hemat — **tapi belum diputuskan**.
   Wajib: kalibrasi dari **naskah kacau** (fid=115), bukan Asih yang rapi.
2. **`p` belum dipakai siapa pun** — hakim (T①) belum disambung.
3. **Naskah Disertasi (fid=104) belum diuji** dengan S1.
4. **Putaran >1** belum diuji untuk `p` (uji ini putaran=1). Rancangan pakai
   rata semua putaran; belum dibuktikan lebih baik dari 1 putaran.
5. **`peta3_jev.py` belum masuk `app/`** — masih di root `/app/`.

---

## 6. BERKAS

- `peta3_jev.py` — **diubah** (S1) · backup `_arsip/pre-s1-p-label-09okt26/`
  (md5 sebelum: `5a01fcbac64b4d4f8dd07522c04a3231`)
- `_gerbang_s1.py` — gerbang S1 (9/0, bergigi)
- `RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md` §3 (S1) · §11 (U4b)
