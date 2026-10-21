# 💰 IDE — PENCARIAN JURNAL OLEH USER = BERBAYAR 1 TOKEN (06 Okt 2026)

<!-- ⛔ SOT: IDE — DILARANG DIKODING -->
> # ⛔ IDE / USULAN — **DILARANG dikoding** sampai Bos bilang "mulai".
> Isi berkas ini = **gagasan menunggu putusan Bos**, BUKAN keadaan kini dan
> BUKAN rencana kerja aktif. ❌ JANGAN dibaca sebagai status proyek.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Arah Bos 06 Okt 2026 (verbatim):
> *"Untuk membatasi, user cari sendiri adalah fitur berbayar 1 token tiap
> pencarian, agar user tidak kebanyakan cari dan misal akhirnya tidak terpakai
> dan saya bisa kontrol resource vps. Dan gak rugi."*
> *"Tapi catatan harus presisi hasil pencariannya. Karena berbayar."*
>
> Status: **BAHAN DISKUSI.** Belum diputuskan. DILARANG dikoding.

---

## ✅ KEPUTUSAN YANG BOS SUDAH AMBIL (06 Okt 2026)

| Hal | Putusan Bos |
|---|---|
| **Pencarian jurnal oleh USER** | **BERBAYAR — 1 token per pencarian** |
| Alasan | (a) user tidak kebanyakan cari; (b) hasil tak terpakai = rugi; (c) kontrol resource VPS; (d) tidak rugi |
| Syarat mutlak | **Hasil WAJIB PRESISI** — karena user sudah bayar |
| **Auto Harvest oleh AI** | (implisit) tetap gratis/paket — karena AI yang tentukan, bukan user |

---

## 🔍 BUKTI KODE — MESINNYA SUDAH ADA, JANGAN BIKIN BARU

### A. Dompet token (`app/saldo.py`) — SUDAH LENGKAP ✅
| Fungsi | Baris | Guna |
|---|---|---|
| `sisa(db, u)` | 54 | cek sisa saldo |
| `masuk(db, u, jumlah, sumber)` | 68 | saldo masuk |
| `pakai(db, u, jumlah, sumber, catatan)` | 88 | **POTONG saldo** — raise `ValueError` kalau kurang → pemanggil ubah ke **HTTP 402** |
| `kembalikan(db, u, jumlah, sumber)` | 107 | **kembalikan saldo** — komentar di kode: *"pagar P2: fitur gagal → saldo utuh"* |
| `rincian(db, u, batas)` | 114 | riwayat token (untuk tampilan "token saya dari mana") |

### B. Gerbang kuota (`app/kuota.py`) — SUDAH LENGKAP ✅
| Fungsi | Baris | Guna |
|---|---|---|
| `cek_dan_potong(db, u, jenis)` | 292 | cek + potong sekali jalan |
| `potong_banyak(db, u, butuh)` | 487 | **potong untuk N permintaan** ← cocok untuk pencarian |
| `kembalikan_banyak(db, u, jumlah)` | 579 | kembalikan kalau gagal |
| `saldo_token(db, u, jenis_addon)` | 461 | info saldo (balas DICT) |
| `_admin(u)` | 50 | admin sengaja TIDAK dipotong |

⇒ **NOL dompet baru. NOL tabel baru.** Tinggal dipakai.

### C. Sumber pencarian (`app/pustaka.py`) — SUDAH ADA ✅
`cari_semua()` → Scopus + OpenAlex + Garuda + CrossRef → `audit_doi()` → saring
→ hasil ber-link (`doi`, `garuda_id`).

---

## 🎯 IDE WULAN — "BAYAR → CARI → JIKA GAGAL, UANG KEMBALI"

Ini yang menjawab **"gak rugi"** dan **"presisi karena berbayar"** sekaligus.

### Aturan yang Wulan usulkan (mengikuti pola pagar yang SUDAH jadi di EduAi)

```
User ketik kata kunci → tekan [Cari] (1 token)
        ↓
   POTONG 1 token SEKARANG (biar tidak bisa dicurangi)
        ↓
   CARI ke 4 sumber → AUDIT DOI → SARING
        ↓
   ┌── hasil BAGUS  → tampilkan. Selesai. Token dipakai. ─────┐
   │                                                          │
   └── hasil KOSONG → 🔙 KEMBALIKAN token + jujur: ───────────┘
       "Tidak ada artikel yang cocok untuk kata kunci itu.
        Token kamu sudah dikembalikan. Coba kata kunci lain."
```

**Kenapa "kembalikan kalau kosong" itu penting:**
- Bos **tidak rugi** ✔ (uang masuk saat hasil ada)
- User **tidak merasa dipermainkan** ✔ (bayar → dapat; gagal → uang kembali)
- Ini **persis pola yang sudah dipakai EduAi** untuk revisi gagal (token selalu
  dikembalikan tiap gagal — sudah terbukti di produksi)

### 🔴 PAGAR PENTING — apa yang boleh "kembalikan token", apa yang TIDAK

