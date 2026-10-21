<!-- LAPORAN (RIWAYAT) — bukan SOT status -->
# 📊 LAPORAN #4 (U4b) — KALIBRASI AMBANG: **HASILNYA MENOLAK ASUMSI RANCANGAN**

> ## 🔓 PUTUSAN BOS (09 Okt 2026) — **AMBANG DIBUBARKAN, BUKAN DISELESAIKAN**
> Verbatim: *"Masalah ambang ini tidak perlu DISELESAIKAN. Perlu DIBUBARKAN. …
> Ini bukan masalah kalibrasi; ini masalah **salah alat ukur**."*
>
> **⇒ Skema pengganti TANPA ambang (§7c rancangan):**
> - **curiga** ← kode deterministik `judul_curiga` v5c → **lapor ke manusia**
> - **ragu** ← vonis Hakim sendiri per-BAB (menilai barisnya langsung, bukan baca `p`)
> - **sepakat** ← sisanya
> - **`p`** → **HANYA info tampilan** (*"keyakinan surveyor: 0,20"*), ⛔ bukan input keputusan
>
> ⇒ Tidak ada ambang ⇒ tidak ada yang dikalibrasi ⇒ `p=0,20` pada judul asli
> **tidak bisa merusak apa pun**. Tujuan S1 **ditulis ulang**: `p` = data
> diagnostik/laporan, BUKAN alat hemat biaya.

> **Perintah Bos:** pilih **4** = U4b kalibrasi ambang (09 Okt 2026).
> **Dasar:** `RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md` §11 U4b:
> *"Ambang 0,85 terbukti salah tempat. Wajib: cari ambang dari sebaran conf
> di naskah KACAU (fid=115), bukan Asih yang rapi."*
>
> **HASIL:** kalibrasi **SUDAH DIKERJAKAN** — dan **menemukan bahwa ambang tunggal
> TIDAK BISA dipakai.** Rancangan §7a `p < 0,85 ⇒ periksa ulang` **DITOLAK DATA.**

---

## 1. BAHAN (semua SUDAH ADA, tidak bikin baru)

| Bahan | Berkas | Isi |
|---|---|---|
| Kunci jawaban | `HASIL_UKUNCI.json` | 75 baris fid=115: **24 asli · 51 palsu** + `conf` |
| `p` dari S1 | `peta3_jev.petakan(115)` | `p` per label (S1, baru dipasang) |
| Garis dasar | `HASIL_U5_BASELINE_115.json` | ~~75 sub-bab · 51 palsu (68%)~~ ⚠️ **DITANGGUHKAN** (kunci cacat — lihat §5b) |

---

## 2. ⚠️ TEMUAN KE-1: `conf` LAMA ≠ `p` S1 (60 dari 75 BEDA >0,05)

```
Baris       p_S1    conf_lama   selisih
L000406     0,95    0,23        TERBALIK
L000777     0,39    0,92        TERBALIK
L000509     0,25    0,99        TERBALIK
L000783     0,44    0,955       TERBALIK
⇒ BEDA >0,05 pada 60/75 baris (80%)
```

**SEBAB:** dua angka diambil pada **panggilan Jev yang BERBEDA**. Jev menjawab
beda untuk baris yang sama antar-panggilan.

⇒ **PELAJARAN:** kalibrasi **WAJIB dari `p` yang SAMA** yang nanti dipakai.
Angka `conf` lama (U-KUNCI) **TIDAK SAH** untuk mengkalibrasi `p` baru.

---

## 3. ✅ TEMUAN KE-2: `p` S1 STABIL (goyang kecil ⇒ LAYAK dipakai)

Uji 3 putaran, 25 baris ber-kunci:

```
simpangan rata = 0,076 · maks = 0,35 · >0,30 hanya 1 dari 25
Contoh stabil: L000002 (1,00/1,00/1,00) · L007947 (1,00/1,00/1,00)
```

⇒ **`p` bukan angka acak.** Bisa dipakai — **pertanyaannya: dipakai UNTUK APA.**

---

## 4. 🚨 TEMUAN KE-3 (TERBESAR): **`p` rendah ≠ "baris palsu"**

Kalibrasi **dari `p` S1 yang sah** (bukan conf lama):

```
AMBANG   dipanggil   TANGKAP palsu   ASLI KENA (boros)
0,70        32        24/48 (50%)        8/24
0,80        39        31/48 (65%)        8/24
0,85        45        34/48 (71%)       11/24
0,90        51        39/48 (81%)       12/24
```

⚠️ Terukur di ambang **0,90**: **12 dari 24 ASLI ikut dipanggil** (boros 50%).
Sementara di ambang **0,70**: hanya 50% palsu tertangkap.

### Akar: `p` rendah muncul di DUA arah

