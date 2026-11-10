# Rancangan Alur User Jev/Hakim — Supaya Tidak Mempersulit User

Status: **BAHAS DULU**. Rencana saja, bukan kode. Belum dibangun, belum push, belum merge, belum deploy.
Tanggal: 10 November 2026.
Dasar ukur: hasil live v7 (3 run x 4 naskah), branch `agen/wulan/optimalkan-jev-hakim-v5` commit `b41392a`; paket label kebenaran dasar commit `ba62c2c`.

## Prinsip yang Boss tetapkan (tidak boleh dilanggar)

1. User hanya unggah naskah, tekan satu tombol, tunggu.
2. Semua yang rumit (stitch, gelombang, tanya ulang, Hakim) jalan di belakang dan tidak terlihat.
3. Hasil tampil sederhana sebagai daftar bab dan subbab yang rapi.
4. User hanya menyentuh butir yang Hakim tandai ragu atau curiga, satu ketukan per butir (terima atau perbaiki).
5. Lalu unduh naskah dengan label yang benar.
6. Tidak ada pilihan model, tidak ada istilah teknis, tidak ada token yang membingungkan.

Prinsip lain yang sudah terkunci dan berlaku di sini: naskah user tidak diubah tanpa persetujuan, hasil pratinjau dulu sebelum diterapkan (seperti Revisi AI yang sudah ada), dan Bab IV tetap privat dari pembimbing sampai user sengaja mengekspornya.

---

## 1. Alur layar per layar

Lima layar saja. Tidak ada layar tambahan, tidak ada pengaturan, tidak ada menu tersembunyi.

### Layar 1 — Unggah

Satu halaman, satu kotak unggah, satu tombol.

Teks tampil:

> **Periksa Struktur Naskah**
>
> Unggah naskah skripsi Anda (DOCX atau PDF). Sistem akan membaca susunan bab, subbab, dan paragrafnya.
>
> [Pilih berkas]
>
> Berkas: contoh-skripsi.docx
>
> [Periksa Naskah]

Yang tidak ada di layar ini: pilihan model, pilihan paket pemetaan, kolom pengaturan, istilah Jev, Hakim, stitch, gelombang, confidence, atau token. Bila berkas bukan DOCX/PDF, pesannya: "Berkas ini belum bisa diperiksa. Silakan unggah DOCX atau PDF."

Batas yang ditampilkan jujur: ukuran berkas mengikuti kuota paket user yang sudah ada di EduAi (Gratis 30 MB), bukan batas baru. Tidak ada batas jumlah halaman yang ditulis di layar, karena belum teruji di naskah sangat besar.

### Layar 2 — Proses

Sesudah tombol ditekan, layar berubah menjadi satu halaman tunggu.

Teks tampil:

> **Pemeriksaan sedang berlangsung.**
>
> Ini biasanya 1 sampai 2 menit. Anda boleh meninggalkan halaman ini, pemeriksaan tetap jalan.
>
> [gambar putar sederhana]
>
> Tahap: Membaca susunan bab...

Kata "Tahap" hanya menampilkan tiga kata yang dipahami user: "Membaca susunan bab...", "Memeriksa bagian yang meragukan...", "Merapikan hasil...". Tidak ada hitungan panggilan, tidak ada persentase palsu, tidak ada log teknis. Bila proses lewat dari 5 menit, teks berubah menjadi: "Naskah Anda agak besar, mohon tunggu sebentar lagi." Bila proses gagal, layar tidak menampilkan kode galat; lihat bagian 4.

Tombol "Batalkan" ada, dan membatalkan berarti berhenti dan tidak ada biaya yang jalan terus. (Syarat teknis: pembatalan harus benar-benar menghentikan antrean, bukan hanya menutup layar. Ini masuk daftar yang harus diuji sebelum produksi.)

### Layar 3 — Hasil

Daftar bab dan subbab yang rapi, seperti daftar isi. Tidak ada angka goyang, tidak ada skor, tidak ada label teknis.

Contoh tampil:

> **Struktur Naskah Anda**
>
> BAB I PENDAHULUAN
>
> &nbsp;&nbsp;&nbsp;&nbsp;1.1 Latar Belakang
>
> &nbsp;&nbsp;&nbsp;&nbsp;1.2 Rumusan Masalah
>
> &nbsp;&nbsp;&nbsp;&nbsp;1.3 Tujuan Penelitian
>
> BAB II TINJAUAN PUSTAKA
>
> &nbsp;&nbsp;&nbsp;&nbsp;2.1 Pemasaran Digital
>
> ...
>
> [Unduh Naskah Berlabel] &nbsp; [Periksa 3 Bagian yang Meragukan]

Yang ditampilkan hanya yang sistem yakini. Paragraf tidak ditampilkan sebagai daftar panjang di layar ini; paragraf hanya dipakai di dalam berkas unduhan. Alasannya: batas paragraf adalah bagian yang paling bergoyang antar run (fid=81 paragraf 166 sampai 173 dalam 3 run v7), jadi menampilkan semuanya di layar hanya menambah keraguan user.

Bila tidak ada satu pun butir ragu atau curiga, tombol kedua tidak ada. Layar hanya berisi daftar dan tombol unduh. Ini keadaan yang normal dan diharapkan pada naskah rapi: fid=81 di v7 memberi 0 curiga dan 0 ragu.

### Layar 4 — Periksa butir ragu (hanya bila ada)

Layar ini hanya muncul bila Hakim menemukan butir ragu atau curiga. Satu butir per halaman, bukan daftar panjang. User mengetuk satu pilihan, lalu lanjut ke butir berikutnya.

Contoh satu butir:

> **Bagian 2 dari 3**
>
> "1.1 LATAR BELAKANG Indonesia merupakan salah satu negara..."
>
> Sistem membaca bagian ini sebagai judul subbab, tapi kalimatnya ikut menempel. Bagaimana menurut Anda?
>
> [Ya, ini judul subbab] &nbsp; [Bukan, ini isi paragraf]
>
> [Lewati dulu]

Aturan tampilan per butir:

- Tampilkan teks barisnya apa adanya, supaya user mengenali naskahnya sendiri.
- Pilihan memakai kata user, bukan kata sistem: "Ya, ini judul subbab" / "Bukan, ini isi paragraf" / "Ini judul bab". Tidak ada pilihan "bab/subbab/paragraf/biasa".
- "Lewati dulu" selalu ada. Butir yang dilewati tidak menghalangi unduhan; sistem memakai keputusan terbaiknya sendiri dan menandai butir itu di berkas unduhan sebagai "belum diperiksa", bukan memaksa user.
- Sesudah butir terakhir, layar kembali ke Layar 3 dengan tulisan: "Terima kasih, 3 bagian sudah Anda periksa."

### Layar 5 — Unduh

Bukan layar baru, melainkan hasil akhir di Layar 3: tombol "Unduh Naskah Berlabel" mengunduh DOCX dengan label bab/subbab/paragraf yang sudah diterapkan sebagai heading dan penanda. Sebelum unduhan dimulai, satu kalimat konfirmasi:

> "Naskah asli Anda tidak diubah. Berkas ini adalah salinan berlabel."

Bila user sudah memeriksa butir ragu, berkas unduhan memakai keputusan user untuk butir itu. Bila user melewati butir, berkas memakai keputusan sistem dan butir itu dicatat di satu halaman ringkasan di akhir berkas ("Bagian yang belum diperiksa"), bukan sebagai galat.

---

## 2. Kapan user diganggu dan kapan tidak

### Ambang yang sudah ada

Hakim v2 memakai ambang ragu 0,7 (selaras dokumen resmi TypeSafe: nilai 0,3 sampai 0,7 diserahkan ke manusia). Yang di bawah 0,7 tidak pernah sampai ke user; sistem memutuskan sendiri dan mencatatnya di log. Yang di atas 0,7 dan lolos audit kode menjadi "sepakat" dan juga tidak sampai ke user.

Hanya dua kelompok yang sampai ke user:

- **Ragu**: Jev tidak yakin, perlu satu ketukan user.
- **Curiga**: audit kode menemukan pola yang hampir pasti salah (mis. sitasi yang terlabel judul, penomoran loncat), perlu satu ketukan user.

### Berapa banyak butir yang wajar

Angka live v7 (rata-rata 3 run):

