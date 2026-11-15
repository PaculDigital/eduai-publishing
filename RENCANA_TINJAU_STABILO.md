# RENCANA TINJAU STABILO: Halaman Tinjau Tanpa Teks Naskah

Status: **DIBANGUN 15 Nov 2026 15:17 WIB, DITAMBAH daftar pilihan revisi
16:50 WIB, BELUM push/merge/deploy**.
Dokumen diskusi Boss dan Wulan, 15 Nov 2026 13:11-14:50 WIB.
Branch `agen/wulan/tinjau-sidebar`, commit `6e9acc2` + `289b036`
(dari `32c4269`) + `04ff0dd` (daftar pilihan: perintah kosong/luas
menjadi 5 pilihan per round, terima semua/pilih/tulis sendiri; tiap
butir diterima 1 token, pembuatan daftar gratis; yang sudah dipilih
disaring keras dari round berikutnya) + `ba864e0` (sinkron AI: format
Asisten disamakan dengan Periksa, jangkar kutipan di revisi) +
`b1bea42` (penggalan penasaran di layar pilihan + verifikasi jangkar:
kutipan/bagian karangan dibuang sebelum tampil). Bukti: 120
uji sidebar lulus, suite lama 508 + 58 + 9 + 23 + 30 lulus. TIDAK dibangun: usul alamat
LLM inline (versi minimal saja), lompat otomatis ke bagian di dalam
editor OnlyOffice, uji browser live, simpan butir yang ditolak.
Sifat: **memperbaiki kode yang sudah ada agar sempurna, bukan bikin baru**
(perintah Boss 14:10 WIB). Satu mesin inti, fitur jadi lapisan kecil.

## 1. Masalah

Halaman tinjau hari ini menampilkan naskah sebagai teks polos
(`#isi-{bk.id}`, dimuat lewat JS sebagai `textContent`).
Itu menyesatkan: pembimbing melihatnya dan bingung, kok hasilnya seperti ini?
Teks polos itu tidak presisi (tanpa format, tabel, gambar utuh, nomor halaman),
padahal pembimbing harus melihat naskah apa adanya, sama seperti mahasiswa.

Keputusan Boss 00:07 WIB (render berformat di halaman tinjau, opsi 2)
**digantikan oleh rancangan ini**: tidak ada render sama sekali.
Naskah hanya dilihat di OnlyOffice. Halaman tinjau hanya berisi catatan.

## 2. Keputusan Boss (dirangkum dari diskusi)

1. Halaman tinjau **TIDAK BOLEH berisi teks naskah apa pun**.
2. Pembimbing melihat naskah yang **SAMA** dengan mahasiswa, lewat tautan
   dari mahasiswa, dengan framework OnlyOffice, **tanpa mendaftar**.
3. Penanda seperti **stabilo** di naskah; pembimbing menulis keterangan
   di halaman tinjau. Sederhana, kedua belah pihak paham.
4. **Peta Jev adalah alamatnya.** Tiap tandaan menempel di Bab / Sub-bab /
   nomor paragraf yang sudah diperiksa Hakim. LLM membantu saat pembimbing
   menjelaskan dengan kata-kata sendiri, bukan kutipan persis.
5. Dua jenis catatan dalam satu daftar yang sama (lihat §4).
6. Mahasiswa **klik revisi, langsung anchoring** ke bagian yang dimaksud.
7. Revisi AI: kena charge token, AI memperbaiki **HANYA area itu saja
   dengan bertetangga (±1)** agar tetap natural.
8. **1 dompet per id.** Tidak ada dompet pembimbing vs mahasiswa.
   Meninjau lewat tautan gratis tanpa daftar; wajib daftar HANYA bila mau
   pakai AI, karena AI menagih ke dompet id itu.
9. Kalimat legenda: **"Tidak tercetak di naskah Asli (hanya penanda revisi)"**
   (sudah diterapkan, commit `32c4269`, branch
   `agen/wulan/selaraskan-pembimbing-member`).

## 3. Mekanisme sederhana

### Alur pembimbing (tanpa daftar)

1. Mahasiswa kirim tautan (7 atau 30 hari, bisa dicabut).
2. Pembimbing klik tautan, isi identitas sekali (email atau nomor HP).
3. Pembimbing membuka naskah asli di OnlyOffice, mode baca
   (lihat §6). Itulah naskahnya, persis seperti yang dilihat mahasiswa.
