# RENCANA PEMBIMBING AI — VERSI SEDERHANA

<!-- ⚠️ SOT: RENCANA SUDAH TUNTAS — JANGAN PERCAYA "BELUM DIKODE" -->
> # ⚠️ RENCANA INI **SUDAH DIKODE & LIVE** (03 Okt 2026) — BUKAN penentu status.
> 🚩 **PENTING:** baris **"Status: RENCANA — BELUM DIKODE"** di bawah ini
> **SUDAH BASI**. Pembimbing AI **sudah LIVE di produksi** sejak 03 Okt 2026
> (`pembimbing_ai.py` + `rute_pembimbing_ai.py`, disambung `main.py:33,105,106`).
> Berkas ini kini **catatan putusan D1–D9** (rujukan), bukan rencana tertunda.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.

### (Versi ini menggantikan §1.5 "jalur BARU" pada rencana 23Sep26)

**Disetujui Bos:** 02 Okt 2026 · **Status:** RENCANA — BELUM DIKODE
**Versi sebelumnya (usang):** `RENCANA_KOLABORASI_PEMBIMBING_23SEP2026.md`
**Cadangan:** `_arsip/pre-rencana-sederhana-20261002-1444/`

---

## 1. MASALAH DENGAN RENCANA LAMA

Rencana 23Sep26 memuat putusan **C8**:

> *"Jalur lama `/tinjau/<token>` — JANGAN DIPUTUS. Dibuat **jalur BARU** 'Pembimbing_ai'."*

Kata **"jalur BARU"** itulah sumber bahaya. Kalau ditafsirkan *"bikin sistem kedua"*:

| Risiko | Akibat |
|---|---|
| Dua sistem paralel | Yang satu jalan, yang satu tidak → lama-lama bentrok |
| Dua tabel catatan | Data terpecah, laporan tidak sinkron |
| Dua dompet | Dua tempat top-up, dua angka → user bingung |
| Menyentuh dashboard yang sudah jalan | Merusak yang sudah teruji |

**Bos menolak arah ini** (02Okt26, verbatim):
> *"Saya tidak mau merubah atau buat baru, yang ada bisa sinkron dan tidak menjadi penghalang."*

**Kenyataan terukur:** `grep pembimbing_ai` di seluruh `app/` = **KOSONG**.
Rencana lama **murni di atas kertas** — belum ada satu baris kode pun. Tidak ada
yang perlu dibongkar.

---

## 2. PRINSIP BARU — TIGA KALIMAT

> 1. **SATU DOMPET.** Token milik ORANG, bukan milik peran.
> 2. **PERAN MENEMPEL PADA HUBUNGAN**, bukan pada orang.
> 3. **PEMBIMBING = USER DENGAN PAKET `gratis`.** Tidak ada peran baru.

---

## 3. YANG **TIDAK** DIBUAT (ini yang membuat sederhana)

| ❌ Tidak dibuat | Kenapa |
|---|---|
| Role/peran `pembimbing` baru | Role sekarang `client`\|`admin` SAJA (aturan Bos). Paket `gratis` sudah cukup |
| Jatah khusus pembimbing | Paket `gratis` sudah memberi **3 token** — sama seperti mahasiswa |
| Tabel dompet kedua | `saldo_token` (kolom `user_id`) sudah ada & sudah terbukti |
| Tabel catatan kedua | `catatan_pembimbing` (24 kolom) sudah ada & sudah dipakai |
| Sistem login kedua | Tabel `users` + sistem login sudah ada |
| Mesin sorot kedua | `app/sorotan.py` (287 baris) sudah ada & terbukti bergigi |
| Jalur AI kedua | **DILARANG KERAS** — satu pintu 9router |

---

## 4. YANG **DIBUAT** (cuma ini)