| Naskah | Ragu | Curiga | Total butir user |
|---|---|---|---|
| fid=81 (kontrol, rapi) | 0 | 0 | 0 |
| fid=115 (PDF pecah per huruf) | 2 | 3 | 5 |
| fid=112 (kualitatif) | 4 | 4 | 8 |
| WULAN-1 (paling lemah) | 14 | 1 | 15 |

Kesimpulan: naskah rapi memberi 0 butir, naskah sulit memberi 5 sampai 15 butir. Satu ketukan per butir berarti naskah tersulit pun selesai dalam 1 sampai 2 menit. Itu masih wajar.

### Bila butir ragu terlalu banyak

Batas yang ditetapkan di rancangan ini: **maksimal 20 butir per naskah** yang ditampilkan ke user. Bila Hakim menemukan lebih dari 20:

1. Butir diurutkan menurut dampak: judul BAB dulu, lalu subbab, lalu paragraf. (Judul yang salah merusak seluruh daftar isi; satu batas paragraf yang salah hanya merusak satu tempat.)
2. Butir dengan pola yang sama dikelompokkan menjadi satu pertanyaan. Contoh: 30 subbab berekor kalimat yang sama polanya ditanyakan sekali sebagai: "Beberapa judul subbab di naskah ini diikuti kalimat. Pisahkan semuanya?" dengan pilihan Ya / Tidak / Periksa satu per satu. Ini memakai temuan v7 bahwa WULAN-1 punya 30 pisahan ekor subbab dengan pola yang sama.
3. Sisanya tidak ditampilkan dan tidak diblokir: sistem memakai keputusan terbaiknya, mencatatnya di ringkasan akhir berkas, dan user tetap bisa mengunduh.
4. Bila total butir melebihi 20, layar hasil menambahkan satu kalimat jujur: "Naskah ini punya banyak bagian yang meragukan. 20 bagian terpenting sudah Anda periksa, sisanya memakai keputusan sistem." Tidak ada angka teknis, tidak ada istilah ambang.

Yang tidak boleh terjadi: user dipaksa memeriksa 50 butir sebelum bisa mengunduh. Unduhan tidak pernah dikunci oleh butir yang belum diperiksa.

---

## 3. Mekanisme biaya yang tidak membingungkan user

### Fakta biaya (terukur, bukan karangan)

Per naskah, hasil live v7:

| Naskah | Panggilan Jev | Waktu |
|---|---|---|
| fid=112 | 40 | 26 detik |
| fid=115 | 36 | 22 detik |
| fid=81 | 7 | 6 detik |
| WULAN-1 | 7 | 5 detik |

Rata-rata 22,5 panggilan dan 15 detik per naskah. Rentang 7 sampai 42 panggilan. Harga rupiah per panggilan Jev belum diketahui (harga token TypeSafe belum diukur dalam rupiah), jadi rancangan ini tidak menulis angka rupiah apa pun.

### Aturan biaya untuk user

1. **User tidak pernah ditagih per panggilan.** Kata "panggilan", "token Jev", dan "biaya per run" tidak muncul di layar mana pun. User tidak bisa memahami dan tidak perlu memahami satuan itu.
2. **Keputusan Boss 10 Nov 2026: pengecekan naskah GRATIS untuk semua.** Pemeriksaan struktur naskah (peta Jev/Hakim) tidak dipotong token apa pun, berapa pun panggilan Jev di belakangnya. Opsi A dan Opsi B di atas DIBATALKAN oleh keputusan ini.
3. **Yang berbayar hanya naskah revisi dan naskah kolaborasi.** Bila user masuk ke Revisi AI atau Kolaborasi, aturan token yang sudah berlaku dipakai (1 Token Revisi per pemakaian AI, token kembali bila AI gagal). Batas gratis/berbayar ada di pintu masuk Revisi dan Kolaborasi, bukan di pintu pengecekan naskah.
4. **Di Layar 1 tidak ada baris biaya.** Tidak ada tulisan "gratis" dan tidak ada tawaran AddOn/UPGRADE di layar pengecekan.
5. **Periksa ulang naskah yang sama tetap gratis dan memakai cache.** Cache peta (sidik teks + versi aturan) membuat naskah yang sama dan belum berubah langsung memakai hasil lama tanpa panggilan Jev baru. Ini juga alasan cache antar proses masuk rencana skala v8.

### Yang tidak ditampilkan

