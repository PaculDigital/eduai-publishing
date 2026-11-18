# Rencana: Diagram Model Penelitian dan Desain Penelitian

Catatan Wulan, 14 November 2026, dari diskusi dengan Boss. STATUS: DIBANGUN 17 Nov 2026, branch `agen/wulan/diagram-model-desain`, BELUM merge/deploy/push, menunggu Gas + token Boss.

## Fakta pedoman (diverifikasi dari PEDOMAN_UTUH.txt, 14 Nov 2026 23:39 WIB)
- Bab II 2.3 Hipotesis dan Model Penelitian: 2.3.1 Pengembangan Hipotesis, 2.3.2 Model Penelitian. Model penelitian adalah abstraksi dari fenomena-fenomena yang sedang diteliti; contoh penyusunan ada di Lampiran 24. Hipotesis umumnya HA/H1 tanpa H0; ada uji satu arah dan dua arah.
- Bab III 3.1 Jenis dan Desain Penelitian. Jenis: kualitatif, kuantitatif, campuran. Desain kuantitatif: eksperimental atau survei. Desain kualitatif: eksploratif, fenomenologis, atau studi kasus. Desain campuran: gabungan kuantitatif dan kualitatif.
- Gambar: nomor + judul di BAWAH gambar, rata kiri (Tabel 2 pedoman). Daftar Gambar ada di bagian awal.
- Koreksi: Wulan sempat bilang diagram di 2.3 Kerangka Pikir (itu ikut kerangka buku). Menurut pedoman skripsi, tempatnya 2.3.2 Model Penelitian. Pedoman yang menang untuk skripsi.

## Mekanisme lengkap (disepakati dalam diskusi 14 Nov 2026, 23:33-23:51 WIB)

### 1. Baca dari naskah (di naskah)
- Model dibaca dari naskah mahasiswa sendiri: variabel + peran (X bebas, Z mediator, Y terikat) + hipotesis (H1... dengan arah positif/negatif) dari Bab II, dan jenis + desain dari 3.1. Pedoman tidak menetapkan jumlah model; model mengikuti variabel dan hipotesis mahasiswa, bukan katalog tetap.
- Kalau naskah belum punya model yang dideklarasikan, mahasiswa isi formulir kecil (nama variabel, peran, hipotesis) dulu, baru digambar.

### 2. Periksa gambar yang sudah ada di naskah
- Mesin TIDAK BISA membaca isi gambar (gambar itu piksel; panah dan teks di dalamnya tidak bisa diverifikasi). Yang bisa diperiksa: gambar ada atau tidak, keterangannya benar atau tidak, dan teks modelnya cocok dengan yang dideklarasikan atau tidak.
- Vonis: sesuai (dibiarkan, tidak diganggu), meragukan (ditawarkan ganti), tidak ada (ditawarkan buat). Mahasiswa yang memutuskan; gambarnya tidak diganti diam-diam.
- Ditegaskan Boss 17 Nov 2026 09:24 WIB: bila di naskah sudah ada gambarnya, TAWARKAN DULU, jangan langsung diganti dengan gambar mesin atau gambar mahasiswa sebelumnya.

### 3. Tombol
- "Buat Model Penelitian": menggambar diagram panah dari data model, menyisipkan di 2.3.2. Sesudah dibuat, tombol berubah jadi "Perbarui Model Penelitian" (gambar dibuat ulang kalau hipotesis berubah).
- "Buat Desain Penelitian": membaca jenis + desain dari naskah, menulis teks 3.1, plus diagram alur penelitian, disisipkan di 3.1.

### 4. Menggambar (bukan AI, bukan app lain)
- BUKAN digambar AI (AI selalu merusak teks dan panah; itulah sebabnya ilustrasi buku dilarang pakai teks). Digambar mesin secara deterministik dari data model.
- TIDAK butuh mesin gambar baru, MATLAB, atau install baru. Yang dibutuhkan hanya satu fungsi gambar panah baru di dalam `app/gambar.py` yang sudah ada (modul itu sudah menggambar batang/garis/histogram/pai dengan PIL dan sudah bisa menyisipkan gambar ke docx dengan keterangan via `sisip_gambar_docx` / `sisip_gambar_setelah_bagian`). Panah hanya garis ditambah kepala segitiga kecil.
- Template layout dipilih dari bentuk modelnya (langsung, mediasi, banyak X).

### 5. Template EduAi + geser manual
- Mahasiswa menggambar dengan bebas dan leluasa di template EduAi: geser kotak, ketik label. Panah ikut bergerak karena panah dihitung dari posisi kotak.
- Yang digeser hanya letaknya, bukan modelnya. Kalau hipotesis berubah, gambar dibuat ulang tapi letak yang sudah diatur mahasiswa dipertahankan sebisa mungkin.
- Keputusan Boss 17 Nov 2026 09:22 WIB: mesin menggambar draf dulu; mahasiswa tinggal terima, tolak, atau lengkapi gambar dari mesin. Bila ditolak, mahasiswa menggambar sendiri dengan tool yang disediakan (template EduAi).

