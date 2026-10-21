<!-- SOT: KAMUS_25_DAN_SCOPUS_DIAM_12OKT2026.md — catatan temuan kamus 25
     konsep + Scopus diam + ide 3 lapis. STATUS: BELUM DIKODING. -->

# 🔍 KAMUS KONSEP 25 & SCOPUS DIAM — TEMUAN + IDA (12 Okt 2026)

> **STATUS: DOKUMEN CATATAN — BELUM DIKODING.**
> Perintah Bos: *"A tulis dulu di dokumen nanti kerjakan lain waktu"*
> Dokumen ini **memuat apa adanya**, termasuk kesalahan Wulan sendiri.

---

## A. APA ITU "KAMUS 25 KONSEP"

### Bukti dari kode
`app/pustaka.py` baris 3–5 (docstring asli berkas):

```
📌 ASAL (bukan bikin baru — sesuai arahan Bos 26Sep26 "kamu cek dulu di kode,
   dan copy jadikan skill pencarian di EduAi ini"):
   Disalin dari /opt/data/services/jurnalkit/phase1_harvest_v2.py (1.044 baris)
   — HANYA bagian PENCARIAN.
```

### Jadi asalnya
| Pertanyaan | Jawaban (terverifikasi dari kode) |
|---|---|
| Siapa yang membuat? | **BUKAN Wulan.** Bawaan proyek `jurnalkit` |
| Kenapa masuk EduAi? | **Perintah Bos 26Sep26** — "copy jadikan skill pencarian di EduAi" |
| Dasarnya apa? | Skill `penelitian-ilmiah` v2.2 (kerangka **PICO/SPIDER**) + pelajaran `eduai-lab` |
| Kenapa isinya olahraga? | Tema proyek asalnya (olahraga/kesehatan) |

### Isi 25 konsep (terukur 12 Okt 2026)
```
 1. aktivitas fisik       14. minat belajar
 2. siklus menstruasi     15. hasil belajar
 3. amenore               16. literasi digital
 4. atlet                 17. umkm
 5. remaja                18. ekonomi digital
 6. keputusan pembelian   19. tata kelola
 7. kualitas produk       20. etika bisnis
 8. harga                 21. pendidikan tinggi
 9. promosi               22. kesehatan mental
10. kepuasan kerja        23. kecemasan
11. kinerja karyawan      24. cricket    ← sisa tema lama
12. kepemimpinan          25. cedera     ← sisa tema lama
13. motivasi
```

---

## B. 🚨 TEMUAN 1 — "SCOPUS DIAM" PADAHAL KUNCINYA SUDAH AKTIF

### Kejadian
12 Okt 2026 kunci Scopus `EDUAI_SCOPUS_KEY` **dihidupkan** di produksi
(sebelumnya tidak pernah masuk container). Tapi saat diuji:

```
Tema "relationship marketing"   → Scopus: 0 hasil ❌
Tema "aktivitas fisik siklus menstruasi" → Scopus: 15 hasil ✅
```

### Akar (TERUKUR, bukan dugaan)
```
kata_kunci(tema)  → hasilkan 'konsep' (dari kamus) + 'sisa' (kata mentah user)
                              ↓
                 'konsep' → rumus_scopus()  ✅ dipakai
                 'sisa'   → TIDAK PERNAH DISERAHKAN ke Scopus ❌
```

**Bukti grep:** `kw['sisa']` **dihitung** (`pustaka.py:707`) dan **dikembalikan**
(`pustaka.py:710`), tetapi **tidak ada satu pun pembaca `kw['sisa']`** di jalur
pencarian (`grep "\['sisa'\]" app/*.py` → nol pada pustaka).

### Kenapa OpenAlex selamat, Scopus tidak
| Mesin | Jaring pengaman bila kamus kosong | Hasil |
|---|---|---|
| **OpenAlex** | ADA — `_frasa_en = frasa or ' '.join(kw_en[:1]) or ' '.join(kw_id[:1])` | ✅ dapat 7 hasil |
| **Scopus** | **TIDAK ADA** — hanya menerima `konsep` | ❌ query kosong → 0 |
| Garuda | ikut konsep ID | ❌ 0 |
| CrossRef | ikut konsep EN | ❌ 0 |

