# 🛡️ PRINSIP — FLEKSIBEL TAPI DI DALAM PAGAR MESIN (06 Okt 2026)

<!-- ⛔ SOT: IDE — DILARANG DIKODING -->
> # ⛔ IDE / USULAN — **DILARANG dikoding** sampai Bos bilang "mulai".
> Isi berkas ini = **gagasan menunggu putusan Bos**, BUKAN keadaan kini dan
> BUKAN rencana kerja aktif. ❌ JANGAN dibaca sebagai status proyek.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> Arah Bos 06 Okt 2026 (verbatim):
> *"Iya maksud saya mesin juga harus bisa fleksibel, kalo user mau tambah
> artikel untuk ditambahkan dalam pembahasan bab juga harus bisa, tapi HANYA
> artikel khusus dengan mekanisme mesin yang sudah disediakan untuk menambah
> artikel dalam pembahasan bab. Tidak bisa user upload artikel di luar
> mekanisme dari mesin / liar. Itu untuk menjaga mesin tetap konsisten
> hasilnya."*
>
> Status: **ARAH DISETUJUI WULAN.** Belum dikoding. DILARANG dikoding.

---

## ✅ WULAN SETUJU 100% — dan alasannya kuat

Aturan Bos ini **bukan membatasi tanpa alasan**. Ada 3 alasan nyata:

| Kalau artikel LIAR (upload bebas) | Kalau LEWAT MEKANISME mesin |
|---|---|
| Artikel palsu bisa masuk naskah → **naskah mahasiswa rusak** | Setiap artikel **diaudit DOI** dulu ✅ |
| PDF yang diupload belum tentu artikel jurnal (bisa makalah, blog, foto) | Bentuk datanya **seragam** → mesin tetap jalan ✅ |
| Daftar pustaka bisa kacau (penulis/tahun tidak terbaca) | APA 7 **terbentuk otomatis** ✅ |
| Hasil mesin **tidak konsisten** (kadang bagus, kadang rusak) | Hasil **selalu sama mutunya** ✅ |
| Mahasiswa bisa **dituduh plagiat/fabrikasi** | Terlindungi ✅ |

⇒ Sama seperti aturan Bos di proyek lain: **"satu pintu"**, jangan banyak jalur.

---

## 🎯 BENTUK YANG WULAN USULKAN — "2 CARA MASUK, 1 PINTU AUDIT"

```
   2 CARA MASUK ARTIKEL              ↓              1 PINTU AUDIT
┌──────────────────────┐                            ┌──────────────┐
│ A. KOTAK TULIS       │                            │              │
│    (judul/penulis/   │──────┐                     │  AUDIT DOI   │
│     tahun/DOI/link)  │      │                     │  (CrossRef)  │
└──────────────────────┘      │                     │              │
                              ├────────────────────→│  + cek       │
┌──────────────────────┐      │                     │    bentuk    │
│ B. TEMPEL LINK/DOI   │──────┘                     │    artikel   │
│    (mesin yang       │                            │              │
│     carikan data)    │                            └──────┬───────┘
└──────────────────────┘                                   │
                                                  ┌────────┴────────┐
                                                  │                 │
                                            ✅ LOLOS          ⚠️ TIDAK LOLOS
                                              │                    │
                                     masuk naskah +        ditampilkan jujur
                                     daftar pustaka        TIDAK dipakai
```

⇒ **Yang DILARANG = upload PDF/berkas liaran.** Tidak ada tombol "unggah PDF".
⇒ **Yang BOLEH = memasukkan artikel lewat 2 cara DI ATAS** — dua-duanya
**lewat audit** yang sama.

---

## 💡 3 IDE WULAN (yang lebih bagus & praktis)

### IDE 1 — "Tempel DOI, mesin yang urus sisanya" ⭐ (paling praktis)
User **cuma perlu tempel DOI** (atau link artikel). Mesin:
1. ambil data dari CrossRef (`cari_crossref` **SUDAH ADA**)
2. lengkapi penulis, tahun, judul, jurnal
3. audit
4. masukkan ke daftar

```
Tambah artikel:
  [ 10.29040/jie.v4i01.900              ]  [ Tambahkan ]

   → ✅ Ditemukan: Yusnia & Burhanudin (2020)
     Customer Experience, Diferensiasi Produk...
     Jurnal Ilmiah Edunomika
     Ditambahkan ke daftar.
```

⇒ User **tidak perlu mengetik APA 7 manual.** Mesin yang urus.
⇒ Kalau DOI palsu → **langsung ketahuan** (CrossRef tidak menemukan).

