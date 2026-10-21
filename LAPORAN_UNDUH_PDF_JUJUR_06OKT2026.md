# ✅ UNDUH PDF: JUJUR + PAGAR ANTI-HALUSINASI (06 Okt 2026)

> Keputusan Bos: **"Setuju A, tapi kata kata jangan unduh sendiri"**
> Pertanyaan Bos: *"saya bingung bagaimana jika berkas tidak bisa diunduh,
> script/bot bisa tahu isinya tanpa halusinasi?"*

---

## 1. AKAR MASALAH (yang Wulan temukan)

Rute `/jurnal/unduh` **ADA**, tapi:
- **OpenAlex & Garuda tidak mengisi `pdf_url`** → tiap klik unduh balas
  *"artikel tidak menyertakan tautan PDF"*.
- ⇒ Fitur **tampak selesai, tapi tidak berguna.** Kelas masalah yang Bos benci.

**Lebih penting — Wulan temukan asumsi SALAH di kode Wulan sendiri:**
Wulan menandai `is_oa=True` hanya karena **tautan ketemu**.

**Uji nyata 3 artikel Garuda:**

| Artikel | Hasil sebenarnya |
|---|---|
| Petra (1818743) | dialihkan ke **LOGIN** |
| Unik Kediri (4200800) | **HTTP 403** |
| Garuda sendiri (2426413) | **HTTP 404** |

⇒ **0 dari 3 benar-benar PDF.** "Ada tautan" **≠** "terbuka".
Wulan hampir menyelesaikan sesuatu yang tak berfungsi — kelas kesalahan `spark`.

---

## 2. JAWABAN PERTANYAAN BOS: **ABSTRAK**

Mesin tahu isi artikel **tanpa mengunduh berkas**, dari **abstrak** —
ringkasan yang **ditulis penulis artikelnya sendiri**. Itu **data NYATA**,
bukan tebakan.

**Terukur (06 Okt 2026):**

| Sumber | Abstrak | Panjang |
|---|---|---|
| Garuda | ✅ | 664 · 1038 · 2000 huruf |
| Crossref | ✅ (sebagian) | 1163 · 2666 huruf |
| OpenAlex | ✅ (`abstract_inverted_index`) | direkonstruksi |
| Scopus | ✅ (`dc:description`) | — |

**Diuji nyata:** 5 artikel Garuda → **5/5 punya abstrak** → bahan AI memuat
kata penulis asli. ✅

---

## 3. 3 PAGAR (BARU — `app/pagar_artikel.py`)

| Pagar | Isi |
|---|---|
| **1 — HANYA YANG ADA** | AI hanya boleh pakai **judul + abstrak + jurnal + tahun**. Abstrak < 80 huruf → **tidak layak** jadi dasar temuan. |
| **2 — TANDA ISI TERBATAS** | Artikel tanpa abstrak ditandai `isi_terbatas=True` → tampil ⚠️ + tidak boleh jadi dasar temuan. |
| **3 — TAMPILKAN SUMBER** | Abstrak ikut ke bahan AI **dan** ke layar → user bisa **membuktikan**. |

**Aturan yang disisipkan ke prompt AI:**
1. Tulis **HANYA** berdasarkan judul & abstrak yang diberikan
2. **JANGAN** menambah temuan/angka/nama penulis/tahun dari luar
3. Bahan tak cukup → jangan tulis klaimnya
4. Artikel "TANPA ABSTRAK" hanya boleh disebut judulnya

⇒ Sesuai 3 pilar Bos: **NYATA · TERKELOMPOK · TERPAGAR**.

---

## 4. KATA-KATA (perintah Bos)

❌ **DIHAPUS:** *"…supaya kamu bisa membukanya **sendiri** ya."*

✅ **4 pesan baru (semua jujur, tanpa menyuruh):**

