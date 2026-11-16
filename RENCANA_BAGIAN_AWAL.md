# Rencana: Lengkapi Bagian Awal (front matter skripsi)

Catatan Wulan, 14 November 2026, dari diskusi dengan Boss. STATUS: PERBAIKAN PENCARI BAB I + TAMPILAN KEGAGALAN SELESAI DIBANGUN + DIUJI (Gas Bos 16 Nov 2026 18:09 WIB, branch agen/wulan/bagian-awal-cari-bab1, BELUM merge/deploy/push, menunggu Gas + token). Riwayat: DIBANGUN + DEPLOYED main d6e6e44 (15:11 WIB); uji live 16 Nov 2026 16:01 WIB (file 126, akun uji, 10 token) menemukan 4 cacat besar; perbaikan 4 cacat + layar sederhana DIBANGUN (branch agen/wulan/bagian-awal-perbaiki) lalu DEPLOYED main 6014ee9 (image eduai-app:20261116_103319-sot, 17:41 WIB, smoke fid=81 lulus). Uji live ulang 16 Nov 2026 18:04 WIB: layar sederhana LULUS (tepat 6 item), tapi Perbarui GAGAL dalam 1 detik, galat 'Bab I tidak ditemukan di naskah', sementara layar terus menampilkan 'sedang ditempel' 16 menit tanpa menunjukkan kegagalan; token tidak terpotong (40/40), dokumen tidak berubah. Sebab terlacak + direproduksi: pencari Bab I gagal di berkas 126 yang tercemar (entri Daftar Isi berjudul huruf campuran tidak terhitung, judul badan 'BAB 1' telanjang terjebak di dalam blok Daftar Isi sehingga aturan ulang tidak menyala). Perbaikan ini: (1) pencari: baris telanjang 'BAB n' di dalam blok Daftar Isi adalah judul badan HANYA bila blok itu sudah berisi entri berjudul (aturan halus, supaya entri Daftar Isi buatan aplikasi yang telanjang tetap dihitung dan Perbarui tidak rusak); (2) tampilan: pekerjaan gagal kini tampil di halaman + di polling JS (pesan galat + 'Token kembali' + jalan coba lagi), dan muat ulang sesudah selesai membuang ?pesan= yang basi. Bukti: reproduksi berkas 126 sebelum None, sesudah 619 ('BAB 1'); penyembuhan di salinan berkas 126: paragraf 1815 jadi 1198, KATA PENGANTAR 7 jadi 1, badan 1196 paragraf utuh sama persis; tes bagian_awal 168 lulus 0 gagal (156 lama + 12 baru), suite lama semua lulus (pustaka 103, Jev/Hakim 522, sidebar 135, sederhana 36, rantai 40, member 30, ambang 58, antrean 9, latar 23). Batas jujur: judul badan berjudul huruf campuran di dalam blok daftar yang macet tetap gagal tertutup (aman, bukan potong salah). Masih perlu uji live sesudah deploy: Perbarui file 126 (2 token akun uji), periksa duplikasi sembuh + penomoran + Daftar Isi + halaman abstrak.

## Keputusan desain (disepakati dalam diskusi 14 Nov 2026, 23:00-23:07 WIB)

