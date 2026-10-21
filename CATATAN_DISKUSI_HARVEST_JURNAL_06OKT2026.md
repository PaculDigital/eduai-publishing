# 📚 CATATAN — HARVEST ARTIKEL JURNAL DI EDUAI (06 Okt 2026)

<!-- 📝 SOT: CATATAN DISKUSI — bukan penentu status -->
> # 📝 CATATAN DISKUSI — BUKAN penentu status proyek.
> Berkas ini merekam **bahan pembicaraan** saat itu. Sebagian bisa sudah
> dikerjakan, sebagian belum. ❌ JANGAN dipakai sebagai keadaan kini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Status: **DISKUSI.** Belum diputuskan, DILARANG dikoding. Isi = arah Bos +
> hasil CEK KODE SUNGGUHAN (bukan dugaan) + uji nyata di container produksi.

---

## 🎯 ARAH BOS (verbatim 06 Okt 2026)

> "Sekarang fitur Harvest artikel jurnal, bagaimana selama ini bekerja di app
> EduAi ini, jelaskan. Dan kalo user mau download artikel aslinya apakah bisa?
> Atau kamu hanya cari artikel tanpa tahu sumber alamat web nya yang nyata.
> **Saya mau saat kamu cari user dapat link webnya untuk download artikelnya
> secara publik.**"

---

## 🔍 JAWABAN 1 — "Bagaimana Harvest artikel bekerja selama ini?"

**Bukan "Harvest" — namanya `app/pustaka.py`.** Ini **SUDAH ADA & LIVE** di
produksi (bukan rencana). Terverifikasi 06 Okt 2026.

### Apa yang dilakukan (alur)

1. **Ambil tema** dari judul naskah / tema kerja.
2. **Bikin kata kunci** dua bahasa (`kata_kunci()`) — Inggris + Indonesia.
3. **Cari ke 4 sumber** sekaligus (`cari_semua()`):
   | Sumber | Fungsi | Status terukur 06Okt26 |
   |---|---|---|
   | **Scopus** | `cari_scopus()` | ⚠️ **kunci API TIDAK ADA → DILEWATI** |
   | **OpenAlex** | `cari_openalex()` | ✅ jalan (15 hasil) |
   | **Garuda** (jurnal Indonesia/SINTA) | `cari_garuda()` | ✅ jalan (10 hasil) |
   | **CrossRef** | `cari_crossref()` | ✅ jalan (10 hasil) |
4. **Buang duplikat** (`_kunci_dedup()`).
5. **AUDIT DOI ke CrossRef** (`audit_doi()`) — **anti-halusinasi**: DOI yang
   tak bisa dibuktikan **DIBUANG**. Inilah pagar utamanya.
6. **Saring yang nyambung** dengan tema (`_nyambung()`).
7. **Hasil** → `ringkas_untuk_ai()` (untuk AI mengutip) + `daftar_pustaka_apa7()`.

### Bukti uji nyata (06 Okt 2026, tema "kualitas produk → keputusan pembelian")
```
per_sumber: Scopus 0 | OpenAlex 15 | Garuda 10 | CrossRef 10   (35 mentah)
total_unik: 1 | terverifikasi: 1                                (1 lolos)
```
⇒ **Pagar bekerja keras**: 35 hasil mentah → **1** yang lolos AUDIT DOI.
Judul yang lolos pun sebenarnya **kurang nyambung** (tema beda) — jadi
pagar saringnya **belum cukup pintar** memilih relevansi.

---

## 🔍 JAWABAN 2 — "User mau download artikel aslinya, bisa?"

### ❌ BELUM BISA. Dan ini alasannya (3 lapis):

**Lapis 1 — Data link-nya ADA, tapi tidak lengkap.**
Yang disimpan per artikel: `title, doi, year, authors, cited_by_count, source,
abstract, journal, garuda_id`.

