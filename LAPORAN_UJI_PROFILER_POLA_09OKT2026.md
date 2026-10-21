<!-- LAPORAN (RIWAYAT) — SOT: bukan sumber status -->
# 📐 LAPORAN UJI — PROFILER POLA PENULISAN (murni kode, tanpa Jev)

> **Perintah Bos:** "Ok Mulai" (09 Okt 2026) → koding `pola_penulisan.py`.
> **Dasar:** RANCANGAN_PROFILER_POLA_09OKT2026.md (**v3**).
> **Prinsip terpasang:** AI menulis kata · kode menulis angka **dan pola**.
> **Status:** ✅ MODUL SELESAI · gerbang **36 LULUS / 0 GAGAL** · nol baris produksi diubah.
> **Riwayat angka:** versi awal laporan ini dicatat saat gerbang masih **26/0**. Setelah
> §6b–6e (campuran, judul_curiga, Disertasi) gerbang jadi **36/0**. Angka **36/0 = yang berlaku**.

---

## 1. APA YANG DIBANGUN

| Berkas | Isi |
|---|---|
| `app/pola_penulisan.py` | Modul profiler (~300 baris) — **nol panggilan Jev** (P1) |
| `app/_gerbang_pola.py` | Gerbang uji **36 LULUS / 0 GAGAL**, EXIT 0, **terbukti bergigi** |
| `_sketsa/_uji_pola.py` | Uji nyata di Asih (fid=81) + Wulandari (fid=115), jalur resmi |

**Jalan uji:** `docker exec -w /app eduai-app python3 _uji_pola.py`
**Jalan gerbang:** `docker exec -w /app eduai-app python3 app/_gerbang_pola.py`

---

## 2. HASIL UJI NYATA (jalur resmi, pagar `<w:tab>` = 0 ✅)

> ⚠️ **HIGIENE ANGKA (pelajaran fid=112):** setiap angka WAJIB dilabeli **run-nya**.
> Label Jev bisa **berbeda antar-run** (panggilan ulang = goyang 3% terukur). Karena itu:

| Run | Naskah | BAB | subbab | tidak_jelas | catatan |
|---|---|---|---|---|---|
| **A** (awal, §3–§4) | ASIH fid=81 | **5 ✅** | **130–138** * | 0,0% | label Jev run-1; subbab bergoyang antar-panggilan |
| **A** (awal, §3–§4) | WULANDARI fid=115 | **4 ✅** | 74 | 0,0% | — |
| **B** (§6d, verifikasi ulang) | ASIH fid=81 | **5 ✅** | **134** | 0,0% | panggilan ulang → angka bisa beda |
| **B** (§6d) | WULANDARI fid=115 | **4 ✅** | 74 | 0,0% | — |
| **B** (§6d) | DISERTASI fid=104 | **5 ✅** | **320** | 0,0% | — |

\* subbab ASIH tercatat 130 (§2 awal), 138 (§2 lainnya), 134 (§6d) ⇒ **variasi antar-run
label Jev**, bukan bug. **Yang STABIL & tidak goyang:** BAB (5/4/5) — karena dari `gabung`
(kode murni), bukan label Jev.

**Yang paling berharga — `nomor_terakhir` (nomor lanjutan dihitung MESIN):**
```
WULANDARI BAB I  : {'1': '1.5'}
WULANDARI BAB II : {'2': '2.4', '2.1': '2.1.3'}
WULANDARI BAB III: {'3': '3.4', '3.1': '3.1.3', '3.2': '3.2.3', '3.4': '3.4.3'}
WULANDARI BAB IV : {'4': '4.3', '4.1': '4.1.4', '4.3.2': '4.3.2.3'}   ← termasuk 3 tingkat
```
⇒ Persis permintaan Bos: **nomor ditetapkan mesin, bukan AI mengarang.**

---

## 3. AKAR MASALAH YANG DITEMUKAN & DIBETULKAN (semua TERUKUR)

### 🚨 A. Ambang panjang + cek titik-akhir → **DIBUANG** (2× salah)
```
TERUKUR: ASIH       → 491/491 baris TANPA titik akhir (100%)
         WULANDARI  → 8.554/8.555 baris TANPA titik  (100%)
⇒ cek "titik akhir" TIDAK BERGUNA SAMA SEKALI (baris ≠ kalimat)

TERUKUR: WULANDARI p50 panjang baris = 1 KARAKTER (PDF hancur!)
         < 10 kar: 69,1%     ⇒ ambang panjang APA PUN akan gagal di naskah PDF
         ASIH p50 = 139 kar  ⇒ naskah Word SEHAT
```
**Kesimpulan:** `tidak_jelas` **tetap ada** (itu FITUR), tapi **bukan** dari panjang/titik —
**hanya untuk label yang belum diputuskan surveyor.** Naskah Wulandari yang hancur
**memang tidak boleh direvisi AI** (mencegah AI bikin lebih rusak).

