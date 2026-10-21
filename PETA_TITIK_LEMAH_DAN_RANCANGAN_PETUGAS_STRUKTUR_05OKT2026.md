# 🔍 PETA TITIK LEMAH EDUAI — DARI KODE (bukan dugaan)
**Tanggal:** 05 Okt 2026 · **Perintah Bos:** "A dan B" (kerjakan IDE 1 + petakan dulu)
**Metode:** ukur 56 modul + uji 7 naskah NYATA di DB produksi. Semua angka di bawah TERUKUR.

---

## BAGIAN 1 — HASIL PEMETAAN 56 MODUL (tugas B)

### Cara ukur
Hitung per modul: baris · jumlah `re.*` (pola teks) · jumlah `if ... in teks` (cocok-kata)
· jumlah jalur AI. **Modul dengan pola teks BANYAK tapi jalur AI NOL = paling rawan**
(memutuskan dengan cocok-kata, tak ada penilai kedua).

### Peringkat RAWAN (pola teks banyak, AI nol)

| Modul | baris | re. | Menentukan apa | Dampak kalau salah |
|---|---|---|---|---|
| **parser.py** | 448 | 12 | **PENGALI HARGA** (`x1/x3/x4/x5`) | ⚠️ DUIT — salah tebak = salah tagih |
| **state.py** | 814 | 23 | **PETA BAB / HARGA** | ⚠️ DUIT + AI salah konteks |
| **jenis.py** | 547 | 9 | jenjang S1/S2/S3 | naskah direvisi standar SALAH |
| **konsistensi.py** | 825 | 10 | cek judul/variabel/hipotesis | lolos cacat / menuduh benar |
| **etika.py** | 751 | 20 | kelayakan etik | lolos / protes palsu |
| **pustaka.py** | 769 | 19 | daftar pustaka | sitasi palsu lolos |
| **gambar.py** | 886 | 16 | gambar & tabel | "ada gambar" padahal tidak nyambung |
| **konteks.py** | 815 | 20 | konteks revisi | salah arah revisi |
| **citation_validator.py** | 348 | 7 | validasi sitasi | sitasi palsu lolos |

### Kesimpulan peta
**Ada 9 modul yang memutuskan dengan COCOK-KATA, tanpa penilai kedua** — inilah
"titik rawan salah / tidak presisi" yang Bos maksud. Yang **paling menyentuh uang**:
`parser.py` (pengali harga) dan `state.py` (peta bab → jumlah bagian → harga).

---

## BAGIAN 2 — TEMUAN TERUKUR: DETEKSI STRUKTUR (tugas A)

### Bukti dari 7 naskah ASLI di DB produksi

| id | kar | sub-bab | BAB | bagian dipakai harga |
|---|---|---|---|---|
| 9 | 65.067 | 9 | 5 | **9 (sub-bab — presisi)** |
| 60 | 70.487 | **0** | 5 | 5 (BAB BESAR — kasar) |
| 70 | 44.782 | 5 | 6 | **5 (sub-bab)** |
| 71 | 93.818 | 8 | 3 | **8 (sub-bab)** |
| 72 | 415.284 | **0** | 5 | 5 (BAB BESAR — kasar) |
| 81 | 159.909 | **0** | 5 | 5 (BAB BESAR — kasar) |
| 86 | 70.487 | **0** | 5 | 5 (BAB BESAR — kasar) |

### 🚨 T1 — 4 dari 7 naskah (57%) → sub-bab = 0
Penyebab: `_POLA_SUBBAB` (state.py:298) **hanya satu bentuk**:
```python
r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\s+([A-Z][^\n]{2,110})$'
```
Hanya menerima `X.Y` + judul HURUF BESAR. Naskah disertasi 415rb kar & skripsi
Asih 159rb kar → **nol**. Akibat nyata: **harga jatuh ke BAB BESAR** (5 kuota)
padahal isinya jauh lebih banyak bagian, **dan ingatan per sub-bab hilang**.

