# RANCANGAN JEMBATAN BAB IV — EduAi → Statistik Lab (backend hitung)

Tanggal: 21 Oktober 2026 · Penyusun: Wulan · Branch: `agen/wulan/bab4-statistik-backend`
Status: RANCANGAN untuk diputuskan Bos — BELUM dikoding.
Dasar putusan: CATATAN_DISKUSI_BAB4_KONVERSI_08OKT2026.md §4.4 (TERKUNCI oleh Bos)
+ inventaris kode nyata Statistik Lab (repo statistik-lab, src @ 9ca0364) 21 Okt 2026.
Istilah dikunci Bos 21 Okt 2026: BAB IV = HASIL & PEMBAHASAN (bukan Metodologi).

---

## 1. INVENTARIS MESIN STATISTIK LAB — YANG BENAR-BENAR ADA

Endpoint diagnosis (mesin hitung data ASLI user — bukan BUAT DATA/simulasi):

| Endpoint | Isi | Bukti |
|---|---|---|
| `POST /api/diagnosis/unggah` | Multipart berkas (CSV/XLSX), maks 10 MB → `{kunci, n_baris, n_kolom, kolom[{nama,kosong,jenis}], pratinjau}` | app/main.py:702 statistik-lab |
| `POST /api/diagnosis/periksa-peran` | `{kunci, peran}` → validasi peran kolom (masalah/tanya/kelompok) TANPA menghitung | app/main.py:742 |
| `POST /api/diagnosis/periksa` | `{kunci, mode, kolom_x, kolom_y, kolom_m, kolom_z, peran, konstruk, missing}` → hasil lengkap (di bawah) | app/main.py:832 |
| `GET /api/status` | `{app, ai_aktif, versi}` — live 21 Okt: ai_aktif=true | live |

Hasil `/periksa` mode SPSS (dari `periksa_spss`, app/diagnosis.py:184):
`n, n_dibuang, koef[{nama,b,se,t,p}], r2, r2_adj, normalitas{ks,shapiro,
dagostino,skew,kurtosis,lulus}, hetero{glejser,lulus}, vif[], vif_maks,
linearitas, outlier, dw, kaitan{mediasi/moderasi}, titik{zpred,zresid,pp,
hist,xy}` + `masalah[]` berisi nasihat cara memperbaiki (dari server).
Mode PLS (`periksa_pls`): per konstruk outer loading, AVE, CR, Cronbach
alpha; VIF inner; Fornell-Larcker; HTMT.

Peta ke kerangka BAB IV EduAi (`app/kerangka_bab.py` bab '4'):

| Sub-bab | Dilayani mesin? |
|---|---|
| 4.1 Deskripsi objek & responden | ⚠️ Sebagian — n & tingkat pengembalian dari EduAi (data EduAi sendiri); karakteristik responden belum ada di mesin |
| 4.2 Deskripsi data (mean, SD, kategori) | ❌ BELUM ada di respons mesin — lihat §4 usulan |
| 4.3 Uji prasyarat | ✅ normalitas, linearitas, multikolinearitas (VIF), hetero, DW, outlier |
| 4.4 Uji hipotesis | ✅ koefisien + t + p + R²; mediasi/moderasi lewat `kaitan`; PLS lengkap |
| 4.5 Pembahasan | ✅ bahan lengkap untuk AI EduAi menafsir (hasil + nasihat mesin) |

## 2. ⚠️ SATU TABRAKAN DENGAN PUTUSAN BOS — PERLU PUTUSAN BARU

Putusan 08 Okt: "mesin hanya hitung, TIDAK menyimpan."
Realita kode mesin: `/unggah` menyimpan data di MEMORI server
(`simpan_sementara`, app/diagnosis.py:131) — tidak ke disk, maks 12 sesi,
umur 45 menit, lalu hilang. Alasannya alur 2 langkah: user menunjuk peran
kolom dulu, baru hitung (keputusan Bos sendiri di Statistik Lab, 21 Sep).

Dua jalan jembatan:

**Opsi A — Pakai alur 2 langkah apa adanya (tanpa ubah Statistik Lab).**
EduAi: unggah → terima kunci → periksa-peran → periksa → selesai.
Data singgah di memori mesin ≤45 menit, tidak pernah ke disk.
Plus: nol perubahan di repo statistik-lab, bisa dibangun sekarang.
Minus: "menyimpan sementara" — melunak dari bunyi putusan, walau
semangatnya (tidak ada rumah data kedua) tetap terjaga.

**Opsi B — Endpoint jembatan khusus stateless di Statistik Lab.**
`POST /api/jembatan/hitung` baru: satu panggilan berisi data rapi + peran
+ mode → hasil, tanpa sesi, tanpa simpan apa pun.
Plus: persis bunyi putusan Bos; kontrak bersih untuk mesin-ke-mesin.
Minus: perlu perubahan + deploy di repo statistik-lab juga
(satu PR di sana), dan duplikasi sebagian logika unggah/periksa.

Rekomendasi Wulan: **Opsi B untuk produksi, Opsi A untuk prototipe uji**
— prototipe membuktikan kontrak datanya benar dengan mesin yang ada hari
ini; produksi tidak membawa pengecualian diam-diam terhadap putusan Bos.

## 3. KONTRAK DATA (EduAi → mesin) — bentuk yang dikirim

EduAi (Jev/AI/kode) menyiapkan, mesin tidak menebak:

```json
{
  "mode": "spss | pls",
  "peran": {"Kualitas_Produk_1": "X1", "Kualitas_Produk_2": "X1",
            "Harga_1": "X2", "Kepuasan_1": "Y1"},
  "model": {"jenis": "kuantitatif", "desain": "survei",
            "jalur": "X1,X2 -> Y1", "bentuk_mediasi": null},
  "missing": "buang | rata",
  "berkas": "<csv/xlsx data lapangan ASLI user, kolom per-item>"
}
```

Aturan kontrak:
- Nama kolom = per-item, pola terbukti Statistik Lab: `Nama_Variabel_Nomor`.
- Peran hanya: X*, M* (perantara/mediasi), Z* (penguat/moderasi), Y*.
  (Pelajaran mesin 21 Sep: peran Z dulu terbuang diam-diam — kontrak wajib
  menguji Z terkirim & terhitung.)
- Skala Likert 1–5; sel kosong = kosong betulan (di SPSS jadi SYSMIS),
  JANGAN diisi -1/0 oleh EduAi.
- Batas: berkas ≤10 MB (MAX_BYTE mesin), n baris bersih ≥10 (mesin menolak
  di bawah itu dengan pesan ramah), target sampel wajar 30–2000.

Kontrak balikan (mesin → EduAi): respons `/periksa` apa adanya +
`masalah[]` (nasihat perbaikan). EduAi menyimpan HASIL ini + data asli
di EduAi (rumah data), meneruskannya ke AI untuk tafsir 4.5, dan ke
mesin gambar EduAi untuk grafik (`titik` sudah bahan gambar siap pakai).

## 4. CELAH YANG HARUS DITUTUP (jujur)

1. **Deskriptif 4.2** (mean/SD/kategori per variabel): belum keluar dari
   mesin. Usulan: hitung di EduAi dari data asli yang memang disimpan
   EduAi — hitungan ringan satu sumber dari data yang sama, BUKAN mesin
   kedua. Perlu ACC Bos karena menyentuh prinsip "satu mesin hitung".
   Alternatif: tambah `deskriptif` ke respons mesin (PR kecil di
   statistik-lab, sekalian Opsi B).
2. **Karakteristik responden 4.1** (usia/jenis kelamin/dll): kolom
   demografis bukan peran X/Y — kontrak perlu bagian `demografis: [...]`
   agar EduAi bisa menabulasikannya sendiri.
3. **Autentikasi antar-layanan**: API diagnosis hari ini publik tanpa
   kunci. Jembatan produksi perlu token antar-layanan BARU milik EduAi
   (dibuat untuk EduAi, disimpan di .env EduAi + .env statistik-lab
   sebagai pasangan) — BUKAN pinjam kredensial proyek lain (aturan
   batas proyek tetap berlaku). Perlu ACC Bos untuk pembuatannya.
4. **Kualitatif**: mesin kualitatif Statistik Lab sudah live terpisah
   (/kualitatif) — di luar kontrak ini. BAB IV kualitatif tetap di luar
   lingkup sampai Bos putuskan.

## 5. ALUR BAB IV DI EDUAI (sketsa layar — nol halaman lepas, menumpang sistem ada)

Sesuai putusan 08 Okt §2.4: titip ke sistem yang ada (editor OnlyOffice +
jalur revisi + satu dompet token). Harga sudah ada: analisa 30 /
olah_data 30 token (`app/config.py`).

```
[1] User minta lengkapi BAB IV dari naskah (di editor / jalur kerangka)
[2] Jev baca BAB I–III → tarik 4 prasyarat: jenis, desain, model, sampel
    · ketemu semua → tampilkan untuk dikonfirmasi user (bukan form kosong)
    · ada yang hilang → tanya user HANYA yang hilang
[3] Satu pertanyaan pemotong: "Data lapanganmu sudah terkumpul?"
    · BELUM → "Siapkan Penelitian": AI susun kuesioner dari model
      (butir per variabel sesuai peran X/M/Z/Y) + panduan sebar.
      Berhenti di sini — tidak ada BAB IV palsu dari data kosong.
    · SUDAH → lanjut
[4] User unggah data KE EDUAI → kode EduAi periksa bentuk (GRATIS):
    kolom per-item? peran lengkap? n cukup? skala 1–5?
    · keliru → beri tahu persisnya + jalan perbaikinya
      (perbaikan berbayar sesuai putusan Bos — nominal belum diputuskan)
    · benar → kunci peran bersama user (layar konfirmasi peran,
      pola periksa-peran mesin)
[5] Potong token olah_data → kirim lewat jembatan → mesin hitung
    → hasil + tabel + bahan grafik disimpan DI EDUAI
[6] Potong token analisa → AI tafsir hasil → draf 4.1–4.5 masuk editor
    (Jev periksa hasil) → user terima/tolak per bagian, pola revisi lama
```

## 6. KEPUTUSAN YANG DIMINTA KE BOS (urut)

1. Jembatan: Opsi A (prototipe sekarang) → B (produksi), atau langsung B?
2. Deskriptif 4.2: hitung di EduAi, atau tambah ke mesin sekalian Opsi B?
3. Token antar-layanan baru untuk jembatan: ACC dibuatkan?
4. Harga: "Siapkan Penelitian" (kuesioner) masuk token olah_data,
   atau AddOn terpisah? (terbuka sejak 08 Okt §6.3/4/11)
5. Data keliru: charge perbaikan berapa & bentuknya?

Setelah 1–3 diputuskan, Wulan mulai koding di branch ini:
modul baru `app/bab4.py` + `app/jembatan_statistik.py` (router terpisah,
tidak menumpuk di main.py), uji kontrak terhadap mesin live dengan data
contoh, jalankan gerbang, lalu PR dengan keluaran gerbang ditempel.
