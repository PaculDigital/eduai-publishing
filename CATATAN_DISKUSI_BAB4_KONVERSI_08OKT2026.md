<!-- CATATAN DISKUSI (RIWAYAT) — SOT: bukan sumber status. Status fitur konversi ada di SOT_KONVERSI_JURNAL.md -->

# CATATAN DISKUSI — BAB IV (KONVERSI ARTIKEL JURNAL): KEKURANGAN BAB

> ⛔ STATUS: **DILARANG DIKODING.** Ini catatan diskusi saja (perintah Bos
> 08 Okt 2026: *"Kamu catat dulu saja, untuk masalah detail pengerjaan bab 4"*).
> Dibahas lagi kapan-kapan setelah Bos buka.

Tanggal catat: 08 Oktober 2026
Proyek: EduAi Publishing · Fitur konversi naskah → artikel jurnal
Terkait: `SOT_KONVERSI_JURNAL.md` · `app/konversi.py` · Statistik Lab (kuantitatif)

---

## 1. LATAR: masalah yang muncul

Saat user menekan konversi ke artikel jurnal, naskahnya bisa **belum lengkap**:

- baru **proposal** (BAB I–III saja)
- hanya **3 bab**
- Jev **tidak bisa memolakan** (tidak ketemu bab sama sekali)

**Masalah logika (kata Bos, verbatim inti):** artikel jurnal lahir dari
penelitian yang **SUDAH SELESAI** (ada hasil & ada simpulan). Naskah baru
3 bab / proposal **tidak bisa** jadi artikel jurnal — itu **cacat logika**.

⇒ Kesimpulan Bos: jangan konversi, **arahkan user melengkapi dulu**, dan
bantuan melengkapi itu **layanan berbayar seperti biasa**.

---

## 2. PUTUSAN BOS YANG SUDAH DIKUNCI (08 Okt 2026)

### 2.1 Tidak memblokir — beri penjelasan + tawaran bantuan
Verbatim: *"Jangan blokir, tapi di beri penjelasan dan berikan tawaran bantuan
agar user nanti bisa konversi naskahnya dengan benar dan produk akhirnya
adalah artikel jurnal dari naskah"*

⇒ User **tetap bisa** membuka naskahnya, melihat apa yang kurang, dan
**memilih** mau dibantu atau tidak. Bukan dinding, tapi **pintu**.

### 2.2 Nada tolakan: HANGAT & HALUS
Verbatim: *"Ya tolak saja secara hangat dan halus. Dan jangan sebut alat atau
mesin atau ai kita tidak mampu"*

⇒ **DILARANG** menulis "AI kami tidak sanggup" / "mesin tidak bisa".
Boleh disebut: naskahnya **belum sampai tahap penelitian selesai**.

### 2.3 Aturan penentu (usul Wulan, disetujui arah)
Verbatim Bos: *"yang jelas jika naskah masuk dan tidak bisa di polakan oleh
jev atau hanya ada 3 bab maka di tolak"*

⇒ Penentu = **Jev tidak menemukan bab** ATAU **bab kurang**.
⚠️ **Catatan Wulan (perlu dibahas lagi):** memakai patokan **kata**, bukan
angka buta — sebab ada kampus dengan **BAB IV = Simpulan** (total 4 bab).
Jadi yang diperiksa: **"ada bab HASIL?"** + **"ada bab SIMPULAN?"**
(bukan wajib angka "V"). Aturan ini **BELUM diputuskan Bos** — masih terbuka.

### 2.4 Tidak buka cabang baru
Verbatim: *"Saya juga ada pemikiran agar tidak buat cabang baru yang bikin
ruwet... masalah kekurangan bab di konversi ini di masukkan ke sistem kita,
agar tidak buka jalur baru"*

⇒ Arah: **titipkan ke sistem yang SUDAH ADA** (OnlyOffice + jalur revisi +
satu dompet). **Nol halaman baru, nol mesin baru, nol dompet baru.**

