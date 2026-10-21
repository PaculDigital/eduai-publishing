# 🚀 DEPLOY SUKSES (06 Okt 2026, 17:25 UTC)

> Perintah Bos: **"A"** (deploy supaya permanen)

---

## Image

| | |
|---|---|
| **LIVE** | `eduai-app:20261006_172538-sot` |
| **Titik mundur** | `eduai-app:cadangan-pra-sot` |
| **Sebelumnya** | `eduai-app:20261006_083031-sot` |
| **Backup DB** | `_arsip/pra-sot/20261006_172333-sot` |
| **URL** | `http://127.0.0.1:8000` (host: 127.0.0.1:8100) |

---

## ⚠️ TEMUAN SAAT DEPLOY (akar, bukan tambalan)

**Masalah:** Gerbang keaslian ikon gagal di produksi (lapor **"62 beda" PALSU**)
karena `jalankan.sh` **tidak pernah menyalin** simpanan wujud resmi
`_ikon-asli/*.txt` → tiap deploy menghapusnya → gerbang baca **kosong**.

**Ini kesalahan yang SAMA PERSIS** seperti `_contoh-dokumen` (16 Sep 2026) —
sudah pernah terjadi, tercatat di `jalankan.sh` sendiri, tapi **tidak
diterapkan** ke berkas baru.

**Perbaikan permanen:** tambahkan blok ke `jalankan.sh` (IKUT POLA yang sudah
ada, bukan bikin mekanisme baru):

```sh
if [ -d "$PROYEK/_ikon-asli" ]; then
  ... docker cp → periksa jumlah → lapor ✅/⚠️ ...
fi
```

**Hasil:** `✅ Wujud resmi ikon tersalin: 64 berkas (gerbang keaslian bisa
jalan offline)`

**Pelajaran:** setiap berkas pendukung BARU harus diperiksa — apakah
`jalankan.sh` menyalinnya? Kalau tidak → **hilang tiap deploy**.

---

## 📊 VERIFIKASI PASCA-DEPLOY

### Container & data
| | |
|---|---|
| Container dari image | ✅ `eduai-app:20261006_172538-sot` |
| `/health` | ✅ 200 |
| Berkas kode identik source | ✅ 4/4 (pagar_artikel, pustaka, rute_jurnal, kerangka) |
| Simpanan ikon di produksi | ✅ **64** berkas |
| Sprite ikon | ✅ **64** ikon |
| Modul `pagar_artikel` | ✅ ADA (aturan_prompt 389 huruf) |
| DB | ✅ 25 tabel · 7 user · 52 berkas |

### Halaman hidup (semua 200)
`/` · `/masuk` · `/naskah` · `/referensi` · `/belajar` · `/kolaborasi` ✅

### 11 gerbang = **469 LULUS / 0 GAGAL**
| Gerbang | Lulus |
|---|---|
| jurnal · jurnal2 · jurnal3 | 21 · 60 · 53 |
| jatah · rute_jurnal | 42 · 62 |
| halaman_ref · kata_ref | 35 · 35 |
| ikon_ref · ikon_semua · ikon_asli | 55 · 76 · 5 |
| pagar_artikel | 25 |

> ⚠️ Catatan: gerbang **tidak ikut ke image** (memang rancangan:
> `COPY app ./app` saja). Dijalankan dari salinan penuh — 13 gerbang tersedia.

### Gerbang Editor OnlyOffice
✅ LULUS — `oo-converter` terjangkau · `/oo/aset` 200 · kunci COCOK ·
`api.js` 200 · tak ada `Editor.bin` ditolak.

### Audit MATA (vision, dari produksi)
> *"Halaman tampil normal, tidak ada error. Seluruh ikon menggunakan gaya
> garis/vektor yang rapi, profesional, konsisten — bukan emoji. Tidak ada
> yang rusak atau tumpang tindih."*

---

## ✅ YANG SUDAH PERMANEN (tidak bisa hilang lagi)

1. Fitur jurnal Langkah 1–6
2. 64 ikon Lucide di **semua** halaman (0 emoji tampil)
3. **Pagar artikel** (jawaban "tanpa halusinasi")
4. `pdf_url` dari OpenAlex + Garuda (tautan, bukan tebakan)
5. Kata-kata baru (tanpa "unduh sendiri")
6. `jalankan.sh` menyalin `_ikon-asli` otomatis

## ⚠️ MASIH TERBUKA (jujur)

1. Tanda ⚠️ "isi terbatas" **belum tampil** di kartu artikel (penanda sudah
   ada di data, tampilannya belum).
2. Pagar baru belum diuji **sampai AI benar-benar menulis** (butuh saldo token uji).
3. OpenAlex **kena batas harian** tanpa API key.
4. 8 dari 13 gerbang ikut disalin; sisanya (`_gerbang_*` lama) belum diperiksa
   apakah masih relevan.

## 📁 Berkas
**Diubah:** `jalankan.sh` (+blok `_ikon-asli`)
**Backup:** `_arsip/pre-deploy-unduh-pdf-06okt26/` (8 berkas + MD5.txt)
**Laporan:** `LAPORAN_UNDUH_PDF_JUJUR_06OKT2026.md` ·
`CARA_MESIN_TAHU_ISI_ARTIKEL_06OKT2026.md`
