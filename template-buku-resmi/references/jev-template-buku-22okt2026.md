# JEV UNTUK TEMPLATE BUKU — HASIL UKUR 22 OKT 2026

Semua angka di sini **hasil panggilan nyata** ke jembatan 8130
(`typesafe/jev-1.13`), bukan perkiraan.

## 1. Dua koreksi dokumentasi resmi (dibaca ulang 22 Okt 2026)

Sumber: `https://docs.typesafe.ai/primitives/noul.md` + `primitives.md` +
`agent-skill.md` — salinan lama di `_arsip/pre-perbarui-22okt26/`.

### K1. `noul` BOLEH `criteria` (skill lama SALAH)

Resmi:
> *"`criteria`: Optional. An object with `true` and `false` descriptions of
> what a yes and a no mean."*
> *"When the boundary between yes and no is subtle, add `criteria` with `true`
> and `false` descriptions… try your questions with and without `criteria` and
> keep whichever gives better answers on your documents."*

**Terbukti di jembatan kita (22 Okt 2026):**

| Bentuk | Pagar `app/jev.py` | Jev | noul |
|---|---|---|---|
| noul TANPA criteria | terima | balas | **0,03** |
| noul + criteria `{true,false}` | terima | balas | **0,04** |
| noul + criteria STRING | **TOLAK** | — | — |
| noul + criteria `{ya,tidak}` | **TOLAK** | — | — |

⇒ Pagar kita **sudah benar**: menerima objek `{true,false}`, menolak bentuk lain.
Selisih p dengan/tanpa criteria = **0,01** (kecil, tapi criteria tidak merusak).

### K2. `instructions` boleh OBJEK / ARRAY

Resmi:
> *"A string is enough for most questions. It can also be an object or an array,
> which puts the question in one field and the data it refers to in others."*

⇒ Untuk state berlapis, bentuk berstruktur lebih disarankan & bisa menunjuk
field dengan backtick. **Belum dipakai** di EduAi (masih string semua).

## 2. Hasil ukur — template buku resmi (67 baris, 5.868 karakter)

### Ronde 1 — cara LAMA (1 kalimat panjang, tanpa criteria, klaim bernomor)
| Pertanyaan | noul | Masalah |
|---|---|---|
| blok 16pt tengah = kutipan? | **0,91** | ✅ benar |
| hirarki bab 22pt > sub bab 13pt? | **0,45** | ❌ RAGU |
| isi buku mulai paragraf 44? | **0,04** | ❌ SALAH — 3 varian semua tolak |

**Akar kegagalan:** pertanyaan **menggabung 2 hal** (bab & sub bab) + **memakai
nomor paragraf** (Jev tidak menghitung — kelemahan resmi #2).

### Ronde 2 — cara RESMI (atomik + criteria + fakta positif + fan-out 1 panggilan)

| Pertanyaan | noul | yakin |
|---|---|---|
| blok 16pt tengah = kutipan | **0,92** | 0,84 |
| "BAB I" dan judul menyatu satu baris | **0,96** | 0,92 |
| nomor bab angka Romawi | **0,94** | 0,88 |
| sub bab bernomor bertingkat | **0,98** | 0,96 |
| ada KATA PENGANTAR | **0,99** | 0,98 |
| ada TENTANG PENULIS | **0,99** | 0,98 |
| ada data penerbitan (ISBN dll) | **0,96** | 0,92 |
| **choice** jenis dokumen | **`buku`** | **conf 1,00** |

**8 pertanyaan, SATU panggilan.** Semua ≥0,92 (kecuali koreksi diri).

## 3. Pelajaran yang bisa dipakai ulang

1. **Pertanyaan yang menyebut NOMOR = gagal** (Jev tak menghitung). Ganti jadi
   pertanyaan tentang **sifat** ("menyatu satu baris", "angka Romawi").
2. **Pertanyaan gabungan (A dan B) = ragu** (0,45). Pecah jadi atomik ⇒ 0,96 & 0,98.
3. **`criteria {true,false}` menaikkan keyakinan** pada batas yang halus.
4. **Fan-out 8 pertanyaan 1 panggilan** — resmi: 11,5× lebih murah, 9,6× lebih cepat
   daripada 8 panggilan terpisah, jawaban sama.
5. **choice conf 1,00** untuk jenis dokumen — bisa dipercaya untuk memilih jalur.

## 4. Yang Jev TIDAK boleh dipakai (dari template ini)

- Menghitung nomor paragraf / jumlah bab / jumlah kata ⇒ **kode**.
- Menyebut/menyalin teks ⇒ **kode**.
- Membandingkan dua baris mana yang lebih tepat ⇒ **kode** (independen).
- Menentukan font/ukuran/margin ⇒ **XML** (`periksa_buku_template.py`).

**Pembagian tugas yang sah:**
```
XML  (angka pasti)   : halaman, batas, font, ukuran, spasi, perataan
JEV  (makna/peran)   : peran blok, jenis dokumen, sifat struktur
KODE (hitungan)      : nomor, jumlah, batas bagian, urutan
```

## 5. Skrip uji

| Berkas | Isi |
|---|---|
| `_uji_noul_criteria.py` | A/B/C/D — bukti criteria diterima & bentuk salah ditolak |
| `_jev_template_optimal.py` | 8 pertanyaan fan-out, cetak noul + yakin |
| `_tanya_jev2.py` | ronde 1 (cara lama) — arsip kegagalan |
