# 🔍 HASIL PENYELIDIKAN — PETA NASKAH (14 Okt 2026)

> **Perintah Bos:** *"Saya tidak tahu, harus pilih apa. Kamu selidiki yang terbaik
> dan sesuai catatan, dokumentasi."*
>
> **Cara Wulan:** baca ULANG 4 dokumen resmi (SOT peta 08 Okt · URUTAN_RESMI 09 Okt ·
> CATATAN_KEPUTUSAN_PETA3 09 Okt · RANCANGAN_HAKIM v2 09 Okt) + **PENUTUP_UJI_K5 09 Okt**
> + periksa kode nyata. **NOL kode disentuh.**

---

## 🔴 TEMUAN 1 — SATU DOKUMEN YANG MENGUBAH RENCANA (wajib Bos tahu)

**`PENUTUP_UJI_K5_09OKT2026.md`** — vonis Bos 09 Okt (verbatim):
> *"Saya mau akhiri uji-uji ini. Hasil uji ini tidak bisa buat naskah general.
> Terlalu detail cocok untuk 1 naskah saja."*

**Keputusan Bos waktu itu: A — tutup rapi; K5 ditandai JANGAN dipakai produksi.**

Artinya: **`app/hakim_peta.py` sekarang masih membawa K5 + ambang 0,60/0,30 yang
Bos tandai JANGAN dipakai produksi.** Di dalam kode pun sudah ada tanda
`🚩 SETELAN 1-NASKAH` (baris 80 & 183).

⇒ **Kalau Wulan sambung hakim apa adanya, Wulan menyambung setelan yang Bos
sendiri sudah tolak.** Ini JANGAN dilakukan.

---

## 🔴 TEMUAN 2 — `peta3_jev.py` BELUM "MATANG" (temuan arsitektur U1-U9)

Dari PENUTUP_UJI_K5 §2 — 9 temuan yang berlaku **UMUM** (bukan setelan 1 naskah).
Yang paling penting untuk rencana ini:

```
U1  ADA 3 PENGGARIS berbeda membaca naskah: MENTAH · SUSUN · BLOK
    ⇒ INDEKS TIDAK BISA DITUKAR (ini akar "baris salah diukur")
U2  Salah penggaris = bug nyata (c04: ambil baris daftar isi, bukan judul)
U3  Jev TURUN & GOYANG kalau bahan bercampur (1 kandidat 0,71 · 2+ kandidat 0,52)
U6  Uji WAJIB baca lewat `susun()`, bukan mentah
U9  PASS-1 STITCH SUDAH ADA di konversi.py (_pecah_blok, 23→5 panggilan)
    ✅ DIPAKAI produksi konversi
    ❌ BELUM dipakai peta3_jev   ← Wulan verifikasi: grep = KOSONG
```

⇒ **Peta3_jev belum memakai penggaris yang sama dengan konversi.** Kalau
disambung sekarang, **dua fitur bisa memotong naskah di tempat berbeda**.

---

## 🔴 TEMUAN 3 — HAKIM BELUM TERBUKTI BERGUNA (kill-switch belum dijawab)

Rancangan Hakim §11 menetapkan **kill-switch**: *"Y = X ⇒ JANGAN dipasang"*
(hakim tidak menurunkan sub-bab palsu ⇒ jangan dipasang).

**Statusnya: BELUM DIUKUR.** Dua uji kunci belum ada:
```
U5  metrik X→Y (baseline sub-bab palsu) — dokumen sendiri bilang
    "X belum boleh dikunci"
U4b kalibrasi ambang — 0,85 terbukti salah tempat (rata-rata conf Jev 0,839)
```

Dan §7c sudah **membubarkan ambang** dengan putusan Bos: *"Ini bukan masalah
kalibrasi; ini masalah salah alat ukur."*

⚠️ **Jujur:** kalau Wulan sambung hakim sekarang, hakim **belum punya alat ukur
yang sah** untuk membuktikan dirinya berguna.

---

## ✅ TEMUAN 4 — YANG SUDAH SIAP (kabar baik)

