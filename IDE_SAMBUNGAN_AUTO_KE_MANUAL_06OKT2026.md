# 🔗 SAMBUNGAN AUTO AI → MANUAL (06 Okt 2026)

> Pertanyaan Bos 06 Okt 2026 (verbatim):
> *"Trus kalau user tidak cocok artikelnya, dan mau menambah manual. Bagaimana?
> Apakah bisa disambung ke manual? Atau itu jadi rumit?"*

---

## 🎯 JAWABAN WULAN: **BISA DISAMBUNG — dan ternyata BOS SUDAH PERNAH MEMUTUSKAN INI**

Wulan cek kode (`kerangka.py`), dan **pagarnya sudah tertulis di sana**.
Ini **bukan usulan baru** — ini **melanjutkan keputusan Bos yang sudah ada**.

---

## 📌 KEPUTUSAN BOS YANG SUDAH ADA (26 Sep 2026, tertulis di kode)

Tertulis verbatim di `kerangka.py:11-15`:
```
📌 PUTUSAN BOS (26Sep26, 5 butir — TERKUNCI):
   Q1. Panjang      = 5 sub-bab · 3-5 poin tiap sub-bab
   Q2. Masuk naskah = panel rencana DULU → [Masukkan ke naskah]
   Q3. Artikel <5   = J U J U R + 3 PILIHAN (ubah kk / lanjut / batal)  ⭐
   Q4. Bab dulu     = BAB I saja
   Q5. Gagal        = token kembali + lonceng
```

### ⭐ **Q3 = JAWABAN PERTANYAAN BOS SEKARANG**

Bos **sudah pernah memutuskan** apa yang terjadi kalau artikelnya kurang/ tidak
cocok: **JUJUR + 3 PILIHAN**. Tertulis juga di pagar berkas (baris 13):
```
Q3. Artikel <5 = jujur + 3 pilihan (ubah kk / lanjut / batal)
```
Dan ambangnya juga ada: `ARTIKEL_MIN = 5` (`kerangka.py:34`).

⇒ Jadi **jawabannya: BISA, dan Bos sendiri sudah merancangnya.**

---

## 🎯 IDE WULAN — 4 pintu (bukan 3), biar "tambah manual" masuk

Pagarnya sekarang sudah punya **3 pilihan**. Wulan usulkan **tambah 1** —
inilah sambungan ke pencarian manual yang Bos tanyakan:

```
📚 Artikel yang ditemukan: 3 (kurang dari 5)

  1. Yusnia (2020) — Customer Experience...  ✅ NYATA  🟢 PDF gratis
  2. Smith (2021) — The Role of...           ✅ NYATA  🔒 Berlangganan
  3. Lee (2019) — Analisis...                ✅ NYATA  🟢 PDF gratis

  Apa yang mau kamu lakukan?

  (a) 🔄 Ubah kata kunci — coba lagi (GRATIS, masih Tahap 2)
  (b) ➕ Cari sendiri / tambah manual   ← ⭐ IDE WULAN (sambungan ke manual) ⭐
  (c) ➡️  Lanjut saja pakai 3 artikel ini (lanjut ke tulis bab — bayar token)
  (d) ❌ Batal
```

⇒ **(b) itu jawaban pertanyaan Bos**: user tidak cocok → bisa **cari sendiri**,
**tanpa keluar** dari alur.

---

## 🔑 KENAPA INI **TIDAK RUMIT** (alasan teknis, terukur)

Wulan cek: **mesinnya SUDAH SATU.**

| Bagian | Auto AI | Manual |
|---|---|---|
| Mesin cari artikel | `pustaka.cari_semua()` | **`pustaka.cari_semua()` — SAMA** |
| Audit DOI | `audit_doi()` | **SAMA** |
| Penyaring relevansi | `_pilih_relevan()` (`kerangka.py:406`) | **SAMA** |
| Susun daftar pustaka | `daftar_pustaka_apa7()` | **SAMA** |

⇒ **Tidak ada mesin kedua yang harus dibangun.**
Pencarian manual **sudah memakai mesin yang sama** — jadi menyambungnya
**hanya soal tampilan**, bukan bongkar-membangun.

---

## 🎯 CARA SAMBUNG YANG WULAN USULKAN (paling murah & rapi)

