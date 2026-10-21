# PENUTUP UJI K5 — APA YANG UMUM, APA YANG CUMA 1 NASKAH (09 Okt 2026)

> 🔒 **URUTAN RESMI = `URUTAN_RESMI_PETA_NASKAH_TERKUNCI.md`** — surveyor → hakim → mesin → AI.
> Dokumen ini RIWAYAT uji, BUKAN acuan urutan.

> **Vonis Bos:** *"Saya mau akhiri uji-uji ini. Hasil uji ini tidak bisa buat naskah
> general. Terlalu detail cocok untuk 1 naskah saja."*
> **Keputusan Bos: A** — tutup rapi & simpan temuan; K5 ditandai JANGAN dipakai
> produksi sampai ada arahan baru.

---

## 1. KENAPA DIHENTIKAN (Bos benar — ini buktinya, bukan sekadar patuh)

```
Uji malam ini menyetel K5 dengan 12-16 kasus BUATAN dari SATU naskah (fid=115).
⇒ "cocok untuk 1 naskah saja" = TEPAT, dan buktinya ada di catatan Wulan sendiri:

   · '3. Tinjauan Literatur' → 0,63 di Asih · 0,12/0,67 di fid=115
     ⇒ naskah beda = jawaban beda ⇒ setelan tidak menyeberang naskah
   · K5 12/12 di set latih → ~10/16 di set uji ⇒ setelan terlalu halus
   · 4× 'Informan' tak pernah selesai walau sudah diberi 3 definisi tambahan
     ⇒ definisi buatan manusia TIDAK bisa menutup semua bentuk naskah

⇒ Uji malam ini jatuh ke perangkap yang Bos larang sejak awal:
   MENYETEL KALIMAT JEV PER-KASUS.

📌 Pengingat dari memory kita sendiri (Bos sudah bilang dari dulu):
   · "BATAS: 'JUTAAN naskah' ⇒ solusi yang butuh koding per naskah = SALAH.
      Arah: SATPAM sebelum AI bekerja — keputusan BERTIPE + confidence,
      RAGU → tanya manusia."
   · "AI menulis kata, KODE menulis angka DAN POLA."
   · Jev = MATA yang memberi tahu bentuk — bukan dinilai dengan kalimat
     criteria yang disetel per-kasus.
```

## 2. YANG TERBUKTI **UMUM** (berlaku lintas naskah — SIMPAN)

| # | Temuan | Bukti |
|---|---|---|
| **U1** | **Ada 3 penggaris berbeda** membaca naskah: MENTAH (`split('\n')`), SUSUN (`peta3.susun()['baris']`), BLOK (`konversi._pecah_blok()`) | fid=115: 9.042 / 8.755 / blok; fid=81: 2.224 / 1.874; fid=104: 26.065 / 25.055 — **indeks TIDAK bisa ditukar** |
| **U2** | **Salah penggaris = bug "baris salah diukur"** | c04: harness ambil indeks 8.337 (daftar isi) padahal judul asli di 8.050 ⇒ skor palsu 0,12 |
| **U3** | **Jev turun & goyang saat bahan bercampur** (perhatian terbagi) | 1 kandidat = **0,71 stabil (5×)** · 2+ kandidat = **~0,52 goyang** · 16 = 0,49 |
| **U4** | **Penular tidak spesifik** — bahkan judul asli lain menularkan | +'4. Threats (Ancaman)' (judul) → 0,54; +'2020' (angka) → 0,50 |
| **U5** | **Pemisah tegas MEMPERBURUK** | P1 bernomor 0,34 · P2 terpagar 0,38 · P3 kosong 0,40 (polos 0,54) |
| **U6** | **Uji wajib baca lewat `susun()`** | harness lama (mentah) mengukur baris daftar isi ⇒ angka uji tidak sah |
| **U7** | **criteria panjang itu PERLU**, bukan hiasan | criteria panjang 0,57-0,80 vs dipendekkan 0,25 |
| **U8** | **`petakan()` mengembalikan DICT** `{baris,kand,gabung,buang,awal,akhir}`, bukan list | KeyError: 0 saat Wulan salah pakai |
| **U9** | **Pass-1 stitch SUDAH ADA** di `konversi.py:874 _pecah_blok` + `_kandidat_sambung` (852); terukur 23→5 panggilan | dipakai produksi konversi (konversi.py:1024), **BELUM** dipakai peta3_jev |

