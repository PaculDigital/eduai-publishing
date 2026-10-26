# 📌 SOT — EDUAI PUBLISHING (SINGLE SOURCE OF TRUTH)

<!-- SOT: Pintu masuk tunggal dokumen EduAi, diperbarui 26 Okt 2026. -->
<!-- 🚩 DIPERBARUI 26 Okt 2026 — perapihan dokumen: root 170 md → 29 md + docs/sot/. -->

> **BACA FILE INI DULU, LALU IKUTI TAUTANNYA. JANGAN MEMBUKA BERKAS ARSIP SECARA ACAK.**
>
> Aturan hierarki (mengikat semua agen, termasuk agen AI):
> 1. **Kode yang berjalan + `sot.py` menang atas dokumen.** Status dihitung dari kode, bukan dihafal di dokumen. Jalankan `SOT_DIREKTORI_DOKUMEN="$PWD" python3 sot.py --periksa`.
> 2. **Jika `docs/sot/` bertabrakan dengan berkas root lain, `docs/sot/` yang menang.** Berkas root yang dipertahankan adalah lampiran teknis / bukti uji, BUKAN sumber status, flow, atau harga.
> 3. **Harga yang ditagih ke user = `app/config.py`.** Dokumen lama yang menulis angka lain adalah usang — lihat `docs/sot/04-harga-dan-kuota.md`.
> 4. **Berkas di `_arsip/usang-26okt2026/` adalah RIWAYAT, bukan panduan.** Jangan mengutipnya sebagai keadaan kini. Daftar lengkapnya: `docs/sot/INDEKS-ARSIP.md`. Isinya tetap ada di riwayat git dan di folder `_arsip/` (folder ini di-`.gitignore`, tidak ikut commit).
> 5. **Komentar kode yang menunjuk berkas arsip adalah penunjuk lama.** Ikuti `docs/sot/`, bukan komentar itu. Memperbarui semua komentar kode adalah pekerjaan susulan, bukan bagian perapihan 26 Okt ini.

## Peta dokumen hidup (7 domain, 1 fakta = 1 tempat)

| # | Dokumen | Isinya — dan hanya itu |
|---|---|---|
| 1 | `docs/sot/01-produk-dan-flow.md` | Apa itu EduAi, 4 bisnis dalam 1 app, flow mahasiswa & pembimbing |
| 2 | `docs/sot/02-arsitektur.md` | Modul `app/`, rute, tabel DB, cara deploy, cara verifikasi |
| 3 | `docs/sot/03-keputusan-terkunci.md` | Keputusan Boss yang masih berlaku, ber tanggal, plus yang masih terbuka |
| 4 | `docs/sot/04-harga-dan-kuota.md` | Paket, AddOn, tarif per bab, dompet token — sesuai `app/config.py` |
| 5 | `docs/sot/05-jembatan-dan-layanan-luar.md` | Statistik Lab, OJS/JEMT, 9router, OnlyOffice, Pakasir, WA |
| 6 | `docs/sot/06-buku-dan-mutu.md` | 5 jenis buku, generator template, SSOT mutu buku |
| 7 | `docs/sot/07-aturan-agen.md` | Cara kerja agen di repo ini: BAHAS DULU → Gas, cabang, gerbang, larangan |

## Berkas root yang dipertahankan (29) — lampiran, bukan SOT