### 2.5 Alasan: core awal sistem = OnlyOffice
Verbatim: *"kita arahkan ke system yang sudah ada melalui revisi dengan
pembimbing, yang core awal menggunakan onlyoffice"*

⇒ Pintu masuknya **editor yang sudah jalan** (OO), bukan UI baru.

---

## 3. MASALAH BESAR YANG BELUM TERPECAHKAN: BAB IV

Verbatim Bos: *"Saya mau khusus bab IV ini unik dan khusus karena melibatkan
narasi, uji dan olah data."*

### 3.1 BAB IV = TIGA pekerjaan berbeda pemilik

| # | Pekerjaan | Pemilik | Bisa otomatis? |
|---|---|---|---|
| 1 | Kuesioner / instrumen penelitian | Mesin (+ AI bantu rumus) | ✅ bisa |
| 2 | **Kumpul data lapangan** | **USER** | ❌ **mustahil otomatis** |
| 3 | Uji & tabel hasil | Mesin (Statistik Lab) | ✅ bisa |
| 4 | Interpretasi / tafsir hasil | AI | ✅ bisa |

Verbatim Bos: *"untuk buat bab 4 butuh data lapangan, berarti kena charge buat
data lapangan juga, butuh olah data juga kan. Ini gap yang belum kita
selesaikan untuk buat bab 4"*

### 3.2 Rincian 5 langkah versi Bos (verbatim)
1. Mesin mengeluarkan pertanyaan kuesioner
2. Mesin mengeluarkan data lapangan
3. Data lapangan perlu uji
4. Mesin perlu mengeluarkan hasil uji dan tabel hasil
5. AI perlu interpretasi hasil

⚠️ **Catatan Wulan — ada satu kekeliruan kecil di nomor 2:** mesin **tidak
bisa "mengeluarkan data lapangan"** — data lapangan itu dari **USER** (ke
lapangan/kuesioner). Yang bisa mesin: **kuesioner kosong siap dibagikan** +
**panduan cara kumpul data**. Perlu diklarifikasi ke Bos saat bahasan dibuka.

### 3.3 Usul pembagian kerja
- **Narasi saja** (tafsir/tulis 1 bab): **15–20 token per bab** (angka Bos)
  · kalau 2 bab → dikali dua
- **Ada olah data** → masuk **AddOn Olah Data** (tersendiri)
- User **sudah punya data** → tinggal **unggah data lapangan**
- Data **salah/keliru** → **kena charge lagi** untuk perbaikan (kata Bos)

### 3.4 Ide pemotong kerumitan (usul Wulan, BELUM diputuskan)
**Satu pertanyaan di depan:** *"Data penelitianmu sudah terkumpul?"*

```
BELUM  → jangan tawarkan BAB IV. Tawarkan "Siapkan Penelitian":
         mesin keluarkan kuesioner + panduan kumpul data. Selesai.
         (user pergi ke lapangan; tidak ada BAB IV di tahap ini)
SUDAH  → masuk AddOn Olah Data:
         unggah data → mesin periksa bentuk dulu (GRATIS, pola yg sudah ada)
         → keliru: beri tahu + charge perbaikan
         → benar: uji + tabel hasil → AI tafsir → BAB IV jadi
```

### 3.5 Usul harga (BELUM diputuskan Bos)
Wulan condong: **olah data = AddOn TERPISAH dari token**, alasannya
**token = jasa AI**, sedangkan **olah data = jasa mesin hitung** — beda jenis
jasa, beda harga. Kalau dicampur, user bingung kenapa olah data dihitung
sama dengan revisi tulisan.

⚠️ **Terbuka:** "Siapkan Penelitian" (kuesioner) dan "Olah Data" itu
**satu AddOn dua tahap** atau **dua AddOn terpisah**? Wulan condong
**satu AddOn, dua tahap**.

---

## 4. PENGHALANG TEKNIS YANG DISEBUT BOS

