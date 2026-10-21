# 🔖 MULAI DARI SINI — SESI BARU EduAi KONVERSI

**Tanggal catatan:** 09 Okt 2026 (malam)
**Proyek:** `/opt/data/services/eduai-publishing`

---

## 🟢 FLAG SESI TERAKHIR — 09 OKT 2026 (malam), TUTUP BERSIH

> Sesi berakhir jam 02:55 (UTC). Sesi berikutnya (setelah reset 04:00 UTC / 11.00 WIB)
> **BACA 3 BERKAS INI DULU, URUTAN:**
> 1. **`SESI_09OKT2026_KRONOLOGIS.md`** ← ringkasan 1 berkas, urut waktu, dari awal sampai putusan
> 2. **`CATATAN_KEPUTUSAN_PETA3_09OKT2026.md`** ← 6 aturan + urutan wajib + cara baca yang benar
> 3. **`TEMUAN_EKSTRAKSI_PDF_TABEL_09OKT2026.md`** ← mutu file user = akar sisa masalah

### ✅ SELESAI & TERPASANG malam ini (`peta3_jev.py`, 368 baris)
```
Poin 1: POLA_BAB terima angka "BAB 1"                        ✅
Poin 2: ANGKET = sinonim KUESIONER                           ✅
Poin 3: D1 pakai pola AWALAN (2 putaran; putaran 1 SALAH)    ✅
Poin 4: ronde beda ⇒ 'biasa' — putusan Bos A (konservatif)   ✅
ATURAN 5: diawali huruf kecil ⇒ KOREKSI LABEL                ✅
ATURAN 6: nomor halaman murni ⇒ BUANG                        ✅
D1 varian-2: "bagian ini" + frasa di dalam baris sendiri     ✅
VERIFIKASI ASIH: bab 5 · subbab 130 · NOL REGRESI            ✅
```

### 🔴 YANG HARUS DILANJUT (urut dampak)
```
1. `peta3_jev.py` BELUM MASUK APP (`app/peta_halus_jev.py` masih cara lama)
   ⇒ ini gerbang menuju fitur KOLABORASI
2. Uji naskah #3 = Disertasi 103 (gerbang validasi 3-naskah belum genap)
3. Simpan `section_state` + kolom mulai/akhir (bug `CatatanPembimbing.mulai`=0)
4. Sambung Kolaborasi: komentar pembimbing → tunjuk sub-bab → AI revisi potongan itu
```

### 🚨 3 PAGAR BARU (hasil kesalahan Wulan malam ini — WAJIB DIPATUHI)
```
① UJI NASKAH WAJIB lewat `app.ai._teks_dari_berkas` (jalur resmi).
   JANGAN skrip sendiri di host — Wulan 2× salah, 259 `<w:tab` bocor.
② SEBELUM lapor "berhasil": `grep -c '<w:tab' <hasil>` WAJIB 0.
③ SEBELUM lapor "berhasil": baca `gabung` + `sistematika` dari hasil NYATA.
   `r['label']` HANYA berisi KANDIDAT — BAB asli ada di `r['gabung']`
   ⇒ BAB ASLI = len(r['gabung']) + label 'bab' yang BUKAN sistematika.
```

### 📌 Yang Bos PUTUSKAN malam ini
```
① Poin 4 → A   ② Temuan ekstraksi → A (catat, tanpa ubah kode)   ③ Tutup sesi → C
```

---

## 🚨 BACA 2 BERKAS INI DULU (urutan)

1. **`CATATAN_KERJA_KONVERSI.md`** — status lengkap + cara lanjut + angka terukur
2. **`app/konversi.py`** — KODE NYATA (jangan percaya ringkasan)

**JANGAN percaya ringkasan sesi / ingatan.** Ringkasan sesi panjang SUDAH TERPOTONG
(context compaction) → itu sebab Wulan salah berkali-kali 08 Okt
(sesi panjang dipotong ⇒ ingatan hilang ⇒ Wulan mulai MENEBAK).

---

## 🎯 PEKERJAAN BERIKUTNYA (pilih satu)

### Pilihan 1 — Peta bab pakai **Jev** (pola resmi)
Ubah `_posisi_dari_jev()` di `app/konversi.py` jadi pola resmi:
- kode beri ID baris (`L014| teks`)
- Jev dapat **1 pertanyaan `noul` SEMPIT per kandidat baris**
- kode merakit peta (Jev tak pernah menulis teks)

Baca dulu: skill `typesafe-jev` → `references/cookbook-structure-recovery.md`
Detail: bagian 🔴 di `CATATAN_KERJA_KONVERSI.md`

### Pilihan 2 — Pintu revisi (MESIN UANG)
Mesin SUDAH ADA (`daftar_revisi`, `hitung_biaya_revisi`, `susun_pesan_revisi`).
Belum ada: rute POST + halaman hasil + kotak centang.
Detail: bagian 🔑 di `CATATAN_KERJA_KONVERSI.md`

### Pilihan 3 — DEPLOY
Semua perubahan 07–08 Okt masih di container (`docker cp`), **belum masuk image**.
⚠️ Container dibuat ulang = HILANG. Deploy = `bash jalankan.sh` (build image baru).

