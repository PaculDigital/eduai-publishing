# UJI D — PEMISAH TEGAS: **GAGAL** (09 Okt 2026)

> **Putusan Bos: "D"** — uji apakah pemisah tegas antar-kandidat menolong.
> **HASIL: TIDAK. Semua pemisah MEMPERBURUK.** Usul Wulan SALAH.

---

## 1. HASIL (3× ulang tiap bentuk, 5 kandidat, c00 = L008050 JUDUL ASLI)

```
P0_polos      k00 = 0,55 0,51 0,55   rata 0,54   ← kontrol (bahan sekarang)
P1_bernomor   k00 = 0,33 0,35 0,34   rata 0,34   ❌ TURUN 0,20
   "== KANDIDAT 1 dari 5 =="
P2_terpagar   k00 = 0,37 0,38 0,38   rata 0,38   ❌ TURUN 0,16
   garis ------- di atas & bawah tiap kandidat
P3_kosong     k00 = 0,41 0,38 0,41   rata 0,40   ❌ TURUN 0,14
   satu baris kosong antar kandidat
```

**⇒ SEMUA bentuk pemisah MENURUNKAN skor judul asli.** Yang terburuk justru
pemisah paling tegas (bernomor).

## 2. KENAPA (hipotesis dari data)

```
Pemisah TEGAS justru memberi Jev lebih banyak "bahan yang bukan naskah"
(label, garis) ⇒ perhatian makin terbagi ⇒ skor turun.
⇒ Bahkan `#### k00` di P0 pun sudah jadi "beban" — memisah lebih banyak = buruk.
⇒ Ini SEJALAN dengan pelajaran LAMA kita (memory): "kalimat paling SIMPEL =
   paling BURUK... daftar LARANGAN merusak" — makin banyak penanda buatan,
   makin bingung Jev.
```

## 3. KESIMPULAN

```
❌ D GAGAL. Pemisah BUKAN jalan keluar.
✅ Yang BENAR (dari ukur batas, sudah terbukti):
     1 kandidat → 0,71 STABIL
     2+ kandidat → jatuh ~0,52 dan goyang
   ⇒ masalahnya JUMLAH KANDIDAT, bukan pemisahnya.
```

## 4. JALAN YANG TERSISA (pilih — keputusan Bos)

```
A. PECAH GELOMBANG: kirim 1-2 kandidat per panggilan
   ✅ presisi terjaga (0,71)
   ❌ 74-77 kandidat ⇒ 37-74 panggilan per naskah ⇒ LAMBAT + MAHAL
   ⚠️ tapi TERUKUR di memory: "156 pertanyaan / 20.622 kar ✅" dulu BERHASIL —
      jadi banyaknya panggilan bukan masalah teknis, hanya waktu & biaya.

B. SKOR RELATIF (bukan absolut):
   Terima bahwa saat kandidat banyak, SEMUA skor turun rata (~0,52) —
   TAPI judul asli tetap LEBIH TINGGI dari butir (0,71 vs 0,30 saat bersih).
   ⇒ Uji dulu: apakah URUTAN masih benar saat bercampur? (belum diuji)
   ⇒ Kalau ya: pakai PERINGKAT relatif, bukan ambang absolut 0,60.
   ⇒ Ini MURAH (nol perubahan gelombang).

C. PECAH DUA TAHAP:
   Tahap 1: semua kandidat (kondisi bercampur) → ambil skor TERTINGGI
   Tahap 2: hanya 1-3 teratas → tanya ULANG sendiri-sendiri (0,71)
   ⇒ 1 panggilan besar + 1-3 panggilan kecil ⇒ kompromi biaya & presisi ⭐
   ⇒ Pola SUDAH ADA: konversi.py punya `_GAL_KAND` (gelombang) tinggal
     dirapikan jadi "panggilan besar dulu, lalu verifikasi ulang teratas".
```

## 5. YANG WULAN USUL

**C** — dua tahap. Alasannya:
```
· murah (1 panggilan besar + 1-3 kecil, bukan 74)
· presisi akhir = kondisi bersih (0,71)
· TIDAK menghapus apa pun; menumpang pola gelombang yang sudah ada
· nol tebakan di kode (kode hanya memilih yang SKORNYA TERTINGGI — fakta, bukan tebakan)
```

⚠️ Risiko C: kalau Tahap 1 salah memberi skor rendah ke judul asli (seperti
L007929), ia tidak masuk 3 teratas ⇒ tidak diverifikasi ulang. **Perlu diuji.**

## 6. URUTAN

```
① ✅ harness diperbaiki (susun())
② ✅ ukur batas → 1 kandidat 0,71 vs 2+ ~0,52
③ ✅ uji D (pemisah) → GAGAL, semua menurunkan
④ ⬜ Bos putuskan: A (pecah gelombang) / B (skor relatif) / C (dua tahap)
⑤ ⬜ ukur ulang 16 kasus kondisi bersih → skor sebenarnya K5
⑥ ⬜ uji Opsi A (4× Informan) · instalasi
```
