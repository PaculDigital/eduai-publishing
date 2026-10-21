# AUDIT: SURVEYOR & HAKIM vs DOKUMENTASI RESMI TypeSafe (09 Okt 2026)

> **Pertanyaan Bos:** *"Apakah jev baik surveyor ataupun hakim ini sudah sesuai
> dengan dokumentasi resmi cara bertanya & pemakaiannya? Kalau sudah resmi pasti
> tidak ada lubang atau bug. Mungkin kurang optimal dua-duanya."*
>
> **Sumber diperiksa (dari docs resmi, bukan ingatan):**
> `agent-skill.md` · `cookbooks.md` (daftar) · `autoformat.md` (structure
> recovery) · `rerank_typesafe.md` · `consistency_choice_cookbook.md` ·
> `semantic_find.md`
>
> **JAWABAN JUJUR: BELUM. Ada 5 penyimpangan, 2 di antaranya NYATA & terukur.**

---

## 0. RINGKASAN: apa yang SALAH vs apa yang BENAR

| # | Titik | Kita | Resmi | Nilai |
|---|---|---|---|---|
| **①** | Nama field `criteria` untuk noul | **DILARANG** oleh `jev.py` | **WAJIB** (`NoulCriteria(true=…, false=…)`) | 🔴 **BERTENTANGAN** |
| **②** | Pass 1 "stitch" (sambung baris terpotong) | **TIDAK ADA** | **WAJIB** — pass-1 khusus | 🔴 **HILANG — sumber lubang** |
| **③** | Blok vs baris | per **baris** | per **BLOK** (setelah stitch) | 🟠 kurang optimal |
| **④** | Baris polos tanpa "gap" | tidak kirim penanda baris kosong | **gap dikirim** (`\n` di depan baris) | 🟠 hilang 1 bukti |
| **⑤** | Ambang ragu | `|2p−1| < 0,80` → 'ragu' (kita karang) | **`max(prob) < 0,60`** → `uncertain` | 🟠 beda angka |
| — | **1 pertanyaan per kandidat** | ✅ **SESUAI** | resmi memang per item/pair | ✅ |
| — | **Baris ber-ID (`L014\|`)** | ✅ **SESUAI** | persis pola resmi | ✅ |
| — | **Fan-out 1 panggilan** | ✅ **SESUAI** | resmi (12,2× lebih murah) | ✅ |
| — | **Kode pegang kendali** | ✅ **SESUAI** | resmi | ✅ |
| — | **Pilih opsi = prob tertinggi** | ✅ **SESUAI** | resmi `argmax` | ✅ |

---

## ① 🔴 BERTENTANGAN: `criteria` untuk noul

**Resmi (rerank + autoformat):**
```python
Noul(
    instructions="Is this candidate the cited case?",
    criteria=NoulCriteria(                 # ← WAJIB ADA
        true ="The candidate states the specific rule the query cites.",
        false="The candidate is only on a similar topic.",
    ),
)
```

**Kita (`app/jev.py:127-130`):**
```python
if 'tipo' == 'noul' and 'criteria' in q:
    keluhan.append("tipe noul TIDAK BOLEH punya `criteria` — Hapus field `criteria`.")
```

**⇒ DAMPAK:** kita **kehilangan kemampuan resmi paling penting**: mendefinisikan
tepat apa arti "true" vs "false". Itu **persis** yang bikin jawaban Jev tidak
tajam pada kasus batas (L008622 header tabel → kita jawab "sepakat" = salah).

**Catatan asal-usul kesalahan:** aturan "noul tanpa criteria" muncul dari
**HTTP 400 Zod**, saat `criteria` dikirim berbentuk **string/list** — bukan objek
`true/false`. Kesimpulan "noul tak boleh criteria" **TERLALU LEBAR** — yang salah
BENTUKNYA. ⇒ **Wajib diuji ulang** ke jalur `/systemone` (bukan disimpulkan).

---

## ② 🔴 HILANG: Pass 1 "stitch" — INI SUMBER LUBANG

Resmi = **2 pass**:
```
Pass 1 (STITCH)  : 1 noul per PASANGAN baris:
                   "Does line L014 pick up mid-sentence, continuing a sentence
                    left unfinished at the end of line L013?"
                   ⇒ baris tersambung DIGABUNG JADI BLOK
Pass 2 (CLASSIFY): 1 choice per BLOK (heading/paragraph/list/quote/code/callout)
```

**Kita:** langsung klasifikasi **per baris** — **tanpa pass 1**.

