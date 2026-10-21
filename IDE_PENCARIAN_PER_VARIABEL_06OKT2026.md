# 🎯 IDE — PENCARIAN PER VARIABEL (JUDUL → PISAH VARIABEL) (06 Okt 2026)

<!-- ⛔ SOT: IDE — DILARANG DIKODING -->
> # ⛔ IDE / USULAN — **DILARANG dikoding** sampai Bos bilang "mulai".
> Isi berkas ini = **gagasan menunggu putusan Bos**, BUKAN keadaan kini dan
> BUKAN rencana kerja aktif. ❌ JANGAN dibaca sebagai status proyek.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Arah Bos 06 Okt 2026 (verbatim):
> *"Jadi agar presisi dari sisi user, user bisa masukkan judul penelitian +
> keyword yang mau dia tambahkan jika ada (optional). Jadi output langsung kita
> pisahkan per variabel. Jadi kita bisa baca judul lalu hasilnya dipisahkan
> berdasar variabel dalam judul tersebut, jadi user dapat hasil yang lebih mudah
> dibaca."*
>
> Status: **BAHAN DISKUSI.** Belum diputuskan. DILARANG dikoding.

---

## 🎯 ARAH BOS → 4 hal

1. **User masukkan JUDUL PENELITIAN** (wajib).
2. **+ kata kunci tambahan** (OPTIONAL — kalau user mau menambahkan).
3. **Output DIPISAH PER VARIABEL** dari judul itu.
4. Tujuan: **user lebih mudah membaca** hasilnya.

Contoh:
```
Judul: "Pengaruh Kualitas Produk dan Harga terhadap Keputusan Pembelian
        dengan Citra Merek sebagai Variabel Mediasi"

Hasil diterima user (DIPISAH PER VARIABEL):
┌─ 🟦 Kualitas Produk ────────────── 12 artikel ─┐
│  1. ...                                          │
│  2. ...                                          │
├─ 🟩 Harga ────────────────────────── 9 artikel ─┤
│  1. ...                                          │
├─ 🟨 Citra Merek (perantara) ──────── 7 artikel ─┤
│  1. ...                                          │
├─ 🟥 Keputusan Pembelian ─────────── 15 artikel ─┤
│  1. ...                                          │
└──────────────────────────────────────────────────┘
```

Jadi user tidak melihat **satu tumpukan panjang 50 artikel**, tapi
**kelompok per variabel** — jauh lebih mudah dibaca.

---

## ✅ BUKTI KODE — MESINNYA SUDAH ADA & SUDAH TERBUKTI

### ⭐ `pustaka.py:449` — `konsep_dari_judul()`
**Ini persis mesin yang Bos butuhkan. Sudah ada, sudah hidup.**

```python
def konsep_dari_judul(judul: str) -> list[dict]:
    """Pecah judul penelitian → daftar KONSEP (bukan kata).

    Contoh:
      "Pengaruh Aktivitas Fisik terhadap Siklus Menstruasi pada Atlet Remaja"
      → [ {konsep:'aktivitas fisik', ...},
          {konsep:'siklus menstruasi', ...},
          {konsep:'atlet', ...},
          {konsep:'remaja', ...} ]
    """
```
- Pakai **`KAMUS_KONSEP`** (kamus konsep, bukan pecahan otomatis sembarangan).
- **Frasa panjang diperiksa dulu** — biar "siklus menstruasi" menang atas
  "menstruasi" (presisi).
- Dasarnya: **framework PICO/SPIDER** + pelajaran eduai-lab
  (*"kategori = DAFTAR PILIHAN, bukan pecahan otomatis"*).

### Mesin pendukung yang juga SUDAH ADA

| Fungsi | Letak | Guna untuk fitur ini |
|---|---|---|
| `konsep_dari_judul()` | `pustaka.py:449` | **pecah judul → variabel** ⭐ |
| `rumus_scopus()` | `pustaka.py:475` | susun query AND antar konsep |
| `rumus_openalex()` | `pustaka.py:494` | query per konsep inti |
| `rumus_crossref()` | `pustaka.py:509` | query per konsep |
| `konsep_id()` | `pustaka.py:519` | nama Indonesia dari konsep |
| `kata_kunci()` | `pustaka.py:530` | kata kunci dua bahasa |
| `_nyambung()` | `pustaka.py:556` | saring artikel yang nyambung |
| `audit_doi()` | `pustaka.py:381` | pastikan artikel NYATA |
| `kata_kunci_akademik()` | `konsistensi.py:222` | ambil istilah penting dari teks |
| `kemiripan_makna()` | `konsistensi.py:296` | ukur kemiripan makna |

⇒ **NOL mesin pemecah baru. Yang dibangun hanya TAMPILAN + pemanggilan.**

---

## 🎯 IDE WULAN — cara paling praktis

### Contoh nyata (Wulan jalankan konsepnya)

```
Judul: "Pengaruh Kualitas Produk dan Harga terhadap Keputusan Pembelian"

konsep_dari_judul()  →  [ kualitas produk, harga, keputusan pembelian ]

Lalu CARI PER KONSEP (bukan sekali cari untuk semua):
  cari("kualitas produk")      → 12 artikel → disaring
  cari("harga")                →  9 artikel → disaring
  cari("keputusan pembelian")  → 15 artikel → disaring
        ↓
   Semua audit DOI dulu → buang yang tak nyata
        ↓
   Tampilkan DIPISAH PER VARIABEL
```

### Kenapa cari per konsep lebih baik daripada sekali cari

