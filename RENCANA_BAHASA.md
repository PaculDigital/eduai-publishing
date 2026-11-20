# Rencana Cek Bahasa Pedoman (fitur 3 dari 10)

Gas Boss 20 Nov 2026 16:54 WIB. Rancangan dibahas 19 Nov 20:26 WIB,
sonde fid 81 putaran 2 (skrip /tmp/sonde_bahasa2.py).

## Prinsip (sama seperti Cek Format)

- Lengkapi `app/standar_penulisan.py` sebagai **Bagian 3**, bukan modul baru.
  Aturan bahasa sudah ada sebagai data di `ATURAN_BAKU["bahasa"]`; yang
  dibangun hanya pemeriksanya.
- Deterministik TANPA LLM, GRATIS 0 token.
- Vonis `lulus` / `tidak` / `ragu`, satu aturan = satu baris.
- Tidak memblokir. Tidak butuh Periksa Struktur dulu (membaca docx
  langsung, pakai ulang `baca_docx_format` dari Cek Format).
- Rute + panel ikut pola Cek Format (`rute_format.py`, panel `naskah.html`).

## Aturan yang sudah ada (ATURAN_BAKU["bahasa"])

- pasif: WAJIB bentuk pasif; DILARANG saya/aku/kita.
- dilarang: kata penghubung (sehingga/sedangkan) di awal kalimat;
  'pada' di depan subjek; 'dimana'/'dari' seperti where/of Inggris;
  salah bedakan awalan ke-/di- vs kata depan ke/di.
- istilah_asing: cetak miring + dijelaskan artinya.
- ejaan: PUEBI; kosakata KBBI; desimal pakai KOMA (50,5); bilangan di
  awal kalimat dieja.

## Sonde fid 81 (176 paragraf isi, 448 kalimat, putaran 2)

| Pemeriksaan | Hasil | Vonis |
|---|---|---|
| saya/aku/kita/kami | 1 ("Kita") | tidak bila ketemu |
| sehingga/sedangkan di awal kalimat | 0 | tidak bila ketemu |
| "dimana" satu kata | 2 | tidak bila ketemu |
| di-/ke- menempel kata tempat (diatas, dirumah) | 1 ("diatas") | tidak bila ketemu |
| desimal pakai titik (50.5) | 0 | tidak bila ketemu |
| kalimat aktif (tanpa kata di-/ter-) | 82 dari 448 (18%) | ragu (kemungkinan) |
| pola aktif eksplisit ("penelitian ini menunjukkan") | 15 | contoh untuk ragu |
| "pada" di awal kalimat | 1 | TIDAK diperiksa v1 (sering keterangan waktu, bukan subjek) |
| angka di awal kalimat | 10 | TIDAK diperiksa v1 (kebanyakan potongan sitasi) |

Pelajaran sonde putaran 1 (yang salah, diperbaiki di putaran 2):
- Desimal: 293.753 itu pemisah ribuan (benar), bukan desimal. Hanya
  1-2 digit sesudah titik yang dicurigai (50.5); "Tabel 4.1" dikecualikan.
- Pemecah kalimat: belah hanya sesudah titik + spasi + huruf kapital,
  bukan tiap titik (pecahan desimal dan nomor daftar memecah kalimat).
- "dimana" masuk daftar kata tempat ('mana') di putaran 1 sehingga
  terhitung ganda; di putaran 2 'mana' dikeluarkan dari daftar tempat.

## Pemeriksaan v1 (6 baris)

1. **saya** — kata saya/aku/kita/kami (batas kata, tak peduli kapital).
   Ketemu -> `tidak` ("1 kali, contoh: Kita"). Bersih -> `lulus`.
2. **hubung_awal** — sehingga/sedangkan di awal kalimat. Ketemu ->
   `tidak`. Bersih -> `lulus`.
3. **dimana** — kata "dimana" satu kata. Ketemu -> `tidak`. Bersih ->
   `lulus`.
