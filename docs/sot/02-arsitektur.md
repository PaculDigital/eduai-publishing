# 02 — Arsitektur EduAi

<!-- SOT: Arsitektur EduAi. Diperbarui 26 Okt 2026. Angka dari hitungan berkas di cabang main, 26 Okt 2026. -->

## Ukuran (terhitung, bukan klaim)

- `app/` = 92 modul Python. Terbesar: `app/ai.py` 4.729 baris, `app/main.py` 3.832 baris, `app/konversi.py` 2.547 baris, `app/pustaka.py` 1.857 baris, `app/models.py` 1.460 baris.
- `app/models.py` = 28 tabel (termasuk `hasil_bab4`, `peta_bab4`, `data_lapangan_bab4`, `saldo_token`).
- Rute utama di `app/main.py` + router: `app/ai.py` (`/api/ai`), `app/rute_alur.py` (`/api/ai/v1` alur awal), `app/rute_pembimbing.py` (`/tinjau/{token}`), `app/rute_bagikan.py` (`/pembimbing/*`), `app/rute_jurnal.py` (`/api/ai/v1/jurnal`), `app/bab4_rute.py` (`/api/bab4` — belum live, lihat `01-produk-dan-flow.md`).
- Template Jinja di `app/templates/` (landing, naskah, belajar, buku, artikel, tinjau, loa, dll.) + aset di `app/static/`.

## Modul kunci per domain

| Domain | Modul |
|---|---|
| Peta naskah | `app/jev.py`, `app/satpam.py`, `app/hakim_peta.py`, `app/peta_halus.py`, `app/peta3_jev.py`, `app/konsistensi.py`, `app/pola_penulisan.py` |
| Revisi & kerangka | `app/ai.py` (satu pintu AI), `app/kerangka.py`, `app/kerangka_bab.py`, `app/asisten.py`, `app/catatan_ai.py`, `app/etika.py` |
| Storage & editor | `app/folder.py`, `app/onlyoffice.py`, `app/sampah.py`, `app/versi.py`, `app/sesi.py` |
| Kolaborasi | `app/pembimbing.py`, `app/pembimbing_ai.py`, `app/rute_pembimbing.py`, `app/rute_bagikan.py`, `app/notifikasi.py`, `app/wa.py` |
| Jurnal | `app/jurnal.py`, `app/pustaka.py`, `app/konversi.py`, `app/submit_jurnal.py`, `app/loa.py`, `app/plagiarisme.py`, `app/citation_validator.py` |
| Buku | `app/buku.py`, `app/penyusunan_buku.py`, `app/gambar.py`, `app/brief.py` + mesin di root (`buku_umum_pipeline.py`, `buku_umum_assembly.py`, dll.) |
| BAB IV | `app/bab4.py`, `app/bab4_rute.py`, `app/bab4_narasi.py`, `app/jembatan_statistik.py`, `app/kunci_layanan.py` |
| Uang | `app/kuota.py`, `app/saldo.py`, `app/pakasir.py`, `app/config.py` |

## Prinsip arsitektur (terkunci, dari MASTER_PLAN yang diarsipkan)

1. **Jev di depan, bukan di belakang:** Jev kenali bentuk → mesin olah → AI tulis → Jev periksa hasil. Jev hanya membaca BENTUK/STRUKTUR/KEBERADAAN, tidak menilai mutu tulisan.
2. **Satu pintu AI:** semua panggilan model lewat 9router; tidak ada jalur kedua.
3. **Jangan menambal, cari akar:** perbaikan di sumbernya, bukan di hilir. Bukti terukur wajib (uji nyata, bukan klaim).
4. **Gerbang hijau di host ≠ produksi sehat:** `/health` 200 bukan bukti kode sehat; bukti produksi hanya dari image/container yang jalan.

## Deploy & verifikasi (jalur resmi)

- Jalur resmi: `bash jalankan.sh` (Langkah 0 = `scripts/periksa_kode.sh`; gerbang gagal → deploy berhenti).
- Image produksi dibangun dari `Dockerfile`; container dibuat ulang = perubahan `docker cp` yang tidak masuk image akan hilang.
- Verifikasi dokumen vs kode: `SOT_DIREKTORI_DOKUMEN="$PWD" python3 sot.py --periksa` — harus 0 masalah. Catatan: tanpa env itu, `sot.py` membaca path container (`/opt/data/services/eduai-publishing` / `/app`) dan akan melaporkan berkas "HILANG" secara keliru di host.
- Produksi jalan dari image Docker, bukan dari cabang `main` secara langsung — **merge ≠ deploy**. Ini terbukti lagi pada BAB IV (sudah merge, belum deploy).
