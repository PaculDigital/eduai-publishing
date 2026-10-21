# 🧭 IDE PERLUASAN PERAN JEV DI EDUAI (07 Okt 2026)

> 🚩 **DIPERBARUI 07 Okt 2026 — CARA PAKAI JEV DI SINI SUDAH USANG.**
> Sebagian isi catatan ini dibuat waktu Wulan **belum membaca dokumentasi resmi**,
> jadi ada **klaim yang keliru & berbahaya** (mis. *"skema Jev tertutup / hanya 3 nama"*,
> *"Jev tidak stabil"*, *"hanya 2 tipe sah"*, *"criteria boleh string"*).
> ⇒ **ACUAN TUNGGAL cara pakai Jev sekarang:** `PANDUAN_PAKAI_JEV.md`
>   + skill `typesafe-jev` (dokumentasi RESMI `docs.typesafe.ai`).
> ⇒ Blok lama **TIDAK dihapus** (riwayat) — tapi **DILARANG dipakai sebagai panduan**.
> ⇒ Penjaga: `_gerbang_skema_jev.py` + `_uji_gigi_skema_jev.py`.



<!-- 📝 SOT: CATATAN DISKUSI — bukan penentu status -->

> # 📝 CATATAN DISKUSI — BUKAN penentu status proyek.
> Berkas ini merekam **bahan pembicaraan** saat itu. Sebagian bisa sudah
> dikerjakan, sebagian belum. ❌ JANGAN dipakai sebagai keadaan kini.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.

> **STATUS: 🟡 DILARANG DIKODING** — menunggu putusan Bos.
> Permintaan Bos (opsi C): *catat dulu, jangan koding.*

---

## 0. 🚨 KOREKSI — WULAN SALAH BERULANG (WAJIB DIBACA DULU)

Berkas `CATATAN_JEV_FITUR_JURNAL_06OKT2026.md` ditulis Wulan 06 Okt dengan
kesimpulan **"Jev TIDAK perlu"**. **Itu keliru** — dan pola itu TERULANG.

Catatan itu sendiri sudah menuliskan janji (baris 137–139):
> *"Kalau Bos punya alasan lain yang Wulan belum lihat ... tolong Bos sebutkan —
> Wulan akan cek kodenya, **bukan langsung menolak**."*

**Bos SUDAH menyebutkan alasannya — berulang kali — tapi Wulan tetap menolak.**
Buktinya (verbatim):
> *"Makanya dari kemarin saya sudah menawarkan pakai jev, tapi kamu terus selalu
> menolak."* (07 Okt 2026)

### ❌ Kesalahan berpikir Wulan (akar)
1. Wulan membaca **"Jev GAGAL menilai MUTU"** → lalu menyimpulkan
   **"Jev tidak berguna di mana-mana"**. Ini **melompat terlalu jauh**.
2. Wulan menyamakan **MUTU** ("bagus/tidak") dengan **BENTUK/KEBERADAAN**
   ("ini bentuk apa / ada atau tidak"). **DUA HAL BERBEDA.**
3. Wulan menganggap **mesin sudah cukup**. Bos membuktikan **tidak**:
   > *"Mesin tidak bisa menangani / identifikasi berbagai macam bentuk naskah."*

### ✅ PRINSIP INDUK BARU (putusan Bos 07 Okt, verbatim)
> **"Ingat wulan di mana-mana jev selalu terdepan sebelum mesin dan Ai — itu
> memang fungsi jev di mana pun. Agar mesin dan Ai enak dalam bekerja dan hasil
> presisi."**

⇒ **JEV = PENDAHULU (gatekeeper).** Jev membaca MENGENALI LEBIH DULU; mesin &
AI bekerja SETELAHNYA. Jev **bukan pelengkap di belakang** — ia **PEMBUKA JALAN**.

**Urutan baku yang benar:**
```
① JEV kenali bentuk/struktur  →  ② MESIN olah  →  ③ AI tulis  →  ④ JEV periksa hasil
```

### 🔒 Batas yang TETAP (jangan dilanggar)
Yang dulu **terbukti gagal** = Jev **menilai MUTU TULISAN** ("bagus/tidak",
"layak/tidak", `nilai_balasan()` dicabut 05 Okt). Yang **tetap sah** = Jev
**MENGENALI BENTUK & KEBERADAAN** ("ini bentuk apa", "bagian ini ada/tidak").
Perluasan peran **WAJIB diusulkan**, bukan ditahan.

---

## 1. 🎯 MASALAH YANG MAU DITUTUP (keluhan Bos, verbatim)

> *"Mesin tidak bisa menangani / identifikasi berbagai macam bentuk naskah.
> Maka perlu jev."*

