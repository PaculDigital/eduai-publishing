# 💡 IDE — TAB "REFERENSI": 2 JALUR JURNAL TANPA BENTROK (06 Okt 2026)

<!-- ⛔ SOT: IDE — DILARANG DIKODING -->
> # ⛔ IDE / USULAN — **DILARANG dikoding** sampai Bos bilang "mulai".
> Isi berkas ini = **gagasan menunggu putusan Bos**, BUKAN keadaan kini dan
> BUKAN rencana kerja aktif. ❌ JANGAN dibaca sebagai status proyek.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Menjawab arah Bos 06 Okt 2026 (verbatim):
> *"Mungkin tampil di halaman user samping tab Belajar dengan nama Referensi.
> Agar jelas dan rapi. Tapi nanti bentrok dengan fitur yang akan sy bangun,
> yaitu pencari artikel jurnal. Di fitur tersebut, user bebas mencari artikel
> berdasar kata kunci atau judul penelitian dia. Akan berbeda dengan auto
> Harvest oleh ai. Paham gak maksud saya, jadi ada seperti 2 jalur Harvest
> artikel jurnal yang satu sudah ditentukan oleh ai yang satu oleh user
> sendiri. Bagaimana ide kamu? Gar tidak bertabrakan."*
>
> Status: **BAHAN DISKUSI.** Belum diputuskan. DILARANG dikoding.

---

## 🎯 MASALAH YANG BOS TANGKAP (inti)

Ada **2 jalur** yang beda sifat, dan Bos khawatir keduanya tabrakan:

| | **Jalur 1 — Auto Harvest AI** | **Jalur 2 — Pencari User** |
|---|---|---|
| Siapa yang tentukan | **AI** | **User** |
| Dasarnya | Tema naskah | Kata kunci / judul sendiri |
| Sifat | Otomatis, sekali | Bebas, berkali-kali |
| Contoh | AI baca skripsi → cari artikel yang cocok → tampilkan | User ketik "brand image UMKM" → cari sendiri |

---

## ✅ IDE WULAN — SATU PINTU, DUA TAB DI DALAMNYA

**Jangan bikin 2 menu.** Bikin **satu tab bernama "📚 Referensi"** (sejajar dengan
Naskah Saya · Kolaborasi · 🎓 Belajar). Di dalamnya **dua bagian jelas**:

```
┌─ 📚 Referensi ─────────────────────────────────────────┐
│                                                        │
│  ┌─ 🤖 Dari AI (otomatis) ─────────────────────────┐   │
│  │  AI sudah memilih artikel yang cocok dengan     │   │
│  │  naskahmu. Tidak perlu kamu cari.               │   │
│  │                                                 │   │
│  │  1. Yusnia (2020) ........................ ✅   │   │
│  │  ...

```

### 🎯 Ide pokok penyelesaian bentroknya

**Bukan dua fitur berbeda — tapi SATU fitur dengan DUA SUMBER MASUKAN.**

Bayangkan **satu lemari arsip** dengan **2 pintu**:
- **Pintu 1 (AI):** AI yang memasukkan artikel — otomatis, dari tema naskah.
- **Pintu 2 (User):** user yang memasukkan artikel — manual, dari kata kunci.

Hasilnya **bertemu di satu tempat yang sama**: satu **daftar pustaka** milik user.
Tidak ada dua daftar, tidak ada dua tempat menyimpan, tidak ada tabrakan.

### Kenapa ini tidak tabrakan

| Sumber bentrok | Kenapa aman |
|---|---|
| Menu/UI | Satu tab saja ("Referensi"), bukan dua |
| Mesin pencari | **Pakai yang sama** — `app/pustaka.py` (cari_scopus, cari_openalex, cari_garuda, cari_crossref, audit DOI) |
| Penyimpanan | **Satu daftar** per user (bukan per jalur) |
| Unduhan | **Satu pintu unduh** ke workspace |
| Kuota | Satu aturan |

⇒ **Yang beda HANYA "siapa yang mengisi kata kuncinya"** — AI atau user.
Sisanya (cari → audit DOI → tampilkan link → unduh) **jalur yang sama persis.**

### Perbedaan yang tetap dihormati (biar user tidak bingung)

| | Bagian AI | Bagian User |
|---|---|---|
| **Judul bagian** | "🤖 Pilihan AI untuk naskahmu" | "🔎 Pencarian kamu sendiri" |
| **Cara isi** | tombol "Cari lagi" (pakai tema naskah) | kotak kata kunci (user ketik sendiri) |
| **Penanda tiap artikel** | 🔵 **Dari AI** | 🟢 **Kamu cari** |
| **Bisa dihapus?** | ya (kalau tidak suka) | ya |
| **Simpan ke daftar pustaka** | tombol "pakai" | tombol "pakai" |

⇒ Jadi user **selalu tahu** artikel mana yang datang dari AI dan mana yang
dia cari sendiri — **tidak tercampur diam-diam**, tapi juga **tidak terpisah
jadi dua tempat**.

