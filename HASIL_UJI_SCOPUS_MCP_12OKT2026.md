<!-- SOT: UJI REPO SCOPUS-MCP-EXTENDED + METRIK JURNAL — 12 Okt 2026 -->
# 🔬 HASIL UJI ENDPOINT SCOPUS + TINJAUAN REPO `scopus-mcp-extended`

**Tanggal:** 12 Okt 2026
**Pertanyaan Bos:** *"Cek repo ini. Apakah pencarian scopus kita akan lebih baik?"*
→ `https://github.com/oliviercaron/scopus-mcp-extended`

**KESIMPULAN:** ❌ **TIDAK.** Repo itu **JANGAN dipakai**. Tetapi uji ini
menemukan **1 peluang nyata** (metrik jurnal) yang layak dipakai.

---

## 1. Mesin pencarian Scopus kita SEKARANG

**Pakai QUERY SENDIRI — bukan MCP.** Terbukti dari kode:

- `grep -rniE "mcp|model.context.protocol" app/*.py` → **KOSONG** (nol MCP)
- `app/pustaka.py:52` → `SCOPUS_URL = 'https://api.elsevier.com/content/search/scopus'`
  (API RESMI Elsevier, dipanggil langsung)
- `app/pustaka.py:580` → `rumus_scopus()` menyusun query sendiri:
  `TITLE-ABS-KEY("konsep A" OR sinonim) AND TITLE-ABS-KEY("konsep B" OR sinonim)`
  (aturan: **AND antar konsep, OR di dalam konsep**, dibatasi 3 konsep)
- 4 mesin, semua API resmi langsung: Scopus · OpenAlex · Garuda · CrossRef
- Satu pintu gabungan: `cari_semua()` (`app/pustaka.py:724`)

---

## 2. Isi repo `scopus-mcp-extended`

MCP server untuk **25 alat** Scopus/ScienceDirect/PlumX/Embase.
Fitur yang ditawarkan: cari penulis, cari jurnal, abstrak, daftar referensi,
siapa mengutip, altmetrics (PlumX), BibTeX, cache per-jenis, retry otomatis.

**Dari README repo itu sendiri** (kutipan resmi Elsevier):

> *"An insttoken is an additional security token... Insttokens are only available
> for customers or partners working on behalf of a customer..."*

> Access-controlled: **Citation Overview API · refEID field · Index Keyword field ·
> DOCUMENTS view** — dibuka **hanya atas permintaan** ke Elsevier.

⇒ Artinya: sebagian besar alat andalannya **BUTUH LANGGANAN INSTITUSI**
(bukan sekadar kunci API biasa).

---

## 3. 🧪 UJI NYATA — 11 endpoint, kunci Scopus KITA

Dijalankan **di dalam container** dengan kunci kita (`scopus_api_creds.json`,
label "Penelitian Bot"), tanpa insttoken, tanpa langganan:

| # | Endpoint | HTTP | Keterangan |
|---|---|---|---|
| 1 | **search_scopus** (yang KITA pakai) | **200** ✅ | totalResults=4776, ada isi |
| 2 | search + field `REFEID` (siapa mengutip) | 400 | `INVALID_INPUT · Use of certain field restrictions... not allowed` |
| 3 | abstract by DOI | 404 | `RESOURCE_NOT_FOUND` |
| 4 | citation count (batch) | 403 | `Requestor configuration settings insufficient` |
| 5 | citation overview | 400 | `INVALID_INPUT · No resource identifier` |
| 6 | author search | 401 | `The requestor is not authorized` |
| 7 | affiliation search | 401 | `The requestor is not authorized` |
| 8 | **journal metrics by ISSN** | **200** ✅ | `serial-metadata-response` |
| 9 | ScienceDirect search | 401 | butuh langganan |
| 10 | PlumX altmetrics | 401 | butuh langganan |
| 11 | quota status | 404 | `RESOURCE_NOT_FOUND` |

```
HIDUP (2): ① search_scopus  ⑧ journal metrics
MATI  (9): sisanya
```

### Kenapa repo itu TIDAK membuat pencarian kita lebih baik

1. **Satu-satunya alat pencariannya = `search_scopus` = PERSIS yang kita pakai.**
   Query yang sama (`TITLE-ABS-KEY`), database yang sama, API yang sama.
   → **Mutu pencarian TIDAK berubah sedikit pun.**
2. **9 dari 11 alat MATI** dengan kunci kita → kalau dipasang, yang kita dapat
   hanya **tombol-tombol error 401/403**.
3. Repo itu menambah **MCP** = perantara baru, sementara aturan Bos =
   **satu pintu, jangan buat jalur paralel, sederhana > lengkap**.

