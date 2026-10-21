# ❓ JEV UNTUK MESIN PENCARI JURNAL? — JAWABAN (06 Okt 2026)

> 🚩 **DIPERBARUI 07 Okt 2026 — CARA PAKAI JEV DI SINI SUDAH USANG.**
> Sebagian isi catatan ini dibuat waktu Wulan **belum membaca dokumentasi resmi**,
> jadi ada **klaim yang keliru & berbahaya** (mis. *"skema Jev tertutup / hanya 3 nama"*,
> *"Jev tidak stabil"*, *"hanya 2 tipe sah"*, *"criteria boleh string"*).
> ⇒ **ACUAN TUNGGAL cara pakai Jev sekarang:** `PANDUAN_PAKAI_JEV.md`
>   + skill `typesafe-jev` (dokumentasi RESMI `docs.typesafe.ai`).
> ⇒ Blok lama **TIDAK dihapus** (riwayat) — tapi **DILARANG dipakai sebagai panduan**.
> ⇒ Penjaga: `_gerbang_skema_jev.py` + `_uji_gigi_skema_jev.py`.



> Pertanyaan Bos 06 Okt 2026 (verbatim):
> *"Bisa tidak mesin pencari ini melibatkan jev? Atau tidak perlu?"*

---

## 🎯 JAWABAN WULAN: **TIDAK PERLU.** Dan ini alasannya (bukan opini — terukur)

---

## 📌 APA ITU JEV (terverifikasi dari kode `app/satpam.py`)

Jev = **penjaga STRUKTUR naskah**. Pagarnya tertulis di kode sendiri:

```
satpam.py:15   P3 HANYA MENILAI STRUKTUR — tidak menyentuh isi/layout naskah
```

### Jev hanya menjawab **4 pertanyaan** — semuanya soal BAB:
| # | Pertanyaan Jev | Jawaban |
|---|---|---|
| 1 | Berapa bab yang BENAR-BENAR ada? | 0–8 |
| 2 | Nomor bab semua pakai romawi sah? | ya/tidak |
| 3 | Bab berurutan tanpa melompat? | ya/tidak |
| 4 | Sedalam apa penomoran bertingkat? | 0–5 tingkat |

⇒ **Jev tidak tahu apa pun soal jurnal, artikel, DOI, atau kata kunci.**

---

## ❌ KENAPA JEV TIDAK COCOK UNTUK MESIN PENCARI

### 1. Bidangnya beda total
| Jev | Mesin pencari |
|---|---|
| Menghitung **bab** di naskah | Mencari **artikel** di internet |
| Soal **struktur dokumen** | Soal **relevansi & keaslian artikel** |
| Tidak ada hubungan | — |

Jev **tidak punya alat** untuk menilai artikel. Kamusnya tidak memuat
"DOI", "Scopus", "sitasi", "relevansi".

### 2. Menilai mutu = zona yang Jev SUDAH TERBUKTI GAGAL
Ini **tercatat sebagai putusan, bukan opini**:

> **JEV — BATAS PERAN (putusan 06 Okt 2026):** Jev HANYA 1 peran = `periksa()`
> PETA BAB. **TIDAK ditambah ke modul lain.**
> - `nilai_balasan()` **DICABUT 05 Okt** — 3 percobaan GAGAL (jev-1.13 tak bisa
>   bedakan "memperdalam" vs "menambah yang tak diminta").
> - `parser.py` **TIDAK perlu** Jev — lubangnya sudah ditutup fix-C; aturan murni
>   gratis+instan **LEBIH AMAN** dari AI, manfaat Jev di sana **Rp 0**.
> - **8 modul lain** (jenis/konsistensi/etika/pustaka/gambar/konteks/
>   citation_validator) = menilai **ISI/MUTU** → wilayah yang Jev **SUDAH
>   TERBUKTI GAGAL**.
> - **ATURAN INDUK:** Jev penjaga **STRUKTUR** saja; **GAGAL untuk menilai
>   mutu tulisan.**