### 6. OnlyOffice
- Geser kotak di DALAM OnlyOffice hanya bisa kalau diagram dimasukkan sebagai bentuk asli dokumen (DrawingML), bukan PNG. PNG hanya bisa digeser utuh.
- Keputusan: gesernya di halaman EduAi sendiri; sesudah rapi, dimasukkan ke dokumen sebagai gambar. Bentuk asli dokumen jadi langkah kedua kalau nanti diinginkan.
- PRASYARAT: editor OnlyOffice saat ini sedang gagal di gerbang deploy (KUNCI BEDA, editor -4, di semua deploy 13-14 Nov 2026; skrip perbaikan `scripts/perbaiki_oo.sh` ada, belum dijalankan). Harus diperbaiki dulu sebelum fitur yang bergantung pada editor jalan.

### 7. Alur selesai (desain Boss, 23:51 WIB)
- Gambar bebas di template EduAi, klik "Selesai", jadi PNG, otomatis tersisip di naskah di tempat yang sesuai.
- Tersisip di paragraf sendiri, di tengah, kiri kanan kosong, tanpa teks di sampingnya, supaya teks badan tidak berantakan saat gambar disisipkan.
- Keterangan gambar di bawahnya ("Gambar 2.1 Model Penelitian"), dan gambarnya masuk Daftar Gambar otomatis (daftar turunan dari keterangan, seperti Daftar Isi).

## Harga (keputusan Boss 17 Nov 2026 09:24 WIB)

1 token per gambar (Model Penelitian 1 token, Desain Penelitian 1 token).

## Keadaan kode saat ini (diverifikasi Wulan 14 Nov 2026 23:36 WIB)
- Kerangka sudah menuntut gambar ini: `app/kerangka_bab.py` subbab 2.3 memuat 'GAMBAR kerangka pikir (diagram panah antar variabel)' dan daftar kebutuhan grafik memuat 'kerangka pikir (diagram panah)'; `app/kerangka.py:574` memetakan Bab 2 ke 'diagram_panah'.
- `app/bab4.py` sudah memahami bentuk model penelitian (X, Z mediator, Y).
- Yang BELUM ADA: fungsi gambar panah itu sendiri (`"panah"` 0 kemunculan di `app/gambar.py`). Tinggal satu fungsi baru plus menyambung data modelnya. Satu mesin inti, jangan buat mesin baru (aturan Boss 26 Okt 2026).

## Status build (17 Nov 2026, Gas Boss 09:25 WIB)

SELESAI dibangun, BELUM merge/deploy/push. Commit di branch `agen/wulan/diagram-model-desain` (lihat `git log`).
- Fungsi gambar panah ADA: `gambar_panah` + `gambar_alur` di `app/gambar.py`; data model di `app/diagram.py`; rute + pekerja latar di `app/rute_diagram.py`; 4 layar (`diagram.html`, `diagram_model.html`, `diagram_desain.html`, `diagram_editor.html`); tombol "Diagram" di `app/templates/naskah.html`.
- Tes: `tests/test_diagram.py`, 47 lulus 0 gagal (model mediasi Nura X1/X2/Z/Y, H1-H7; PNG deterministik; sisip + Daftar Gambar + nomor dari render palsu).
- Keputusan yang dibuat sendiri: teks 3.1 ditulis dari template deterministik (bukan AI), gratis, bagian dari 1 token gambar Desain. Alasan: isinya hanya fakta standar (jenis, desain, langkah); tidak butuh AI; hanya ditambah bila 3.1 masih kosong.
- Sederhana (Boss 17 Nov 09:26 WIB): layar utama 33 kata bila belum ada gambar; tombol "Buat Model Penelitian" / "Buat Desain Penelitian" (jadi "Perbarui ..." sesudah dibuat); satu langkah satu layar; "Terima" tampil bila draf belum diubah, "Selesai (1 token)" tampil bila sudah diubah/manual.
- Batas jujur: belum uji live (butuh deploy); model dengan banyak X (lebih dari 4) dan moderator belum diuji; berkas besar belum diuji; nomor Daftar Gambar live butuh OnlyOffice (sudah teruji lewat render palsu saja).
- ATURAN UJI LIVE (Boss 17 Nov 2026 10:51 WIB): uji live fitur skripsi WAJIB di fid 81 (skripsi, user 8 asih.susanti@eduai.test), JANGAN PERNAH di file 126 (buku referensi 191 halaman, milik user 12 uji-buku). Uji live Diagram di file 126 pada 17 Nov 10:50 WIB salah sasaran dan DIHENTIKAN (0 token); yang terbukti hanya mesinnya jalan, bukan di naskah skripsi.