```
✅ peta3_jev.py    SUDAH keluarkan `p` per label (S1) — baris 337
✅ hakim_peta.py   SUDAH dirancang menilai PETA SURVEYOR (T1) — baris 5, 117-123
✅ peta_jembatan   GERBANG 16/0 LULUS (jembatan siap)
✅ hakim_peta      `p` BUKAN input keputusan (pagar U4b dipatuhi, F4 lulus)
✅ Gerbang Jalantol 28/0 (2 GAGAL = laporan .md, bukan kerusakan kode)
✅ Jalur biaya     satu pintu: satpam → jev.tanya (terbukti)
```

---

## 🎯 KESIMPULAN PENYELIDIKAN — APA YANG TERBAIK

Berdasarkan **dokumen**, urutan "peta3_jev → hakim → mesin → AI" **tetap benar**
(Terkunci 09 Okt). Bos tidak salah.

**TAPI** kenyataan waktu menunjukkan **BELUM MATANG untuk disambung utuh**:

| Yang Bos minta | Status sebenarnya | Boleh disambung? |
|---|---|---|
| peta3_jev mengganti peta_halus | mesin unggul ✅, tapi **belum satu penggaris** dgn konversi (U9) | ⚠️ perlu stitch dulu |
| hakim memperjelas fokus | **setelan K5 = DITOLAK Bos** · kill-switch belum diukur | ❌ **JANGAN apa adanya** |
| fallback peta lama | peta_halus masih ada ✅ | ✅ aman |

⇒ **Yang terbaik = jangan sambung utuh sekarang.** Kerjakan **prasyarat** dulu.

---

## 📋 URUTAN YANG WULAN SARANKAN (dari dokumen, bukan opini)

```
TAHAP 0 (prasyarat — di JALUR UJI, bukan produksi)
  0a. S1 sudah ada ✅ — pastikan `p` diuji terbaca (1 naskah, 1 perintah)
  0b. U9: sambungkan PASS-1 STITCH ke peta3_jev → SATU PENGGARIS
      (dokumen bilang ini "masuk #2" — pekerjaan berikutnya)
  0c. Ukur U5 (X = baseline sub-bab palsu) lewat JALUR RESMI, ≥3 naskah
      ⚠️ JANGAN skrip host (pelajaran fid=112 — angka lama TIDAK VALID)

TAHAP 1 (sambung surveyor — risiko sedang, produksi berubah)
  1a. peta3_jev jadi MODUL (bukan skrip CLI) — wajib, sudah Wulan tunjukkan
  1b. Rute /v1/peta/* → surveyor + FALLBACK (peta lama) + JEJAK
      ⇒ peta_halus TETAP ADA (putusan Bos #4)
  1c. Uji regresi: Asih vs BASELINE_PETA3.json (alat SUDAH ADA)

TAHAP 2 (hakim — BARU boleh sesudah 0c terbukti berguna)
  2a. Buang K5 + ambang (atau matikan) — sesuai putusan Bos 09 Okt
  2b. Pakai §7c: curiga = KODE deterministik · ragu = vonis hakim · `p` = tampilan
  2c. Uji kill-switch: Y < X baru dipasang
  2d. Pagar H1/P1-P6 dipertahankan

TAHAP 3 (section_state + tombol layar)
```

---

## ❓ 1 PERTANYAAN SAJA YANG WULAN BUTUH DARI BOS

Wulan **tidak** minta Bos pilih A/B/C lagi. Wulan cuma butuh **1 hal**:

> **Bos, `peta3_jev` sekarang sudah cukup baik menurut Bos (Bos bilang sudah
> uji sendiri). Kalau begitu — apakah Wulan langsung SAMBUNG peta3_jev
> (surveyor) saja DULU, dan HAKIM menyusul setelah prasyaratnya beres?**

Alasannya: menyambung surveyor **sendiri** = 1 lapis core (risiko sedang).
Menyambung surveyor **+ hakim sekaligus** = 2 lapis, dan hakim masih membawa
setelan K5 yang Bos tolak.

**Saran Wulan (kalau Bos setuju):**
```
SAMBUNG SURVEYOR DULU (peta3_jev + fallback + jejak)
HAKIM MENYUSUL setelah: stitch (U9) → baseline X (U5) → buang K5
```
