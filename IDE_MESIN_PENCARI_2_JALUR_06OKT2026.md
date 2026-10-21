# 🔎 IDE — MESIN PENCARI 2 JALUR (AI OTOMATIS vs USER MANUAL) (06 Okt 2026)

<!-- ⛔ SOT: IDE — DILARANG DIKODING -->
> # ⛔ IDE / USULAN — **DILARANG dikoding** sampai Bos bilang "mulai".
> Isi berkas ini = **gagasan menunggu putusan Bos**, BUKAN keadaan kini dan
> BUKAN rencana kerja aktif. ❌ JANGAN dibaca sebagai status proyek.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Arah Bos 06 Okt 2026 (verbatim):
> *"Biaya API kan kita charge pemakaiannya di fitur berbayar jadi sudah ter-cover.
> Yang buat mesin pencari kita BERBEDA dengan yang lain adalah KEMUDAHAN dalam
> pencarian dan output sudah diKELOMPOKKAN agar mudah."*
> *"Kalo user ingin cari tidak berdasarkan judul juga bisa dengan keyword sendiri
> dengan tanda koma sebagai pemisah keyword."*
> *"Bagaimana ide ini agar menjadi menarik dan mudah bagi user, atau apa ide
> kamu yang lebih bagus lagi untuk mesin pencari 2 jalur ini dari AI otomatis
> dan dari user manual."*
>
> Status: **BAHAN DISKUSI.** Belum diputuskan. DILARANG dikoding.

---

## ✅ TITIK TERANG DARI BOS (ini yang mengubah arah)

> **Pembeda kita BUKAN biaya — tapi KEMUDAHAN + OUTPUT TERKELOMPOK.**
> Biaya API sudah ter-cover oleh fitur berbayar. Jadi jangan pelit fitur —
> **justru buat lebih mudah & lebih rapi dari yang lain.**

Ini penting: **gratis/pakai token bukan lagi pertimbangan utama** — yang
pertimbangan utama adalah **user senang & hasil enak dibaca**.

---

## 🎯 IDE WULAN — 3 PEMBEDA YANG BIKIN MESIN INI MENANG

### PEMBEDA 1 — "Tempel judul, selesai" (1 kotak, 30 detik)

Aplikasi lain: user harus mikir sendiri kata kunci apa.
Kita: **tinggal tempel judul skripsi** → mesin pecah sendiri.

```
┌─────────────────────────────────────────────────────────┐
│  Mau cari referensi apa?                                │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Pengaruh Kualitas Produk dan Harga terhadap       │  │
│  │ Keputusan Pembelian pada UMKM                     │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  (Opsional) kata kunci tambahan, pisah dengan koma:     │
│  ┌───────────────────────────────────────────────────┐  │
│  │ brand image, e-commerce                           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│               [ 🔍 Cari Referensi ]                     │
└─────────────────────────────────────────────────────────┘
```

### PEMBEDA 2 — "Hasil sudah rapi per variabel" (tanpa user mengelompokkan)

```
Terbaca dari judulmu — 5 kelompok:

🟦 Kualitas Produk ......... 12 artikel
🟩 Harga ...................  9 artikel
🟥 Keputusan Pembelian ..... 15 artikel
⬜ UMKM ....................  4 artikel
➕ Kata kunci tambahanmu:
   🟪 Brand Image ..........  7 artikel
```

**Semua sudah terdeteksi otomatis.** User tidak perlu menyusun apa pun.

### PEMBEDA 3 — "Kata kunci manual tetap bisa" (koma sebagai pemisah)

Kalau user tidak punya judul (atau mau cari bebas), tinggal:
```
brand image, e-commerce, minat beli
        ↓
🟪 Brand Image ............. 7 artikel
🟪 E-commerce .............. 5 artikel
🟪 Minat Beli .............. 8 artikel
```

⇒ **Dua mode dalam SATU kotak** — mesin yang sama, cuma beda cara user mengisi.

---

## 🧠 IDE TAMBAHAN WULAN (biar benar-benar "menarik & mudah")

### 1. Chip yang bisa dimatikan/ditambah (konfirmasi SEBELUM cari)
Setelah tempel judul, mesin tunjukkan konsep terdeteksi **sebagai chip**:
```
Konsep terdeteksi:  [✓ Kualitas Produk] [✓ Harga] [✓ Keputusan Pembelian]
                    [✓ UMKM]  [+ tambah]  [− kurangi]
```
User bisa **mematikan** yang tidak perlu (mis. "UMKM" → 4 artikel saja,
buang saja). ⇒ Hasil tepat sasaran, dan **user merasa memegang kendali.**

### 2. Tampilkan APA yang tidak dikenali (jujur & berguna)
Kalau judul punya istilah yang tidak ada di kamus:
```
⚠️ "Citra Merek" belum dikenali otomatis — tambahkan sebagai kata kunci?
   [ Ya, tambahkan ]
```
⇒ **Kelemahan kamus diubah jadi fitur** — user diberi tahu, bukan dibiarkan.
Mesin yang **jujur soal batasnya** lebih dipercaya daripada yang pura-pura tahu.

### 3. Per variabel: beri "cari lagi" sendiri
```
🟥 Keputusan Pembelian .... 15 artikel
   [ Lihat semua ]  [ Cari lagi variabel ini ]
```
⇒ Kalau user mau memperdalam satu variabel saja, tinggal tekan.

