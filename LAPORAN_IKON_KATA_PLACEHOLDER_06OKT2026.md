# ✅ IKON LUCIDE + PLACEHOLDER PENDEK + PERBAIKAN KATA (06 Okt 2026)

> Permintaan Bos: "Perpendek place holder dan cek icon icon di aplikasi masih
> standard, kan kita punya icon yang menarik sebelumnya, pakai lah ikon yang
> bagus" + sebelumnya "jangan pakai kata jatah ganti kata kata yang bagus"
> + "Kata 'Gratis' saja" (→ diganti).

---

## ✅ SELESAI & TERUJI

### 1. 🐛 BUG NYATA — kotak kesempatan MACET "Memuat…"

**Gejala:** akun yang BELUM punya naskah → kotak jatah macet selamanya.

**Akar (1 kalimat):** `muat()` di `referensi.html` **berhenti lebih dulu**
(`if(!fid){...return}`) sebelum `gambarJatah()` dipanggil — padahal kuota itu
milik **USER**, bukan naskah.

**Lokasi:** `app/templates/referensi.html` fungsi `muat()` (cabang tanpa naskah).

**Perbaikan:** rute baru `/api/ai/v1/jurnal/kesempatan` (tanpa `file_id`) +
panggil `await gambarKesempatan()` **sebelum** `return`.

**Bukti mata:** *"Sudah menampilkan angka (2). Teks: `Kamu punya 2 pencarian
tanpa Token minggu ini`."*

**Pelajaran bergigi:** gerbang otomatis 35/0 LULUS tapi bug ini LOLOS —
ketemu HANYA dari potret + vision. ⇒ **potret + mata wajib, bukan pelengkap.**

### 2. ✍️ Ganti kata (perintah Bos)

| Sebelum | Sesudah |
|---|---|
| Memuat **jatah**… | Kamu punya **2 pencarian tanpa Token** minggu ini |
| **GRATIS** | **TANPA TOKEN** |
| 2× **gratis** | 2× **tanpa Token** |
| **jatah gratis**nya kembali | pencarian **tanpa Token** kembali |
| 1 token / pencarian | 1 **Token Revisi** |

Alasan pilih "tanpa Token": kata "gratis" di aplikasi berbayar bisa bikin salah
paham (user mengira semua bebas). "tanpa Token" jelas: tetap bisa dipakai,
tapi tidak mengurangi Token Revisi.

Diterapkan di: `models.pesan_jatah()`, `jatah.pesan_tidak_cukup_saldo()`,
dan seluruh teks `referensi.html`.

**Bukti mata:** *"Kata 'jatah' maupun 'gratis' sudah tidak ditemukan sama
sekali di seluruh halaman."*

### 3. 🎨 Ikon — emoji → Lucide (56 ikon sprite SUDAH ADA)

**Temuan penting:** EduAi **SUDAH PUNYA** sprite Lucide
(`app/static/ikon/lucide.svg`, 56 ikon) + makro `{{ ikon('nama', ukuran) }}`
+ `ikon.css` — **ACC Bos 15Sep26**, bukan dibangun baru. ⇒ mengikuti aturan
"pakai yang sudah ada".

**Yang diperbaiki:**

| Halaman | Sebelum | Sesudah |
|---|---|---|
| referensi.html | 16 emoji (🤖🔎📚➕✅⚠️🗑️🔗) | 0 emoji → semua Lucide |
| referensi.html | sprite **BELUM** dimuat | sprite + `ikon.css` dimuat |
| naskah.html | tab 🎓📚 | `graduation-cap` + `book-open` |
| kolaborasi.html | tab 🎓📚 · **tanpa** sprite/css | Lucide + sprite + css |
| belajar.html | tab 🎓📚 | Lucide |

Ikon dipakai: `book-open` · `sparkles` · `search` · `file-plus` ·
`shield-check` · `shield-alert` · `trash-2` · `external-link` ·
`graduation-cap`.

**⚠️ ATURAN (kesalahan Wulan yang berulang):** GREP dulu setiap nama ikon
sebelum menulis — JANGAN mengarang. Gerbang I3 memeriksa **semua** nama ikon
yang dipakai benar-benar ada di sprite (39 nama dicek vs 56 tersedia).

### 4. 📏 Placeholder diperpendek

| Sebelum | Sesudah |
|---|---|
| `mis. kualitas produk, keputusan pembelian` (44) | `mis. kualitas produk` (20) |
| `mis. pengaruh harga terhadap keputusan pembelian` (50) | `mis. pengaruh harga` (19) |
| `mis. 10.1016/j.jbusres.2020.01.001` (34) | `mis. 10.1016/j.jbusres` (22) |
| `mis. Susanti, A. & Pratama, B.` (31) | `mis. Susanti, A.` (16) |

**Bukti mata:** *"placeholder ... pendek, jelas, dan tidak terpotong."*

---

## 📊 BUKTI

| Gerbang | Hasil |
|---|---|
| jurnal · jurnal2 · jurnal3 | ✅ 21 · 60 · 53 / 0 |
| jatah · rute_jurnal | ✅ 42 · 62 / 0 |
| halaman_referensi | ✅ 35 / 0 |
| kata_referensi | ✅ 35 / 0 |
| **ikon_referensi (baru)** | ✅ **55 / 0** |
| **TOTAL** | **✅ 363 LULUS / 0 GAGAL** |
| `periksa_kode.sh` | ✅ LULUS |
| Halaman ter-render | ✅ 4/4 → 200 + sprite ADA |
| Ikon ter-render (CDP) | ✅ **9 ikon Lucide** (bukan emoji) |

**UJI BERGIGI terbukti:**
- Masukkan emoji 🤖 lagi → **2 GAGAL** ✅
- Panjangkan placeholder → harus GAGAL ✅

## ⚠️ Catatan jujur

1. **124 emoji masih ada di template LAIN** (naskah 40, belajar 4, kolaborasi 2,
   + halaman lain: ⚠ ✓ 🐛 🟡 📄 ✨ dll). **BELUM Wulan ganti** — itu di luar
   lingkup tab + Referensi. Perlu keputusan Bos apakah diganti semua.
2. **Nama fungsi internal** masih `gambarJatah`/`pesan_jatah` — tidak terlihat
   user, sengaja dibiarkan supaya kode nyambung.
3. **Belum deploy** ke image produksi — menunggu izin Bos.
4. **Pelajaran uji:** 4 GAGAL PALSU ketemu (uji usang menuntut kata lama yang
   Bos suruh ganti). Uji harus ikut berubah saat aturan bahasa berubah.

---

## 📁 Berkas

**Baru:** `_gerbang_kata_referensi.py` (35 uji) · `_gerbang_ikon_referensi.py` (55 uji)
**Diubah:** `referensi.html` (bug + kata + ikon + placeholder) · `models.py`
(`pesan_jatah`) · `jatah.py` (`pesan_tidak_cukup_saldo`) · `rute_jurnal.py`
(rute `/kesempatan`) · `naskah.html`/`kolaborasi.html`/`belajar.html` (tab +
sprite) · `_gerbang_halaman_referensi.py` (uji diperbarui).
