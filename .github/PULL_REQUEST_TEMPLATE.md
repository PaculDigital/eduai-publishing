## Apa yang diubah

<!-- Ringkas: berkas/fitur apa saja. Sebut jalurnya. -->

-

## Kenapa

<!-- Masalah apa yang diselesaikan? Kalau memperbaiki bug, apa AKAR-nya
     (bukan gejalanya)? -->

-

## Apa yang diuji — WAJIB ADA ANGKA

```bash
# Tempel perintah yang dijalankan
$ bash scripts/periksa_kode.sh
# Tempel keluaran ASLINYA (baris terakhir cukup kalau panjang)
```

| Uji | Perintah | Hasil |
| :- | :- | :- |
|  |  |  |

<!-- DILARANG menulis "sudah dites, aman" tanpa keluaran.
     Kalau belum diuji, tulis "BELUM DIUJI" — itu lebih berguna. -->

## Apa yang BELUM

<!-- Batasan yang kamu tahu tapi belum dikerjakan. Jujur di sini
     mencegah orang lain mengira ini sudah lengkap. -->

-

## Risiko

<!-- Apa yang bisa rusak kalau perubahan ini salah? Bagian mana yang
     paling perlu diperiksa manusia? -->

-

---

## Daftar periksa (centang yang benar)

- [ ] Saya **tidak** mengubah `main` — bekerja di branch `agen/<nama>/<tujuan>`
- [ ] Saya **tidak** mengubah berkas terlarang (`.gitignore`, `Dockerfile`, `jalankan.sh`, `SOT_*.md`, `scripts/periksa_kode.sh`)
- [ ] Tidak ada `.env`, `secret`, `*.pem`, `*.key`, atau DB di commit ini
- [ ] `bash scripts/gerbang_git.sh --periksa` → **LULUS**
- [ ] `bash scripts/periksa_kode.sh` dijalankan, keluarannya ditempel di atas
- [ ] Saya sudah membaca `AGEN_LUAR_ATURAN.md`

## Catatan untuk peninjau

<!-- Apa yang paling ingin kamu dapat masukan? Bagian mana yang kamu
     sendiri masih ragu? -->
