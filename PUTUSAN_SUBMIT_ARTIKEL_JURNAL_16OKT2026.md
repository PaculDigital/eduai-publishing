# 🔒 PUTUSAN BOS — SUBMIT ARTIKEL JURNAL (16 Okt 2026)

<!-- SOT: putusan fitur "Submit Artikel Jurnal" EduAi · 16 Okt 2026
     Acuan tunggal untuk: (a) peta lapis; (b) aturan login Tridarma;
     (c) isi tiap kartu; (d) harga & jatah; (e) pagar.
     DILARANG koding ulang sebelum baca ini sampai habis. -->

## 1. PINTU
- **Tab ke-7** di menu bersama `app/templates/_menu.html`, **setelah** Uji Plagiarisme.
- Nama tab: **"Submit Artikel Jurnal"**.
- Rute: `/submit-jurnal` (halaman) + rute aksi.

## 2. ISI HALAMAN — 3 KARTU (sketsa PILIHAN 1, ACC Bos 16 Okt)

### Kartu 1 — Jurnal NASIONAL
- Keterangan indeks: **Google Scholar · Garuda · Ber-ISSN**.
- Isi:
  - **Pilih naskah** (pola SAMA dengan fitur Uji Plagiarisme — `FileBerkas` milik user).
  - Muncul **konfirmasi data**: **nama lengkap · email · no HP** (dari profil akun, BOLEH diubah).
  - Tombol **Kirim** → muncul **modul AddOn "Terbit Jurnal" bayar QRIS**.

### Kartu 2 — Terbit Jurnal SINTA
- **Dropdown peringkat: Sinta 2, 3, 4, 5, 6.**
- **Pilih naskah** → tombol **Submit**.
- Muncul **buka WA Admin**, dengan **tulisan sesuai peringkat yang dipilih user**.
- Alasan (Bos): *"karena ini negosiasi dan pekerjaan manual"*.
- **Naskah TIDAK dikirim ke WA** — admin mengambil sendiri dari akunnya (putusan 1A).

### Kartu 3 — DAFTAR ARTIKEL (BARU, ACC Bos 16 Okt)
- Letak: **DI BAWAH 2 kartu submit** (putusan Bos).
- Isi: daftar artikel user di Tridarma + **status** (Review · Revisi · Diterima · Ditolak · Antrean).
- **Hanya tampil kalau user sudah pernah submit** (kalau belum → bagian ini tidak muncul).
- Termasuk baris **"Lupa sandi Tridarma? Reset ▸"**.

## 3. ATURAN LOGIN TRIDARMA (putusan Bos, TERBUKTI 16 Okt)

| Hal | Putusan |
|---|---|
| **Username OJS** | **EMAIL user** (sama dengan EduAi) |
| **Sandi awal** | **`Pass1EduAi`** |
| User ganti sandi | SENDIRI di Tridarma (boleh); setelah itu **tidak masalah** |
| Jurnal tujuan | **JEMT saja** (`context_id=1`) — nanti user bisa pilih bidang |

### TERBUKTI (uji nyata di VPS Tridarma 16 Okt)
```
user_id=161 · username=uji-wulan-16okt2026@eduai.test
OJS kenal user: id=161 username=uji-wulan-16okt2026@eduai.test
sandi 'Pass1EduAi' COCOK?  YA ✅
```

### Submit ke-2 dst — KUNCI: JEMBATAN TIDAK BUTUH SANDI
```php
$user = Repo::user()->getByUsername($username, true);   // cuma username
$submission->setData('submitterId', $userId);
```
⇒ **User tidak pernah mengetik sandi Tridarma di EduAi.** Submit ke-1, ke-2, ke-50 sama saja.
⇒ Jembatan sendiri punya pagar `getByUsername()` → **tidak bikin akun dobel**.

## 4. HARGA & JATAH (ACC Bos 16 Okt: pilihan A)
- **1 AddOn "Publish Jurnal" Rp 500.000 = 1 artikel** (beli lagi untuk artikel ke-2).
- AddOn SUDAH ADA di `app/config.py` → `ADDON['publish']`.
- Bayar pakai mesin QRIS yang SUDAH ADA: `POST /api/addon/buat` + `app/pakasir.py`.

## 5. RESET SANDI TRIDARMA (ACC Bos 16 Okt)
- EduAi **BISA** melayani reset sandi Tridarma.
- Cara AMAN: minta **OJS kirim tautan reset resmi** ke email user
  (`PasswordResetRequested.php` / `sendPasswordReset` — sudah ada di OJS).
- **EduAi TIDAK menyimpan sandi baru user** (aman).
- Alternatif di layar: tampilkan pengingat sandi awal `Pass1EduAi` (putusan 1A).

## 6. STATUS ARTIKEL (ACC Bos 16 Okt)
- Kolom nyata di DB OJS (`submissions`): `stage_id`, `status`, `date_submitted`, `date_last_activity`.
- Peta tahap: `stage_id` 1 = Antrean · 3 = Review · 4 = Revisi · `status` 3 = Diterima · 4 = Ditolak.

## 7. PETA LAPIS (8 lapis — 5 SUDAH ADA, 3 PEMASANGAN)

| # | Lapis | Keadaan |
|---|---|---|
| ① | Menu `_menu.html` (6→7 tab) | **perlu dibuat** |
| ② | Rute + layar `submit_jurnal.html` (3 kartu) | **perlu dibuat** |
| ③ | Daftar OJS `register_user.php` | SUDAH ADA ✅ |
| ④ | Submit `submit_article.php` (tanpa sandi) | SUDAH ADA ✅ |
| ⑤ | Kirim kredensial WA + email | SUDAH ADA (`addon_buat` + WA EduAi) |
| ⑥ | Reset sandi (tautan resmi OJS) | **perlu disambung** |
| ⑦ | Baca status artikel | **perlu disambung** |
| ⑧ | Bayar `ADDON['publish']` + QRIS | SUDAH ADA ✅ |

## 8. PAGAR (dari jembatan OJS — JANGAN diduplikasi)
- Judul min **10 huruf**; abstrak min **80 kata**.
- **Anti-dobel 24 jam** (judul + email pertama).
- User tak ada → `404`; field kurang → `400`.
- 1 naskah WAJIB milik user (`user_id` cocok, belum dihapus).

## 9. YANG BELUM (catat, jangan lupa)
- **WA jembatan Tridarma BELUM terkirim** (`wa_notification: sent=false, http_code=0`)
  ⇒ EduAi kirim sendiri lewat WA EduAi (yang terbukti hidup).
- User uji `uji-wulan-16okt2026@eduai.test` (id 161) di Tridarma — perlu keputusan hapus/tidak.