| Sumber | Punya link nyata? |
|---|---|
| OpenAlex | ✅ `doi` (https://doi.org/...) TAPI `garuda_id: None` |
| Garuda | ✅ `garuda_id` → **bisa dibentuk link** |
| CrossRef | ✅ `doi` |
| Scopus | DOI (kalau kunci ada) |

**Lapis 2 — Link dibentuk, tapi HANYA di daftar pustaka.**
Terukur `pustaka.py:719-721`: kalau tidak ada DOI tapi ada `garuda_id`, link
dibuat:
```python
teks += (' https://garuda.kemdiktisaintek.go.id/documents/detail/'
         f'{r["garuda_id"]}')
```
⚠️ Ini **HANYA muncul di `daftar_pustaka_apa7()`** — dipakai AI & daftar
pustaka. **BUKAN tampilan klik-untuk-user.**

**Lapis 3 — TIDAK ADA halaman untuk mahasiswa.**
Grep rute `pustaka|referensi` di `main.py` → **KOSONG**. Jadi:
- Mahasiswa **tidak bisa** melihat daftar hasil pencarian.
- Mahasiswa **tidak bisa** mengklik link.
- Fitur ini **murni di belakang layar** — dipakai `kerangka.py` (Tahap 2,
  susun rencana bab, GRATIS 0 token) untuk memberi AI daftar terverifikasi.

### 🎯 Jawaban tegas pertanyaan Bos

> "Atau kamu hanya cari artikel tanpa tahu sumber alamat web nya yang nyata."

**BUKAN.** Sistem **TAHU alamat nyatanya** (`garuda_id` + `doi`), dan
memang **sudah pernah membentuk link Garuda**. Yang belum ada = **halaman
untuk mahasiswa melihat & mengklik link itu.**

### ⚠️ TAPI Wulan harus jujur — masalah sebenarnya lebih dalam

**Link ≠ file artikel.** Untuk sebagian besar jurnal internasional:
- Link `doi.org/...` sering **berbayar (paywall)** atau butuh langganan kampus.
- "Download otomatis" artikel asli **melanggar hak cipta** untuk banyak jurnal.
- Untuk **Garuda (jurnal Indonesia)**, file PDF-nya **umumnya GRATIS &
  publik** — ini yang paling aman.

Dan **ini bukan hal baru** — sudah jadi keputusan Bos sebelumnya (tercatat di
memori):
> **"REFERENSI TERVERIFIKASI: prinsip Bos = JANGAN download artikel, kasih
> daftar LINK (lebih jujur) + pakai API key Scopus yg sudah ada."**

⇒ Arah Bos sekarang ("user dapat link webnya untuk download publik")
**SEJALAN** dengan prinsip itu — bahkan lebih jelas.

---

## ❓ PERTANYAAN TERBUKA

1. **Halaman baru untuk mahasiswa, atau tempel di halaman yang sudah ada?**
   (Belajar/Buat Data/Kerangka Bab?)
2. **Scopus kunci API belum ada** di container produksi — mau dipasang?
3. **Tampilkan link apa saja?** DOI saja, atau + Garuda, atau + "cari di
   Google Scholar" sebagai cadangan?
4. **Kalau DOI berbayar** — tampilkan apa? (tanda "berlangganan" + link
   Scholar?)
5. **Harvest otomatis ke workspace** — apakah hasil pencarian langsung
   disimpan sebagai berkas di workspace, atau cuma link di layar?
6. **Hasil pencarian 35 → 1 laba-laba** (saringan terlalu ketat?). Perlu
   ditinjau: buang karena saring relevansi, atau karena DOI tak lolos?

---

## 🧠 IDE WULAN (bahan diskusi — belum diputuskan)

1. **Titip di mesin yang sudah ada.** `pustaka.py` sudah lengkap (cari, audit
   DOI, susun APA 7). Yang kurang **hanya tampilan** — halaman untuk mahasiswa.
   Nol mesin baru untuk pencarian; cukup **satu halaman + tombol**.
2. **Link = DOI + Garuda + Scholar.** Tiga jalur supaya selalu ada yang bisa
   diklik:
   - `https://doi.org/<doi>` — jalur resmi (kadang berbayar)
   - `https://garuda.kemdiktisaintek.go.id/documents/detail/<id>` — **gratis & publik** (jurnal Indonesia)
   - `https://scholar.google.com/scholar?q=<judul>` — cadangan mencari
     PDF publik
3. **Jujur soal akses.** Beri **label** di setiap hasil: "🟢 PDF Gratis" /
   "🔒 Berlangganan" / "🔎 Cari versi publik". Ini melindungi mahasiswa dari
   klik sia-sia DAN melindungi aplikasi dari masalah hak cipta.
4. **Simpan ke workspace** = cukup tulis satu baris link ke berkas
   (`.md`/daftar pustaka) di `folder_id` yang dipilih — pola yang sama dengan
   diskusi workspace.
5. **Saringan relevansi perlu diperiksa.** 35 → 1 itu terlalu tajam; mungkin
   `_nyambung()` perlu dilonggarkan sedikit (atau beri pilihan "ketat/sedang").

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] Kode diperiksa + diuji nyata di container produksi
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
