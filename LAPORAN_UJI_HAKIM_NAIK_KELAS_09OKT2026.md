<!-- LAPORAN (RIWAYAT) — SOT: bukan sumber status. Status ada di SOT.md §SESI TERAKHIR -->
# 📊 LAPORAN UJI — HAKIM JEV NAIK KELAS (U1–U5, 09 Okt 2026)

> Perintah Bos: *"Saya mau kamu upgrade dulu jev hakim agar setara jev surveyor"* → **"Ok mulai"**.
> Sifat: **jalur UJI saja. NOL baris kode produksi diubah.**
> Backup: `_arsip/pre-hakim-naik-09okt26/` (satpam.py · peta3_jev.py md5 `5a01fcba…`).

---

## RINGKASAN SATU LAYAR

| Uji | Hasil | Putusan |
|---|---|---|
| **U5** baseline X | 75 sub-bab · **51 PALSU (68%)** · 24 ASLI · BAB 4/4 BENAR | metrik X→Y punya titik mula |
| **U4** kalibrasi p | kesepakatan antar-putaran **selalu 1,00** · conf Jev 0,36–0,99 (rata **0,839**) | **p = confidence Jev** (bukan kesepakatan) |
| **U1** adversarial | **6/6 BENAR** | ⚠️ menguji JEV, **belum** HAKIM |
| **U2** biaya | per-BAB **1 panggilan/1,01 dtk** · per-sub-bab 17–25 panggilan | ✅ per-BAB layak · ❌ bertingkat GAGAL |
| **U-KUNCI** | ⛔ **BELUM DIKERJAKAN** | ini penentu sesungguhnya |

---

## U5 — BASELINE SUB-BAB PALSU (fid=115, jalur RESMI)

### Rekonsiliasi angka (nit Bos)
| Angka beredar | Asal | Status |
|---|---|---|
| "89 dari 109 palsu" | catatan 09 Okt — **fid=112** (file buatan Wulan) | ❌ INVALID |
| "38+11 dari 108" | fid=112 juga | ❌ INVALID |
| **75 sub-bab** | **fid=115** jalur resmi | ✅ SAH |

Bukti tak sah: catatan sendiri mengaku (baris 155) — *"fid 112 & 113 = file buatan
Wulan (salah) · 114 & 115 = jalur resmi (benar)"*.

### Hasil hitung ulang (jalur resmi)
```
baris total : 8.755      kandidat : 8.555
gabung      : 4  → BAB I (0) · BAB II (471) · BAB III (7927) · BAB VI (8141)
sistematika : [451, 454, 459, 463, 468]
label bab   : 2 → [459, 468] — KEDUANYA sistematika
label subbab: 75         paragraf : 92 · goyang : 0
⇒ BAB ASLI  = 4 ✅          ⇒ SUB-BAB PALSU = 51 dari 75 (68%)
```

### Pengelompokan palsu (verifikasi ke sumber, baris-per-baris)
| Kelompok | Jml | Contoh |
|---|---|---|
| lanjutan/fragmen kalimat | 5 | `Tape AyuMeera berdasarkan analisis SWOT.` |
| ekor sitasi | 4 | `(David, 2010) dalam (Andika, 2020).` |
| jilid/cover | 3 | `5 Adyatma` · `PENGARUH` |
| tabel (langkah/informan) | 3 | `6 Sidang Skripsi` · `4 Mbak April Konsumen` |
| butir daftar bernomor | 7 | `2. Wawancara` · `3. Tinjauan Literatur` |
| daftar tanda "-" | 12 | `- Pengaruh peran media sosial` |
| fragmen kolom tabel | 9 | `AyuMeera)` ×4 · `(Regina – Div AyuMeera)` ×2 |
| judul kolom tabel | 4 | `Kategori Hasil Kutipan Informan` ×2 |

### 24 sub-bab ASLI (semua ketemu ✅)
`1.1` – `1.4` · `2.1` · `2.1.1` · `2.1.2` · `2.3` · `3.1` · `3.1.1` · `3.1.2` ·
`3.2` · `3.2.2` · `3.3` · `3.4.2` · `4.1` · `4.1.1` · `4.1.2` · `4.1.3` · `4.2` ·
`4.3.2.1` · `4.3.2.2` + 3 judul tanpa nomor (`Faktor – Faktor Penentu Strategi Bersaing`,
`Kekuatan (Strength)`).

⚠️ **CATATAN JUJUR:** klasifikasi ini Wulan kerjakan **dengan mata** (Wulan baca 75
baris + konteksnya). Wulan **gagal 2×** dulu: (1) classifier regex → 22 baris palsu
lolos ke "ASLI"; (2) susun manual dari ingatan → **jumlahnya 71, bukan 75** (4 baris
`AyuMeera)` terlewat). ⇒ **Angka 51/24 masih berpotensi meleset ±3.** Kalau angka ini
dipakai jadi metrik resmi, **Bos perlu memutuskan** apakah cukup, atau minta Wulan
bikin alat ukur yang lebih kokoh.

---

## U4 — KALIBRASI `p` (12 kandidat Asih × 3 putaran)

