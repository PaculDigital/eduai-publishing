<!-- 🚪 SOT: PUTUSAN BOS (pagar unggah = SATU sumber) — bukan penentu status aplikasi. Status ada di SOT.md + sot.py -->
# 🚪 PAGAR PINTU NASKAH + FORMAT STANDAR — 10 Okt 2026

> Putusan Bos (verbatim): *"Agar standard aplikasi. Jika user upload .doc
> diminta ganti menjadi .docx terlebih dahulu."* ⇒ pilihan **B** lalu **A**
> (semua format lama Office dilarang, diseragamkan di mana pun).
>
> 🚩 **DIPERBARUI 10 Okt 2026** — dokumen ini DIPERLUAS dengan pasal ③
> (MUTU NASKAH DI HULU) + 3 temuan nyata + bukti uji gigi terbaru.

---

## 0. RINGKAS SATU LAYAR (kalau Bos cuma baca satu bagian, baca ini)

```
✅ SUDAH HIDUP DI PRODUKSI:
   ① Format lama Office (.doc/.xls/.ppt) DITOLAK + user diarahkan ganti
   ② Isi berkas diperiksa di pintu: makro / zip-nyamar / bukan-Word DITOLAK

⏳ BELUM DIKERJAKAN (pasal ③):
   ③ MUTU NASKAH di hulu — hitung fakta, TANPA Jev, GRATIS
      (deteksi naskah PDF pecah per-huruf / per-baris-kosong)

🧹 DIBERESKAN 10 Okt 2026:
   · Gerbang uji cemar DB produksi (48 berkas + 8 akun uji) → DIHAPUS
   · Gerbang uji lapor GAGAL PALSU (jalur login salah) → DIPERBAIKI
```

---

## 1. Yang dikerjakan (pasal ① & ②)

### ① Format lama Office DILARANG (seragam, satu sumber)

| Berkas | Sebelum | Sesudah |
|---|---|---|
| `app/config.py` `EKSTENSI_DIIZINKAN` | ada `.doc .xls .ppt` | **dibuang** + tabel baru `EKSTENSI_LAMA` (arahan pengganti) |
| `app/lampiran_pembimbing.py` `EKSTENSI_LAMPIRAN` | ada `.doc .xls .ppt` | **dibuang** |
| `app/lampiran_pembimbing.py` `_TANDA` + `_kelompok()` | cabang `doc` (OLE) | **cabang mati dibuang** |
| `app/lampiran_ai.py` `TEKS_EKST` | ada `.doc .xls` | **dibuang** |
| `app/ai.py` `_teks_dari_berkas` | pembaca `.doc` biner ASCII | **dibuang** (kode mati) |

**Pesan ke user (arahkan, bukan cuma tolak):**
> Format .doc (Office lama) tidak didukung. Silakan buka di Word lalu
> "Save As" .docx, kemudian unggah berkas .docx itu.

### ② Pagar ISI berkas dipakai di pintu unggah (temuan lubang)

**LUBANG NYATA:** `konversi.periksa_berkas_aman()` (deteksi `word/vbaProject.bin`
= makro, ZIP rusak, bukan Word) SUDAH ADA sejak 07 Okt, tapi **hanya dipakai di
jalur konversi jurnal** — TIDAK di `POST /unggah` ⇒ berkas bermakro bisa masuk
storage.

**Obat (aturan Bos "jangan bikin baru — pakai yang sudah ada"):**
`app/main.py:863-880` memanggil `konversi.periksa_berkas_aman()` APA ADANYA di
`/unggah`, **sebelum** berkas ditulis ke storage. Nol mesin baru, nol salinan kode.

---

## 2. ✅ PASAL ③ — MUTU NASKAH DI HULU (LIVE 11 Okt 2026)

> **STATUS: SELESAI & LIVE.** Kode `app/periksa_mutu.py` (SUDAH ADA, tidak bikin
> baru) dititipkan di rute yang sudah ada `app/rute_alur.py:150` (kunci `'mutu'`)
> + tampil di `app/templates/mulai.html` kotak `#det-mutu` (JS `tampilMutu()`).
> **Gerbang:** `_gerbang_periksa_mutu.py` 18/0 · `_gerbang_http_mutu.py` 14/0,
> **BERGIGI** (14/0 → 12/2 EXIT 1 saat dirusak → 14/0). Deploy: berkas tampilan
> disalin ke container + `docker restart eduai-app`, md5 host = container.
> **Sifat: MEMBERI TAHU, TIDAK MEMBLOKIR** (naskah tetap boleh lanjut).

