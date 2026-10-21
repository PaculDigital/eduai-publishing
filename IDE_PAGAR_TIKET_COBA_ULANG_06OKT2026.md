# 🔒 PAGAR "TIKET COBA ULANG" — ANTI RUGI (06 Okt 2026)

<!-- ⛔ SOT: IDE — DILARANG DIKODING -->
> # ⛔ IDE / USULAN — **DILARANG dikoding** sampai Bos bilang "mulai".
> Isi berkas ini = **gagasan menunggu putusan Bos**, BUKAN keadaan kini dan
> BUKAN rencana kerja aktif. ❌ JANGAN dibaca sebagai status proyek.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Arah Bos 06 Okt 2026 (verbatim):
> *"Ya tapi harus dibatasi, jangan sampai saya rugi. User coba-coba terus padahal
> sudah dapat bagus tapi biar dapat gratis terus."*
>
> Status: **BAHAN DISKUSI.** Belum diputuskan. DILARANG dikoding.

---

## 🎯 AKAR MASALAH YANG BOS TANGKAP

Bahaya bukan "user gagal dapat tiket" — tapi **user yang SENGAJA GAGAL** biar
dapat gratis terus:

```
User minta AI cari dengan kata kunci aneh/kosong
        ↓ (hasil memang kosong — TAPI DISENGAJA)
   "Hasil AI kosong" → dapat tiket GRATIS cari manual
        ↓
   diulang 10× sehari = CARI MANUAL GRATIS TAK TERBATAS
        ↓
   Bos bayar API, user bayar Rp 0  ⇒  RUGI
```

⇒ **Pagar harus menutup "kegagalan yang disengaja"**, bukan cuma "kegagalan
yang wajar".

---

## 🔒 PAGAR WULAN — 7 LAPIS (semuanya kunci satu pintu)

### LAPIS 1 — Syarat "GAGAL" harus KETAT
Tiket **HANYA** keluar kalau memenuhi **SEMUA** ini:

| Syarat | Nilai |
|---|---|
| Hasil AI | **0 artikel** (bukan ≤2 — bukti lebih kuat) |
| Kata kunci yang dikirim | **berasal dari judul naskah** (bukan diketik bebas user) |
| Naskah | punya judul yang **sah** (≥3 kata, ada variabel) |
| AI sudah mencoba | **≥3 sumber** benar-benar dihubungi (bukan 1 gagal teknis) |

⇒ User **tidak bisa "mengosongkan"** hasil, karena kata kuncinya **diambil dari
naskahnya sendiri** — bukan dari kotak ketikan. **Ini kunci penutup celahnya.**

### LAPIS 2 — Jatah HARIAN (bukan "per workspace selamanya")
| Aturan | Nilai |
|---|---|
| Maks tiket | **1 per HARI per user** |
| Tambahan | maks **3 per BULAN** per user |
| Kalau kuota harian/bulanan habis | tiket berikutnya **ditolak otomatis** |

⇒ Walaupun user punya 10 workspace, **tetap** hanya 1 tiket sehari. **Batas
mengikuti USER, bukan workspace** — menutup celah "bikin 10 workspace".

### LAPIS 3 — Hitungan di SERVER (bukan browser)
Disimpan di DB: `user_id · tanggal · jumlah_tiket_dipakai`.
Wajib **server-side** — kalau di browser, user hapus cookie → tiket baru lagi.

### LAPIS 4 — Tiket BERLAKU SEKALI & TIDAK MENUMPUK
- Tiket dipakai → **hangus** (tidak kembali walau hasil manual juga kosong).
- Tidak ditumpuk: kemarin 1 tiket, hari ini 1 tiket — **bukan** jadi 2.
- Kedaluwarsa **hari itu** juga.

### LAPIS 5 — WAJIB ADA "JEJAK" (audit trail)
Setiap tiket dicatat: **siapa · kapan · kata kunci apa · hasil AI berapa ·
hasil manual berapa**.
⇒ Kalau ada pola aneh (user sering "kosong"), Bos **bisa lihat & cabut haknya.**
Tanpa jejak, penyalahgunaan **tak terlacak**.

