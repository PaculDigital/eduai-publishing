# 🤖 JALUR AUTO AI (HARVEST OTOMATIS) — CARA KERJA & USULAN (06 Okt 2026)

> Pertanyaan Bos 06 Okt 2026 (verbatim):
> *"Kemudian itu kita bahas yang pencarian manual. Untuk pencarian auto dengan
> AI bagaimana?"*

---

## ✅ TEMUAN BESAR: **AUTO HARVEST SUDAH JALAN** (bukan rencana)

Wulan cek langsung ke kode — **bukan dugaan**. Ini yang Wulan temukan:

### Pipa Auto AI yang SUDAH HIDUP

| Bagian | Letak | Keadaan |
|---|---|---|
| Mesin cari artikel | `pustaka.cari_semua()` | ✅ 4 sumber + audit DOI |
| **Pemakainya** | `kerangka.py:178` **dan** `kerangka.py:355` | ✅ **SUDAH DIPANGGIL** |
| Nama fungsinya | `susun_rencana()` (`kerangka.py:158`) | ✅ "TAHAP 2 — RENCANA (GRATIS, 0 token)" |
| yang menerima hasil | `bangun_isi()` (`kerangka.py:329`) | ✅ menulis bab pakai artikel itu |
| Endpoint | `ai.py:4092` (`susun_rencana`) + `ai.py:4147` (`bangun_isi`) | ✅ **LIVE** |
| Tombol di layar | `mulai.html:249` **"Susun kerangka BAB I →"** | ✅ **ADA** |

### Alur Auto AI yang sudah jalan sekarang

```
User tulis JUDUL / tema
        ↓
TAHAP 2 — susun_rencana()   ← GRATIS (0 token)
   ├─ cari artikel NYATA (pustaka.cari_semua → audit DOI)
   ├─ ambil kerangka baku bab
   └─ laporkan perkiraan biaya + pagar artikel-sedikit
        ↓
User lihat rencana → tekan "Setuju"
        ↓
TAHAP 3 — bangun_isi()      ← POTONG token (token_bab)
   ├─ tulis bab PAKAI artikel nyata tadi
   └─ kalau gagal → token DIKEMBALIKAN (pagar P2) ✅
```

### ⭐ Yang PENTING — Auto AI sudah punya pagar yang benar
Dari kode (`ai.py:4166`), pagar P2 sudah tertulis:
```
'pesan': 'Kerangka tidak bisa disusun dari bahan yang ada.
          Token Revisi kamu sudah dikembalikan — coba ubah judul
          atau kata kuncinya.'
```
⇒ Jadi **kalau bahan tidak ada → token kembali.** Pola yang sama seperti
usulan Wulan untuk pencarian manual. **Sudah konsisten.**

---

## 🎯 PERBANDINGAN 2 JALUR (terukur, bukan dugaan)

| | 🤖 **Auto AI** (sudah jalan) | 🔎 **Manual** (belum ada UI) |
|---|---|---|
| Yang tentukan kata kunci | **AI** (dari judul/tema) | **User** (ketik sendiri) |
| Tujuan | **MENULIS bab** pakai artikel | **MENCARI bahan** untuk dibaca |
| Keluaran | **bab baru** + daftar pustaka | **daftar artikel** (link) |
| Biaya | **0 token** di Tahap 2, token di Tahap 3 (tulis) | **1 token/pencarian** |
| Jatah gratis | — (sudah termasuk alur tulis) | **2× per minggu** |
| Status | ✅ **LIVE** | ❌ **belum ada UI** |

⇒ **Penting:** dua-duanya **beda tujuan**:
- Auto AI = **"tolong tuliskan bab ini dengan referensi nyata"** → hasilnya bab
- Manual = **"tolong carikan referensi, nanti aku pakai sendiri"** → hasilnya daftar

⇒ **Tidak bentrok — beda pekerjaan.** Yang satu **menulis**, yang satu **mencari.**

---

## 💡 IDE WULAN — 3 USULAN UNTUK AUTO AI

### 1. Tampilkan artikel yang dipakai (sekarang tersembunyi?)
Sekarang Auto AI sudah mencari + mengaudit artikel — **tapi apakah user bisa
MELIHAT artikel mana yang dipakai?** Wulan belum memeriksa bagian ini.

**Usul:** sebelum menekan "Setuju" (Tahap 2), user **melihat daftar artikel**
yang akan dipakai — **lengkap dengan link**.

