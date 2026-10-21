# 💡 IDE — HARVEST JURNAL + UNDUH KE WORKSPACE (06 Okt 2026)

<!-- ⛔ SOT: IDE — DILARANG DIKODING -->
> # ⛔ IDE / USULAN — **DILARANG dikoding** sampai Bos bilang "mulai".
> Isi berkas ini = **gagasan menunggu putusan Bos**, BUKAN keadaan kini dan
> BUKAN rencana kerja aktif. ❌ JANGAN dibaca sebagai status proyek.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Menjawab arahan Bos 06 Okt 2026 (verbatim):
> *"Intinya user bisa lihat hasil Harvest artikel yang AI cari bahwa artikel
> tersebut nyata, bukan karangan dan bisa user download jika free to download
> dan katakan berlangganan / paid artikel."*
> *"Ketika user download maka berkasnya ada di workspace tersebut, bukan bisa
> download di hp atau pc user, artinya file ada di workspace agar tidak hilang
> dan bisa dihapus juga oleh user. Jadi dari link download tadi user bisa
> pilih yang di-download yang mana, kalo sudah download tidak bisa download
> atau double, kecuali telah dihapus dan download lagi."*
> *"Atau kamu punya ide yang lebih bagus dan praktis lagi untuk ini."*
>
> Status: **BAHAN DISKUSI.** Belum diputuskan. DILARANG dikoding.

---

## ✅ BUKTI TERUKUR (06 Okt 2026, dijalankan di container produksi)

| Uji | Hasil |
|---|---|
| Server punya `httpx` (bisa ambil dari internet) | ✅ v0.28.1 |
| Ambil halaman detail Garuda | ✅ 200 |
| Temukan link PDF di halaman itu | ✅ dapat `.../article/download/900/pdf` |
| **Unduh PDF-nya sungguhan** | ✅ **200 · application/pdf · 406.375 byte · `%PDF-1.5`** |

⇒ **Rencana Bos BISA dikerjakan.** Bukan khayalan — mesinnya sanggup.

---

## 🎯 ARAHAN BOS → jadi 4 aturan

1. **Hasil Harvest harus TERBUKTI NYATA** — user bisa lihat bahwa artikel itu
   betul-betul ada (bukan karangan AI).
2. **Ditandai statusnya** — mana yang **GRATIS (free)** dan mana yang
   **BERLANGGANAN (paid)**.
3. **Unduhan masuk ke WORKSPACE**, bukan ke HP/PC user. Alasannya jelas:
   agar tidak hilang, dan bisa user hapus sendiri.
4. **Anti-unduh-ganda** — satu artikel satu salinan. Kalau sudah
   diunduh, tombol unduh **mati**. Baru bisa unduh lagi **setelah dihapus**.

---

## 🧠 IDE WULAN — versi praktis (gabungan dari arahan Bos)

### A. Halaman "Jurnal" di dalam workspace

Bukan sekadar berkas `.txt` (ide kemarin), tapi **halaman kecil** yang:

```
┌─ Workspace: Skripsi Saya ──────────────────────────┐
│  [Naskah]  [Jurnal & Link]  ← tab                │
├───────────────────────────────────────────────────┤
│  🔎 Tema: [kualitas produk → keputusan pembelian] │
│                                                   │
│  1. Yusnia & Burhanudin (2020)       ✅ NYATA     │
│     Customer Experience, Diferensiasi Produk...   │
│     Jurnal Ilmiah Edunomika                       │
│     🟢 PDF GRATIS          [ ⬇ Unduh ]            │
│                                                   │
│  2. Smith et al (2021)                ✅ NYATA    │
│     The Role of ...                               │
│     🔒 BERLANGGANAN                               │
│     [ Buka Situs ]  [ Cari versi gratis ]         │
│                                                   │
│  3. Sudah diunduh                          📁     │
│     [ Lihat berkas ]  [ 🗑 Hapus ]                │
└───────────────────────────────────────────────────┘
```

### B. Bagaimana "NYATA, bukan karangan" dibuktikan ke user

