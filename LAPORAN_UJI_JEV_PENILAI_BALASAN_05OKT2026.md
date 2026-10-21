# 🧪 LAPORAN UJI JEV SEBAGAI PENILAI BALASAN AI — 3 PERCOBAAN, SEMUA GAGAL

> 🚩 **DIPERBARUI 07 Okt 2026 — CARA PAKAI JEV DI SINI SUDAH USANG.**
> Sebagian isi catatan ini dibuat waktu Wulan **belum membaca dokumentasi resmi**,
> jadi ada **klaim yang keliru & berbahaya** (mis. *"skema Jev tertutup / hanya 3 nama"*,
> *"Jev tidak stabil"*, *"hanya 2 tipe sah"*, *"criteria boleh string"*).
> ⇒ **ACUAN TUNGGAL cara pakai Jev sekarang:** `PANDUAN_PAKAI_JEV.md`
>   + skill `typesafe-jev` (dokumentasi RESMI `docs.typesafe.ai`).
> ⇒ Blok lama **TIDAK dihapus** (riwayat) — tapi **DILARANG dipakai sebagai panduan**.
> ⇒ Penjaga: `_gerbang_skema_jev.py` + `_uji_gigi_skema_jev.py`.



<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.

**Tanggal:** 05 Okt 2026 · **Putusan akhir Bos:** "A" — **peran ini DISUDAHI**
**Status:** ✅ Jev DICABUT dari peran penilai · kembali ke **peta bab** (peran terbukti)

---

## 1. PERTANYAAN YANG DIJAWAB

Bos: *"Uji jev dulu masalah ambang ini agar presisi dan tidak merugikan user atau saya."*

**Konteks:** pagar panjang (`PANJANG_MAKS_KALI`) menolak balasan AI yang jauh lebih
panjang dari bagian yang diganti → **503** → user gagal dapat revisi (token tetap
dikembalikan, jadi user **tidak dirugikan**). Ide Bos: pakai **Jev** untuk membantu
memutuskan "balasan ngawur atau sah".

**Cara uji:** 12 kasus nyata — 6 NGAWUR + 6 SAH — dijalankan lewat `pipa.periksa()`
dan `satpam.nilai_balasan()` dengan **jev-1.13 SUNGGUHAN** (bukan dipalsukan).

---

## 2. HASIL TIGA PERCOBAAN (semua terukur, jangan diulang)

### ❌ Percobaan 1 — jev MEMUTUSKAN (`ngawur` + `menyisipkan` + `sesuai_tugas`)

| | Hasil |
|---|---|
| NGAWUR ditolak | **6/6** ✅ |
| SAH diloloskan | **1/6** ❌ (5 ditolak, keyakinan 0,96–1,00) |

**Mencoba ambang 0,60 → 0,90 TIDAK menolong** (tetap 5 salah) → **bukan soal ambang**.

### ❌ Percobaan 2 — pertanyaan dipisah jadi `jawab_tugas` (putusan Bos "A")

| | Hasil |
|---|---|
| NGAWUR benar | **3/3** ✅ |
| SAH benar | **0/3** ❌ ("tidak_nyambung" keyakinan 0,97–1,00) |

### ❌ Percobaan 3 — ukuran `menyisipkan` (choice) + ambang 0,85 (putusan Bos "B")

| Kasus | `menyisipkan` | Keyakinan |
|---|---|---|
| NGAWUR (4×) | ya ✅ | 0,99–1,00 |
| SAH (4×) | **ya** ❌ | **0,93–1,00** |

**Tidak ada celah ambang** — kedua kelompok tumpang tindih di atas 0,90.

---

## 3. AKAR (terbukti dari jawaban MENTAH jev, bukan dugaan)

> **`jev-1.13` TIDAK BISA membedakan "memperdalam topik yang sama" dari
> "menambahkan hal yang tidak diminta". Ia melihat setiap PENAMBAHAN ISI
> sebagai "menyisipkan".**