| Keuntungan |
|---|
| User tahu **bahan apa** yang akan masuk ke babnya (tidak buta) |
| Kalau artikelnya tidak cocok → user **batalkan sebelum bayar token** |
| Menjawab keinginan Bos: **"artikelnya nyata, bukan karangan"** — user bisa klik sendiri |

⇒ Ini **hemat token user** dan **meningkatkan kepercayaan**.

### 2. Simpan hasil ke workspace (sambung diskusi kemarin)
Artikel yang dipakai Auto AI → **otomatis masuk daftar link jurnal workspace itu.**

⇒ Jadi **sekali cari (oleh AI), tersimpan sendiri** — user tidak perlu ulangi
pencarian. Nyambung dengan ide "1 berkas link jurnal per workspace".

### 3. Hasil Auto AI yang bagus → bisa dipakai ulang
Kalau Auto AI sudah menemukan 20 artikel nyata untuk judul itu, dan user mau
**cari manual nanti** dengan judul yang sama → **pakai hasil yang sudah ada,
jangan cari ulang.**

⇒ Hemat biaya API + hemat token user. **Bonus, bukan fitur utama.**

---

## 🤔 PERTANYAAN PENTING YANG BELUM TERJAWAB

Wulan **tidak menebak** — ini yang perlu Bos putuskan:

### A. Auto AI kena biaya APA?
Sekarang: Tahap 2 (cari artikel) = **0 token**, Tahap 3 (tulis bab) = **token**.
⇒ Apakah Bos mau:
- (a) tetap begitu — cari gratis, tulis berbayar ✅ (Wulan sarankan)
- (b) cari juga kena token
- (c) keduanya masuk paket (gratis semua, sampai kuota paket habis)

### B. Auto AI jalan KAPAN?
Sekarang: saat user **tekan tombol "Susun kerangka BAB I"** (manual trigger).
⇒ Apakah Bos mau:
- (a) tetap begitu — user yang tekan ✅ (pasti, tidak boros)
- (b) otomatis saat dokumen baru dibuat (background)
- (c) keduanya

### C. Jatah 2×/minggu — apakah berlaku untuk Auto AI juga?
Putusan Bos: **2× gratis/minggu** untuk **pencarian MANUAL**.
⇒ Auto AI **tidak masuk hitungan itu** (betul?) — karena Auto AI punya
hitungan sendiri (token saat menulis bab).

### D. Auto AI menulis bab — pakai artikel yang DIA cari sendiri.
⇒ Kalau user **tidak suka** artikel pilihannya, bisakah diganti **sebelum**
token dipotong? (Nyambung usulan 1 di atas.)

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR

1. **Auto AI SUDAH ADA dan sudah jalan** — ini kabar baik. **Tidak perlu
   dibangun dari nol.**
2. **Wulan BELUM memeriksa** apakah user bisa *melihat daftar artikel* di
   Tahap 2 (sebelum bayar). Ini perlu dicek lagi sebelum menjanjikan.
3. **Scopus belum ada kuncinya** di produksi → Auto AI pakai OpenAlex + Garuda
   + CrossRef saja.
4. **Saringan relevansi ketat** (terukur: 35 hasil mentah → 1 lolos). Untuk
   Auto AI ini **mungkin bagus** (hanya yang sangat cocok yang masuk bab), tapi
   **perlu ditinjau** apakah tidak terlalu pelit.
5. **`KAMUS_KONSEP` cuma 25 konsep** — judul dengan istilah baru tidak
   terdeteksi sebagai konsep (tetap dicari, tapi tidak terkelompok).

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **Auto AI cari artikel: tetap GRATIS (0 token)**, token hanya saat menulis
   bab? (Wulan sarankan ya)
2. **Auto AI jalan saat ditekan tombol** (bukan otomatis) — setuju?
3. **Tampilkan daftar artikel sebelum user bayar token** (di Tahap 2) —
   perlu? (Wulan sarankan **YA**, biar user tidak buta)
4. **Hasil Auto AI otomatis masuk** daftar link jurnal workspace — setuju?
5. **Auto AI tidak masuk hitungan 2×/minggu** (punya hitungan sendiri) — betul?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **TERUKUR**: Auto AI SUDAH LIVE (`kerangka.py:178` + `ai.py:4092` + tombol `mulai.html:249`)
- [x] Pagar P2 (token kembali kalau gagal) **sudah ada** di `ai.py:4166`
- [ ] **PERLU DICEK LAGI**: apakah user bisa melihat daftar artikel di Tahap 2
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
