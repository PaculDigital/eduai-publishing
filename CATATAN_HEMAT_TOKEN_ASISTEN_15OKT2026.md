<!-- SOT: CATATAN_HEMAT_TOKEN_ASISTEN_15OKT2026 -->

# 💰 HEMAT TOKEN ASISTEN PEMBIMBING — 15 Okt 2026

> Perintah Bos (pilihan **A**): sambungkan alat hemat yang **sudah ada**
> (`app/konteks.py`) ke jalur asisten pembimbing. Bukan mesin baru.

---

## 1. AKAR MASALAH (terukur, bukan tebakan)

```
app/asisten.py:39    NASKAH_MAKS = 40_000      ← naskah DIPOTONG 40.000 kar
app/asisten.py:147   return teks[:NASKAH_MAKS] ← lalu dikirim UTUH ke AI
```

Alat hemat token **sudah ada** dan **sudah terbukti** (`app/konteks.py`,
hemat 91% — terukur 25 Sep 2026), **dan sudah dipakai** jalur revisi mahasiswa
(`app/ai.py:2444-2477`). Di jalur **asisten pembimbing**, alat itu **belum
disambungkan** ⇒ AI menerima naskah 40.000 huruf utuh.

**Ini bukan mesin baru** — pemasangan pemanggil, sesuai aturan Bos.

---

## 2. YANG DIPASANG (3 fungsi kecil di `app/asisten.py`)

| Fungsi | Gunanya |
|---|---|
| `_bagian_dari(teks)` | Pecah naskah jadi BAGIAN lewat `state.petakan()` + `state.buang_daftar_isi()` |
| `_baca_giliran` / `_simpan_giliran` | Nomor giliran di tabel `setelan` (tabel yang SUDAH ADA) |
| `_siapkan_kirim(db, b, teks)` | Susun teks kiriman: 1 bagian + tetangganya via `konteks.bangun_prompt()` |

**Cara kerja:** sekali operasi meninjau **1 bagian** + konteks tetangganya
(judul bab, sebelum, sesudah, isi target, tugas). Operasi berikutnya **maju 1
bagian** ⇒ seluruh naskah kebagian (bab 1 → 2 → 3 → … berputar kembali).

---

## 3. HASIL UJI (terukur)

### Gerbang `_uji_hemat_asisten.py` — **18 LULUS / 0 GAGAL** (EXIT 0)

| Kasus | Hasil |
|---|---|
| A. Naskah panjang dipecah | ✅ 5 bagian, kirim 8.161 kar dari 25.080 (**hemat 67,5%**) |
| B. Naskah pendek | ✅ kirim UTUH (pagar bekerja) |
| C. Mesin pecah GAGAL | ✅ kirim UTUH (tinjauan tetap jalan) |
| D. Giliran | ✅ 3 operasi → posisi `[0, 1, 2]` (bagian berbeda) |
| E. Isi target terkirim | ✅ penanda peta/isi/tugasan ada |
| F. Pencari kutipan | ✅ `simpan_usulan()` tetap pakai naskah UTUH |

### Uji nyata naskah ASLI mahasiswa — **hemat 90,0%**

| Naskah | Sebelum | Sesudah | Hemat |
|---|---|---|---|
| 16 naskah @ 70.487 kar | 1.127.792 kar | 112.528 kar | **90,0%** |
| 5 naskah @ 362 kar | dikirim utuh | dikirim utuh | (pagar) |

---

## 4. PAGAR (tidak boleh dilanggar)

1. **Gagal apa pun → jalur lama.** Tinjauan TIDAK pernah gagal karena optimasi.
2. **Naskah < 6.000 kar → kirim utuh.** Tak ada gunanya memecah.
3. **Peta < 2 bagian → kirim utuh.** Tidak ada tetangga.
4. **Hasil potongan HARUS lebih kecil.** Kalau tidak → kirim utuh.
5. **`simpan_usulan()` TETAP pakai naskah UTUH** untuk cari kutipan.
   Yang dipotong **hanya** yang dikirim ke AI — **sorotan tidak jadi palsu**.

---

## 5. CATATAN UJI (pelajaran)

- Gerbang **menangkap 2 cacat nyata** sebelum tayang: (a) kirim 3 bagian
  sekaligus cuma hemat **2,8%**; (b) giliran bisa keluar rentang → `-1`.
  Keduanya diperbaiki jadi **hemat 67,5%** dan giliran `[0,1,2]`.
- Uji **WAJIB di dalam container** (kode produksi ada di image, bukan host).
- Nama kelas berkas kolaborasi = **`BerkasPembimbingan`** (bukan `FileBerkas`);
  `SessionLocal` ada di **`app/models.py`** (bukan `app/database.py`).

---

## 6. STATUS — ✅ SUDAH LIVE DI PRODUKSI (15 Okt 2026)

| | |
|---|---|
| Kode | ✅ `app/asisten.py` (host = image, IDENTIK 80 berkas) |
| Gerbang | ✅ 30/0 (hemat+pagar) · 76/0 (pembimbing) · 15/0 (C7 dompet) |
| Container | ✅ **LIVE** — image `eduai-app:20261015_085014-sot` |
| Ukur nyata | ✅ **hemat 90,0%** pada 16 naskah asli (1.127.792 → 112.528 kar) |
| Backup | `_arsip/pre-hemat-asisten-15okt26/` |
| Titik mundur | `eduai-app:cadangan-pra-hemat-asisten` (= `20261015_002535-sot`) |

## 6b. PAGAR 2 — permintaan MENYELURUH (15 Okt 2026)

**Kapan berlaku:** pembimbing menulis catatan seperti *"ubah alur seluruh
naskah"* / *"ganti alur seluruh dokumen"* → asisten **TIDAK memotong**,
kirim naskah **utuh** (hemat token sengaja dilepas di situ).

**Pakai mesin yang sudah ada** — `ai._boleh_konteks()` (ai.py:1931) yang
membaca komentar lewat `parser.pilih_pengali` (UBAH_ALUR ×4, +SEMUA ×5).
Aturannya **tidak disalin** supaya asisten & revisi mahasiswa tidak pernah
beda pendapat.

⚠️ **Catatan penting (jangan dianggap bug):** pemicunya kata-kata
`parser._KATA_ALUR` = *ubah alur · ganti alur · ubah paradigma ·
ganti paradigma · deduktif jadi induktif · induktif jadi deduktif ·
ubah kerangka · rombak alur · ganti alur berpikir*. Kalimat
*"perbaiki alur"* **tidak termasuk** — itu rancangan lama, di luar tugas
pagar ini (dikunci oleh pemeriksa G4e).

**Bukti bergigi (G7):** dengan pagar menutup → kirim 25.080 kar (utuh);
tanpa pagar → 8.161 kar (dipotong).

| | |
|---|---|
| Backup DB | `_arsip/pra-sot/20261015_085014-sot` |
| Produksi | ✅ `/` 200 · `/health` 200 · `/masuk` 200 · editor hidup |
| Cadangan kode | `_arsip/pre-hemat-asisten-15okt26/asisten.py` |

## 6c. PAGAR 2 — status

⚠️ **Kode pagar 2 (`_catatan_terbaru` + `_boleh_potong`) BELUM DEPLOY.**
Tersimpan di `app/asisten.py` host; container masih menjalankan versi
tanpa pagar 2. Menunggu izin Bos (aturan: deploy = izin dulu).

**Verifikasi sesudah deploy hemat token (15 Okt):** gerbang dijalankan
ULANG di dalam container baru — 18/0 · 76/0 · 15/0, ukur nyata **90,0%**.