⇒ **Lubang ada di Scopus/Garuda/CrossRef, bukan di kamus saja.**

---

## C. ⚠️ TEMUAN 2 — DOKUMEN LAMA MENJANJIKAN LEBIH DARI KENYATAAN

Dokumen `IDE_MESIN_PENCARI_2_JALUR_06OKT2026.md` (baris ~171) menulis:

> *"**Kabar baik:** `kata_kunci()` **tetap mengambil 'sisa' kata** yang tak
> dikenali kamus → jadi istilah khusus **tetap dipakai** sebagai kata kunci
> tambahan, hanya **tidak terkelompok rapi**."*

**Status klaim itu: SALAH untuk Scopus/Garuda/CrossRef** (terukur 12 Okt 2026).
Benar hanya untuk OpenAlex. Dokumen itu **belum menyebut** bahwa Scopus tidak
punya jaring pengaman.

⇒ **Pelajaran:** dokumen bisa "berjanji" melebihi kode. **Wajib diukur ulang**
sebelum dipakai sebagai dasar (sama seperti kasus SOT/flag 06 Okt 2026).

---

## D. ⚠️ KESALAHAN WULAN DALAM SESI INI (dicatat supaya tidak terulang)

| # | Kesalahan | Akar | Akibat |
|---|---|---|---|
| 1 | Menyalin kunci OpenAlex dari `/opt/data/services/jurnalkit/` (**proyek lain**) | Tidak membaca `ATURAN_BATAS_PROYEK_03OKT2026.md` dulu | Melanggar aturan keras Bos 03 Okt |
| 2 | Mengarang teori "mount Docker membeku / overlay / propagation" | **Menebak** tanpa membaca kode & dokumen | Menyesatkan; akarnya sebenarnya sederhana (kunci memang tak pernah masuk) |
| 3 | Membuat folder `_rahasia/` + mount baru + mekanisme baru | Tidak mencari pola yang **SUDAH ADA** (`.env` + `--env-file`) | Melanggar "jangan buat baru" |
| 4 | Menyetel label mutu **lebih dulu** sebelum kunci hidup | Urutan kerja keliru | Waktu terbuang; tanda mutu sia-sia saat Scopus masih diam |

**AKAR SEMUA: Wulan tidak MEMBACA dulu.** Pola `.env` (dipakai `EDUAI_ROUTER_KEY`,
`PAKASIR_API_KEY`) sudah ada sejak lama dan jelas di `app/config.py`.

**PERBAIKAN YANG SUDAH DILAKUKAN (12 Okt 2026):**
- ✅ Folder `_rahasia`, `_kunciuji`, `zz_uji_baru` dibuang
- ✅ Mount `_rahasia` dibuang dari `jalankan.sh`
- ✅ Kunci lewat **`.env`** (`EDUAI_SCOPUS_KEY`, `EDUAI_OPENALEX_KEY`) — **pola resmi**
- ✅ `pustaka.py` baca dari `os.getenv()` seperti kunci lain
- ✅ `jalankan.sh` **melaporkan** status kunci tiap deploy (jangan diam-diam)
- ✅ **Terbukti produksi:** 4 mesin hidup → Scopus 15 · OpenAlex 15 · Garuda 10 · CrossRef 10

---

## E. 💡 IDA WULAN — 3 LAPIS, NOL MESIN BARU

### Prinsip yang dipakai (aturan Bos sendiri)
- *"Jev selalu terdepan sebelum mesin dan AI"* (07 Okt 2026)
- *"Mesin tidak bisa menangani/identifikasi berbagai macam bentuk naskah. Maka perlu Jev."*
- *"AI GRATIS sampai kerangka"* (putusan 06 Okt 2026)
- *"jangan buat baru, lebih optimal kan yang sudah ada"* (02 Okt 2026)

### ⛔ YANG **TIDAK** DILAKUKAN
**Menambah isi kamus** (mis. 25 → 200 konsep) = **tambal gejala**.
Judul mahasiswa tak terbatas ⇒ kamus **tak akan pernah cukup**, dan menambah
daftar manual = pekerjaan per-naskah ⇒ **melanggar prinsip skala "jutaan naskah"**.

