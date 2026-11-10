# Rencana Skala Jev/Hakim untuk Ribuan Naskah (v8)

Status: **BAHAS DULU**. Rencana saja, bukan kode. Belum dibangun, belum push, belum merge, belum deploy.
Tanggal: 10 November 2026.
Dasar ukur: hasil live v7 (3 run x 4 naskah), branch `agen/wulan/optimalkan-jev-hakim-v5` commit `b41392a`.

## 1. Hitungan biaya dan waktu

### Angka dasar yang dipakai (terukur, bukan karangan)

Per naskah, hasil live v7:

| Naskah | Panggilan Jev | Waktu |
|---|---|---|
| fid=112 | 40 | 26 detik |
| fid=115 | 36 | 22 detik |
| fid=81 | 7 | 6 detik |
| WULAN-1 | 7 | 5 detik |

Rata-rata 4 naskah: **22,5 panggilan dan 15 detik per naskah**.
Rentang terukur: **7 sampai 42 panggilan, 5 sampai 30 detik per naskah**.

### Asumsi yang ditulis jelas

1. Naskah baru diasumsikan mirip 4 naskah uji ini. Naskah yang lebih besar atau lebih rusak dari fid=115 bisa melewati rentang atas.
2. Panggilan Jev dan waktu jalan berurutan per naskah, jadi waktu serial adalah jumlah waktu per naskah.
3. Pekerja paralel diasumsikan membagi waktu dengan efisiensi 0,8 (ada jeda, antrean, dan batas laju). Angka paralel di bawah ini adalah perkiraan, bukan janji, karena batas laju TypeSafe belum diukur (lihat bagian 2.3).
4. Harga per panggilan Jev **belum diketahui**. Semua hitungan di bawah ini memakai jumlah panggilan, bukan rupiah. Harga rupiah hanya bisa dihitung sesudah harga per panggilan diketahui dari penyedia.

### 1.000 naskah

| Skenario | Panggilan Jev | Jam serial | 4 pekerja | 8 pekerja | 16 pekerja |
|---|---|---|---|---|---|
| Ringan (7 panggilan, 5 detik) | 7.000 | 1,4 jam | 0,4 jam | 0,2 jam | 0,1 jam |
| Khas (22,5 panggilan, 15 detik) | 22.500 | 4,2 jam | 1,3 jam | 0,7 jam | 0,3 jam |
| Berat (42 panggilan, 30 detik) | 42.000 | 8,3 jam | 2,6 jam | 1,3 jam | 0,7 jam |

### 10.000 naskah

| Skenario | Panggilan Jev | Jam serial | 4 pekerja | 8 pekerja | 16 pekerja |
|---|---|---|---|---|---|
| Ringan (7 panggilan, 5 detik) | 70.000 | 14 jam | 4,3 jam | 2,2 jam | 1,1 jam |
| Khas (22,5 panggilan, 15 detik) | 225.000 | 42 jam | 13 jam | 6,5 jam | 3,3 jam |
| Berat (42 panggilan, 30 detik) | 420.000 | 83 jam | 26 jam | 13 jam | 6,5 jam |

### Yang dibaca dari angka ini

- Serial saja masih sanggup untuk 1.000 naskah khas (4,2 jam, selesai dalam satu malam). Untuk 10.000 naskah, serial tidak sanggup (42 jam khas, 83 jam berat), paralel wajib.
- Panggilan Jev adalah biaya utama, bukan waktu. 10.000 naskah khas berarti 225.000 panggilan. Bila harga per panggilan diketahui, kalikan langsung dengan angka ini.
- Paralel 16 pekerja hanya membantu bila batas laju TypeSafe mengizinkan. Bila batas laju lebih rendah dari 16 panggilan bersamaan, menambah pekerja tidak mempercepat apa pun, hanya menambah antrean dan risiko 503. Karena itu probe batas laju (bagian 2.3) adalah langkah pertama sebelum klaim waktu paralel.

## 2. Arsitektur

### 2.1 Antrean job

Satu baris antrean per naskah, dengan kolom:

- `naskah_id`, `status`, `percobaan`, `pekerja`, `dimulai`, `selesai`, `panggilan_jev`, `kesalahan_terakhir`, `sidik_teks`, `versi_aturan`.

Status yang dipakai, dan artinya:

- `menunggu`: belum dikerjakan.
- `jalan`: sedang dipetakan oleh satu pekerja.
- `selesai`: peta tersimpan dan lolos pemeriksaan akhir.
- `gagal`: berhenti karena kesalahan yang bisa dicoba lagi (mis. 503, putus koneksi).
- `gagal_tetap`: berhenti karena kesalahan yang tidak bisa dicoba lagi (mis. berkas rusak, teks kosong). Manusia yang memutuskan.
- `ditahan`: menunggu label manusia (lihat bagian 3.3).