### Kenapa ini "praktis" (bukan cuma rapi)

1. **Satu mesin, satu aturan.** Cari, audit DOI, tanda gratis/berlangganan,
   unduh ke workspace, anti-unduh-ganda — semua **sekali bangun, dua-duanya
   dapat.** Kalau dipisah, semua itu **harus dibangun dua kali.**
2. **Daftar pustaka jadi satu.** Mahasiswa butuh **satu** daftar pustaka,
   bukan dua. Kalau dipisah, nanti harus ada "gabungkan" — kerja tambah.
3. **User bisa menyaring, tidak dipaksa.** Artikel AI yang tidak cocok →
   bisa dibuang. Hasil cari sendiri → bisa disimpan. Saling melengkapi.
4. **Tidak menambah menu.** Pita tab tetap 4 (Naskah Saya · Kolaborasi ·
   Belajar · Referensi) — tidak jadi 5-6 yang bikin bingung pemula.
5. **Nol mesin baru.** `pustaka.py` sudah ada. Yang dibangun = **tampilan**
   + tombol unduh. Itu saja.

---

## ⚠️ RISIKO YANG WULAN WAJIB SEBUT

1. **Tema naskah belum dibaca berulang.** Auto Harvest sebaiknya **sekali per
   naskah** (atau saat user minta) — bukan tiap kali halaman dibuka, supaya
   tidak berat & tidak boros.
2. **Kuota pencarian.** Kalau user bisa cari 100× sehari, server & API kebanjiran
   (Scopus/OpenAlex ada batas). Perlu **batas harian** (mis. 10–20 pencarian/hari).
3. **Saringan relevansi perlu diperiksa.** Uji 06Okt26: 35 hasil mentah → 1
   lolos. Terlalu tajam. Perlu ditinjau `_nyambung()`.
4. **Scopus belum ada kuncinya** di produksi → jalur internasional berkurang.
5. **Kalau nanti daftar pustaka dipakai menulis naskah**, artikel "dari AI"
   dan "dari user" harus **sama-sama terverifikasi DOI** — jangan sampai
   artikel cari-sendiri yang tak terverifikasi ikut dikutip AI.

---

## ✅ PUTUSAN BOS (07 Okt 2026, TERKUNCI)

> **PILIHAN BOS = A** — verbaatim: *"A"*

**SATU tab "📚 Referensi" dengan DUA BAGIAN di dalamnya.** Bukan dua tab terpisah.

⇒ Semua pertanyaan lain di bawah **diikuti** oleh pilihan ini:

| # | Pertanyaan | Jawaban (mengikuti A) |
|---|---|---|
| 1 | Satu tab atau dua tab? | ✅ **A — SATU tab, dua bagian** |
| 2 | Nama bagiannya | 🤖 **"Pilihan AI untuk naskahmu"** · 🔎 **"Pencarian kamu sendiri"** (usulan Wulan — Bos boleh ganti) |
| 3 | Daftar pustaka | **SATU daftar** (bukan dipisah per jalur) |
| 4 | Batas pencarian harian | ✅ **15× per hari** |
| 5 | Auto Harvest | ✅ **TUNGGU DITEKAN** (tidak jalan sendiri) |
| 6 | Artikel cari-user dipakai AI? | ✅ **HANYA yang TERVERIFIKASI** · maks **8 artikel per bab** |

✅ **SEMUA PERTANYAAN SUDAH DIJAWAB — tidak ada yang menggantung lagi.**
6 jawaban lengkap: A · (nama usulan Wulan) · satu daftar · 15/hari · tunggu ditekan · hanya terverifikasi & maks 8/bab.

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **Satu tab "Referensi" dengan 2 bagian** (ide Wulan) — atau Bos mau
   **dua tab terpisah** ("Referensi" + "Pencari")?
2. **Nama bagiannya**: "Pilihan AI" vs "Pencarian Saya"? atau nama lain?
3. **Daftar pustaka digabung** (satu daftar) — atau tetap dipisah per jalur?
4. **Batas pencarian harian** berapa?
5. **Auto Harvest jalan sendiri** saat user buka naskah, atau **menunggu
   ditekan**?
6. **Artikel hasil cari user — ikut dipakai AI** saat menulis bab, atau
   hanya jadi bahan bacaan user saja?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] Pita tab diperiksa: `naskah.html:618-622` (Naskah Saya · Kolaborasi · 🎓 Belajar)
- [x] ✅ **DIPUTUSKAN BOS 07 Okt 2026 — PILIHAN A** (satu tab, dua bagian)
- [x] ✅ **6 JAWABAN LENGKAP** (A · 15/hari · tunggu · hanya terverifikasi & maks 8/bab)
- [x] Boleh dikoding (putusan sudah ada)
- [ ] Tab dipasang di 4 template (naskah/kolaborasi/belajar/referensi)
- [ ] Isi 2 bagian (🤖 Dari AI · 🔎 Pencarian kamu)
