# 04 — Harga & Kuota

<!-- SOT: Harga & kuota EduAi. Diperbarui 26 Okt 2026. Sumber tunggal angka: app/config.py. Jika dokumen lain menulis angka berbeda, dokumen itu usang. -->

## Peringatan hierarki

**Yang ditagih ke user adalah angka di `app/config.py`.** Dokumen lama (termasuk MASTER_PLAN yang sudah diarsipkan) menulis Peneliti Rp160.000 dan Penerbit Rp500.000 — angka itu TIDAK sama dengan kode dan TIDAK berlaku sebagai harga tagih. Penyelarasan dokumen lama menunggu keputusan Boss (lihat `03-keputusan-terkunci.md` butir terbuka 3). Jangan mengubah angka di sini tanpa ACC Boss, dan jangan menulis angka harga di template/JS — satu sumber saja (`app/config.py`).

## Paket (`app/config.py`: `KUOTA_PAKET`, `PAKET_URUT`)

| Paket | Harga | Storage | Revisi AI/bulan | Belajar (naskah) | Konversi |
|---|---|---|---|---|---|
| Gratis | Rp 0 | 30 MB | 3 | 0 | 0 |
| Penulis | Rp 50.000 | 100 MB | 12 | 0 | 0 |
| Peneliti | Rp 100.000 | 300 MB | 15 | 1 | 1× |
| Penerbit | Rp 300.000 | 1 GB | 50 | 2 | 2× |

Aturan: beli paket lebih tinggi = NAIK; beli paket lebih rendah = TIDAK menurunkan paket user. Reset tiap tanggal 1, sisa credit HANGUS (lazy, tanpa cron). Kuota habis → tawarkan AddOn, BUKAN upgrade paket.

## AddOn (terkunci untuk paket Gratis — validasi di backend)

| AddOn | Harga | Isi |
|---|---|---|
| AI | Rp 50.000 | +30 revisi |
| Konversi Jurnal | Rp 100.000 | 1× konversi |
| Publish Jurnal | Rp 500.000 | 1× pendampingan publish (tidak termasuk paket mana pun) |
| Belajar | Rp 75.000 | +1 naskah Mode Belajar |
| Storage & Folder | Rp 25.000 | +50 MB & +10 folder |

## Tarif kerangka per bab (`TOKEN_KERANGKA_BAB`, ACC 26 Sep 2026)

| Bab | Token |
|---|---|
| BAB I | 15 |
| BAB II | 20 |
| BAB III | 20 |
| BAB IV analisa | 30 |
| BAB IV olah_data | 30 |
| BAB V | 15 |

BAB IV punya DUA layanan terpisah: `analisa` (membaca/menafsirkan hasil + narasi pembahasan) dan `olah_data` (mengolah data mentah → tabel/grafik + uji statistik). Tarif BAB IV lapangan: olah data 30 token, hasil simulasi 5 token, narasi manual gratis (keputusan 21 Okt, mengikuti aturan revisi kolaborasi yang sudah ada: 1 token per item yang dikerjakan AI, gratis bila manual).

## Dompet & potongan

- Satu dompet token per akun (`saldo_token`); potong tepat satu kali di server saat pekerjaan selesai.
- Token Revisi dihitung dari token NYATA yang dilaporkan model (bukan tebakan): `ceil((token_in + token_out) / 10.000) × pengali`, cap 60.
- Dokumen > 55.000 karakter diproses bertahap; tiap bagian = 1 revisi, user diberi tahu dulu (maks 6 bagian).
- Tong sampah: berkas dihapus pindah ke sampah dulu (bukan langsung hilang), hapus permanen otomatis setelah 30 hari, tetap menghitung kuota storage, DB di-backup otomatis sebelum hapus permanen (simpan 5 backup terakhir).
- Topup: QRIS via Pakasir (`app/pakasir.py`); riwayat & pembatalan/refund kuota di `app/saldo.py`, `app/pembatalan.py`.
