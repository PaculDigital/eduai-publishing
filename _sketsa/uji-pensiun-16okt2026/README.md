# 🗄️ UJI YANG DIPENSIUNKAN — 16 Okt 2026

Dua uji dipindah ke sini karena **cacat**, bukan karena fiturnya selesai.
Aturan Bos: **`mv`, bukan `rm`** — riwayat disimpan untuk pelajaran.

## 1. `_uji_jembatan_bab.py` (140 baris) — **TERBUKTI PALSU**

Melaporkan **27 LULUS / 0 GAGAL** untuk jembatan bab kurang, padahal di
produksi jembatan **tidak pernah muncul**.

**Sebab:** uji ini **memaksa** nilai `siap.kelengkapan` langsung di dalam
template, sedangkan **rute asli mengirim `kelengkapan` dari tempat lain**
(bentuk berbeda) ⇒ yang diuji **bukan jalur produksi**.

**Pengganti:** `_uji_jembatan_kurang.py` (pakai naskah asli pendek, bajak
`muat_naskah`) + `_uji_jembatan_final.py` (lewat rute nyata).

## 2. `_uji_gigi_jembatan.py` (87 baris) — **MERUSAK PRODUKSI**

Untuk membuktikan uji bergigi, uji ini **menimpa**
`app/templates/artikel_konversi.html` **di dalam container yang SEDANG
MELAYANI USER**, lalu memulihkannya. Proses **crash di tengah** ⇒ pemulihan
tidak jalan ⇒ judul jadi `XXX-MATI-XXX` dan **tertinggal di produksi** ⇒ uji
berikutnya GAGAL dan Wulan **hampir menyalahkan kode aplikasi**.

**Pengganti:** uji gigi di dalam `_uji_jembatan_final.py` — kerusakan disuntik
ke **SALINAN** di `/tmp/uji_gigi_tpl/`, berkas produksi **tidak disentuh**.

## 📌 Pelajaran (masuk skill `test-gate-design`)

`references/tiga-pola-uji-merusak-16okt2026.md`:
1. Uji gigi JANGAN menimpa berkas produksi hidup.
2. Uji yang memaksa variabel template = UJI PALSU.
3. Gagal palsu karena kata kunci juga ada di blok lain / MENU.

**Tanda kenal kerusakan tertinggal:** hasil uji **berubah-ubah antar-run**
tanpa kode disentuh ⇒ BACA ISI BERKAS DULU.