⇒ Menilai "artikel ini relevan atau tidak" = **menilai mutu**. Itu **persis
zona yang Jev gagal 3×.**

### 3. Ada alat yang LEBIH BAIK dan SUDAH ADA
Untuk "apakah artikel ini nyata": **`audit_doi()`** — cek ke CrossRef.
⇒ Deterministik, gratis, instan, **sudah terbukti**.
Untuk "apakah nyambung": **`_nyambung()`** + skor kecocokan.

**Mengganti alat yang sudah terbukti dengan AI = menambah biaya + risiko, tanpa manfaat.**

### 4. Mesin pencari TIDAK butuh AI sama sekali (Rp 0)
Mencari artikel = **HTTP request ke API** (Scopus/OpenAlex/Garuda/CrossRef).
Bukan pekerjaan AI. Menambah Jev di situ = **memboroskan token** untuk hal yang
sudah gratis.

---

## ✅ KESIMPULAN

| Pertanyaan | Jawaban |
|---|---|
| Bisa? | **Secara teknis bisa** — tapi... |
| Perlu? | **TIDAK PERLU** |
| Kenapa | (1) bidangnya beda; (2) menilai mutu = zona Jev gagal; (3) alat lebih baik SUDAH ADA (`audit_doi`); (4) mesin pencari Rp 0 tanpa AI |

---

## 🎯 DI MANA JEV MEMANG BERGUNA (kalau Bos mau pakai Jev lagi)

Jev berguna **hanya** kalau ada **masalah STRUKTUR** — misalnya:

| Skenario | Jev berguna? |
|---|---|
| Ada **fitur baru yang membaca bab naskah** untuk mencari referensi per bab | ⚠️ **MUNGKIN** — tapi bab sudah dibaca `state.petakan()` (terbukti). Jev = **lapis tambahan**, Rp 0 bedanya. |
| **Cek artikel itu nyata** | ❌ tidak — pakai `audit_doi()` |
| **Cek artikel nyambung** | ❌ tidak — pakai `_nyambung()` |
| **Pecah judul jadi variabel** | ❌ tidak — pakai `konsep_dari_judul()` |
| **Nilai kualitas hasil pencarian** | ❌ tidak — zona Jev gagal |

---

## 💡 KALAU BOS MAU "AI" DI MESIN PENCARI — yang tepat BUKAN Jev

Kalau Bos memang mau ada AI di mesin pencari (bukan Jev), yang **masuk akal**:

| Kebutuhan | Alat yang TEPAT |
|---|---|
| Pecah judul yang **tidak dikenali kamus** (25 konsep) | **AI biasa** (bukan Jev) — sekali panggil, murah |
| **Terjemahkan** istilah Indonesia → Inggris | **AI biasa** / kamus |
| **Rapikan kata kunci** yang diketik user berantakan | **AI biasa** |

⇒ Semua itu **tugas AI umum (LLM)**, bukan tugas Jev.
**Jev = penjaga struktur naskah.** Jangan dicampur.

**Wulan sarankan pola yang sama seperti keputusan Bos yang sudah ada:**
> *"kata kunci (Rp 0) → AI kalau ragu → manual (penutup)"* — hybrid 3 lapis
> (pola yang Bos sudah pakai di Statistik Lab)

Artinya: **kamus dulu (Rp 0)** → kalau judul tak dikenali, **baru panggil AI**
(1× saja, murah) → user tetap bisa menambah manual.

---

## 📋 STATUS
- [x] Dicatat 06 Okt 2026
- [x] `satpam.py` diperiksa langsung (P3: "HANYA MENILAI STRUKTUR")
- [x] Putusan lama dicek: Jev TIDAK ditambah ke modul lain
- [ ] Ditunggu putusan Bos
- [ ] DILARANG dikoding sebelum Bos bilang mulai
