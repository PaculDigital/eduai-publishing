# 🔒 URUTAN RESMI PETA NASKAH EDUAI — TERKUNCI (09 Okt 2026)

> **Perintah Bos (verbatim):** *"Kunci urutan yang benar, hapus urutan yang selalu
> kamu rekomendasikan yang salah."*
>
> **Dokumen ini = SATU-SATUNYA acuan urutan.** Wulan DILARANG menyebut urutan lain.

---

## ✅ URUTAN YANG BENAR (TERKUNCI)

```
① JEV SURVEYOR   →  peta3_jev.py        MENGUKUR bentuk naskah, MEMBERI TAHU
② JEV HAKIM      →  hakim_peta.py       MEMERIKSA & MELAPOR (peer reviewer)
③ MESIN          →  peta_jembatan.py    mengikuti hasil Jev
④ AI             →  penulis isi
```

**Sumber (kata-kata Bos di dokumen):**
- `RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md:6-8` — *"Framing (koreksi Bos):
  hakim = **PEER REVIEWER, bukan peer decider**. Dia memeriksa & melapor;
  **TIDAK PERNAH** meng-override peta surveyor."*
- `FLAG_LANJUT_DISINI.md:64-66` — *"KEPUTUSAN: surveyor & hakim **TETAP TERPISAH**
  (putusan Bos: jangan gabung beda fungsi)… Hakim pakai status `ragu` = TERBUKTI BEKERJA."*
- Memory (07 Okt, verbatim) — *"Ingat wulan dimana mana jev selalu terdepan sebelum
  mesin dan Ai itu memang fungsi jev di mana pun."*

## ❌ URUTAN SALAH YANG WULAN DILARANG SEBUT LAGI

```
🚫 "Jev surveyor → Jev hakim → mesin → AI"   [DITULIS SEBAGAI NAMA FUNGSI]
   ⇒ KELIRU: surveyor & hakim BUKAN dua fungsi teknis berurutan.
     Yang benar: keduanya PERAN JEV yang TERPISAH (jangan digabung).
     Kalau perlu disebut teknis, urutannya:
        peta3_jev.petakan() → hakim_peta.periksa_peta() → peta_jembatan.dari_surveyor() → AI

🚫 "Hakim mengoreksi/override surveyor"
   ⇒ DILARANG. Hakim LAPOR saja (pagar H1). Tidak pernah membalik peta surveyor.

🚫 "Tambah aturan/criteria ke hakim supaya lebih pintar"
   ⇒ DILARANG (kesalahan 09 Okt). Dokumen sendiri bilang:
     **"rapikan KANDIDAT SURVEYOR, bukan menambah kerja hakim."**

🚫 "Satukan surveyor & hakim jadi satu jalur"
   ⇒ DILARANG (putusan Bos: "jangan gabung beda fungsi").

🚫 "Surveyor sebelum AI / AI sebelum Jev"
   ⇒ DILARANG. Jev SELALU di depan (gatekeeper); mesin & AI mengikuti.
```

## 🧩 PEMBAGIAN PERAN (satu kalimat masing-masing)

| Peran | Satu kalimat |
|---|---|
| **Jev Surveyor** | "Saya lihat naskahnya, saya beri tahu bentuknya." |
| **Jev Hakim** | "Saya periksa peta surveyor, saya LAPOR kalau ada yang meragukan." |
| **Mesin** | "Saya ikut petunjuk Jev, saya kerjakan angkanya." |
| **AI** | "Saya menulis kata-katanya." |

## 🚩 PAGAR HAKIM (dari kode `hakim_peta.py`, jangan dilanggar)

```
H1  Hakim LAPOR, jangan BLOKIR — mesin tetap jalan walau hakim mati
P1  Hakim mati/galat ⇒ laporan KOSONG, mesin tetap jalan
P2  Jangan melempar galat keluar
P3  JANGAN memutuskan label — hanya melaporkan status per bagian
P4  Jumlah bagian TIDAK berkurang
P5  `p` hanya info tampilan, TIDAK pernah jadi input keputusan
P6  JANGAN menyentuh `app/satpam.py` (jalur biaya) — hakim_peta modul TERPISAH
```

## 📌 AKIBATNYA — apa yang harus dikerjakan (bukan usul Wulan, tapi dari dokumen)

```
🔴 TEMUAN 09 Okt (FLAG_LANJUT_DISINI.md:59-62):
   "baris penting (mis. L008039 `2. Wawancara`) TIDAK PERNAH dijadikan kandidat
    oleh surveyor ⇒ hakim tak punya kesempatan memeriksanya.
    ⇒ Pekerjaan berikutnya: RAPIKAN KANDIDAT SURVEYOR, bukan menambah kerja hakim."
```

⇒ **PEKERJAAN BERIKUTNYA = RAPIKAN KANDIDAT SURVEYOR** (+ kenali kuantitatif/kualitatif,
perintah Bos 09 Okt). BUKAN menyetel criteria hakim.

## ⚠️ CATATAN K5

```
criteria K5 + ambang 0,60/0,30 di `app/hakim_peta.py` = TAMBAHAN WULAN 09 Okt
yang bertentangan dengan dokumen ini ("peer reviewer, memeriksa & melapor").
Status: 🚩 ditandai JANGAN dipakai produksi. Menunggu perintah Bos untuk dibuang.
```