| Keadaan | Pesan |
|---|---|
| Berkas berhasil | *"Artikel tersimpan di berkas naskahmu ya."* |
| Terbuka, berkas tak terambil | *"Artikelnya terbuka. Tautannya kami sertakan di bawah ini supaya kamu bisa memeriksanya langsung."* |
| Terbuka, tanpa tautan | *"Artikelnya terbuka, tapi berkasnya belum bisa kami ambil otomatis saat ini."* |
| Tersedia di penerbit | *"Artikel ini tersedia di penerbit. Tautannya kami sertakan di bawah ini."* |
| Abstrak tak ada | *"Abstrak artikel ini tidak dicantumkan. Tautannya kami sertakan supaya bisa kamu cek langsung."* |

**Bukti mata (vision):** *"TIDAK ADA tulisan menyuruh unduh/buka sendiri.
Kata 'sendiri' hanya di tombol 'Cari sendiri' & 'Tambah artikel sendiri'
(beda makna = benar)."* ✅

---

## 5. `pdf_url` DIAMBIL (bukan ditebak)

| Sumber | Cara | `is_oa` |
|---|---|---|
| **OpenAlex** | `open_access.oa_url` + `best_oa_location.pdf_url` | dari **data resmi OpenAlex** ✅ |
| **Garuda** | `tautan_garuda()` — halaman **DETAIL**, dipanggil **saat unduh saja** (supaya pencarian tetap cepat) | **False selalu** — bukan tebakan |
| **Crossref** | tidak punya link PDF → cukup link | — |

---

## 📊 BUKTI

| Gerbang | Hasil |
|---|---|
| **11 gerbang** | ✅ **469 LULUS / 0 GAGAL** |
| `periksa_kode.sh` | ✅ LULUS |
| Uji nyata Garuda | ✅ 5/5 abstrak terambil |
| Potret + vision | ✅ tak ada "unduh sendiri" |

**Uji bergigi pagar artikel — TERBUKTI BISA GAGAL:**

| Kerusakan disuntik | GAGAL |
|---|---|
| Pagar 1 dimatikan | **6** |
| Penanda isi terbatas dihapus | **3** |
| Artikel tanpa abstrak ikut jadi bahan | **2** |

| Gerbang | Lulus |
|---|---|
| jurnal · jurnal2 · jurnal3 | 21 · 60 · 53 |
| jatah · rute_jurnal | 42 · 62 |
| halaman_ref · kata_ref | 35 · 35 |
| ikon_ref · ikon_semua · ikon_asli | 55 · 76 · 5 |
| **pagar_artikel (baru)** | **25** |

---

## 6. ⚠️ MASIH TERBUKA (jujur)

1. **Belum deploy** — masih `docker cp`. Perubahan bisa HILANG kalau
   container dibangun ulang.
2. **Pagar baru belum diuji sampai AI benar-benar menulis** — baru diuji di
   tingkat modul (bahan + aturan). Uji ujung-ke-ujung butuh saldo token uji.
3. **Halaman belum menampilkan ⚠️ "isi terbatas"** — penanda sudah ada di
   data (`isi_terbatas`), tampilan ⚠️ di kartu artikel belum dipasang.
4. **OpenAlex kena batas harian** (tanpa API key) — pencarian OpenAlex bisa
   kosong kalau kuota bersama habis.

---

## 📁 Berkas

**Baru:** `app/pagar_artikel.py` · `_gerbang_pagar_artikel.py` ·
`CARA_MESIN_TAHU_ISI_ARTIKEL_06OKT2026.md` · laporan ini
**Diubah:** `app/pustaka.py` (pdf_url OpenAlex + `tautan_garuda` +
`lengkapi_tautan`, `is_oa` tak lagi ditebak) · `app/rute_jurnal.py` (kata-kata
+ `lengkapi_tautan`) · `app/kerangka.py` (sambung pagar) ·
`_gerbang_rute_jurnal.py` (R12c)
**Backup:** `_arsip/pre-unduh-pdf-06okt26/` + MD5 ✅
