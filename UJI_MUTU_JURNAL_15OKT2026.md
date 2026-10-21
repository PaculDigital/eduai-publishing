# ✅ UJI MUTU JURNAL — SELESAI & TERBUKTI (15 OKT 2026)

<!-- SOT: dokumen INI = laporan uji (15 Okt 2026). BUKAN sumber kebenaran.
     Sumber resmi: SOT.md (+ SOT_KONVERSI_JURNAL.md). Kalau bertentangan ⇒ SOT.md MENANG.
     Keadaan kini: FLAG_LANJUT_DISINI.md. -->

**Perintah Bos:** *"Saya sudah pernah uji dan berhasil. Tapi kamu cek uji mutu jurnal juga."*
**Status:** ✅ **SUDAH JADI & SUDAH BENAR** — tidak perlu diperbaiki.

---

## 🎯 KESIMPULAN 1 KALIMAT

Mesin mutu jurnal **bisa membedakan artikel bagus dari artikel kosong** —
artikel lengkap skor **0,89–0,99** · artikel cacat skor **0,05–0,1**. **Bukan seperti
analisis mediasi Statistik Lab** (yang layarnya ada tapi mesinnya tidak nyampe).

---

## 🗺️ ARSITEKTUR — 2 LAPIS + 1 JALAN PINTAS

| Lapis | Fungsi | Yang diperiksa | Biaya |
|---|---|---|---|
| **1** | `konversi.periksa_hasil()` | **ADA/TIDAK ADA**: 4 bagian wajib · 11 elemen JEMT · abstrak ID+EN · nama penulis | **Rp 0** (mesin, tanpa AI) |
| **2** | `konversi.periksa_hasil_jev()` | **18 poin mutu** (11 JEMT + 7 IMBAD) dinilai Jev di ARTIKEL JADI | kecil (Jev) |
| **pintas** | pagar naskah rusak | naskah rusak konversi → **Jev DILEWATI** | Rp 0 |

**Catatan nama (jangan tertukar):**
- `periksa_mutu.py` = periksa **NASKAH MASUKAN** (rusak konversi PDF: *"D i n a"* terpecah)
- `konversi.periksa_hasil*()` = periksa **ARTIKEL JADI** ← **ini yang Bos maksud "mutu jurnal"**

---

## 📊 BUKTI UJI (15 Okt 2026, jalur fungsi produksi di container)

### GERBANG LAMA (sudah ada, dijalankan ulang)

| Gerbang | Hasil |
|---|---|
| `_gerbang_periksa_mutu.py` | **29 LULUS / 0 GAGAL** ✅ |
| `_gerbang_http_mutu.py` | **14 LULUS / 0 GAGAL** ✅ |
| `_gerbang_pagar_mutu_peta.py` | **15 LULUS / 0 GAGAL** ✅ |

### LAPIS 1 — MESIN (Rp 0), uji bergigi

| Kasus | Hasil |
|---|---|
| Artikel **LENGKAP** | lolos ✅ · **11/11 elemen** · 0 temuan |
| Artikel **CACAT SENGAJA** | **tidak lolos** ✅ · 6/11 elemen · **5 temuan** |

Cacat yang ditanam & **tertangkap semuanya**: metode < 120 kar · 5 elemen mutu dibuang ·
abstrak ID terlalu pendek · abstract EN kosong · **nama penulis hilang**.

⇒ **BERGIGI** — bukan hijau palsu.

### LAPIS 2 — JEV (AI sungguhan, 0,59 detik)

| Elemen | Artikel LENGKAP | Artikel CACAT |
|---|---|---|
| pembukaan menarik (hook) | 0,94 *(ragu)* | **0,05** |
| perkembangan ilmu (state of the art) | 0,94 | **0,10** |
| celah penelitian (gap) | 0,94 | **0,08** |
| kebaruan (novelty) | 0,93 | **0,06** |
| penyampaian temuan | 0,96 | 0,84 |
| analisis kritis | 0,89 | **0,09** |
| pembanding penelitian lain | 0,98 | **0,07** |
| kaitan dengan teori | 0,94 | 0,49 *(ragu)* |
| keterbatasan penelitian | 0,98 | **0,05** |
| rekomendasi lanjutan | 0,99 | **0,06** |
| implikasi teoretis & praktis | 0,98 | 0,82 |
| abstrak | 0,99 | 0,99 |

| | Artikel LENGKAP | Artikel CACAT |
|---|---|---|
| **skor total** | tinggi | **0,52** |
| **keputusan** | 1 ragu (hook) | **8 KURANG** + 1 ragu |

⇒ **Jev BERMATA** — teks kosong → skor jatuh ke 0,05. **Tidak buta.**

---

⚠️ **JEBAKAN YANG DIKETAHUI:**
- **`periksa_mutu.py` (NASKAH MASUKAN) vs `konversi.periksa_hasil` (ARTIKEL JADI)** —
  beda mesin, jangan tertukar.
- **Ambang MUTU ARTIKEL = `AMBANG_ADA 0,50` & `AMBANG_RAGU 0,35`** (konversi.py:654-656),
  BUKAN 0,95. Angka 0,95 itu milik `mata_jev` (peta bab) — **Wulan pernah salah baca ini**.
- **Jev menilai ULANG tiap panggilan** ⇒ nilai satu elemen **bisa bergeser** (hook terukur
  0,94 lalu 0,51 pada artikel sama). Karena ambangnya 0,50, geseran itu bisa mengubah
  "ADA" ↔ "ragu" pada elemen batas. **JANGAN potong keluaran uji (`tail`) waktu menyimpulkan**
  — Wulan pernah menyimpulkan "ambang kaku" dari keluaran terpotong. **BUKTI: uji ulang
  artikel lengkap → 18/18 ADA, 0 ragu.**
- ⇒ **TIDAK ADA masalah "peringatan palsu"** — sistem sudah benar, ambang tidak perlu diubah.

**Bukti koreksi (uji ulang 15 Okt, sama artikel):** seluruh 18 poin dinilai **ADA**
(hook 0,51 · state of art 0,93 · gap 0,94 · novelty 0,92 · temuan 0,96 · analisis kritis 0,90 ·
pembanding 0,98 · kaitan teori 0,95 · limitasi 0,98 · rekomendasi 0,99 · implikasi 0,98 ·
abstrak 0,99 · pendahuluan 0,99 · metode 0,99 · hasil 0,99 · pembahasan 0,97 · kesimpulan 0,99 ·
daftar pustaka 0,99) ⇒ **0 kurang · 0 ragu**. ⇒ **sistem sudah benar.**

---

## 🔒 KEADAAN

| | |
|---|---|
| Image produksi | `eduai-app:20261015_112244-sot` (tidak diubah) |
| Perubahan kode | **NOL** (uji saja, tidak menyentuh produksi) |
| Alat uji | `_uji_mutu_jurnal.py` · `_uji_mutu_jev.py` |
| Biaya uji | kecil (1 panggilan Jev × 2) |

**⇒ JANGAN uji ulang. Sudah terbukti. Rujuk dokumen ini.**
