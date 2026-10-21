# SOT PETA NASKAH — SATU PINTU (08 Okt 2026)

> **Menggantikan** (sudah dipindah ke `_arsip/pre-rapi-peta-08okt26-cara-lama/`):
> `HASIL_UKUR_PETA_JEV_08OKT2026.md` · `HASIL_UKUR_PETA_HALUS_08OKT2026.md` ·
> `RANGKUMAN_UTUH_PETA_NASKAH_JEV_08OKT2026.md` · `HASIL_UJI_PETA_3_TINGKAT_08OKT2026.md`
> **Baca dokumen INI saja.** Cara lama sudah diarsipkan agar tidak membingungkan.

---

## 1. APA YANG SEDANG DIBANGUN

Peta naskah **3 tingkat sekaligus** (BAB + SUB-BAB + PARAGRAF) dalam **1 panggilan Jev**,
dipakai semua fitur EduAi (kolaborasi, revisi, konversi jurnal, rujukan).

**Peran (TERKUNCI):**
```
KODE   : pola DETERMINISTIK (caption, "Sumber:", daftar isi, BAB I-V) — gratis, 100%
JEV    : penilaian AMBIGU (awal paragraf? sub-bab?) — 1 panggilan, banyak pertanyaan
MESIN  : verifikasi DOI (Crossref), hitung, rakit
```
⚠️ Jev **TIDAK** menilai MUTU tulisan (bagus/tidak) — itu terbukti GAGAL.
Jev hanya **BENTUK/STRUKTUR/KEBERADAAN**.

---

## 2. SKRIP RESMI (SATU SAJA)

| Berkas | Isi |
|---|---|
| **`peta3_jev.py`** | **SKRIP RESMI.** `petakan(fid, awal, akhir, putaran)` → peta 3 tingkat |
| `saringan_bersih.py` | saringan kandidat (dipakai `peta3_jev.py`) |
| `_audit_per_aturan.py` | **WAJIB** dijalankan tiap naskah baru: hitung apa yang DIMAKAN tiap aturan |
| `_saji_asih_utuh.py` | sajian 2 kolom untuk diperiksa Bos |

Cara pakai:
```bash
python3 peta3_jev.py <fid> <awal> <akhir> [judul] [baris_sorot...]
```
⚠️ Di dalam container: `docker cp peta3_jev.py eduai-app:/app/` lalu `docker exec -w /app …`

---

## 3. CARA YANG TERBUKTI (JANGAN DIUBAH TANPA UJI)

```
1. KODE : buang_daftar_isi() RESMI (app/state.py:478) → halaman awal + daftar isi
2. KODE : saringan_bersih.dibuang() — 5 aturan:
          · _PEMBUJUANG  : penanda daftar / Sumber: / Keterangan: / LAMPIRAN
          · _TITIK_ISI   : daftar isi ber-titik-titik
          · POLA_MARKER  : [[GAMBAR-7: …]] penanda teknis
          · POLA_SUMBER  : "Sumber: …" (caption)
          · POLA_CAPTION : HANYA kalau PENDEK (≤70 kar)
            ⛔ JANGAN buang kalau panjang — itu paragraf yang MENYEBUT gambar
               (FAKTA: caption asli 23/62/64 kar · paragraf asli 389/556 kar)
3. KODE : BAB dilabeli DI KODE (regex), TIDAK lewat Jev. Nol biaya, 100% akurat.
4. JEV  : 1 panggilan. Tiap kandidat 1 pertanyaan **choice** 4 pilihan
          (bab / subbab / paragraf / biasa).
5. KODE : rakit. Goyang ⇒ label 'biasa' (AMAN: ragu jangan ditandai).
```

