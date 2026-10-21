# ✅ CEK — 2 JALUR PENCARIAN (06 Okt 2026) — HASIL CEK KODE

> Tegasan Bos 06 Okt 2026 (verbatim):
> *"Jadi saya tegaskan 2 jalur pencarian. **1. Otomatis dari AI** saat mahasiswa /
> user memulai dokumen baru / kosong dan akan buat penelitian pada awalnya, dan
> dia akan menulis judul dan **AI merekomendasikan judul**. (Cek benar atau
> tidak). **2. User cari artikel manual** dengan memasukkan judul atau keyword
> sendiri. Bagaimana pendapatmu."*

---

## 🎯 JAWABAN: **BENAR** — dan Bos BENAR dua-duanya. Ini hasil cek kode.

---

## JALUR 1 — "AI merekomendasikan judul"

### ⚠️ HASIL CEK: **SETENGAH BENAR — ada, tapi belum AI**

Ini temuan penting. Wulan cek langsung, bukan mengiyakan.

| Pertanyaan | Kenyataan (terukur) |
|---|---|
| Ada fungsi contoh judul? | ✅ **ADA** — `alur_awal.py:377` `contoh_judul(bidang, mode)` |
| Ada rutenya? | ✅ **ADA & LIVE** — `rute_alur.py:201` `GET /alur/contoh-judul` |
| Jalan tanpa login? | ✅ ya, gratis (`'gratis': True`) |
| **Pakai AI?** | ❌ **TIDAK** — ambil dari **daftar tetap** (`BIDANG[...]['contoh']`) |
| Jumlah opsi | 3–5 judul |

### 🔴 BEDANYA DENGAN YANG BOS BAYANGKAN

| Yang Bos mau | Yang ADA sekarang |
|---|---|
| User **menulis judul** → AI **merekomendasikan** judul | User **pilih bidang** → sistem **menampilkan 3-5 contoh** dari daftar tetap |
| AI **membaca** judul user | Sistem **tidak membaca** apa pun |
| Hasil **disesuaikan** judul user | Hasil **sama** untuk semua orang di bidang itu |

⇒ **Artinya:** yang ada sekarang = **"contoh judul per bidang"** (katalog statis).
Yang Bos mau = **"AI baca judulku, lalu merekomendasikan judul yang lebih baik"**
(mesin yang menyesuaikan diri). **INI BELUM ADA.**

⚠️ **Catatan penting:** Wulan BUKAN bilang fiturnya salah. Contoh judul tetap
berguna (memancing ide user yang belum punya judul). Tapi **beda fungsi** —
dan **beda biaya** (katalog = Rp 0; AI = berbayar).

### Yang SUDAH ADA untuk menopang Jalur 1 (nanti)
| Bahan | Letak | Guna |
|---|---|---|
| `contoh_judul()` | `alur_awal.py:377` | 3-5 contoh per bidang |
| `daftar_bidang()` | `alur_awal.py:390` | 8 bidang |
| `daftar_jenjang()` | `alur_awal.py:395` | jenjang (S1/S2/S3) |
| `petakan_jalur()` | `alur_awal.py:172` | jalur (baru/lanjut) |
| `deteksi_isi()` | `alur_awal.py:255` | baca isi naskah |
| `_al.JENIS_PENELITIAN` | `rute_alur.py:195` | jenis penelitian + `bab4`, `siap` |
| Rute dokumen baru | `rute_alur.py:464` | `POST /alur/dokumen-baru` |
| Rute simpan alur | `rute_alur.py:503` | `POST /alur/simpan` |

---

## JALUR 2 — "User cari artikel manual (judul / keyword sendiri)"

### ✅ HASIL CEK: **BENAR — mesinnya SUDAH SIAP**

| Pertanyaan | Kenyataan (terukur) |
|---|---|
| Ada mesin cari artikel? | ✅ `pustaka.cari_semua()` (4 sumber + audit DOI) |
| Pecah judul jadi variabel? | ✅ `pustaka.konsep_dari_judul()` (25 konsep) |
| Bisa keyword manual? | ✅ ambil "sisa" kata — **tapi tanda koma BELUM** |
| Tampilan ke user? | ❌ **BELUM ADA** (rute/template tidak ada) |
| Bayar token? | ❌ **BELUM ADA** |

⇒ Mesinnya lengkap, **yang belum = tampilan + tombol + potong token.**

---

## 📊 PERBANDINGAN 2 JALUR (yang Bos tegaskan)