| Sekali cari (cara sekarang) | **Cari per konsep (ide Bos)** |
|---|---|
| Hasil campur jadi satu tumpukan | **Kelompok per variabel** ⭐ |
| Satu konsep kuat menelan yang lain | Tiap variabel dapat bagian sendiri |
| User sulit menilai | User langsung lihat var mana yang kurang |

### Kata kunci tambahan (optional)

Bos minta user bisa **menambahkan** kata kunci. Ini berguna kalau:
- konsep tidak ada di `KAMUS_KONSEP` (kata baru/istilah khusus),
- user mau mempersempit (mis. "kualitas produk" + "UMKM"),
- user mau istilah asing (mis. "brand image").

⇒ Isi tambahan ini **digabung sebagai konsep ekstra**, ditampilkan sebagai
kelompok tambahan: **"🔎 Kata kunci tambahanmu"**.

---

## 📏 CARA MEMBUAT "PRESISI" (karena berbayar 1 token)

1. **Kata kunci yang dipakai DITAMPILKAN** — user lihat konsep apa saja yang
   diambil dari judulnya. Kalau ada yang salah baca → user bisa betulkan
   **sebelum** menekan Cari (hemat token!). Ini penting: **konfirmasi dulu,
   baru bayar.**
2. **Bisa dicoret/ditambah.** Judul "Pengaruh X dan Y terhadap Z pada UMKM di
   Jakarta" → muncul chip: `[X] [Y] [Z] [UMKM] [Jakarta]`. User bisa
   **mematikan** chip yang tidak perlu (mis. Jakarta) atau **menambah** sendiri.
   ⇒ Hasil jadi tepat sasaran, dan **user yang pegang kendali**.
3. **Audit DOI wajib** (sudah ada) — hanya artikel nyata.
4. **Skor kecocokan per artikel** + **jumlah per variabel** — biar user tahu
   var mana yang perlu kata kunci ditambah.
5. **Kalau satu variabel tidak dapat hasil** → katakan jujur per variabel:
   *"Kualitas Produk: 12 artikel · Harga: 9 · ⚠️ Citra Merek: belum ada,
   coba tambah kata kunci."* ⇒ **Jauh lebih berguna** daripada "0 hasil" global.
6. **Token kembali kalau SEMUA variabel kosong** — tapi kalau **ada** hasil
   (walau sedikit), token terpakai. Ini adil dua pihak.

---

## 🔗 MENYAMBUNG KE DISKUSI SEBELUMNYA

| Diskusi | Kaitan |
|---|---|
| **2 jalur** (AI auto + user cari) | Pencarian-per-variabel = versi **user** |
| **Berbayar 1 token** | Tetap berlaku; plus **konfirmasi kunci dulu** (hemat token user) |
| **Unduh ke workspace** | Hasil per variabel → tombol unduh per artikel, masuk workspace |
| **Anti-unduh-ganda** | Sama — tanda `[TERUNDUH]` |
| **Tab "Referensi"** | Hasil per variabel ditampilkan di dalam tab ini |

⇒ Semua diskusi hari ini **bertemu di satu tempat**: tab **📚 Referensi**,
dengan dua bagian: **🤖 Pilihan AI** (dari tema naskah) dan
**🔎 Pencarian Saya** (judul + kata kunci → dipisah per variabel).

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR

1. **`KAMUS_KONSEP` ada batasnya.** Konsep di luar kamus tidak terdeteksi
   otomatis → **inilah gunanya kata kunci tambahan** (dan "koreksi chip").
   Wulan **belum** memeriksa berapa banyak isi `KAMUS_KONSEP` — perlu diukur
   dulu sebelum menjanjikan akurasi.
2. **Variabel mediasi/moderasi** ("dengan Citra Merek sebagai mediasi") belum
   tentu terpisah otomatis — perlu diperiksa apakah `KAMUS_KONSEP` paham
   kata "mediasi/moderasi". Kalau tidak, perlu tabel kecil penanda peran.
3. **Biaya API naik.** Cari per konsep = **beberapa permintaan** (bukan satu).
   3 variabel = 3 kali cari. Perlu dipikirkan: 1 token = 1 pencarian
   (semua variabel) atau 1 token = 1 variabel?
4. **Hasil bisa tumpang tindih** — artikel tentang "kualitas produk" bisa juga
   muncul di daftar "keputusan pembelian". Perlu **dedup lintas variabel**
   (`_kunci_dedup()` sudah ada) + tanda "artikel ini juga muncul di var lain".

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **1 token = 1 pencarian judul** (semua variabel sekaligus), atau
   **1 token = 1 variabel**?
2. **Konfirmasi kata kunci dulu** (user bisa coret/tambah chip) sebelum
   bayar — setuju? (Wulan sarankan YA — hemat token user, hasil lebih presisi)
3. **Artikel yang muncul di 2 variabel** — tampil di dua-duanya, atau
   taruh di satu saja + tanda rujukan?
4. **Variabel mediasi/moderasi** diberi bagian sendiri + label peran?
5. **Kata kunci tambahan** — digabung ke pencarian, atau dicari terpisah
   sebagai bagian sendiri?
6. **Daftar pustaka akhir** — digabung semua variabel jadi satu, atau per
   variabel?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] Mesin diperiksa: `konsep_dari_judul()` **SUDAH ADA** di `pustaka.py:449`
- [ ] **PERLU DIUKUR DULU**: isi `KAMUS_KONSEP` (berapa konsep? paham
      mediasi/moderasi?) — JANGAN dijanjikan sebelum diukur
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