### 🐛 B. Rentang BAB salah (BUG WULAN) → **DIPERBAIKI**
```
ASIH      label 'bab' = [191,195,199,203,207] = SEMUA di DAFTAR ISI
          gabung (BAB ASLI) = {0,211,385,607,833}
WULANDARI label 'bab' = [459,468]             = sistematika
          gabung (BAB ASLI) = {0,471,7927,8141}
⇒ SUMBER BENAR = `gabung` + label 'bab' NON-sistematika
   (memory: "BAB ASLI = len(gabung) + label 'bab' non-sistematika")
```

### 🐛 C. `gaya_judul` selalu `campuran` (3× diperbaiki, akar ditemukan)
```
Percobaan 1: hitung huruf besar ≤2  → 'Uji Koefisien Determinasi (R2)' dibaca 'sentence' ❌
Percobaan 2: banding proporsi       → masih salah ❌
AKAR: definisi kabur + judul BAB "BAB I" (caps) dicampur subbab
FIX (Opsi A Bos): `title` = SEMUA kata diawali besar (kata fungsi boleh kecil)
                  judul BAB tidak ikut dihitung dalam gaya_judul
HASIL: 7/7 contoh benar ✅
```
**Catatan jujur:** `gaya_judul` per-BAB masih `campuran` — dan itu **JAWABAN BENAR**:
naskah memang campur (`'Gap research'` = campur bahasa; ada kalimat yang salah dilabeli judul).

---

## 4. 🎁 TEMUAN TAMBAHAN (tak diminta, bernilai)

> 🔴 **DIPERBARUI §6e — bagian ini mencatat versi LAMA (v1) `judul_curiga`.**
> Angka "10 dari 132" di bawah = **percobaan pertama** yang kemudian **DIBUANG**
> karena 2× salah tuduh. Versi final (v5c) = **0 curiga di Asih**.
> Lihat §6e untuk trade-off-nya. Bagian ini disimpan sebagai riwayat.

Fungsi **`judul_curiga()`** — tanda untuk HAKIM (bukan keputusan; hakim LAPOR jangan BLOKIR).

**Hasil di Asih (v1, TERBUKTI TERLALU LONGGAR): 10 dari 132 sub-bab dicurigai** — isinya:
```
L000149 'Hasil pra-survei menunjukkan bahwa instrumen penelitian'  ← KALIMAT, bukan judul ❌
L000253 'Penggunaan media digital'                 ← ini BUTIR daftar, bukan sub-bab ❌
L000257 'Kualitas konten digital'                  ← BUTIR ❌
L000261 'Interaksi dua arah dengan pelanggan'      ← BUTIR ❌
L000265 'Kemudahan proses transaksi digital'       ← BUTIR ❌
```
⇒ **KELAS KESALAHAN BARU** yang belum tertangkap hakim U-KUNCI (hakim lama menangkap
"butir daftar dianggap judul"; ini menangkap **"kalimat panjang dianggap judul"**).
Sinyal siap pakai, tidak membuang apa pun.

---

## 5. UJI BERGIGI — gerbang TERBUKTI BERGIJI

> Diukur saat gerbang masih **26 uji**. Setelah §6b–6e ditambah, **36 uji** —
> uji bergigi **diulang** di akhir: SEHAT **36/0 EXIT 0** · DISUNTIK **34/2 EXIT 1** ✅

```
SEHAT (modul asli)          : 26 LULUS / 0 GAGAL · EXIT=0  ✅   ← run awal
DISUNTIK (buang `gabung`)   : 24 LULUS / 2 GAGAL · EXIT=1  ✅   ← B1+B2 tertangkap
SEHAT (setelah 36 uji)      : 36 LULUS / 0 GAGAL · EXIT=0  ✅   ← run final
DISUNTIK (36 uji)           : 34 LULUS / 2 GAGAL · EXIT=1  ✅
```

⚠️ **2 cacat gerbang DITEMUKAN & DIBETULKAN saat uji bergigi:**
1. **Kasus uji B salah** — di kasus lama `label bab` == `gabung` ⇒ kode rusak pun lolos
   (uji BUTA). **Pelajarannya sama seperti 18 Sep**: *"sebelum menuduh MESIN rusak,
   pastikan KASUS UJINYA memang layak."* Kini pakai kasus PEMBEDA (label 4 titik vs gabung 2).