| Ukuran | Rata-rata |
|---|---|
| Kesepakatan antar-putaran | **1,000** (12/12 SEMPURNA) |
| Confidence Jev | **0,839** (rentang 0,36–0,96) |
| Selisih | −0,161 |

**Temuan:**
1. **Kesepakatan antar-putaran = 1,00 SELALU** ⇒ tak berguna jadi ambang (tanpa daya pisah).
2. **Confidence Jev punya daya tangkap** — L000038: konsisten bilang `paragraf`
   **tapi conf 0,36** ⇒ sinyal ragu ada di confidence, **bukan** di kesepakatan.
3. Jev **lebih hati-hati** (−0,16), bukan terlalu percaya diri.

**⇒ Koreksi rancangan v2:** `p` = **confidence Jev**, bukan kesepakatan antar-putaran.

⚠️ **Batas jujur:** diukur hanya di Asih (naskah RAPI, 11/12 benar). Belum diuji di
naskah KACAU (Wulandari-PDF).

---

## U1 — ADVERSARIAL (6 kasus NYATA, jendela baris)

| Kode | Kasus | Putusan | Conf |
|---|---|---|---|
| A1 | nomor halaman `"30"` jadi BAB | biasa | 0,8x |
| A2 | nomor halaman `"65"` jadi BAB | biasa | 0,83 |
| A3 | typo `"BAB VI"` | bab ✅ setia | 0,99 |
| A4 | butir `"f. Pelayanan pelanggan"` | biasa | 0,97 |
| A5 | `"PENDAHULUAN"` (judul bab) | bab | **0,43** ⚠️ |
| A6 | butir `"1. Apakah…"` | biasa | 0,81 |

**6/6 BENAR. TAPI — 3 alasan uji ini BELUM membuktikan hakim berguna:**
1. **Menguji JEV, bukan HAKIM** — jendela baris disusun Wulan sendiri (= konteks bagus).
2. **Justru memperkuat bahwa surveyor sudah cukup** — kalau Jev 6/6 dengan jendela
   baris (cara surveyor), apa lagi kerja hakim?
3. **A5 = blind spot tersembunyi** — jawaban benar tapi conf **0,43** (di bawah ambang
   ragu). Jev benar **dengan ragu**.

---

## U2 — BIAYA JEV (Asih, 131 sub-bab)

| Skenario | Panggilan | Waktu | Putusan |
|---|---|---|---|
| S0 sekarang | 1 | 0,82 dtk | baseline |
| **S1 per-BAB** | **1** | **1,01 dtk** | ✅ **LAYAK** |
| S2a per-sub-bab semua | 17 | ≈23 dtk | ⚠️ mahal |
| S2b bertingkat (p<0,85) | **25** | lebih lama | ❌ **LEBIH MAHAL** |

**MENGAPA BERTINGKAT GAGAL:** ragu (<0,85) = **46% kandidat**. Sebab rata-rata conf
Jev = **0,839** — persis di bawah ambang 0,85 ⇒ menangkap hampir separuh.

**KEPUTUSAN:** hakim naik kelas **sampai level BAB saja** (1 panggilan, gratis).
Putaran bertingkat **DIBUANG** dari rancangan.

---

## ⛔ YANG BELUM DIKERJAKAN (dan ini yang paling penting)

**UJI KUNCI: apakah HAKIM menangkap yang SURVEYOR lewatkan?**

Belum ada satu pun uji yang menjawab ini. Cara yang benar:
```
1. Ambil kasus ASLI dari fid=115 (bukan tiruan) — 51 sub-bab palsu yang SUDAH ada
2. Lihat: apakah surveyor (label) salah di situ?  ← biasanya YA (51 palsu)
3. Tanya HAKIM: apakah dia MENANDai bagian itu ragu/curiga?
4. Hitung: berapa dari 51 yang hakim TANGKAP?
   · Tertangkap banyak → hakim BERGUNA (metrik X→Y turun)
   · Tertangkap sedikit/nol → hakim TIDAK BERGUNA (aturan Bos: jangan pasang)
```

**Metrik keputusan (S3, kill-switch):** `sub-bab palsu turun dari 51 ke Y`.
`Y = 51` ⇒ **JANGAN PASANG**.

---

## KESIMPULAN SEMENTARA (jujur, belum final)

1. ✅ **Surveyor + confidence Jev sudah kuat** — 6/6 adversarial, conf berguna sebagai sinyal.
2. ❌ **Rancangan v2 salah di 2 tempat:** `p` (harus conf Jev) & putaran bertingkat (lebih mahal).
3. ❓ **Hakim BELUM terbukti berguna** — belum ada uji yang mengujinya.
4. ⚠️ **Kalau uji kunci gagal → JANGAN GABUNG** (aturan Bos: *"Jika hasil jelek,
   maka jangan gabung beda fungsi"*).

---

## BERKAS UJI
- `_sketsa/_u5_baseline_wulandari.py` → `HASIL_U5_BASELINE_115.json`
- `_sketsa/_u4_kalibrasi_p.py` → `HASIL_U4_KALIBRASI.json`
- `_sketsa/_u1_adversarial.py` → `HASIL_U1_ADVERSARIAL.json`
- `_sketsa/_u2_biaya.py`
- `_uji_adu_surveyor_hakim.py` (uji A awal, 09 Okt)