> **Arah Bos (verbatim, 10 Okt):** *"arah yang benar = bersihkan saat UNGGAH
> (hulu), bukan tambal di peta"* + *"masalah simple jangan dibuat detail
> karena tidak bisa buat general naskah"*.

### Kenapa di HULU, bukan di peta

```
Masalah naskah rusak (PDF pecah per-huruf / per-baris-kosong) BUKAN kekurangan
Jev — itu MUTU FILE USER. Kalau ditambal di peta ⇒ tiap naskah butuh kode
sendiri ⇒ BIAYA JEV MEMBENGKAK ("makin banyak kandidat makin mahal saya bayar
Jev" — Bos, 10 Okt). Karena itu: BERHENTI tambal di peta; kerjakan di pintu.
```

### Ukuran TERUKUR (dari `CATATAN_TEMUAN_STITCH_10OKT2026.md`)

| Naskah | Baris | Kandidat | Sampah ≤2 kar | Median baris | Sehat? |
|---|---|---|---|---|---|
| fid=81 (Asih) | 1.874 | 491 (26%) | 655 | 37 kar | ✅ sehat |
| fid=115 (Wulandari PDF) | 8.755 | 8.555 (98%) | 5.623 (64%) | **1 kar** | ❌ RUSAK fatal |
| fid=104 (Disertasi) | 25.055 | 12.302 (49%) | 12.916 (52%) | 15 kar | ⚠️ terpotong |

**Ambang yang dipakai (kode hitung fakta, TANPA Jev, GRATIS):**
```
baris isi 1 huruf · baris ≤2 karakter · rata-rata panjang baris

naskah SEHAT  (fid=81) : baris huruf-tunggal = 1
naskah RUSAK  (fid=115): baris huruf-tunggal = 4.989
⇒ Jev TERBUKTI TIDAK BISA membedakan (0% vs 0% — dijawab sama).
⇒ Karena itu cukup KODE HITUNG FAKTA. Jev tidak dibutuhkan di pintu ini.
```

### Rencana pagar ③ (belum dikode)

```
/periksa-mutu (GRATIS, tanpa Jev):
   hitung fakta baris → kalau RUSAK: beri tahu user APA ADANYA
   ("naskah Anda terbaca per-huruf — ini biasanya karena PDF hasil scan /
     konversi gambar. Coba unggah .docx asli atau PDF yang bisa di-copy")
   ⇒ TIDAK MEMBLOKIR (naskah tetap masuk) — sesuai sifat "pagar ③ memberi tahu"
```

---

## 3. Urutan pagar (satu jalur bersih)

```
① FORMAT     : .doc/.xls/.ppt/dll ⇒ TOLAK + arahkan ganti .docx/.xlsx/.pptx  ✅ HIDUP
② ISI BERKAS : makro / zip-nyamar / bukan-Word ⇒ TOLAK di pintu              ✅ HIDUP
③ MUTU NASKAH: hitung fakta (baris huruf-tunggal/≤2 kar/median)              ✅ LIVE
                ⇒ BERI TAHU user, TIDAK memblokir. TANPA Jev, GRATIS.
④ JEV SURVEYOR: naskah sehat ⇒ peta bentuk (bab/sub-bab/paragraf)
⑤ MESIN + AI
```

---

## 4. Bukti uji (dijalankan DI DALAM container, 10 Okt 2026)

```
_gerbang_format_standar.py : 11 LULUS / 0 GAGAL  EXIT 0  ✅
_gerbang_pagar_unggah.py   :  5 LULUS / 0 GAGAL  EXIT 0  ✅

UJI GIGI (suntik pagar dimatikan ⇒ gerbang WAJIB GAGAL):
  format_standar : 11 LULUS → 5 LULUS / 6 GAGAL   ✅ BERGIGI
  pagar_unggah   :  5 LULUS → 2 LULUS / 3 GAGAL   ✅ BERGIGI

Kesehatan: periksa_kode.sh LULUS · aplikasi /health HTTP 200 ✅
           md5 host == container (main.py 65221953…, config.py 5b52d51c…) ✅
```

