# ① `criteria` NOUL — TERBUKTI, PAGAR DIBUKA (09 Okt 2026)

> **Putusan Bos:** *"① criteria noul — SETUJU, ini luka buat sendiri… Uji ulangnya
> murah (10 menit, tanpa sentuh produksi) — kerjakan pertama."*

---

## 1. UJI LANGSUNG KE JALUR (bukan disimpulkan lagi)

Skrip `uji_criteria_noul.py` — tembak **langsung ke jembatan**, melewati pagar kita:

| Bentuk | Hasil |
|---|---|
| **A.** noul TANPA criteria | ✅ OK — `{"cek": {"noul": 0.76}}` |
| **B.** noul + criteria **OBJEK** `{true, false}` (**RESMI**) | ✅ **OK — `{"cek": {"noul": 0.79}}`** |
| **C.** noul + criteria **STRING** (bentuk lama) | ❌ HTTP 502 — Zod: `"expected": "object"`, `path: ["questions","cek","criteria"]` |

**⇒ ASAL-USUL KESALAHAN TERBUKTI PERSIS:**
Kesimpulan lama *"noul TIDAK BOLEH punya criteria"* lahir dari error **C** —
Zod bilang **`expected: "object"`**, artinya `criteria` **MEMANG DITERIMA**,
hanya **bentuknya harus objek**. Generalisasi "tak boleh ada" = **terlalu lebar**.

---

## 2. apakah `criteria` MENAJAMKAN? (diukur, bukan teori)

Skrip `uji_criteria_tajam.py` — 2 kasus nyata dari U-KUNCI:

| Kasus | Tanpa criteria | Dengan criteria | Kunci | Benar? |
|---|---|---|---|---|
| L008622 header TABEL | 0,84 | **0,73** ⬇️ | bukan judul | ✅ makin tepat menolak |
| L008050 `3. Tinjauan Literatur` | — | **0,91** ⬆️ | judul sah | ✅ makin yakin judul |

**⇒ `criteria` MEMISAHKAN kasus batas:** yang palsu turun, yang asli naik.
Ini tepat alat penajam yang dibutuhkan hakim (kasus batas = titik lemah tunggal
kita: L008622 pernah dijawab 'sepakat' = salah).

---

## 3. YANG DIUBAH (kode)

**`app/jev.py::periksa_skema()`** — pagar dibalik:

```
SEBELUM: tipe == 'noul' and ada_crit ⇒ KELUHAN ("tidak boleh punya criteria")
SESUDAH: tipe == 'noul':
           · criteria tidak ada        ⇒ ✅ diterima (tetap sah)
           · criteria OBJEK {true,false} ⇒ ✅ DITERIMA (resmi)
           · criteria bukan objek      ⇒ ❌ ditolak (sebab 502 semu)
           · criteria objek tanpa true/false ⇒ ❌ ditolak
```

**Gerbang:** `_gerbang_jev_jalantol.py` → **21 LULUS / 0 GAGAL** (tetap hijau).

---

## 4. YANG BELUM (jujur)

- ❌ **Belum dipakai** oleh surveyor/hakim. Ini baru **membuka pagar** — kalimat
  `criteria` yang TAJAM untuk tiap pertanyaan Belum ditulis & belum diukur.
- ❌ Belum masuk gerbang khusus (perlu asersi: noul+objek DITERIMA · noul+string
  DITOLAK · noul+objek-tanpa-true/false DITOLAK).
- ⚠️ Kunci jawaban masih cacat ⇒ ukuran "benar" di atas memakai kunci yang
  kita kontrol sendiri (L008622 memang header tabel — diverifikasi ke naskah).

---

## 5. URUTAN BERIKUTNYA (sesuai vonis Bos)

1. ✅ **① uji criteria** — SELESAI (dokumen ini)
2. ⬜ **② Pass-1 stitch + ③④** (per-blok · stop kirim baris bernomor) —
   **ukur recall kandidat**: apakah stitch memulihkan kandidat tipe-L008039?
3. ⬜ **⑤ pensiunkan ambang-`p`** (sinkron U4b — `p` bukan alat ukur kepalsuan;
   JANGAN hidupkan kembali mekanisme yang sudah dibubarkan)
