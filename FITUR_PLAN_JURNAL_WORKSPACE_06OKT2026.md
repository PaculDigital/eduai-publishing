# 📘 FITUR PLAN — JURNAL, WORKSPACE & PENCARIAN REFERENSI EDUAI

<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> **Status:** 🟢 **TAHAP 1 SELESAI SEMUA (Langkah 1–7) + LIVE** — image
> `eduai-app:20261006_210738-sot` (06 Okt 21:07). Langkah 7 = **sambungan unduh
> PDF → workspace** (dropdown pilihan workspace + tombol di tiap kartu) SUKSES
> deploy, `/health` 200, 13 gerbang 502/0. **2 BUG NYATA ikut dicabut** (unduh
> selalu gagal; halaman Referensi mati untuk semua akun) — rincian di
> `FLAG_LANJUT_DISINI.md` blok atas. **BELUM:** berkas "Link Jurnal.txt"
> (IDE, belum diputuskan) · potret tanda ⚠️ · uji artikel Garuda sungguhan.
> **Tanggal:** 06 Oktober 2026 (diperbarui 06 Okt malam)
> **Berkas ini = SUMBER KEBENARAN** untuk rancangan fitur jurnal/workspace.
> Rincian diskusi ada di `RINGKASAN_DISKUSI_JURNAL_06OKT2026.md` + 41 berkas
> `*_06OKT2026.md`. Laporan koding per langkah: `LAPORAN_TAHAP1_*_06OKT2026.md`.
> ✅ Izin "mulai" dari Bos **sudah ada** (06 Okt 2026).

---

## 🎯 TUJUAN FITUR (kata Bos)

> *"Intinya user bisa lihat hasil Harvest artikel yang AI cari bahwa artikel
> tersebut NYATA, bukan karangan, dan bisa user download jika free to download,
> dan kita katakan berlangganan / paid artikel."*

> *"Satu halaman/file yang berisi link jurnal dari masing-masing workspace."*

> *"Mesin juga harus bisa fleksibel, kalau user mau tambah artikel untuk
> ditambahkan dalam pembahasan bab juga harus bisa, tapi HANYA artikel khusus
> dengan mekanisme mesin yang sudah disediakan. Tidak bisa user upload artikel
> di luar mekanisme dari mesin / liar. Itu untuk menjaga mesin tetap konsisten
> hasilnya."*

**3 pilar:**
1. **Nyata** — user bisa buktikan sendiri artikelnya bukan karangan (buka link, unduh).
2. **Terkelompok** — hasil rapi per variabel/bab, mudah dibaca.
3. **Terpagar** — semua artikel lewat audit mesin; tidak ada jalan masuk liar.

---

## 🧩 BAGIAN 1 — WORKSPACE (PROJECT)

| Hal | Putusan Bos |
|---|---|
| Bentuk | ✅ **SATU TINGKAT** (tidak bersarang) |
| Bisa banyak workspace per user? | ✅ Ya |
| Model | ✅ `folders` **SUDAH ADA** (`models.py`) — **nol tabel baru** |

**Yang perlu dibangun:** tampilan & alur (mesin folder sudah ada, 4 rute hidup).
⚠️ **Temuan: 0 folder di produksi** — belum pernah dipakai user sungguhan.
⇒ Saran Wulan: buat 1 workspace uji dulu sebelum dipakai luas.

---

## 📚 BAGIAN 2 — HARVEST JURNAL (MESIN INI SUDAH LIVE)

| Hal | Keadaan |
|---|---|
| Mesin | ✅ `app/pustaka.py` — **LIVE** |
| Sumber | Scopus ⚠️ (kunci belum ada) · OpenAlex ✅ · Garuda ✅ · CrossRef ✅ |
| Audit DOI | ✅ `audit_doi()` ke CrossRef |
| Daftar pustaka | ✅ `daftar_pustaka_apa7()` (hanya terverifikasi) |
| Pecah judul → variabel | ✅ `konsep_dari_judul()` (**25 konsep**) |
| Link nyata | ✅ `pustaka.py:719` (Garuda) |

### 🔬 BUKTI UJI NYATA (06 Okt 2026)
- Cari "kualitas produk → keputusan pembelian": **35 hasil mentah → 1 lolos** (saringan ketat).
- **Unduh PDF diuji langsung di server:** `status 200`, `content-type: application/pdf`,
  `406.375 byte`, `awalan: b'%PDF-1.5'` ⇒ **PDF SUNGGUHAN, BISA DIUNDUH OTOMATIS.**

---

## 🔎 BAGIAN 3 — DUA JALUR PENCARIAN