| | **Jalur 1 — SAAT MULAI (AI)** | **Jalur 2 — CARI SENDIRI (User)** |
|---|---|---|
| Kapan | saat **dokumen baru/kosong** | kapan saja user mau |
| Masukan | **judul** yang user tulis | **judul atau keyword** |
| Keluaran | **rekomendasi judul** (ide penelitian) | **daftar artikel** (referensi) |
| Fungsi | bantu **menentukan arah** penelitian | bantu **mencari bahan** bacaan |
| Sifat | sekali, di awal | berkali-kali, kapan saja |
| Status kode | ⚠️ **setengah** (contoh statis, belum AI) | ✅ **mesin siap**, ❌ UI belum |
| Biaya | **berbayar** (kalau pakai AI) | **1 token/pencarian** |

### 💡 Menurut Wulan, 2 jalur ini BAGUS dan TIDAK bertabrakan
Kenapa? Karena **waktunya beda dan gunanya beda**:
- Jalur 1 = **sebelum ada penelitian** ("mau meneliti apa?")
- Jalur 2 = **sesudah ada judul** ("cari bahan untuk judul ini")

⇒ Bukan dua fitur yang bersaing — **dua TAHAP berbeda** dalam perjalanan
mahasiswa. **Wulan setuju dengan tegasan Bos.**

---

## 💡 PENDAPAT WULAN (yang Bos tanyakan)

### 1. Jalur 1 — pakai **hybrid 3 lapis**, jangan AI langsung
Pola yang Bos sudah pakai di Statistik Lab dan sudah **terbukti 95% akurat**:
```
Lapis 1 — daftar contoh per bidang (Rp 0)      ← SUDAH ADA (contoh_judul)
Lapis 2 — AI kalau user minta (berbayar)       ← BELUM (
              "Mau AI sarankan judul khusus untukmu?"
Lapis 3 — user tulis sendiri (selalu bisa)     ← penutup, jangan pernah ditutup
```
⇒ Kenapa hybrid? Karena user yang **belum tahu mau meneliti apa** cukup dapat
contoh (Rp 0, instan). Yang **sudah punya bayangan** minta AI (bayar, dapat
yang pas). **Tidak semua user perlu bayar.**

### 2. Jalur 2 — jangan di halaman terpisah
Tempatkan di **tab 📚 Referensi**. Kalau di **halaman baru**, user harus
mengingat ada fitur itu. Kalau menempel di halaman naskah, **ketemu sendiri
saat dibutuhkan**.

### 3. Hasil Jalur 1 → **jangan buang**
Kalau AI sudah menyarankan judul dan user memilihnya, judul itu **otomatis
jadi tema awal** → siap dipakai Jalur 2. ⇒ **Dua jalur menyambung, tidak
masing-masing sendiri.**

```
Jalur 1: user tulis/pilih judul  →  judul tersimpan
                                         ↓ otomatis
Jalur 2: mesin cari artikel pakai judul itu → dipisah per variabel
```
⇒ Ini yang membuat 2 jalur terasa **satu kesatuan**, bukan dua fitur terpisah.

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR

1. **Jalur 1 belum ada AI-nya.** Yang ada baru **contoh statis per bidang**.
   Membangun yang versi AI = pekerjaan baru + biaya + bisa salah.
2. **Wulan BELUM mengukur** daftar `BIDANG[...]['contoh']` — berapa banyak
   contoh judulnya, kualitasnya bagaimana. **Perlu diukur sebelum menjanjikan.**
3. **Rekomendasi judul oleh AI punya risiko.** Judul yang "bagus" menurut AI
   belum tentu layak secara akademik (kelayakan dinilai dosen). AI sebaiknya
   **memberi OPSI + alasan**, bukan satu jawaban mutlak.
4. **Kalau judul dari AI ternyata menyalahi kaidah** (mis. tidak ada variabel
   terukur), itu **kerugian reputasi**. Perlu pagar: AI harus menyebut
   **variabelnya**, bukan cuma judul.

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **Jalur 1**: cukup **contoh statis** (yang sudah ada, Rp 0), atau naikkan
   jadi **AI yang benar-benar merekomendasikan** (berbayar)?
2. Kalau AI: **berbayar berapa token?** (1 token per rekomendasi?)
3. **Jalur 1 murni Judul saja**, atau sekalian AI sarankan **variabel + model**
   (biar nyambung ke Statistik Lab)?
4. **Judul hasil Jalur 1 otomatis dipakai Jalur 2** — setuju?
5. **Jalur 2 di tab Referensi** — atau Bos mau tempat lain?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **DI CEK LANGSUNG KE KODE** (bukan dugaan)
- [x] Temuan: Jalur 1 = ⚠️ setengah (contoh statis, bukan AI) · Jalur 2 = ✅ mesin siap
- [ ] **PERLU DIUKUR**: isi `BIDANG[...]['contoh']` (berapa judul, kualitasnya)
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