Ini bagian yang **paling penting** menurut Wulan — dan mesinnya **sudah ada**:

| Penanda | Sumber (sudah ada di `pustaka.py`) |
|---|---|
| ✅ **Terverifikasi** | `audit_doi()` — DOI dicek ke CrossRef. Kalau tak lolos → **dibuang** |
| 🔗 **Link bisa diklik** | `doi` + `garuda_id` |
| 📅 Tahun, penulis, jurnal | sudah diambil dari API |
| 🌐 Sumbernya disebut | "OpenAlex" / "Garuda" / "CrossRef" |

⇒ Kuncinya: **kalau user bisa mengklik dan membuka sendiri artikelnya, dia
tahu itu nyata.** Bukan percaya kata AI — **mata sendiri.**

### C. Cara tahu "gratis" atau "berlangganan"

| Jalur | Cara tahu | Hasil |
|---|---|---|
| **Garuda** (jurnal Indonesia) | server coba unduh PDF | kalau dapat `%PDF` → 🟢 **GRATIS** |
| **DOI internasional** | cek ke halaman penerbit | kalau balas halaman berbayar/HTML → 🔒 **BERLANGGANAN** |

⚠️ **Wulan sarankan: server MENGUJI dulu** (seperti yang Wulan baru lakukan)
saat user menekan "Unduh" — bukan menebak. Kalau benar dapat PDF → simpan.
Kalau tidak → beri tahu jujur "artikel ini berlangganan" + beri jalur lain.

### D. Anti-unduh-ganda (arahan Bos)

Wulan usulkan: **tidak perlu kolom baru**. Cukup **tandai dari nama/isi
berkas** — atau lebih rapi: simpan di berkas jurnal workspace satu baris
penanda `[TERUNDUH] <nama berkas>`.

⇒ Kalau tanda itu ada & berkasnya masih ada → tombol jadi **"Lihat berkas"**
(bukan unduh lagi). Kalau berkasnya dihapus → tanda ikut hilang → tombol
**"Unduh"** hidup lagi. **Persis seperti yang Bos mau**, dan tanpa tabel baru.

---

## ⚠️ HAL YANG WULAN WAJIB SEBUT JUJUR

1. **Hak cipta.** Artikel berbayar **tidak boleh** kita unduh-paksa atau
   tembus paywall. Yang boleh: **artikel gratis/publik** (Garuda, jurnal open
   access). Untuk yang berbayar → cukup beri **link** + tanda 🔒.
   Ini sejalan prinsip Bos sendiri: *"JANGAN download artikel, kasih LINK."*
2. **Kuota storage.** PDF artikel bisa 300 KB–2 MB. Kalau banyak, storage user
   cepat penuh. Perlu dipikirkan: apakah unduhan artikel **masuk hitungan
   kuota** (seperti berkas lain) atau **kuota terpisah**.
3. **Tidak semua Garuda ada PDF-nya.** Sebagian hanya abstrak. Server harus
   **jujur bilang "PDF tidak tersedia"** daripada menggantung.
4. **Kecepatan.** Unduh 1 PDF ≈ 1–3 detik. Kalau user minta 10 sekaligus,
   perlu **satu per satu** (jangan bikin server berat) — atau kerjakan di
   belakang layar.

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **Halaman "Jurnal & Link" di dalam workspace, atau cukup berkas `.txt`?**
   (Halaman = lebih rapi & ada tombol unduh; berkas = lebih sederhana)
2. **Satu workspace satu daftar jurnal**, atau boleh banyak daftar per topik?
3. **Unduhan artikel masuk kuota storage user**, atau kuota terpisah?
4. **Tombol "Unduh semua yang gratis"** — perlu, atau satu-satu saja?
5. **Artikel berlangganan** — cukup tombol "Buka Situs" + "Cari versi gratis",
   atau ada tambahan lain?
6. **Kalau hasil pencarian tidak menemukan PDF gratis** — apakah tetap
   ditampilkan (dengan tanda 🔒), atau disembunyikan?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] **DIUJI NYATA** di container produksi (unduh PDF berhasil)
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
