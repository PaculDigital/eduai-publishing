# VALIDASI SILANG K5 + PEMETAAN PRODUKSI (09 Okt 2026)

> **Vonis Bos:** *"Satu putaran validasi silang di naskah ketiga, lalu K5 layak
> dipasang."* · *"Definisikan pemetaan produksi. 0,5 di laporan ini ambang
> pengukuran. Sebelum dipasang, perlu spesifikasi: skor noul → status
> sepakat/ragu/curiga yang bagaimana?"*

---

## 1. ✅ VALIDASI SILANG — K5 DIKUNCI, NASKAH KETIGA (Disertasi-104)

**K5 TIDAK DIUBAH SAMA SEKALI.** Naskah: `DISERTASI-S3-unhas-kesehatan-stunting.docx`
(415.284 karakter, 26.065 baris) — **belum pernah dipakai menyetel K5**.

| Ukuran | Hasil (3× ulangan) |
|---|---|
| **Total** | **12/12 (100%)** — 3× berturut |
| **POSITIF (judul)** | **5/5** ✅ ← cabang `true` yang sebelumnya nyaris tak teruji |
| **NEGATIF (butir/tabel)** | **7/7** ✅ |

**Pemisahan BERSIH — tidak ada yang mepet ambang:**
```
judul  : 0,85  0,89  0,89  0,74  0,75     ← POSITIF
bukan  : 0,13  0,15  0,14  0,08  0,06  0,07  0,08   ← NEGATIF
celah  : 0,75 vs 0,15 = jurang lebar, bukan garis tipis
```

**Judul licin yang BERHASIL (yang Bos minta ditambah):**
```
P1 'Patofisiologi Stunting'   0,85  (tanpa nomor, garis akhir hilang)
P2 'Epidemilogi Stunting'     0,89  (nomor polos + nama topik)
P3 'Dampak stunting'          0,89  (huruf kecil, nomor polos)
P4 '1. Manfaat ilmiah'        0,74  (butir manfaat — bentuk NAMA TOPIK)
P5 '3. Manfaat institusi'     0,75  (butir manfaat — nama topik)
```
⇒ P4/P5 menarik: bentuknya "butir bernomor" seperti `2. Wawancara` (yang dulu
gagal), tapi **K5 benar** — karena isinya **nama topik** (ilmiah/praktis/
institusi), bukan **nama kegiatan**. ⇒ **Pembeda K5 bekerja di naskah baru.**

**Yang DITOLAK benar:**
```
N1-N3 pertanyaan penelitian ('1. Bagaimana pola spasial …')  → 0,13-0,15
N4-N5 daftar lampiran ('1. Surat Persetujuan Etik')          → 0,06-0,08
N6-N7 angka tahun ('2020', '2000')                            → 0,07-0,08
```

---

## 2. ✅ PEMETAAN PRODUKSI — skor noul → status hakim

**⚠️ PENTING — INI BUKAN GERBANG-`p`.** Pagar Bos dipatuhi: `p` pada **peta/label**
tetap **display-only**. Yang dipetakan di sini = **vonis HAKIM** (`hakim_peta`,
T①), ranah yang Bos nyatakan **sah diputuskan** — hakim memang pekerjaannya
memvonis kandidat judul.

### Aturan pemetaan (diusulkan)

```
noul ≥ 0,60                     ⇒ 'sepakat'  ← hakim SETUJU ini kepala bagian
0,30 ≤ noul < 0,60              ⇒ 'ragu'     ← hakim tidak yakin → tanya manusia
noul < 0,30                     ⇒ 'curiga'   ← hakim MENOLAK kandidat ini
```

### Dasar angka (bukan tebakan — dari 3 naskah)

| Zona | Data terukur | Sumber |
|---|---|---|
| **≥ 0,60** | judul sah: **0,63–0,91** (3 naskah) | kandidat + kasus batas |
| **0,30–0,60** | hanya `Kategori Hasil Kutipan Informan` 0,44–0,51 | 1 baris ambigu |
| **< 0,30** | bukan judul: **0,02–0,28** (kecuali 1) | 7 kasus batas |

**Mengapa 0,60 (bukan 0,50 atau 0,80):**
```
· Terukur: POSITIF terendah = 0,63 · NEGATIF tertinggi (bukan-kasus-batas) = 0,28
· 0,60 duduk di celah itu (0,28 ← → 0,63) — tidak memotong data
· 0,80 (aturan LAMA) TERUKUR SALAH: rata-rata label 0,839 ⇒ menangkap 46% saja
  (LAPORAN_4_U4b). 0,80 menolak judul asli yang sah (0,63-0,79) — GAGAL.
```

**Zona 0,30–0,60 = ZONA KERJA HAKIM.** Data nyata menunjukkan hanya 1 baris di
zona ini (`Kategori Hasil Kutipan Informan` = header tabel, memang ambigu).
Justru **di situ hakim berguna**: ia berkata "Wulan tidak tahu" — bukan menebak.

### Sifat (bukan sekadar 2–3 ambang)
```
· 'sepakat' = diteruskan apa adanya (kandidat KEPALA BAGIAN dari surveyor)
· 'curiga'  = ditandai untuk dibuang/dikoreksi, TIDAK memblokir (pagar H1)
· 'ragu'    = diteruskan + ditandai agar manusia memeriksa
· TIDAK ADA zona 'tidak_jelas' terpisah — 'ragu' sudah memainkan peran itu
```

⚠️ **Catatan jujur:** angka ini dari **18 kandidat uji** (12 kasus batas + 6
kandidat nyata) + 2 naskah. **Belum** dari seluruh naskah. Kalau nanti ada
kandidat sah bernilai 0,55, aturan ini masih perlu disetel.

---

## 3. YANG BELUM (jujur)

- ❌ K5 **belum dipasang** ke `peta3_jev`/`hakim_peta` (menunggu ACC pemetaan).
- ❌ Pemetaan produksi **belum diuji** lewat `hakim_peta.periksa_peta()`.
- ⚠️ 3 naskah (Asih · Wulandari · Disertasi) — ketiganya **skripsi/tesis/disertasi
  kesehatan-manajemen**; naskah **artikel jurnal** belum diuji.
- ❌ Belum jadi gerbang otomatis (asersi: validasi-silang ≥ 10/12).

---

## 4. URUTAN

1. ✅ ① criteria — pagar + kalimat K5 tervalidasi silang (dokumen ini)
2. ⬜ Asersi gerbang validasi-silang (K5 di naskah ke-3 ≥ 10/12)
3. ⬜ **② Pass-1 stitch + ③④** — ukur recall kandidat
4. ⬜ **⑤ pensiunkan ambang-`p`**