- **Aturan & pagar teknis:** `ATURAN_FORMAT_PEDOMAN_26SEP2026.md`, `ATURAN_SITASI_PEDOMAN_26SEP2026.md`, `ATURAN_BATAS_PROYEK_03OKT2026.md`, `PAGAR_PINTU_NASKAH_10OKT2026.md`, `PAGAR_MUTU_PETA_DAN_HEMAT_JEV_14OKT2026.md`, `PAGAR_BATAS_BAB_15OKT2026.md`, `PANDUAN_PAKAI_JEV.md`, `URUTAN_RESMI_PETA_NASKAH_TERKUNCI.md`
- **SOT per fitur (masih dirujuk):** `SOT_KONVERSI_JURNAL.md`, `SOT_LOA_QR_17OKT2026.md`, `SOT_PUBLISH_BUKU_17OKT2026.md`, `SOT_JEV_BUKU_UMUM_20OKT2026.md`, `SOT_PETA_NASKAH_SATU_PINTU_08OKT2026.md`
- **Putusan fitur yang masih hidup:** `PUTUSAN_FITUR_LOA_16OKT2026.md`, `PUTUSAN_SUBMIT_ARTIKEL_JURNAL_16OKT2026.md`, `PUTUSAN_TIKET_LOLOS_LAPIS3_16OKT2026.md`, `PUTUSAN_UJI_PLAGIARISME_16OKT2026.md`, `PUTUSAN_JEMBATAN_KONVERSI_15OKT2026.md`, `PUTUSAN_SISIP_ARTIKEL_KE_BAB_13OKT2026.md` (putusan ini BELUM dikoding — lihat `03-keputusan-terkunci.md`)
- **Rancangan & bukti yang dirujuk gerbang kode:** `DOKUMENTASI_BAB4_RANCANGAN_FINAL_21OKT2026.md`, `STANDAR_PEMBUATAN_BUKU_20OKT2026.md`, `HASIL_UJI_12_KASUS_BATAS_09OKT2026.md`, `HASIL_VALIDASI_SILANG_K5_09OKT2026.md`, `HASIL_PENYELIDIKAN_PETA_14OKT2026.md`, `PENUTUP_UJI_K5_09OKT2026.md`, `DEMOSI_CURIGA.md` (log runtime Hakim, bukan panduan)
- **Tata kelola repo:** `README.md`, `AGEN_LUAR_ATURAN.md`

## Yang TIDAK diubah perapihan 26 Okt ini (sengaja, di luar scope)

- Kode aplikasi (`app/`) — tidak ada satu baris pun yang diubah, kecuali registry `sot.py` (lihat bawah).
- `mutu-buku/` — semesta SOT buku (SOT-INDUK, RENCANA, STATUS, skill agen kolaborator) dibiarkan utuh; `docs/sot/06-buku-dan-mutu.md` hanya menunjuk ke sana. Pekerjaan SSOT buku di cabang `agen/wulan/fase1-ssot` (belum ter-push) juga tidak disentuh.
- Komentar kode yang menunjuk berkas arsip — belum diperbarui (pekerjaan susulan).
- Isi berkas arsip — tidak diedit, tidak dihapus permanen.

## Perubahan `sot.py` dalam perapihan ini

- `DOK_STATUS` kini hanya `['SOT.md']` — MASTER_PLAN, FLAG_LANJUT_DISINI, dan CATATAN_PROYEK sudah diarsipkan; isinya yang masih berlaku dipindahkan ke `docs/sot/`.
- `PERAN_DOKUMEN` kini memetakan `SOT.md` + `docs/sot/*` + lampiran root di atas.
- `PENANDA_SOT_WAJIB` dikosongkan — berkas-berkas itu sudah diarsipkan, dan berkas root yang tersisa tidak lagi diawasi lewat daftar itu; pengawasan kini lewat hierarki di atas + `periksa_berkas_luar_pengawasan` untuk berkas root yang tersisa.

## Cara memperbarui SOT ini (aturan hidup)

1. Ubah fakta di SATU tempat saja (domain yang tepat di `docs/sot/`), lalu perbarui tanggal di kepala file itu.
2. Jangan membuat berkas `.md` baru di root tanpa persetujuan Boss — tempatkan di `docs/sot/` (panduan) atau jangan dibuat sama sekali (bukti uji sekali pakai masuk `_arsip/`, bukan root).
3. Setelah mengubah dokumen, jalankan `SOT_DIREKTORI_DOKUMEN="$PWD" python3 sot.py --periksa` dan pastikan 0 masalah sebelum commit.
