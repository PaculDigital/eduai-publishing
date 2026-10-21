<!-- LAPORAN (RIWAYAT) — SOT: bukan sumber status. Status ada di SOT.md §SESI TERAKHIR -->
# UJI P — POLA PENULISAN: HASIL + RENCANA
### 09 Okt 2026 · Perintah Bos: "lakuan uji P dan laporkan berupa file lengkap dengan keterangan dan langkah rencana"

---

## 1. APA YANG BOS MINTA

> *"Harus ada yang melihat pola sekitarnya seperti beretangga juga **tapi bukan makna**,
> lebih ke **pola penulisan yang sesuai**. Apakah paragraf, butir, sub bab dll.
> Jadi **tidak aneh polanya**. Dan juga **ikuti pembimbing jika minta pola tertentu**."*

**Keputusan Bos: OPSI C** — peta = default, pembimbing boleh menimpa.

**Yang harus dijawab lebih dulu:** *apakah Jev sanggup mengenali pola penulisan?*
Kalau tidak → seluruh rencana runtuh. **Maka UJI P wajib jalan sebelum koding.**

---

## 2. HASIL UJI P — GAGAL (jujur)

| Percobaan | Cara | Hasil |
|---|---|---|
| **P-1** | jendela **3 baris**, 4 pilihan pola | **4/12 (33%)** |
| **P-2** | jendela **5 baris**, 4 pilihan pola | **2/12 (17%)** |

Ambang kesepakatan: **≥80% = jalan · <80% = cari cara lain.**
⇒ **GAGAL JAUH.** Wulan **STOP** di percobaan ke-2 (aturan Bos: maks 2×, ke-3 = menambal = HARAM).

### Tabel lengkap P-1
| Kasus | Kunci mata | Jev bilang | Conf | |
|---|---|---|---|---|
| fid=78 L358 (1.2 Rumusan Masalah) | judul_isi | paragraf | 0,7 | ❌ |
| fid=78 L606 (1.3 Tujuan) | judul_isi | paragraf | 0,72 | ❌ |
| fid=78 L620 (1.4 Manfaat) | judul_isi | paragraf | 0,61 | ❌ |
| fid=78 L638 | judul_isi | paragraf | 0,84 | ❌ |
| fid=115 L2 (1.1 LATAR BELAKANG) | judul_isi | judul_isi | 0,98 | ✅ |
| fid=115 L877 (4. Threats) | butir | judul_isi | 0,63 | ❌ |
| fid=115 L3486 (tabel) | tabel | tabel | 0,64 | ✅ |
| fid=115 L7997 (tabel langkah) | tabel | judul_isi | 0,73 | ❌ |
| fid=115 L8019 (tabel informan) | tabel | judul_isi | 0,36 | ❌ |
| fid=115 L555 (paragraf) | paragraf | butir | 0,88 | ❌ |
| fid=115 L4000 (paragraf) | paragraf | tabel | 0,49 | ❌ |
| fid=115 L6000 (paragraf) | paragraf | tabel | 0,54 | ❌ |

---

## 3. AKAR MASALAH — SALAH WULAN, BUKAN SALAH JEV

**Bukti paling telak:**
```
fid=78 L358 "1.2 Rumusan Masalah"  →  Jev bilang "paragraf"
   ↑ ini judul sub-bab yang JELAS
   ↑ Wulan SENDIRI sudah buktikan Jev bisa kenali (peta halus: p = 0,91!)
```

⇒ **Jev sanggup.** Yang salah **cara Wulan bertanya.**

| Peta halus (BERHASIL) | Uji P (GAGAL) | Akibat |
|---|---|---|
| Tanya **sempit**: *"apakah baris ini AWAL SUB-BAB?"* | Tanya **melayang**: *"bentuk penulisan apa?"* | Jev bingung |
| Pilihan **YA/TIDAK** | Pilihan **4 macam pola** | Jev tersesat |
| **Satu** hal per pertanyaan | **4** hal sekaligus | tidak fokus |

**Wulan melanggar aturan yang SUDAH TERTULIS di catatan sendiri:**
> ⛔ *JANGAN tanya luas. "same paragraph?" SALAH (semua dijawab ya).
> "picks up mid-sentence?" BENAR. Pertanyaan HARUS SEMPIT.*

⇒ Petunjuk tambahan: banyak conf rendah (0,36–0,60) = **Jev sendiri bilang "aku tidak yakin"**. Itu tanda pertanyaannya tidak jelas, bukan tanda Jev bodoh.

---

## 4. RENCANA — 3 LANGKAH (Wulan, siap Bos perbaiki)

### LANGKAH 1 — Ganti cara tanya: PECAH jadi pertanyaan SEMPIT ya/tidak

Jangan tanya *"bentuk apa?"*. Tanya **3 hal terpisah**, masing-masing ya/tidak:

```
T1: "Apakah baris >>> ini JUDUL bagian akademik?"          → ya / tidak
T2: "Apakah baris >>> ini PENANDA BUTIR (a./b./1./2./-)?"  → ya / tidak
T3: "Apakah baris >>> ini POTONGAN SEL TABEL?"             → ya / tidak
```

**Kombinasi jawaban → pola:**
| T1 | T2 | T3 | ⇒ Pola |
|---|---|---|---|
| ya | tidak | tidak | `judul_isi` |
| tidak | ya | tidak | `butir` |
| tidak | tidak | ya | `tabel` |
| tidak | tidak | tidak | `paragraf` |

⚠️ Kalau hasilnya **campur** (mis. T1 ya & T2 ya) → **ambang/kombinasi perlu diukur**, jangan ditebak.
⚠️ **Tanya POLA, bukan ISI** — sesuai perintah Bos ("bukan makna, tapi pola penulisan").

### LANGKAH 2 — Kalau L1 masih gagal: pindah yang membaca pola

```
Pilihan pengganti:
 (a) Jev baca DENGAN jendela lebih lengkap (7–9 baris) + fakta yang kode TAHU
     tapi tak bisa putuskan (mis. "baris ini punya tanda a./b. di awal?")
 (b) KODE sediakan FAKTA DASAR (ada penanda butir? ada titik akhir? panjang?)
     → Jev hanya MENIMBANG fakta itu jadi pola (pola yang sudah TERBUKTI
       berhasil di peta bab: kode kasih fakta angka → Jev menimbang)
 (c) Kalau Jev tetap tidak bisa → POLA TIDAK DIBACA, tapi DIWARISI:
     "bagian baru mewarisi pola bagian sebelahnya" (aturan sederhana, nol Jev)
```

### LANGKAH 3 — Kalau pola sudah terbaca akurat (≥80%)

Baru susun rancangan resmi "POLA PENULISAN (Opsi C)":
```
1. Peta simpan kolom baru: `pola` (4 nilai: judul_isi/butir/tabel/paragraf)
2. Prioritas penentu pola (opsi C Bos):
     ① permintaan PEMBIMBING (jika ia sebut pola tertentu)   ← menimpa
     ② POLA TETANGGA dari peta                                ← default
     ③ default aman: `paragraf`                              ← cadangan
3. NOMOR dihitung MESIN dari peta (2.1 → 2.2 / 2.1.1) — AI DILARANG mengarang nomor
4. Prompt ke AI: "tulis ISI saja. BENTUK + NOMOR sudah disediakan."
5. "Bertetangga" = kirim ke AI: pola bagian SEBELUM & SESUDAH (bukan isinya)
```

---

## 5. ⚠️ YANG BELUM ADA (jujur — bukan berarti sudah selesai)

| Hal | Status |
|---|---|
| Kolom `pola` di peta | ❌ belum ada |
| Jev bisa kenali pola | ❌ **BELUM TERBUKTI** (uji P gagal 2×) |
| Nomor otomatis + geser nomor | ❌ belum ada |
| Sambung ke Kolaborasi | ❌ `kolaborasi.py` 0 panggilan peta |
| Kolom `mulai`/`akhir` | ❌ masih bug (nilai 0) |

---

## 6. ⛔ YANG TIDAK WULAN USULKAN (pagar)

1. **Tidak** paksa Jev kalau memang tidak sanggup kenali pola (aturan Bos: jangan paksakan).
2. **Tidak** bikin modul/tabel/jalur baru — pakai peta yang sudah ada.
3. **Tidak** suruh AI memutuskan bentuk/nomor (itu sumber "pola aneh").
4. **Tidak** tanya user soal pola (aturan Bos: jangan banyak tanya — pakai default aman).
5. **Tidak** koding apa pun sebelum uji pola terbukti ≥80%.

---

## 7. YANG WULAN MINTA DARI BOS

1. **Setuju cara LANGKAH 1** (pecah jadi pertanyaan sempit ya/tidak)? Atau Bos punya arah lain?
2. Kalau L1 masih gagal — Bos pilih **(a) / (b) / (c)** di LANGKAH 2?
3. **Definisi pola**: cukup **4 nilai** (judul_isi / butir / tabel / paragraf) — atau Bos mau tambah (mis. `kutipan`, `rumus`)?

---

## BERKAS UJI
- `_sketsa/_uji_p_pola.py` → `HASIL_UJI_P_POLA.json` (P-1, jendela 3 baris)
- `_uji_p2.py` (P-2, jendela 5 baris — di dalam container)
- Rancangan terkait: `RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md`
- Laporan uji lain: `LAPORAN_UJI_HAKIM_NAIK_KELAS_09OKT2026.md`
