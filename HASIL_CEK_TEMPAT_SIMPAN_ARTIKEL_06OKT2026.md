# 🔍 HASIL CEK — TEMPAT PENYIMPANAN ARTIKEL & PENANDA BAB (06 Okt 2026)

<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Perintah Bos (verbatim): *"Cek dulu, pokoknya jangan buat baru tapi lebih
> optimal kan yang sudah ada jadi tidak rumit dan lebih sederhana"*
>
> Status: **PEMERIKSAAN SELESAI — ADA TEMPAT YANG SUDAH SIAP. Tidak perlu tabel baru.**

---

## 🎯 KESIMPULAN: **TIDAK PERLU TABEL BARU** ✅

**Dua tempat yang sudah ada sudah lebih dari cukup:**

| Kebutuhan | Tempat yang SUDAH ADA |
|---|---|
| Daftar artikel + penanda bab | **`profil_dokumen`** — sudah punya **5 kolom JSON** |
| Pola cache (agar tidak cari ulang) | **`peta_json` + `peta_sidik`** — **SUDAH DIPAKAI**, bisa ditiru |
| Wadah (workspace) | **`folders`** — sudah ada (putusan Bos: satu tingkat) |
| Dompet (token) | **`saldo_token` + `kuota.py`** — sudah ada |

⇒ **Sesuai perintah Bos: pakai yang sudah ada, tidak rumit, lebih sederhana.**

---

## 🔬 BUKTI CEK (dari DB produksi, bukan dugaan)

### 1. `profil_dokumen` — **tempat favorit titip data per-naskah**
```
file_id, user_id, judul, jenjang, bidang, mode_penelitian, alur,
brief_json, istilah_json, struktur_json, peta_json, peta_sidik, peta_dibuat,
panduan_json, ...
```
- **5 kolom JSON** sudah dipakai: `brief_json`, `istilah_json`, `struktur_json`,
  `peta_json`, `panduan_json`
- **5 baris terisi** di produksi → **pola ini sudah terbukti jalan**
- ✅ **`file_id` + `user_id`** → sudah menempel per-naskah, tidak perlu kaitan baru

### 2. ⭐ POLA YANG PERSIS DIBUTUHKAN SUDAH ADA — `peta_json` + `peta_sidik`
Dari `models.py` (komentar asli di kode):
```python
# peta_sidik = hash naskah saat peta dibuat → kalau naskah berubah,
# peta lama tidak dipakai ulang (pagar kredibilitas).
peta_json: Mapped[str]   # hasil (JSON)
peta_sidik: Mapped[str]  # sidik jari naskah saat dibuat (cache invalidasi)
```
Dan polanya di `ai.py:4246`:
```python
if (prof and prof.peta_sidik == sid and prof.peta_json
        and mode == 'peta_awal'):
    return json.loads(prof.peta_json)   # ← PAKAI ULANG, tidak hitung lagi
```

⇒ **Ini PERSIS pola yang dibutuhkan** untuk:
- **menyimpan hasil pencarian** jurnal (agar tidak cari ulang / hemat token)
- **tahu kapan hasil lama sudah basi** (kalau judul/kata kunci berubah)

⇒ **Wulan tinggal TIRU pola ini** — bukan bikin mekanisme baru.

### 3. `pustaka.py` — **murni hitung, TIDAK menyimpan apa pun**
Hasil grep: nol `conn` / `sqlite` / `INSERT` di `pustaka.py`.
⇒ Cocok: artinya `pustaka.py` bersih sebagai **mesin pencari**, dan
**penyimpanan** jadi tugas pemanggil — **pola pemisahan yang sudah rapi**.
⇒ Wulan tidak perlu mengubah `pustaka.py` untuk menyimpan.

### 4. Tabel lain yang dicek (tidak dipilih, alasannya)
| Tabel | Kenapa tidak |
|---|---|
| `belajar_naskah` | khusus fitur Belajar (`insight_json`, `soal_json`) — beda urusan |
| `files` | sudah 11 kolom & dipakai banyak fitur — **jangan disentuh** |
| `section_state` | per **sub-bab** hasil revisi — beda urusan |
| `versi_dokumen` | isi versi naskah — beda urusan |

---

## 💡 USULAN WULAN — TITIP DI KOLOM YANG **SUDAH ADA**

### Untuk penanda artikel↔bab + daftar artikel
**Pilihannya (perlu keputusan Bos):**

| Opsi | Cara | Penilaian Wulan |
|---|---|---|
| **A** ⭐ | Pakai **`structured_json`/kolom JSON baru di `profil_dokumen`**... | perlu kolom baru |
| **B** ⭐⭐ | Titip di kolom JSON yang **SUDAH ADA** (mis. `panduan_json`? tidak cocok) | perlu dicek cocok-tidaknya |
| **C** | Tambah **1 kolom JSON** baru di `profil_dokumen` (`jurnal_json` + `jurnal_sidik`) | **paling mirip pola `peta_json`** |

⚠️ **Wulan BELUM memutuskan** — perlu periksa dulu apakah ada kolom yang
**benar-benar kosong & bisa ditumpangi** (supaya **nol kolom baru**), atau
memang lebih aman **menambah 1 kolom JSON** yang mengikuti pola `peta_json`.

⇒ **Mirip `peta_json` = pola yang SUDAH TERBUKTI.** Menambah 1 kolom JSON
**bukan "bangun sistem baru"** — itu **memperluas pola yang sudah ada**.

### Untuk pagar batas 8
Tidak perlu tempat baru — **cukup hitung** dari daftar artikel yang tersimpan
(berapa yang bertanda "manual" di bab itu). **Rp 0, tanpa tabel.**

---

## 📋 STATUS
- [x] **Cek selesai** — perintah Bos dijalankan (cek dulu, jangan buat baru)
- [x] **TEMUAN: tidak perlu tabel baru** — `profil_dokumen` + pola `peta_json` sudah ada
- [x] `pustaka.py` bersih (murni hitung) → penyimpanan di pemanggil (pola sudah rapi)
- [ ] **MENUNGGU**: apakah Wulan boleh **tambah 1 kolom JSON** di `profil_dokumen`
      (mengikuti pola `peta_json` yang SUDAH TERBUKTI), atau Bos mau cara lain
- [ ] Belum ada kode ditulis — masih tahap pemeriksaan