### ⚠️ JENDELA WAJIB "APA ADANYA"
Bahan ke Jev = **baris j-1 · j · j+1 APA ADANYA, TERMASUK BARIS KOSONG**.
```
✅ BENAR : sebelum=L000349| (kosong) · tengah=L000350| BAB I · sesudah=L000351| (kosong)
❌ SALAH : sebelum=L000344 "ABSTRAK" · tengah=L000350 "BAB I" · sesudah=L000352 "PENDAHULUAN"
⇒ UJI 19 AMBRUK total (18%) karena Wulan membuang baris kosong.
⇒ Baris kosong = INFORMASI ("berdiri sendiri" = judul). JANGAN dibuang dari jendela.
```

### ⚠️ GELOMBANG (batas bahan)
```
1 panggilan maksimal: BATAS_TANYA=120 · BATAS_KAR=18.000
(batas aman terukur: 156 tanya / 20.622 kar)
Naskah besar ⇒ dipecah gelombang. Tiap gelombang 1 panggilan Jev.
```

---

## 4. ⛔ DILARANG (SEMUA TERBUKTI SALAH)

| Larangan | Bukti |
|---|---|
| **`state._subbab_palsu()` untuk MENYARING baris** | makan **922 baris (76%)** Asih — termasuk **10 judul BAB** + **274 paragraf asli**. Fungsi itu untuk menyaring JUDUL SUB-BAB (butuh `^[A-Z][a-z]{2,}` ⇒ "BAB I" & paragraf panjang wajar dianggap palsu). |
| Membuang baris kosong dari jendela | UJI 19 ambruk 90% → 18% |
| Kirim FAKTA HITUNGAN panjang isi (peta halus) | v9: 1.3 & 1.4 terlewat (p 0,63/0,58) |
| Kalimat BERLARANGAN ("bukan paragraf…") | peta bab: 0,844 → 0,32 |
| Baca `abs(2p-1)`; baca `p` LANGSUNG | Wulan salah baca di v7 |
| Regex untuk MENGENALI bentuk naskah | tak sanggup ribuan naskah (Bos marah 08 Okt) |
| Menyimpitkan bahan sampai Jev buta lalu menyalahkan Jev | — |
| Menganggap 503 = batas tetap | UJI 9: 156 pertanyaan BERHASIL setelah jeda |

---

## 5. ⚠️ PELAJARAN WAJIB: UKUR **RECALL**, BUKAN CUMA PRECISION

**UJI 21 mengukur precision** (32/32 yang dibuang memang layak dibuang) ✅
**TIDAK mengukur recall** (apa yang SEHARUSNYA dibuang tapi lolos / apa yang DIBUANG padahal berharga) ❌
⇒ Akibatnya: 1.003 dari 1.221 baris dibuang (82%) dan **tidak ada yang tahu**.

**KEBIASAAN BARU (WAJIB):** setiap naskah/template baru ⇒ jalankan
`_audit_per_aturan.py` → periksa **tiap aturan, berapa baris dimakan, ada paragraf asli (>80 kar) yang ikut?**

---

## 6. HASIL TERUKUR

### Asih (fid=81, 2.224 baris / 159.909 kar) — SELURUH NASKAH

| | SEBELUM (salah pakai `_subbab_palsu`) | **SESUDAH (saringan bersih)** |
|---|---|---|
| dibuang kode | **1.003 (82%)** — termasuk 10 judul BAB + 283 paragraf asli | **182 (15%)**, nol mencurigakan ✅ |
| 🅱️ label BAB | 2 (tebakan) | **5** — semua benar ✅ |
| 📄 paragraf | 26 | **143** ✅ |
| kandidat ke Jev | 218 | **1.029** ✅ |
| goyang | 7 (3,2%) | 31 (3,0%) ✅ |
| waktu | — | 0,7–1,0 dtk/panggilan · 0 gagal |

**Bos verifikasi:** *"— perbaikannya bekerja."*

### Naskah lain (dari cara RESMI sebelumnya — peta bab)
```
DISERTASI S3 415.284 kar → 5/5 bab, yakin 0,64–0,88 ✅ (peta lama regex: 0 dari 5 ❌)
TESIS S2     93.818 kar → 3/3 bab, yakin 0,84–0,86 ✅
SKRIPSI Asih 159.909 kar → 5/5 bab, yakin 0,80–0,88 ✅
```