### IDE 2 — "Kotak isian terkunci" (kalau user tidak punya DOI)
Untuk artikel yang tidak punya DOI (mis. artikel Garuda), user mengisi kotak yang
**bentuknya sudah ditentukan mesin**:
```
Judul     : [_______________________________]  (wajib)
Penulis   : [_______________________________]  (wajib)
Tahun     : [____]                              (wajib, 4 angka)
Jurnal    : [_______________________________]  (wajib)
Link/DOI  : [_______________________________]  (opsional)
Sumber    : [ Garuda ▾ ]  ← dropdown, bukan ketik bebas
```
⇒ **Bukan "upload bebas"** — mesin **memaksa bentuk yang benar**. Kalau ada
kolom kosong → **ditolak**: *"Penulis belum diisi — artikel belum bisa dipakai."*

### IDE 3 — 🚨 PAGAR "PENGARUH TERBATAS" (ide terpenting Wulan)
Masalahnya kalau artikel manual **dipakai bebas**: user bisa menyelipkan
**1 artikel jelek** yang **mendominasi** seluruh bab (karena mesin memberi bobot
pada semua artikel sama rata).

**Usul Wulan — batasi porsi:**
| Aturan | Nilai |
|---|---|
| Maks artikel manual per bab | **misal 30%** dari total (sisanya dari AI) |
| Kalau user menambah 10, dan AI punya 20 | maks 6 manual (30% dari 26) |
| Alasan | Mesin tetap **didominasi sumber teraudit otomatis** → mutu terjaga |
| Ditampilkan jujur | *"Kamu bisa menambah maksimal 3 artikel lagi untuk bab ini."* |

⇒ Ini **kunci "menjaga mesin tetap konsisten"** yang Bos minta — bukan cuma
audit per artikel, tapi juga **keseimbangan keseluruhan**.

---

## 🧩 BENTUK DATA YANG WAJIB SAMA (kunci "konsisten")

Ini yang membuat mesin bisa menerima artikel manual **tanpa merusak apa pun** —
bentuk datanya **sudah baku** (terukur di `pustaka.py`):

| Kunci | Isi | Dari mana |
|---|---|---|
| `title` | judul artikel | API / kotak isian |
| `authors` | penulis | API / kotak isian |
| `year` | tahun | API / kotak isian |
| `journal` | nama jurnal | API / kotak isian |
| `doi` | DOI | API / kotak isian |
| `garuda_id` | ID Garuda (kalau ada) | API / kotak isian |
| `cited_by_count` | jumlah sitasi | API / 0 kalau manual |
| **`doi_status`** | **`verified` / `no_doi` / `unverified`** | **HASIL AUDIT — bukan dari user** |

⇒ **`doi_status` TIDAK BISA diisi user** — itu **hasil audit mesin**.
Inilah yang membuat artikel manual **tidak bisa "mengaku-aku" terverifikasi**.

---

## ⚠️ YANG WULAN WAJIB SEBUT JUJUR

1. **Yang SUDAH ADA:** `audit_doi()` (`pustaka.py:381`), `cari_crossref()`
   (`:401`), `daftar_pustaka_apa7()` (`:696`), bentuk data baku.
   ⇒ **Semua bahan pagarnya sudah ada.** Tidak perlu bikin dari nol.
2. **Yang BELUM ADA:**
   - Pintu masuk artikel manual (2 cara di atas) → **belum ada UI**
   - `bangun_isi()` **belum menerima** artikel kiriman (`kerangka.py:354` masih
     cari ulang sendiri)
   - Pagar porsi (IDE 3) → **belum ada**
3. **Satu risiko yang perlu Bos sadari:** kalau user **tidak punya DOI** dan
   **tidak ada di Garuda**, artikelnya akan **selalu ⚠️ tidak terverifikasi** —
   artinya **tidak bisa dipakai**. Ini **memang disengaja** (menjaga mutu),
   tapi perlu pesan yang **hangat**, bukan menakutkan:
   > *"Artikel ini belum bisa kami pastikan keasliannya. Coba tempel DOI-nya
   > atau link Garuda-nya ya — biar bisa dipakai di naskahmu."*

---

## ❓ YANG PERLU DIPUTUSKAN BOS

1. **2 cara masuk** (tempel DOI + kotak isian) — setuju? Atau cukup **1 saja**
   (tempel DOI saja → paling aman)?
2. **Kotak isian** (IDE 2) perlu, atau **hanya DOI** yang boleh?
3. **Pagar porsi 30%** (IDE 3) — perlu, atau semua artikel manual boleh masuk
   sebanyak apa pun?
4. **Artikel ⚠️ tidak terverifikasi** — tetap ditampilkan (dengan tanda), atau
   **ditolak sejak awal** (tidak muncul)?
5. **Sumber yang diizinkan** — hanya Garuda/CrossRef/Scopus, atau user boleh
   memasukkan dari **situs jurnal kampus** juga?

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] Arah Bos ("fleksibel tapi di dalam pagar") **disetujui Wulan** + alasan
- [x] Bahan pagar **SUDAH ADA** (`audit_doi`, `cari_crossref`, bentuk data baku)
- [ ] Ditunggu putusan Bos (5 pertanyaan di atas)
- [ ] DILARANG dikoding sebelum Bos bilang mulai
