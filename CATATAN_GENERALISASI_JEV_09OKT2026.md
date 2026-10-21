<!-- CATATAN USULAN (RIWAYAT) — SOT: bukan sumber status. Status peta naskah ada di SOT.md §SESI TERAKHIR + CATATAN_KEPUTUSAN_PETA3_09OKT2026.md -->

# 🧭 JEV BERSIFAT GENERAL — USUL BOS, 09 OKT 2026

> **Status:** USULAN BOS, DICATAT — belum dikoding (kecuali Lapis 1 yang sudah 80% jadi).
> **Asal:** pesan Bos, 09 Okt 2026 (verbatim arah: "Agar jev bersifat general,
> mirip-mirip tapi tidak sama. Strategi: jangan kejar satu aturan untuk semua
> kampus. Bangun dua lapis.")

---

## 🎯 MASALAH YANG DITUTUP

Naskah antar-kampus **mirip tapi tidak sama**: format BAB ("BAB I" vs "BAB 1"),
nama bagian depan, gaya lampiran, kapitalisasi judul, kata kuesioner vs angket.
Kalau semua dipaksa cocok dengan **satu** daftar aturan → aturan bertambah terus
(whack-a-mole) dan tetap tak akan menangkap ribuan bentuk naskah.

---

## 🏗️ DUA LAPIS (strategi inti)

### Lapis 1 — UNIVERSAL (sudah ~80% jadi malam ini, TERBUKTI di Asih)

Sinyal struktur yang **TIDAK berubah antar-kampus**. Tetap di **KODE**, berlaku
untuk semua naskah:

| Aturan | Isi | Status |
|---|---|---|
| ① pipa ≥2 & ≤300 kar | baris tabel = bukan judul | ✅ terpasang |
| ② >300 kar | bukan sub-bab (koreksi label → paragraf) | ✅ terpasang |
| ③ `KUESIONER…` | lampiran, bukan struktur | ✅ terpasang |
| ④ header SPSS (daftar tertutup) | bukan sub-bab (koreksi → biasa) | ✅ terpasang |
| ⑤ D1 blok sistematika | ditandai, jangan dibuang | ✅ terpasang |
| — baris huruf kecil | bukan judul (usul Bos, BELUM dikode) | ⏳ |
| — caption Gambar/Tabel, "Sumber:" | bukan judul | ✅ sudah ada |

### Lapis 2 — PROFIL KAMPUS (INI YANG BELUM ADA)

Yang **BEDA antar-kampus** JANGAN di-hardcode — taruh di **file konfigurasi
per kampus**, mis. `profil/kampus-a.yaml`. Pipeline **baca profil**, bukan kode.

```
Kampus baru  =  tambah 1 file profil  (BUKAN ubah kode)
```

**Isi profil kandidat (belum final — dikunci setelah 3 kampus):**
- pola BAB: `^BAB\s+([IVX]+)$` vs `^BAB\s+(\d+)$`
- nama bagian depan (PENDAHULUAN vs BAB I PENDAHULUAN)
- gaya lampiran (LAMPIRAN, KUESIONER, ANGKET, LAMPIRAN 1-11)
- kapitalisasi judul (SEMUA KAPITAL vs Title Case)
- istilah lokal (kuesioner / angket / daftar pertanyaan)

**Cara mengisi profil (sekali per kampus, ~30 menit):**
```
1. Ambil 3 naskah kampus itu
2. Audit seperti malam ini (peta3_jev + saringan + sajian HTML)
3. Catat polanya (apa yang lolos, apa yang salah)
4. Tulis profil/kampus-<nama>.yaml
```

---

## 🛡️ DUA PENGAMAN

### 1. REGRESSION CORPUS
Simpan **output final Asih malam ini sebagai BASELINE**.
Tiap ubah prompt/aturan → uji ulang ke corpus → **kalau skor turun, ketahuan
langsung**. (Pelajaran dari insiden prompt korup / Uji 8.)

**Baseline Asih (09 Okt 2026, md5 `peta3_jev.py` = `f65cd563bd30e87178eefdc913d68929`):**
```
BAB      : 5   (5 asli + 5 sistematika ditandai)
SUB-BAB  : 130
PARAGRAF : 157
biasa    : 199
kandidat : 491
buang    : 720
goyang   : 23
koreksi_label (Aturan 2) : 4   (L000545/559/563/1232)
koreksi_spss   (Aturan 4) : ~7
sistematika    (D1)       : [191,195,199,203,207]
```
Sajian bukti: `SAJI_ASIH_D1.html`

### 2. JANGAN OVERFIT KE ASIH
4 aturan malam ini **bukti dari 1 naskah**. Uji Tesis 78 akan menunjukkan
**mana yang benar-benar umum vs kebetulan cocok di Asih**.

⚠️ **Sudah dicurigai:** aturan ③ `KUESIONER` — kampus lain mungkin pakai
**"ANGKET"** ⇒ kandidat pindah ke Lapis 2 (profil) atau perluasan daftar.

---

## 📋 URUTAN KERJA YANG DISARANKAN BOS

```
1. ✅ Kunci v1 + simpan baseline Asih          (SELESAI 09 Okt)
2. ⏳ Uji Tesis 78  → profil kampus #2
3. ⏳ Uji Disertasi 103 → profil kampus #3
4. ⏳ Setelah 3 kampus stabil → buat deteksi profil OTOMATIS
```

---

## 🔗 KAITAN
- `SOT_PETA_NASKAH_SATU_PINTU_08OKT2026.md` — arsitektur resmi peta
- `peta3_jev.py` — Lapis 1 (kode universal)
- Skill `typesafe-jev` — panduan Jev
- Backup: `_arsip/pre-3aturan-09okt26/`