1. **Bagian awal dibuat DUA TAHAP** (keputusan Boss 16 Nov 2026 13:58 WIB, menggantikan "dibuat terakhir sesudah Bab I-V"). Tahap proposal: sesudah Bab I-III selesai dan strukturnya terverifikasi, tombol muncul untuk ujian proposal skripsi. Tahap final: sesudah Bab V atau VI final, mahasiswa lanjut update lewat tombol "Perbarui Bagian Awal" untuk ujian skripsi. Alasan: daftar isi, daftar tabel, dan daftar gambar bergantung pada struktur akhir dan nomor halaman; lembar persetujuan butuh naskah selesai. Versi proposal adalah potret sementara yang diperbarui di tahap final. Abstrak (Indonesia) dan Abstract (Inggris) HANYA di tahap final (keputusan Boss 16 Nov 2026 13:59 WIB): bila naskah baru sampai Bab III, abstrak belum bisa ditulis, menunggu Bab IV, V atau VI selesai, karena abstrak merangkum hasil dan kesimpulan. Di tahap proposal abstrak tidak ditagih sebagai "belum lengkap"; halaman abstrak baru ditambahkan saat Perbarui di tahap final, sebagai template dengan kolom terisi (judul, nama) dan isi yang ditulis mahasiswa sendiri. Isi abstrak juga bisa dibuat dengan AI (keputusan Boss 16 Nov 2026 14:01 WIB): AI membaca naskah lalu menulis draf abstrak. Harga diputuskan Boss 16 Nov 2026 14:03 WIB, ditegaskan 14:04 WIB: HANYA ada abstrak lengkap, 6 token untuk Indonesia dan Inggris. Tidak ada pilihan abstrak kerangka sama sekali. AI menulis abstrak penuh kedua bahasa, bukan garis besar. Aturan pengembalian tetap berlaku: kembali bila AI gagal. Draf AI hanya usulan, mahasiswa memeriksa dan mengubahnya sebelum masuk ke bagian awal; jalur tulis sendiri tetap gratis.
2. **Tombol "Lengkapi Bagian Awal".** Satu klik, tapi tidak diam-diam: sistem tunjukkan dulu daftar cek (mana yang ada, mana yang kurang, mana yang tidak cocok). Daftar cek menandai bila judul di form berbeda dengan judul di Bab I, mahasiswa memilih yang benar. Mahasiswa menyetujui sebelum apa pun ditambah.
3. **Keadaan tombol:**
   - Bab I-III belum selesai: tombol TIDAK AKTIF, catatan "Selesaikan Bab I sampai III dulu, bagian awal untuk ujian proposal."
   - Bab I-III selesai tapi belum diperiksa: TIDAK AKTIF, catatan "Periksa Struktur dulu."
   - Bab I-III sudah diperiksa, bagian awal belum lengkap: AKTIF (untuk ujian proposal).
   - Bagian awal sudah ditempel: tombol berubah jadi "Perbarui Bagian Awal", tetap bisa dipakai sampai Bab V atau VI final untuk ujian skripsi.
4. **Teks mahasiswa tidak pernah ditimpa.** Kata pengantar, persembahan, pernyataan keaslian yang sudah ditulis mahasiswa dipertahankan apa adanya. Yang ditambah hanya yang kurang (dari template, kolom sudah terisi dari akun dan naskah). Yang salah ditawarkan perbaikannya, mahasiswa yang menyetujui.
5. **Daftar isi, daftar tabel, daftar gambar, daftar lampiran dibuat ulang dari peta Jev/Hakim yang sudah terverifikasi.** Daftar isi jangan diketik tangan. Daftar-daftar ini bertumbuh otomatis sesuai update (keputusan Boss 16 Nov 2026 14:15 WIB): sekali jalan Perbarui, keempat daftar dibuat ulang dari peta yang terverifikasi dan nomor halaman hasil render, mengikuti pertambahan bab dan halaman naskah, jadi rapi; mahasiswa tidak pernah mengetik ulang daftar.
6. **Nomor halaman daftar isi itu nyata**, dari hasil render dokumen (mesin hitung halaman yang sudah ada, WordCraft/OnlyOffice), bukan tebakan. Kalau isi berubah, daftar isi ditandai usang dan ada tombol "Perbarui Daftar Isi". Penomoran: bagian awal angka Romawi kecil, Bab I mulai halaman 1 Arab; penulis .docx memasang pemisah bagian dan memulai ulang penomoran.
7. **Urutan bagian awal ikut Pedoman Skripsi Prodi Manajemen FEB UPB Edisi Revisi 2025:** Sampul, Judul, Persetujuan, Pengesahan, Persembahan/Motto (opsional), Pernyataan Keaslian, Kata Pengantar, Daftar Isi, Daftar Tabel, Daftar Gambar, Daftar Lampiran, Abstract (Inggris), Abstrak (Indonesia) (keduanya hanya di tahap final, lihat keputusan 1). Halaman bagian awal memakai angka Romawi kecil (i, ii, ...).

8. **Harga** (keputusan Boss 16 Nov 2026 14:08 WIB): pembuatan bagian depan lengkap tanpa abstrak = 2 token; update lewat "Perbarui Bagian Awal" = 2 token juga; sudah termasuk Kata Pengantar lengkap. Abstrak terpisah 6 token. Karena sekali jalan kena 2 token, data form harus valid sebelum klik: yang diisi harus benar (yang kosong tetap boleh kosong dan tampil sebagai garis kosong, dilengkapi nanti lewat Perbarui). Layar sebelum tempel menampilkan kembali semua data untuk diperiksa sekali lagi (lihat keputusan form 5). Jalur tulis sendiri tetap gratis. Belum diputuskan: bila Kata Pengantar sudah ditulis mahasiswa sendiri, apakah tetap 2 token penuh; dan update ringan (hanya data + daftar isi, tanpa tulis ulang Kata Pengantar) apakah tetap 2 token.
9. **Dua versi Persetujuan** (catatan Wulan, diverifikasi ke Pedoman, 16 Nov 2026 14:08 WIB): Pedoman punya contoh Persetujuan Pembimbing Proposal (Lampiran 2) dan Persetujuan Pembimbing final (Lampiran 5) + Pengesahan Dewan Penguji (Lampiran 6). Sistem memakai template yang benar di tiap tahap, bukan satu template untuk keduanya.
10. **Kata kunci abstrak** (catatan Wulan, 16 Nov 2026 14:08 WIB): halaman abstrak butuh kata kunci (3-5 kata, dua bahasa). AI abstrak 6 token menyertakannya, atau mahasiswa mengisinya di form abstrak.

