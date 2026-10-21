<!-- SOT: RANCANGAN_KOTAK_TEORI_13OKT2026.md — racangan Wulan atas ide Bos
      (Bank Teori + Grand Theory + Teori Variabel + Kata Kunci per Hubungan).
      STATUS: BELUM DIKODING. Menunggu putusan Bos. -->

# 📚 RANCANGAN "KOTAK TEORI" — 1 Bank, 1 Fungsi AI, 3 Pemakai

> **Ide asal = BOS.** Wulan hanya menyusun agar rapi, sinkron dengan mesin
> yang sudah ada, dan tidak bentrok. Perintah Bos: *"coba kamu susun yang
> rapi dan sinkron dengan pencarian kata kunci… berikan ide kamu yang
> sederhana agar semua ide saya dan mesin sinkronisasi dan presisi."*
> Dan: *"Grand theory SOR itu contoh saja, masih banyak grand theory lain
> tergantung judul user."*

---

## A. MASALAH YANG DIPECAHKAN

| # | Masalah nyata (terukur) | Bukti |
|---|---|---|
| 1 | Larik judul di luar kamus → hasil NGACO | 13Okt26: "Analisis Faktor-Faktor…" → AlphaFold, GLOBOCAN ❌ |
| 2 | Teori dipilih dari INGATAN AI → bisa halusinasi | aturan Bos, 13Okt26 |
| 3 | Kata kunci disusun per JUDUL, bukan per HUBUNGAN | `kata_kunci()` = 1 tema → 1 query |
| 4 | User tidak tahu grand theory + teori variabel apa yang cocok | belum ada fitur |

---

## B. ARSITEKTUR — SATU BANK, SATU FUNGSI, TIGA PEMAKAI

```
              ┌────────────────────────────────────────┐
              │  data/bank_teori.json                  │
              │  10 entri · 6 grand_theory · 4 variabel │
              │  DOI dicek Wulan 8/8 NYATA (13Okt26)    │
              │  Bos bisa TAMBAH sendiri (format sama)  │
              └────────────────┬───────────────────────┘
                               │
              ┌────────────────▼───────────────────────┐
              │  app/teori.py  (BARU, 1 berkas kecil)  │
              │  teori_dari_judul(judul, naskah=None)  │
              │  Tugas AI: PILIH dari bank — BUKAN karang
              └────────────────┬───────────────────────┘
                               │  1 panggilan AI (cache)
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
   PEMAKAI 1              PEMAKAI 2              PEMAKAI 3
   Grand Theory           Teori per Variabel     Kata Kunci per Hubungan
   (1 payung model)       (1 ahli per konstruk)  (X1→Z · Z→Y · dst)
```

**Kenapa ini sederhana:** ketiganya keluar dari **1 pembacaan judul yang
sama** ⇒ tidak ada 2 mesin yang bisa berbeda pendapat. Sesuai aturan Bos
*"jangan buat baru — lebih optimal kan yang sudah ada"*.

---

## C. ALUR SINKRON (hulu → hilir)

```
USER tulis JUDUL
      │
      ▼
① AI PECAH JUDUL → VARIABEL
   Y (outcome) · X (penyebab) · Z (mediator/moderator bila ada)
   ← INI PONDASI SEMUA LANGKAH DI BAWAH
      │
      ▼
② AI PILIH grand theory DARI BANK
   (6 pilihan: SOR · TAM · UTAUT2 · TPB · SET · UG)
   → tulis PEMETAAN eksplisit, mis. "X1/X2 = stimulus · Z = organism · Y = response"
   → tidak ada yang cocok ⇒ KATAKAN TERUS TERANG
      │
      ▼
③ AI PILIH teori VARIABEL dari bank
   1 entri per konstruk: X1 → AUTH · X2 → PSI · Z → CE · Y → IB
   → sitasi APA diambil PERSIS dari bank (bukan dari ingatan AI)
      │
      ▼
④ TAMPIL KE USER — pintu persetujuan (yang diminta Bos)
   ┌──────────────────────────────────────────────────────┐
   │ 🎯 GRAND THEORY: S-O-R — Mehrabian & Russell (1974)   │
   │    Pemetaan: X1/X2 = stimulus · Z = organism · Y = response │
   │ 📚 TEORI PER VARIABEL                                 │
   │    X1 Keaslian Streamer      → Audrezet dkk. (2020) ✅ │
   │    X2 Interaksi Parasosial   → Horton & Wohl (1956) ✅ │
   │    Z  Keterlibatan Pelanggan → Brodie dkk. (2011) ✅   │
   │    Y  Pembelian Impulsif     → Rook (1987) ✅          │
   │    [✅ Benar]  [🔄 Ganti teori]  [❌ Lewati]            │
   └──────────────────────────────────────────────────────┘
      │  user SETUJU (inilah pintu penentu)
      ▼
⑤ MODEL JADI JELAS (X1→Z→Y) — dari jawaban user, BUKAN tebakan
      │
      ▼
⑥ BARU kata kunci PER HUBUNGAN:
   X1→Z · X2→Z · Z→Y · X1→Y · X2→Y
   ┌──────────────────────────────────────────────────────┐
   │ X1→Z: "streamer authenticity" AND "customer engagement" │
   │       Scopus: TITLE-ABS-KEY("streamer authenticity" AND …) │
   │       Garuda: keaslian streamer keterlibatan pelanggan  │
   │       OpenAlex: api.openalex.org/works?search=…        │
   └──────────────────────────────────────────────────────┘
      │
      ▼
⑦ 4 MESIN NYATA cari (Scopus·OpenAlex·Garuda·CrossRef) → audit DOI
```

