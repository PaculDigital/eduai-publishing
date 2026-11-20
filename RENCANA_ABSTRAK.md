# Rencana Cek Abstrak — Fitur 4 dari 10 (Gas Boss 20 Nov 2026 20:23 WIB)

EduAi membantu mahasiswa menulis skripsi yang benar, dari nol atau dari
naskah sendiri. Fitur ini memeriksa abstrak mahasiswa, bukan membuatnya.

## Yang diperiksa
Abstrak (Indonesia) dan Abstract (Inggris) cocok dengan isi atau tidak
(masalah, metode, hasil, kesimpulan), panjangnya sesuai, spasinya 1.

## Yang SUDAH ADA (baca dulu, jangan buat baru)
- `app/bagian_awal.py`: `draf_abstrak` (AI, 1 panggil, hasil
  {id, en, kunci_id, kunci_en}), `urai_draf_abstrak`, `simpan_abstrak`,
  `muat_abstrak`, `hapus_abstrak`. Harga generator: 6 token
  (HARGA_ABSTRAK, keputusan Boss 16 Nov, dikonfirmasi ulang 20 Nov).
- `app/konsistensi.py` Bagian 2: `ekstrak_bagian_bab` (6 bagian dari
  peta Jev), `susun_prompt_bab`, `urai_jawaban_bab`,
  `langkah_berikut_bab`, `SAMBUNGAN_BAB`. Pola LLM yang dipakai ulang.
- `app/rute_bagian_awal.py`: SUDAH punya pola /v1/ mulai-latar +
  status (pekerja latar) untuk tempel/perbarui. Rute cek abstrak
  ditambahkan ke berkas ini, bukan berkas baru.
- `app/rute_konsistensi.py`: pola pekerja latar + gerbang sidik +
  simpan hasil di Setelan (dipakai ulang).
- Panel `naskah.html`: pola bahasa/format/konsistensi (tombol +
  wadah + JS IIFE polling).
- `app/ai.py`: `_panggil_router` (pintu tunggal LLM).

## Yang KURANG (yang dibangun)
Pemeriksa abstrak di `app/bagian_awal.py` (Bagian baru di akhir
berkas, Bagian 1 yang lama TIDAK berubah), rute di
`app/rute_bagian_awal.py`, panel di `app/templates/naskah.html`.

## 5 pemeriksaan
Tiga pakai LLM (SATU panggil, pola konsistensi), dua deterministik.

| id | label tampil | cara | vonis |
|---|---|---|---|
| cocok_id | Abstrak cocok dengan isi | LLM: abstrak Indonesia mencakup masalah, metode, hasil, kesimpulan dari 6 bagian? | cocok / tidak / ragu |
| cocok_en | Abstract cocok dengan abstrak | LLM: Abstract Inggris isinya sama dengan abstrak Indonesia? | cocok / tidak / ragu |
| kunci | Kata kunci cocok dengan isi | LLM: kata kunci (ID + EN) sesuai variabel dan isi? | cocok / tidak / ragu |
| panjang | Panjang abstrak sesuai | Deterministik: tiap bahasa 150-300 kata (generator menargetkan sekitar 250 kata; ambang v1, Boss boleh ubah) | lulus / tidak |
| spasi | Spasi abstrak 1 | Deterministik: spasi baris bagian ABSTRAK/ABSTRACT di docx = 1; bila abstrak belum ada di docx, ragu | lulus / tidak / ragu |

Vonis LLM di luar tiga yang sah dianggap 'ragu'. Gagal parse JSON
LLM -> semua vonis LLM 'ragu' (pola `urai_jawaban_bab`).

## Harga
GRATIS untuk mahasiswa (seperti konsistensi): 1 panggil LLM, biaya
dari saldo Apinex Boss. Yang 6 token HANYA untuk MEMBUAT abstrak
(generator), bukan untuk memeriksa. Pemeriksaan tidak memotong Token
Revisi.

## Alur rute (pola konsistensi)
- POST /v1/abstrak/mulai-latar: titip ke pekerja latar, balas cepat.
  Tekan 2x saat jalan ditahan sopan. Tanpa abstrak tersimpan ->
  tolak "Belum ada abstrak. Buat dulu." (tanpa panggil LLM).
  Tanpa peta Jev -> tolak "Periksa Struktur dulu."
  Abstrak + peta tidak berubah sejak cek terakhir -> hasil terakhir
  langsung (sudah_tersedia), tanpa panggil LLM baru.
- GET /v1/abstrak/status: keadaan + hasil untuk polling.
- Hasil di Setelan `abstrak_hasil_berkas_{fid}` (JSON): sidik
  abstrak + sidik peta, diperiksa_pada, ringkasan, temuan[5],
  langkah_berikut.

## Belum ada abstrak
Bila `muat_abstrak` kosong: rute menolak dengan pesan jelas, panel
menampilkan "Belum ada abstrak" dan mengarahkan ke pembuat abstrak.
Pemeriksa (fungsi) bila dipanggil dengan abstrak kosong mengembalikan
semua vonis 'ragu' (untuk ketahanan dan tes).

## Kriteria terima fid 81
fid 81 TIDAK punya abstrak tersimpan di Setelan (sonde 20 Nov: 0 baris),
jadi rute menolak "Belum ada abstrak". Docx-nya SENDIRI punya abstrak
lengkap (Abstract Inggris 197 kata di paragraf [307] + Abstrak
Indonesia, keduanya spasi 1) — jadi cek spasi dari docx BISA lulus,
walau rute menolak karena Setelan kosong. Verifikasi LLM
(cocok_id/cocok_en/kunci) dilakukan dengan memanggil fungsi pemeriksa
langsung di container memakai abstrak uji (ditulis dari isi fid 81,
TIDAK disimpan ke Setelan, TIDAK memotong token), bukan lewat rute,
supaya tidak mengubah data mahasiswa. Hasil verifikasi 20 Nov 20:35
WIB: LLM menangkap kesalahan nyata di abstrak uji (orientasi
kewirausahaan ditulis "memperkuat pengaruh" seolah moderasi, padahal
hasil menunjukkan pengaruh langsung t=7,645 dan simultan F=640,505);
ringkasan {cocok: 2, lulus: 1, tidak: 2, ragu: 0}; saldo 281 tetap.

## Tes
- tests/test_abstrak.py: pemeriksa (fungsi murni) + panjang + spasi
  + abstrak kosong -> semua ragu + aturan lama tidak berubah.
- tests/test_abstrak_rute.py: router 2 endpoint, Setelan round-trip,
  teks panel, main sudah mendaftarkan rute_bagian_awal.
- Regresi: test_bahasa, test_bahasa_rute, test_format,
  test_format_rute, test_konsistensi_bab, test_konsistensi_rute,
  test_pustaka_periksa, test_pustaka_hidup, test_diagram, test_bab4,
  test_jev_hakim (semua harus tetap lulus seperti di main 4c79e06).

## Batas v1
- Spasi hanya diperiksa bila bagian ABSTRAK/ABSTRACT sudah ada di
  docx; bila belum, ragu (bukan tidak).
- Panjang memakai ambang 150-300 kata (v1); pedoman tidak menyebut
  angka pasti di intisari yang Wulan baca.
- Kata kunci dinilai LLM (cocok/tidak/ragu), bukan pencocokan kata
  persis, karena kata kunci boleh sinonim.