`_gerbang_format_standar.py` menguji (perilaku, bukan grep):
```
✅ .doc ⇒ 400 + pesan menyebut ".docx"      ✅ docx ISI bermakro ⇒ 400 MAKRO
✅ .xls ⇒ 400 + pesan menyebut ".xlsx"      ✅ ZIP dinamai .docx ⇒ 400
✅ .ppt ⇒ 400 + pesan menyebut ".pptx"      ✅ docx bukan-zip ⇒ 400
✅ .dotm ⇒ 400                              ✅ docx SAH ⇒ TIDAK ditolak (kontrol)
✅ EKSTENSI_DIIZINKAN/LAMPIRAN bebas .doc/.xls/.ppt
✅ semua ekstensi lama punya arahan pengganti
```

⚠️ **Pelajaran gerbang (JANGAN diulang):** gerbang versi-1 TIDAK bergigi karena
hanya `grep` teks di main.py — saat pagar dimatikan (`if not aman:` → `if False:`),
grep tetap menemukan teksnya ⇒ LULUS palsu. **Gerbang WAJIB memanggil PERILAKU.**

---

## 5. 🚨 3 TEMUAN NYATA 10 Okt 2026 (semua sudah dibereskan)

### Temuan ① — Gerbang uji MENCEMARI DB produksi (berat)

Gerbang memakai `TestClient` tanpa mengalihkan DB ⇒ setiap kali dijalankan ia
**mendaftarkan akun uji + menyimpan berkas uji ke DB produksi**.
Terukur: **48 berkas + 8 akun uji** menumpuk di produksi (bukan dari gerbang hari
ini saja — sisa gerbang sesi lama: uji mutu 07 Okt, e2e unduh 06 Okt, dll).

```
SEBELUM bersih-bersih : 12 user · 65 berkas  (8 akun uji, 48 berkas uji)
SESUDAH               :  4 user · 17 berkas  (semua akun asli Bos)
DIHAPUS               : uji-asing-t52 · uji-berbayar-e2e · uji-berat-e2e
                        uji.tanda · uji_mutu_tampil/v2/v3 · cekhtml
DIPERTAHANKAN         : wulan@bikinaja.me (7) · wulan-setwa@ (0)
                        asih.susanti@eduai.test (9) · potret-ref@eduai.test (1)
```

**OBAT — pola SUDAH ADA, dipakai apa adanya:** `_gerbang_unduh_dobel.py` sudah
memakai **DB SALINAN** (salin DB ke tmpdir → `EDUAI_DB` → session dipaksa ke
salinan). Pola itu kini dipakai di `_gerbang_format_standar.py` &
`_gerbang_pagar_unggah.py`.

**BUKTI OBAT BEKERJA:** gerbang dijalankan 2× ⇒ angka produksi **TIDAK BERGERAK**
(12/65 sebelum = 12/65 sesudah).

### Temuan ② — Gerbang lapor GAGAL PALSU (jalur login salah)

`_gerbang_pagar_unggah.py` versi-1 memakai `/api/daftar` + `/api/masuk`
(**HTTP 404**) ⇒ tidak pernah login ⇒ `/unggah` membalas **HTTP 303 See Other**
⇒ 4 GAGAL PALSU. Jalur login yang BENAR: **`/daftar` + `/masuk`**
(form: `nama`/`email`/`password`).

⚠️ Jebakan ini **sudah tercatat di `_gerbang_format_standar.py`** tetapi belum
ikut diperbaiki di gerbang kedua ⇒ **pelajaran: kalau satu gerbang menemukan
jebakan, SAPI SEMUA gerbang sekaligus.**

### Temuan ③ — Dokumen ini & catatan TIDAK berpenanda SOT

`PAGAR_PINTU_NASKAH_10OKT2026.md`, `CATATAN_TEMUAN_STITCH_10OKT2026.md`,
`POSISI_PRODUKSI_VS_BELUM_MASUK_10OKT2026.md`,
`DEFINISI_BARU_PUTUSAN_BOS_09OKT2026.md` tidak punya penanda `<!-- … SOT: … -->`
di kepala ⇒ `sot.py --periksa` protes (1 masalah). **Sudah ditambahkan.**

---

## 6. Backup

`_arsip/pre-pagar-unggah-20261010-033713/` — main.py + config.py + MD5.txt

---

## 7. BELUM (menunggu keputusan Bos)

- **Pasal ③ pintu periksa MUTU naskah** — kode hitung fakta, TANPA Jev, GRATIS.
- Sketsa layar hasil periksa: `_sketsa/sketsa_periksa_naskah_10okt2026.html`
- Koneksi `JEV` di panel 9router masih ADA (tak dipakai) — hapus butuh tangan Bos.