| ✔ Dibuat | Ukuran |
|---|---|
| **1 tombol** "Periksa dengan AI" di halaman `/tinjau` | kecil |
| **1 rute** baru di `pembimbing.py` untuk memanggil AI | kecil |
| **Pemakaian `saldo.py`** yang sudah ada (potong dompet pengklik) | **nol kode baru** — pakai fungsi lama |
| **Penulisan hasil AI** ke `catatan_pembimbing` (tabel yang sama) | **nol skema baru** |
| **Saklar ON/OFF** tombol AI (di pengaturan) | kecil |

**Total: 1 tombol + 1 rute + 1 saklar.** Tidak ada yang lain.

---

## 5. CARA KERJA

### 5.0 ⭐ ALAT SAMA: mahasiswa & pembimbing dua-duanya pakai OnlyOffice

**ATURAN BOS (02Okt26, verbatim):**
> *"agar alat sama mahasiswa=Pembimbing alatnya sama onlyoffice hanya pembimbing
> cuma bisa baca atau onlyoffice non aktif semua tombolnya."*

```
MAHASISWA  → OnlyOffice mode 'edit'  → semua tombol HIDUP (bisa tulis & simpan)
PEMBIMBING → OnlyOffice mode BACA    → semua tombol MATI
             ✔ tetap bisa baca naskah ASLI (bukan render ulang)
             ✔ bisa menyisipkan komentar / sorotan
             ✘ tidak bisa mengubah isi naskah
```

**Kenapa ini yang benar:**
- Tidak ada tampilan kedua → **tidak ada yang dibangun ulang**
- Naskah tampil **asli, apa adanya** (bukan hasil render)
- Memakai mesin yang **sudah ada & sudah teruji**

**MESINNYA SUDAH ADA** (`app/onlyoffice.py`):
```python
def tipe_dokumen(nama) -> (documentType, mode):   # mode = 'edit' | 'view'
```
dan config editor:
```python
'edit': mode == 'edit',   'comment': mode == 'edit',
'fillForms': mode == 'edit', ...
⇒ mode='view' → SEMUA False = tombol mati total
```

**WAJIB DIUJI DULU SEBELUM KODE** (belum diverifikasi):
1. Mode 'view' **masih boleh** sisip komentar? Atau perlu `mode='edit'` +
   `permissions.edit=False, comment=True`?
2. Mode 'view' bisa **ditembus** (ganti URL / dev tools)? Tombol mati di layar
   **tidak boleh palsu**.
3. Pastikan OO **tidak dikirimi `url_simpan`** untuk pembimbing (pagar `/oo/simpan`
   hanya menerima token pemilik).

> ⚠️ **CATATAN KOREKSI:** pada diskusi 02Okt26 Wulan 2× menyebut *"pembimbing pakai
> HTML"* — itu **KARANGAN Wulan**, tidak ada di dokumen mana pun. Rencana 23Sep26
> baris 149 hanya menulis *"jendela PEMBIMBING (terkunci: lihat+komentar)"* tanpa
> menyebut alat. Aturan yang berlaku = **alat SAMA (OnlyOffice)**, seperti di atas.

### 5.1 Alur pembimbing

```
1. Mahasiswa kirim link undangan          ← SUDAH ADA
2. Pembimbing klik link → lihat naskah    ← SUDAH ADA
3. Pembimbing klik kalimat → sorot + catat ← SUDAH ADA
4. Pembimbing klik "Periksa dengan AI"     ← ★ BARU
     ├─ BELUM punya akun → registrasi (email + sandi)
     │     → jadi user paket 'gratis' → dapat 3 token
     ├─ SUDAH punya akun → langsung jalan
     └─ AI baca naskah → temuan masuk sebagai catatan + sorotan
5. Pembimbing bisa HAPUS temuan AI kalau tidak setuju
6. Naskah mahasiswa TIDAK PERNAH tersentuh          ← putusan C3
```

### 5.2 Satu dompet, dua peran — TIDAK PERLU ATURAN APA PUN

