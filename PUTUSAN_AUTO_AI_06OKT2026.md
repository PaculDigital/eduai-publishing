# 🔒 PUTUSAN BOS — AUTO AI (HARVEST OTOMATIS) (06 Okt 2026)

<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Jawaban Bos 06 Okt 2026 (verbatim):
> *"1. Ok hanya sampai kerangka saja, gratis · 2. Ok · 3. Maksudnya? ·
> 4. Betul, punya mekanisme sendiri."*
>
> Status: **PUTUSAN TERKUNCI** (kecuali poin 3 masih menunggu jawaban).

---

## ✅ PUTUSAN BOS

| # | Pertanyaan Wulan | Putusan Bos |
|---|---|---|
| 1 | Auto AI cari artikel gratis? | ✅ **GRATIS hanya sampai KERANGKA saja** |
| 2 | Auto AI jalan saat tombol ditekan? | ✅ **OK** (bukan otomatis) |
| 3 | Tampilkan daftar artikel sebelum bayar? | ❓ **Wulan jelaskan dulu** — menunggu keputusan |
| 4 | Auto AI masuk hitungan 2×/minggu? | ✅ **TIDAK** — punya mekanisme sendiri |

---

## 📊 ARTI PUTUSAN No.1 (PENTING — batas gratisnya)

```
User tulis JUDUL
        ↓
TAHAP 2 — susun_rencana()
   ├─ cari artikel nyata
   ├─ susun kerangka bab
   └─ perkiraan biaya
        ↓
   ⛔ GRATIS SAMPAI SINI (putusan Bos)
        ↓
TAHAP 3 — bangun_isi()  ← BARU POTONG TOKEN (menulis bab jadi)
        ↓
   Bab jadi + daftar pustaka
```

⇒ **Yang gratis = mencari + menyusun kerangka.**
⇒ **Yang berbayar = MENULIS babnya** (Tahap 3).
⇒ Ini **cocok** dengan kode yang sudah ada: `susun_rencana()` memang berlabel
*"TAHAP 2 — RENCANA (GRATIS, 0 token)"* di kode.

---

## ❓ POIN 3 — PENJELASAN WULAN (menunggu keputusan Bos)

**Yang Wulan maksud:** apakah user bisa **melihat daftar artikel** yang akan
dipakai **SEBELUM** menekan "Setuju" (sebelum token terpotong)?

### Keadaan sekarang (perlu dicek lagi ke kode)
Tahap 2 mengembalikan: rencana kerangka + perkiraan biaya + info pencarian
(`per_sumber`, `total_unik`, `terverifikasi`, `kata_kunci`).
⇒ **Belum pasti** apakah **daftar ARTIKEL-nya** (judul + penulis + link)
ditampilkan ke user. **Wulan belum memeriksa bagian tampilannya.**

### Usul Wulan (kalau belum ada)
```
TAHAP 2 (GRATIS)
├─ Rencana kerangka BAB I
├─ Perkiraan biaya: 2 Token
│
├─ 📚 Artikel yang akan dipakai:
│   1. Yusnia (2020) — ... ✅ NYATA  🟢 PDF gratis
│   2. Smith (2021) — ...  ✅ NYATA  🔒 Berlangganan
│
├─ [ ✅ Setuju, tulis bab — 2 Token ]
└─ [ ❌ Batal ]
```

**Kenapa Wulan usulkan:**
| Tanpa ini | Dengan ini |
|---|---|
| User bayar token tanpa tahu bahannya | User lihat dulu, baru bayar |
| Token bisa terbuang kalau bahan tidak cocok | Token terpakai dengan sadar |
| Menjawab "artikelnya nyata" hanya lewat kata | User bisa **klik link-nya sendiri** |
| Risiko dikeluhkan | Bos terlindungi |

⇒ **Bukan fitur baru** — hanya **menampilkan yang sudah dicari** ke layar.

---

## 📋 RANGKAIAN PUTUSAN 06 OKT 2026 (lengkap)

### 🔎 Pencarian MANUAL (user)
| Hal | Putusan |
|---|---|
| Berbayar? | ✅ 1 token per pencarian |
| Jatah gratis | ✅ **2× per minggu** |
| Siklus | ✅ **sejak awal pemakaian** user (7 hari) |
| Takaran | ✅ 1 pencarian = 1 judul/keyword |
| Yang dihitung | ✅ pencarian manual saja |

### 🤖 Auto AI (harvest otomatis)
| Hal | Putusan |
|---|---|
| Biaya cari + kerangka | ✅ **GRATIS** (sampai kerangka) |
| Biaya menulis bab | token (Tahap 3, seperti sekarang) |
| Kapan jalan | ✅ saat tombol ditekan |
| Masuk 2×/minggu? | ✅ **TIDAK** — mekanisme sendiri |
| Tampilkan artikel sebelum bayar | ❓ menunggu keputusan Bos |

### 🏗️ Workspace & mesin
| Hal | Putusan |
|---|---|
| Workspace (wadah) | ✅ bisa — pondasi `folders` ada |
| Harvest jurnal | ✅ `pustaka.py` sudah live |
| Unduh PDF → workspace | ✅ terbukti bisa |
| Jev di mesin pencari | ✅ **tidak perlu** |
| Pencarian per variabel | ✅ mesin `konsep_dari_judul()` ada |
| Tab "📚 Referensi" | 💡 ide, belum putus |

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] Putusan 1, 2, 4 **TERKUNCI**
- [ ] Poin 3: Wulan sudah jelaskan, **menunggu keputusan Bos**
- [ ] DILARANG dikoding sebelum Bos bilang mulai