### 4.1 Statistik Lab baru KUANTITATIF
Verbatim: *"mesin Statistik baru kuantitatif saja kwalitatif belum bisa."*

⇒ Naskah **kualitatif** dengan bab kurang: **BELUM ada jalannya**.
Opsinya (belum diputuskan): tolak halus, atau tawarkan **narasi saja**
tanpa olah data.

### 4.2 BAB IV butuh MESIN dari proyek lain — ✅ BOS SUDAH IZINKAN JEMBATAN
Verbatim: *"Karena menyangkut mesin kita di lab Statistik"*

⚠️ **PEMBUKAAN PENTING — PUTUSAN BOS 08 Okt 2026 (verbatim):**
> *"project Statistik lab walau independent tapi bisa di beri jembatan ke
> project EduAi ini sebagai backend khusus."*

⇒ **ATURAN BATAS PROYEK TIDAK DILANGGAR.** Aturan 03 Okt 2026 melarang
**memakai kredensial berkas proyek lain secara diam-diam**. Yang Bos
izinkan sekarang = **JEMBATAN RESMI**: Statistik Lab jadi **backend khusus**
EduAi untuk olah data.

**Jembatan resmi ≠ pinjam kredensial.** Aturannya tetap:
- **TANYA/BERI TAHU BOS** sebelum menyambung (bukan diam-diam) ✅ sudah
- **JANGAN** membaca `.env`/kredensial Statistik Lab sewenang-wenang
- Jembatan dibuat **eksplisit**: panggilan API resmi antara dua layanan
  (pola yang sudah ada di EduAi: `oo-converter` = layanan terpisah,
  dipanggil lewat HTTP + jaringan `eduai-net`)
- Ini **menyentuh proyek lain** ⇒ **WAJIB bahasan khusus + izin sebelum koding**

Referensi pola jembatan yang sudah jalan: `oo-converter` (OnlyOffice) —
container terpisah, diakses lewat jaringan Docker, bukan impor kode.

### 4.3 ⭐ PRASYARAT WAJIB SEBELUM BAB IV (putusan Bos 08 Okt 2026)

Verbatim: *"sebelum mengerjakan bab 4 wajib tahu jenis penelitian, design
penelitian, model penelitian dan sample penelitian dulu. Data ini penting
untuk memperak(an) kuesioner dan variabel apa saja agar bisa di baca oleh
mesin Statistik lab."*

⇒ **4 hal yang WAJIB diketahui DULU (bukan opsional):**

| # | Yang wajib diketahui | Gunanya |
|---|---|---|
| 1 | **Jenis penelitian** | kuantitatif / kualitatif (menentukan jalur) |
| 2 | **Desain penelitian** | eksperimen / survei / korelasi / komparatif |
| 3 | **Model penelitian** | X, M, Y, Z — jalur pengaruh (regresi/mediasi/moderasi) |
| 4 | **Sampel penelitian** | siapa responden, berapa jumlahnya |

**Kenapa 4 ini wajib:** supaya bisa:
- **Merancang kuesioner** yang benar (pertanyaan sesuai model)
- **Menentukan variabel** apa saja yang diukur
- Menghasilkan **bentuk data yang bisa DIBACA mesin Statistik Lab**
  (kolom per-item, pola yang sudah terbukti: `Kualitas_Produk_1`, `Harga_1`, `Y1`…)

⇒ Urutan logisnya: **kenali 4 hal dulu → baru kuesioner → baru data lapangan
→ baru olah data → baru BAB IV.**

⚠️ Ini **memperkuat ide pertanyaan pemotong (§3.4)**: pertanyaan "data sudah
terkumpul?" **BUKAN cukup**. Kalau **belum**, yang ditanyakan bukan cuma
"belum", tapi **4 hal di atas** — dan **itu bisa digali dari naskah BAB I–III
yang sudah ada** (jenis/desain/model/sampel biasanya **sudah tertulis** di
metode penelitian). Jadi: **Jev baca naskah → tarik 4 hal itu → baru dirancang
kuesionernya.** Kalau tidak tertulis, baru tanya user.