```
Dr. Andi — 1 akun, paket 'gratis', 1 dompet (3 token)

  Pakai di naskah SENDIRI    → potong 1 → sisa 2   (peran: mahasiswa)
  Pakai periksa naskah Budi  → potong 1 → sisa 1   (peran: pembimbing)

⇒ Bebas dipakai ke mana saja, sesuai keinginan Bos.
   Tidak ada percabangan anggaran. Tidak ada jatah terpisah.
```

**Peran dihitung SAAT ITU JUGA** dari pertanyaan sederhana:
*"Ini naskah siapa?"* → naskah sendiri = mahasiswa · naskah orang lain = pembimbing.

---

## 6. PERBANDINGAN: RENCANA LAMA vs VERSI SEDERHANA

| Aspek | Rencana lama (23Sep26) | Versi sederhana (02Okt26) |
|---|---|---|
| Jalur | "jalur BARU Pembimbing_ai" | **Tambah tombol di jalur `/tinjau` yang ada** |
| Peran | Bikin peran `pembimbing` | **Tidak ada** — pakai paket `gratis` |
| Dompet | (2 tab, 2 dompet) | **SATU** — `saldo_token` yang ada |
| Jatah | "1× per akun" (usang) | **3 token** — paket `gratis` (kode sudah begini) |
| Dashboard | Diubah jadi 2 TAB | **Tidak disentuh** |
| Kode baru | Banyak | **1 tombol + 1 rute + 1 saklar** |
| Risiko | TINGGI | **RENDAH** |

---

## 7. PUTUSAN BOS 02Okt26 (menggantikan bagian terkait di 25Sep26)

| # | Putusan | Menggantikan |
|---|---|---|
| **D1** | **BUKAN "jalur baru"** — cukup **TAMBAH tombol AI** di jalur `/tinjau` yang sudah ada | C8 |
| **D2** | Catatan AI masuk ke **TABEL YANG SAMA** (`catatan_pembimbing`) — satu tabel, sederhana | §1.5 "2 TAB" |
| **D3** | **SATU DOMPET** (`saldo_token`) — token milik ORANG, bebas dipakai 2 peran | C1d, C7 sebagian |
| **D4** | Pembimbing = **user paket `gratis`** (3 token) — TIDAK ada peran/jatah/dompet baru | C1b, C1d |
| **D5** | 🔴 **HAPUS** aturan lama *"jatah AI 1× per akun"* — **usang**, bertentangan dengan kode (3) | C1d |
| **D6** | Dompet pembimbing = dompet sendiri (otomatis, karena akunnya sendiri) — sesuai jawaban Bos | C7 |
| **D7** | ⭐ **ALAT SAMA**: mahasiswa & pembimbing **dua-duanya pakai OnlyOffice** — pembimbing mode baca. **BUKAN HTML.** | §1.5 "jendela berbeda" |
| **D8** | ⭐ **SINGLE SOURCE OF TRUTH**: satu editor, satu halaman, satu mesin token, satu pagar. **TIDAK ada HTML/berkas tampilan kedua.** | §1.5 konsep lama |
| **D9** | **Naskah orang lain TIDAK disimpan** di akun pembimbing — tidak ada salinan; naskah tetap **satu** di folder pemiliknya | (penegasan) |

**Yang TETAP berlaku dari 25Sep26** (tidak berubah):
- **C1** — pembimbing klik link langsung tanpa daftar; daftar hanya saat klik AI
- **C1c** — akun PER ORANG (per email); daftar 1× untuk semua mahasiswa
- **C2** — naskah milik mahasiswa; mahasiswa tidak perlu tahu dosen pakai AI
- **C3** — 🔴 AI **LIHAT + KOMENTAR SAJA**, tidak sama sekali mengubah naskah
- **C4** — harga disamakan AddOn AI mahasiswa (1 daftar harga)
- **C5** — catatan AI langsung masuk (tanpa persetujuan dulu)
- **C6** — undangan selalu pembimbing (lihat + komentar)

---

