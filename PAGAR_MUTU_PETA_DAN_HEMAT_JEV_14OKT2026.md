<!-- SOT: PAGAR_MUTU_PETA_DAN_HEMAT_JEV_14OKT2026 -->

# 🔒 PAGAR MUTU DI JALUR PETA + BUKTI HEMAT JEV (14 Okt 2026)

> **Status:** ✅ SELESAI & TAYANG PRODUKSI
> **Image:** `eduai-app:20261014_071115-sot` · **Mundur:** `eduai-app:cadangan-pra-sot`
> **Putusan Bos:** "Opsi B" (dua kali) — naskah rusak = **beri tahu, jangan bayar Jev**

---

## 1. LATAR — KENAPA INI DIKERJAKAN

Bos menanyakan biaya Jev setelah saldo OpenRouter habis (sisa $3,62 dari $30).

**Hasil ukur langsung dari OpenRouter (bukan tebakan):**

| Naskah | Biaya Jev |
|---|---|
| Naskah 145 KB (4.138 kandidat) | **Rp 111** |
| Naskah biasa 70 KB | **Rp 28** |
| Harga 1 token masuk | Rp 0,00067 |

⇒ **Jev murah.** Biaya produksi normal Rp 28–111/naskah.
⇒ Yang membuat saldo habis = **(a) uji berulang Wulan**, **(b) naskah RUSAK dibayar Jev penuh**.

---

## 2. 🎯 JAWABAN BOS YANG TERUKUR: JEV TIDAK DIPANGGIL BERULANG

**Pertanyaan Bos:** *"Apakah Jev akan ditanya berulang-ulang di naskah yang sama terus?"*

**JAWABAN: TIDAK.** Sudah terbukti lewat uji nyata (rute produksi):

| | Ronde 1 | Ronde 2 (naskah sama) |
|---|---|---|
| **Waktu** | **55,6 detik** | **0,0 detik** |
| **Panggil Jev?** | ✅ ya | ❌ **TIDAK** — dari simpanan |
| Bagian | 80 | 80 (sama) |

Hasil uji: **6 LULUS / 0 GAGAL**.

**Mekanismenya** (`app/ai.py:4312` — PAGAR C2, sudah ada sejak lama):

```
sid = sidik_naskah(teks)                 ← sidik jari SHA-256
kalau prof.peta_sidik == sid:
    return peta tersimpan ('dari_simpanan': True)   ← Rp 0, 0 detik
```

**Kunci = SIDIK JARI.** Naskah berubah sedikit ⇒ sidik beda ⇒ baru dipanggil ulang.

**Simpanan:** `ProfilDokumen.peta_json` + `peta_sidik` + `peta_dibuat` (models.py:594-596).

---

## 3. 🔧 YANG DIPASANG (PAGAR MUTU DI JALUR PETA)

**Berkas:** `app/ai.py` — sisipan sebelum surveyor Jev dipanggil (rute `/api/ai/v1/peta/mulai`).

```python
_mutu_rusak = False
if body.get('file_id') and mode == 'peta_awal' and teks.strip():
    _m = periksa_mutu(teks)                        # TANPA Jev, Rp 0
    _mutu_rusak = (_m.get('tingkat') == 'rusak_konversi')

if body.get('file_id') and mode == 'peta_awal' and not _mutu_rusak:
    _ps = peta3_jev.petakan(file_id)               # ← surveyor Jev
```

**SIFAT: TAHU + TAWAR (bukan blokir)** — user tetap boleh lanjut, tapi pakai
**jalur fallback** (peta halus/kasar lama) yang **Rp 0**.

### Syarat keselamatan (kenapa ini aman)
1. `periksa_mutu()` **tanpa Jev**, murni hitungan ⇒ Rp 0, ~0 detik.
2. `AMBANG_HURUF_TUNGGAL = 50`, pemisahan terukur **1 vs 4.989** ⇒ naskah sehat tidak mungkin tertahan.
3. Hanya tingkat `rusak_konversi` dilewatkan; `sehat` & `baris_pendek` **jalan seperti biasa**.
4. Gagal periksa ⇒ **jangan tahan** (selalu utamakan jalur normal).

