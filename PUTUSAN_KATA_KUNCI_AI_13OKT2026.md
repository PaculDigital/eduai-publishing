<!-- SOT: PUTUSAN_KATA_KUNCI_AI_13OKT2026.md — keputusan Bos 13 Okt 2026
      (pilihan 1A/2B + PAGAR TANGGUNG JAWAB AI). STATUS: BELUM DIKODING,
      sketsa sudah disetujui. -->

# 🔑 PUTUSAN BOS — KATA KUNCI AI & SARAN JUDUL (13 Okt 2026)

> **PUTUSAN BOS (verbatim):** *"1. A (hapus tulisan tanpa Token) 2. B"*
> dan perintah pagar: *"Tanya apakah ai merekomendasikan itu nanti juga
> bertanggung-jawab dalam pencarian artikel jurnal berdasar keyword dan
> variabel juga. Jangan sampai ai merekomendasikan tapi artikel setelah
> dicari tidak valid atau tidak ada, bahkan variabel juga tidak ada atau
> halusinasi. Saya memastikan hal ini. Karena penting.!"*

---

## A. KEPUTUSAN TERKUNCI

| # | Soal | Putusan | Arti |
|---|---|---|---|
| 1 | Bentuk tampilan sketsa | **A** | Sudah pas → boleh lanjut koding |
| 1b | Tulisan lencana | **HAPUS "TANPA TOKEN"** | Lencana di bagian ① Pilihan EduAi dibuang |
| 2 | Bentuk bantuan AI | **B** | Kata kunci (bisa diubah) **+ beberapa TEMA lengkap siap-cari** — user tinggal klik |

**Berkas sketsa yang disetujui:**
`_sketsa/sketsa_kata_kunci_judul_13okt2026.html`
(potret: `/tmp/sk_referensi.png` · `/tmp/sk_langkah4.png`)

---

## B. 🛡️ PAGAR TANGGUNG JAWAB AI — PERINTAH KERAS BOS

**Inti kekhawatiran Bos:** AI merekomendasikan kata kunci/variabel, tapi
artikel hasil pencariannya tidak ada / tidak valid / variabelnya bahkan tidak
ada = **HALUSINASI**. Bos: *"Saya memastikan hal ini. Karena penting.!"*

### ✅ KENAPA HALUSINASI ARTIKEL **TIDAK MUNGKIN** TERJADI
Pembagian tugas (terukur dari kode, bukan janji):

```
AI   → HANYA menyusun KATA KUNCI (tidak pernah menyebut artikel)
MESIN → artikel 100% dari DATABASE NYATA
        Scopus · OpenAlex · Garuda · CrossRef
KODE → audit DOI ke CrossRef + saring relevansi
```

⇒ AI **tidak diberi kesempatan** menyebut judul artikel. Kalau AI salah
membaca variabel → query salah → **hasil 0 artikel** → user TAHU.
**Tidak ada jalan** dari kata kunci salah menuju artikel palsu.

### 4 LAPIS PAGAR YANG SUDAH ADA (terukur 13 Okt 2026)

| Lapis | Di mana | Bukti |
|---|---|---|
| ① MESIN NYATA | `pustaka.cari_semua()` | 4 mesin paralel, bukan AI |
| ② AUDIT DOI | `pustaka.py:489` `audit_doi()` | docstring: *"pagar anti-halusinasi"* |
| ③ DAFTAR PUSTAKA | `pustaka.py:1508` | `verified` ✅ · `no_doi` ✅ · `unverified` ❌ DIBUANG |
| ④ ATURAN KE AI | `pagar_artikel.py::aturan_prompt()` | 4 aturan: hanya judul+abstrak, jangan menambah, abstrak kurang = jangan klaim |

**Terukur pada pencarian nyata** ("pengaruh kualitas produk…"):
`verified=8 · unverified=0 · no_doi=4` dari 12 artikel.
Semua artikel **TANPA ABSTRAK** ⇒ AI hanya boleh sebut judulnya
(tidak boleh jadi dasar temuan) — **pagar ④ bekerja**.

### ➕ PAGAR BARU YANG DIMINTA (kecil — pakai yang SUDAH ADA)

**Rambu kosong yang JUJUR.** Pesan 0-hasil **sudah ada**
(`referensi.html:377` — *"Belum ada artikel untuk bab ini"*).
Yang ditambah: **memperjelas sebabnya** saat kata kunci datang dari AI.

```
Tombol AI → kata kunci → cari 4 mesin
                            ↓
                    0 artikel?
                            ↓
   ⚠️ "Kata kunci ini belum menemukan artikel — coba ubah
       kata kuncinya." (BUKAN diam-diam kosong, BUKAN artikel karangan)
```

⛔ **DILARANG:** mengisi hasil kosong dengan artikel susulan AI.
⛔ **DILARANG:** menyembunyikan 0 hasil.

---

## C. YANG AKAN DIKODING (Tahap 1 — belum dijalankan)

**1 fungsi AI, 2 pintu** (putusan Bos "A" sesi sebelumnya):

| Pintu | Berkas | Yang ditambah |
|---|---|---|
| Pintu 2 · Referensi | `app/templates/referensi.html` + `app/rute_jurnal.py` | kotak kata kunci + tombol **"EduAi bantu isi"** + chip kata kunci + kartu tema |
| Pintu 1 · Langkah 4 | `app/templates/mulai.html` + `app/rute_alur.py` | tombol **"Minta saran judul dari EduAi"** di kotak judul |

**Yang TIDAK diubah:** bagian ② "Pencarian kamu" · ③ "Tambah manual" ·
daftar statis contoh judul per bidang · satu mesin `pustaka.cari_semua()`.

**Yang DIHAPUS:** lencana "TANPA TOKEN" di bagian ① (putusan 1b).

**Cache WAJIB:** judul/tema sama → **0 panggilan AI** (hemat + cepat),
pola sama seperti cache kutipan Scite (`_SCITE_KUTIPAN_CACHE`).

---

## D. URUTAN KERJA (sesuai kebiasaan proyek)

```
1. Kalibrasi pagar (bagian C): uji AI petakan 10 judul NYATA
   → ukur: berapa % dapat artikel > 0 (bukti angka, bukan klaim)
2. Koding: 1 fungsi AI `kata_kunci_dari_ai()` + cache
3. Sambung ke 2 pintu (tanpa mesin/tabel/halaman baru)
4. Gerbang BERGIGI (disuntik rusak WAJIB gagal)
5. Potret + MATA (verifikasi ke sumber lewat CDP innerText)
6. Deploy — IZIN BOS DULU
```

---

## E. CARA BALIK
Bos bilang **"lanjut kata kunci AI"** → baca berkas ini + bagian teratas
`FLAG_LANJUT_DISINI.md`.