## 7b. ⭐ ATURAN SINGLE SOURCE OF TRUTH (D8) — RINCIAN

**Bos (02Okt26, verbatim):**
> *"Jadi ketika jadi mahasiswa tetap pakai onlyoffice edit / load naskah sendiri, dan
> ketika jadi Pembimbing, pakai onlyoffice dan load naskah orang lain + read only.
> Jadi resource sama, tidak ada html dll. Single source of truth"*

```
                         SATU SUMBER KEBENARAN
  ┌──────────────────────────────────────────────────────────┐
  │  1 EDITOR  (oo-converter)          ← tidak berubah        │
  │  1 HALAMAN (/edit/{fid})           ← tidak berubah        │
  │  1 MESIN TOKEN (_token_berkas)     ← tidak berubah        │
  │  1 PAGAR   (/oo/simpan cek pemilik)← tidak berubah        │
  │  1 TABEL   (users, saldo_token)    ← tidak berubah        │
  └──────────────────────────────────────────────────────────┘

  YANG BEDA hanya 2:
     · mode editor  ('edit'  vs  'view')
     · token siapa yang dipakai
```

**Dua mode pemakaian:**

| | MAHASISWA | PEMBIMBING |
|---|---|---|
| Naskah yang dimuat | **milik sendiri** | **milik orang lain (diundangkan)** |
| Mode OnlyOffice | `edit` (tombol hidup) | **baca** (tombol mati) |
| Token berkas | `_token_berkas(fid, PEMILIK)` | `_token_berkas(fid, PEMBIMBING)` |
| Bisa simpan? | ✅ ya | ❌ **tidak** — pagar menolak otomatis |

### Kenapa pagar simpan otomatis menolak pembimbing

```python
# yang ADA sekarang (main.py:1553 & 2089) — TIDAK PERLU DIUBAH
def _token_berkas(fid, user_id):
    pesan = f'{fid}:{user_id}'          # 2 angka: berkas + SIAPA
    return hmac(SECRET_KEY, pesan)[:40]

# pagar /oo/simpan:
if _token_berkas(kandidat.id, kandidat.user_id) == token:   # ← hanya PEMILIK
⇒ token pembimbing (fid, PEMBIMBING) TIDAK PERNAH cocok ⇒ 403
```

**Jadi: NOL kode baru untuk pagar simpan.** Pagar lama sudah benar.

### Jebakan yang WAJIB dijawab sebelum kode

| # | Jebakan | Kenapa penting |
|---|---|---|
| J1 | **Token berkas mengunci ke PEMILIK, bukan pembaca.** Token yang sama membuka `/oo/unduh` DAN `/oo/simpan`. | Bagus untuk pagar simpan, tapi `/oo/unduh` untuk pembimbing **belum ada** → harus dibuat aturan baru, tetap dengan mesin token yang sama |
| J2 | **OO butuh `url_simpan`, kalau kosong bisa protes.** Config sekarang **selalu** dikirimi `url_simpan`. | Dulu pernah muncul modal "Unduhan gagal" (bug 30Sep26). Pembimbing harus tetap dikirimi URL simpan — URL yang **menolak** dia, bukan URL kosong |
| J3 | **Mode baca vs komentar.** OO punya 2 cara: `mode='view'` (semua mati **termasuk** komentar) vs `mode='edit'` + `permissions.edit=false, comment=true` (baca+komentar hidup, tulis mati) | Harus dipilih yang benar: pembimbing **harus bisa** komentar + sorot (itu inti fiturnya) |
| J4 | **Jangan sampai `/oo/unduh` pembimbing jadi pintu terbuka** — token pembimbing hanya sah untuk naskah yang **memang diundangkan** ke dia | Kalau bocor → semua orang bisa baca naskah siapa pun |
| J5 | **Tombol mati tidak boleh palsu** — harus ditolak di **server**, bukan cuma di tampilan | Pelajaran MASTER_PLAN §4.12 (Lapis 1 UI bisa dilewati) |