| | 🤖 **Auto AI** | 🔎 **Manual (user)** |
|---|---|---|
| Siapa tentukan | AI (dari judul naskah) | User (ketik sendiri) |
| Gunanya | **MENULIS bab** | **MENCARI bahan** |
| Keluaran | bab baru + daftar pustaka | daftar artikel (link) |
| Biaya | **GRATIS sampai kerangka** | **1 token / pencarian** |
| Jatah gratis | — | **2× per minggu** |
| Status | ✅ **SUDAH LIVE** | ❌ **belum ada UI** |

### 🤖 Auto AI — keadaan terukur
| Bagian | Letak | Status |
|---|---|---|
| Mesin cari | `pustaka.cari_semua()` | ✅ |
| Pemakai | `kerangka.py:178` & `:355` | ✅ |
| Susun rencana (GRATIS) | `susun_rencana()` `kerangka.py:158` | ✅ |
| Tulis bab | `bangun_isi()` `kerangka.py:329` | ✅ |
| Endpoint | `ai.py:4092` + `ai.py:4147` | ✅ **LIVE** |
| Tombol | `mulai.html:249` "Susun kerangka BAB I" | ✅ |
| Pagar gagal | `ai.py:4166` → token dikembalikan | ✅ |

⚠️ **"AI rekomendasi judul" = SETENGAH.** Yang ada = `contoh_judul()`
(`alur_awal.py:377`) — **daftar statis per bidang**, **belum pakai AI**.

---

## 💰 BAGIAN 4 — PAGAR PENCARIAN MANUAL (TERKUNCI)

| Hal | Putusan |
|---|---|
| Yang dihitung | pencarian **MANUAL** saja |
| Harga | **1 token per pencarian** |
| Jatah gratis | **2× per MINGGU** |
| Siklus | **sejak awal pemakaian** user (7 hari) |
| Takaran | **1 pencarian = 1 judul/keyword** |
| Lewat 2× | **kena token** |

**Mesin dompet SUDAH ADA:** `saldo.py` (`sisa`, `masuk`, `pakai`, `kembalikan`,
`rincian`) + `kuota.potong_banyak/kembalikan_banyak`. **Nol dompet baru.**
🔴 **Pagar wajib:** hitungan di **SERVER (DB)**, **per user** (bukan per
workspace), **tidak menumpuk**, ada **jejak audit**, harga **selalu tampak**.

---

## 📝 BAGIAN 5 — ARTIKEL MANUAL (FLEKSIBEL TAPI TERPAGAR)

### Bentuk masuk — **2 cara, 1 pintu audit**
```
A. TEMPEL DOI/LINK  ─┐
                     ├─→ AUDIT DOI ─→ ✅ lolos → masuk naskah + daftar pustaka
B. KOTAK ISIAN      ─┘             └→ ⚠️ tidak lolos → tampil jujur, TIDAK dipakai
```
❌ **DILARANG:** upload PDF/berkas liar. Tidak ada tombol unggah artikel.

| Hal | Putusan Bos |
|---|---|
| Sumber diizinkan | ✅ **hanya mesin resmi** (Garuda/OpenAlex/CrossRef/Scopus) + **DOI sendiri** |
| Upload PDF liar | ❌ DILARANG |
| Batas per bab | ✅ **MAKS 8 ARTIKEL (selalu)** |
| Penanda bab | ✅ **YA** (dropdown, user pilih) |
| Artikel belum terverifikasi | ✅ **DITAMPILKAN + user bisa masukkan DOI-nya** |
| Pakai ulang di bab lain | ✅ YA (tanpa hitung dobel) |
| Masuk daftar pustaka? | ✅ YA — asal lolos audit |
| Dipakai sitasi? | ✅ YA |
| Tampil sebelum bayar? | ✅ YA |

### 🔑 Kunci keamanan (terukur)
`daftar_pustaka_apa7()` (`pustaka.py:696`) — syaratnya **status verifikasi,
BUKAN asal artikel**:
```python
if r.get('doi_status') not in ('verified', 'no_doi'): continue
```
⇒ Artikel manual **bisa masuk** asal lolos audit. Dan **`doi_status` hanya
hasil audit — user TIDAK bisa mengisinya** → tidak bisa "mengaku-aku terverifikasi".

⚠️ **TEMUAN — perlu 1 perbaikan:**
`bangun_isi()` (`kerangka.py:354`) masih **cari ulang sendiri** → belum menerima
artikel kiriman. Perlu parameter `artikel_tambahan` (opsional). Kalau kosong →
perilaku lama **tetap persis** (tidak membongkar).

---

## 🖥️ BAGIAN 6 — TAMPILAN (belum dirancang detail)

