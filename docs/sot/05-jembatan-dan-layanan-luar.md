# 05 — Jembatan & Layanan Luar

<!-- SOT: Jembatan & layanan luar EduAi. Diperbarui 26 Okt 2026. -->

## Prinsip jembatan (terkunci 06–08 Okt 2026)

Satu proyek = satu dunia. Jangan pinjam kredensial antar proyek. Jembatan antar layanan hanya lewat API resmi + kunci layanan, bukan lewat kredensial user atau layanan lain.

## Statistik Lab (BAB IV)

- Bentuk: OPSI B (21 Okt 2026) — EduAi mengirim header `X-Kunci-Layanan`, timeout 60 detik.
- Kunci: EduAi membaca `EDUAI_STATISTIK_KUNCI` (atau lewat halaman pengaturan layanan `'statistik'`), Statistik Lab membandingkannya dengan env `JEMBATAN_KUNCI_LAYANAN`. Keduanya harus sama persis. Belum dipasang = 503, salah/tanpa kunci = 401.
- URL bawaan sudah mengarah ke https://statistik.bikinaja.id sehingga tidak perlu diubah.
- Rumah data = EduAi; mesin Statistik Lab hanya hitung & tidak menyimpan; parsing oleh Jev/AI EduAi.
- Modul: `app/jembatan_statistik.py` (klien), `app/bab4.py` (layanan simpan/kunci/tarif), `app/kunci_layanan.py` (pendaftaran layanan `'statistik'`).
- Status: sudah merge ke `main`, BELUM deploy (cek live 26 Okt 10.44 WIB: `/api/bab4/ringkasan` = 404). Sisa: build/deploy image + pasang kunci produksi.

## OJS / JEMT (Tridarma)

- Jurnal: Tridarma.id — Jurnal Ekonomi dan Manajemen Tridarma (JEMT), E-ISSN 3163-608X.
- Jembatan OJS yang benar: `https://tridarma.id/mcp`.
- LoA otomatis: EduAi mencetak LoA sendiri (OJS tidak punya berkas LoA) — PDF 1 halaman + tanda tangan + QR verifikasi. Halaman verifikasi publik: https://qr.tridarma.id. Modul: `app/loa.py`, template `app/templates/loa/loa-jemt.html`.
- Syarat LoA terbit: status = Diterima, Volume + Nomor ada, WA `0851-7813-8514`. Kosong ⇒ LoA TIDAK terbit (pesan jelas). Status = TOMBOL MANUAL, bukan otomatis.
- Detail fitur LoA: `SOT_LOA_QR_17OKT2026.md` (root, dipertahankan). Detail submit artikel: `PUTUSAN_SUBMIT_ARTIKEL_JURNAL_16OKT2026.md`.

## Layanan luar lain

| Layanan | Peran | Catatan |
|---|---|---|
| 9router | Satu pintu AI (semua panggilan model lewat sini, tidak ada jalur kedua); juga vision untuk foto bukti di Statistik Lab | Modul: `app/ai.py` |
| Jev / TypeSafe | Membaca BENTUK naskah (bab/subbab/posisi), di depan mesin & AI | Acuan pakai: `PANDUAN_PAKAI_JEV.md`; urutan resmi: `URUTAN_RESMI_PETA_NASKAH_TERKUNCI.md` |
| OnlyOffice | Editor & kolaborasi dosen↔mahasiswa (mode baca untuk pembimbing) | Modul: `app/onlyoffice.py`; jebakan editor: `JEBAKAN_EDITOR_OO.md` |
| Pakasir | Topup QRIS | Modul: `app/pakasir.py` |
| WA (Gowa) | Notifikasi ke mahasiswa/pembimbing | Modul: `app/wa.py`; webhook & nomor resmi diatur di setelan WA |

## Jika flow putus di tengah

Flow putus sering bukan bug EduAi, melainkan salah satu layanan di atas mati — dan dari layar user terlihat sama saja. Urutan periksa: (1) layanan luar itu hidup atau tidak, (2) kunci layanan cocok atau tidak, (3) baru kode EduAi. Jangan menambal di hilir sebelum akar di layanan itu dipastikan.