---

## ⚠️ 7 ATURAN KERAS (semua ini Wulan pernah langgar)

1. **BUKA BERKAS DULU** sebelum bilang "belum ada / tidak ada / rusak"
2. **Angka dari CETAKAN UJI**, bukan ingatan
3. **Tiap patch → cek lint** (Wulan pernah hapus docstring 2× → SyntaxError)
4. **Ragu ⇒ BILANG RAGU**, jangan menebak yakin
5. **`docker cp` → WAJIB `docker restart`**; JANGAN `docker run -v` (mount tak nyambung)
6. **Jev menuduh "kurang" ⇒ CURIGAI BAHAN DULU** (4× bahan cacat, 1× Jev benar)
7. **Jev = MATA, lapor; USER putuskan.** Jev tidak memblokir.

---

## 🔑 NAMA YANG JANGAN DIKARANG

| Barang | Nama BENAR | Wulan pernah salah tulis |
|---|---|---|
| Model konversi | `models.KonversiNaskah` | ~~`KonversiPakai`~~ |
| Sesi DB | `models.SessionLocal` | ~~`app.db.SessionLocal`~~ |
| Login API | `auth.wajib_login_api` (401) | ~~`wajib_login` (303)~~ |
| Judul bagian | `'KESIMPULAN'` HURUF BESAR | ~~`'Kesimpulan'`~~ |
| Kotak token | `kuota.potong_banyak()` | ~~dompet baru~~ |

---

## 📌 PRINSIP INDUK BOS (jangan dilanggar)

> *"Jev selalu terdepan sebelum mesin dan Ai."*

**Urutan baku:** ① Jev kenali bentuk → ② mesin olah → ③ AI tulis → ④ Jev periksa hasil.

**DILARANG:** mesin menebak bentuk naskah dengan regex.
Kalau mesin tak bisa mengenali suatu bentuk → **itu tugas Jev**.

> *"Jangan bangun baru kalau sudah ada."* — CARI dulu di kode.
> *"Jangan percaya dokumen, ingatan, atau catatan."* — CEK KODE.

---

## 🎯 TUJUAN BISNIS (kenapa ini dikerjakan)

Pintu uang = **kekurangan naskah yang ditemukan Jev**.
Contoh: Jev bilang kurang **Novelty** + kurang **research gap** →
user setuju perbaiki → **bayar 4 token** (2 + 2).
Atau pilih satu (gap saja) → **2 token**.

Harga jualan per item = **2 token** (`TOKEN_PER_REVISI`).

---

## 🧹 08 Okt 2026 — PETA NASKAH DIRAPIKAN (SATU PINTU)

**BACA: `SOT_PETA_NASKAH_SATU_PINTU_08OKT2026.md`** ← SATU-SATUNYA dokumen peta naskah.

```
RESMI  : peta3_jev.py + saringan_bersih.py + _audit_per_aturan.py
DIHAPUS: peta_bab_jev.py · peta_halus_jev.py (cara lama)
         HASIL_UKUR_PETA_JEV_08OKT2026.md · HASIL_UKUR_PETA_HALUS_08OKT2026.md
         RANGKUMAN_UTUH_PETA_NASKAH_JEV_08OKT2026.md · HASIL_UJI_PETA_3_TINGKAT_08OKT2026.md
ARSIP  : _arsip/pre-rapi-peta-08okt26-cara-lama/ (arkeologi saja, JANGAN dipakai)
```

**Hasil terukur (Asih SELURUH NASKAH, 159.909 kar):** 5/5 BAB ✅ · 143 paragraf ·
1.029 kandidat · goyang 3,0% · 0,7–1,0 dtk/panggilan · 0 gagal.

**2 akar yang ditutup hari ini:**
1. `_subbab_palsu()` dipakai untuk MENYARING baris ⇒ makan **922 baris (76%)** Asih,
   termasuk 10 judul BAB + 274 paragraf asli.
2. Baris KOSONG dibuang dari jendela ⇒ UJI 19 ambruk (90% → 18%).

**⚠️ PELAJARAN WAJIB: UKUR `RECALL`, BUKAN CUMA PRECISION.**
Uji 21 cuma ukur precision ⇒ 82% baris terbuang tanpa ada yang tahu.
Tiap naskah/template baru ⇒ jalankan `_audit_per_aturan.py`.

**SISA (jujur, belum beres):**
- goyang 3,0% (65% soal "awal paragraf atau bukan" — dampak kecil; TIDAK ada goyang bab⇔subbab)
- "Temuan tersebut memperlihatkan…" bisa jatuh 'biasa'
- header tabel kuesioner "Kode (Indikator) | Setuju…" masih jadi sub-bab
- celah regex: `BAB 1` (angka) & `BAB IV PENDAHULUAN` (nempel)
- belum masuk app · belum uji Tesis 78 utuh & Disertasi utuh & naskah Inggris
- saran Bos utk general: varian penomoran · halaman depan konsisten · set pola Inggris · paket uji 3–5 naskah
