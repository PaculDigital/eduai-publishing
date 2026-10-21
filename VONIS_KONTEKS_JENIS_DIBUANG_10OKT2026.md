# 🚫 VONIS: KONTEKS JENIS KE SURVEYOR — DIBUANG (10 Okt 2026)

> **Putusan Bos (verbatim): "A"** — buang drop-in, pakai cara resmi.
> **Uji:** `uji_dampak_konteks_surveyor.py` (fid=115, SEBELUM vs SESUDAH) —
> diarsipkan di `_arsip/pre-dropin-jenis-10okt26/`.

---

## 1. APA YANG DIUJI

Ide Bos: `deteksi_jenis()` (kode) + `PANDUAN_JENIS` (teks ~1.500 kar) + `ATURAN_UMUM`
diselipkan ke `instructions` SETIAP pertanyaan surveyor, supaya Jev "tahu konteks".

---

## 2. HASIL — GAGAL, dan gagalnya KERAS

```
SEBELUM (tanpa konteks) : kandidat terjawab
SESUDAH (pakai konteks) : waktu 53,8 dtk · 79 gelombang
   biasa 1.229 · subbab 96 · paragraf 33 · bab 2 · BELUM 7.195 (84%) ❌

[jev] Jev HTTP 502: max_tokens_exceeded  ← BERULANG
```

**Sebab:** konteks ~1.500 kar ditambahkan ke **SETIAP** pertanyaan (8.555 kandidat)
⇒ state per gelombang meledak ⇒ **lewat batas 64k token** ⇒ 84% kandidat tak terjawab.

👉 **Yang gagal bukan konteksnya — tapi CARA MENEMPELKANNYA.** Menempelkan teks
yang sama ke ribuan pertanyaan = melipatgandakan bahan ribuan kali.

---

## 3. BUKTI DARI DOKUMENTASI RESMI (bukan opini)

Dokumen resmi `docs.typesafe.ai` + cookbook `structure-recovery`:

| Sumber | Kalimat |
|---|---|
| jaggedness jev-1.13 #5 | *"State besar + tak relevan ⇒ **context rot** ⇒ akurasi turun"* |
| jaggedness #5 aturan | **"Saring di kode dulu; kirim HANYA yang perlu"** |
| cookbook structure-recovery | *"Direct evidence stays in code… **NEVER** sent to the model to reconsider"* |
| cookbook structure-recovery | *"The model gets **only the questions code cannot answer**"* |
| cookbook (bukti) | Pertanyaan **"same paragraph"** (lebih luas) → **GAGAL**; <br>**"picks up mid-sentence"** (sempit) → **BERHASIL** |

⇒ Cara menang resmi = **pertanyaan SEMPIT + fakta yang kode TAK BISA putuskan**.
BUKAN menyuap model dengan teks konteks panjang.

---

## 4. YANG SUDAH ADA & TERBUKTI (jangan bikin baru)

```
✅ DETEKSI JENIS SUDAH ADA — lewat JEV, 1 pertanyaan `choice`:
   "Naskah ini jenis penelitian apa?"
   criteria: kuantitatif / kualitatif / literatur_review / lainnya
   TERUKUR: conf 1,00 ✅  (katalog: skill typesafe-pertanyaan §3)
   Tempat: PANDUAN_PAKAI_JEV.md §6 "Deteksi jenis — choice ✅ TERBUKTI"
```

⇒ Drop-in tadi **DUPLIKAT** dari yang sudah terbukti — dan versinya lebih buruk.

---

## 5. ATURAN YANG DIPEGANG (dari session ini)

```
① Jev = MATA: diberi PERTANYAAN SEMPIT + FAKTA yang kode tahu, bukan KONTEKS PANJANG.
② Jev DITANYA hal yang kode tak bisa putuskan — bukan DIBERI TAHU lewat teks.
③ Bahan kurasi: hanya yang RELEVAN (hukum #5 context rot).
④ Jangan tempel teks sama ke ribuan pertanyaan (token meledak).
⑤ Kalau butuh jenis naskah: 1 pertanyaan choice, bukan 1.500 kar konteks × N.
```

---

## 6. ARSIP

```
📦 _arsip/pre-dropin-jenis-10okt26/
   ├─ pola_jenis_surveyor.py            (drop-in, TIDAK dipakai)
   ├─ uji_jenis_3naskah.py              (uji deteksi 3 naskah — deteksi BENAR,
   │                                     tapi cara pakainya yang salah)
   └─ uji_dampak_konteks_surveyor.py    (uji SEBELUM vs SESUDAH — GAGAL)
```

⚠️ Catatan: **detektor `deteksi_jenis()` sendiri TIDAK salah** — akurat di 3 naskah
(81 kuantitatif · 115 kualitatif · 104 campuran, terverifikasi ke isi naskah).
Yang salah = **cara memakainya** (ditempel ke prompt Jev, bukan ditanyakan ke Jev).