## 3. YANG **CUMA 1 NASKAH** (JANGAN dipercaya sebagai aturan)

```
❌ K5 12/12 (set latih fid=115+Asih) — overfit, ~10/16 di set uji segar
❌ K5-BARU vs K5-KETAT (11/16 vs 10/16) — dari 16 kasus satu naskah
❌ Definisi "anak bernomor" (putusan Bos ③) — 4× Informan TETAP gagal (0,04-0,07)
   ⇒ Jev menilai dari ISI baris, bukan dari keadaan sekitar
❌ Ambang 0,60 / 0,30 — disetel dari 18 kandidat uji; goyang ±4 kandidat/putaran
❌ c07 '4. Threats' 0,45-0,47 — tidak konsisten dengan 0,63 di uji lain
```

## 4. STATUS KODE (apa adanya — tidak ada yang disembunyikan)

```
✅ app/jev.py (JALAN TOL JEV) — TIDAK disentuh, gerbang 30 LULUS / 0 GAGAL
✅ app/_gerbang_jev_jalantol.py — 8 asersi (E1-E5 criteria + F1-F4 K5/pemetaan)
⚠️ app/hakim_peta.py — K5 TERPASANG + ambang 0,60/0,30 + DEMOSI_CURIGA.md
   ⇒ 🚩 DITANDAI: SETELAN 1-NASKAH — JANGAN dipakai produksi sampai arahan Bos
   ⇒ Wulan TIDAK mencabut (butuh izin eksplisit Bos)

📌 Pemakaian hakim_peta di produksi HARI INI: TIDAK ADA (baru dipakai uji).
   ⇒ risiko nol untuk pengguna. Statusnya "terpasang tapi menganggur".
```

## 5. YANG TETAP BERHARGA UNTUK PEKERJAAN BERIKUTNYA

```
① U1-U3 (tiga penggaris, perhatian terbagi) = TEMUAN ARSITEKTUR, bukan setelan
   ⇒ masuk ke pekerjaan stitch / satpam sebelum AI
② Pass-1 stitch perlu disambungkan ke peta3 (satu penggaris) — masuk #2
③ Uji ke depan: WAJIB ≥3 naskah berbeda + banyak kasus, JANGAN 1 naskah
④ Setiap angka uji harus menyebut: naskah apa, penggaris apa, berapa kandidat
```

## 6. ARSIP & KEBERSIHAN

```
Backup: _arsip/pre-md-09okt26/ (skrip uji + laporan)
Container dibersihkan dari skrip selidik sementara
Berkas laporan sesi ini (semua .md, sesuai perintah Bos "jangan json"):
   SELIDIK_C04_09OKT2026.md (sudah dikoreksi)
   SELIDIK_C_DUA_DAFTAR_BARIS_09OKT2026.md
   TEMUAN_KEKABURAN_MENULAR_09OKT2026.md
   HASIL_UKUR_BATAS_KANDIDAT_09OKT2026.md
   HASIL_UJI_PEMISAH_KANDIDAT_09OKT2026.md
   HASIL_UKUR_ULANG_19KASUS_09OKT2026.md
   AUDIT_7_BARIS_DEMOSI_09OKT2026.md
   DEFINISI_BARU_PUTUSAN_BOS_09OKT2026.md
   HASIL_VALIDASI_SILANG_K5_09OKT2026.md
```

## 7. TUNGGU ARAHAN BOS

```
Uji per-naskah DIHENTIKAN. Wulan menunggu arah umum dari Bos.
Sampai itu datang: tidak ada uji baru, tidak ada penyetelan K5,
tidak ada perubahan kode produksi.
```