### Alur yang mulus:
```
User tulis judul
      ↓
Auto AI cari → 3 artikel (kurang)
      ↓
User tekan (b) "Cari sendiri / tambah manual"
      ↓
   ┌── Judul dari AI SUDAH TERISI otomatis di kotak ──┐
   │  User tinggal: tambah kata kunci (pisah koma)    │
   │  [ kualitas produk, brand image ]                │
   └──────────────────────────────────────────────────┘
      ↓
Hasil manual DITAMBAHKAN ke daftar yang sudah ada
(artikel AI + artikel manual = SATU daftar)
      ↓
User lihat daftar GABUNGAN → pilih mana yang dipakai
      ↓
Tekan "Setuju" → tulis bab (bayar token)
```

⇒ **Judul tidak perlu diketik ulang.** User tidak keluar dari alur.
**Hasil lama tidak hilang** — ditambah, bukan diganti.

### Yang perlu diputuskan: apakah "tambah manual" ini kena token?

| Pilihan | Artinya |
|---|---|
| **A. Gratis** (1×, sekali per alur) | Ramah — user tidak dihukum karena AI kurang | 
| **B. Kena 1 token** | Konsisten dengan aturan "manual = 1 token" |
| **C. Masuk jatah 2×/minggu** | Sama seperti manual lain |

⚠️ **Ini Wulan TIDAK putuskan sendiri** — Bos yang tentukan.
(Wulan condong **A untuk 1× pertama** — karena user sedang "menambal" hasil AI
yang kurang, bukan mencari dari nol. Tapi tetap Bos yang putuskan.)

---

## 🧩 BENTUK PENYIMPANAN YANG WULAN USULKAN

Artikel dari **dua jalur disatukan** dengan penanda asal:

```
Daftar artikel untuk bab ini:
 1. Yusnia (2020) ...    🔵 dari AI
 2. Smith (2021) ...     🔵 dari AI
 3. Brand Image (2022)   🟢 saya cari
 4. Repurchase (2021)    🟢 saya cari
```

⇒ User **selalu tahu** mana dari AI, mana carinya sendiri.
**Tidak tercampur diam-diam** — tapi juga **tidak dipisah jadi dua tempat**
(satu daftar, satu daftar pustaka).

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR

1. **Pagarnya SUDAH ADA di kode** (Q3, `ARTIKEL_MIN = 5`) — tapi Wulan **belum
   memeriksa** apakah **tampilan 3 pilihannya sudah dibuat di layar**.
   ⇒ **Perlu dicek dulu** sebelum menjanjikan.
2. **Pilihan (b) "cari sendiri" belum ada** — itu **tambahan Wulan**, belum
   pernah diputuskan Bos. **Perlu keputusan Bos.**
3. **Kalau user menambah manual terus-terusan** → berisiko jadi celah gratis
   (pintu masuk untuk "cari gratis"). ⇒ Butuh pagar (lihat pertanyaan di atas).
4. **Artikel gabungan harus diaudit DOI SEMUA** (termasuk yang manual) —
   supaya tidak ada yang lolos tanpa verifikasi. Mesin `audit_doi()` bisa.
5. **Semua ini BELUM dikoding** — yang ada baru **kerangka keputusan** di kode.

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **"Tambah manual" saat artikel AI kurang** — perlu? (Wulan sarankan YA,
   karena Bos sendiri sudah memutuskan pola "jujur + pilihan" di Q3)
2. Kalau ya: **kena token, atau gratis** (sekali per alur)?
3. **Hasil AI + hasil manual digabung jadi SATU daftar** — setuju?
4. **Judul otomatis terisi** di kotak manual (tidak usah ketik ulang) — setuju?
5. Kalau sudah gabungan, **tulis bab pakai semua** — atau user bisa memilih
   **artikel mana saja** yang dipakai?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **TERUKUR**: pagar Q3 **sudah diputuskan Bos** 26 Sep (`kerangka.py:11-15`)
- [x] Mesin Auto AI & Manual **SUDAH SATU** (`pustaka.cari_semua`) → tidak rumit
- [ ] **PERLU DICEK**: apakah tampilan 3 pilihan sudah ada di layar
- [ ] Ditunggu putusan Bos (terutama: "tambah manual" gratis atau token)
- [ ] DILARANG dikoding sebelum Bos bilang mulai