4. Pembimbing kembali ke halaman tinjau, menulis catatan (lihat §4).
5. Pembimbing TIDAK BISA mengubah naskah. Hanya baca dan memberi catatan.

### Alur mahasiswa

1. Mahasiswa melihat daftar catatan, tiap catatan membawa alamat Jev-nya
   (Bab / Sub-bab / Paragraf, atau satu Sub-bab utuh).
2. Mahasiswa **klik catatan, langsung mendarat** di bagian yang dimaksud
   di OnlyOffice. Tidak perlu mencari lagi.
3. Mahasiswa memperbaiki sendiri (manual, gratis), atau lewat AI
   (1 token, hanya area itu + tetangga ±1, lihat §5).
4. Mahasiswa menandai selesai. Pembimbing bisa meminta lagi bila belum
   benar (tombol aktifkan, sudah ada).

### Kenapa stabilo di OnlyOffice tidak bisa bertahan

Komentar pembimbing di dalam OnlyOffice **tidak tersimpan**: simpanan
pembimbing diblokir server (terbukti 403, 03Okt26), jadi coretannya hilang
begitu tab ditutup. Karena itu stabilo yang bertahan adalah **kutipan
persis + alamat Jev** di dalam catatan, yang bisa dicari kedua belah pihak
di OnlyOffice (pencarian kata) dan diverifikasi mesin.

## 4. Dua jenis catatan, satu alamat

Keduanya hidup dalam satu daftar catatan di halaman tinjau.
Tiap catatan membawa: alamat Jev, jenis (Tandaan / Perintah), isi, status
(perlu ditinjau / sudah oke), dan riwayat balasan.

### (a) Tandaan: menunjuk bagian persis

- Pembimbing menyalin kata persis dari naskah (di OnlyOffice, salin
  diizinkan), menempelnya di form, lalu menulis keterangan.
- Server memeriksa kata itu memang ada di naskah (mesin yang sudah ada,
  `cari_bagian.py` LAPIS 1 = teks asli). Bila tidak ditemukan, catatan
  tetap masuk **tanpa sorotan palsu**, jujur, tidak menebak.
- Alamat: Bab / Sub-bab / nomor paragraf.

### (b) Perintah: untuk satu bagian utuh

- Pembimbing memilih Bab / Sub-bab dari **daftar judul saja**
  (diambil dari peta Jev, tanpa teks naskah), lalu menulis perintahnya.
- Contoh: "tambahkan teori pemasaran dan kutipan artikelnya",
  "perbaiki sub bab 2.1".
- Alamat: satu Sub-bab utuh, atau posisi "sesudah 2.1" bila bagiannya
  belum ada (peta tahu urutan bagian).
- Perintah menambah teori dan kutipan artikel memakai mesin panen yang
  sudah ada (artikel nyata terverifikasi); mahasiswa yang menjalankan,
  manual atau AI.

### Bila pembimbing hanya menulis kata-kata

Pembimbing boleh menulis bebas tanpa memilih alamat dan tanpa kutipan
persis ("perbaiki bagian teori pemasaran"). LLM mengusulkan alamat dari
peta Jev, Hakim memeriksa alamat itu nyata (bagian ada, kutipan ada),
pembimbing mengetuk setuju. Tidak ada alamat yang dipasang diam-diam.

## 5. Revisi AI: hanya area itu + tetangga

- Mahasiswa yang memilih menjalankannya. Biaya **1 Token Revisi**,
  dipotong dari dompet mahasiswa (yang klik yang bayar, putusan C7).
  AI gagal memberi hasil, biaya kembali penuh (pagar yang sudah ada).
- AI memperbaiki **hanya area catatan itu + tetangga ±1** (satu bagian
  sebelum dan sesudah), supaya bahasa tetap nyambung dan natural.
- Prinsip tetangga ini **sudah ada di kode**: `periksa_hemat` (bagian
  berubah + tetangga ±1) dan Asisten ("1 bagian + tetangganya").
  Dipakai ulang, bukan mesin baru.

## 6. OnlyOffice mode baca (sudah ada, tidak diubah)

Rute `GET /tinjau/{token}/naskah-baca/{berkas_id}`
(`app/rute_pembimbing_ai.py:163`, putusan D7/D8, ACC Boss 03Okt26):

- Editor yang sama dengan mahasiswa, hanya mode beda: tulis mati
  (`permissions.edit=False`), komentar dan sorot hidup
  (`comment=True`, `review=True`), unduh, cetak, dan salin diizinkan.
