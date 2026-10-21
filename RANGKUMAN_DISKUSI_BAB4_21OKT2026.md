# RANGKUMAN DISKUSI BAB IV — 21 Oktober 2026

Peserta: Bos (pemilik) + Wulan · Mode: BAHAS DULU, belum koding.
Melengkapi: AUDIT_WULAN_BAB4_21OKT2026.md + RANCANGAN_JEMBATAN_BAB4_21OKT2026.md

## A. SUDAH TERKUNCI (keputusan Bos)

1. **Istilah**: yang dibangun = BAB IV HASIL & PEMBAHASAN, backend Statistik
   Lab. (Metodologi = BAB III, bukan yang ini.)
2. **Syarat memulai**: sistem tahu model + desain + rumusan/pertanyaan
   masalah dari bab sebelumnya (dibaca Jev/AI dari BAB I–III user).
3. **Mekanisme peta penelitian**: Jev menemukan tempatnya → AI mengusulkan
   variabel & peran (X/M/Z/Y) WAJIB dengan bukti kalimat dari naskah →
   aturan pemeriksa menjaga konsistensi jalur (mis. ada M wajib ada jalur
   masuk+keluar; jumlah jalur = jumlah hipotesis) → USER mengesahkan di
   satu kartu peta sebelum apa pun dibuat.
4. **Prinsip tanya fakta, bukan label**: user TIDAK PERNAH ditanya memilih
   label jargon ("survei/eksperimen/pembanding?") — kebanyakan salah pilih.
   AI menentukan label dari sidik jari fakta di naskah (perlakuan? kontrol?
   ukur 2×? kuesioner sekali sebar?). Kalau fakta kurang, yang ditanyakan
   adalah pertanyaan FAKTA bahasa sehari-hari tentang apa yang user
   lakukan. User mengonfirmasi CERITA faktual, label dihitung aturan.
5. **Senjata ke lapangan selalu berpasangan** (alat ambil data + wadah
   pengembalian), lahir dari peta yang sama → "match data":
   - Kuantitatif: kuesioner dari indikator definisi operasional (skala 1–5)
     + template data berkomposisi kolom yang sama + kartu petunjuk lapangan.
   - Kualitatif: panduan wawancara per jenis informan (internal/eksternal,
     dirancang berpasangan untuk triangulasi) + template catatan hasil
     + kartu petunjuk.
6. **Satu halaman "Data Lapangan"**, tiga pintu, semua mengisi tabel yang
   sama (baris=responden/informan, kolom=butir/pertanyaan) dan selalu bisa
   diperiksa & dibetulkan user sebelum dihitung:
   - KETIK: formulir online EduAi (user menyalin dari Google Form-nya
     sendiri; EduAi TIDAK mengelola Google Form — ditolak karena izin &
     hak akses Google rumit).
   - UPLOAD: file template dari EduAi → isi tabel langsung terisi otomatis.
   - SIMULASI: tombol pengisi otomatis untuk belajar.
7. **Simulasi terbagi benar**: kuantitatif = MESIN Statistik Lab (BUAT DATA
   terkalibrasi per jalur — angka konsisten dengan model; AI tidak mengarang
   angka). Kualitatif = AI (informan fiktif + jawaban teks per jenis
   informan, pola transkrip latihan modul kualitatif).
8. **Simulasi bisa diatur user** (panel seperti BUAT DATA, bahasa sederhana):
   kuantitatif — tiap jalur dipilih Kuat/Sedang/Lemah/Tidak berpengaruh;
   kualitatif — tiap tema dipilih kuat (semua informan) / sebagian /
   bertentangan, plus jumlah informan. Tujuan: mahasiswa belajar membaca
   data dari akibat pilihannya sendiri (termasuk pelajaran: pengaruh lemah
   + sampel kecil = tidak signifikan).
9. **Visual diagram model berlabel H1, H2, H3 dst** — tampil di 3 momen
   dengan gambar yang sama: pengesahan peta, panel simulasi (pengatur
   menempel di panah), dan hasil hitung (panah menyala/pudar + angka).
   Mahasiswa melihat BERAPA hubungan yang harus ia uji.
   Padanannya kualitatif: peta fokus × informan (gambar triangulasi).
10. **Simulasi TERKUNCI pada model penelitian mahasiswa sendiri** (kedua
    jalur). Mau bebas coba model lain → ke Statistik Lab langsung.
    Alasan: melindungi jalur olah data asli EduAi dari campuran mainan,
    dan menjaga pembagian dua produk (EduAi = ruang kerja resmi,
    Statistik Lab = laboratorium bebas).
11. **Rumah data = EduAi**; mesin Statistik Lab hanya menghitung
    (putusan lama 08 Okt §4.4 tetap berlaku). AI membaca bab sebelumnya
    + hasil olahan → menyusun narasi BAB IV (kuantitatif & kualitatif).