Usulan Wulan (belum diputuskan):
- Tab **📚 Referensi** di halaman naskah (sejajar Naskah Saya · Kolaborasi · Belajar)
- Di dalamnya **2 bagian**: 🤖 *Pilihan AI* + 🔎 *Pencarian kamu*
- Hasil **dikelompokkan** per variabel/bab
- Tiap artikel: judul · penulis · ✅ NYATA · 🟢 gratis / 🔒 berlangganan · tombol unduh
- Tombol **"Simpan ke workspace"**

---

## 🧭 BAGIAN 7 — YANG TIDAK PERLU (putusan)

| Hal | Putusan | Alasan |
|---|---|---|
| **Jev** di fitur jurnal | ❌ TIDAK PERLU | bidangnya beda (soal **bab**, bukan artikel) + menilai mutu = **zona yang Jev sudah terbukti gagal 3×** |
| Jev di struktur naskah | ✅ sudah jalan | `ai.py:2350` |
| Upload PDF | ❌ DILARANG | merusak konsistensi mesin |
| Kategori folder | ✅ **satu tingkat** | user HP mudah bingung |

---

## 📐 RINGKASAN: YANG SUDAH ADA vs PERLU DIBANGUN

| Fitur | Mesin | UI | Perlu kerja |
|---|---|---|---|
| Workspace (`folders`) | ✅ ada | ✅ 4 rute | tampilan & alur saja |
| Harvest jurnal (`pustaka.py`) | ✅ ada | ❌ belum | **halaman baru** |
| Auto AI kerangka bab | ✅ ada | ✅ LIVE | — |
| Cari manual + token | ✅ dompet ada | ❌ belum | **UI + potong token** |
| Unduh PDF ke workspace | ✅ terbukti | ❌ belum | **UI + simpan berkas** |
| Tambah artikel (2 cara) | ✅ audit ada | ❌ belum | **UI + jalur audit** |
| Penanda artikel per bab | ❌ **belum** | ❌ belum | **kaitan baru** |
| `bangun_isi()` terima kiriman | ❌ **perlu 1 perbaikan** | — | parameter kecil |
| Batas 8 artikel | ❌ belum | ❌ belum | pagar di server |
| Jatah 2×/minggu + audit | ❌ belum | ❌ belum | hitungan server |

---

## 🚦 URUTAN KERJA YANG WULAN USULKAN (belum diputuskan Bos)

1. **Penanda artikel per bab** + pagar **batas 8** (fondasi aturan)
2. **Perbaikan kecil** `bangun_isi()` (terima artikel kiriman)
3. **UI tab 📚 Referensi** (tampilan hasil, 2 jalur, kelompok per variabel)
4. **Pencarian manual + potong token** + jatah 2×/minggu
5. **Tambah artikel manual** (2 cara) + audit
6. **Unduh PDF → workspace** + berkas link jurnal
7. ~~**Workspace tampilan** (satu tingkat)~~ ✅ **SELESAI & LIVE** (06 Okt 21:07) —
   = **sambungan unduh PDF → workspace** (pilihan workspace saat unduh), titip
   di tabel `folders` yang sudah ada. Tampilan kartu folder di `/naskah`
   **sudah ada sejak 15Sep26** — tidak dibangun ulang. Catatan Bos: pilih
   **"sambungkan hasil pencarian jurnal ke workspace"** (Opsi A).

⚠️ Wulan **tidak memilih sendiri** — ini usulan, Bos yang menentukan.

---

## ⚠️ CATATAN JUJUR (batas yang Wulan tidak janjikan)

1. **Scopus tanpa kunci API** → jalur internasional berkurang.
2. **`KAMUS_KONSEP` cuma 25 konsep** → judul dengan istilah baru tidak terkelompok.
3. **Saringan relevansi ketat** (35 → 1) → perlu ditinjau apakah terlalu pelit.
4. **0 folder di produksi** → fitur workspace belum pernah diuji user sungguhan.
5. **Hak cipta:** artikel berbayar **tidak ditembus** — hanya link + tanda 🔒.
6. **"Presisi" ada batasnya** — mesin menyaring; yang menilai mutu akhir = manusia (dosen).
7. **Wulan belum memeriksa** apakah tampilan 3 pilihan "artikel <5" (`Q3`) sudah ada di layar.

---

## 🔗 CARA BALIK (kalau sesi baru)

1. Baca **berkas ini** (FITUR_PLAN) → lalu `FLAG_LANJUT_DISINI.md` blok teratas.
2. Rincian diskusi: `RINGKASAN_DISKUSI_JURNAL_06OKT2026.md`.
3. Putusan: `PUTUSAN_*.md` · IDE: `IDE_*.md` · Jawaban: `JAWABAN_*.md`.
4. **Jangan ukur ulang** apa yang sudah terukur di dokumen ini.
