<!-- DRAF (RIWAYAT, sudah dipasang 09 Okt) — SOT: bukan sumber status. Aturan final ada di CATATAN_KEPUTUSAN_PETA3_09OKT2026.md -->

# DRAF ATURAN PRESISI — 3 KOREKSI PETA JEV (08 Okt 2026)

> **Status:** DRAF — BELUM DIPASANG. Menunggu perintah Bos "pasang".
> **Dasar:** vonis Bos atas 13 baris mencurigakan (Asih fid=81).
> **⚠️ CATATAN KRITIS BOS (verbatim):** *">300 karakter hanya boleh dipakai sebagai
> koreksi label — menolak klaim SUB-BAB Jev dan melabel ulang jadi PARAGRAF.
> Jangan dipasang sebagai saringan buang umum! Kalau dipasang mentah sebagai
> 'buang', ratusan paragraf asli ikut terbuang — mengulang bencana Uji 8."*

---

## A. ATURAN 1 — SARINGAN BUANG: baris TABEL (pipa)

**Letak:** `saringan_bersih.py` → `dibuang(s)` (fungsi yang SUDAH ADA).

```python
# ≥2 pipa = PASTI tabel; 1 pipa masih mungkin kalimat biasa, jadi TIDAK dibuang.
# Diketahui sebagai batasan sadar: tabel 2 kolom (1 pipa) LOLOS.
if s.count('|') >= 2:
    return True
```

**Kenapa ≥2 (bukan ≥1):** satu pipa bisa muncul di kalimat biasa
(mis. "a | b" jarang, tapi aman). Dua pipa = struktur tabel.

**Bukti:** menyapu **9 baris** di Asih:
`L000129 · L001078 · L001079 · L001108 · L001117 · L001186 · L001239 · L001756 · L001766`

**Sifat:** DETERMINISTIK · mustahil whack-a-mole · nol risiko (baris pipa tak pernah judul).

---

## B. ATURAN 2 — KOREKSI LABEL: baris panjang yang Jev bilang SUB-BAB

**Letak:** `peta3_jev.py` → `petakan()`, SESUDAH label dirakit (bukan di `dibuang`!).

```python
# ⚠️ CATATAN BOS: ini KOREKSI LABEL, BUKAN saringan buang.
# Paragraf asli sering >300 kar ⇒ kalau DIBUANG = bencana Uji 8.
if label[i] == 'subbab' and len(baris[i].strip()) > 300:
    label[i] = 'paragraf'      # tolak klaim sub-bab, ubah jadi paragraf
```

**Bukti:** memperbaiki **2 baris** di Asih:
`L000563` (856 kar, heteroskedastisitas) · `L001331` (327 kar, koefisien determinasi)

**Sifat:** hanya MENYENTUH label `subbab` ⇒ paragraf yang sudah benar TIDAK tersentuh.
Baris tetap ada (tidak dibuang) ⇒ batas paragraf tidak bergeser.

**⚠️ KEJUJURAN (catatan Bos):** ambang 300 kar hanya menangkap **kasus ekstrem**.
Paragraf PENDEK yang salah label (mis. `L000419` dulu = paragraf 100-an kar) **tetap
tugas SOP Jev** — bukan tugas aturan ini. Disadari & diterima.

---

## C. ATURAN 3 — BUANG: blok LAMPIRAN KUESIONER

**Letak:** `saringan_bersih.py` → `dibuang(s)`.

```python
# Judul lampiran kuesioner (bukan bagian struktur BAB I-V).
if re.match(r'^\s*KUESIONER\b', s, re.I):
    return True
```

**Bukti:** memperbaiki **1 baris** di Asih: `L000985` (154 kar).

**Alasan (sepakat Bos):**
- konsisten dengan kebijakan lampiran yang SUDAH jalan (`LAMPIRAN 1–11`, `DAFTAR LAMPIRAN` sudah dibuang)
- bukan bagian struktur BAB I–V
- isi kuesionernya sendiri = baris tabel (juga dibuang)

---

## D. ATURAN 4 (BARU — temuan Bos) — DEDUPLIKASI JUDUL BAB

**Bos menemukan:** di run terakhir ada **10 label BAB untuk 5 bab yang sebenarnya** —
sebab baris `BAB II TINJAUAN PUSTAKA` di blok **SISTEMATIKA PENULISAN** ikut terlabel
sebagai bab. ⇒ Peta jadi menampilkan bab "kembar".

**Rencana (pilih satu, menunggu putusan Bos):**

**D1 — Tandai khusus (disarankan Wulan):** baris BAB yang isinya **judul bab yang SAMA**
dengan bab lain ⇒ label tetap `bab` tapi beri penanda `asal: 'sistematika'`
(bukan `'jev'`) + `boleh_dipakai_fitur: False`. ⇒ tidak hilang (jujur), tapi fitur
tidak akan salah pakai.