### 4. Bersihkan hasil (anti-tumpang-tindih)
Artikel yang muncul di 2 variabel → diberi tanda:
```
1. Pengaruh Kualitas Produk terhadap Keputusan Pembelian
   🟦 juga ada di: Keputusan Pembelian
```
⇒ Tidak dihapus (bisa memang relevan di dua-duanya), tapi **ditandai** biar
user tidak bingung melihat "artikel yang sama".

### 5. Simpan ke workspace sebagai berkas rapi
Tombol **"Simpan ke workspace"** → jadi satu berkas dengan kelompok per variabel
(nyambung diskusi berkas `Link Jurnal.txt` kemarin). Sudah diunduh → ditandai.

### 6. Ringkasan Bahasa Wulan (bukan angka kering)
Bukan cuma "12 artikel", tapi kalimat ringkas:
> *"Untuk judulmu ini, referensi paling banyak tersedia soal **Keputusan
> Pembelian** (15 artikel), paling sedikit soal **UMKM** (4). Bagian **Citra
> Merek** belum banyak — mungkin perlu kata kunci lain."*

⇒ User langsung tahu **harus berbuat apa**, bukan cuma melihat angka.

---

## 🔗 2 JALUR — CARA MENYATUKAN (tanpa bentrok)

| | 🤖 **Jalur AI (otomatis)** | 🔎 **Jalur User (manual)** |
|---|---|---|
| Sumber pertanyaan | tema **naskah** yang diunggah | **judul / kata kunci** yang diketik |
| Titik mulai | otomatis saat naskah siap | saat user menekan "Cari" |
| Kelompok | **per variabel dari judul naskah** | **per chip/kata kunci user** |
| Biaya | ikut paket (AI yang jalan) | **1 token** (user yang jalan) |
| Unduh | ke workspace | ke workspace |
| Tempat tampil | tab **📚 Referensi** — 2 bagian | tab **📚 Referensi** — 2 bagian |

**Mesin di bawahnya SAMA PERSIS** (`pustaka.cari_semua`, `konsep_dari_judul`,
audit DOI, saring, links). **Yang beda cuma "siapa yang mengisi pertanyaannya".**

⇒ **Tidak bentrok** karena bukan dua mesin — **satu mesin, dua pintu masuk.**

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR (TERUKUR, bukan dugaan)

### 🔴 `KAMUS_KONSEP` hanya **25 konsep** (terukur 06 Okt 2026)
Isinya: aktivitas fisik, siklus menstruasi, amenore, atlet, remaja, keputusan
pembelian, kualitas produk, harga, promosi, kepuasan kerja, kinerja karyawan,
kepemimpinan, motivasi, minat belajar, hasil belajar, dst.

**Artinya:**
- Judul dengan istilah **umum** (produk, harga, keputusan pembelian) → **jalan** ✅
- Judul dengan istilah **khusus/baru** (mis. "kesadaran halal", "green
  marketing", "e-wallet") → **TIDAK terdeteksi** ⚠️
- **Kabar baik:** `kata_kunci()` **tetap mengambil "sisa" kata** yang tak
  dikenali kamus → jadi istilah khusus **tetap dipakai** sebagai kata kunci
  tambahan, hanya **tidak terkelompok rapi**.

⇒ **Kesimpulan jujur:** fitur ini **jalan bagus** untuk judul umum (mayoritas
skripsi), dan **tetap berguna** untuk judul khusus — hanya kelompoknya tidak
sehalus yang umum. **Ini bisa diperbaiki nanti dengan menambah kamus.**

### Hal lain yang perlu diingat
1. **Tanda koma BELUM didukung** — terukur, tidak ada `split(',')` di
   `pustaka.py`. Perlu ditambahkan (mudah, tapi **belum ada**).
2. **Pemecahan judul bergantung kamus** — bukan AI. Kalau Bos mau lebih pintar
   (mis. paham "mediasi/moderasi"), pilihannya: **(a) tambah kamus** (murah,
   cepat, deterministik) atau **(b) pakai AI** (pintar, tapi ada biaya + bisa
   salah). **Wulan sarankan (a) dulu**, AI hanya kalau kamus gagal.
3. **Cari per variabel = beberapa permintaan API** (3 variabel = 3 cari).
   Karena sudah berbayar, **tidak masalah** — tapi perlu **sopan ke API**
   (jangan sampai kena batas Scopus/OpenAlex).
4. **Scopus belum ada kuncinya** di produksi → jurnal internasional terbatas
   pada OpenAlex + CrossRef (tetap jalan, hanya tidak selengkap Scopus).

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **Pemecah judul: tambah kamus** (murah, deterministik) atau **pakai AI**
   (pintar, berbiaya)? — Wulan sarankan **tambah kamus dulu**.
2. **1 token = 1 pencarian judul** (semua variabel sekaligus) — setuju?
3. **Chip bisa dimatikan** sebelum cari (hemat + presisi) — perlu?
4. **Ringkasan Bahasa Wulan** ("paling banyak… paling sedikit…") — perlu?
5. **Tanda koma** untuk kata kunci manual — setuju? (perlu ditambahkan)
6. **Kalau istilah tak dikenali** — tawarkan jadi kata kunci tambahan (usul
   Wulan), atau diabaikan saja?
7. **Kamus** — apakah Bos mau Wulan **kumpulkan istilah umum** (dari judul-judul
   skripsi nyata) supaya kamusnya tumbuh? Berapa target (mis. 100 konsep)?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **SUDAH DIUKUR**: `KAMUS_KONSEP` = 25 konsep (jujur, bukan dugaan)
- [x] `konsep_dari_judul()` SUDAH ADA (`pustaka.py:449`)
- [x] Tanda koma **BELUM** didukung (terukur)
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
