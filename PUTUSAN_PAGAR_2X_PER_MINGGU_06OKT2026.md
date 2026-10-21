# 🔒 PUTUSAN BOS — PAGAR PENCARIAN MANUAL (06 Okt 2026) — TERKUNCI

<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Putusan Bos 06 Okt 2026 (verbatim):
> *"2x percobaan gratis jika mau lanjut kena token lagi."*
> *"2x per minggu, kalo tidak mau ya harus pakai token."*
>
> Status: **PUTUSAN TERKUNCI.** Belum dikoding (menunggu perintah mulai).

---

## ✅ KEPUTUSAN BOS (FINAL)

| Hal | Nilai |
|---|---|
| **Percobaan gratis** | **2×** |
| **Jangka waktu** | **PER MINGGU** (reset tiap minggu) |
| Setelah 2× habis | **KENA TOKEN** (1 token per pencarian) |
| Berlaku untuk | Pencarian jurnal **MANUAL oleh user** |

---

## 📊 CARA KERJANYA

```
┌──────────────────────── MINGGU INI ────────────────────────┐
│  Pencarian manual ke-1  →  GRATIS   (percobaan)            │
│  Pencarian manual ke-2  →  GRATIS   (percobaan)            │
│  ─────────────────────────────────────────────────────     │
│  Pencarian manual ke-3  →  1 TOKEN                         │
│  Pencarian manual ke-4  →  1 TOKEN                         │
│  dst. → token                                              │
└────────────────────────────────────────────────────────────┘
             ↓ minggu baru mulai (mis. Senin 00:00)
┌────────────────────── MINGGU BERIKUTNYA ───────────────────┐
│  Jatah SEGAR: 2× gratis lagi                               │
└────────────────────────────────────────────────────────────┘
```

⇒ **Maksimal 2 pencarian gratis per minggu per user.**
⇒ Sisanya **kena token**. **Bos tidak rugi.**

---

## 🔒 PAGAR PENDUKUNG (WAJIB, supaya tidak bocor)

| # | Pagar | Alasan |
|---|---|---|
| 1 | Hitungan **di SERVER (DB)**, bukan browser | Kalau di browser, user hapus cookie → jatah baru |
| 2 | Hitungan **per USER**, bukan per workspace | Bikin 10 workspace ≠ 20 gratis |
| 3 | Minggu dihitung **angka pekan (ISO week)** — satu sumber | Jangan pakai "7 hari sejak daftar" — bisa tumpang tindih |
| 4 | Jatah **TIDAK menumpuk** | Tidak dipakai minggu ini → hangus, bukan jadi 4 |
| 5 | **Jejak audit** dicatat: siapa · kapan · kata kunci | Kalau pola aneh, Bos bisa lihat |
| 6 | Nada notifikasi **hangat** (aturan EduAi) | Bukan "HABIS!", tapi *"Jatah coba minggu ini sudah dipakai. Minggu depan tersedia lagi ya 😊"* |

---

## ⚠️ SATU HAL YANG WULAN HARUS TANYAKAN (jangan menebak)

**Yang dihitung "percobaan gratis" itu pencarian yang MANA?**

Ada 2 macam:
| Jenis | Siapa yang tentukan kata kunci | Kena token? |
|---|---|---|
| **Auto AI** | **AI** (dari judul naskah) | ❌ tidak — AI yang jalan |
| **Manual user** | **User** (ketik judul/kata kunci) | ✅ **INI yang kena token** |

⇒ Wulan asumsikan: **yang 2× gratis = pencarian MANUAL** (yang berbayar).
**Kalau salah, tolong Bos koreksi.** Kalau **Auto AI juga dihitung**, maka user
yang hanya pakai Auto AI pun bisa "kehabisan jatah" — itu tidak masuk akal.

---

## ❓ MASIH PERLU DIKONFIRMASI

1. **Yang 2× gratis = pencarian MANUAL saja** — betul? (Wulan asumsi: ya)
2. **Harga token: 1 token per pencarian** — tetap, atau Bos ubah?
3. **Reset minggu**: mulai **Senin** (awal pekan) atau **7 hari sejak pakai pertama**?
   (Wulan sarankan **Senin/awal pekan** — lebih mudah dipahami & diaudit)
4. **Apakah "1 pencarian" = 1 judul/variabel**, atau 1 pencarian judul (semua
   variabel sekaligus)?

---

## 📚 RANGKAIAN DISKUSI 06 OKT 2026 (biar tidak hilang)

| # | Topik | Status |
|---|---|---|
| 1 | Workspace/project (wadah) | ✅ Bisa — pondasi (`folders`) ada |
| 2 | Harvest jurnal (`pustaka.py`) | ✅ Sudah ada & live (4 sumber) |
| 3 | 1 berkas link jurnal per workspace | 💡 ide `.txt`, belum putus |
| 4 | Unduh PDF → masuk workspace | ✅ **Terbukti bisa** (406 KB `%PDF`) |
| 5 | Tab "📚 Referensi" | 💡 ide, belum putus |
| 6 | 2 jalur: AI auto + user manual | ✅ Tegasan Bos, tidak bentrok |
| 7 | Jev untuk mesin pencari | ✅ **Tidak perlu** (terukur) |
| 8 | Pencarian per variabel | 💡 mesin `konsep_dari_judul()` **SUDAH ADA** |
| 9 | Jalur 1 "AI rekomendasi judul" | ⚠️ **setengah** — ada `contoh_judul()` tapi **bukan AI** |
| 10 | Cari lepas workspace | 💡 ide, belum putus |
| 11 | **2× gratis/minggu → lalu token** | ✅ **PUTUSAN BOS (terkunci)** |

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **PUTUSAN TERKUNCI: 2× gratis PER MINGGU, lalu 1 token/pencarian**
- [x] 6 pagar pendukung disusun (server-side, per user, tidak menumpuk, jejak)
- [ ] Ditunggu jawaban 4 pertanyaan di atas
- [ ] DILARANG dikoding sebelum Bos bilang mulai