**D2 — Deduplikasi (buang dari bab):** ambil hanya bab **dengan isi terpanjang**
sesudahnya (pola `peta_bab_jev` yang sudah terbukti) ⇒ 5 bab unik. Lebih bersih,
tapi membuang informasi.

**Fakta terukur Asih:** 10 `gabung` = 5 BERJUDUL (`L000000` BAB I+PENDAHULUAN ·
`L000211` BAB II+TINJAUAN PUSTAKA · `L000385` · `L000607` · `L000833`) **= BAB ASLI**
+ 5 POLOS (`L000191`–`L000207`, isinya blok SISTEMATIKA) **= palsu**.
⇒ Pemisahnya **sudah ada**: bab asli punya **judul menyusul**; bab sistematika **tidak**.

**⚠️ BELUM DIPASANG** — menunggu pilihan Bos D1 / D2 / biarkan.

---

## E. EKSPEKTASI (hitungan vonis Bos — harus cocok saat uji)

| | Asih SEBELUM | Asih SESUDAH (harus) |
|---|---|---|
| 🅱️ bab | **5** | **5** (TIDAK BERUBAH ✅) |
| 🔷 subbab | 151 | ~139 (−12) |
| 📄 paragraf | 138 | ~140 (**+2** dari koreksi label) |
| baris tabel jadi sub-bab | 9 | 0 ✅ |
| kuesioner jadi sub-bab | 1 | 0 ✅ |

**Kalau BAB turun ⇒ BATAL, rollback.** Kalau paragraf TURUN banyak ⇒ curiga saringan buang salah.

---

## E. PROTOKOL UJI (urutan wajib — pelajaran hari ini)

```
① Backup           : _arsip/pre-saringan-3-08okt26/
② Pasang 1 aturan   : hanya ATURAN 1 → uji Asih → banding (bab/sub-bab/paragraf/GOYANG)
③ Pasang aturan 2   : → uji Asih → banding
④ Pasang aturan 3   : → uji Asih → banding
⑤ Uji Tesis 78      : banding (subbab 41→~36 · paragraf 77→~79)
⑥ Uji Disertasi 103 : banding (ukur 3 naskah)
⑦ Bos cek sajian    : baru dinyatakan beres
```

**⭐ CATATAN BOS (protokol tambahan — WAJIB):** setiap kali satu aturan dipasang,
**ukur ulang GOYANG**. Perbaikan akurasi TIDAK BOLEH dibayar dengan kenaikan
instabilitas. Tabel banding WAJIB memuat kolom **goyang**:

| Aturan dipasang | bab | subbab | paragraf | **goyang** |
|---|---|---|---|---|
| (awal) | 5 | 151 | 138 | 33 |
| + aturan 1 | ? | ? | ? | **harus ≤ 33** |
| + aturan 2 | ? | ? | ? | **harus ≤** |
| + aturan 3 | ? | ? | ? | **harus ≤** |

Kalau goyang NAIK ⇒ **pertimbangkan rollback** aturan itu.

**Aturan:** 1 aturan = 1 uji = 1 banding. **JANGAN borongan.** Kalau ada yang turun ⇒ rollback.

**Ambang batal:** bab ≠ 5 di Asih ⇒ LANGSUNG rollback ke backup.

---

## F. YANG TIDAK DIKERJAKAN (sengaja ditolak)

```
⛔ "Buang semua baris >300 kar"         → BENcana Uji 8 (ratusan paragraf asli hilang)
⛔ "Buang baris >130 kar"               → SAMA (aturan lama `_subbab_palsu` yang salah)
⛔ regex mengenali "BAB IV HASIL DAN PEMBAHASAN" di 1 baris
   → TERBUKTI RUSAK (menangkap blok SISTEMATIKA PENULISAN, 8 Okt)
⛔ pakai `_subbab_palsu()` untuk menyaring baris → makan 922 baris (76%) Asih
```

## G. SISA MASALAH (di luar 3 aturan — jujur)

```
· butir daftar ("1. Pengenalan masalah", "b. Sosial") masih bisa jadi sub-bab di Tesis 78
  ⇒ percobaan 8 Okt (fakta "baris pendek beruntun") GAGAL — Jev tak terpengaruh
· header tabel yang TIDAK pakai pipa (mis. "Tabel 1.1 Kode Indikator") — belum diukur
· naskah Inggris (CHAPTER/Figure/Table) — belum ada set pola
· varian "BAB 1" (angka) — belum diuji (regex aman sudah terima romawi saja)
```