---

## 4. 🎁 TEMUAN BERHARGA — metrik jurnal HIDUP

Endpoint ⑧ terbukti bekerja. Diuji dengan 3 jurnal (2 nyata + 1 ISSN karangan):

```
Journal of Business Research [0148-2963] → HTTP 200
   SJR 3.498 (@2025) · SNIP 3.083 (@2025) · CiteScore 22.9
   penerbit: Elsevier Inc. · cakupan 1973-2027

Journal of Political Economy [0022-3808] → HTTP 200
   SJR 16.250 (@2025) · SNIP 4.581 (@2025) · CiteScore 11.0
   penerbit: University of Chicago Press

ISSN KARANGAN [0128-1234] → HTTP 404 ✅ RESOURCE_NOT_FOUND
   (pagar bekerja — data tidak bisa asal)
```

**Bisa juga dicari TANPA ISSN:**
```
GET /content/serial/title?title=journal of business research → 200, 3 entri
```

### Yang ADA vs TIDAK ADA di balasan

| Ada ✅ | Tidak ada ❌ |
|---|---|
| SJR (@tahun) · SNIP (@tahun) · CiteScore | **Kuartil (Q1/Q2/Q3/Q4) — KOSONG** |
| Nama jurnal, penerbit, ISSN | Siapa mengutip |
| Cakupan tahun, status open access | Abstrak, penulis, ScienceDirect |
| Cari dari judul jurnal | — |

### 🔬 UJI KUARTIL — SELESAI 12Okt26 (bukti terukur)

Dugaan awal: "kuartil mungkin bisa dihitung dari SJR". **Hasil ujinya:**

```
Journal of Business Research  SJR=3.498   SNIP=3.083  CiteScore=22.9   (Q1 sebenarnya)
Journal of Political Economy  SJR=16.250  SNIP=4.581  CiteScore=11.0   (Q1 sebenarnya)
American Economic Review      SJR=23.489  SNIP=7.228  CiteScore=19.6   (Q1 sebenarnya)
Jurnal Indonesia (karangan)   → HTTP 404
ISSN karangan [0128-1234]     → HTTP 404 ✅ (pagar bekerja)

Sumber kuartil publik uji:
  SciMago (scimagojr.com) → HTTP 403 ❌ DIBLOKIR (menolak akses otomatis)
```

**KESIMPULAN KUARTIL:**
- ❌ **Elsevier TIDAK mengirim kuartil** (dibuktikan, bukan dugaan)
- ❌ **SciMago (pemilik sah kuartil) menolak** akses otomatis → **403**
- ⇒ **Kuartil Q1–Q4 TIDAK BISA dipastikan. JANGAN ditampilkan.** Menulis "Q1"
  tanpa dasar = **karangan** (melanggar prinsip "jangan menebak").
- ✅ Yang **BISA & JUJUR**: tampilkan **SJR + SNIP + CiteScore** apa adanya.
  Angka itu sudah bicara sendiri (SJR 16,2 jelas lebih kuat dari SJR 3,5).

**Status kuartil: ❌ TUTUP — tidak dikerjakan. Alasan: tidak ada sumber sah yang bisa diakses.**

---

## 5. NILAI NYATA untuk EduAi (kalau nanti dipakai)

Saat user mencari artikel di fitur Referensi, kita bisa **menampilkan mutu
jurnalnya** (SJR/CiteScore) → user tahu "artikel ini dari jurnal kuat atau lemah".

**Sesuai putusan Bos:** nol MCP · nol langganan · nol mesin baru —
cuma memakai endpoint yang **sudah diizinkan** kunci kita.

**Status:** ⏳ IDE, belum diputuskan Bos, belum dikoding.

---

## 6. ⛔ JANGAN DIULANG

1. **Jangan pasang repo `scopus-mcp-extended`.** 9/11 alatnya mati dengan kunci
   kita; alat pencariannya identik dengan yang sudah ada.
2. **Jangan minta langganan institusi** untuk ini — laporkan ke Bos dulu.
3. **Jangan janji kuartil Q1-Q4** sebelum dihitung/diuji.
4. **Jangan pakai kredensial proyek lain** (aturan keras 03Okt26). Uji ini
   memakai kunci Scopus milik proyek ini (`/opt/data/home/scopus_api_creds.json`).

## 7. BERKAS UJI

| Berkas | Isi |
|---|---|
| `_sketsa/uji_endpoint_scopus.py` | Uji 11 endpoint repo (200 vs 401/403/404) |
| `_sketsa/uji_metrik_jurnal.py` | Uji metrik jurnal + ISSN karangan + cari dari judul |