Bukti mentah (kasus SAH *"Perdalam latar belakang…"*):
```
sesuai_tugas  = 0,06   → jev TAHU isinya sesuai tugas (0,06 = yakin)
menyisipkan   = 0,53   → ragu
jawab_tugas   = "tidak_nyambung" (0,97)
menyisipkan   = "ya" (0,93) [versi choice]
```

---

## 4. KEPUTUSAN BOS & KEADAAN SEKARANG

| | |
|---|---|
| Putusan | **"A"** — sudahi peran penilai, cabut dari kode |
| Pagar panjang | **ARITMATIKA MURNI** (perilaku lama, tak bisa mati) |
| `nilai_balasan()` | **DIHAPUS** dari `app/satpam.py` |
| Peran jev tersisa | **`periksa()` — PETA BAB** (terbukti: keyakinan 0,95, LIVE) |
| User dirugikan? | ❌ Tidak — balasan sah **lolos** |
| Aplikasi terpengaruh bila jev mati? | ❌ Tidak — pagar panjang murni Python |

---

## 5. ATURAN KE DEPAN

1. **JANGAN pakai jev-1.13** untuk menilai "balasan AI ngawur atau sah" — sudah 3× gagal.
2. Kalau peran ini ingin dicoba lagi → **pakai model LAIN** (mis. `cb/gpt-5.6-luna`,
   yang tercatat aman untuk JSON) — bukan jev-1.13.
3. **Pagar panjang tetap aritmatika.** Jangan sisipkan AI di sana: pagar itu harus
   **tidak bisa mati** (pola P2 `satpam.py`: satpam mati ≠ app berhenti).
4. **Jev tetap dipakai untuk PETA BAB** (`satpam.periksa()`) — peran itu **terbukti**.

---

## 6. JEBAKAN TEKNIS (jangan ulang)

| # | Jebakan |
|---|---|
| 1 | Pertanyaan jev **WAJIB punya `type`** = `'noul'` \| `'choice'` \| `'score'`. Tanpa itu → OpenRouter HTTP 400 `invalid_union` → 9router 502 → app **503**. |
| 2 | `_urai_balasan` bisa kembalikan **DUA bentuk**: `{k:…}` ATAU `{"answers": {k:…}}` → kode wajib tahan dua-duanya. |
| 3 | **Konstanta modul dimuat saat import** — ubah `PERTANYAAN_NILAI` di berkas **tidak berlaku** tanpa restart proses. |
| 4 | `log` **tidak ada** di `pipa.py` — dipakai patch → `NameError` → pagar bisa pecah. Ditambahkan `import logging`. |
| 5 | ⚠️ **Wulan salah baca angka** `menyisipkan` 0,41–0,62 pada percobaan B: itu dari **pertanyaan versi `noul`**, bukan `choice`. Begitu jadi `choice`, jawabannya "ya" 0,93–1,00. **Selalu baca jawaban MENTAH sebelum menyimpulkan.** |
| 6 | **Uji yang memicu fallback WAJIB memalsukan `wa.alarm_admin`** — kalau tidak, notif WA palsu terkirim ke HP Bos (kejadian nyata 05Okt26, `_uji_c6_sabar.py`). |

---

## 7. BERKAS

| Berkas | Keterangan |
|---|---|
| `app/satpam.py` | peran penilai **DIHAPUS**; `periksa()` (peta bab) **utuh** |
| `app/pipa.py` | pagar panjang **kembali aritmatika murni**; komentar jejak 3 percobaan |
| `_sketsa/uji_ambang_jev.py` | uji 12 kasus (6 NGAWUR + 6 SAH) |
| `_sketsa/uji_sungguh_12kasus.py` | uji lewat `pipa.periksa()` sungguhan |
| `_uji_jev_lapor.py` | 9 asersi bergigi (jev lapor vs pagar memutuskan) |
| `_arsip/pre-jev-*/` | 5 backup + MD5 sebelum tiap percobaan |
| `LAPORAN_PANEL_9ROUTER_05OKT2026.md` | urusan panel (model #1 mati) — **terpisah** |