---

## D. 3 REM ANTI-HALUSINASI (menjawab kekhawatiran keras Bos)

| # | Rem | Cara kerja (terukur) |
|---|---|---|
| 1 | **AI MEMILIH, bukan mengingat** | Teori **hanya** dari `bank_teori.json`. Tidak ada ⇒ wajib jawab *"tidak ada di bank — butuh verifikasi manual"*. Dilarang menulis nama/tahun/DOI dari ingatan |
| 2 | **DOI dicek MESIN** | Semua DOI bank → `audit_doi()` (pustaka.py:489) ke CrossRef. Status lama: `terverifikasi_crossref` ✅ / `buku_tanpa_doi_validasi_manual` (buku, tidak bisa auto) |
| 3 | **MODEL tidak ditebak** | Kata kunci per-hubungan **HANYA** keluar setelah user setujui model (langkah ⑤). Sebelum itu → kata kunci **per judul** (yang sudah jalan sekarang) |

**Bukti rem 1 bekerja (terukur 13Okt26):** pencocokan kata KASAR hanya
menemukan teori untuk **2 dari 3** judul uji (judul "stres kerja perawat" →
0 teori). ⇒ AI memang harus jadi **pemilih**, bukan pencocok kata.
Dan kalau bank kosong → **bilang kosong**, bukan dikarang.

---

## E. LAPIS JADI (tidak ada yang dibuang)

```
JALUR KATA KUNCI (3 lapis — semuanya sudah/akan ada):
  LAPIS 1  KAMUS 25 frasa       instan, Rp 0        [SUDAH ADA]
  LAPIS 2  AI + BANK TEORI      presisi, 1 panggilan [BARU]
  LAPIS 3  4 MESIN NYATA        artikel + audit DOI [SUDAH ADA]

YANG TIDAK DISENTUH:
  contoh_judul() statis per bidang · pustaka.cari_semua() ·
  audit_doi() · daftar_pustaka_apa7() · pagar_artikel.py ·
  jatah.py (AI gratis · manual 2×/minggu) · bank_kuota
```

**Yang DIHAPUS:** lencana "TANPA TOKEN" di bagian ① (putusan Bos 1b).

---

## F. URUTAN KERJA (diusulkan)

```
TAHAP 1 — selesaikan KATA KUNCI AI di 2 pintu (yang sedang jalan)
   2 putusan kecil tersisa: pesan 0-hasil · tombol otomatis/manual

TAHAP 2 — KOTAK TEORI (rancangan ini)
   a. app/teori.py — baca bank + 1 fungsi AI pilih + cache
   b. gerbang BERGIGI (bank kosong → wajib bilang kosong; DOI palsu → tolak)
   c. uji 10 judul nyata → ukur: berapa % dapat grand theory + teori variabel
   d. sambung ke pintu yang SUDAH ADA (Langkah 4 /mulai + Referensi)
   e. potret + deploy (izin Bos)

TAHAP 3 — kata kunci PER HUBUNGAN (setelah model terbaca)
   ⚠️ WAJIB setelah model ada — jangan menebak model dari judul
```

---

## G. YANG BELUM DIUKUR (jujur)

1. Apakah AI **benar** memilih grand theory yang cocok? — belum diuji dengan
   10 judul nyata (baru diuji pencocokan kata kasar).
2. Berapa lama 1 panggilan AI untuk langkah ②③? (patokan: 5,4 dtk dari uji
   kata kunci 13Okt26).
3. **Bank baru 10 entri** ⇒ judul di luar bidang konsumen/teknologi
   (mis. kesehatan, pendidikan, hukum) akan **kosong**. Perlu diputuskan:
   pintu tumbuh bank atau manual.
4. Apakah perlu Jev di jalur teori? (usul Wulan: **TIDAK** — teori bukan
   urusan struktur naskah; Jev = penjaga STRUKTUR, bukan pemilih isi).

---

## H. CARA BALIK
Bos bilang **"lanjut kotak teori"** → baca berkas ini + bagian teratas
`FLAG_LANJUT_DISINI.md`.