---

## 7. ⚠️ SISA MASALAH (JUJUR — BELUM BERES)

```
1. Goyang 31 (3,0%) di Asih seluruh naskah.
   Sebaran: ('biasa','paragraf') 20 · ('biasa','subbab') 7 · ('paragraf','subbab') 4
   ⇒ TIDAK ADA goyang bab⇔subbab ⇒ struktur BAB AMAN ✅
   ⇒ 65% cuma soal "awal paragraf atau bukan" (ambigu, dampak kecil)
2. L000028 "Temuan tersebut memperlihatkan…" → 'biasa' padahal harusnya 📄
   (salah satu dari 31 goyang; Bos sudah tunjuk)
3. L000129 "Kode (Indikator) | Setuju & Sangat Setuju | Pers…" → masih 🔷
   ⇒ header tabel kuesioner (pipa `|`) belum ada penyaringnya
4. Celah regex (terukur 08 Okt, Bos tunjuk):
   ✅ "BAB I" · "BAB V" · "BAB VI" cocok
   ❌ "BAB 1" / "BAB 2" (angka) TIDAK cocok
   ❌ "BAB IV PENDAHULUAN" (judul nempel) TIDAK cocok
5. Belum masuk app (peta_halus_jev.py sudah diarsipkan; peta3_jev.py masih skrip root)
6. Belum uji: Tesis 78 utuh · Disertasi utuh · naskah Inggris
7. Bug lama: catatan_ai.py:151-152 `b.get('mulai', 0)` padahal petakan() tak keluarkan 'mulai'
8. section_state belum diisi peta 3 tingkat
```

---

## 8. YANG HARUS DIJAGA SAAT GENERAL (saran Bos, 08 Okt)

```
1. VARIAN PENOMORAN : "BAB 1" (angka) vs "BAB I" (romawi) · ada yang sampai BAB VI
2. HALAMAN DEPAN   : KATA PENGANTAR / LEMBAR PENGESAHAN / DAFTAR ISI-TABEL-GAMBAR
                     ⇒ tentukan kebijakan KONSISTEN (sekarang cuma DAFTAR LAMPIRAN)
3. BAHASA          : pola ini INDONESIA-spesifik ⇒ naskah Inggris butuh set sendiri
                     ("CHAPTER", "Figure", "Table", "Source:", "Appendix")
4. PAKET UJI       : 3–5 naskah dari kampus/template BEDA · audit recall tiap naskah
```

---

## 9. KEPUTUSAN TERKUNCI (08 Okt)

```
① Kirim ke AI    = potongan sub-bab + PETA + judul bab induk (Cara C MENANG)
② Peta           = SATU gabungan (1 panggilan Jev)
③ Presisi        = sampai PARAGRAF
④ Rujukan        → daftar pustaka · KUTIPAN → paragraf
⑤ Rujukan baru   → cek DOI dulu (audit_doi, Crossref — BUKAN Jev).
                   AI WAJIB diberi tahu: "cari artikel WAJIB ber-DOI"
                   supaya tidak 2× kerja (koreksi Bos)
⑥ JEV = MENUNJUK · AI = MENULIS · MESIN = VERIFIKASI DOI
⑦ Biaya Jev DITANGGUNG APLIKASI/BOS (fact 257)
```

---

## 10. PINTU MASUK LAIN

- `PANDUAN_PAKAI_JEV.md` §7b/§7c/§9 — panduan pemakaian
- Skill `typesafe-jev` → `references/peta-bab-terbukti.md`, `peta-halus-terbukti.md`,
  `cookbook-structure-recovery.md`
- `_arsip/pre-rapi-peta-08okt26-cara-lama/` — cara LAMA (JANGAN dipakai, hanya arkeologi)