**Bukti terukur bahwa mesin memang lemah bentuk:**
| Naskah | Mesin | Jev | Kenyataan |
|---|---|---|---|
| SKRIPSI UNHAS | 6 bab | **1 bab** | **dua-duanya ragu** → butuh lapis ketiga |
| SKRIPSI UNMUL | 4 bab | — | email palsu `mAP@0.5` tertangkap sebagai email |
| SKRIPSI Asih | 5 bab | 5 bab (0,99) | **SEPAKAT** ✅ |
| Naskah Asih | bahan peta-bab | bilang "abstrak tidak ada" (0,10) | **padahal ADA** → bahan yang salah |

⇒ Mesin bagus pada naskah **berpola rapi** (BAB I/II/III). Begitu bentuknya
**tidak lazim**, mesin bisa **salah tanpa tahu ia salah**.

---

## 2. 📋 DAFTAR IDE (7 peran baru) — BELUM DIPUTUS

Urutan = **prioritas dampak** (bukan urutan koding).

### 🔴 A. JEV KENALI BENTUK NASKAH LEBIH DULU (paling penting)
**Masalah:** sekarang Jev dipanggil **setelah** mesin memetakan. Kalau bentuk
naskah aneh, **mesin sudah salah duluan** — Jev hanya membetulkan setelahnya.

**Usulan:** balik urutannya.
```
SEKARANG : mesin baca bentuk → Jev periksa peta
USULAN   : Jev baca BENTUK dulu → mesin kerja dengan petunjuk bentuk
```
**Bentuk yang perlu dikenali Jev:** bab romawi · bab angka · bab gabungan
(ANGKA+judul) · naskah tanpa bab (hanya sub-judul) · naskah artikel (bukan
skripsi) · laporan penelitian · naskah campuran.

**Kenapa ini tepat tugas Jev:** mengenali **bentuk** = pekerjaan STRUKTUR
(melihat pola), **bukan** menilai mutu. Selaras batas peran.
**Biaya:** ±0,9 dtk · ~Rp 0,0002 (terukur).

### 🔴 B. JEV SEMPURNAKAN DETEKSI JENIS NASKAH
**Masalah:** `jenis.py` (SUDAH ADA) mendeteksi kuantitatif/kualitatif/review
**murni dari kata kunci**. Naskah campuran / eksperimen → mudah salah.

**Usulan:** mesin tebak → **Jev konfirmasi** → kalau beda → **tanya user**
(bukan paksa pilih). Pola "pola Jev" yang sudah dipakai di peta bab.
**Pagar:** Jev **tidak menggantikan** jenis.py — hanya lapis pemeriksa.
**Catatan jujur:** dulu "jenis" masuk daftar 8 modul zona-gagal. ⚠️ Bedanya:
yang dulu gagal = menilai **MUTU**; yang ini = mengenali **JENIS** (keberadaan
ciri), bukan menilai bagus/tidak.

### 💰 C. ABSTRAK 2 BAHASA — CEK KESELARASAN (PINTU JUALAN KEDUA)
**Masalah:** putusan Bos (no.4, terkunci) = abstrak ID+EN **otomatis** oleh AI.
Tapi sekarang **tidak ada yang memeriksa** apakah EN selaras dengan ID.

**Usulan:** Jev periksa **keberadaan** komponen abstrak di kedua bahasa
(latar · tujuan · metode · hasil · simpulan) → kalau ada yang **belum ada** →
lapor → **[Lengkapi = Token Revisi]**.
**Nilai bisnis:** ini **pintu jualan kedua**, pola sama dengan pesan mutu.

### 🟠 D. JEV CEK KUTIPAN HILANG SAAT KONVERSI
**Masalah:** AI merangkum naskah → **risiko sitasi hilang** tanpa disadari.

**Usulan:** mesin sudah punya daftar pustaka; Jev periksa **keberadaan** sitasi
penting di artikel hasil (bukan menilai mutu sitasi).
⚠️ **Wajib cek dulu:** apakah `citation_validator` sudah menutup ini — jangan
bikin akar kembar.

### 🟠 E. JEV BANDINGKAN SEBELUM vs SESUDAH
**Usulan:** Jev periksa "apakah struktur artikel hasil **utuh** dibanding naskah
asal" — memakai 3 pertanyaan peta yang SAMA (jumlah bab · romawi · berurutan).
**Murah** karena pertanyaannya sudah ada; tinggal dipakai 2×.

### 🟡 F. JEV SARANKAN JUDUL ARTIKEL
**Masalah:** user sering bingung judul artikel jurnal yang tepat.
**⚠️ Hati-hati:** "judul bagus/tidak" = **MUTU** → zona gagal.
⇒ Hanya kalau dibatasi: Jev menyebut **keberadaan unsur** judul (variabel ·
konteks · metode), **bukan** menilai bagusnya.