| Keadaan | Kembalikan token? | Alasan |
|---|---|---|
| Tidak ada hasil sama sekali | ✅ **YA** | Bukan salah user |
| Sumber error / VPS gagal | ✅ **YA** | Bukan salah user |
| Hasil ADA tapi user tidak suka | ❌ **TIDAK** | User sudah lihat hasilnya — kalau dikembalikan, bisa giling gratis |
| User cari kata kunci asal-asalan | ❌ **TIDAK** | Itu hak user, tapi tetap bayar |

⇒ Ini **mencegah celah "cari gratis berulang"** — sama pola dengan pagar
pembatalan kuota yang sudah Bos kunci 17 Sep.

---

## 📏 CARA MEMBUAT HASIL "PRESISI" (syarat Bos, karena berbayar)

Ini bagian paling penting. Hasil **wajib presisi** — kalau tidak, user bayar
untuk hasil ngawur dan itu **merusak kepercayaan + bikin minta refund.**

### 1. Tampilkan kata kunci yang DIPAKAI (transparan)
Saat user ketik "kualitas produk UMKM", sistem menunjukkan:
> *"Kata kunci dipakai: **kualitas produk** · **UMKM** · quality product ·
> SME"* — jadi user tahu apa yang dicari.

Kalau hasil meleset, user **langsung tahu kenapa** (kata kuncinya kurang tepat)
dan bisa memperbaiki sendiri.

### 2. Hanya tampilkan yang LOLOS AUDIT DOI
Sudah ada (`audit_doi()`). Yang tak terverifikasi **dibuang atau ditandai**.
⇒ Ini pembeda utama: bukan "hasil karangan AI", tapi **artikel yang ada di
CrossRef/Garuda.**

### 3. Perbaiki saringan relevansi (MASALAH TERUKUR)
Uji 06 Okt 2026: **35 hasil mentah → 1 lolos**. Itu **terlalu tajam** — user
bayar token, dapat 1 artikel (dan itu pun kurang nyambung).

**Wulan usulkan dua tingkat:**
| Tingkat | Arti |
|---|---|
| **Ketat** (±10 hasil) | hanya yang benar-benar cocok — untuk skripsi tepat sasaran |
| **Luas** (±30 hasil) | lebih banyak, ada yang melenceng — untuk melihat-lihat |

⇒ User **memilih sendiri**, bukan ditebak. Kalau hasil ketat kosong → **token
kembali** + tawaran "coba mode Luas?".

### 4. Tampilkan skor kecocokan
Setiap artikel diberi angka kecocokan (mis. "Cocok 92%") + **kenapa** (kata
kunci mana yang ketemu). Jadi user **bisa menilai sendiri** kualitas hasilnya.

### 5. Batas per hari (cadangan pengaman)
Walaupun sudah berbayar, Wulan usulkan **plafon harian** (mis. maks 20×
pencarian/hari) — untuk melindungi VPS dari penyalahgunaan & dari lonjakan
tak terduga. Ini **lapis kedua**, bukan pengganti token.

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR

1. **1 token itu untuk APA?** Yang berbayar = **PENCARIAN-nya** (mengambil dari
   API + audit DOI), bukan mengunduh. Unduh PDF **tidak** kena token lagi
   (kecuali Bos mau).
2. **Token sama dengan "Token Revisi"?** Perlu diputuskan: pakai dompet token
   yang **sama** (1 pintu, sudah ada) atau jenis AddOn **baru**. Wulan sarankan
   **dompet yang sama** — sejalan aturan Bos *"jangan bikin dompet/jalur paralel"*.
3. **Scopus belum ada kuncinya** di produksi → jalur internasional berkurang.
   Kalau Bos mau presisi maksimal, kunci Scopus perlu dipasang.
4. **API Scopus & OpenAlex punya batas** (±10 req/detik). Kalau banyak user
   cari bersamaan, perlu antrean sopan.
5. **"Presisi" ada batasnya.** Jurnal benar-benar nyambung itu **dinilai
   manusia** (dosen). Mesin bisa bantu **menyaring**, tapi **tidak bisa
   menjamin** semua hasil 100% cocok. Wulan tidak akan mengklaim lebih dari itu.

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **Token untuk pencarian pakai dompet yang SAMA** dengan Token Revisi, atau
   jenis terpisah?
2. **Kalau hasil kosong → token dikembalikan** (usul Wulan)? Atau tetap dipotong?
3. **1 token = 1 pencarian**, atau 1 token = 1 paket (beberapa pencarian)?
4. **Unduh PDF** kena token lagi, atau gratis bila sudah bayar pencarian?
5. **Plafon harian** perlu? Berapa?
6. **Minta kata kunci lebih spesifik** kalau terlalu umum (hemat token user),
   atau langsung cari saja?
7. **Mode Ketat / Luas** — perlu, atau cukup satu mode saja?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] Mesin token diperiksa: `saldo.py` + `kuota.py` SUDAH LENGKAP
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