## Aturan kunci: tulisan mahasiswa tidak pernah hilang (disetujui Boss 16 Nov 2026 14:16 WIB)

Template tidak pernah menulis di atas tulisan mahasiswa. Template hanya membaca tulisan mahasiswa dan menampilkannya lagi.

1. **Baca dulu, tulis belakangan.** Setiap update membaca dulu bagian depan yang ada di naskah, lalu memisahkan tiga jenis isi: milik mahasiswa (Kata Pengantar, Persembahan, dan semua edit tangan di halaman mana pun) dipertahankan kata per kata dan tidak pernah dibuat ulang; data form (nama, NIM, judul, pembimbing, dan kawan-kawan) menang bila berubah; turunan (Daftar Isi, Daftar Tabel, Daftar Gambar, Daftar Lampiran, nomor halaman) selalu dibuat ulang dari peta Jev/Hakim.
2. **Sidik per halaman (SHA-256).** Kalau sidiknya sama dengan yang sistem buat, berarti tidak disentuh mahasiswa, boleh dibuat ulang. Kalau sidiknya beda, berarti mahasiswa mengubahnya, dipertahankan. Halaman yang dihapus mahasiswa ditawarkan untuk dikembalikan; halaman baru yang ditambahkan mahasiswa tidak disentuh sama sekali.
3. **Kata Pengantar yang tidak berubah tidak ditulis ulang AI**, dipertahankan apa adanya.
4. **Layar konfirmasi** sebelum update menampilkan tiga daftar: yang berubah, yang dipertahankan, dan yang dibuat ulang. Sesudah update ada struk bukti (mis. "Kata Pengantar kamu tetap utuh (sekian kata), Daftar Isi diperbarui").
5. **Jaring pengaman:** sebelum menulis, salinan teks mahasiswa disimpan di database, jadi kalau penulisan gagal, teksnya bisa dikembalikan.
6. Abstrak yang sudah diterima atau diubah mahasiswa juga menjadi tulisan mahasiswa: tidak dibuat ulang kecuali mahasiswa menekan tombol AI lagi (6 token).

## Keputusan desain form data vital (diskusi 16 Nov 2026 13:53-13:55 WIB)

Form sebelum tempel berisi: nama lengkap mahasiswa, NIM, program studi, fakultas, jenjang (S1), kota, tahun, nama pembimbing beserta gelar dan NIP, nama penguji I, nama penguji II, nama Ketua Program Studi beserta NIP, nama dekan, nama rektor beserta NIP, tanggal ujian/sidang.

1. Semua kolom BOLEH KOSONG. Kalau mahasiswa belum tahu atau belum paham, dia boleh mengosongkan. Yang kosong tetap tersimpan di database sebagai kosong, bukan ditolak.
2. Kolom kosong tampil sebagai garis kosong di halaman (bukan teks galat) dan ditandai "belum lengkap" di daftar cek.
3. Mahasiswa melengkapi nanti lewat tombol "Perbarui Bagian Awal", yang membuka form yang sama dengan data lama sudah terisi. Isi yang sudah diketahui, klik update, halaman depan ikut berubah.
4. Isi otomatis sebisa mungkin: nama dan gelar pembimbing diambil dari bimbingan kalau mahasiswa sudah mengundang pembimbing lewat EduAi. Nilai yang pernah diisi tersimpan di profil dan terisi otomatis di naskah berikut, mahasiswa tinggal memeriksa.
5. NIP dicek formatnya saja (18 angka) supaya salah ketik ketahuan. Tidak ada cara memeriksa NIP itu benar atau tidak dari sistem, jadi sebelum ditempel layar menampilkan kembali semua data untuk diperiksa sekali lagi.
6. Form dikelompokkan supaya tidak membingungkan: Tentang kamu, Pembimbing, Penguji, Pimpinan kampus. Satu kolom satu baris, dengan contoh di tiap kolom. Semua teks Bahasa Indonesia.
7. Penyimpanan dua tempat: per naskah (sumber kebenaran bagian awal naskah itu) dan profil (untuk isi otomatis naskah berikut).
8. **Verifikasi ulang** (keputusan Boss 16 Nov 2026 14:11 WIB): sebelum jalan berbayar, layar menampilkan kembali semua data dan mahasiswa WAJIB memeriksa ulang lalu menekan konfirmasi. Ini penjaga supaya 2 token tidak terbuang untuk data yang salah.