---

## 8. EMPAT PAGAR (supaya tidak jadi bencana)

### Pagar 1 — FAIL-SAFE
AI hanya **menulis baris baru** ke `catatan_pembimbing`. Jalur lama **tidak
bergantung** pada AI sama sekali. Kalau AI rusak/dimatikan → jalur lama **tetap
100% jalan**. *Analoginya: AI itu penumpang — kalau penumpang sakit, mobil tetap jalan.*

### Pagar 2 — SAKLAR ON/OFF
Tombol AI bisa dimatikan dari pengaturan. Mati → kembali seperti sekarang
**tanpa bongkar kode**.

### Pagar 3 — NASKAH TIDAK PERNAH DISENTUH (putusan C3)
AI hanya menghasilkan **catatan + sorotan**. AI memakai mesin `sorotan.py` yang
sudah ada — **tidak bikin pencari sendiri**.

### Pagar 4 — GERBANG UJI WAJIB BUKTIKAN "YANG LAMA MASIH JALAN"
Setiap perubahan, gerbang wajib membuktikan **DUA hal**:
1. AI jalan
2. **jalur lama (sorot + catatan manual) masih 100%**

Kalau nomor 2 rusak → **deploy DIBATALKAN**.

---

## 9. YANG SUDAH TERBUKTI ADA (bukan asumsi — terukur 02Okt26)

| Benda | Bukti |
|---|---|
| `saldo_token` per `user_id` | kolom: `id, user_id, jumlah, sisa, sumber, catatan, order_id, dibuat` |
| AI pembimbing pernah jalan & potong dompet | baris nyata di DB: `sumber='asisten_pembimbing'`, catatan *"Asisten tinjauan Tab Kolaborasi"* |
| Paket gratis = 3 token | `KUOTA_PAKET['gratis']['revisi'] = 3` (`config.py:284`) |
| Tabel users siap | kolom `email, password_hash, nama, paket, role, aktif, …` |
| Mesin sorot | `app/sorotan.py` — 287 baris; uji: `utuh` (0–93) & `hilang` ✅ |
| Tab kolaborasi (pembimbing) | LIVE sejak 27Sep26 (`app/kolaborasi.py`), gerbang 17/0 |
| Jalur `/tinjau` | LIVE; 6 rute; 21 undangan; 9 catatan di DB |

---

## 10. BELUM DIPUTUSKAN (perlu keputusan Bos nanti)

1. **Bentuk catatan AI** — Wulan usul campuran 3 corak:
   (A) menunjuk lokasi + masalah · (B) temuan lintas-bab · (C) pertanyaan bernada bertanya.
   AI **TIDAK** menulis ulang kalimat.
2. **Nama tombol** yang dilihat pembimbing: *"Periksa dengan AI"* / *"Bantu periksa"* / lain?
3. **Apakah pembimbing melihat catatan mahasiswa** — putusan awal: **ya** (satu tabel).
4. **"Disembunyikan" (C8) maksudnya apa** — dari menu? dari mahasiswa? perlu diperjelas.

---

## 11. CARA BALIK (kalau nanti dikerjakan)

1. Baca berkas ini.
2. Baca `FLAG_LANJUT_DISINI.md` → cari blok Pembimbing AI.
3. **SEBELUM kode:** cek 3 hal yang belum dipastikan (lihat §12).
4. **Saat kode:** rancang → jelaskan ke Bos → Bos putuskan → baru kerjakan.
5. **Saat deploy:** backup `_arsip/pre-<topik>-<tgl>/` + MD5 → `bash jalankan.sh` → gerbang.

---

## 12. YANG WAJIB DIUJI DULU SEBELUM MENGKODE (5 jebakan §7b)

---

## 12b. 🔴 HASIL UJI 03Okt26 — 2 TEMUAN YANG MENGUBAH RENCANA