12. **Label simulasi**: data simulasi bertanda SIMULASI, BAB IV darinya =
    draf latihan; data asli masuk → tanda hilang, draf diganti hasil asli.
    (Prinsip diusulkan Wulan, sejalan dengan tujuan belajar Bos.)

## B. ALUR UTUH (hasil gabungan A)

```
Naskah BAB I–III
 → [1] Jev+AI baca → usulan peta (bukti terlampir)
 → [2] User sahkan peta (betulkan cerita fakta bila perlu)
 → [3] Senjata dibuat dari peta (kuesioner/panduan + template + petunjuk)
 → [4] User ke lapangan (atau tekan SIMULASI untuk latihan)
 → [5] Data kembali ke halaman Data Lapangan (ketik / upload / simulasi)
 → [6] User periksa & betulkan tabel → kirim
 → [7] Jembatan → mesin Statistik Lab hitung (tidak menyimpan)
 → [8] Hasil + tabel + grafik kembali, disimpan di EduAi
 → [9] AI tafsir (baca hasil + BAB II/III) → draf BAB IV 4.1–4.5 di editor
 → [10] Jev periksa → user terima/tolak per bagian (pola revisi lama)
```

## C. YANG KURANG / BELUM DIPUTUSKAN (penghalang BAB IV utuh)

### C1. Keputusan Bos yang masih terbuka
1. **Bentuk jembatan**: Opsi A (alur unggah 2 langkah mesin apa adanya,
   data singgah di memori ≤45 mnt) vs Opsi B (endpoint stateless khusus
   di Statistik Lab). Rekomendasi Wulan: A prototipe → B produksi.
2. **Deskriptif 4.2 & karakteristik responden 4.1** dihitung di mana —
   mesin belum mengeluarkannya. Pilihan: hitung ringan di EduAi dari data
   EduAi sendiri, atau tambah ke respons mesin (sekalian Opsi B).
   Termasuk: kolom demografis (usia/jenis kelamin) masuk kontrak peta?
3. **Harga yang belum diputuskan**: (a) senjata/kuesioner masuk token
   olah_data (30) atau AddOn terpisah; (b) simulasi gratis / token /
   berapa kali; (c) data keliru → charge perbaikan berapa & bentuknya.
   (Harga analisa 30 & olah_data 30 SUDAH ada di config.)
4. **Token antar-layanan** untuk jembatan produksi (API mesin hari ini
   publik tanpa kunci) — ACC pembuatan kunci baru milik EduAi.
5. **Cara Wulan push/PR branch ini** (PAT sesaat / fork / lokal saja).

### C2. Bagian rancangan yang belum dibahas sama sekali
6. **Jembatan KUALITATIF**: kontraknya belum dirancang — data informan di
   EduAi dikirim ke mesin kualitatif Statistik Lab (koding/triangulasi)
   dalam bentuk apa? Atau koding dikerjakan di EduAi dan Statistik Lab
   hanya untuk kuantitatif? Ini lubang terbesar setelah C1.1.
7. **Kerangka BAB IV kualitatif**: kerangka_bab.py yang ada berorientasi
   kuantitatif (4.2 statistik deskriptif, 4.3 uji prasyarat, 4.4 uji
   hipotesis). Versi kualitatifnya (deskripsi situs/informan, temuan per
   tema, triangulasi, pembahasan) belum disusun.
8. **Mixed methods**: urutan & penggabungannya (kuantitatif dulu →
   kualitatif → diskusi terintegrasi) belum dibahas untuk EduAi.
9. **Uji coba instrumen**: kuesioner hasil senjata — perlu uji
   validitas/reliabilitas pilot (responden kecil) sebelum sebar besar?
   Belum dibahas masuk alur atau tidak.
10. **Batas simulasi**: jumlah responden/informan default & maksimum
    simulasi, dan apakah skenario panel atur SELALU tampil atau hanya
    mode lanjutan (pertanyaan Wulan terakhir sebelum rangkuman ini).

### C3. Teknis yang menunggu C1
11. Endpoint & batas jembatan (timeout, ukuran maks — mesin: 10 MB,
    n bersih ≥10), penanganan mesin sibuk/mati (antrean? pesan ramah?).
12. Modul baru di EduAi (usulan: app/bab4.py + app/jembatan_statistik.py,
    router terpisah) — belum dikoding apa pun (mode bahas dulu).

## D. STATUS SAAT RANGKUMAN DIBUAT
- Kode fitur BAB IV: BELUM ADA (sesuai perintah: bahas dulu).
- Branch lokal agen/wulan/bab4-statistik-backend: 3 dokumen
  (audit, rancangan jembatan, rangkuman ini). Belum push (menunggu C1.5).