2. **B2 crash `IndexError`** saat B1 gagal ⇒ gerbang berhenti, sisa uji tidak jalan.
   Kini dicek panjang dulu.

---

## 6. 🔴 TEMUAN SAMPINGAN — BUG NYATA DI `app/konversi.py` (BUKAN kode Wulan)

```
app/konversi.py:1675   bentuk = bentuk_naskah(naskah, peta=keluar.get('mata'))
def bentuk_naskah(...)                                          ← TIDAK ADA DI MANA PUN
```

**Fakta terukur:**
- Fungsi **tidak pernah ada** — dicek 3 backup (1.247 / 1.915 / 2.205 baris), nol hasil
- Ditaruh **8 Okt 04:48** oleh sesi lain (kerja **terputus**, bukan bug logika)
- Komentar lengkap di atasnya (alasan "kepadatan kalimat bukan ukuran sah") ⇒ rencana
  yang berhenti di tengah jalan
- **Container produksi BERSIH** (versi lama 2.348 baris, 0 pemanggilan) ⇒ **belum masuk produksi**
- **Bahaya:** siapa pun yang `docker cp app/konversi.py` ke container → **crash `NameError`**
  saat rute konversi dipakai

**Konteks rencana (dari `CATATAN_DISKUSI_BAB4_KONVERSI_08OKT2026.md` §4.4):**
> *"Kenali bentuk naskah, tarik jenis/desain/model/sampel → **Jev** (EduAi)"*

⇒ Rencana 08 Okt (Jev kenali bentuk dulu) **sudah tergantikan** arah baru (peta3_jev).
Menurut arah Bos terakhir (*"TUAS BERIKUTNYA = BERSIHKAN INPUT, bukan tuning SOP lagi"*),
pemanggil mati ini **seharusnya dibuang** — **tapi Wulan TIDAK sentuh** (di luar tugas,
menunggu izin Bos).

**Efek samping:** `periksa_kode.sh` **GAGAL** karena ini:
```
✗ 1 nama TAK TERDEFINISI: app/konversi.py:1675:14: undefined name 'bentuk_naskah'
```

---

## 6b. ✅ TINDAK LANJUT 09 Okt (putusan Bos: "1 + 2")

### A. Bug `bentuk_naskah` — **DIBUANG** (putusan Bos)
```
Backup: _arsip/pre-buang-bentuk-naskah-09okt26/konversi.py
app/konversi.py:1675 → diganti:
    keluar['bentuk'] = None
    keluar['pesan_bentuk'] = ''
```
**Diperiksa:** `bentuk`/`pesan_bentuk` **tidak dipakai** di template maupun rute mana pun
(grep `templates/`, `main.py`, `rute_jurnal.py` = nol) ⇒ aman dibuang.
**Hasil:** `bash scripts/periksa_kode.sh` → **✅ LULUS** (sebelumnya GAGAL karena 1 ini).

### B. Definisi `campuran` — **DIPERBAIKI** (temuan Bos, revisi kecil)
```
MASALAH: "campuran" salah tembak — dotted-2 + dotted-3 dalam 1 BAB dianggap campur,
         padahal itu HIERARKI NORMAL ("2.1" lalu anaknya "2.1.1").
AKIBAT : pagar P2 menolak renumber yang sebenarnya AMAN.
FIX    : tambah skema 'dotted-hierarkis' (dotted-2 + dotted-3 = normal).
         'campuran' SEJATI hanya kalau sistem BERBEDA bertabrakan
         (dotted + alpha + paren).
```
**Terukur:**
```
dotted-2 + dotted-3        → 'dotted-hierarkis'  ✅ (dulu: 'campuran' ❌)
dotted + alpha             → 'campuran'          ✅ (tetap benar)
dotted-2 saja              → 'dotted-2'          ✅
```
Gerbang: **28 LULUS / 0 GAGAL** (tambah E5, E6).

### C. `tidak_jelas` = 0,0% (temuan Bos — proteksi belum terjangkau)
**Wulan akui:** Bos benar. Karena gerbang panjang/titik dibuang (datanya tak
terbantahkan), **tidak ada lagi yang menghasilkan `tidak_jelas`** ⇒ proteksi
"AI dilarang menyentuh" **belum aktif** — **jangan diklaim sebagai fitur berjalan**.
**Untuk v1 diterima** (revisi bekerja di level bagian via profil, bukan per baris).
Kalau Bos mau proteksinya nyata ⇒ perlu **pendeteksi fragmen baru** atau
**gerbang kesehatan level naskah** (untuk PDF hancur seperti Wulandari). **Belum dibuat.**