Tidak ada penghitung "sisa 26 panggilan", tidak ada "biaya run ini Rp...", tidak ada riwayat panggilan Jev. User hanya melihat saldo Token Revisi yang sudah ada di EduAi.

---

## 4. Bila naskah bermasalah

Setiap masalah diberi satu pesan sederhana dan satu jalan keluar. Tidak ada kode galat, tidak ada istilah teknis.

| Keadaan naskah | Pesan ke user | Jalan keluar |
|---|---|---|
| Tidak ada heading sama sekali (semua 5 naskah Uji Buku seperti ini: "Bab 1" ditulis sebagai teks biasa) | "Naskah ini belum punya penanda bab. Sistem tetap bisa memeriksa susunan dari teksnya, tapi hasilnya perlu Anda periksa lebih banyak." | Proses tetap jalan; butir ragu bertambah, user memeriksa seperti biasa. Tidak ditolak. |
| PDF pecah per huruf (fid=115: 5.240 baris satu huruf) | "Naskah ini hasil pindaian yang hurufnya terpisah. Sistem akan merapikannya dulu, hasilnya mungkin tidak sesempurna naskah ketikan." | Proses tetap jalan dengan segmentasi pasca-stitch v6; baris yang tidak bisa dirapikan tanpa mengarang dibiarkan apa adanya dan ditandai di ringkasan. |
| Bahasa Inggris atau campuran | "Naskah ini sebagian berbahasa Inggris. Sistem tetap memeriksa, tapi bagian berbahasa Inggris masuk daftar periksa Anda." | Baris non-Indonesia masuk antrean ragu untuk manusia, tidak dipaksa label oleh Jev. |
| Naskah kosong, rusak, atau hanya gambar | "Berkas ini tidak bisa dibaca. Silakan unggah DOCX atau PDF yang berisi teks." | Ditolak dengan sopan sebelum token dipotong. Token tidak terpakai. |
| Naskah sangat besar (di atas batas yang diuji) | "Naskah ini besar, pemeriksaannya dibagi menjadi beberapa bagian dan memakan waktu lebih lama." | Proses dibagi per bagian (gelombang yang sudah ada), bukan ditolak. Batas besar yang pasti belum teruji; jangan tulis angka halaman di layar sebelum diuji. |
| Jev mati / 503 di tengah proses | "Sistem pemeriksa sedang sibuk. Naskah Anda tersimpan, silakan coba lagi sebentar lagi." | Token kembali, naskah tersimpan, user bisa coba lagi tanpa unggah ulang. |

Prinsip umum: **tolak hanya bila benar-benar tidak bisa dibaca; selain itu proses tetap jalan dan kejujuran dipindah ke ringkasan.** User tidak pernah melihat kata "503", "stitch", "goyang", "confidence", atau "paragraf 157".

---

## 5. Privasi dan kepemilikan

1. **Naskah asli tidak pernah diubah.** Unggahan disimpan apa adanya. Hasil pemetaan adalah salinan berlabel yang terpisah. Kalimat ini tertulis di Layar 1 dan di konfirmasi unduhan.
2. **Pratinjau dulu, terapkan sesudah setuju.** Seperti Revisi AI yang sudah ada: hasil tampil dulu di layar (daftar bab/subbab), user memeriksa butir ragu, baru unduh. Tidak ada perubahan yang diterapkan diam-diam ke berkas user.
3. **Bab IV privat.** Prinsip yang sudah terkunci: Bab IV adalah "Olah Data dan Narasi", privat dari pembimbing sampai user sengaja mengekspornya ke naskah. Dalam alur ini berarti: hasil pemetaan Bab IV hanya terlihat oleh user pemilik naskah, tidak muncul di tampilan pembimbing, tidak ikut terkirim dalam notifikasi, dan tidak ikut dalam berkas yang dibagikan ke pembimbing kecuali user menekan "Ekspor ke naskah" secara sadar.
4. **Tidak ada yang dikirim ke pihak lain.** Naskah user hanya dipakai untuk pemetaan naskah itu sendiri. Tidak dipakai untuk melatih model, tidak dibagikan ke user lain, tidak tampil di contoh. (Ini perlu ditulis di halaman bantuan, bukan janji teknis yang tidak bisa diverifikasi user.)
5. **Hapus berarti hapus.** Bila user menghapus naskah dari EduAi, peta dan cache-nya ikut terhapus. Cache peta (rencana v8) memakai sidik teks, bukan salinan naskah, supaya penghapusan naskah benar-benar menghilangkan isinya.
6. **Pembimbing hanya melihat yang user izinkan.** Sama seperti Revisi AI: pembimbing tidak melihat antrean ragu user, tidak melihat skor Hakim, tidak melihat naskah sebelum user mengekspornya.

