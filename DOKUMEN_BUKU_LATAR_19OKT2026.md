# ⏳ BUKU DIKERJAKAN DI LATAR — 19 OKT 2026

<!-- 📌 SOT: Buku dititipkan ke `app/proses.py` (jalur yang SUDAH ADA), bukan
     mesin baru. Gerbang: `_gerbang_buku_latar.py` 25/0 (bergigi 3 suntikan). -->

> **ACC Bos 19 Okt 2026 (verbatim): "Kok 36 menit uji, belum bisa paralel"**
> → Bos pilih **A**: pekerjaan latar + halaman status **dulu**, sebelum paralel.

## 1. MASALAH YANG DIPERBAIKI (terukur, bukan dugaan)

| Sebelum | Akibat nyata |
|---|---|
| `/buku/susun` **menunggu** mesin sampai selesai | Buku 6 bab = **±36 menit SATU request** |
| Tab ditutup saat menunggu | Pekerjaan **tetap jalan** tapi user **tidak tahu apa-apa** |
| Request panjang lewat Cloudflare | Bisa diputus di **±125 dtk (HTTP 524)** — pola SAMA dengan bug revisi 16 Sep |
| Tidak ada halaman kemajuan | User tidak tahu bab ke berapa |

## 2. YANG DIPASANG — PEMASANGAN, BUKAN MESIN BARU

Mesin yang dipakai **sudah ada** dan sudah matang di `app/proses.py`
(dipakai revisi naskah sejak 16 Sep):

| Sudah ada (TIDAK diubah) | Dipakai untuk |
|---|---|
| `proses.mulai()` / `jalankan()` / `ubah_tahap()` | menitipkan pekerjaan |
| `proses.tandai_selesai()` / `tandai_gagal()` | menutup status + notifikasi |
| Penjaga hantu `_tutup_bila_menggantung()` | utas mati → status PASTI tertutup + kuota balik |
| Antrean `_antre_atau_jalan()` | batas konkurensi |
| `GET /api/ai/v1/proses/{kode}` + `/hasil` | pemantauan (TAHAP NYATA) |
| `Lapor` | tahap nyata per langkah |

Yang **DITAMBAHKAN** (tipis):

| Berkas | Isi |
|---|---|
| `app/main.py` — `buku_susun` | buat baris proses → jalankan utas → **alihkan** ke halaman pantau |
| `app/main.py` — `halaman_buku_proses` | rute baru `/buku/proses/{kode}` |
| `app/templates/buku_proses.html` | halaman pantau (gaya SAMA dengan `buku_selesai.html`) |
| `_gerbang_buku_latar.py` | gerbang 25 asersi |

## 3. ATURAN YANG DIPATUHI

1. **Kuota TETAP dipotong di dalam `susun()`** — TIDAK dipindah ke rute.
   Gerbang biaya lama tetap **satu pintu**. Dua tempat potong = risiko 2×.
2. **Tahap NYATA, bukan persen karangan** (aturan lama §4.12):
   Menyiapkan kerangka → Menulis bab → Merakit dokumen → Selesai.
3. **`kode` = token acak**, bukan id berurutan ⇒ user lain tidak bisa mengintip.
4. **Halaman pantau tidak menampilkan isi naskah** — hanya status + metadata.
5. Utas memakai **sesi DB sendiri** (`SessionLocal`), bukan `db` milik request
   (sesi request ditutup begitu respons dikirim).

## 4. BUKTI

```
_gerbang_buku_latar.py                      25 LULUS / 0 GAGAL
  bergigi: rute kembali menunggu      → 3 GAGAL ✅
  bergigi: kuota dicabut dari susun() → 1 GAGAL ✅
periksa_kode.sh                             LULUS
```

Isi gerbang (yang penting, bukan jumlahnya):
- rute **tidak** memanggil `susun()` sinkron; memakai `_proses.jalankan`/`mulai`
- `susun()` **masih** memotong kuota; rute **tidak** memotong sendiri
- pekerjaan latar **benar-benar jalan** → status `selesai`, `hasil_json` tersimpan
- pekerjaan gagal → status `gagal` + alasan tersimpan (**bukan hantu**)
- user LAIN tidak bisa membuka kode proses orang lain
- halaman **tidak** punya bar persen karangan
- halaman **tidak** membocorkan isi naskah

## 5. JEBAKAN (menggigit Wulan lagi, 19 Okt)

| # | Jebakan | Akibat | Obat |
|---|---|---|---|
| 10 | Gerbang membuang blok `<script>` saat memeriksa template | 3 asersi gagal **PALSU** — `fetch` ada DI DALAM script | Buang komentar saja, JANGAN buang script |
| 11 | `width:100%` di media query dianggap "persen karangan" | Gagal palsu | Cari pola **bar progres**, bukan semua `width:%` |
| 12 | `hasil_json` dianggap "bocor isi naskah" | Gagal palsu | `hasil_json` = metadata, `hasil` = naskah |
| 13 | Gerbang **dilewati diam-diam** kalau image kosong | `periksa_kode.sh` tetap **LULUS** = gerbang hiasan | Tidak ada image ⇒ **GAGAL**, bukan lewat |
| 14 | Gerbang memilih image **suntikan** (yang sengaja dirusak) | Gagal karena image salah | Buang image suntikan setelah uji bergigi |

## 6. BELUM (jujur)

- **Paralel 4 sub-bab + orkestrator: BELUM.** Bos pilih A dulu. Kecepatan
  masih ±36 menit untuk 6 bab — yang berubah: user **boleh meninggalkan layar**.
- **Belum diuji dengan buku sungguhan** (butuh token). Yang diuji: utas nyata
  di DB sementara + isi image.
- Belum ada tombol "batalkan" di halaman pantau (mesin `batalkan` sudah ada,
  tombolnya belum dipasang).
- Setelah selesai, halaman otomatis pindah ke `/buku/selesai` — belum diuji
  lewat browser ber-login.