- Berkas yang dibaca adalah **berkas milik mahasiswa langsung**
  (putusan D9, tidak disalin ke akun pembimbing).
  Token unduhnya token pemilik yang sama
  (`_token_berkas(fb.id, fb.user_id)` → `/oo/unduh/{tk}`),
  jadi OnlyOffice mengambil byte berkas yang sama persis.
  Kunci dokumen `baca{fb.id}v{...}` vs mahasiswa `e{fid}v{...}`:
  sesi terpisah, dokumen sama.
- Simpan diblokir di server (`/oo/simpan` hanya terima token pemilik,
  terbukti 403). Akses tanpa akun lewat "Kunci Tinjau" (ACC Boss 03Okt26):
  cookie httponly jalur `/oo/aset`, kedaluwarsa mengikuti token tinjau
  (sampai expired atau mahasiswa cabut).
- Halaman editor sudah punya tombol kembali ke `/tinjau/{token}`
  (`tinjau_baca.html`).

## 7. Dompet dan pendaftaran (sudah ada, tidak diubah)

- **1 dompet per id** (`SaldoToken.user_id`, `PemakaianAI.user_id`,
  `PembelianAddon.user_id` di `app/saldo.py`). Tidak ada dompet peran.
  Kode sudah menulisnya: "satu dompet, dua peran"
  (`app/rute_pembimbing_ai.py`).
- Pendaftaran terbuka (`POST /daftar`, `role='client'`).
  Pembimbing yang daftar jadi member biasa seperti mahasiswa.
- Tombol "Periksa dengan AI" tanpa akun dialihkan ke
  `/daftar?dari=/tinjau/{token}` (jawaban Boss: A).
  Asisten Pembimbing di `/kolaborasi` wajib login.
- Keputusan Boss 03Okt26 (verbatim di kode): "Pembimbing yang sah dapat
  kunci dari mahasiswa, sah melakukan baca dan komentar, tapi jika
  Pembimbing klik pakai Ai dia wajib daftar seperti mahasiswa."

## 8. Yang diubah di kode yang ada

Perbaiki, bukan baru. Tanpa berkas baru, tanpa endpoint baru,
tanpa tabel baru, tanpa mesin baru.

| Berkas | Perubahan |
|---|---|
| `app/templates/tinjau.html` | **Hapus** render teks naskah (`#isi-{bk.id}` dan pemuatan teks polos). Halaman hanya berisi: sambutan + form identitas, kepala (nama mahasiswa, sisa hari), tombol besar "Buka Naskah Asli", panel catatan (angka, legenda, kelompok per bab, form catatan baru dengan pemilih alamat: kutipan + daftar judul dari peta). Kalimat legenda baru sudah masuk (commit `32c4269`). |
| `app/rute_pembimbing.py` | Rute tinjau tidak lagi menyajikan teks naskah; menyajikan daftar judul bagian dari peta + daftar catatan. Tetap: penjaga privasi (hanya nama mahasiswa), identitas sekali, `tambah_catatan` (ditambah jenis Tandaan/Perintah + alamat), balasan, `aktifkan`, kaitkan. |
| `app/cari_bagian.py` | Pakai ulang LAPIS 1 (teks asli) untuk tandaan; tambah alamat struktur (satu bagian utuh / posisi "sesudah X") untuk perintah, dari peta Jev. |
| `app/pembimbing.py` | Pakai ulang: `daftar_catatan`, `rangkai`, `status_kunci`, `sisa_hari`. Tidak ada perubahan perilaku. |
| `app/rute_pembimbing_ai.py` | Tidak diubah: `naskah-baca` (OnlyOffice mode baca) dan `periksa-ai` (alihkan ke daftar bila belum login) sudah benar. |
| `app/pembimbing_ai.py`, `app/asisten.py` | Revisi AI dibatasi area catatan + tetangga ±1 (memakai pola hemat yang sudah ada). Biaya tetap 1 Token Revisi dari yang klik; kembali bila gagal. |
| `app/onlyoffice.py` | Tidak diubah: `konfigurasi_editor(mode_baca=True)` sudah benar. |

Catatan alamat: pakai ulang kolom yang sudah ada di catatan
(`teks_asli`, `section_id`, nomor paragraf). Bila jenis Tandaan/Perintah
tidak muat di kolom yang ada, itu diputuskan saat membangun, bukan
dengan menambah tabel baru.

## 9. Yang tetap

- Pembimbing hanya baca, tidak menyimpan, tidak menyentuh mesin revisi
  mahasiswa dan tidak mengubah naskah.