### ✅ USULAN: 3 LAPIS

```
┌─ LAPIS 1 — KAMUS (SUDAH ADA, Rp 0, instan)
│    judul → konsep → cari. Kena untuk judul umum. (mayoritas)
│
├─ LAPIS 2 — JARING PENGAMAN (BARU, KECIL — ±5 baris)
│    kamus gagal → pakai kata mentah user APA ADANYA.
│    Terapkan KE SEMUA mesin (Scopus, Garuda, CrossRef) — pola yang
│    OpenAlex SUDAH pakai. ⇒ Scopus hidup untuk SEMUA judul.
│    ⚠️ "Sisa" itu tidak boleh diabaikan — atau jangan dihitung sama sekali.
│
└─ LAPIS 3 — AI (SUDAH ADA, hanya kalau perlu)
     L1+L2 hasilnya jelek → AI menyusun kata kunci PICO.
     Dibayar SEKALI saat buat kerangka (sesuai putusan Bos: GRATIS s/d kerangka).
     ⚠️ Bila AI tak dipakai → JANGAN mengarang; katakan terus terang.
```

### Kenapa cocok dengan EduAi
| Alasan | Bukti |
|---|---|
| Nol mesin baru | Kamus, AI, Jev semuanya **sudah ada** |
| Satu pintu | Semua lewat `pustaka.cari_semua()` — tidak ada jalur paralel |
| Tidak menebak | Kamus gagal → pakai kata user atau **tanya AI**, bukan dikarang |
| Skala jutaan naskah | Bukan daftar manual yang harus dirawat selamanya |
| Jujur ke user | Kalau hasilnya sedikit, **bilang apa adanya** (pola notifikasi hangat Bos) |

### Pertanyaan yang HARUS dijawab sebelum koding
1. **Lapis 2:** kata mentah user dipakai **utuh** atau disaring (buang kata umum ID)?
   Risiko: kata umum ("pengaruh", "terhadap") merusak query Scopus.
2. **Lapis 2:** berapa batas kata (Scopus lebih rewel daripada OpenAlex)?
3. **Lapis 3:** kapan dianggap "hasil jelek"? (mis. < 3 artikel, atau 0)
4. **Lapis 3:** AI mana — 9router combo `EduAi` (sama seperti jalur lain)?
5. Apakah user **diberi tahu** saat kamus gagal + AI dipakai? (usul: YA, jujur)
6. Apakah ada **jatah** untuk Lapis 3? (putusan lama: AI gratis s/d kerangka)
7. **Jev** — apakah ikut? (Jev = struktur. Kata kunci ≠ struktur ⇒ usul Wulan: **TIDAK**)

---

## F. SISA PEKERJAAN (bila Bos buka nanti)

| # | Hal | Status |
|---|---|---|
| 1 | Kunci Scopus + OpenAlex di produksi | ✅ SELESAI 12 Okt 2026 |
| 2 | Tanda mutu jurnal (SJR/CiteScore) di hasil | ✅ SELESAI (11 dari 23 artikel bertanda) |
| 3 | **Lapis 2 — jaring pengaman Scopus/Garuda/CrossRef** | ⬜ **BELUM** (dokumen ini) |
| 4 | **Lapis 3 — AI penyusun kata kunci** | ⬜ BELUM, perlu putusan |
| 5 | **Ukur** berapa % judul nyata yang gagal (bukti angka) | ⬜ BELUM |
| 6 | Tanda koma untuk kata kunci manual | ⬜ BELUM (temuan 06 Okt) |
| 7 | Tampilan tanda mutu **dilihat mata** di HP | ⬜ BELUM (potret kena login) |

---

## G. CARA BALIK KE DOKUMEN INI
Bos cukup bilang **"lanjut kamus/scopus"** atau **"buka dokumen kamus 25"**.
Sebelum kerja: **UKUR DULU** (bagian F nomor 5) → baru putuskan Lapis 2/3.
**DILARANG DIKODING sampai Bos bilang "mulai".**
