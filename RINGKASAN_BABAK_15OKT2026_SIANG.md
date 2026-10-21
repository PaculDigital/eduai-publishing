# 📌 RINGKASAN BABAK — 15 OKT 2026 (siang)

<!-- SOT: dokumen INI = ringkasan babak kerja (15 Okt 2026 siang). BUKAN sumber
     kebenaran. Sumber resmi tetap: SOT.md (+ SOT_KONVERSI_JURNAL.md). Kalau
     bertentangan dengan SOT.md ⇒ SOT.md MENANG. Keadaan kini: FLAG_LANJUT_DISINI.md. -->

**Untuk:** Bos · **Oleh:** Wulan · **Status:** SELESAI & TERBUKTI DENGAN AI SUNGGUHAN

---

## 🎯 APA YANG DIKERJAKAN HARI INI (4 hal)

| # | Pekerjaan | Bukti | Status |
|---|---|---|---|
| 1 | **Gerbang setelan produksi** (`_gerbang_setelan_produksi.py`) | 8 pemeriksa · menolak deploy | ✅ LIVE |
| 2 | **Uji mutu revisi AI** (potongan vs penuh) | PENUH 3,83 vs POTONG 4,00 | ✅ Selesai |
| 3 | **Pagar konteks asisten** (`_boleh_konteks` → asisten) | 30/0 · uji hidup 71% vs 0% | ✅ LIVE |
| 4 | **Uji hulu-hilir AI sungguhan** | 8 usulan nyata · 8/8 kutipan asli | ✅ Lulus |

---

## 1. GERBANG SETELAN PRODUKSI — MENGAPA PENTING

**Akar masalah nyata:** alat ukur Wulan (`_hakim_mentah.py`, dibuat 24 Sep) **ketinggalan
zaman** — tidak punya `enable_thinking: False` yang **sudah dipasang di produksi 29 Sep**.
Akibatnya: model **berpikir** → jatah token habis → jawaban **kosong** → Wulan **hampir
melapor "produksi cacat"**.

**Bos sudah mengingatkan:** *"Kan pernah di setting matikan reasoning, pernah diuji juga
kok balik lagi?"* — **Bos BENAR.** Produksi tidak pernah balik; **alat uji Wulan** yang
ketinggalan.

**Obat:** gerbang `_gerbang_setelan_produksi.py` (8 pemeriksa, **ikut menolak deploy**
lewat `scripts/periksa_kode.sh`). **Terbukti bergigi** — candik disuntik → deploy ditolak.

---

## 2. UJI MUTU REVISI (potongan vs penuh)

Alat ukur **diperbaiki dulu** (impor setelan dari `app.config`), **baru** mengukur:

| Naskah | PENUH | POTONG | Pemenang |
|---|---|---|---|
| Disertasi | 4,00 | **4,25** | potong |
| Olahraga | **4,75** | 4,00 | penuh |
| Fazri | 2,75 | **3,75** | potong |
| **Rata-rata** | 3,83 | **4,00** | **praktis sama** |

⚠️ **Juri buta belum sah** — PENUH selalu keluar sebagai "Hasil 1" (bias urutan).
Perlu **acak + 2 juri**.

---

## 3. PAGAR KONTEKS ASISTEN — TERBUKTI DENGAN AI SUNGGUHAN

**Masalahnya:** asisten **selalu** kirim 1 bab. Kalau pembimbing bilang *"ubah alur
seluruh naskah"*, 1 bab **tidak cukup**.

**Perbaikannya = PEMASANGAN**, bukan mesin baru:
- `_catatan_terbaru()` baca catatan pembimbing (tabel **sudah ada**)
- `_boleh_potong()` **memanggil** `ai._boleh_konteks()` — aturan **tidak disalin**

**Bukti dari log produksi sendiri (2 operasi AI nyata, ~Rp 4):**

```
catatan "perbaiki ejaan"
  [asisten] konteks DIPAKAI: bagian ke-1/5 (BAB 1) → kirim 9.144 kar (dari 31.140) | hemat 71%

catatan "ubah alur seluruh naskah"
  [ai]      konteks tetangga DILEWATI: pengali > 1 (intent 'REVISI')
  [asisten] PAGAR: permintaan menyeluruh (dari 1 catatan) → kirim naskah UTUH 31140 kar
```

---

## 4. UJI HULU-HILIR — AI MENDAPATI CACAT NYATA

Naskah uji **berisi kesalahan sengaja** → AI beri **8 usulan nyata**:

| Cacat yang ditanam | Kata AI |
|---|---|
| sig **0,023** tapi disimpulkan **H0 diterima** | *"0,023 lebih kecil dari 0,05, semestinya **H0 ditolak** dan Ha diterima"* |
| **120 sampel dari 120 populasi** disebut *purposive* | *"teknik yang lebih tepat adalah **sampling jenuh**"* |
| Tujuan **"self efficacy"** vs rumusan **"motivasi"** | ditandai *"mohon disesuaikan"* |

**8/8 kutipan ADA di naskah asli** — AI **tidak mengarang** (anti-karangan terbukti).

---

## 🙏 YANG WULAN AKUI (jujur)

**1. Hampir melapor "produksi cacat"** — padahal **alat ukur Wulan** yang basi.
**2. Hampir melapor "AI mengarang kutipan"** (5/8) — padahal **uji Wulan** tidak
merapikan spasi (naskah punya ENTER, AI salin jadi SPASI) ⇒ setelah dirapikan 8/8.
**3. Menulis kalimat uji dari ingatan** — *"perbaiki alur"* bukan pemicu resmi.
**4. Lupa menyalin DB** ke folder uji ⇒ tabel `setelan` hilang ⇒ hasil tidak sah.
**5. Kehilangan jejak berkas** `_naskah_uji.txt` ⇒ ulang dengan impor dari sumber.

**Pelajaran tertulis:** `references/alat-uji-wajib-setelan-produksi-15okt2026.md`
(skill `test-gate-design`) + catatan di `FLAG_LANJUT_DISINI.md`.

---

## 🔒 KEADAAN AKHIR

| | |
|---|---|
| Image produksi | `eduai-app:20261015_112244-sot` (Up) |
| Titik mundur | `eduai-app:cadangan-pra-pagar2` |
| Backup DB | `_arsip/pra-sot/20261015_112244-sot` |
| Gerbang | 30/0 · 76/0 · 15/0 · deploy LULUS |
| SOT | SELARAS (0 masalah) |
| Produksi | `/` 200 · `/health` 200 |
| Disk | 4,2 GB sisa |

---

## ⬜ LANJUTAN (utang)

1. **Juri buta belum sah** — perlu **acak urutan + 2 juri**
2. **Bab otomatis dari komentar** (12 rekomendasi `/peta/mulai`)
3. Kalimat layar "peta pakai mode hemat"
4. Satukan **6 penulis romawi** (SEPAKAT I–X, beda jangkauan)
5. Disk VPS 94% penuh (sisa 4,2 GB)