**Perintah Bos:** *"Ok lakukan uji yang benar"* lalu *"Ok lanjutkan"* (uji lewat produksi).
**Alat uji:** `_sketsa/uji_mode_baca.py` (dalam container) · `_sketsa/uji_lewat_produksi.py` (**terbukti**, via domain) · `_sketsa/layar_uji_host.py` (layar — macet).
**Status: ✅ TUNTAS untuk pertanyaan inti** (pagar simpan + permission) — sisa 1: banding visual V1 vs V2 (tidak mendesak, lihat bawah).

**RINGKASAN 1 BARIS:**
```text
Pembimbing TIDAK bisa menembus simpan (403 di SERVER) ✅
mode='view' bikin tombol mati TAPI komentar juga mati ⚠️
Tidak perlu mesin baru — cukup 1 parameter masukan ✅
```

### ✅ YANG TERBUKTI (dari dalam mesin + LEWAT PRODUKSI 03Okt26)

| # | Uji | Hasil |
|---|---|---|
| A1 | mode `edit` → permissions | `edit=true`, `comment=true` ✅ |
| A2 | mode `view` → permissions | `edit=false`, **`comment=FALSE`** ⚠️ |
| A3 | `callbackUrl` (url_simpan) | **SELALU dikirim** OO ✅ |
| A4 | token pemilik vs token pembaca | **BERBEDA** ✅ |
| **A5** | **PAGAR SIMPAN di SERVER (via domain)** | **pemilik → 200 `{'error':1}` · pembaca → 403 `'Token tidak valid'`** ✅✅ |
| A6 | OO hidup | judul `ONLYOFFICE Document Editor`, badan 324.154 aksara ✅ |
| A7 | berkas inti OO | index.html · app.js · app.css · sdk-all.js **semua 200** ✅ |
| A8 | `semua_permission_ikut_mode_edit` | **TRUE** — 6 permission ikut satu nilai `mode` ✅ |

**⇒ A5 = bukti TERKUAT:** pagar simpan bekerja **di server**, lewat **domain
produksi**. Pembimbing **tidak bisa** menembus dengan ganti URL. Jebakan J1 & J5
**TERTUTUP**.

### 🔴 TEMUAN 1 — `mode` DIHITUNG di dalam, bukan diterima sebagai masukan

```python
# app/onlyoffice.py::konfigurasi_editor()
# parameter masuk : kunci, nama, url_unduh, url_simpan, user_id, user_nama, extensi
# variabel lokal  : dok_tipe, mode, cfg
def konfigurasi_editor(*, kunci, nama, url_unduh, url_simpan,
                       user_id, user_nama, extensi):
    dok_tipe, mode = tipe_dokumen(nama)   # ← mode dari EKSTENSI
```

**⚠️ KOREKSI:** catatan awal Wulan *"TIDAK punya parameter mode"* **KURANG
TEPAT**. Yang benar: `mode` **ADA** sebagai variabel di dalam fungsi, tapi
**BUKAN parameter masukan** — ia dihitung dari ekstensi. `.docx` **selalu**
`edit`.

**⇒ YANG DIBUTUHKAN:** tambah **parameter masukan** (mis. `mode_baca: bool =
False`), bukan membuat mesin mode baru. Klaim *"nol kode"* tetap **BATAL** —
tetap ada titik sentuh kode, tapi **kecil & jelas**.

### 🔴 TEMUAN 2 — `mode='view'` MEMATIKAN KOMENTAR

```text
mode='view' → permissions: edit=false, comment=FALSE
                              ^^^^^^^^^^^^^^^^^^^^^^^^
              pembimbing TIDAK BISA komentar
              padahal komentar = INTI fiturnya
```

**⇒ SOLUSI BENAR:** pembimbing **bukan** `mode='view'`, melainkan:

```python
mode = 'edit'                          # editor hidup
permissions.edit = False               # ← TULIS MATI
permissions.comment = True             # ← KOMENTAR HIDUP
permissions.review = True              # ← usul perubahan hidup
permissions.fillForms = False
permissions.modifyFilter = False
permissions.modifyContentControl = False
```