---

## 4. 📊 BUKTI UJI PRODUKSI (angka nyata)

| Uji | Berkas | Hasil |
|---|---|---|
| **A** | fid=115 (**PDF rusak**) | 15,4 dtk · `peta_dari=fallback` · alasan: *"naskah rusak (pecah per-huruf) — Jev dihemat"* |
| **B** | fid=81 (**sehat**) | 0,8 dtk · `peta_dari=jev` · **5 bab, 130 sub-bab** ✅ tetap jalan |

### Gerbang (semua LULUS)
| Gerbang | Hasil |
|---|---|
| `app/_gerbang_pagar_mutu_peta.py` (BARU) | **15 LULUS / 0 GAGAL** |
| `app/_gerbang_jev_jalantol.py` | **30 LULUS / 0 GAGAL** |
| `scripts/periksa_kode.sh` | **LULUS** |
| Gerbang editor OnlyOffice | **LULUS** |
| Health produksi | **200** |

### Hemat terukur
| | Sebelum | Sesudah |
|---|---|---|
| PDF rusak (fid=115) | ~**Rp 111** + 55 dtk | **Rp 0** (Jev dihemat) |
| Naskah sehat | normal | normal (tidak diubah) |

---

## 5. 🎁 CACAT LAMA YANG IKUT DIBERESKAN

**Gerbang jalan tol Jev selalu melaporkan 2 GAGAL (F1/F2) di produksi.**

**Akar:** bukan kode — 2 berkas laporan **tidak ikut image**:
- `HASIL_UJI_12_KASUS_BATAS_09OKT2026.md`
- `HASIL_VALIDASI_SILANG_K5_09OKT2026.md`

**Fix:** ditambahkan `COPY` di `Dockerfile` → gerbang **30/0** (dari 28/2).

---

## 6. 🧠 TEMUAN BESAR: MENGAPA "OPTIMALKAN JEV" SUDAH SELESAI (DAN TIDAK BISA DIPAKSA)

### A. Dokumentasi resmi TypeSafe MENJAWAB
`cookbook-structure-recovery.md` (resmi): seluruh pipeline = **2 permintaan
per dokumen** (10.211 token, 0,8 dtk, $0,0015). **Bukan 40.**

Tapi kuncinya: dokumentasi itu memakai **17 blok**, bukan 28 baris mentah.
⇒ **Kita 244× lebih banyak baris.** Masalahnya bukan "kurangi panggilan",
tapi **"jangan kirim semua baris"**.

### B. Percobaan "jahit baris (stitch)" SUDAH PERNAH DILAKUKAN — 10 Okt 2026
Perintah Bos waktu itu (verbatim):
> *"Dah cukup, makin banyak kandidat makin mahal saya bayar jev. Kalo masalah yang sederhana jangan detail karena tidak bisa buat general naskah"*

Semua perubahan kode **DIBATALKAN** saat itu. Hasil ukurannya masih tersimpan
(`CATATAN_TEMUAN_STITCH_10OKT2026.md`):

| Naskah | Baris | Setelah stitch |
|---|---|---|
| fid=115 (PDF rusak) | 8.755 | → 1.586 ✅ |
| fid=104 (Disertasi) | 25.055 | → 7.020 (**tetap terpotong**) ❌ |
| fid=81 (normal) | 1.874 | **tidak berubah** ✅ |

⇒ **Stitch membantu 1 naskah, GAGAL 1 naskah. Bukan solusi global.**

### C. DILARANG DIULANG (semua TERBUKTI SALAH)
| Cara | Bukti gagal |
|---|---|
| Regex mengenali bentuk naskah | peta lama Disertasi **0/5 bab** |
| Kode menebak bentuk (v1–v6) | naskah A jalan, naskah B **nol** |
| "Pola global sekali kunci" | baris kosong **beda arti tiap naskah** |
| Menyaring kandidat dengan panjang baris | makan **922 baris (76%)** Asih |

