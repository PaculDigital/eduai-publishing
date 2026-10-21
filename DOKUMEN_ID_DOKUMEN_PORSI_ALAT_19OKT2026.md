<!-- 📌 SOT: ID dokumen → porsi alat. Status HITUNG dari kode: _gerbang_porsi_alat.py + _uji_id_buku_ke_alat.py + periksa_kode.sh. Sumber resmi tetap SOT.md -->
# 🎯 ID DOKUMEN → PORSI ALAT — 19 OKT 2026

> **ACC Bos 19 Okt 2026 (verbatim):**
> "Dan yang jelas harus punya id sendiri Antr naskah, jurnal dan buku agar
> enggunakan jev dan hakim tepat dan tidak salah alat, tau ini dokumen perlu
> jev , hakim atau tidak, kalo perlu sudah sesuai porsinya."

**STATUS: KODE SIAP, GERBANG LULUS, BELUM DEPLOY.**

---

## 1. MASALAH YANG DITUTUP

Sebelum hari ini, **buku tidak punya ID**. Daftar jenis dokumen di
`app/jenis.py` hanya 6 (skripsi…dokumen_umum) — **buku tidak termasuk**.
Akibatnya alat dipilih dari **tebakan isi naskah**, bukan dari identitas.
Kalau ada yang menyuruh Jev memetakan buku, Jev akan menganggapnya naskah
akademik biasa ⇒ **salah alat** (persis yang Bos takutkan).

---

## 2. YANG DIBUAT (NOL tabel baru, NOL dompet baru)

### Lapis 1 — `app/jenis.py`

| Tambahan | Isi |
|---|---|
| 5 konstanta ID buku | `buku_ajar` · `buku_umum` · `buku_monograf` · `book_chapter` · `buku_referensi` |
| `JENIS_BUKU` (tuple) | daftar 5 ID itu |
| `LABEL_JENIS` +5 | nama tampil tiap buku |
| `STANDAR` +5 | aturan per jenis buku (hipotesis 0, kedalaman, catatan) |
| **`PORSI_ALAT`** | tabel **ID → {jev, hakim, mutu_buku}** — SATU SUMBER KEBENARAN |
| `PORSI_ALAT_TAK_DIKENAL` | semua `False` — ID tak dikenal **tidak menebak** |
| `porsi_alat()` · `perlu_jev()` · `perlu_hakim()` · `perlu_mutu_buku()` · `apakah_buku()` | pembaca tabel (mengembalikan **salinan**, tabel tak bisa dirusak pemanggil) |

`JENIS_AKADEMIK` **TIDAK diubah** — perilaku lama aman.

### Lapis 2 — `app/buku.py`

`id_dokumen(kode_kartu)` — penerjemah **satu-satunya** antara kartu layar
(`buku-umum`, pakai strip) dan identitas (`buku_umum`, pakai garis bawah).
ID tak dikenal → `''`.

### Lapis 3 — `app/main.py` rute `/buku/susun`

Dua penjaga, dipasang **SEBELUM kuota dipotong**:
1. `id_dok` kosong → tolak ("belum punya identitas — lapor admin")
2. `porsi['jev'] or porsi['hakim']` hidup untuk buku → tolak ("susunan alat salah")

Alasan urutan: kalau penjaga di belakang, user bisa **kehilangan token**
karena kesalahan sistem.

---

## 3. TABEL PORSI ALAT (yang berlaku sekarang)

| ID dokumen | Jev | Hakim | Pemeriksa mutu buku |
|---|---|---|---|
| `skripsi` | ✅ | ✅ | — |
| `tesis` | ✅ | ✅ | — |
| `disertasi` | ✅ | ✅ | — |
| `artikel_jurnal` | ✅ | ✅ | — |
| `proposal` | ✅ | ✅ | — |
| `buku_ajar` | ❌ | ❌ | ✅ |
| `buku_umum` | ❌ | ❌ | ✅ |
| `buku_monograf` | ❌ | ❌ | ✅ |
| `book_chapter` | ❌ | ❌ | ✅ |
| `buku_referensi` | ❌ | ❌ | ✅ |
| `dokumen_umum` | ❌ | ❌ | — |
| **tak dikenal** | ❌ | ❌ | — |