**Varian inilah (`V2`) yang wajib dipakai untuk pembimbing** — bukan "matikan
semua tombol" seperti dugaan awal.

### ❌ BELUM TERBUKTI (jujur — jangan dianggap selesai)

```text
1. Perbandingan V1 vs V2 DI LAYAR (tombol mati? komentar hidup?) → BELUM
   (uji lewat produksi sudah dicoba untuk pagar; banding visual belum)
```

**SEBAB:** lingkungan uji CDP **cacat** — toolbar OO berhenti di *skeleton*
walau semua berkas 200 & OO hidup. 7 lapis jebakan ditemukan (semua tercatat
di `_sketsa/`), lapis ke-7 (asal `172.17.0.3` bukan hostname sah) **belum
tertembus**. Produksi tidak mengalami ini karena asalnya `eduai.bikinaja.id`.

**YANG SUDAH DIBUKTIKAN LEWAT PRODUKSI (03Okt26, tanpa menambah berkas apa pun):**
A5 (pagar simpan 403) + A8 (6 permission ikut satu mode) — pakai rute yang
SUDAH ADA (`/oo/simpan/{token}`), jadi **tidak ada berkas uji di produksi**.

**SISA 1 LANGKAH:** banding visual V1 vs V2 di layar. Bisa dilakukan nanti
saat fitur benar-benar dikode (uji penerimaan), **tidak perlu memaksa
sekarang** — karena A8 sudah membuktikan keenam permission ikut satu nilai mode.

### 5 JEBAKAN ALAT UJI (tercatat supaya tidak terulang)

| # | Jebakan | Pelajaran |
|---|---|---|
| 1 | `tab_baru()` TIDAK navigasi | WAJIB `Page.navigate` sendiri |
| 2 | Browser uji tak punya internet keluar | layani berkas dari server sendiri |
| 3 | iframe minta `/documenteditor/…` | jalur benar `/web-apps/apps/…` |
| 4 | OO **302** ke jalur **berversi** | ikuti redirect (`fetch` `redirect:'follow'`) |
| 5 | beda asal → Chrome tahan iframe | halaman uji WAJIB satu asal dengan OO |

---

## 12c. UJI 5 HAL SEBELUM KODE (daftar asli)

**UJI 3 HAL (perintah Bos 02Okt26 — kerjakan SEBELUM kode):**

1. **Mode baca: tombol benar-benar MATI?** — buka naskah dalam mode baca,
   lihat dengan MATA apakah toolbar benar-benar non-aktif. *(J3, J5)*
2. **Komentar & sorotan masih bisa dipakai di mode baca?** — kalau `mode='view'`
   mematikan komentar, harus pakai `mode='edit'` + `permissions.edit=false,
   comment=true`. *(J3)*
3. **Pagar simpan memblokir di SERVER, bukan cuma tampilan?** — coba akali simpan
   dari sisi pembimbing; harus **ditolak**. *(J1, J5)*

**Tambahan yang wajib dipastikan saat mengkode:**

4. **Registrasi dari halaman `/tinjau`** — bisa memanggil alur registrasi yang ada
   tanpa mengganggu alur mahasiswa? *(C1, C1c)*
5. **Dompet yang dipotong = dompet PENGLIK** (pembimbing), bukan pemilik naskah.
   *(C7 / D6)*
6. **`/oo/unduh` pembimbing hanya sah untuk naskah yang diundangkan ke dia.** *(J4)*
7. **Gerbang "yang lama masih jalan" harus BERGIGI** — uji dengan sengaja merusak
   (seperti gerbang bahasa dokumen 02Okt26 yang terbukti menangkap).
8. **`url_simpan` tetap dikirim ke OO untuk pembimbing** (URL yang menolak), jangan
   dikosongkan → hindari modal "Unduhan gagal". *(J2)*