### D. AKAR SEBENARNYA = MUTU FILE USER, BUKAN MESIN
fid=115 rusak **per-HURUF** (`D`,`i`,`n`,`a`). fid=104 tiap baris dipisah baris kosong.
⇒ **PDF rusak.** Catatan resmi: *"MUTU FILE > KODE; ekstraktor kita sudah benar."*

---

## 7. 🚪 PAGAR PINTU UNGGAH — 3 LAPIS SUDAH ADA (terverifikasi 14 Okt)

| # | Pagar | Berkas:baris | Fungsi |
|---|---|---|---|
| ① | **Format lama** | `config.py:51` + `:63` (`EKSTENSI_LAMA`) | `.doc/.xls/.ppt` ditolak → arahkan *"Save As .docx"* |
| ② | **Isi berkas** | `main.py:868` (`periksa_berkas_aman`) | Makro/zip rusak/bukan Word → **ditolak** |
| ③ | **Mutu naskah** | `periksa_mutu.py` (112 baris) | Pecah per-huruf → beri tahu + arahkan .docx |

**Catatan penting:** pagar ③ bersifat **TAHU + TAWAR, bukan BLOKIR** — keputusan
Bos 10 Okt (*"supaya user tidak kabur"*). Yang **baru** 14 Okt: peta **tidak
membayar Jev** untuk naskah yang sudah diketahui rusak (Pasal 3 di atas).

---

## 8. 📌 UNTUK FITUR KOLABORASI (pertanyaan Bos, jawaban dari kode)

**Pertanyaan Bos:** *"Disimpan dan ditanya hanya pada blok penajaman saja?"*

**Jawaban: pondasi SUDAH ADA semua.**

| Komponen | Berkas:baris | Status |
|---|---|---|
| Peta disimpan sekali (tidak dihitung ulang) | `ai.py:4312` | ✅ **TERBUKTI** (uji 6/0) |
| `SectionState` — ingatan per sub-bab | `models.py:635` | ✅ ADA, **33 baris produksi** |
| `sidik_bab` — deteksi **bab mana yang berubah** | `models.py:669` | ✅ ADA |
| `RevisiHistory` — riwayat revisi per sub-bab | `models.py:685` | ✅ ADA |
| Kolaborasi ambil dari peta tersimpan | `kolaborasi.py` | ❌ **BELUM disambung** |

**Rancangan Bos (08 Okt, sudah dikunci):**
> *"Satu peta per naskah (dibuat JEV) disimpan di `section_state`, dibuat saat
> naskah pertama dibutuhkan, semua fitur ambil dari situ (1× Jev per naskah)."*

⇒ **`sidik_bab` = kunci hemat kolaborasi:** pembimbing komentari sub-bab 2.1.5
⇒ **hanya blok itu** yang peta-nya diperbarui, bab lain **tidak** dipanggil ulang.

---

## 9. 📁 BERKAS TERKAIT

```
app/ai.py:4312-4380        pagar C2 (simpanan) + pagar mutu (BARU)
app/periksa_mutu.py        hitungan mutu (112 baris, TANPA Jev)
app/_gerbang_pagar_mutu_peta.py   gerbang BARU (15/0)
Dockerfile                 + 2 COPY laporan uji
_arsip/pre-pagar-mutu-peta-20261014-070718/   backup app/ai.py
_sketsa/uji_peta_2x.py     uji bukti "panggil 2×" (6/0)
CATATAN_TEMUAN_STITCH_10OKT2026.md            hasil stitch 10 Okt
PAGAR_PINTU_NASKAH_10OKT2026.md               3 pagar pintu unggah
```

---

## 10. ⬜ BELUM DIKERJAKAN (jujur)

```
⬜ Kalimat di LAYAR: "Peta pakai mode hemat — naskahmu terpotong, unggah
   .docx asli supaya peta lebih rapi" (kotak mutu sudah ada, kalimat belum)
⬜ Sambung kolaborasi ke SectionState + sidik_bab (Lapis 3-5)
⬜ Uji BAB III-V naskah 112 · naskah Asih/Disertasi utuh
⬜ Disk penuh (96%, sisa 3,1 GB) — belum diberesi
```