---

## 6c. 🔴 GANGGUAN LUAR SAAT VERIFIKASI ULANG (bukan kode Wulan)

Saat Wulan mengulang uji (setelah perubahan §6b), **Jev TIDAK BISA DIPANGGIL**:
```
SATPAM/typesafe/jev-1.13 → 502 → OpenRouter decisions HTTP 403:
   "Key limit exceeded (total limit)"
provider 'cb' → "No active credentials for provider: cb"
9router sendiri → HTTP 200 ✅ HIDUP (962 model)
```
⇒ **Kunci OpenRouter di belakang 9router HABIS LIMIT** (+ provider `cb` kredensial cabut).
**Ranah Bos (kredensial/modal), bukan Wulan.**

**Dampak ke laporan ini:**
- **Uji #1 (Asih/Wulandari) TETAP SAH** — dilakukan saat Jev HIDUP, hasilnya nyata.
- **Uji ulang TIDAK BISA** sampai kunci Jev pulih. Semua bagian **nol-Jev**
  (gerbang 28/0, skema, nomor_terakhir, pola_baris) **tetap lulus** dan tidak
  terpengaruh gangguan ini.

---

## 6d. ✅ UJI NASKAH KE-3 — DISERTASI UNHAS (fid=104) · gerbang 3-naskah GENAP

```
fid=104  DISERTASI-S3-unhas-kesehatan-stunting.docx (175 KB)
baris 25.055 · <w:tab>=0 ✅ BERSIH · waktu peta 167 dtk (naskah besar)
BAB ASLI = 5 ✅  (I PENDAHULUAN → V SIMPULAN DAN SARAN)
subbab 320 · judul_isi 328 · paragraf 11.521 · butir 453
```

**Skema nomor Disertasi BERBEDA TOTAL** (temuan penting — profiler membacanya benar):
```
'A. Latar Belakang'  → alpha-dot
'1. Tujuan umum:'    → num-dot
'Penyebab dan Faktor Risiko' → tanpa-nomor  (mayoritas)
⇒ skema = 'campuran' ✅ BENAR (memang campur, bukan dotted)
⇒ nomor_terakhir = {} ✅ BENAR (naskah ini TIDAK bernomor bertingkat)
```

**➜ PELAJARAN:** `nomor_terakhir` terisi HANYA kalau naskah memang bertingkat.
Disertasi (A./1.) & Asih (tanpa nomor) ⇒ `{}` = **jawaban yang BENAR**, bukan bug.
Profiler **membaca** pola, **tidak menebak**. (Renumber otomatis P2 = tidak berlaku di sini.)

### Tabel ringkas 3 naskah
| Naskah | BAB | subbab | `nomor_terakhir` | `curiga` | Verdict |
|---|---|---|---|---|---|
| ASIH fid=81 | **5** ✅ | 134 | makna `{}` | 0 | tak bernomor — benar |
| WULANDARI fid=115 | **4** ✅ | 74 | **10** | 10 | bertingkat + ada sitasi |
| DISERTASI fid=104 | **5** ✅ | 320 | makna `{}` | 0 | skema A./1. — benar |

---

## 6e. ✅ `judul_curiga` — 2× GAGAL, lalu DIPERKETAT ke sinyal PASTI

Wulan **2× gagal** (sesuai aturan maks 2, lantas STOP):
```
percobaan 1 (ambang 60 kar)  → Asih 12 curiga, SALAH TUDUH 'Uji heteroskedastisitas' ❌
percobaan 2 (ambang ≥6 kata) → Wulandari 29 curiga, SALAH TUDUH 'Uji Validitas Variabel X1' ❌
AKAR: panjang/kata/kapitalisasi TIDAK memisahkan judul vs kalimat akademik
      ⇒ persis kata Bos: "mesin tidak bisa mengenali bentuk naskah, perlu Jev"
```
**Perbaikan terakhir (v5c):** sisakan **2 sinyal yang TIDAK PERNAH SALAH**:
```
① awal-sitasi     '(Nama, thn)' di awal & pendek   → potongan isi/sitasi
② butir-bertanya  awal '1./2.' + diakhiri '?'      → heuristik Bos §8.2
```
**Hasil terukur (0 salah tuduh):**
```
ASIH      : 0 curiga      ✅
WULANDARI : 9 (12%) — SEMUA awal-sitasi:
   '(Khoironi, 2023)' · '(David, 2010) dalam…' · '(Regina – Div AyuMeera)' · '(Divisi Chemical)'
DISERTASI : 0 curiga      ✅
```
Gerbang: **36 LULUS / 0 GAGAL** · bergigi (disuntik → 34/2, EXIT 1).

