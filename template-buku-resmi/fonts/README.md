# Font Template Buku — Kenapa Folder Ini TIDAK Berisi Berkas Font

## Jawaban singkat

Font template **tidak bisa disimpan di repo ini**, dua alasan:

1. **Repo ini PUBLIK.** Menaruh berkas font berbayar di repo publik =
   menyebarkan salinan font ke siapa pun yang membuka internet. Itu
   pelanggaran lisensi & hak cipta, dan berisiko repo di-takedown (DMCA).
2. **Semua font kunci template adalah font komersial/proprietary** —
   tidak ada satu pun yang berlisensi bebas sebar (lihat tabel).

Template `.docx` sendiri juga **tidak membawa font tertanam** — terverifikasi
22 Okt 2026: tidak ada berkas `.odttf`/font di dalam zip, dan
`embedTrueTypeFonts` di settings.xml = mati. Yang ada hanya **nama** font
di `fontTable.xml` dan di setiap run. Font hidup di mesin yang membuka
dokumen; kalau tidak terpasang, Word/LibreOffice menggantinya diam-diam
dan bentuk buku berubah (README utama §7).

## Asal-usul font ini

Wulan **tidak pernah mengunduh/memiliki berkas font-font ini**. Nama-nama
di bawah dibaca dari XML template yang Boss terima dari **Jejak Publisher**
(`docProps/core.xml`: creator = "Jejak Publisher") — mesin pembuat template
itulah yang memasangnya dulu. Di mesin Wulan (Linux), **tidak satu pun**
terpasang (terverifikasi `fc-list`, 22 Okt 2026).

## Daftar font & cara memperoleh yang SAH

| Font | Dipakai untuk | Sumber sah |
|---|---|---|
| **Trajan Pro** | judul bab & judul bagian (Heading1) | Adobe — beli lisensi / langganan Adobe Fonts. Lisensi Adobe Fonts **melarang** mengunggah berkas font ke repo/server bersama. |
| **Palatino Linotype** | **isi buku** (paling kritis) | Terbundel di Windows berlisensi (Microsoft). Mesin Windows + Office umumnya sudah punya. Berkasnya tidak boleh disebar ulang. |
| **Adobe Garamond Pro** | sampul | Adobe — sama seperti Trajan Pro. |
| **Elephant** | sampul / judul besar | Font komersial (lisensi desktop berbayar). |
| **Digory Doodles** | hiasan (eastAsia judul sampul) | Font komersial. |
| **Nyala** | style Pa2/Pa5 | Terbundel di Windows berlisensi (Microsoft). |
| **Calibri** | eastAsia pendamping di banyak run | Terbundel di Windows/Office berlisensi. |
| **Times New Roman** | style Normal (dasar) | Terbundel di Windows/Office berlisensi (Monotype). |
| Roboto | elemen lain-lain (2 run) | **Bebas** (Apache 2.0, Google Fonts) — satu-satunya yang boleh disimpan di repo bila perlu. |

## Cara membuat paket ini "komplet" — yang SAH

1. **Di mesin produksi/render (Windows)**: pastikan font di atas terpasang
   dari sumber sahnya (Windows berlisensi menutup Palatino/Nyala/Calibri/
   Times New Roman; Adobe menutup Trajan Pro + Garamond Pro).
2. **Periksa dengan alat, bukan perasaan**:
   `python3 scripts/periksa_font.py` — memeriksa font terpasang di mesin
   ini; `--folder <folder>` memeriksa folder font tertentu (mis. folder
   font di server Boss) tanpa menyalin apa pun ke repo.
3. **Kalau Boss memiliki berkas font berlisensi milik sendiri** (mis. dari
   mesin Windows tempat template dibuat): simpan di **penyimpanan privat
   di luar repo publik** (server produksi / drive privat), lalu arahkan
   `periksa_font.py --folder` ke sana. JANGAN commit ke repo ini.
4. Mengganti font dengan alternatif gratis = mengubah wajah buku =
   **bukan persis template**. Hanya layak untuk render draf, bukan final.

## Yang diperiksa `periksa_font.py`

Sembilan nama font di tabel atas. Keluaran per font: ADA (dan contoh
lokasinya) / HILANG. Exit 0 bila semua ada, 1 bila ada yang hilang —
pola yang sama dengan gerbang buku.