### 🟡 G. JEV DETEKSI BAGIAN TIDAK LAZIM
**Bukti nyata:** naskah Asih → mesin bilang **BAB V = 197.997 karakter**
(mencolok vs BAB lain 28rb–131rb) ⇒ kemungkinan lampiran ikut terbaca.
**Usulan:** Jev lapor "bagian ini ukurannya tidak lazim" → mesin tak bisa lihat ini.

---

## 3. 🔒 PAGAR WAJIB (jangan dilewat)

| # | Pagar | Alasan |
|---|---|---|
| 1 | Jev **LAPOR**, tidak memblokir | Putusan Bos: user yang putuskan |
| 2 | Jev **tidak** menilai MUTU ("bagus/tidak") | Terbukti gagal 3× (`nilai_balasan()` dicabut) |
| 3 | Jev mati/ragu → **mesin & AI tetap jalan** | Jangan jadikan Jev penghalang |
| 4 | Nilai **0,35–0,50 = RAGU** → jangan klaim | Bahaya: user senang padahal cacat |
| 5 | **GREP dulu** sebelum bikin fungsi/konstanta | Wulan pernah menimpa `BAGIAN_WAJIB` ⇒ rusak |
| 6 | Jev **tidak menyentuh** Mode Belajar | Putusan Bos 06 Okt (naskah sudah jadi) |
| 7 | Biaya: 1 panggilan gabung (18+ pertanyaan), bukan 18 panggilan | Hemat; terbukti 0,87 dtk |
| 8 | Tipe pertanyaan **hanya** `noul` / `choice` | Tipe lain → 503 `invalid_union` |

---

## 4. 📊 BUKTI JEV MAMPU (terukur 07 Okt, naskah Asih nyata)

| Hal | Nilai |
|---|---|
| Model asli | `typesafe/jev-1.13-20260917` |
| Waktu | **0,87 detik** (18 pertanyaan sekaligus) |
| Biaya | ~Rp 0,0002 (in 546 tok · out 234 tok) |
| Ketepatan | abstrak 0,82 ✅ · pustaka 0,92 ✅ · novelty 0,16 (memang belum ada) |
| Uji skema | 18 nama bebas dijawab — **hanya TIPE** yang terbatas |

⇒ Jev **murah, cepat, dan mampu**. Yang selama ini menahan = **Wulan**, bukan mesinnya.

---

## 5. 📋 RENCANA KERJA (SETELAH IZIN BOS — belum dikoding)

| Tahap | Isi | Prasyarat |
|---|---|---|
| **J0** | Tampilkan pesan mutu di `/artikel` (mesin sudah kirim `mutu_pesan`) | — |
| **J1** | Jev kenali BENTUK naskah (ide A) — balik urutan | J0 |
| **J2** | Jev konfirmasi JENIS naskah (ide B) | J1 |
| **J3** | Abstrak 2 bahasa + Token Revisi (ide C) 💰 | J2 |
| **J4** | Kutipan hilang (ide D) — **cek `citation_validator` dulu** | J1 |
| **J5** | Bandingkan sebelum/sesudah (ide E) | J1 |

**Aturan kerja tiap tahap:** backup `_arsip/pre-*` + MD5 → koding → gerbang
**DI DALAM container** → **uji gigi** (harus bisa GAGAL) → uji naskah **NYATA**
→ laporan sebelum deploy.

---

## 6. ⚠️ YANG WULAN TIDAK USAHKAN (jujur)

1. **Jev untuk fitur Jurnal/Workspace** (cari artikel, DOI, relevansi) — bidang
   beda; alatnya `audit_doi()` + `_nyambung()`. **Catatan 06 Okt soal ini TETAP BENAR.**
2. **Jev menilai "bagus/tidak"** — zona gagal, jangan diulang.
3. **Jev masuk Mode Belajar** — putusan Bos 06 Okt.
4. **Jev jadi penghalang** (memblokir konversi) — putusan Bos: user yang putuskan.

⇒ Koreksi 06 Okt berlaku untuk **perluasan ke BENTUK/STRUKTUR**, **bukan**
membatalkan batas mutu.

---

## 📋 STATUS
- [x] Dicatat 07 Okt 2026
- [x] Koreksi kesalahan Wulan (menolak Jev) — dicatat
- [x] Prinsip induk Bos: **Jev TERDEPAN sebelum mesin & AI**
- [ ] Ditunggu putusan Bos per ide (A–G)
- [x] **DILARANG dikoding** sebelum Bos bilang mulai
