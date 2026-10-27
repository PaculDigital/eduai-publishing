# Jalur Operator — jalur produksi resmi buku (Opsi C)

**Keputusan Boss 27 Okt 2026 (Opsi C+A):** sampai gerbang per-buku
tersambung ke aplikasi web (Opsi B, bertahap), buku produksi
dibuat lewat jalur operator ini. Jalur ini yang dijaga gerbang
deploy (`scripts/periksa_buku.sh`, dipanggil sebelum
`jalankan.sh` di perintah deploy).

## Prosedur

1. **Checkout bersih di `main` terbaru** (bukan cabang kerja):
   `git fetch origin main && git checkout main && git pull origin main`.
2. **Gerbang buku harus LULUS dulu:**
   `bash scripts/periksa_buku.sh`
   (jenis, chapter, cari-TOC, isi-nomor-TOC, regresi-emas.
   Gagal = berhenti, perbaiki dulu, jangan lanjut.)
3. **Bangun buku dari spec** dengan skrip di `scripts/`:
   - Buku biasa: `buat_buku.py` dari spec JSON.
   - Chapter: `buat_book_chapter.py`, lalu cek dengan
     `periksa_book_chapter.py`.
   - Buku assembly (dari aplikasi web, TOC-nya kosong):
     isi nomornya dengan `isi_nomor_toc.py MASUK [KELUAR]`
     (default KELUAR = stem + `.bernomor.docx`).
4. **Serahkan berkas jadi** (.docx sudah lolos gerbang) ke
   pemesan. Jangan serahkan berkas yang gerbangnya gagal.

## Yang TIDAK dilakukan jalur ini

- Tidak mengubah `app/`, `jalankan.sh`, `Dockerfile`, atau
  `scripts/periksa_kode.sh` (berkas-berkas itu dilindungi
  `AGEN_LUAR_ATURAN.md` §4).
- Tidak menulis emas regresi (`uji_regresi_emas.py` tanpa
  `--perbarui`); emas hanya diperbarui lewat keputusan
  tersendiri, bukan dari jalur produksi.
- Tidak mengaktifkan jenis `buku-referensi` di aplikasi web
  (mesinnya di aplikasi tertulis "(belum ada)").

## Catatan lingkungan

- Hitung halaman / render memakai WordCraft (bukan soffice —
  soffice DIHAPUS dari desain per keputusan Boss 26 Okt 2026).
  WordCraft dicari: `$WORDCRAFT_CLI` -> PATH -> salinan hermes
  (`/opt/data/services/wordcraft-uji/bin/wordcraft-cli`).
- Baca PDF memakai `pdftotext` (PATH -> salinan permanen hermes
  `/opt/data/services/pdftotext/bin`). Jangan pakai `/tmp/ptbin`
  (hilang saat bersih-bersih).