### 🚨 T2 — naskah 71 ada `2.1.3`; pola hanya `X.Y`
Baris 295-297 state.py **mengakui sendiri**: *"3 dari 5 dokumen memang TIDAK
menomori sub-bab sama sekali, jadi perbaikan ini HANYA menolong naskah bergaya
bernomor. Sisanya perlu pendekatan lain (belum diputuskan Bos)."*
→ **Celah ini SUDAH DIKETAHUI tapi belum ditutup.**

### 🚨 T3 — `BAB 1` (angka Arab) belum diuji ke DETEKSI
`_POLA_BAB` (state.py:235) memakai `[IVXLC]{1,5}` — **hanya romawi**.
`kategori_bab_besar()` (05Okt26) sudah menerima angka Arab, tapi
**deteksi babnya sendiri belum**. Perlu diukur pada naskah bergaya `BAB 1`.

### ⚠️ KOREKSI JUJUR WULAN
Wulan sempat menghitung "89 kandidat sub-bab" di naskah 72 lalu hampir menyimpulkan
mesin buta. **SALAH** — setelah diperiksa, 89 itu **angka statistik**
(`5.156 anak`, `109.041 rumah`), bukan sub-bab. Aplikasi **sudah BENAR** menolaknya
(saringan `_subbab_palsu` bekerja). Klaim itu **ditarik**.

---

## BAGIAN 3 — RANCANGAN A: PETUGAS STRUKTUR (Jev)

### Prinsip (mengikuti pola satpam — nol risiko)
1. Mesin lama **TETAP mencari** (`deteksi_subbab` → `deteksi_bab_besar`) — tidak dibuang
2. Jev **memeriksa** hasil + menambah bagian yang mesin lewatkan
3. Jev mati / ragu / lambat → **pakai hasil mesin apa adanya** (perilaku lama persis)
4. **Tidak boleh** memotong kuota lebih mahal tanpa sepengetahuan user

### Alur
```
naskah → [mesin lama: deteksi_subbab] → bagian_kasar
                    ↓
        [JEV: petugas struktur]  ← BARU
        kirim: 300 kar awal tiap bagian + daftar judul yang dilewatkan
        tanya: "ada bagian yang terlewat? sebutkan nomor + judulnya"
                    ↓
        gabung: mesin ∪ jev → bagian_final
                    ↓
        kalau jumlah NAIK → user diberi tahu (harga berubah, minta setuju)
```

### Pagar wajib
- **Pagar 1:** Jev gagal/mati → `bagian_kasar` (perilaku lama) — prompt TIDAK berubah
- **Pagar 2:** jumlah bagian naik → **harga naik** → WAJIB minta izin user dulu
  (pola yang SUDAH ADA di `Q1`/`butuh_izin`)
- **Pagar 3:** maksimal `AI_MAX_KOMENTAR`-gaya cap (jangan sampai Jev kembalikan 500 bagian)
- **Pagar 4:** hasil Jev yang **tidak ada di teks** → dibuang (anti-halusinasi)

### Yang diuji (gerbang bergigi)
- naskah `X.Y` normal → hasil sama seperti mesin (tidak mengubah yang sudah benar)
- naskah `A.`/`X.Y.Z`/`BAB 1` → Jev menemukan yang mesin lewatkan
- Jev dimatikan → perilaku lama persis
- Jev mengarang nomor → dibuang

---

## BAGIAN 4 — USULAN URUTAN

1. **Ukur batas dulu** — 20-30 naskah asli (bukan 7) supaya angkanya jujur
   (pelajaran deteksi judul: *30 judul gampang = menipu diri sendiri*)
2. Bangun `app/petugas_struktur.py` (modul baru, **tidak menyentuh** `state.py`)
3. Gerbang bergigi + smoke (pola C7)
4. Baru sambung ke jalur biaya (setelah terbukti)

---

## 📌 CATATAN
- Modul baru **DI LUAR** `app/` untuk uji (aturan: `COPY app` ⇒ apa di `app/` ikut image)
- Backup sebelum sentuh: `_arsip/pre-petugas-struktur-<tgl>/` + MD5
- `state.py` **DILARANG diubah** di tahap 1 (biar mesin lama tak tersentuh)