---

## 6. Risiko jujur — di mana alur ini masih bisa membingungkan user

1. **Belum ada uji user nyata.** Seluruh rancangan ini dibangun dari angka live dan dugaan, bukan dari user sungguhan yang mencoba. Yang paling berisiko: apakah user memahami pertanyaan satu butir ("Ya, ini judul subbab" vs "Bukan, ini isi paragraf") tanpa penjelasan tambahan. Ini hanya bisa dijawab dengan uji 3 sampai 5 user nyata sebelum produksi.
2. **Butir ragu 15 di naskah tersulit.** WULAN-1 memberi 15 butir. Satu ketukan per butir masih wajar, tapi bila user tidak memahami satu butir pun, 15 butir terasa seperti ujian. Pengelompokan per pola (bagian 2) adalah penahan pertama; bila pengelompokan gagal, batas 20 butir adalah penahan kedua.
3. **Paragraf yang bergoyang tidak terlihat user, tapi terasa di hasil.** Batas paragraf bergoyang 166 sampai 173 antar run di fid=81. User tidak melihat goyangnya, tapi bila mengunduh dua kali di hari berbeda dan isinya sedikit berbeda, kepercayaan hilang. Penahannya: cache peta membuat unduhan ulang naskah yang sama memberi hasil yang sama persis, selama aturan tidak berubah.
4. **Pesan "naskah belum punya penanda bab" bisa dibaca sebagai tuduhan.** User yang naskahnya ditulis sebagai teks biasa bisa merasa disalahkan. Kalimatnya harus diuji ke user nyata; alternatif yang lebih lembut: "Sistem membaca susunan dari teks naskah Anda."
5. **Biaya per naskah SUDAH diputuskan Boss 10 Nov 2026: pengecekan gratis untuk semua, berbayar hanya bila masuk Revisi dan Kolaborasi.** Jangan tulis angka apa pun di layar pengecekan.
6. **Pembatalan di tengah proses belum teruji.** Tombol "Batalkan" di Layar 2 menjanjikan proses berhenti. Bila di belakang antrean tetap jalan dan token tetap terpotong, itu tagihan yang tidak jujur. Harus diuji sebelum produksi.
7. **Bahasa Inggris dan naskah campuran belum diuji live.** Perlakuan "masuk antrean ragu" adalah rencana, bukan perilaku yang sudah terukur. Naskah Inggris nyata belum pernah dipetakan.
8. **Satu tombol berarti satu harapan.** User menekan satu tombol dan berharap selesai. Bila di belakang ternyata butuh 3 run dan 2 menit, layar tunggu harus jujur soal waktu ("biasanya 1 sampai 2 menit"), bukan janji "sebentar" yang tidak terukur.

## Yang masih kurang sebelum alur ini bisa dibangun

1. Keputusan Boss: Opsi A atau Opsi B untuk biaya per naskah (bagian 3).
2. Uji user nyata 3 sampai 5 orang dengan naskah sendiri, sebelum kode layar ditulis.
3. Uji pembatalan, uji unduh ulang (cache memberi hasil sama), uji naskah Inggris.
4. Label kebenaran dasar untuk sengketa paragraf antar-run v7 (butuh Gas ~180 panggilan Jev) supaya keputusan "paragraf" yang tampil di unduhan punya wasit.
5. Gerbang 3-naskah live (butuh Gas ~166 panggilan Jev) supaya perubahan aturan sesudah alur ini dibangun tidak merusak hasil diam-diam.
6. Keputusan model 1.13 ke 1.14 sebelum pensiun 1.13 sekitar 13 Desember 2026 (vonis saat ini berbalik: di 21 baris sengketa fid=81, 1.13 benar 8/21, 1.14 benar 13/21 menurut label Wulan commit `ba62c2c`; menunggu Boss memeriksa 6 baris keyakinan sedang).
