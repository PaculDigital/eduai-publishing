# Rencana: Cek Konsistensi Antar Bab (DRAFT → dibangun 19 Nov 2026)

Gambaran besar dalam satu kalimat: EduAi adalah alat bantu mahasiswa menulis skripsi yang benar, dan cek konsistensi memastikan rumusan masalah, tujuan, hipotesis, metode, hasil, dan kesimpulan nyambung satu sama lain, sebelum mahasiswa maju ke sidang.

Status: DIBANGUN 19 Nov 2026 atas Gas Boss ("Ok, yang rapi, sederhana dan presisi serta mudah digunakan"). Keputusan Boss 19 Nov 16:09 WIB: GRATIS untuk mahasiswa, Boss yang tanggung biayanya (dari saldo Apinex, sama seperti Jev/Hakim).

## 1. Yang dicek: 5 sambungan

| # | Dari | Ke | Pertanyaan |
|---|------|----|------------|
| 1 | Rumusan Masalah (Bab I) | Tujuan (Bab I) | Tujuan menjawab masalahnya? |
| 2 | Tujuan (Bab I) | Hipotesis (Bab II) | Hipotesis menguji tujuannya? |
| 3 | Hipotesis (Bab II) | Metode (Bab III) | Metode menguji hipotesisnya? |
| 4 | Metode (Bab III) | Hasil (Bab IV) | Hasil menjawab yang diuji metodenya? |
| 5 | Hasil (Bab IV) | Kesimpulan (Bab V) | Kesimpulan mengikuti hasilnya? |

## 2. Cara kerja

1. Ekstrak 6 pernyataan dari peta Jev (deterministik, tanpa LLM): tiap bagian dicari subbabnya dari judul, lalu diambil paragraf di bawahnya sampai subbab berikut (maks ~1500 karakter per bagian).
2. Satu panggil LLM (`_panggil_router`, pintu yang sama dengan Jev/Hakim) menilai 5 sambungan sekaligus. Jawaban berupa JSON: tiap sambungan `nyambung` / `putus` / `ragu` + satu kalimat alasan yang menunjuk kalimat yang tidak nyambung.
3. `ragu` TIDAK divonis: tampil sebagai "Perlu diperiksa" dan mahasiswa diminta cek ke pembimbing. Mesin tidak menghalangi dan tidak berpura-pura tahu.
4. Hasil disimpan ke Setelan (`konsistensi_hasil_berkas_<fid>`), jadi dibaca ulang tanpa panggil LLM lagi. Pemeriksaan ulang hanya bila naskah berubah (sidik berubah).
5. GRATIS: tidak memotong Token Revisi. Biaya LLM dari saldo Apinex Boss.

## 3. Tampilan: ceklist 5 baris

Sama polanya dengan ceklist Struktur naskah dan Daftar Pustaka Hidup:

```
Cek Konsistensi
✓ Masalah ke Tujuan
✓ Tujuan ke Hipotesis
! Hipotesis ke Metode — Uji t tidak menguji H2 ...
✓ Metode ke Hasil
✓ Hasil ke Kesimpulan
```

- Satu baris per sambungan: status (✓ nyambung / ! putus / ? perlu diperiksa) + nama sambungan + satu kalimat alasan bila putus/ragu.
- Ketuk baris: alasan lengkapnya terbuka (kalimat yang tidak nyambung ditunjuk).
- Tidak ada bahasa sistem, tidak ada tombol konfirmasi, tidak ada nomor halaman.
- Tombol "Cek Konsistensi" + keadaan "Sedang Diperiksa" mengikuti pola "Periksa Struktur" (titip ke pekerja latar, baca lewat status).

## 4. Yang TIDAK diubah

- Tidak menulis apa pun ke docx mahasiswa.
- Tidak mengubah label Jev/Hakim dan tidak memakai antrean peta (ragu konsistensi bukan baris peta, jadi tidak masuk AntreanPeta).
- Tidak memotong token. Tidak memblokir naskah.

## 5. Kriteria terima (diuji di fid 81)

1. 6 bagian terekstrak dari peta fid 81 (masalah, tujuan, hipotesis, metode, hasil, kesimpulan), masing-masing tidak kosong.
2. 5 sambungan dinilai, tiap vonis salah satu dari nyambung/putus/ragu + satu kalimat alasan.
3. Panel menampilkan 5 baris dengan status yang benar; ketuk baris membuka alasannya.
4. Pemeriksaan kedua tanpa perubahan naskah memakai hasil tersimpan (0 panggil LLM).
5. Tidak ada kata "salah" di teks tampil; tidak ada pemotongan token (saldo user 8 tetap).