### 4.4 ✅ JEMBATAN KE STATISTIK LAB — PUTUSAN BOS 08 Okt 2026 (TERKUNCI)

Prinsip Bos: **satu mesin, dua pintu.** Mesin hitung **SATU** (Statistik Lab),
**FE-nya beda sendiri-sendiri** (EduAi punya FE sendiri, Statistik Lab punya
FE sendiri) — tapi **mesinnya sama**. Pola yang sudah terbukti di EduAi:
`oo-converter` (layanan terpisah, disambung lewat jaringan, bukan impor kode).

**3 PUTUSAN BOS (verbatim + tafsir):**

**(1) Rumah data = EDUAI. Mesin cuma menghitung.**
> *"A karena usernya adalah EduAi maka data asli dan hasil mesin disimpan di
> EduAi. Mesin hanya hitung saja."*

⇒ **Data asli user DISIMPAN DI EDUAI.** Mesin Statistik Lab **TIDAK menyimpan**
apa pun — hanya **terima → hitung → kembalikan hasil**. Hasil mesin juga
disimpan di EduAi.
Selaras aturan lama Bos: **jangan dua salinan** (rumah data = akun user EduAi).

**(2) Yang PARSING = EduAi (AI atau Jev), bukan mesin.**
> *"Ai dari EduAi atau jev yang parsing dahulu menjadi data siap masuk mesin,
> agar mesin statistik lab mudah dan tidak salah deteksi."*

⇒ Urutan: **Jev/AI EduAi membaca & menata** → kirim ke mesin sudah dalam
**bentuk rapi siap hitung** → mesin **tidak perlu menebak** apa pun.
Alasan: mesin Statistik Lab **tidak tahu** mana X/M/Y/Z dan tidak tahu arti
kolom ⇒ **jangan biarkan mesin menebak**.
🧭 Selaras **prinsip induk Bos**: **Jev selalu terdepan** — Jev kenali bentuk
dulu (jenis/desain/model/sampel), baru mesin bekerja.

**Pembagian tugas (kode vs Jev vs mesin):**
| Tugas | Siapa |
|---|---|
| Kenali bentuk naskah, tarik jenis/desain/model/sampel | **Jev** (EduAi) |
| Susun kuesioner + tentukan variabel | **AI EduAi** |
| Rapikan data jadi "data siap masuk mesin" | **kode/AI EduAi** |
| Hitung (regresi/mediasi/uji/tabel) | **MESIN Statistik Lab** |
| Tafsir hasil → tulis BAB IV | **AI EduAi** |
| Simpan data asli + hasil | **EduAi** |

**Pagar WAJIB (usul Wulan, disetujui arah):**
- Data dikirim ke mesin **hanya untuk dihitung**, mesin **tidak menyimpan**
- Jembatan **eksplisit** (panggilan API resmi) — **bukan** impor kode,
  **bukan** pinjam `.env`/kredensial proyek lain
- Mesin **tidak menerima** data mentah yang belum diparsing EduAi
- **Bentuk data** yang dikirim **wajib disepakati dua sisi** (kontrak)
  — pola kolom per-item yang sudah terbukti: `Kualitas_Produk_1`, `Harga_1`, `Y1`…

**Contoh alur lengkap:**
```
user: "naskahku kurang BAB IV"
   ↓ Jev baca BAB I–III → dapat: jenis=kuantitatif, desain=survei,
     model: X1,X2 → Y1 (berganda), sampel: 100 responden UMKM
   ↓ AI EduAi susun kuesioner (X1 5 butir, X2 5 butir, Y1 5 butir)
   ↓ user sebar kuesioner → unggah data lapangan ke EDUAI
   ↓ kode EduAi rapikan → "data siap mesin" (kolom ber-nama, jalur X1→Y1)
   ↓ kirim ke MESIN Statistik Lab (hitung saja, tidak menyimpan)
   ↓ mesin kembalikan: β, p, R², tabel hasil, uji asumsi
   ↓ AI EduAi tafsirkan → tulis BAB IV
   ↓ simpan hasil DI EDUAI
   ↓ Jev/AI periksa hasil → naskah lengkap → konversi artikel jurnal
```