**a) Benar ragu pada sampah** ✅ (Jev tepat)
```
L000638  kunci=palsu  p=0,99  '2020).'                        ← potongan kalimat
L007947  kunci=palsu  p=1,00  'AyuMeera].'                    ← pecahan tabel
L000692  kunci=palsu  p=0,95  '(David, 2010) dalam (Andika 2020).'  ← sitasi
```
⚠️ Perhatikan: baris ini **justru `p` TINGGI** (Jev yakin **bukan** judul → label
`biasa`/`paragraf`). Jadi **`p` tinggi di sini = benar**, bukan salah.

**b) SALAH ragu pada JUDUL ASLI** ❌ (ini masalahnya)
```
L000509  kunci=asli   p=0,20  '2.1.1 Pengertian Analisis SWOT'   ← JUDUL NYATA!
L007911  kunci=asli   p=0,47  '2.3 Kerangka Berfikir'            ← JUDUL NYATA
L000380  kunci=asli   p=0,51  '1.2 Rumusan Masalah'              ← JUDUL NYATA
L000402  kunci=asli   p=0,59  '1.3 Tujuan Penelitian'            ← JUDUL NYATA
```

⇒ **`'2.1.1 Pengertian Analisis SWOT'` p=0,20** — padahal itu judul yang nyata,
lengkap dengan nomor bertingkat. Jev **ragu pada baris yang paling jelas**.

---

## 5. ✅ KESIMPULAN & KEPUTUSAN (bukan tambalan)

```
❌ Ambang 0,85 tunggal TIDAK BISA dipakai  ⇒ §7a rancangan DITOLAK DATA
❌ Bukan karena ambangnya salah angka
❌ Juga bukan karena `p` rusak (p stabil, rata 0,076)
✅ Sebabnya: `p` = "Jev tidak yakin", BUKAN "baris ini palsu"
   ⇒ Jev tidak yakin di DUA arah: benar-ragu (sampah) DAN salah-ragu (judul asli)
```

**⇒ `p` TIDAK BOLEH jadi gerbang pemanggil hakim.**

### Yang SAH dipakai:
| Kegunaan `p` | Sah? | Alasan |
|---|---|---|
| Pemicu periksa ulang pada `p` rendah **+ label judul** | ⚠️ **ragu** | 50% boros di 0,70; 50% boros-di-asli di 0,90 |
| Penanda "baris ini perlu perhatian" **untuk dilaporkan** | ✅ **SAH** | pagar H1: hakim **LAPOR, jangan BLOKIR** |
| Gerbang mutlak (p<X ⇒ buang/ubah) | ❌ **HARAM** | akan memotong judul asli (`2.1.1` p=0,20) |

**⇒ `p` = bahan LAPORAN, bukan saklar.** Persis pagar yang sudah tertulis di
rancangan §5: *"Peran: PEER REVIEWER · Pagar: Lapor, tidak blokir"*.

---

## 5b. ✅ VERIFIKASI KUNCI JAWABAN (Langkah 1, atas perintah Bos)

### Hasil
```
24 kunci "ASLI"  → SEMUA BENAR ✅ (semua judul nyata: '1.2 Rumusan Masalah',
                    '2.1.1 Pengertian Analisis SWOT', '4.3.2.1 Faktor Internal', …)
51 kunci "PALSU" → 18 di antaranya MEMANG JUDUL ASLI ❌ (KUNCI SALAH)
```

### ⚠️ KOREKSI KLAIM (Bos 09 Okt): 18 itu **CAMPUR** — pisah jadi 2 kelompok jujur

Klaim awal Wulan *"18 MEMANG JUDUL ASLI"* **SALAH** — anotasinya sendiri bilang
sebagian **bukan judul**. Fragmen/butir yang dilabeli `subbab` memang **palsu** ⇒
**kunci BENAR** untuk kelompok itu. Ini dosa kunci lama: **angka pasti padahal
definisi goyang.**

**Kelompok (a) — KUNCI BENAR (7)** — Jev memang salah label; fragmen/butir:
```
L003486  '5 Adyatma'                        ← pecahan TABEL (fragmen)
L005826  'PENGARUH'                         ← pecahan TABEL (fragmen)
L007914  'Berfikir'                         ← pecahan JUDUL (fragmen)
L008434  '- Pengaruh peran media sosial'    ← BUTIR daftar
L008448  '- Perubahan tren hijab anti meleyot'  ← BUTIR daftar
L008473  '- Zaman yang serba media sosial'  ← BUTIR daftar
L008523  '- Pengaruh peran media'           ← BUTIR daftar
```
⇒ Fragmen & butir **BUKAN judul** ⇒ kunci `palsu` **BENAR**. (Jev yang salah, bukan kunci.)