Aturan antrean:

- Satu naskah hanya dikerjakan satu pekerja dalam satu waktu. Pekerja mengambil job dengan kunci, bukan dengan membaca lalu menulis tanpa kunci, supaya dua pekerja tidak mengerjakan naskah yang sama.
- **Retry**: job `gagal` dicoba lagi paling banyak 3 kali, dengan jeda yang membesar (mis. 1 menit, 5 menit, 15 menit). Sesudah 3 kali, status jadi `gagal_tetap` dan masuk daftar manusia.
- **Resume**: pekerja menyimpan kemajuan per tahap (teks dibaca, kandidat dibuat, gelombang selesai, tanya ulang selesai, Hakim selesai). Bila proses berhenti di tengah, job kembali ke `menunggu` dengan kemajuan yang sudah tersimpan, dan pekerja berikutnya melanjutkan dari tahap terakhir yang selesai, bukan dari awal. Tanpa ini, satu kali restart membuang semua panggilan Jev yang sudah dibayar.
- **Idempotensi**: menjalankan job yang sama dua kali tidak boleh menulis peta dua kali dan tidak boleh memanggil Jev dua kali untuk tahap yang sama. Kunci idempotensi adalah pasangan `sidik_teks` dan `versi_aturan` (lihat bagian 2.4).

### 2.2 Pekerja paralel antar naskah

- Pekerja adalah proses yang sama dengan pemeta sekarang, hanya dijalankan beberapa salinan sekaligus. Tidak ada perubahan logika pemetaan di dalam pekerja.
- Paralel hanya antar naskah, bukan di dalam satu naskah. Gelombang di dalam satu naskah tetap berurutan, karena tiap gelombang butuh konteks naskah yang sama dan urutan yang tetap.
- Jumlah pekerja diatur lewat satu angka di config, bukan hardcode. Mulai dari 4, naik hanya sesudah probe batas laju (bagian 2.3) membuktikan aman.
- Satu pekerja, satu naskah, satu waktu. Pekerja tidak mengambil job baru sebelum job lamanya selesai atau gagal dan dilepas kuncinya. Bila pekerja mati mendadak, kuncinya kedaluwarsa sesudah batas waktu (mis. 10 menit tanpa detak) dan job kembali ke `menunggu`.
- Batas laju bersama dipakai semua pekerja. Bila batas laju tercapai, pekerja menunggu, bukan memaksa. Memaksa hanya menghasilkan 503 dan membuang panggilan.

### 2.3 Batas laju TypeSafe (rencana probe, bukan klaim angka)

Angka batas laju TypeSafe **belum diukur**. Rencana ini tidak mengklaim angka apa pun. Probe yang aman:

1. Mulai 1 pekerja, 10 naskah berurutan. Catat panggilan per menit dan berapa 503 yang muncul.
2. Naik ke 2 pekerja, 10 naskah. Bandingkan dengan langkah 1.
3. Naik ke 4 pekerja, 10 naskah. Bila 503 muncul atau waktu per naskah memburuk, berhenti di angka sebelumnya.
4. Ulangi di jam yang berbeda, karena batas laju bisa berubah menurut beban penyedia.
5. Catat hasilnya sebagai angka resmi batas laju di dokumen ini, baru sesudah itu hitungan paralel di bagian 1 boleh dipakai sebagai janji.

Yang tidak boleh dilakukan: menebak batas laju dari dokumentasi umum, atau langsung menjalankan 16 pekerja di ribuan naskah tanpa probe. Itu cara paling cepat mendapat 503 massal dan membuang panggilan Jev.

### 2.4 Cache peta di database

Keadaan sekarang: cache peta hanya hidup di dalam satu proses. Bila proses mati atau pekerja lain mengambil naskah yang sama, peta dihitung ulang dan Jev dibayar ulang.

Rancangan cache:

- Kunci cache: `sidik_teks` (hash isi teks naskah) ditambah `versi_aturan` (mis. `jev-peta-v6.8`). Bila teks berubah satu huruf, sidik berubah dan peta dihitung ulang. Bila aturan berubah, versi berubah dan semua cache lama kedaluwarsa.
- Isi cache: peta lengkap (label per baris, goyang, p, dan hasil Hakim) plus waktu simpan dan jumlah panggilan Jev yang dipakai untuk menghasilkannya.
- Alur: sebelum memanggil Jev, pekerja memeriksa cache dengan kunci itu. Bila ada, peta dipakai langsung, nol panggilan Jev. Bila tidak ada, peta dihitung dan hasilnya disimpan ke cache sebelum job ditandai `selesai`.
- Cache disimpan di database yang sudah ada (tabel baru, bukan tabel `proses_ai` yang dipakai guard deploy), supaya semua pekerja melihat cache yang sama.
- Cache tidak pernah dipakai untuk naskah yang teksnya berubah, dan tidak pernah dipakai lintas versi aturan. Aturan baru berarti hitung ulang, bukan memakai peta lama.
- Perkiraan manfaat: untuk naskah yang diunggah ulang tanpa perubahan (kasus yang sering terjadi di bimbingan), penghematan 100 persen panggilan Jev. Untuk naskah baru, penghematan nol. Manfaat nyata hanya bisa diukur sesudah ada data berapa persen naskah yang diunggah ulang.

### 2.5 Pemantauan kemajuan per naskah

Satu layar pantau, satu baris per naskah, dengan kolom: naskah, status, tahap, panggilan Jev sejauh ini, waktu berjalan, dan kesalahan terakhir bila ada.

Angka yang dipantau selama jalan:

- Naskah selesai per jam, dan perkiraan selesai untuk sisa antrean.
- Panggilan Jev per jam, dan total panggilan sejauh ini.
- Jumlah 503 dan gagal per jam. Bila 503 naik mendadak, turunkan jumlah pekerja, jangan naikkan.
- Jumlah `gagal_tetap` dan `ditahan`, supaya antrean manusia tidak tumbuh diam-diam.

Peringatan yang berhenti otomatis: bila 503 melebihi ambang (mis. 5 dalam 10 menit), semua pekerja berhenti mengambil job baru sampai manusia memeriksa. Lebih baik berhenti sebentar daripada membuang ratusan panggilan ke 503.

## 3. Apa yang diputuskan kode vs Jev, dan bagaimana Hakim menangani ribuan naskah

### 3.1 Yang tetap diputuskan kode (tanpa Jev)

Prinsip yang sudah terbukti di v4 sampai v7: bukti langsung tetap di kode, Jev hanya menjawab yang kode tidak bisa putuskan. Pada skala ribuan, prinsip ini menjadi penghemat biaya utama, karena tiap baris yang diputuskan kode adalah nol panggilan Jev.

Yang diputuskan kode:

- Penanda BAB deterministik ("BAB I", "BAB 1", angka Romawi). Sudah di v6.4, dipertahankan.
- Pisah judul BAB dan subbab yang berekor kalimat. Sudah di v6.2 dan v7.1, dipertahankan.
- Segmentasi kata sesudah stitch untuk teks pecah per huruf. Sudah di v6.1 dan v6.8, dipertahankan.
- Saring sampah ke `buang` sebelum Jev (nomor halaman, fragmen tabel, potongan SPSS).
- Audit deterministik Hakim: penomoran loncat, subbab yatim, judul lebih dari 300 karakter, judul huruf kecil, fragmen tabel.

Yang tidak boleh dipindah ke kode: penilaian makna baris yang benar-benar ambigu. Kode yang menebak makna hanya memindahkan kesalahan dari Jev ke kode, tanpa jejak goyang dan p untuk menangkapnya.

### 3.2 Yang tetap ditanya ke Jev

- Klasifikasi baris kandidat yang tidak bisa diputuskan kode (bab, subbab, paragraf, biasa).
- Stitch, yaitu apakah dua baris yang menggantung adalah satu baris yang sama.
- Tanya ulang hanya untuk baris yang goyang atau p rendah. Sudah terbukti bermanfaat di v7 (34 balik label, 31 bertahan dari 12 run). Dipertahankan, dengan cap per gelombang seperti v5.1.
- Pertanyaan Hakim yang sempit, yang kode tidak bisa putuskan.

### 3.3 Hakim dan antrean ragu/curiga ribuan naskah

Masalah skala: pada 4 naskah uji, Hakim menghasilkan 0 sampai 14 ragu dan 0 sampai 5 curiga per naskah. Bila 1.000 naskah menghasilkan rata-rata 5 ragu dan 2 curiga, antrean manusia menjadi 5.000 ragu dan 2.000 curiga. Tanpa penyaringan, manusia tenggelam.

Cara Hakim menangani antrean sebesar itu:

1. **Hakim tetap log saja, tidak memblokir.** Ini keputusan Boss yang dipertahankan. Peta yang ada ragu atau curiga tetap tersimpan dan tetap bisa dipakai, dengan bendera yang terlihat. Tidak ada naskah yang tertahan hanya karena Hakim ragu.
2. **Urutkan antrean menurut dampak, bukan menurut waktu.** Curiga yang menyangkut label BAB didahulukan, karena satu BAB yang salah mengubah seluruh peta. Curiga pada satu paragraf didahulukan paling akhir. Ragu yang hanya soal batas paragraf didahulukan paling akhir, karena batas paragraf adalah sumber goyang terbesar dan paling sering benar di salah satu run.
3. **Kelompokkan pola yang sama.** Bila 200 naskah punya curiga yang sama (mis. pola sitasi yang sama salah terlabel judul), kelompok itu ditangani sekali sebagai perbaikan aturan kode, bukan 200 kali sebagai keputusan manusia. Perbaikan aturan lalu diuji di gerbang 3-naskah sebelum dipakai massal.
4. **Batas harian manusia.** Tentukan jumlah ragu/curiga yang sanggup ditangani manusia per hari (mis. 50). Antrean di atas batas itu bukan dikerjakan lembur, melainkan ditandai sebagai utang tinjauan dan dilaporkan. Sistem yang jujur soal utang tinjauan lebih baik daripada sistem yang pura-pura semua sudah ditinjau.
5. **Jangan kirim semua ragu ke manusia sekaligus.** Antrean ragu dikirim dalam kelompok kecil per naskah, supaya manusia meninjau satu naskah sampai tuntas sebelum pindah ke naskah berikut. Tinjauan yang berpindah-pindah naskah lebih banyak salahnya.

## 4. Prasyarat sebelum skala

Tidak ada satu pun yang boleh dilewati. Skala tanpa prasyarat ini hanya memperbesar kesalahan yang sama ke ribuan naskah.

### 4.1 Label kebenaran dasar (ground truth)

- Yang dibutuhkan: label benar untuk baris yang diperselisihkan antar run, terutama batas paragraf dan deteksi BAB. Tanpa ini tidak ada cara membedakan variansi mana yang salah.
- Pekerjaan ini adalah pekerjaan manusia, bukan ronde kode. Manusia memberi label benar pada baris yang diperselisihkan di naskah uji.
- Ukuran awal yang masuk akal: 3 naskah (Asih, fid=115, fid=112) dengan label benar untuk semua baris yang goyang di 3 run v7. Bila label ini ada, tiap ronde kode berikutnya bisa diukur benar atau salah, bukan hanya stabil atau goyang.
- Tanpa label ini, klaim "optimal" tidak bisa dibuktikan, karena stabil belum tentu benar.

### 4.2 Gerbang 3-naskah

- Gerbang yang belum selesai sejak Oktober 2026: tiap perubahan aturan harus lolos di 3 naskah yang sama sebelum dipakai.
- Aturan gerbang: perubahan yang membuat satu naskah membaik tapi satu naskah lain memburuk tidak lolos. Perubahan yang hanya membaik di satu naskah dan netral di dua naskah lain lolos dengan catatan.
- Gerbang harus selesai dan ditulis sebagai pemeriksaan otomatis (bukan janji lisan) sebelum skala. Pada skala ribuan, perubahan aturan yang tidak lewat gerbang bisa merusak ribuan peta dalam satu malam.

### 4.3 Keputusan model 1.13 ke 1.14

- Model `typesafe/jev-1.13` pensiun sekitar **13 Desember 2026**.
- Model 1.14 sudah diukur lebih yakin tapi menjauh dari baseline, dan lebih goyang di naskah sulit. Pin tetap 1.13 sampai ada label kebenaran dasar.
- Keputusan yang harus diambil Boss sebelum skala: pindah ke 1.14, tetap di 1.13 sampai pensiun lalu pindah, atau uji model lain. Keputusan ini tidak bisa ditunda sampai sesudah skala dimulai, karena pindah model di tengah ribuan naskah berarti dua kelompok naskah dipetakan model yang berbeda dan tidak bisa dibandingkan.
- Bila pindah ke 1.14, semua angka dasar di bagian 1 harus diukur ulang, karena panggilan, waktu, dan goyang 1.14 belum tentu sama dengan 1.13.

### 4.4 Uji beban kecil sebagai bukti sebelum klaim ribuan

- Uji beban: 10 naskah paralel (4 pekerja), di luar 4 naskah uji yang sudah ada, dengan antrean, retry, resume, dan cache yang sudah dibangun.
- Yang diukur: waktu per naskah di paralel, jumlah 503, jumlah job yang butuh retry, apakah resume bekerja bila satu pekerja dimatikan di tengah, dan apakah cache menghemat panggilan untuk naskah yang diunggah ulang.
- Uji beban 10 naskah bukan bukti untuk 10.000 naskah, tapi tanpa uji beban ini, klaim apa pun soal ribuan naskah hanya teori. Bila 10 naskah saja sudah gagal, ribuan naskah pasti gagal lebih besar.
- Setelah uji beban 10 naskah lolos, naik bertahap: 100 naskah, lalu 1.000 naskah. Jangan loncat dari 10 langsung ke 10.000.