4. **dike_tempat** — di-/ke- menempel kata tempat/waktu yang umum
   (rumah, kampus, sekolah, kantor, pasar, kota, desa, jalan, tahun,
   bulan, hari, sini, sana, situ, dalam, luar, atas, bawah, depan,
   belakang, samping, tengah, pinggir, seberang). Ketemu -> `tidak`.
   Bersih -> `lulus`.
5. **desimal** — angka.titik 1-2 digit (50.5), bukan pemisah ribuan
   (293.753) dan bukan rujukan Tabel/Gambar/Bab (4.1). Ketemu ->
   `tidak`. Bersih -> `lulus`.
6. **aktif** — kalimat tanpa kata berawalan di-/ter- (proksi kasar
   kalimat aktif). Ketemu -> `ragu` ("82 dari 448 kalimat tampak aktif,
   contoh: penelitian ini menunjukkan... Perlu diperiksa, mesin tidak
   bisa memastikan."). Bersih -> `lulus`. TIDAK PERNAH `tidak`.

## Ruang lingkup

Paragraf isi yang sama seperti Cek Format: gaya Normal/List Paragraph,
panjang teks >= 80 karakter, di antara judul bab pertama dan
'DAFTAR PUSTAKA' (`_batas_isi` dari Cek Format). Kata pengantar dan
bagian awal TIDAK diperiksa (aturan 'saya' di kata pengantar beda:
'saya' diganti 'penulis', tetap dilarang, tapi ruang lingkup v1 hanya
isi agar hitungan bersih).

## Batas jujur v1

- Pasif TIDAK bisa dipastikan dengan aturan saja. Vonis `aktif` selalu
  `ragu`, tidak pernah `tidak`. "Gambar 1.1 menunjukkan" dan "merupakan"
  adalah frasa akademik yang umum, bukan pelanggaran yang pasti.
- "pada" di depan subjek dan angka di awal kalimat TIDAK diperiksa di v1
  (terlalu banyak positif palsu: keterangan waktu dan potongan sitasi).
- Kosakata KBBI dan istilah asing miring DITUNDA ke v2 (butuh daftar kata
  dan pemeriksa miring; pemeriksa miring belum ada di modul).

## Kriteria terima (fid 81)

- Ringkasan dari sonde: lulus 2, tidak 3, ragu 1.
  (saya tidak, dimana tidak, dike_tempat tidak, hubung_awal lulus,
  desimal lulus, aktif ragu.)
- Tes unit 23+ dan tes rute 11+, semua lulus, tidak ada regresi.

## Kode yang dibangun

- `app/standar_penulisan.py` Bagian 3: `periksa_bahasa(jalur,
  aturan=None)` -> {sidik_berkas, diperiksa_pada, ringkasan, temuan,
  langkah_berikut}; `langkah_berikut_bahasa(temuan)`; pemeriksa
  `_cek_kata` (saya, dimana, dike_tempat), `_cek_awal_kalimat`
  (hubung_awal), `_cek_desimal`, `_cek_aktif`; helper
  `_kalimat_isi(model)` (pemecah kalimat yang sama seperti sonde 2).
  Konstanta: `PEMERIKSAAN_BAHASA` (6), `VONIS_SAH_BAHASA`,
  `KATA_TEMPAT_BAHASA`, `KATA_KERJA_AKTIF_BAHASA`,
  `PANJANG_MINIMAL_KALIMAT_BAHASA=20`.
- `app/rute_bahasa.py`: POST `/v1/bahasa/mulai-latar`, GET
  `/v1/bahasa/status`, pola `rute_format.py` (gerbang sidik, pekerja
  latar, hasil di Setelan `bahasa_hasil_berkas_{fid}`).
- Panel `app/templates/naskah.html`: `.panel-bahasa`, tombol
  "Cek Bahasa" (`data-bahasa`), JS IIFE sendiri (akhiran B).
- Tes: `tests/test_bahasa.py`, `tests/test_bahasa_rute.py`.