## Tiga kasus pengguna

- **Mulai dari nol:** tulis Bab I-III dulu (terpandu) untuk ujian proposal, bagian awal ditempel sesudah Bab I-III terverifikasi; update sampai Bab V atau VI final.
- **Naskah tanpa bagian awal:** sistem tawarkan buatkan dari template + peta terverifikasi.
- **Naskah dengan bagian awal belum komplit:** sistem tunjukkan yang kurang dan yang tidak cocok dengan isi sebenarnya, lalu tawarkan melengkapi.

## Tooltip tombol (tambahan Boss 16 Nov 2026 14:17 WIB, masuk build yang sama)

Tombol dilengkapi tooltip agar mahasiswa paham maksud dan kapan munculnya: menjelaskan maksud tombol (menempelkan bagian depan skripsi: sampul, judul, persetujuan, pengesahan, kata pengantar, daftar isi, daftar tabel, daftar gambar, daftar lampiran; abstrak hanya di tahap final) dan kapan muncul (sesudah Bab I-III selesai dan terverifikasi, untuk ujian proposal; update lanjut sampai Bab V atau VI final untuk ujian skripsi). Saat tombol TIDAK AKTIF, tooltip menjelaskan ALASANNYA (Bab I-III belum selesai, atau belum diperiksa lewat Periksa Struktur); tombol nonaktif tanpa penjelasan membingungkan mahasiswa. Tombol "Perbarui Bagian Awal" punya tooltip sendiri (memperbarui bagian depan mengikuti naskah, 2 token; tulisan mahasiswa dipertahankan). Semua teks tooltip Bahasa Indonesia; mengikuti pola TOOLTIP_JENIS di app/pembimbing.py. Tes memeriksa teks tooltip di tiap keadaan tombol (aktif, nonaktif karena Bab belum selesai, nonaktif karena belum diperiksa, mode Perbarui).

## Keadaan kode saat ini (diverifikasi Wulan 14 Nov 2026 23:07 WIB)

Mekanisme "Lengkapi Bagian Awal" untuk skripsi **BELUM ADA**. Yang sudah ada, terpisah-pisah:

- `app/standar_penulisan.py:101-102` — urutan bagian awal sudah tertulis.
- `app/state.py:35,229` — daftar isi/tabel/gambar/lampiran sudah dikenali sebagai bagian 'meta'.
- `app/konversi.py:314` — konverter mengenali PENGESAHAN, PERSETUJUAN, ORISINALITAS, PERNYATAAN.
- `app/cover.py:169` + `POST /buku/cover/lengkapi` — pola tombol "Lengkapi Sampul" untuk sampul buku, bisa ditiru polanya.
- `app/peta_halus.py:190` — peta bisa mendeteksi bab yang kurang dan melengkapi dari peran bab standar.
- Jev/Hakim saat ini justru MEMBUANG blok daftar isi (`buang_daftar_isi`, demosi blok daftar isi) karena dianggap gangguan saat pelabelan — kebalikan dari yang dibutuhkan di sini.

Jadi: bukan bangun dari nol, tinggal merangkai bagian yang sudah ada, memakai mesin yang sama.

## Prinsip yang mengikat (keputusan Boss 26 Okt 2026)

Satu mesin inti, fitur jadi lapisan kecil di atasnya, bukan mesin baru. Semua fitur membaca naskah yang sama. Cek sitasi memakai fungsi panen yang sudah ada (`app/pustaka.py`: Scopus, OpenAlex, CrossRef, Garuda, DOAJ + audit DOI), bukan bikin pencari baru. Menulis dari nol memakai Jev/Hakim yang sama per bagian, lewat revisi hemat.

## Yang masih terbuka (di luar rencana ini)

- Cek sitasi mahasiswa (ambil Daftar Pustaka, periksa satu-satu ke sumber panen) — fitur baru, belum disambung ke Jev/Hakim.
- Alur pilot (tombol "Periksa Struktur" + antrean admin) — mesin sudah live v18, alur pengguna belum ada.
- Antrean admin + dashboard pindah ke HP — ditunda sampai semua beres (Boss 14 Nov 21:55 WIB).
