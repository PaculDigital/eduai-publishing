# 📕 SOT TUNGGAL — FITUR KONVERSI SKRIPSI/TESIS/DISERTASI → ARTIKEL JURNAL (EduAi)

<!-- SOT: SOT TUNGGAL fitur Konversi → Artikel Jurnal (07 Okt 2026). Menggantikan
     CATATAN_DISKUSI_KONVERSI_JURNAL_07OKT2026.md + KESIMPULAN_FITUR_KONVERSI_ARTIKEL_JURNAL_07OKT2026.md
     yang sudah dipindah ke _arsip/pre-gabung-konversi-07okt26/. Status: SIAP DIKERJAKAN, BELUM DIKODING. -->

> **Berkas ini = SATU-SATUNYA sumber kebenaran (SOT) untuk fitur Konversi Jurnal.**
> Menggabungkan: `CATATAN_DISKUSI_KONVERSI_JURNAL_07OKT2026.md` (830 baris diskusi)
> + `KESIMPULAN_FITUR_KONVERSI_ARTIKEL_JURNAL_07OKT2026.md` (kesimpulan/putusan).
>
> **Tanggal gabung:** 07 Okt 2026 (perintah Bos: *"Gabungkan dulu berkas agar SOT dan
> tidak bingung. Kamu laporan sebelum koding"*).
> **Status:** 🟡 **SIAP DIKERJAKAN — DILARANG DIKODING** sampai Bos bilang **"mulai"**.
> Perintah Bos: **LAPORAN DULU sebelum koding.**
>
> **Berkas asal (ARSIP — jangan dibaca lagi, sudah pindah ke sini):**
> - `_arsip/pre-gabung-konversi-07okt26/CATATAN_DISKUSI_KONVERSI_JURNAL_07OKT2026.md`
> - `_arsip/pre-gabung-konversi-07okt26/KESIMPULAN_FITUR_KONVERSI_ARTIKEL_JURNAL_07OKT2026.md`

---

# BAGIAN A — APA YANG DIMINTA BOS

**Ide dasar Bos (verbatim, 07 Okt 2026):**
> *"Saya mau menambahkan Konversi skripsi/tesis/desertasi menjadi jurnal. Seperti harga
> di AddOn EduAi. Jadi naskah yang sudah jadi atau user bisa upload naskah yang sudah
> jadi untuk di proses menjadi jurnal ilmiah dan siap publish."*

**Lanjutan (verbatim):**
> *"Baik kuantitatif dan kualitatif atau literasi review pastikan terdeteksi dan bisa
> dibuat artikel jurnal. Sepertinya buatlah ai untuk ini terwujud."*

**Aturan infografis (verbatim):**
> *"Bagaimana dengan infografis seperti grafik, tabel dan hasil uji. Perlu atau tidak.
> Atau ambil yang penting saja."* → *"Tidak perlu kamu tunjukkan, tapi memastikan ide
> kamu itu masuk dalam sistem prompt ai saja."*

⇒ **INTI:** naskah apa pun → **dikenali JENIS-nya** (KUANTITATIF · KUALITATIF ·
LITERATUR REVIEW) → **dikonversi jadi artikel jurnal siap submit**.

---

# BAGIAN B — ATURAN INFOGRAFIS (WAJIB MASUK SISTEM PROMPT AI, jangan tampil ke user)

| Jenis | Badan naskah | Lampiran |
|---|---|---|
| Tabel deskriptif | ringkas | detail |
| Uji asumsi (normalitas, hetero) | **1 grafik wakil** | semua grafik |
| Uji hipotesis (β, p, R²) | **WAJIB** | — |
| Scatter / plot | hanya kalau periksa pola | sisanya |

- **Badan:** tabel hasil uji + 1 grafik wakil tiap uji.
- **Lampiran:** output mentah SPSS, grafik sejenis (histogram + P-P + Q-Q cukup **satu**).
- Mesin **sudah bisa** membuat grafik ini (SPSS & PLS) — bahan sudah ada.

---

# BAGIAN C — ✅ SEMUA PUTUSAN BOS (TERKUNCI)

## C.1 Pintu & halaman
| # | Hal | Putusan |
|---|---|---|
| 1 | Pintu masuk | **B + A** — halaman sendiri `/artikel` + di dalamnya **tab "Naskah Saya"**. **BENTUK TAMPILAN = PILIHAN A (dua kartu)** — ✅ diputuskan Bos 07 Okt (dari 3 sketsa). |
| 2 | Deteksi jenis | **A** — **OTOMATIS + bisa DITIMPA** user (pola Jev: mesin mengusul, user memutuskan) |
| 3 | Hasil | **A** — **SATU artikel utuh** dari seluruh naskah (per-bab = IDE lama, tidak masuk rilis ini) |
| 4 | Keluaran | **A** — **PREVIEW**, tanpa tombol batal |

## C.2 DUA PINTU, SATU TUJUAN (koreksi Bos, §4.8)
```
Pintu 1: TAB "Konversi" di menu (samping Belajar & Referensi)
         ← untuk yang DATANG BARU (belum punya naskah di situ)
Pintu 2: TOMBOL "Konversi ke Jurnal" di baris naskah
         ← jalan pintas untuk yang SUDAH di dalam naskah
```
⚠️ **MENU DISALIN DI 11 BERKAS** (`naskah.html`, `referensi.html`, `belajar.html`,
`kolaborasi.html`, `mulai.html`, `editor.html`, `batas_sesi.html`, `pengaturan.html`,
`sampah.html`, `setelan_wa.html`, `tidak_bisa_edit.html`).
Usul lama Wulan (CATAT saja, perlu izin terpisah): jadikan `_menu.html` + `{% include %}`
⇒ tambah tab berikutnya = sunting 1 tempat (SOT: satu hal satu tempat).

## C.3 Model bisnis: PAKET dulu → habis → AddOn (koreksi Bos, §4.9)
> Bos verbatim: *"Masalah peneliti dapat 1x konversi dan penerbit dapat 2x konversi itu
> benar namanya paket, setelah paket dipakai dan habis maka bisa beli AddOn terpisah,
> seperti beli addon untuk token, sifatnya."*

| Paket | Konversi dari PAKET | Setelah habis |
|---|---|---|
| Gratis | **0** (tak dapat AddOn, selamanya) | ❌ buntu → upgrade paket |
| Penulis Rp50rb | **0** | beli AddOn Konversi Rp100.000 |
| Peneliti | **1** | beli AddOn Konversi Rp100.000 |
| Penerbit | **2** | beli AddOn Konversi Rp100.000 |

⇒ **`config.py:299-302` SUDAH BENAR** — `peneliti: 1` & `penerbit: 2` **tidak bentrok**.
**NOL perubahan** pada angka itu. (Wulan sempat salah kira "bentrok" — ditarik.)

## C.4 Pola kuota: IKUT BELAJAR (putusan Bos, §4.10)
> Bos verbatim: *"Konversi pola ikut seperti belajar, beli untuk sekali konversi naskah
> lengkap. Perlu pengecekan naskah lengkap atau belum, perlu jev memutuskan mungkin."*

```
1× beli AddOn (Rp100.000) = 1× konversi untuk 1 NASKAH LENGKAP
```
Persis pola `belajar`. **Bukan** saldo token, **bukan** per bab.
⇒ Ikut `sisa_addon(db, uid, 'belajar')` + `_jml_belajar()`.

## C.5 JEV — MAKSud SEBENARNYA (koreksi Bos, §4.11)
> Bos verbatim: *"Maksud saya jev itu, untuk cek saja point point penting yang harus ada
> dalam membuat artikel jurnal, kemudian di verifikasi oleh user serta jika ada yang
> belum lengkap sampaikan, ini belum ada xxx, apakah user mau lanjut? Kalo tidak user
> bisa melengkapi dan jika pakai ai dalam melengkapi maka kena charge point token revisi."*

⇒ **Bos BENAR, Wulan salah 2×** (sempat kira Jev = pintu PENOLAK). Yang benar:
```
Jev  → periksa POIN PENTING artikel (Jev = MATA, bukan HAKIM)
  ↓
"Poin ini belum ada: XXX"
  ↓
USER VERIFIKASI (user yang putuskan, bukan Jev)
  ↓
[Lanjut saja]        → konversi jalan terus
[Lengkapi dulu]      → user lengkapi
   └─ pakai AI       → KENA Token Revisi 💰
```
⇒ **BUKAN pagar — ini PINTU JUALAN.** User tak pernah tertolak; kalau kurang → jadi
token lagi. Persis filosofi: **PAKET = tiket masuk · ADDON = mesin uang**.

### ✅ C.5.1 SKEMA JEV YANG BENAR — `criteria` WAJIB PER-TIPE (07 Okt 2026, TERUKUR)
> 🚩 **DIPERBARUI 07 Okt 2026.** Versi lama bagian ini berbunyi *"SKEMA JEV
> TERTUTUP — HANYA 3 NAMA + 2 TIPE"* — **ITU KELIRU BERAT** dan berbahaya karena
> membuat Jev dihindari padahal mampu. Kebenaran di bawah terukur dari
> `openrouter.ai/api/v1/systemone` **LANGSUNG** (galat Zod UTUH, tidak terpotong).

**Aturan sebenarnya (3 hal):**
```
① NAMA pertanyaan    → BEBAS apa saja (tidak pernah dikirim ke model)
② TIPE               → HANYA 3:  noul  ·  choice  ·  score
③ criteria           → WAJIB PER-TIPE (INI AKAR 503 SEMU):
     noul    ⛔ TIDAK BOLEH ada `criteria`   (bentuk apa pun ⇒ HTTP 400)
     choice  ✅ OBJEK  {'opsi': 'deskripsi'} (WAJIB)
     score   ✅ ARRAY  ['tingkat 0', …]      (WAJIB, 2–10 tingkat)
```

**❌ TIDAK BERLAKU LAGI / DILARANG (pernah membuat 503 semu):**
| Cara lama (salah) | Akibat |
|---|---|
| `noul` + `criteria` (string) | `Invalid input: expected object, received string` |
| `noul` + `criteria` (objek/array) | `invalid_union` — noul memang tak punya field itu |
| `choice` + `criteria` array | `expected record, received array` |
| `choice` + `options` array | `expected record, received undefined` |
| `score` + `criteria` objek | `expected array` |
| tipe karangan (`text`/`bebas`/TANPA type) | tidak dikenal skema |

⇒ Semua bentuk salah di atas muncul sebagai **HTTP 400 Zod** yang **DISAMAR jadi
   HTTP 503** oleh 9router (pesan asli dipotong) ⇒ tampak seolah "Jev/9router rusak".
   **BUKAN kerusakan.** Ini **bug kita**, bukan bug Jev.

**🔴 KESALAHAN WULAN 07 Okt 2026 (JANGAN TERULANG):**
- ❌ *"Skema Jev tertutup, hanya 3 nama"* → **KELIRU**; yang terbatas = bentuk `criteria`.
- ❌ *"Jev tidak stabil / flaky"* → **KELIRU**; penyebabnya salah bentuk, **konsisten 100%**.
- ❌ *"Hanya 2 tipe sah (noul, choice)"* → **KELIRU**; ada **3 tipe** (+ `score`).
- ❌ *"Panjang state penyebab gagal"* → **KELIRU**; **24.000 kar LULUS** (terukur).
- ❌ *"Rate limit"* → **KELIRU**; **10× tanpa jeda = LULUS semua** (terukur).

🧠 **ATURAN INDUK:** Jev membalas **503/400** ⇒ **PERIKSA BENTUK `criteria` DULU**.
   Jev menjawab "tidak ada" padahal ada ⇒ **PERIKSA BAHANNYA DULU**.
   **JANGAN menuduh Jev.** (Dua-duanya pernah terjadi dan dua-duanya salah Wulan.)

⇒ **Rujukan resmi:** skill **`typesafe-jev`** (12 berkas dokumentasi `docs.typesafe.ai`
   + skrip pembaru). Dokumentasi internal proyek **BUKAN** acuan soal kemampuan Jev.
⇒ **Penjaga otomatis:** `_gerbang_skema_jev.py` (34 asersi) + `_uji_gigi_skema_jev.py`
   (5 suntikan, semua TERTANGKAP) memastikan bentuk salah **tidak bisa masuk**
   ke `satpam.TANYA`, `konversi.PERTANYAAN_PETA`, `ELEMEN_MUTU`, `BAGIAN_WAJIB_JEV`.
⇒ **Pagar kode:** `satpam._periksa_skema()` dipanggil `tanya_bebas()` &
   `tanya_bebas_mutu()` — gagal-cepat (`raise ValueError`) sebelum ke jaringan.
⇒ Jev **TIDAK memblokir** — mati/ragu ⇒ konversi TETAP jalan pakai peta mesin;
   beda pendapat ⇒ **LAPOR** angka, **USER** yang putuskan.
⇒ Jev dipanggil **SETELAH pagar ①②③**.
⇒ BUKTI NYATA (naskah Asih, 07 Okt): Jev **0,8 detik** untuk **5 pertanyaan
   campur (choice+noul+score)**, 9.000 kar ⇒ jenis `kuantitatif` conf **1,00** ·
   abstrak 0,93 · pustaka 0,92 · metode 0,96 · pembahasan 0,96 — **semua BENAR**.

### 🚀 C.5.2 JEV DIPERLUAS — PERIKSA MUTU ARTIKEL (optimasi 07 Okt, putusan Bos)
> Bos verbatim: *"user bayar mahal, masa kita tidak kasih yang berbayar juga."*

Jev **tidak lagi cuma peta bab**. Sekarang juga **memeriksa KEBERADAAN 11 elemen
mutu (JEMT) + 7 bagian wajib IMRAD** = **18 poin** dalam SATU panggilan.

| Hal | Nilai (terukur atas naskah Asih, 07 Okt) |
|---|---|
| Model asli | `typesafe/jev-1.13-20260917` |
| Waktu | **0,87 detik** |
| Biaya | ~Rp 0,0002 (input 546 tok · output 234 tok) |
| Hasil | skor **0,71** · **2 kurang** · 4 perlu diperiksa |

**Tipe pertanyaan yang sah = `noul` · `choice` · `score`** (lihat §C.5.1 untuk
bentuk `criteria` per-tipe — **jangan menulis `criteria` pada `noul`**).

**🔎 CACAT BESAR YANG KETEMU (dan dicabut) — BAHAN salah, bukan Jev:**
Bahan lama pakai `satpam._susun_state()` = **peta bab saja** (1.905 kar) ⇒
**ABSTRAK & DAFTAR PUSTAKA TIDAK IKUT** (ada di depan/belakang, di luar bab)
⇒ Jev bilang *"tidak ada abstrak"* (0,10) **padahal naskah Asih PUNYA**.
⇒ **Obat**: `_bahan_mutu()` = AWAL naskah (abstrak+hook) + awal tengah +
AKHIR naskah (kesimpulan+pustaka). Hasil: abstrak **0,10 → 0,82**,
daftar pustaka **0,34 → 0,92**, skor **0,58 → 0,71**.
🧠 **PELAJARAN: Jev jawab salah ⇒ PERIKSA DULU BAHANNYA sebelum menuduh Jev.**

**🔒 BATAS: Jev LAPOR, bukan hakim.** Ambang: `<0,35` = kurang · `0,35–0,50` =
**ragu** (jangan diklaim apa pun) · `≥0,50` = ada. Jev **TIDAK memblokir**;
kalau mati/ragu → konversi TETAP jalan. Kalimat ke user = *"Poin ini BELUM ADA:
…"* (bukan vonis). Ditutup tawaran **Token Revisi** = **pintu jualan** (pola Bos).

**✅ Uji:** `_gerbang_jev_optimasi.py` **56/0** · uji gigi **4/4 TERTANGKAP**
(Jev-jadi-penghalang · rangkum-memvonis · ambang-dirusak · tipe-karangan).
Wulan **gagal 1×**: menamai `BAGIAN_WAJIB` — **timpa nama mesin `periksa_hasil()`**
⇒ rusak; sudah diganti `BAGIAN_WAJIB_JEV` + gerbang menahannya.

## C.6 TEMPLATE · NADA · PEMERIKSA (3 putusan Bos, §4.12)
> Bos verbatim:
> 1. *"Point penting dalam sebuah artikel jurnal, sudah ada template jurnal sinta 4 atau
>    jemt itu jadi default. Dan juga disediakan jika format dari template user sendiri
>    atau upload template dari user, mungkin beda dengan default kita."*
> 2. *"Kalo user nekat lanjut, padahal tidak komplit atau standar template jurnal, maka
>    diberi pemberitahuan dengan halus dan disarankan untuk diperbaiki dulu, dengan
>    manual atau dengan AI maka (kena token revisi)."*
> 3. *"Pemeriksa point penting dalam naskah untuk menjadi standar template artikel jurnal
>    yang ada, jika belum standar/point belum ada maka ditanyakan ke user untuk perbaiki."*

## C.7 TOKEN: revisi kecil + konversi penuh (putusan Bos 07 Okt, terbaru)
| # | Hal | Putusan |
|---|---|---|
| 1 | Token/AddOn | **C** — **AddOn AI** (revisi kecil) **+ AddOn Konversi Jurnal** (konversi penuh) |
| 2 | Mesin revisi | **Ok** — mesin revisi **dipakai ulang**, petanya jadi **bagian artikel** |
| 3 | Cakupan revisi | **A** — **SEMUA bagian** (abstrak s/d kesimpulan), **utamakan yang belum ada secara 11 elemen mutu** |
| 4 | Jev | **A** — **Jev DIPERLUAS** (kenali 2 bentuk: bab skripsi + bagian artikel, SATU mesin) |
| 5 | **Angka token revisi jurnal** | **1× revisi = 2 token** · dihitung **PER REVISI** (bukan sekali untuk semua). Contoh: revisi Abstrak + revisi Novelty = **2× = 4 token**. |

## C.8 🔒 ANTI "GILING GRATIS" (verbatim Bos)
> *"kalo user batal kan saya rugi dong, tidak bisa batal. tetap preview dan bisa direvisi
> kena token."*

⇒ Token **dipotong saat PREVIEW DIBUKA** (bukan saat unduh) · **TIDAK ADA tombol batal** ·
preview = hasil pertama **SUDAH BAYAR** · mau ubah → **REVISI KENAI TOKEN LAGI**
(rollback HARAM) · notifikasi wajib sebut *"Hasil ini sudah memakai 1 Token Konversi."*

## C.9 🛡️ TEKAN BACK / TAB KETUTUP (jawaban 07 Okt)
**AKAR:** token dipotong **di SERVER saat proses SELESAI** — layar cuma JENDELA.
**3 lapis anti-rugi:**
1. **Hasil LANGSUNG jadi berkas di workspace OTOMATIS** (tidak tunggu tombol unduh) —
   layar preview hanya **MEMBACA** berkas (pola `dokumen_baru`/`_simpan_pdf` LIVE).
2. **Notifikasi + tombol "Lanjutkan"** → *"Artikelmu sudah jadi — buka di /artikel."*
3. **Pagar token:** AI **GAGAL TEKNIS** → `kuota.kembalikan_banyak()` token UTUH ✅ ·
   user **tekan back setelah hasil jadi** → token **tetap terpakai**, hasil AMAN ✅

## C.10 🗑️ HAPUS & KONVERSI ULANG (verbatim Bos)
> *"Ya setuju hapus boleh tapi konfersi lagi tetap bayar lagi atau beli AddOn lagi."*

| Aksi user | Bayar? | Alasan |
|---|---|---|
| **Pulihkan dari Tong Sampah** (≤30 hari) | **GRATIS** ✅ | AI **tidak bekerja ulang** — cuma balik `terhapus_pada = None` |
| **Hapus permanen** lalu konversi lagi | **BAYAR LAGI** | AI kerja ulang dari nol |
| **Konversi ulang / naskah baru** | **BAYAR LAGI** | kuota terpakai |

⇒ **BUKAN jalur gratis-putar.** Salah-klik hapus = aman, tidak rugi token.

---

# BAGIAN D — 🗑️ TONG SAMPAH (verified ke kode 07 Okt)

**✅ SUDAH ADA & LIVE.** ⚠️ **30 hari** — **bukan 60** (Bos sudah mengakui salah sebut).
`app/config.py:267`: `SAMPAH_HARI = int(os.getenv('EDUAI_SAMPAH_HARI','30'))`
⇒ Mau 60 hari → ubah **1 angka** di `.env`, bukan bikin sistem baru.

| Hal | Kenyataan (`app/sampah.py`, `models.py:182–223`) |
|---|---|
| File di disk saat masuk sampah | **TIDAK disentuh** — cuma disembunyikan |
| Siapa bisa pulihkan | **hanya pemilik** |
| Kuota storage | **tetap dihitung** selagi di sampah |
| Backup sebelum hapus permanen | **otomatis** (`backup_db`, simpan 5 terbaru) |
| Cara jalan | **lazy** — dicek saat halaman sampah dibuka (belum ada cron) |
| Halaman & rute | `main.py:957` `/sampah` · `:974` pulihkan · `:1004` kosongkan |

---

# BAGIAN E — 🧩 11 ELEMEN MUTU (dibaca dari `jurnalkit/jemt_prompt.md:50-63` — BUKAN karangan)

| # | Elemen | Section Penempatan | Tanda Keberadaan |
|---|---|---|---|
| 1 | **Hook** | Pendahuluan ¶1 | Bukan definisi, bukan "Di era digital…" — fakta mengejutkan/anekdot/pertanyaan retoris |
| 2 | **State of Art** | Pendahuluan ¶2–3 | Ringkasan riset sebelumnya + sitasi |
| 3 | **Gap** | Pendahuluan ¶4 | Celah yang belum terjawab |
| 4 | **Novelty** | Pendahuluan ¶5 | Kebaruan spesifik (**bukan** "artikel ini bertujuan untuk…") |
| 5 | **Findings** | Hasil & Pembahasan | Hasil utama, satu temuan per sub-bagian |
| 6 | **Critical Analysis** | Hasil & Pembahasan | "Mengapa hasil ini muncul?" — interpretasi, bukan deskripsi |
| 7 | **Diskusi Komparatif** | Hasil & Pembahasan | "Sejalan dengan X…" **+ justifikasi** kemiripan/perbedaan |
| 8 | **Kaitan Teori** | Hasil & Pembahasan | Kembali ke grand theory |
| 9 | **Limitasi** | Kesimpulan ¶1 | Min. 3 keterbatasan **spesifik** |
| 10 | **Rekomendasi Riset Lanjut** | Kesimpulan ¶2 | Spesifik, bukan klise |
| 11 | **Implikasi Teoretis + Praktis** | Kesimpulan ¶3 | Pisahkan implikasi ilmu vs praktisi |

### 🎯 11 ELEMEN ≠ SECTION BARU (hasil cek ⚠️ penting)
```
11 ELEMEN = isi di DALAM section template (NESTED, bukan section baru)
   Hook · State of Art · Gap · Novelty      → DI DALAM "PENDAHULUAN"
   Findings · Critical · Komparatif · Teori → DI DALAM "HASIL DAN PEMBAHASAN"
   Limitasi · Rekomendasi · Implikasi       → DI DALAM "KESIMPULAN"
```
| Pertanyaan | Jawaban |
|---|---|
| 11 elemen = section baru? | ❌ **Bukan** — semuanya di dalam section template |
| Perlu daftar terpisah untuk cek BAGIAN? | ❌ **Tidak** — cukup 1 template |
| Tetap berguna? | ✅ **Ya** — untuk cek **MUTU/ISI** (yang mesin tak bisa) |

---

# BAGIAN F — 📐 FORMAT ARTIKEL (bahan SUDAH ADA, terverifikasi)

**Berkas:** `/opt/data/services/ojs/references/template-jpem-structural.md` (JPEM) —
status: **100% cocok** dengan artikel yang sudah **sukses publish**.

```
1. Judul (KAPITAL)
2. Penulis + instansi + email (superscript 1,2,3)
3. ABSTRACT (EN) + Keywords
4. ABSTRAK (ID) + Kata Kunci
5. PENDAHULUAN
6. METODE PENELITIAN
7. HASIL DAN PEMBAHASAN  ← DIGABUNG
8. KESIMPULAN (tanpa nomor, tanpa referensi)
9. DAFTAR PUSTAKA
```
**Aturan mutlak:** Garamond · A4 margin 2,54 cm · abstrak bilingual ≤200 kata ·
sitasi Chicago 17th (Author-Date) · daftar pustaka APA · plagiarisme maks 30% ·
header JPEM-ISSN-Vol-Hal · footer URL jurnal.

**Bahan lain yang ada:** `_bahan/PEDOMAN_UTUH.txt` (pedoman TA S1 UPB, 8 bab) ·
`ATURAN_SITASI_PEDOMAN_26SEP2026.md` · `ATURAN_FORMAT_PEDOMAN_26SEP2026.md` ·
`jurnalkit/templates/Template-JEMT-Modified-2026.docx` (3,3 MB) ·
`jurnalkit/SOP_JURNALKIT_v11.md`.

**Pilihan template:**
```
DEFAULT → JEMT / SINTA 4 (1 kolom — paling umum untuk pemula; terbukti)
CUSTOM  → user upload template sendiri
```
⚠️ **Upload template = RISIKO** (mirip "upload PDF liar" yang DILARANG). Pagar ringan
(MESIN, bukan AI): cek ada ABSTRAK/PENDAHULUAN/METODE/HASIL/KESIMPULAN/PUSTAKA ·
ekstensi **`.docx` saja** (TOLAK `.dotm/.docm` — macro) · ≤5 MB · gagal → pakai DEFAULT.

---

# BAGIAN G — 👁️ DETEKSI JENIS (kuantitatif · kualitatif · literatur review)

**Aturan putusan Bos:** deteksi **OTOMATIS + bisa ditimpa** user (pola Jev).

**Mesin yang sudah ada:**
| Alat | Berkas | Fungsi |
|---|---|---|
| Kategori jenis | `app/etika.py` (3 kategori: kuantitatif · kualitatif · umum) | ✅ ADA |
| Jenis dokumen | `app/jenis.py:53` (`artikel_jurnal` sudah dikenal) | ✅ ADA |
| Peta bab | `app/satpam.py` (Jev `periksa()`, keyakinan 0,95) | ✅ LIVE `ai.py:2350` |
| Hitung bab | `app/versi.py:157` (`deteksi_bab()`) | ✅ ADA |

**Untuk LITERATUR REVIEW:** tak ada data lapangan — sumber **hanya pustaka**.
⇒ deteksi: tak ada METODE/HASIL lapangan → arahkan ke jalur REVIEW.

---

# BAGIAN H — 🗺️ PETA BAB → BAGIAN ARTIKEL (WAJIB tertulis, bukan ditebak AI)

| Dari skripsi | Ke artikel |
|---|---|
| BAB I panjang (latar belakang 5 hlm) | → **PENDAHULUAN 2-3 paragraf** |
| BAB II kajian teori | → **DILIPAT ke pendahuluan/pembahasan** |
| BAB III metode | → **METODE ringkas** |
| BAB IV hasil | → **HASIL DAN PEMBAHASAN** (TANPA sub-bab 4.1, 4.2) |
| BAB V simpulan | → **KESIMPULAN 1 paragraf** |
| Lampiran, daftar tabel/gambar | → **BUANG** |

⇒ Mesin revisi (`konteks.py`, `parser.py`, alur per-komentar) **DIPAKAI ULANG**.
Yang beda cuma **PETA** (bagian artikel vs bab skripsi).

---

# BAGIAN I — ⚙️ ALUR KERJA LENGKAP (MESIN vs AI)

```
USER pilih naskah → klik [Konversi]
        ↓
┌─── MESIN BEKERJA (GRATIS · PASTI · INSTAN) ───────────────┐
│ 1. BACA    naskah → teks + peta bab (parser SUDAH ADA)    │
│ 2. KENALI  jenjang (jenis.py ADA) + JENIS penelitian      │
│ 3. BANDING bagian naskah vs TEMPLATE                      │
│ 4. LAPOR   "ini ADA, ini BELUM ADA" (layar konfirmasi)    │
└───────────────────────────────────────────────────────────┘
        ↓
   USER LIHAT & PUTUSKAN → [Lanjut] atau [Lengkapi dulu]
        ↓
┌─── AI BEKERJA (bayar: AddOn Konversi / jatah paket) ──────┐
│ 5. TULIS   naskah → artikel (11 ELEMEN = PERINTAH)        │
│            aturan infografis DISISIPKAN ke prompt         │
└───────────────────────────────────────────────────────────┘
        ↓
┌─── CEK HASIL (2 lapis) ───────────────────────────────────┐
│ 6a. MESIN cek BAGIAN hasil (gratis · pasti)               │
│ 6b. JEV cek MUTU 11 ELEMEN → lapor ke user →              │
│     [Lanjut saja] atau [Lengkapi pakai AI = KENA TOKEN]   │
└───────────────────────────────────────────────────────────┘
        ↓
   hasil OTOMATIS jadi berkas di workspace → PREVIEW
```

### 📊 Pembagian tugas
| Tahap | Alat | Biaya | Bisa salah? |
|---|---|---|---|
| 1. Baca naskah | **mesin** (parser) | gratis | tidak |
| 2. Deteksi jenjang/jenis | **mesin** (`jenis.py`, `etika.py`) | gratis | kecil |
| 3. Cek bagian | **mesin** (vs TEMPLATE) | gratis | tidak |
| 4. Tampilkan | **mesin** | gratis | tidak |
| 5. **Tulis artikel** | **AI** (11 elemen = PERINTAH) | AddOn/jatah paket | ya |
| 6a. Cek bagian hasil | **mesin** | gratis | tidak |
| 6b. Cek mutu 11 elemen | **JEV/AI** | token bila perbaiki | ya |

### ❓ Perlu putusan: cek bagian SEBELUM atau SESUDAH konversi?
- **Opsi A SEBELUM:** user tahu sebelum bayar · tapi yang dicek = naskah skripsi (bagiannya beda)
- **Opsi B SESUDAH:** cek yang relevan (artikel) · tapi user tahu setelah bayar
- **💡 Usul Wulan: DUA-DUANYA** — SEBELUM (mesin, gratis): cek naskah SIAP/belum;
  SESUDAH (mesin + Jev): cek HASIL. Alasan: sebelum = tahu sebelum bayar; sesudah = cek yang relevan.

---

# BAGIAN J — 🛠️ MESIN: SUDAH ADA vs BELUM

## J.1 SUDAH ADA (jangan bangun baru — aturan Bos)
| Komponen | Berkas | Status |
|---|---|---|
| Kuota `konversi` per paket | `config.py:299-302` | ✅ 0·0·1·2 sudah BENAR |
| **AddOn `konversi` Rp100.000, kuota 1** | `config.py:339` | ✅ ADA |
| Kolom `jenis` (ai\|konversi\|publish\|belajar) | `models.py:463` | ✅ siap terima `konversi` |
| Jenis dokumen `artikel_jurnal` | `jenis.py:53`, `kerangka.py:64` | ✅ AI sudah tahu |
| Deteksi kategori (kuantitatif/kualitatif) | `etika.py` | ✅ ADA |
| Format JPEM + pedoman | `ojs/references/`, `_bahan/` | ✅ ADA |
| Template JEMT docx | `jurnalkit/templates/` | ✅ ADA (3,3 MB) |
| 11 elemen + SOP | `jurnalkit/jemt_prompt.md`, `SOP_JURNALKIT_v11.md` | ✅ ADA |
| Jev (peta bab) | `satpam.py` | ✅ LIVE `ai.py:2350` |
| Mesin revisi + konteks | `konteks.py`, `parser.py`, `ai.py` | ✅ LIVE |
| Pola simpan berkas | `dokumen_baru.py`, `rute_jurnal.py /unduh` | ✅ LIVE |
| Kuota potong/kembalikan | `kuota.py:487,579` | ✅ ADA |
| Tong Sampah | `sampah.py` | ✅ LIVE (30 hari) |
| Notifikasi | `notifikasi.py`, `setelan.py:122` | ✅ LIVE |

## J.2 ⚠️ BELUM & HARUS DIBANGUN
| Hal | Keterangan |
|---|---|
| **UI `/artikel` + tab** | belum ada (grep `konversi` di luar config/kuota/models = KOSONG) |
| **Prompt "tulis sebagai artikel jurnal"** | belum ada |
| **Halaman konfirmasi** (peta bab, kelengkapan) | belum ada |
| **Jalur AddOn Konversi di `kuota.py`** | ❌ BELUM ADA — 4 fungsi kurang (lihat J.3) |
| **Pemeriksa poin penting** (2 lapis: mesin + Jev) | belum ada |
| **Jev perluasan** (kenali bagian artikel) | belum — Jev sekarang 4 hal struktur NASKAH |
| **Menyisipkan aturan infografis** ke prompt | belum |

## J.3 🔴 TERUKUR KE KODE (07 Okt, dibuktikan dengan perintah grep — bukan klaim)

**Perintah bukti:** `grep -rn "konversi" app/ --include=*.py --include=*.html`
(kecuali `config.py`/`kuota.py`/`models.py`) → **HASIL: KOSONG (exit 1)**.

⇒ Artinya: **kata `konversi` HANYA muncul di 3 berkas itu** — di tempat lain NOL.
Tidak ada modul, rute, template, atau fungsi yang mengerjakan konversi.

### 📋 PETA JELAS: apa yang ADA vs apa yang BELUM

| # | Komponen | Bukti kode (terukur) | Status |
|---|---|---|---|
| 1 | Jatah paket | `config.py:299-302` → `{'gratis':0,'penulis':0,'peneliti':1,'penerbit':2}` | ✅ **ADA** |
| 2 | AddOn harga | `config.py:339` → `'konversi': Rp100.000, kuota 1` | ✅ **ADA** |
| 3 | Kolom DB AddOn | `models.py:459-470`: `pembelian_addon.jenis` (String 40, `# ai \| konversi \| publish \| belajar`), `sisa_kuota`, `kedaluwarsa` | ✅ **ADA** — kolom siap |
| 4 | Tabel `pembelian_addon` | `models.py:459` | ✅ **ADA** |
| 5 | `sisa_addon(db, uid, jenis)` | `kuota.py:86-106` | ✅ **ADA** — generik, sudah terima `'konversi'` |
| 6 | `tambah_addon(...)` | `kuota.py:392` | ✅ **ADA** — generik |
| 7 | `saldo_token` (kantong token) | `kuota.py:461` | ✅ ADA (untuk REVISI, bukan konversi) |
| 8 | `_jml_belajar(db, uid)` | `kuota.py:187-193` | ✅ **ADA** (khusus belajar) |
| 9 | Tabel `belajar_naskah` | `models.py:481` | ✅ ADA (khusus belajar) |
| 10 | Kuota belajar dipotong saat aktivasi | `belajar.py:57-83` `hak_paket()` + `_terpakai()` | ✅ **ADA** — pola "jatah paket + sisa AddOn − terpakai" |
| 11 | **Hitung konversi terpakai** (`_jml_konversi`) | grep `_jml_konversi` = **KOSONG** | ❌ **BELUM ADA** |
| 12 | **Pemakaian konversi disimpan** (tabel baris) | tak ada tabel baris-per-konversi | ❌ **BELUM ADA** |
| 13 | **Fungsi potong kuota konversi** | grep `potong_konversi` = **KOSONG** | ❌ **BELUM ADA** |
| 14 | `ringkasan_kuota` ikut hitung konversi | `kuota.py:180` = `{'jatah_paket': konv_paket}` **saja** — belum ada `aktif`/`sisa` | ⚠️ **SETENGAH** |
| 15 | **Modul mesin konversi** | tidak ada berkas | ❌ **BELUM ADA** |
| 16 | **Rute/UI `/konversi` atau `/artikel`** | `main.py` tak punya rute ini | ❌ **BELUM ADA** |
| 17 | **Prompt "tulis sebagai artikel jurnal"** | `prompts/` tak punya | ❌ **BELUM ADA** |
| 18 | **Pemeriksa poin penting artikel** | tidak ada | ❌ **BELUM ADA** |
| 19 | **Jev periksa bagian artikel** | `satpam.py` hanya 4 hal struktur NASKAH (jumlah_bab, romawi, urutan, kedalaman) | ❌ **BELUM** — perlu ditambah |
| 20 | Deteksi jenis (kuantitatif/kualitatif) | `etika.py` 751 baris (3 kategori) | ✅ ADA (untuk ETIKA, bisa dipakai ulang) |
| 21 | Jenis dokumen `artikel_jurnal` | `jenis.py` 547 baris | ✅ ADA |
| 22 | Template JPEM + JEMT docx | `ojs/references/`, `jurnalkit/templates/` | ✅ ADA |
| 23 | 11 elemen mutu | `jurnalkit/jemt_prompt.md` | ✅ ADA (referensi teks, bukan kode) |
| 24 | Tong sampah | `sampah.py` (30 hari) | ✅ ADA |
| 25 | Editor OnlyOffice | `onlyoffice.py`, `/edit/{fid}` | ✅ ADA (bisa dipakai ulang) |

### 🎯 RINGKASAN JUJUR
```
RANCANGAN/ANGKA-ANGKA : SUDAH LENGKAP ✅ (jatah paket, harga AddOn, kolom DB)
MESIN YANG BEKERJA     : BELUM ADA ❌ (hanya definisi, belum ada logika)
```
**Perkiraan kerja:** meniru pola `belajar` (belajar.py 978 baris untuk 1 fitur penuh),
tapi konversi **lebih besar** dari belajar karena harus: baca naskah utuh → peta bab
(Jev) → tulis artikel (prompt baru) → cek 2 lapis → simpan berkas.
⇒ **Konversi ≈ 1,5–2× pekerjaan Mode Belajar.**

### ⚠️ RISIKO (diukur dari kode, bukan dugaan)

| # | Risiko | Bukti/dasar | Berat |
|---|---|---|---|
| R1 | **`ringkasan_kuota` setengah jadi** — `kuota.py:180` hanya kirim `jatah_paket`, tanpa `aktif`/`sisa` | baris 180 | 🟡 Sedang — UI akan butuh `sisa`; kalau lupa diperbaiki → panel kuota salah tampil |
| R2 | **Nol tabel baris-per-konversi** | grep tabel = kosong | 🟠 **TINGGI** — tanpa tabel, "sudah dipakai berapa" tak terlacak → user bisa konversi berkali-kali tanpa terpotong = **kebocoran uang** |
| R3 | **Jev belum kenal bagian artikel** | `satpam.py:44-88` = 4 hal naskah | 🟠 TINGGI — aturan induk: Jev penjaga STRUKTUR. Kalau dipaksa periksa bagian artikel tanpa ditambah → Jev salah lapor |
| R4 | **Prompt 100+ halaman lewat Cloudflare** | `asisten.py:38` NASKAH_MAKS=40.000 kar (batas 524 terukur) | 🟠 TINGGI — naskah skripsi 118 hlm ≈ 200rb+ kar → **WAJIB bertahap** (`AI_POTONG_KARAKTER=55.000` sudah ada) |
| R5 | **Folder baru tiap konversi → GRATIS buntu** | `config.py:406` FOLDER_PAKET (gratis 3) | 🟡 Sedang — kalau tiap konversi bikin folder, gratis mentok 3× & tak bisa beli AddOn |
| R6 | **Menu disalin di 11 berkas** | terukur §C.2 | 🟡 Sedang — tambah 1 tab = sunting 11 berkas; kelewat 1 → tab hilang |
| R7 | **`pagar_artikel.py` nama mirip** | berkas 118 baris ada | 🟢 Rendah — tapi salah paham = bikin berkas duplikat |
| R8 | **Antrean AI tidak bertahan restart** | memori: pekerjaan mengantre ditandai gagal saat restart | 🟡 Sedang — konversi panjang (mungkin >5 menit) → kalau server restart di tengah, hasil hilang (token sudah terpotong ⇒ harus pakai `kembalikan_banyak`) |
| R9 | **Konversi panjang vs batas 524 Cloudflare** | pola sudah dipakai: `/v1/peta/kerjakan` dibuat LATAR BELAKANG | 🟠 TINGGI — konversi WAJIB latar belakang + polling (pola yang sudah terbukti), jangan tunggu sinkron |

### ✅ YANG TIDAK BERISIKO (sudah terbukti jalan, tinggal dipakai)
- Kuota potong/kembalikan (`kuota.py:487,579`) — teruji
- Simpan berkas + tong sampah (`dokumen_baru.py`, `sampah.py`) — teruji
- Editor OnlyOffice — teruji
- Notifikasi (`notifikasi.py`) — teruji
- Deteksi jenis + peta bab (`etika.py`, `satpam.py`, `jenis.py`) — teruji

---

# BAGIAN K — ⚠️ PAGAR TABRAKAN (jangan bentrok fungsi lain)

| Bahaya | Berkas terancam | Aturan |
|---|---|---|
| Nama modul bentrok | `pagar_artikel.py` (SUDAH dipakai) | **DILARANG** bikin berkas bernama "artikel" baru |
| Halaman bentrok | `main.py` (punya `/`, `/naskah`, `/referensi`, `/mulai`, `/belajar`, `/kolaborasi`, `/sampah`) | Titip di halaman terdekat; halaman baru → route baru |
| 3 jalur kode kembar | — | **SATU** modul, cabang `jenis` — JANGAN 3 modul terpisah |
| Dompet kedua | `kuota.py` (satu kantong) | **DILARANG** dompet/tabel token baru |
| Tabel/kolom baru | `profil_dokumen` (`jurnal_json`, `jurnal_sidik`, `brief_json`) | **TITIP** di kolom ada; perlu kolom → migrasi idempoten `models.py::_migrasi_kolom` |
| Jev ditambah peran | `satpam.py` | Jev tetap **SATU peran** (`periksa()`) — hanya **DIPAKAI** pemanggil baru, **bukan** peran baru |
| Folder baru tiap konversi | `config.py:406 FOLDER_PAKET` (gratis 3 · penulis 10 · peneliti 25) | ⚠️ Kalau tiap konversi bikin folder baru → **paket GRATIS mentok 3×** & gratis tak dapat AddOn = **buntu permanen**. Pilih: **tanpa folder baru** (hasil masuk folder ada) atau **1 folder tetap "Jurnal"** dibuat sekali |

---

# BAGIAN L — 🎯 YANG TIDAK DIUSULKAN (supaya tidak rumit)
- ❌ **Bukan** "pilih dari 20 jurnal" — baru punya 1 template terverifikasi (JPEM/JEMT)
- ❌ **Bukan** agentic (AI bebas pilih sendiri) — konversi butuh **terkontrol**
- ❌ **Bukan** tabel DB baru — kolom `jenis` sudah ada
- ❌ **Bukan** interface "atur template" yang rumit — 1 tombol, 1 hasil
- ❌ **Bukan** janji "pasti diterima jurnal" — kalimat jujur: **"siap submit"**, bukan "pasti publish"

# BAGIAN M — ⚠️ RISIKO YANG WULAN SEBUT (jujur)
| Risiko | Kenapa serius |
|---|---|
| Jurnal tidak menolak karena STRUKTUR | Struktur bisa dibetulkan mesin. Yang bikin ditolak: **kebaruan (novelty)** & kecocokan scope. Mesin **TIDAK BISA** menambah kebaruan |
| Naskah berbeda pemilik | Konversi = satu naskah, banyak template jurnal → pilih dulu jurnal tujuan (JPEM saja dulu) |
| Banyak jurnal = banyak format | Tridarma baru punya 1 template terverifikasi ⇒ mulai dari JPEM SAJA |
| Etika/pengarang | Menambah nama pembimbing di artikel → **putusan Bos**, bukan AI |
| Turnitin 30% | Hasil konversi **tetap** perlu uji kemiripan. Jangan janji "lolos Turnitin" |

---

# BAGIAN N — ✅ 9 PERTANYAAN TERBUKA — **SUDAH DIJAWAB BOS 07 Okt 2026 (TERKUNCI)**

| # | Pertanyaan | PUTUSAN BOS | Arti teknis |
|---|---|---|---|
| 1 | Template awal | **A + upload** | Default **JPEM/JEMT**. User boleh **unggah template sendiri**. WAJIB **deteksi**: benar template atau bukan · **tolak jika mengandung makro** (`.dotm/.docm`) atau bukan template → beri info jelas *"upload bukan template / salah upload"*. |
| 2 | Kuota konversi | **A** | **Sekali jadi**, tidak bisa diulang. **Revisi = bayar Token Revisi lagi.** |
| 3 | Sumber masukan | **A + B** | Naskah dari **EduAi** DAN **unggah naskah luar**. Unggah WAJIB **deteksi keaslian + tolak makro/script berbahaya**. |
| 4 | Bahasa abstrak | **A** | **AI otomatis** menghasilkan abstrak **2 bahasa** (ID + EN). |
| 5 | Nama penulis | **A (PAGAR KERAS)** | Ambil **nama + email DARI NASKAH**. Kalau TIDAK ADA → **user wajib lengkapi dulu, MESIN TIDAK JALAN**. Alasan Bos: *"ini penting"*. ⇒ Pagar WAJIB dipasang **SEBELUM kuota dipakai**. |
| 6 | Pagar uji mirip | **A — TIDAK ikut konversi** | Konversi **boleh langsung** tanpa uji mirip. **Uji mirip (Cek Plagiarisme/Turnitin) = FITUR TERPISAH YANG DIJUAL SENDIRI.** Pola sama: user cek sendiri atau unggah artikel. |
| 7 | Cek bagian | **A — SEBELUM** | Cek kelengkapan **SEBELUM** konversi (mesin vs template, gratis). User tahu sebelum bayar. |
| 8 | Menu 11 berkas | **A — RAPIKAN DULU** | Menu jadi **1 berkas bersama** (`_menu.html`), 11 halaman memanggil. Alasan Bos: *"nanti akan ada fitur baru dari situ juga. Misal fitur Cek Plagiarisme, Konversi buku dll"* → tab baru akan TERUS bertambah. |
| 9 | Token revisi jurnal | **2 token per revisi** | **1× revisi jurnal = 2 token.** Bisa **lebih dari 1×** per jurnal → dihitung **per revisi**. Contoh Bos: revisi Abstrak + revisi Novelty = **2× revisi = 4 token**. |

## 🧩 CATATAN WULAN ATAS PUTUSAN INI (yang harus dijaga saat koding)
1. **Pagar makro = WAJIB** (no. 1 & 3). Ekstensi berbahaya: `.dotm`, `.docm`, `.doc` (macro lama), `.dot`. Hanya `.docx` sah. Cek juga isi `word/vbaProject.bin` di dalam zip (makro tersembunyi).
2. **Pagar nama/email = WAJIB & BLOKIR** (no. 5) — beda dengan pagar bagian (no. 7) yang hanya **memberi tahu**. Yang ini **menghentikan mesin**.
3. **Uji mirip DIPISAH** (no. 6) → jangan disambungkan ke konversi. Nanti jadi fitur/pintu sendiri (bisa satu menu dengan no. 8).
4. **Token revisi = 2 per revisi** (no. 9) → revisi berjalan **per-item** (abstrak, novelty, dll), tiap item = 2 token. Bukan sekali bayar untuk semua.
5. **Urutan pagar:** cek template/makro → cek nama+email → cek bagian (no.7) → konversi (potong kuota) → periksa hasil.

---

# BAGIAN O — ▶️ LANGKAH SESUDAH IZIN "MULAI"

**✅ 9 pertanyaan SUDAH DIJAWAB (Bagian N) — TIDAK ADA yang menunggu lagi.**

**URUTAN KERJA (6 tahap, dari risiko KECIL → BESAR):**

**Tahap 0 — SKETSA HTML** ✅ *sudah dikerjakan 07 Okt*
`_sketsa/sketsa_konversi_jurnal_07okt2026.html` (3 pilihan A/B/C + konfirmasi + hasil) → tunggu Bos pilih.

**Tahap 1 — KUOTA (fondasi, risiko sedang)** ✅ *SELESAI & TERUJI 07 Okt*
- ✅ Tabel `konversi_naskah` (`models.py` — salinan pola `BelajarNaskah`)
- ✅ `_jml_konversi()` · `jatah_konversi()` · `potong_konversi()` · `kembalikan_konversi()` · `selesaikan_konversi()`
- ✅ R1 ditutup: `ringkasan_kuota['konversi']` kirim `sisa` (dulu cuma `jatah_paket`)
- ✅ Gerbang `_gerbang_konversi_kuota.py`: **37 LULUS / 0 GAGAL** · Uji gigi **3/3 TERTANGKAP**
- ✅ Tabel terbukti otomatis dibuat `create_all()` (tes DB salinan: 24→25 tabel)
- ✅ `periksa_kode.sh` EXIT 0 · `sot.py --periksa` EXIT 0
- 📦 Rollback: `_arsip/pre-konversi-tahap1-07okt26/`

**Tahap 2 — MESIN KONVERSI (paling besar)** ✅ *SELESAI & TERUJI 07 Okt — mesin/pagar; panggilan AI sungguhan menyusul di Tahap 5*
- ✅ `app/konversi.py` (491 baris) — modul mesin, SATU modul 3 jalur (kuantitatif/kualitatif/review)
- ✅ `prompts/artikel_jurnal.txt` (192 baris) — prompt IMRAD + 11 elemen + aturan infografis + abstrak 2 bahasa
- ✅ **PAGAR ①** makro/template: `.dotm/.docm/.doc/.dot` DITOLAK + cek `vbaProject.bin` DI DALAM zip
- ✅ **PAGAR ②** nama+email: BLOKIR kalau tak ada (`periksa_sebelum_konversi`)
- ✅ **PAGAR ③** cek kelengkapan bagian — memberi tahu, gratis, tidak memblokir
- ✅ Jev = MATA: pakai ulang `ai._brief_dan_peta` + `state.petakan` (nol mesin baru)
- ✅ Deteksi jenis otomatis + keyakinan (bisa ditimpa user)
- ✅ Pemeriksa hasil lapis-1 (mesin, gratis): bagian wajib + 11 elemen dari `elemen` JSON
- ✅ Gerbang `_gerbang_konversi_mesin.py`: **53 LULUS / 0 GAGAL** · uji gigi **4/4 TERTANGKAP**
- ✅ 3 cacat nyata DITEMUKAN gerbang lalu DIPERBAIKI (regex `\s`, variabel `bagian` bentrok, case-sensitive)
- 📦 Rollback: `_arsip/pre-konversi-tahap2-07okt26/`

**Tahap 3 — PAGAR & PENGEMBALIAN TOKEN**
- AI gagal teknis → `kembalikan_banyak()` · hasil otomatis jadi berkas (anti tombol back)

**Tahap 4 — PEMERIKSA 2 LAPIS + REVISI PER-ITEM**
- Lapis 1 mesin (gratis) · Lapis 2 Jev (11 elemen, perlu diperluas — R3)
- **Revisi PER-ITEM = 2 token tiap item** (no.9) — mesin revisi dipakai ulang

**Tahap 5 — MENU BERSAMA + UI**
- **8A: satukan menu jadi `_menu.html`** + 11 halaman memanggil (izin Bos SUDAH ADA)
- Halaman `/artikel` + tab "Naskah Saya" + tombol di baris naskah (2 pintu)
- **Uji bergigi:** suntik "tab hilang di 1 halaman" → gerbang HARUS GAGAL

**Tahap 6 — GERBANG PENUH + LAPORAN**
- Gerbang bergigi (≥30 asersi), dibuktikan bisa GAGAL kalau dirusak
- `periksa_kode.sh` + `sot.py` EXIT 0 → **LAPORAN ke Bos** → deploy **setelah izin**

**⏭️ TIDAK masuk rilis ini (nanti):** Cek Plagiarisme/Turnitin (no.6 — dijual terpisah) · Konversi buku · konversi per-bab · halaman riwayat konversi.

---

# BAGIAN P — 📌 CATATAN KEJUJURAN & JEBAKAN
- **JANGAN karang daftar poin.** 11 elemen di Bagian E **dibaca** dari `jemt_prompt.md:50-63`.
- **Nilai jual bukan di format** — di **judul + abstrak + kebaruan**. Format bisa disalin mesin; kebaruan tidak.
- **Jangan janji "pasti diterima jurnal"** — itu di luar kendali.
- 🚨 **Gerbang `_gerbang_*.py` WAJIB dijalankan DI DALAM container** (butuh `httpx` + `/app/data/eduai.db`).
- 🚨 **JANGAN pakai pipe** (`| tail`) — menutupi EXIT CODE.
- 🚨 **`docker cp` WAJIB disusul `docker restart`.**
- 🚨 **UPLOAD_DIR = `/app/uploads`** — ambil dari `app.config.UPLOAD_DIR`.
- 🚨 **Mata/vision bisa salah** — verifikasi ke sumber (`document.body.innerText`).
- 🚨 **BROWSER CACHE** ⇒ potret bisa ber-sidik identik; matikan cache.
- 🚨 **`pagar_artikel.py` sudah ada** — ⚠️ namanya mirip tapi **BUKAN** konversi (itu anti-halusinasi saat AI menulis DARI artikel).

---

# BAGIAN Q — 🌉 JEMBATAN BAB KURANG + 🔖 TIKET LOLOS (15–16 Okt 2026) — **LIVE**

## Q.1 Jembatan bab kurang (putusan Bos 15 Okt)
**Masalah:** `cek_kelengkapan()` SUDAH menghitung bab kurang tapi **tidak
dipakai di layar** ⇒ tidak ada jembatan ke perbaikan.

> *"kalo dua duanya muncul user akan bingung dan sistem app EduAi akan kacau
> dalam mengidentifikasi naskah tersebut, bisa error atau salah pilih"*

| Keadaan | Yang tampil |
|---|---|
| Bab kurang | HANYA tombol **"Perbaiki"** → `/kolaborasi`. Mutu & konversi **DISEMBUNYIKAN** |
| Bab lengkap, mutu kurang | **"Tambah elemen (n token)"** + **"Lanjut apa adanya"** |
| Semua lengkap | **"Mulai Konversi"** |

**Harga mutu BERTINGKAT** (koreksi Bagian N no.9 yang dulu seragam 2):
**BERAT 5** (State of Art · Diskusi Komparatif) · **SEDANG 3** (Gap · Novelty ·
Findings · Analisis Kritis · Kaitan Teori) · **STANDAR 2** (Hook · Limitasi ·
Rekomendasi · Implikasi). **Bagian artikel tetap 2.**
Satu sumber: `konversi.py` `TOKEN_ELEMEN` + `token_elemen()`.

**Jaminan:** sudah bayar = **HARUS LOLOS**. Kecuali **trouble** server/AI
⇒ token TIDAK dipotong + beri tahu lembut.
Aturan tampil: `≥0,50` → tidak ditanya · `<0,50` + sudah bayar → tidak ditanya ·
`<0,50` + belum bayar → DITANYAKAN. Ambang `AMBANG_ADA=0,50` `AMBANG_RAGU=0,35`.

## Q.2 Tiket Lolos — Lapis 3 (putusan Bos 16 Okt)
**Pertanyaan Bos:** *"user sudah bayar & dapat kebutuhannya di bab itu, lalu
edit manual / menambah kalimat yang TIDAK merubah makna — lolos atau tidak?"*

⇒ **LOLOS.** Yang dinilai **MAKNA**, bukan huruf. Sidik teks mentah **DITOLAK**
(tidak bisa bedakan "tambah kalimat pendukung" dari "ganti temuan" ⇒ user yang
cuma menyempurnakan akan diminta bayar lagi = TIDAK ADIL).

**Cara kerja:**
1. Revisi sukses ⇒ tulis **tiket** per elemen: `{bab, sidik, waktu}`
2. Konversi ulang ⇒ Jev ditanya **1 pertanyaan CHOICE**: *"masih membahas hal
   yang sama?"* `{sama / beda}`
3. `sama` ⇒ tiket **TETAP** ⇒ elemen **`☑ Done`** (tidak ditanyakan lagi)
   · `beda` / ragu / **Jev mati** ⇒ tiket **BATAL** ⇒ ditanyakan kembali

| Putusan | Nilai |
|---|---|
| Sidik | **1.500 huruf awal bab** dari **naskah asli** |
| Biaya Jev | **GRATIS** (ditanggung EduAi) |
| Tampilan Done | **tetap MUNCUL** dengan tanda `☑ Done`, tanpa checkbox |

⚠️ **PRINSIP AMAN:** Jev mati ⇒ tiket BATAL. Kegagalan teknis **BUKAN** pintu gratis.

**Berkas:** `app/tiket_lolos.py` (BARU) · `konversi.py` ⑤b + `_teks_bab_untuk()`
· `main.py` ④b · `artikel_konversi.html` (`.itm.done`).
**Uji:** 25/0 · 7/0 · 12/0 · Jev NYATA 2/2 tepat (0,5 dtk).
Dokumen rinci: `PUTUSAN_TIKET_LOLOS_LAPIS3_16OKT2026.md`.

## Q.3 Pelajaran uji (16 Okt) — WAJIB DIBACA
- 🚨 **UJI GIGI JANGAN MERUSAK BERKAS PRODUKSI.** Uji lama menimpa template di
  container hidup; crash ⇒ judul `XXX-MATI-XXX` TERTINGGAL. Uji gigi WAJIB
  lewat **salinan** (`/tmp` + `try/finally`).
- 🚨 **Uji yang MEMAKSA variabel template = UJI PALSU.** Uji lama bilang 27/0
  padahal jalur rute mengirim data dari tempat lain. Uji WAJIB lewat **rute
  nyata** (`TestClient`).

---

**Terakhir diperbarui:** 16 Okt 2026 · **Status:** ✅ **LIVE**
(image `eduai-app:20261016_021214-sot`)
**Cara balik:** Bos bilang *"lanjut konversi jurnal"* → baca berkas INI,
Bagian Q paling baru.