**⇒ DAMPAK (ini menjelaskan temuan U-KUNCI kita sendiri):**
```
L008039 '2. Wawancara'  — surveyor TIDAK menjadikannya kandidat
⇒ karena baris "2. Wawancara" muncul SETELAH baris yang terpotong
⇒ tanpa stitch, batas baris salah → kandidat hilang
⇒ HAKIM TIDAK BISA MENANGKAP YANG TIDAK PERNAH JADI KANDIDAT
```
Bukti pendukung dari uji kita sendiri (08 Okt): **"sambung baris terpotong"
memperbaiki L000570 & L000602** — tapi hanya ditambal sebagian lewat daftar kata
menggantung (~28 baris), **bukan pass-1 resmi**.

**⇒ INILAH "LUBANG" yang Bos maksud. Bukan bug hakim — pass 1 yang tidak ada.**

---

## ③ 🟠 Blok vs baris

Resmi mengklasifikasi **BLOK** (hasil stitch), bukan baris. Kita per baris ⇒
satu paragraf bisa jadi 3-5 kandidat ⇒ **kandidat palsu bertambah** (dari sini
pula 51 'palsu' di kunci lahir) ⇒ hakim kerja ekstra menyaring.

---

## ④ 🟠 Baris kosong (gap) sebagai bukti

Resmi: **penanda baris kosong DIBACA KODE, TIDAK dikirim** — tapi **dipakai
kode** untuk memutus pasangan (`pairs separated by a blank line are skipped`).
Kita tidak memakai gap ⇒ kandidat melewati batas paragraf.

⚠️ Catatan: dokumen resmi bilang penanda **eksplisit** (`#`, `- `, `1.`) itu
**dibaca kode, jangan dikirim ke model**. Kita **mengirim** baris bernomor ke Jev
jadi kandidat ⇒ **menyimpang** dari semangat resmi (kandidat yang bisa diputus
kode sebaiknya tidak ditanyakan). Ini penyebab "baju mirip" (temuan Bos 08 Okt:
`1. Apakah…` dianggap sub-bab).

---

## ⑤ 🟠 Ambang "ragu"

| | Angka | Sumber |
|---|---|---|
| Kita | `\|2p−1\| < 0,80` (noul) · `prob < 0,50` (choice) | **karangan kita** |
| Resmi | `max(probabilities) < 0,60` → `uncertain` | `MIN_CHOICE_PROBABILITY = 0.60` (contoh resmi) |

Dan resmi menegaskan: *"threshold is an illustrative application policy, not a
calibrated guarantee… Choose production thresholds using [data]"* ⇒
**ambang WAJIB dikalibrasi ke data kita**, dan angka 0,80 kita **belum
diverifikasi** ke data.

---

## YANG SUDAH SESUAI (jangan diubah)

1. ✅ **1 pertanyaan per kandidat** (bukan menumpuk) — resmi memang begitu.
2. ✅ **Baris ber-ID** `L014| teks` — persis pola resmi (autoformat & semantic_find).
3. ✅ **Fan-out** — semua pertanyaan 1 panggilan (resmi: 12,2× murah, 10× cepat).
4. ✅ **Kode yang merakit**, Jev tidak menulis/menyalin teks.
5. ✅ **Pilih opsi = probabilitas tertinggi** (`argmax`) — persis resmi.
6. ✅ **Pertanyaan sempit** ("pick up mid-sentence?" bukan "same paragraph?") —
   arah kita sudah benar (terukur 0,823 vs 0,224).

---

## 🎯 KESIMPULAN

**Bos BENAR: keduanya BELUM optimal.** Yang paling menentukan:

```
🔴 ② PASS-1 STITCH TIDAK ADA  ← INI LUBANG UTAMA (menjelaskan baris hilang)
🔴 ① `criteria` noul DILARANG  ← kita buang alat penajam resmi
🟠 ④ Baris bernomor dikirim ke Jev ← "baju mirip" (temuan Bos sendiri)
```

**Urutan perbaikan yang diusulkan:**
1. **Uji ulang `criteria` noul** ke jalur `/systemone` (10 menit, tanpa mengubah
   produksi) — kalau objek `true/false` DITERIMA ⇒ buka pagar & pakai.
2. **Tambah Pass 1 (stitch)** ke `peta3_jev` — sambung baris, BARU klasifikasi
   blok. Ini menutup lubang "kandidat hilang".
3. **Berhenti mengirim baris bernomor** ke Jev (kode sudah bisa memutuskan).
4. **Kalibrasi ambang** dari data sendiri (bukan 0,80 karangan).

⚠️ Semua di atas **belum dikerjakan** — menunggu putusan Bos. Tidak ada yang
diubah tanpa izin.