### 4.5 Prasyarat 4 hal — diatur DI EDUAI (putusan Bos)
> *"Atur di EduAi"*

⇒ Siapa yang mengisi **jenis/desain/model/sampel** = **diatur di EduAi**
(bukan di Statistik Lab). Cara teknisnya (Jev tarik dari naskah vs form user)
**belum diputuskan** — tercatat di §6 butir 9.

### 4.6 Ketergantungan pada fitur KONVERSI
Detail BAB IV ini **bergantung** pada fitur konversi artikel jurnal
yang sedang dikerjakan (`SOT_KONVERSI_JURNAL.md`). Rilis konversi
**tidak perlu menunggu** penyelesaian bab.

---

## 5. YANG SUDAH JADI (konteks supaya tidak diulang)

| Bagian | Status |
|---|---|
| Pagar identitas (nama+email) | ✅ ADA — blokir di depan |
| Cek kelengkapan bagian | ✅ ADA (`cek_kelengkapan`) |
| Peta bab oleh Jev | ✅ ADA (`_posisi_dari_jev`, 5 bab benar) |
| Cek "ada bab KESIMPULAN?" | ✅ ADA (`konversi.py:370`) |
| Mesin tulis bab | ✅ ADA (`kerangka.bangun_isi`) |
| Satu dompet token | ✅ ADA (`kuota.potong_banyak`) |
| Rute + tombol revisi (2 token/item) | ✅ ADA & teruji |
| Editor OnlyOffice | ✅ ADA |
| Mesin olah data | ⚠️ ADA di **proyek lain** (Statistik Lab) — kuantitatif saja |

---

## 6. YANG MASIH TERBUKA (untuk bahasan berikutnya)

1. Aturan penentu "utuh": pakai **kata** (ada HASIL + ada SIMPULAN) atau wajib **angka V**?
2. Naskah **kualitatif** kurang bab → diapakan?
3. "Siapkan Penelitian" + "Olah Data": **satu AddOn** atau dua?
4. Harga olah data: AddOn tersendiri vs numpang token?
5. **Bentuk JEMBATAN ke Statistik Lab**: ✅ *arah sudah diputuskan Bos 08 Okt (§4.4)* — mesin hitung saja tidak menyimpan, EduAi yang parsing, data di EduAi. **Bentuk teknis belum**: HTTP API (pola oo-converter)? nama jaringan? nama endpoint? batas ukuran? timeout?
6. Naskah user bayar 15–20 token tapi data lapangannya keliru → alur & charge perbaikan
7. Apakah naskah yang sudah dikonversi (lengkap) bisa **balik** ke jalur lengkapi-bab?
8. Detail tampilan/layar (belum dibuat sketsanya)
9. **4 prasyarat (§4.3)**: siapa yang mengisi — Jev baca dari naskah, atau user isi form? bagaimana kalau naskah TIDAK menuliskannya?
10. **Variabel hasil rancangan** — bagaimana bentuk final kolom data yang mau dibaca Statistik Lab (per-item? nama kolom?), biar dua sisi sepakat
11. Apakah **kuesioner** ikut dihitung token, atau masuk AddOn olah data?

---

## 7. CATATAN WULAN — KEJUJURAN

- **Belum ada kode apa pun** yang ditulis untuk ini.
- **Belum ada sketsa** dibuat.
- Dokumen ini **catatan diskusi**, bukan rancangan teknis, bukan SOT.
- Wulan **tidak** menyentuh proyek Statistik Lab dalam catatan ini —
  hanya menyebut keberadaannya sebagai penghalang.