## 5. Risiko yang jujur

### 5.1 Variansi model antar run

- Terbukti di v7: paragraf fid=81 bergoyang 166 sampai 173 dalam 3 run, deteksi BAB kadang kehilangan satu BAB, dan satu judul BAB sampah muncul di 1 dari 12 run.
- Pada skala ribuan, variansi ini berarti ratusan naskah punya peta yang berbeda bila dipetakan dua kali. Ini bukan cacat yang bisa dihilangkan dengan ronde kode, karena sumbernya adalah model Jev sendiri.
- Penanganan: label kebenaran dasar (bagian 4.1) untuk mengukur mana yang salah, dan tanya ulang bertarget untuk baris yang goyang. Bila variansi tetap besar sesudah itu, terima sebagai batas sistem dan laporkan rentangnya, jangan pura-pura peta itu pasti.

### 5.2 Biaya Jev

- 10.000 naskah khas berarti 225.000 panggilan. Harga per panggilan belum diketahui, jadi total biaya rupiah belum bisa dihitung. Ini risiko terbesar yang belum terukur.
- Bila harga per panggilan ternyata besar, skala ribuan bisa menjadi tidak sanggup secara biaya, bukan secara teknis. Hitung biaya rupiah sebelum membangun, bukan sesudah 10.000 naskah selesai.
- Penghemat biaya yang sudah terbukti: putuskan sebanyak mungkin di kode (bagian 3.1), cache naskah yang diunggah ulang (bagian 2.4), dan tanya ulang hanya untuk yang goyang.

### 5.3 Batas laju

- Batas laju TypeSafe belum diukur. Bila batasnya rendah, semua hitungan paralel di bagian 1 tidak berlaku, dan 10.000 naskah bisa memakan waktu berminggu-minggu, bukan berjam-jam.
- 503 massal adalah cara kegagalan yang paling mungkin terjadi pertama kali, karena probe batas laju belum pernah dilakukan.
- Penanganan: probe bertahap (bagian 2.3), jeda adaptif yang sudah ada sejak v4, dan berhenti otomatis bila 503 naik (bagian 2.5).

### 5.4 Apa yang bisa gagal duluan

Urutan kegagalan yang paling mungkin, dari yang paling cepat terjadi:

1. **Batas laju (503 massal)** pada uji beban pertama, bila pekerja langsung dijalankan banyak tanpa probe.
2. **Biaya Jev membengkak** bila cache tidak bekerja dan naskah yang diunggah ulang dipetakan ulang dari awal.
3. **Antrean ragu/curiga menenggelamkan manusia**, bila Hakim dibiarkan mengirim semua ragu tanpa pengelompokan dan batas harian.
4. **Model 1.13 pensiun di tengah jalan** (sekitar 13 Desember 2026) bila keputusan 1.14 ditunda sampai skala sudah berjalan.
5. **Satu perubahan aturan merusak ribuan peta**, bila gerbang 3-naskah belum selesai dan perubahan langsung dipakai massal.

### 5.5 Yang rencana ini tidak janjikan

- Rencana ini tidak menjanjikan waktu pasti untuk ribuan naskah, karena batas laju dan harga per panggilan belum diukur.
- Rencana ini tidak menjanjikan peta yang pasti benar, karena variansi model antar run terbukti masih ada dan label kebenaran dasar belum ada.
- Rencana ini tidak menggantikan keputusan Boss soal model 1.14 dan soal berapa banyak ragu/curiga yang sanggup ditinjau manusia per hari.

## 6. Urutan kerja yang diusulkan (bila Boss Gas)

1. Label kebenaran dasar untuk 3 naskah uji.
2. Selesaikan gerbang 3-naskah sebagai pemeriksaan otomatis.
3. Keputusan model 1.13 ke 1.14.
4. Probe batas laju TypeSafe (1, 2, lalu 4 pekerja).
5. Bangun antrean job, retry, resume, dan cache di database.
6. Uji beban 10 naskah paralel.
7. Naik ke 100 naskah, ukur ulang biaya dan waktu, lalu putuskan 1.000 naskah.
8. 10.000 naskah hanya sesudah 1.000 naskah selesai tanpa 503 massal dan tanpa antrean manusia yang menumpuk.