---

## 6f. ⚖️ TRADE-OFF YANG DIAKUI (presisi menang, recall dikorbankan)

**Ini celah yang DIKETAHUI, bukan yang hilang diam-diam:**

```
versi v1  : Asih 10 curiga (TANGKAP L000149 'kalimat dianggap judul')
            TAPI 12 salah tuduh ⇒ presisi RENDAH
versi v5c : Asih 0 curiga  (TIDAK tangkap L000149)
            0 salah tuduh    ⇒ presisi TINGGI, recall TURUN
```

⇒ **Kelas "kalimat-dianggap-judul" saat ini TIDAK tertangkap.**

**Alasan memilih presisi (disetujui arah):** hakim = **reviewer**, bukan pemburu.
Salah tuduh membuat hakim kehilangan kepercayaan (dan menuduh judul SAH = merusak).
Lebih baik **diam** daripada menuduh salah — sejalan pagar H1 (*hakim LAPOR, jangan BLOKIR*).

**Yang MASIH tertangkap (sinyal pasti, 0 salah tuduh):**
```
① awal-sitasi    '(Khoironi, 2023)' · '(Regina – Div AyuMeera)'  → WULANDARI 9
② butir-bertanya '1. Apakah …?'  (heuristik Bos §8.2)
```

**Kalau nanti mau recall kembali:** penangkap "kalimat-dianggap-judul" **bukan** tugas
regex (2× gagal terukur) — itu tugas **Jev** (kode sediakan fakta → Jev menimbang),
persis putusan Bos di rancangan (opsi b/§8.1). **Jangan coba regex lagi.**

---

## 7. YANG BELUM ADA (jujur) — ✅ DISINKRONKAN 09 Okt (setelah §6b–6e)

> ⚠️ Versi lama §7 ini **BASI** (bilang renumber terblokir, periksa_kode GAGAL,
> Disertasi belum, gerbang 26/0). Semua sudah berubah. **Tabel ini = yang berlaku.**

| Hal | Status |
|---|---|
| Kolom `pola` tersimpan di DB | ❌ belum (profiler hitung on-the-fly, §P5) |
| Sambung ke hakim T④ + kontrak AI revisi | ❌ belum |
| Mesin renumber (§4) | ⚠️ **`dotted-hierarkis` diperbaiki ✅ (§6b.B), tapi renumber SENDIRI BELUM DIKODE** (spek saja). Catatan: WULANDARI **memang** dotted-2/3 ⇒ naskah itu **siap** di-renumber begitu mesinnya ada. ASIH (tanpa nomor) & DISERTASI (A./1.) tidak relevan untuk dotted |
| Uji naskah ke-3 | ✅ **SELESAI** — Disertasi **fid=104** (bukan 103) · §6d |
| `periksa_kode.sh` hijau | ✅ **LULUS** setelah bug `konversi.py` dibuang (§6b.A) |
| `tidak_jelas` proteksi AKTIF | ❌ **TIDAK** — 0,0% (tak ada yang menghasilkannya). Menunggu pendeteksi fragmen baru (§6b.C) |
| Deteksi "kalimat-dianggap-judul" | ❌ **CELAH DIKETAHUI** — v5c perketat presisi ⇒ L000149 tidak lagi tertangkap (lihat §4 & §6e). Trade-off disengaja |
| Deploy | ❌ tidak ada — modul belum dipakai fitur mana pun |
| Gangguan Jev (kunci OpenRouter) | ✅ **PULIH** — Bos naikkan limit kunci `JEV` (…10ac): `limit 4 → None` |

---

## 8. BERKAS TERKAIT

- `app/pola_penulisan.py` — modul (BARU)
- `app/_gerbang_pola.py` — gerbang **36/0** (BARU)
- `_arsip/pre-buang-bentuk-naskah-09okt26/konversi.py` — backup sebelum buang pemanggil mati
- `_sketsa/_uji_pola.py` — skrip uji nyata (BARU)
- `RANCANGAN_PROFILER_POLA_09OKT2026.md` — rancangan v3
- `CATATAN_DISKUSI_BAB4_KONVERSI_08OKT2026.md` §4.4 — konteks rencana `bentuk_naskah`
