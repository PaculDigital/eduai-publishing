# 🔒 PUTUSAN BOS — PAGAR TIKET COBA ULANG = 2× GRATIS (06 Okt 2026)

<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Putusan Bos 06 Okt 2026 (verbatim):
> *"2x percobaan gratis jika mau lanjut kena token lagi."*
>
> Status: **PUTUSAN TERKUNCI.** Belum dikoding (menunggu perintah mulai).

---

## ✅ KEPUTUSAN BOS (TERKUNCI)

| Hal | Nilai |
|---|---|
| **Percobaan gratis** | **2×** |
| Setelah 2× habis | **KENA TOKEN** |
| Berlaku untuk | Pencarian Jurnal **oleh USER** (manual) |

---

## 📊 PERHITUNGANNYA (apa artinya bagi Bos)

```
┌─────────────────────────────────────────────────────┐
│  Pencarian manual ke-1  →  GRATIS    (percobaan)    │
│  Pencarian manual ke-2  →  GRATIS    (percobaan)    │
│  ────────────────────────────────────────────────   │
│  Pencarian manual ke-3  →  1 TOKEN → dst. token     │
└─────────────────────────────────────────────────────┘
```

⇒ Amin: user **masih bisa mencoba** (tidak langsung dipaksa bayar) → **ramah**
untuk pengguna baru. Tapi **habis 2×, jelas kena token** → **Bos tidak rugi.**

---

## ❓ YANG MASIH PERLU DIPERJELAS (2 pertanyaan)

### Pertanyaan 1 — 2× itu hitungannya PER APA?

| Pilihan | Artinya |
|---|---|
| **A. Per HARI** | 2 gratis tiap hari. ⇒ 60 gratis/bulan kalau dipakai tiap hari ⚠️ |
| **B. Per BULAN** | 2 gratis per bulan. ⇒ maks 2 gratis/bulan ✅ hemat |
| **C. Sekali selamanya** | seumur akun hanya 2 gratis total ✅✅ paling hemat |
| **D. Per WORKSPACE** | 2 gratis tiap workspace. ⇒ bikin 10 workspace = 20 gratis ⚠️⚠️ |

Wulan **belum memutuskan sendiri** — menunggu Bos. (Wulan condong **B** atau **C**.)

### Pertanyaan 2 — yang dihitung "percobaan gratis" apa?

Ada 2 macam pencarian:
1. **Auto AI** (kata kunci dari judul naskah) → **tidak kena token** (AI yang jalan)
2. **Manual user** (user ketik judul/kata kunci) → **ini yang kena token**

⇒ Wulan asumsikan **yang dihitung 2× gratis = pencarian MANUAL** (yang berbayar).
Kalau salah, tolong Bos koreksi.

---

## 🔗 KAITAN DENGAN DISKUSI SEBELUMNYA

Semua ini **satu rangkaian** dari diskusi 06 Okt 2026:

| # | Topik | Status |
|---|---|---|
| 1 | Workspace/project (wadah) | ✅ Bisa — pondasi ada |
| 2 | Harvest jurnal (mesin `pustaka.py`) | ✅ Sudah ada & live |
| 3 | 1 berkas link jurnal per workspace | 💡 ide, belum putus |
| 4 | Unduh PDF → masuk workspace | ✅ Terbukti bisa unduh |
| 5 | Tab "📚 Referensi" | 💡 ide, belum putus |
| 6 | 2 jalur (AI auto + user manual) | ✅ Tegasan Bos, setuju |
| 7 | Pencarian manual = **1 token** | ✅ Putusan Bos |
| 8 | Jev tidak perlu | ✅ Jawaban Wulan (terukur) |
| 9 | Pencarian per variabel | 💡 mesin `konsep_dari_judul()` ADA |
| 10 | Cari lepas workspace | 💡 ide, belum putus |
| 11 | **2× gratis lalu token** | ✅ **PUTUSAN BOS (baru)** |

---

## ⚠️ CATATAN JUJUR

1. **2× gratis masih punya celah** — kalau hitungannya "per hari" atau
   "per workspace", user bisa giling gratis. **Butuh jawaban Bos** (pertanyaan 1).
2. **Jejak tetap wajib dicatat** (siapa · kapan · kata kunci) — supaya kalau ada
   pola aneh, Bos bisa lihat. Tanpa jejak, tidak terlacak.
3. **Semua ini BELUM ADA di kode** — `pustaka.py` belum punya konsep tiket/token
   pencarian sama sekali.
4. **Kena tokennya sebesar apa?** Diskusi sebelumnya: **1 token per pencarian**.
   Apakah angka itu tetap, atau Bos mau ubah? (perlu dikonfirmasi)

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **PUTUSAN BOS TERKUNCI: 2× gratis → lalu token**
- [ ] Ditunggu jawaban 2 pertanyaan di atas
- [ ] DILARANG dikoding sebelum Bos bilang mulai