**Kelompok (b) — KUNCI SALAH (11)** — judul asli tapi dikunci palsu:
```
L000877  '4. Threats (Ancaman)'                     ← JUDUL (komponen SWOT)
L007997  '6 Sidang Skripsi'                         ← JUDUL (daftar kegiatan)
L008039  '2. Wawancara'                             ← JUDUL (metode)
L008050  '3. Tinjauan Literatur'                    ← JUDUL (metode)
L008426  '1. Informan (Ulan – Pengelola AyuMeera)'  ← JUDUL (daftar informan)
L008449  '2. Informan (Regina – Div. AyuMeera)'     ← JUDUL
L008468  '3. Informan (Anie – Div. Chemical)'       ← JUDUL
L008480  'Hijab yang menjadi trend'                 ← JUDUL (butir ber-judul)
L008485  '4. Informan (April – Konsumen)'           ← JUDUL
L008622  'Kategori Hasil Kutipan Informan'          ← JUDUL (header tabel)
L008709  'Kategori Hasil Kutipan Informan'          ← JUDUL (header tabel)
```
⚠️ **+ baris HILANG** dari tabel (51 palsu → 48 saat diuji) ⇒ indeks kunci
TIDAK LENGKAP. **+ definisi "butir ber-judul" vs "butir" belum tegas** ⇒
kelompok (b) masih mengandung 1 baris yang **batasnya kabur** (`L008480`).

**⇒ KESIMPULAN: `HASIL_UKUNCI.json` CACAT** (≥11 salah + baris hilang + definisi
goyang). Karena `p` kini **bukan** input keputusan (§7c), cacat ini **tidak
merusak produksi** — tapi **semua angka kalibrasi §4 TIDAK SAH** dan **X = "51
palsu (68%)" DITANGGUHKAN** (jangan dikutip lagi).

---

## 5c. ✅ VALIDASI SINYAL DETERMINISTIK `judul_curiga` (Langkah 3)

Diuji di **naskah kacau** fid=115 (jalur resmi):

```
50 baris tertandai — SEMUA alasan 'awal-sitasi'
   L000550 '(Khoironi, 2023)'          ← sitasi
   L000546 '(Kuadran I)'               ← pecahan tabel
   L008645 '(Regina – Div AyuMeera)'   ← pecahan tabel
   L000286 '(Susilowati, 2021)Akses…'  ← sitasi menempel kalimat

SALAH TUDUH = 0 dari 50  ✅ (0 kunci 'asli' yang dikenai)
presisi 100% · biaya Rp 0 (kode murni)
recall 8/51 (≈16%) — ⚠️ **ANGKA SEMENTARA**: penyebutnya (51) ikut kunci yang CACAT
   ⇒ recall sejati belum bisa dihitung sampai kunci dibangun ulang.
   Arah tetap: SENGAJA presisi > recall (hakim = reviewer, jangan salah tuduh).
```

**⚠️ Yang SAH dari uji ini:** `SALAH TUDUH = 0` (kelompok (a) & (b) dua-duanya
tidak dikenai) — itu klaim **kokoh** karena 24 kunci "asli" sudah terverifikasi
**semua benar** dan tak ada satu pun yang tertandai.

⇒ **Sinyal `judul_curiga` SAH dipakai sebagai jalur "curiga".** (Recall ditunda.)

---

## 5d. 🧠 PENGAKUAN METODOLOGI (untuk tim)

**TEMUAN #1 = pelajaran metodologi BESAR:**
```
60 dari 75 baris: `conf` lama ≠ `p` S1 (beda panggilan Jev = beda angka)
⇒ KALIBRASI WAJIB dari `p` yang SAMA yang dipakai PRODUKSI.
⇒ Ini gema pelajaran lama: JANGAN campur angka dari run berbeda.
   (Pelajaran yang sama pernah muncul di fid=112 — lihat memori "angka WAJIB labeli RUN".)
```
Konsekuensi praktis: **setiap angka `p` yang dilaporkan WAJIB menyebut
run/kapan diambil**, kalau tidak, angka itu menyesatkan.

---

## 6. 🔻 YANG BELUM (jujur)

0. 🔴 **X (basis ukur) DITANGGUHKAN.** Jangan kutip *"51 palsu (68%)"* lagi.
   **X baru dihitung ULANG** setelah kunci dibangun ulang **dari run resmi saat
   ini** + **verifikasi manusia** — persis rencana 5 langkah rancangan v3.
   (Alasan: kunci lama cacat ≥11 baris salah · baris hilang · definisi "butir
   vs judul" goyang ⇒ X lama tidak bisa dipercaya.)
1. **Kunci jawaban `HASIL_UKUNCI.json` WAJIB dibangun ulang + diverifikasi manusia.**
   Bukti: kelompok (a) 7 kunci BENAR · kelompok (b) ≥11 kunci SALAH · baris
   hilang · definisi "butir ber-judul" belum tegas (`L008480`).
2. **`p` untuk naskah lain belum diuji** (Asih fid=81, Disertasi fid=104).
3. **Ambang pengganti belum ditetapkan** — menunggu keputusan Bos jenis gerbangnya.
4. **Uji ini 1 naskah kacau saja** (fid=115). Perlu ≥2 naskah kacau.

---

## 7. BERKAS

- `HASIL_UKUNCI.json` (bahan) · `HASIL_U5_BASELINE_115.json` · `HASIL_U4_KALIBRASI.json`
- `peta3_jev.py` (S1 — sumber `p`) · `RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md` §7a/§11 U4b
- **Catatan:** `HASIL_UKUNCI.json` belum ikut `sot.py` (perlu didaftarkan)
