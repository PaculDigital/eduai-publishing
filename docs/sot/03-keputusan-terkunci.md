# 03 — Keputusan Terkunci Boss

<!-- SOT: Keputusan Boss yang masih berlaku. Diperbarui 26 Okt 2026. Setiap keputusan ber tanggal; yang tidak ber tanggal di sini dianggap belum terkunci. -->

## Keputusan yang masih berlaku

| Tanggal | Keputusan |
|---|---|
| 11–13 Sep 2026 | Visi: portal dokumen akademik self-hosted + AI bantu penelitian. 4 layanan core awal: storage, AI revisi, AI belajar, AI jurnal. Funnel: storage (freemium) → revisi → belajar → jurnal. |
| 13 Sep 2026 | Model bisnis Paket + AddOn: PAKET = tiket masuk, ADDON = mesin uang (murah, dibeli berkali-kali). AddOn TERKUNCI untuk paket Gratis (wajib minimal Penulis). Kuota habis → tawarkan AddOn, BUKAN upgrade paket. Reset tiap tanggal 1, sisa hangus. Konversi & Belajar tidak reset bulanan. |
| 15 Sep 2026 | Klasifikasi dokumen & onboarding terarah (jenjang → bidang → mode → judul). Batas berkas 5 MB, timeout AI 420 detik. Dosen gratis sebagai akuisisi (rencana awal; angka paket kini lihat `04-harga-dan-kuota.md`). |
| 16 Sep 2026 | Aturan induk: DILARANG MENAMBAL — reproduksi, ukur, buka rujukan, cari akar 3–5 lapis, perbaiki akar + pasang gerbang. |
| 26 Sep 2026 | Harga token per bab TERKUNCI (lihat `04-harga-dan-kuota.md`). Tiap bab beda bobot kerja. |
| 03 Okt 2026 | Pembimbing AI = saklar (`PEMBIMBING_AI_AKTIF`), bisa dimatikan tanpa menyentuh jalur mahasiswa. Pembimbing paket gratis dibuka khusus lewat `/tinjau`, bukan global. |
| 06 Okt 2026 | Satu proyek = satu dunia (jangan pinjam kredensial antar proyek). Jembatan antar layanan hanya lewat API resmi + kunci layanan, bukan pinjam kredensial. |
| 08 Okt 2026 | Jembatan EduAi→Statistik Lab diizinkan: rumah data = EduAi, mesin hanya hitung & tidak menyimpan, parsing oleh Jev/AI EduAi. |
| 21 Okt 2026 | Jembatan EduAi→Statistik Lab OPSI B: header `X-Kunci-Layanan`, timeout 60 detik. BAB IV = Hasil & Pembahasan (BUKAN BAB III Metodologi). Tarif BAB IV terkunci (lihat `04-harga-dan-kuota.md`). |
| 13 Okt 2026 | Kata kunci AI & pagar tanggung jawab AI: AI HANYA menyusun kata kunci (tidak pernah menyebut artikel); artikel 100% dari database nyata (Scopus/OpenAlex/Garuda/CrossRef) + audit DOI ke CrossRef + saring relevansi. Jika AI salah baca variabel → query salah → hasil 0 artikel → user TAHU. Tidak ada jalan dari kata kunci salah menuju artikel palsu. (Asal: `PUTUSAN_KATA_KUNCI_AI_13OKT2026.md`, diarsipkan 26 Okt 2026 — intinya dipindahkan ke sini.) |
| 21 Okt 2026 | Prinsip BAB IV: jendela "Olah Data dan Narasi" privat dari pembimbing sampai mahasiswa sengaja mengekspornya ke naskah. AI berbayar opsional, tidak pernah dipaksa — jalur manual penuh harus tetap bisa dilalui. |
| 21 Okt 2026 | Prinsip pengalaman mahasiswa: di luar semua harus terasa sederhana & mudah; kerumitan di bawah tidak boleh membingungkan mahasiswa. |
| 23 Okt 2026 | Keputusan SSOT buku: judul referensi TNR 16 SAH; gutter A5/B5 = 0; buku umum pindah B5; gaya gambar umum = infografis 3D kartun (anak tetap flat putih, pendidikan tetap flat). |
| 24 Okt 2026 | Perapihan dokumen: arsipkan yang usang ke `_arsip/` (bukan hapus permanen) — perintah Boss 26 Okt 2026, dieksekusi di cabang `agen/wulan/rapi-sot-26okt2026`. |

## Yang masih TERBUKA (belum diputuskan — jangan dikarang)

1. **Deploy BAB IV** — merge sudah selesai, build/deploy image + kunci produksi `EDUAI_STATISTIK_KUNCI` masih menunggu Boss.
2. **Nasib commit yatim `73a7a64`** (narasi 4.3 kualitatif, 21 Okt) — tidak ikut ke `main`.
3. **Harga paket di dokumen vs kode** — `app/config.py` (Peneliti Rp100rb / Penerbit Rp300rb) vs dokumen lama (Rp160rb / Rp500rb). Yang ditagih = kode; penyelarasan dokumen lama menunggu keputusan Boss (bukan diubah diam-diam di perapihan ini).
4. **Sisip artikel ke bab** (putusan 13 Okt) — BELUM dikoding.
5. **Gerbang font di server produksi** (barang SSOT buku #8, sisa 1 dari 20) — menunggu Boss mengunggah font berlisensi lalu menjalankan `periksa_font` di server.
6. **Komentar kode yang menunjuk berkas arsip** — belum diperbarui (pekerjaan susulan perapihan dokumen).
7. **Keputusan waktu bayar campuran BAB IV** (per putaran vs 60 di depan) — belum dijawab Boss (catatan 21 Okt).

## Yang SUDAH tidak berlaku (dicatat supaya tidak dihidupkan lagi)

- Klaim "MASTER_PLAN.md / SOT.md lama / MULAI_DARI_SINI.md adalah satu-satunya sumber kebenaran" — ketiganya sudah diarsipkan 26 Okt 2026 dan digantikan hierarki di `SOT.md` baru. Jangan mengutip ketiganya sebagai keadaan kini.
- Harga paket lama di MASTER_PLAN (Rp160rb / Rp500rb) — tidak berlaku sebagai harga tagih (lihat `04-harga-dan-kuota.md`).
- Status-status di berkas arsip (mis. "BELUM merge", "BELUM deploy" dari Oktober awal) — keadaan kini ada di `SOT.md` + `sot.py`, bukan di arsip.