### LAPIS 6 — 🚨 INI YANG PALING PENTING — "3 KALI KOSONG = HAK DICABUT"
Ini pagar penutup kebocoran yang Bos khawatirkan:

```
Tiket dipakai → hasil manual JUGA kosong/gagal?
        ↓
  Hitung "tiket sia-sia" user itu
        ↓
  3× tiket sia-sia dalam sebulan
        ↓
  ⛔ HAK TIKET DICABUT (permanen / sampai 3 bulan)
```

**Kenapa ini penting:** user yang **sengaja mengosongkan** hasil AI akan:
1. pakai tiket,
2. cari manual — **tetap kosong** (karena kata kuncinya memang asal),
3. tercatat sebagai "tiket sia-sia",
4. **3× saja → haknya dicabut.**

⇒ **Mencoba-coba = menggerus haknya sendiri.** Justru **merugikan** user yang
bermain-main, dan **aman** bagi user yang benar-benar butuh.

### LAPIS 7 — Nada RAMAH (tetapi jelas)
Sesuai aturan notifikasi EduAi (hangat, bukan menakutkan) — TAPI batas tetap
tegas:
```
Hari ini kamu sudah memakai kesempatan coba-ulang.
Masih ada 12 artikel dari AI untukmu.
Besok kesempatan itu tersedia lagi ya 😊
```
⇒ Tidak menyalahkan, tapi **jelas** — user tidak bingung kenapa tidak dapat.

---

## 📊 SIMULASI — apakah Bos rugi? (hitung jujur)

| Skenario user | Tiket dipakai | Bos rugi? |
|---|---|---|
| Jujur: AI kosong (judul khusus) → cari manual, dapat hasil | 1/hari | **Tidak** — wajar |
| Jujur: AI kosong 3× sebulan, manual selalu dapat | 3/bulan | **Tidak** — masih batas |
| Bermain: sengaja kosong tiap hari | 1/hari, **tapi** tiket sia-sia 3× → **HAK CABUT** | **Tidak** — ditutup di lapis 6 |
| Bermain: bikin 10 workspace | tetap **1 tiket/hari** (batas ikut USER) | **Tidak** — ditutup lapis 2 |
| Bermain: hapus cookie | tidak bisa — **server-side** | **Tidak** — ditutup lapis 3 |

⇒ **Paling banyak 3 pencarian manual gratis per bulan per user.** Sisanya bayar
token. **Tidak mungkin "gratis terus".**

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR

1. **Lapis 6 (3× sia-sia → cabut) butuh keputusan Bos.** Ini agak "keras" —
   tapi **inilah yang benar-benar menutup celah**. Kalau Bos mau lebih lunak,
   alternatifnya: bukan dicabut, tapi **jeda 1 bulan**.
2. **Kapasitas API** tetap perlu sopan — Scopus/OpenAlex ada batas req/detik.
   Mau ada tiket atau tidak, **antrean sopan** tetap perlu.
3. **Kalau kata kunci dari judul naskah ternyata SAMA-SAMA kosong** (judulnya
   memang sangat khusus), user yang jujur akan **terkena lapis 6** juga.
   ⇒ Wulan usulkan: **kalau kata kunci dari JUDUL (bukan dari user), tiket
   sia-sia TIDAK dihitung.** Yang dihitung hanya kalau user mencari manual
   dengan kata kunci **ketikan sendiri**.
4. **Semua ini BELUM ADA di kode** — `pustaka.py` belum punya konsep tiket,
   token, atau jurnal pencarian sama sekali.

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. Syarat tiket: **hasil 0 artikel** (usul Wulan) atau **≤2**?
2. Jatah: **1/hari + 3/bulan** — atau angka lain?
3. **3× tiket sia-sia → hak dicabut** (usul Wulan) — atau **jeda 1 bulan**?
4. **Kata kunci dari judul naskah** (bukan ketikan user) untuk Auto AI —
   setuju? (Ini kunci penutup celahnya)
5. Tiket sia-sia dari **kata kunci judul** — tidak dihitung (usul Wulan)?
6. Perlu **halaman jejak tiket** untuk Bos (siapa pakai berapa kali)?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] 7 lapis pagar disusun (menutup: sengaja kosong, banyak workspace,
      hapus cookie, tumpuk tiket, coba-coba terus)
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