- Tautan 7 atau 30 hari, bisa dicabut mahasiswa kapan saja.
- Identitas diisi sekali; bila sudah diisi orang lain, tidak ditimpa.
- Catatan bisa dibalas (rantai), bisa diminta lagi (aktifkan).
- Privasi Bab IV tetap struktural: pembimbing hanya melihat berkas
  naskah; jendela Bab IV masuk lewat ekspor sadar mahasiswa.
- Pemeriksaan Jev/Hakim gratis; revisi AI berbayar 1 token.
- Semua teks tampil Bahasa Indonesia; tanpa em dash.

## 10. Yang masih terbuka (butuh keputusan Boss)

1. **Pendaratan tautan**: TERJAWAB Boss 15 Nov 2026 14:38 WIB: pakai
   sidebar saja, jangan bolak-balik. Tautan langsung buka OnlyOffice
   dengan sidebar catatan di sampingnya; halaman tinjau diganti sidebar
   (lihat §12).
2. Kolom jenis catatan bila tidak muat di kolom yang ada (lihat §8).

## 11. Uji sebelum Gas deploy

1. Pembimbing tanpa akun: klik tautan, isi identitas, buka naskah asli
   di OnlyOffice (tulis mati, komentar hidup), kembali ke halaman tinjau.
2. Pembimbing menulis tandaan (kutipan persis) dan perintah
   (pilih Sub-bab 2.1, "tambahkan teori pemasaran dan kutipan
   artikelnya"); keduanya muncul di daftar tanpa teks naskah.
3. Mahasiswa klik catatan, mendarat di bagian yang dimaksud di OnlyOffice.
4. Mahasiswa jalankan revisi AI pada satu catatan: 1 token terpotong
   dari dompet mahasiswa, perbaikan hanya area itu + tetangga ±1,
   bahasa tetap nyambung.
5. Pembimbing tanpa akun klik "Periksa dengan AI": dialihkan ke daftar.

## 12. Sidebar gantikan halaman tinjau (keputusan Boss 14:38 WIB)

Jangan bolak-balik. Halaman tinjau (render teks naskah) dihapus,
diganti sidebar di samping editor OnlyOffice. Tautan langsung buka
OnlyOffice dengan sidebar. Pembimbing menunjuk di naskah, menulis
catatan atau revisi di sidebar. Mudah bagi mahasiswa dan pembimbing.

### Isi sidebar

- Daftar Bab / Sub-bab dari **peta Jev** sebagai dropdown (hanya judul,
  tanpa teks naskah). Bila peta belum ada (mahasiswa belum tekan
  "Periksa Struktur"), dropdown memakai potongan bagian dari mesin yang
  sama (`state.petakan()`); tandaan dengan kutipan persis tetap jalan.
- Daftar catatan (alamat Jev + jenis + isi + status + balasan).
- Form catatan baru: kutipan persis (opsional) + pilih Bab/Sub-bab +
  tulis keterangan. LLM mengusulkan alamat bila pembimbing hanya menulis
  kata-kata; Hakim memeriksa alamat itu nyata; pembimbing mengetuk setuju.
- Tombol **Asisten AI** (lihat di bawah).

### Cara membangun (perbaiki, bukan baru)

- Pola panel geser sudah ada di editor mahasiswa (`editor.html`
  `#panel-ai`, geser dari kanan, 404px). Dipakai ulang untuk sidebar
  pembimbing di `tinjau_baca.html` (hari ini halaman itu hanya berisi
  kepala "Mode baca" + tombol kembali + editor, tanpa sidebar apa pun).
- Sidebar memakai endpoint catatan yang **sudah ada**
  (`tambah_catatan`, `daftar_catatan`, `aktifkan`, `periksa-ai`,
  `asisten`). Yang dihapus hanya render teks naskah di `tinjau.html`;
  rutenya tetap (identitas sekali, validasi token, penjaga privasi).
- Mahasiswa melihat sidebar yang sama di editornya, isinya daftar
  catatan yang sama. Hari ini editor mahasiswa sudah punya panel AI
  dengan kotak "Komentar pembimbing" (tempel manual, satu per baris);
  dengan rancangan ini tempelan manual diganti klik catatan.

### Asisten AI: memperbaiki revisi pembimbing, memberi catatan untuk mahasiswa

Dibaca ulang dari kode, 15 Nov 2026 14:38 WIB. Ada **dua** AI pembimbing,
keduanya menulis ke daftar catatan yang **sama** dengan catatan tulisan
tangan pembimbing (satu kanal untuk mahasiswa, putusan C5).

**1. Asisten Pembimbing** (`app/asisten.py`, endpoint
`POST /kolaborasi/asisten/{bimbingan_id}`, wajib login).
Pembimbing yang sudah daftar menekannya dari `/kolaborasi`.

- Membaca naskah utama (`naskah_bimbingan`, mesin baca yang sudah ada).
- Biaya: yang klik yang bayar (C7), 1 Token Revisi dari dompet
  pembimbing, atau trial gratis 1x seumur akun dulu; gagal, biaya kembali
  (trial pun pulih, perbaikan F1).
- Hemat token: mengirim **1 bagian + tetangganya**, bukan naskah utuh
  (`_siapkan_kirim`, giliran berputar bab 1, bab 2, dst, memakai
  `state.petakan()` + `konteks.bangun_prompt()` yang sudah ada).
  Pagar: permintaan menyeluruh ("ubah alur") mengirim naskah utuh
  (`_boleh_potong` memakai `ai._boleh_konteks` yang sudah ada).
- AI menjawab JSON `{"usulan": [{"bab", "kutipan", "catatan"}]}`.
  Aturan jawaban: "kutipan" 8-15 kata persis dari draf (jangkar stabilo),
  "catatan" 1-2 kalimat hangat, dilarang mengarang data, angka, rujukan.
- `simpan_usulan` menyimpan tiap usulan sebagai **catatan pembimbing
  sungguhan** (`dari_pembimbing=True`, warna kuning, sisi pembimbing).
  Kutipan diverifikasi ke naskah; tidak ditemukan, `teks_asli`
  dikosongkan (catatan tetap masuk tanpa sorotan palsu).

**2. Periksa dengan AI** (`app/pembimbing_ai.py::periksa`, endpoint
`POST /tinjau/{token}/periksa-ai`, jalan di latar).
Pembimbing menekannya dari halaman tinjau (atau sidebar nanti).

- Gerbang pintu khusus (`boleh_pakai`): paket gratis **dibuka** untuk
  pintu tinjau naskah orang (putusan Boss 03Okt26); jalur normal naskah
  sendiri tetap menolak gratis tanpa transaksi (§4.10 tidak dilemahkan).
  Tanpa akun, dialihkan ke daftar.
- Potong 1 token **sesudah** naskah terbaca (jangan potong bila naskah
  kosong). Panggil model satu pintu (dengan fallback).
- Hasil diurai (`urai_catatan`) lalu ditulis sebagai catatan lewat mesin
  catatan yang sama (`P.catat(..., dari_pembimbing=False)`, sumber mesin,
  bukan orang), lengkap dengan judul bagian dan kutipan persis.
- Gagal di langkah mana pun, kuota **dikembalikan** + sebab jujur.

### Alur revisi mahasiswa di sidebar

1. Mahasiswa klik catatan di sidebar: alamat Jev (Bab/Sub-bab/Paragraf)
   + kutipan ditunjukkan; mahasiswa melompat lewat daftar isi OnlyOffice
   dan pencarian kata ke bagian itu.
2. Mahasiswa memperbaiki manual (gratis), atau tekan "Revisi dengan AI":
   1 token dari dompet mahasiswa, AI memperbaiki hanya area itu +
   tetangga ±1, lalu catatan ditandai selesai.
3. Pembimbing melihat status di sidebar yang sama dan bisa meminta lagi
   bila belum benar.

### Dua Asisten AI menurut peran (keputusan Boss 14:44 WIB)

Yang satu untuk mahasiswa, yang satu untuk pembimbing, tergantung peran.

- **Mahasiswa**: bila ingin memperbaiki revisi dari pembimbing dengan AI,
  klik Asisten AI di kolom sidebar. AI memperbaiki area itu + tetangga
  ±1, dan **status revisi itu otomatis menjadi selesai**.
- **Pembimbing**: klik Asisten AI untuk memberi revisi atau catatan agar
  diperbaiki mahasiswa (Asisten Pembimbing atau Periksa dengan AI,
  lihat di atas).
- **Biaya**: semuanya kena charge **1 token**, baik mahasiswa maupun
  pembimbing. Pembimbing yang belum mendaftar **otomatis diarahkan untuk
  mendaftar** (wajib mendaftar untuk dapat dompet token); tombol Asisten
  AI di jalur token mengarah ke `/daftar`, bukan ke masuk.
