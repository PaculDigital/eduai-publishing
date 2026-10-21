# UJI HAKIM + K5 + PEMETAAN PRODUKSI — LAPORAN LENGKAP (09 Okt 2026)

> Hasil pemasangan: **asersi gerbang → K5 → pemetaan produksi** (urutan vonis Bos).
> Naskah uji: `fid=115` (Wulandari-PDF, 8.755 baris, 74 kandidat judul).

---

## 1. YANG DIPASANG

| Berkas | Perubahan |
|---|---|
| `app/hakim_peta.py` | **`CRITERIA_K5`** (dikunci, tidak diubah dari yang tervalidasi) · **`AMBANG_SEPAKAT=0,60`** + **`AMBANG_CURIGA=0,30`** (tingkat MODUL, jangan di dalam fungsi) · **`_status_vonis()`** 3-zona · catat demosi ke `DEMOSI_CURIGA.json` |
| `app/_gerbang_jev_jalantol.py` | **+8 asersi** (E1–E5 criteria · F1–F4 K5 & pemetaan) ⇒ **30 LULUS / 0 GAGAL** |

**Pagar U4b DIPATUHI:** asersi **F4** memastikan `hakim_peta.py` **tidak memakai
`p` sebagai input keputusan** (`p_info` = info tampilan saja; nol `AMBANG_P`).

---

## 2. HASIL UJI 3 PUTARAN PENUH (fid=115)

### Jumlah per putaran
| Putaran | sepakat | ragu | curiga |
|---|---|---|---|
| 1 | 23 | 6 | 45 |
| 2 | 20 | 6 | 45 |
| 3 | 19 | 8 | 43 |

### 🎯 Ukuran yang LEBIH PENTING — kestabilan PER-KANDIDAT
```
total kandidat       : 77 (gabungan putaran)
TETAP (3× sama)      : 73  (94%)  ✅
GOYANG (beda-beda)   :  4  ( 5%)

⇒ Jumlah bergeser ±4/putaran, TAPI 94% kandidat TEGUH.
  Bergeser-nya jumlah = efek samping 4 kandidat itu, bukan gejolak menyeluruh.
```

### 4 yang bergoyang (semua)
| Baris | Status 3 putaran | Teks | Skor | Sifat |
|---|---|---|---|---|
| L000658 | ragu→curiga→curiga | `SWOT (Strengths, Weaknesses, …` | p 0,81 | pecahan, bukan judul |
| L007929 | sepakat→ragu→ragu | `3.1 Jenis dan Waktu Penelitian` | p 0,96 | **JUDUL ASLI** ⚠️ |
| L008449 | curiga→curiga→ragu | `2. Informan (Regina – Div. AyuMeera)` | p 0,87 | butir/tabel |
| L008621 | curiga→curiga→ragu | `AyuMeera)` | p 0,79 | pecahan |

**Pembacaan jujur:**
- 3 dari 4 = **memang bukan judul** (pecahan/butir) → goyang di antara `curiga`↔`ragu`
  = **tidak berbahaya** (keduanya bukan 'sepakat').
- **1 berbahaya: L007929 `3.1 Jenis dan Waktu Penelitian`** — **judul asli** yang
  2× jatuh ke `ragu` (Jev tidak yakin). ⇒ **ini bukan cacat ambang**, ini Jev
  ragu pada baris yang seharusnya jelas (baris terlalu panjang? 33 karakter).
  **Masuk daftar perbaikan berikutnya, bukan ditambal sekarang.**

---

## 3. CONTOH STATUS (1 putaran, fid=115)

```
SEPAKAT (benar)  : 1.1 LATAR BELAKANG · 2.1.2 Fungsi dan Tujuan Analisis SWOT
                   3.1.1 Jenis Penelitian · 2.3 Kerangka Berfikir · 3.2.2 Subyek Penelitian
CURIGA (benar)   : (Khoironi, 2023) · 0,5% tingkat engagement. · Rismawati BR.
                   (David, 2010) dalam (Andika, 2020). · 6 Sidang Skripsi
RAGU (benar)     : Berfikir · 2020). · Kategori Hasil Kutipan Informan
                   ⇒ zona ragu menangkap PECAHAN dengan tepat
```

---

## 4. VERIFIKASI

```
gerbang jalan tol          : 30 LULUS / 0 GAGAL
uji bergigi (suntik)       : F2 ⇒ gagal saat benar<10 · pagar lama ⇒ 5 gagal
scripts/periksa_kode.sh    : ✅ LULUS
kestabilan per-kandidat    : 94% tetap
pagar U4b                  : ✅ dijaga (asersi F4)
```

---

## 5. YANG BELUM — JUJUR

1. **Ambang 0,60/0,30 = NILAI AWAL.** Dari 74 kandidat nyata + 18 uji sebelumnya.
   Bos: *"perlakukan sebagai nilai awal + catat semua vonis di produksi; review
   zona ragu berkala."* ⇒ `DEMOSI_CURIGA.json` = alat audit itu.
2. **L007929 `3.1 Jenis dan Waktu Penelitian`** — judul asli yang 2× diragukan
   (Jev ragu). Belum diobati.
3. Uji baru di **1 naskah** (fid=115) untuk hakim penuh. Naskah ke-3 (Disertasi)
   baru diuji untuk kalimat criteria (12 kasus), belum seluruh peta.
4. Belum masuk ke `section_state` (kolom `mulai`/`akhir` masih bug lama).
5. Belum jadi gerbang otomatis untuk **realitas produksi** (baru berkas hasil uji).

---

## 6. URUTAN

1. ✅ asersi gerbang (E1–E5, F1–F4) — 30/0
2. ✅ **K5 dipasang** ke `hakim_peta` (dikunci)
3. ✅ **pemetaan produksi** 0,60/0,30 + catat demosi
4. ⬜ **② Pass-1 stitch + ③④** — ukur recall kandidat (uji L008039)
5. ⬜ **⑤ pensiunkan ambang-`p`**