⚠️ **BELUM DIPUTUSKAN (menunggu Bos):** apakah `buku_ajar` / `book_chapter`
boleh memakai Jev **hanya untuk memetakan bab** (bukan menilai mutu). Sekarang
diputuskan **TIDAK** — kalau Bos mau, ubah 1 baris di `PORSI_ALAT`.

---

## 4. GERBANG

```bash
cd /opt/data/services/eduai-publishing

/opt/data/.venv/bin/python _gerbang_porsi_alat.py    # 138/0
/opt/data/.venv/bin/python _uji_id_buku_ke_alat.py   #  55/0
bash scripts/periksa_kode.sh                         # LULUS (keduanya sudah masuk)
```

**KEDUANYA TERBUKTI BERGIGI (bukan gerbang hiasan):**

| Suntikan | Hasil |
|---|---|
| `buku_umum` dikirim ke Jev | ❌ 2 GAGAL |
| `skripsi` kehilangan Jev | ❌ 1 GAGAL |
| ID tak dikenal menebak Jev | ❌ 7 GAGAL |
| penjaga ID dicabut dari rute | ❌ 1 GAGAL |
| cek porsi dihapus dari rute | ❌ 1 GAGAL |
| penjaga dipindah setelah potong kuota | ❌ 1 GAGAL |
| suntikan ke `jenis.py` lalu `periksa_kode.sh` | ⛔ **"JANGAN DEPLOY"** |

---

## 5. JEBAKAN YANG SUDAH MENGGIGIT (19 Okt 2026)

| # | Jebakan | Akibat terukur | Obat |
|---|---|---|---|
| 1 | **Gerbang palsu karena KOMENTAR** | Uji memeriksa nama fungsi di badan fungsi; nama itu JUGA ada di komentar Wulan ⇒ suntikan "penjaga dicabut" lolos 55/0 | Buang `#...` + docstring **sebelum** memeriksa kode |
| 2 | **Gerbang palsu karena regex** | Pola `def buku_susun\((.*?)\n@_router` tidak pernah cocok ⇒ `badan=''` ⇒ semua `in` bernilai False… tapi cek lama tidak menyadarinya | Regex `def X\(.*?(?=\n@_router|\Z)` + asersi **panjang badan > 300** |
| 3 | **Gerbang menuduh data yang BENAR** | Gerbang menuntut semua buku `wajib_novelty=False`, padahal **monograf memang wajib** bertumpu temuan | Bedakan: hipotesis=0 untuk SEMUA buku; novelty bergantung jenis |
| 4 | Strip vs garis bawah | `buku-umum` ≠ `buku_umum` ⇒ ID tak dikenal, buku ditolak | Penerjemah di SATU tempat (`_buku.id_dokumen`) |

---

## 6. BELUM (jujur)

- **Belum deploy.** Kode di host, produksi masih image `20261019_035552-sot`.
- Buku **belum disimpan** ke tabel `files` dengan ID-nya — rute `/buku/susun`
  masih menyimpan berkas di folder, bukan membuat baris dokumen. Ini kerjaan
  berikutnya (nyambung ke assembly DOCX + OnlyOffice).
- `PORSI_ALAT` **belum dipakai** di jalur peta (`/v1/peta/*`) dan konversi —
  hari ini baru dipakai di rute buku. Pemakaian di jalur lama = pekerjaan
  lanjutan, harus 1 deploy terpisah.
- Deteksi otomatis `app/jenis.py::deteksi()` masih 6 jenis; buku **tidak
  ditebak dari isi** (memang sengaja — buku datang dari kartu, bukan unggahan).

---

## 7. CARA BALIK

```bash
cd /opt/data/services/eduai-publishing
cp _arsip/jenis.py.pra-buku-id-19okt app/jenis.py
# main.py: hapus blok "── ID DOKUMEN (ACC Bos 19 Okt 2026)" di rute buku_susun
# buku.py: hapus id_dokumen()
```
