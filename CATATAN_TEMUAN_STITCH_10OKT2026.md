<!-- 📝 SOT: CATATAN TEMUAN (RIWAYAT + angka terukur) — bukan penentu status. Pagar unggah ada di PAGAR_PINTU_NASKAH_10OKT2026.md -->
# 📝 CATATAN TEMUAN — STITCH SURVEYOR & BATAS MUTU FILE (10 Okt 2026)

> 🚩 **DIPERBARUI 10 Okt 2026:** angka di dokumen ini jadi BAHAN PASAL ③
> (`PAGAR_PINTU_NASKAH_10OKT2026.md` §2). Yang diminta Bos = kerjakan di HULU
> (pintu unggah), BUKAN tambal di peta.

> **Perintah Bos (verbatim):** *"Dah cukup, makin vanyak kandidat makin mahal saya
> bayar jev. Kalo masalah yang simple jnagan detail karena tidak bisa buat general
> naskah"*
> ⇒ **BERHENTI.** Semua perubahan KODE DIBATALKAN (dipulihkan ke versi asli).

---

## 1. STATUS AKHIR (terverifikasi)

```
app/konversi.py : 155a4ab5ddcd6697ca52977183894624  ✅ versi ASLI
peta3_jev.py    : 7e0cd4f7db4e94734f18f8604151c933  ✅ versi ASLI
gerbang jalan tol JEV : 30 LULUS / 0 GAGAL ✅
periksa_kode.sh       : LULUS ✅
```

Tidak ada perubahan produksi. Jejak uji ada di `_sketsa/jejak-stitch-10okt26/`.

---

## 2. YANG DIUKUR (angka nyata, berguna ke depan)

| Naskah | Baris | Kandidat | Sampah ≤2 kar | Median baris |
|---|---|---|---|---|
| fid=81 (Asih) | 1.874 | 491 (26%) | 655 | 37 kar |
| fid=115 (Wulandari PDF) | 8.755 | 8.555 (98%) | 5.623 (64%) | **1 kar** |
| fid=104 (Disertasi) | 25.055 | 12.302 (49%) | 12.916 (52%) | 15 kar |

**fid=115 rusak per-HURUF** (`D`,`i`,`n`,`a` = "Dina…"). **fid=104** tiap baris
dipisah baris kosong DAN barisnya hanya ~65 kar.

Dengan PASS-1 stitch (percobaan, sudah dibatalkan):
```
fid=115: 8.755 → 1.586 baris (kandidat 8.563→1.524, sampah →48) · 155 dtk
fid=81 : TIDAK berubah (kontrol) ✅
fid=104: 12.302 → 7.020 · 571 dtk → 64 dtk   (tetapi baris tetap terpotong)
```

---

## 3. AKAR MASALAH fid=104 (2 sebab, keduanya di KODE)

### Sebab ① — BATAS KANDIDAT TERLALU KECIL (`_KANDIDAT_MAKS_KAR = 60`)
```
2.249 baris (18%) panjangnya 61–90 karakter ⇒ TIDAK LOLOS kandidat
⇒ Jev TIDAK PERNAH ditanya untuk baris itu ⇒ tidak disambung
Contoh nyata (memang terpotong, harusnya disambung):
  [65] 'stunting yang dapat ditoleransi adalah 20% dari total keseluruhan'
  [72] 'tahun 2018, di Indonesia tercatat 7.8 juta dari 23 juta balita menderita'
Penalaran asli (08 Okt): "kalimat terbelah SELALU dua baris PENDEK" ⇒ benar
untuk naskah pecah-per-kata (115), SALAH untuk naskah ~65 kar/baris (104).
```

### Sebab ② — TITIK YANG MENUTUP SITASI dianggap AKHIR KALIMAT
```
'(Kemenkes RI, 2018b).' → KODE lihat titik ⇒ ambang NAIK ke 0,5
⇒ Jev jawab 0,44 (BENAR: harus disambung) ⇒ DIBUANG ❌
⇒ baris akademik tetap terpotong. Naskah akademik PENUH titik sitasi
   ((et al., 2018)., 2018)., ibid., dll.)
```
Obat ② sudah dicoba (`_akhir_sitasi()`, uji 11/12 tepat) tetapi **TIDAK dipakai**
karena keputusan Bos: **BERHENTI** (masalah simple jangan dibuat detail per-naskah).

---

## 4. PELAJARAN UMUM (berguna untuk naskah lain)

```
(U1) JE V TIDAK DETERMINISTIK — jumlah blok beda tipis tiap panggilan
     (19.691/19.715/19.722) tetapi KATA tetap 50.879 (NOL hilang, 3× dicek).
     ⇒ pagar "isi hilang" WAJIB membandingkan JUMLAH KATA (`split()`).
     ❌ 2 cara SALAH yang sudah terukur: `len(teks_blok)` (473 "hilang", palsu)
        dan `re.findall(r'\w+')` (680 "hilang", palsu — huruf per-huruf
        'D i n a' jadi 4 "kata", setelah bersatu jadi 1).
(U2) BARIS KOSONG beda arti tiap naskah (81: pemisah paragraf · 104: pemisah
     tiap baris) ⇒ JANGAN nebak dengan regex (dilarang Bos).
(U3) Jev TERBUKTI BISA menilai baris-kosong: 12.527/12.527 terjawab (60 dtk);
     zona abu 0,32–0,63 = 7 dari 8 MEMANG harus disambung ('namun'+'juga'=0,94).
(U4) `_rapikan_baris.py` (kode menebak via panjang + huruf besar) MENELAN JUDUL
     ('Metode Analisa Data' & 'Kesimpulan' HILANG). Gagal 3×. JANGAN dipakai.
(U5) PAGAR keselamatan BEKERJA: tiap kali hasil stitch tidak utuh, `_stitch_baris`
     kembali ke teks apa adanya ⇒ naskah normal (fid=81) tidak pernah rusak.
```

---

## 5. BIAYA JEV (aturan Bos, 10 Okt 2026)

```
"Makin banyak kandidat ⇒ makin mahal saya bayar Jev"
⇒ JAWABAN BUKAN "naikkan batas kandidat" (itu menambah biaya),
   melainkan **BERSIHKAN MUTU FILE** — kerjakan di HULU.
⇒ Masalah 104/115 = MUTU FILE USER (PDF rusak), BUKAN kekurangan Jev.
   Sudah tercatat: "MUTU FILE > KODE; ekstraktor kita sudah benar".
```

---

## 6. SISA (belum dikerjakan, sesuai keputusan BERHENTI)

```
⬜ MUTU FILE USER: naskah PDF pecah per-huruf / per-baris-kosong
   ⇒ arah yang benar = bersihkan saat UNGGAH (hulu), bukan tambal di peta
   ⇒ belum diputuskan Bos
⬜ fakta: peta3_jev.py belum masuk app/ (app/peta_halus_jev.py masih cara lama)
```
