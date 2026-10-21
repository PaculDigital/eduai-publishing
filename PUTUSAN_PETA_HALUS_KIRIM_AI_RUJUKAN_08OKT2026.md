# 🔖 PUTUSAN BOS — PETA HALUS · CARA KIRIM KE AI · ATURAN RUJUKAN

> **08 Okt 2026 · TERKUNCI · hasil DISKUSI (belum dikoding)**
> Konteks: peta halus (sub-bab) untuk **Kolaborasi** — supaya AI **tidak salah**
> merevisi bagian.

---

## §A · CARA KIRIM BAGIAN KE AI — PUTUSAN: **C** (potongan + peta naskah)

**UJI 2 terlaksana** (`_uji_2_cara_kirim.py` + `_saji_uji2_3cara.py`, naskah Tesis 78,
bagian `2.1.5 Komitmen Perusahaan` baris 1828–1872, model asli `cb/deepseek-v4.1-flash`):

| Cara | Bahan dikirim | Hasil (penilaian BOS) |
|---|---|---|
| A | BAB II penuh (60.288 kar) | cukup |
| B | potongan saja (980 kar) | cukup |
| **C** | **potongan + PETA naskah (1.253 kar)** | **🏆 PALING BAGUS** |

**⇒ PUTUSAN: kirim POTONGAN + PETA NASKAH.**

Alasan: AI tahu **apa yang direvisi** DAN **di mana dia berada dalam naskah**
(bab induk · sub-bab sebelum/sesudah) ⇒ tidak salah sasaran, tidak kehilangan
konteks. Kekhawatiran Bos (AI bingung/sempit konteks) **TIDAK terjadi** — ketiga
cara menghasilkan panjang mirip & tetap fokus ke sub-bab yang benar.

⚠️ **Catatan jujur:** uji 2× (AI rapuh) → waktu & panjang **tidak tetap** antar
putaran (putaran-1 C paling lama 17,2 dtk; putaran-2 C paling cepat 14,5 dtk).
⇒ **JANGAN pakai waktu sebagai penentu**; penentu = **mutu isi**.

---

## §B · ATURAN RUJUKAN vs KUTIPAN — PUTUSAN BOS (verbatim)

> *"rujukannya harus di daftar pustaka bukan di paragraf situ, kalau kutipan boleh
> di paragraf. Dan Rujukan C tetap harus dicek DOI-nya sebelum masuk daftar pustaka."*

```
📎 KUTIPAN (dalam paragraf)                     → BOLEH tetap di paragraf
📚 RUJUKAN (entri baru hasil revisi AI)         → WAJIB ke DAFTAR PUSTAKA
                                                  JANGAN ditulis di paragraf
🔍 RUJUKAN BARU                                 → WAJIB DICEK DOI DULU
                                                  baru boleh masuk daftar pustaka
```

**Koreksi Bos atas pembagian peran (verbatim):**
> *"Kan yang menulis Ai dan yang menunjukkan jev, kenapa jev yang cari doi. Kenapa
> bukan ai langsung verifikasi atas Harvest artikel nya? Dan Harvest artikel juga
> sudah ada sistem aturan tersendiri di EduAi"*

⇒ **JEV TIDAK MENCARI DOI.** Pembagian yang BENAR:
```
JEV  = MENUNJUK  (peta/struktur/bentuk)      ← "di mana"
AI   = MENULIS   (revisi/kutipan/rujukan)    ← "isi"
MESIN = VERIFIKASI DOI (audit_doi → CrossRef) ← "nyata atau tidak"
```

---

## §C · YANG SUDAH ADA (JANGAN BIKIN BARU) — TERBACA DARI KODE

`app/pustaka.py` = **"Mesin PENCARIAN REFERENSI TERVERIFIKASI untuk EduAi"**:

| Ada | Letak |
|---|---|
| Sumber resmi: OpenAlex · Garuda · CrossRef · Scopus | `cari_crossref()` baris 508 · `cari_scopus()` 137 |
| **`audit_doi(doi)`** → `httpx.get(CrossRef/{doi})` → 200 = NYATA | baris ~(docstring: *"pagar ANTI-HALUSINASI"*) |
| `doi_status` = `verified` / `no_doi` / `unverified` | baris 784–789 |
| HANYA `verified`/`no_doi` boleh masuk daftar pustaka | `daftar_pustaka_apa7()` baris 808 |
| Urut: verified dulu → sitasi terbanyak | baris 792 |
| DOI **tidak bisa diisi user** (anti-curang) | putusan 06 Okt |
| Upload PDF liar **DILARANG** | putusan 06 Okt |

**⇒ Verifikasi DOI SUDAH ADA. Yang belum: menutup PINTU KE-2 (rujukan yang
ditambahkan AI saat menulis revisi BELUM lewat `audit_doi`).**

```
Pintu 1 · Tab Referensi (harvest)   → ✅ sudah lewat audit_doi
Pintu 2 · AI menulis revisi         → ❌ BELUM lewat audit_doi   ← CELAH
```

---

## §D · ALUR PUTUSAN C (rujukan dari revisi AI)

```
AI merevisi bagian (cara C: potongan + peta naskah)        ← TERBUKTI
   ↓
KODE pisahkan: isi revisi  vs  rujukan baru
   ↓
Rujukan baru → kotak REFERENSI (bukan paragraf)            ← pintu SUDAH ADA
   ↓
User klik "Masukkan ke daftar pustaka"
   ↓
audit_doi() → CrossRef                                     ← SUDAH ADA
   ↓
200 = masuk daftar pustaka (APA 7) · gagal = TOLAK JUJUR
```

**NOL mesin baru · NOL pintu baru.** Memakai `pustaka.py` + `daftar_pustaka_apa7()`
+ `audit_doi()` yang sudah LIVE.

---

## §E · BUKTI KENAPA DOI WAJIB DICEK (08 Okt 2026, terukur)

Rujukan yang AI tambahkan di hasil C diperiksa ke sumber nyata:

| Rujukan | Nyata? | DOI |
|---|---|---|
| **Morgan & Hunt (1994)** *The Commitment-Trust Theory of Relationship Marketing*, Journal of Marketing | ✅ NYATA | **10.1177/002224299405800302** ✅ |
| **Moorman, Zaltman & Deshpande (1992)** *Relationships between providers and users of market research*, JMR | ✅ NYATA | perlu ambil dari sumber |
| **Gundlach, Achrol & Mentzer (1995)** *The structure of commitment in exchange* | ⚠️ **DOI belum ketemu** saat pencarian | **WAJIB dicek sebelum masuk** |

⇒ **Bukti nyata: 1 dari 3 rujukan DOI-nya belum bisa ditunjuk.** Kalau AI dipercaya
buta → **rujukan palsu masuk daftar pustaka**. Bos benar: **WAJIB dicek.**

---

## §F · YANG BELUM DIKERJAKAN (daftar)

1. **Uji peta halus di naskah lain** (Asih tanpa nomor · Disertasi) — baru Tesis 78.
2. **Peta 3 tingkat dalam SATU panggilan Jev** (bab + sub-bab + paragraf) —
   putusan Bos "Ya, satu peta" — **BELUM DIUKUR**.
3. **Sampai tingkat PARAGRAF** — putusan Bos (presisi maksimal) — **BELUM DIUKUR**.
4. **Menutup Pintu 2**: rujukan dari revisi AI → kotak Referensi → `audit_doi()`.
5. **Simpan peta halus** ke `section_state` + kolom `mulai`/`akhir`
   (`CatatanPembimbing.mulai` **masih diisi 0** — bug nyata).
6. **Sambung ke Kolaborasi**: komentar pembimbing → tunjuk sub-bab → AI revisi
   potongan itu (cara C) → rujukan ke Referensi.

⚠️ **DILARANG DIKODING** sampai Bos bilang "mulai". Berkas ini catatan putusan.
