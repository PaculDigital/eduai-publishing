<!-- LAPORAN (RIWAYAT) — bukan SOT status. Sumber: RANCANGAN_HAKIM_JEV_NAIK_KELAS (v3) + kode NYATA -->
# 🔎 LAPORAN: URUTAN YANG BENAR — SURVEYOR · HAKIM · POLA · AI

> **Permintaan Bos (09 Okt 2026):** *"Sebenarnya kamu tahu tidak? Yang benar yang mana?
> Jangan ngawur. Buat laporan kenapa dan bagaimana seharusnya secara lengkap."*
> **Jawaban singkat:** Wulan **salah urutan** saat menjelaskan. Yang benar ada di
> `RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md` **§6 baris 236-240** — dan Wulan
> membacanya **setelah** Bos menegur. Ini laporan lengkapnya.
>
> **✅ VONIS BOS (09 Okt 2026):** *"Urutan di laporan SUDAH SESUAI. 'Hakim paling akhir'
> SALAH — kecuali yang dimaksud hakim yang lain."* + *"urutan ini benar di atas kertas,
> tapi di kode nyata tiga penghubungnya belum ada."* ⇒ **TEPAT.** Kata "hakim" di
> proyek ini ada DUA: **Hakim PETA** (tengah) & **Hakim MUTU** (paling akhir).
> Lihat §4b (analogi rumah) — akar kesalahan Wulan = memakai hakim yang beda.

---

## 1. ⚖️ URUTAN YANG BENAR (dari dokumen, verbatim)

`RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md` §6 "ALUR KERJA BARU" — **kutipan apa adanya:**

```
NASKAH
   ↓
[1] JEV SURVEYOR  → peta induk (bab+sub-bab+paragraf+batas) + p per label
   ↓                 ← 1× per naskah, disimpan di section_state
[2] JEV HAKIM     → peer review per bagian: sepakat / ragu / curiga
   ↓                 (LAPORAN, bukan vonis)
[3] MESIN         → ini PEMUTUS:
   ↓                 sepakat → pakai · ragu → periksa ulang 1 putaran
   ↓                 curiga  → judul dilepas, isi digabung ke induk
   ↓                 (nol karakter naskah hilang)
[4] AI            → menulis revisi pakai peta yang sudah diperiksa
```

**Aturan tertulis:** *"langkah [2] TIDAK BOLEH menghentikan [3]/[4].
Hakim ragu/mati ⇒ mesin jalan seperti biasa (pagar P1 & P2 dipertahankan)."*

⇒ **Jadi Bos BENAR.** Urutannya: **surveyor → hakim → mesin → AI.**
Wulan tadi menaruh hakim **setelah** AI — **SALAH**. Bos mengoreksi dengan tepat.

---

## 2. ❌ APA YANG WULAN SALAH KATAKAN (dan kenapa Wulan keliru)

**Yang Wulan tulis di diagram tadi:**
```
[1] SURVEYOR ──> [2] POLA ──> [3] AI
                                 ↑ [4] HAKIM ← SALAH TEMPAT
```

**Kenapa Wulan keliru — akar yang jujur:**
Wulan **mencampur dua arti kata "hakim"** yang ada di proyek ini:

| "Hakim" | Di mana | Kapan jalan | Tugas |
|---|---|---|---|
| **HAKIM PETA** | `RANCANGAN_HAKIM_JEV_NAIK_KELAS` | **SEBELUM pola** | Tajamkan label surveyor |
| **HAKIM MUTU** | fitur konversi jurnal | **SETELAH naskah jadi** | Periksa abstrak/novelty/pustaka |

Wulan memakai makna **kedua** (hakim mutu) untuk menjawab pertanyaan Bos yang
sebenarnya tentang makna **pertama** (hakim peta). Dua hal BEDA, Wulan gabung. Itu salah.

---

## 3. 🎯 KENAPA URUTANNYA HARUS BEGINI (sebab, bukan opini)

### ① Kenapa SURVEYOR dulu?
Hakim **butuh bahan**. Tugas hakim (T①) = *"PERIKSA PETA SURVEYOR, bukan peta mesin lagi"*:
```
DULU : _susun_state kirim peta MESIN (deteksi_bab_besar, 5 bab)
BARU : kirim PETA INDUK (hasil surveyor: bab + sub-bab + paragraf + batas)
```
⇒ Kalau surveyor belum jalan, **hakim tidak punya apa pun untuk diperiksa.**
(Verifikasi kode: `app/satpam.py:133-134` **masih** pakai `deteksi_bab_besar` = peta mesin ⇒ **T① belum dikerjakan** ✅ sama dengan dokumen.)

### ② Kenapa HAKIM sebelum MESIN & AI?
Hakim = **PENAJAM**, bukan pemeriksa hasil. Tugasnya (T②) = *"CEK JUDUL vs LANJUTAN"*:
```
Bahan : jendela 3 baris ber-ID
Tanya : noul — "Apakah baris tengah ini benar AWAL <bab|sub-bab>?"
Hasil : p ≥ 0,80 SEPAKAT · < 0,80 ⇒ TANDAI RAGU (bukan buang)
```
Lalu **MESIN** yang memutuskan (langkah [3]):
```
sepakat → pakai · ragu → periksa ulang 1 putaran · curiga → judul dilepas
```
⇒ Kalau hakim ditaruh **setelah AI**, semua kesalahan label surveyor sudah
**terlanjur dipakai AI** untuk menulis revisi. Terlambat — sudah jadi tulisan salah.

### ③ Kenapa MESIN yang memutus (bukan hakim)?
Tertulis: *"Hakim LAPOR, jangan BLOKIR"* + *"mesin yang PEMUTUS"*.
Alasan: hakim Jev bisa **ragu/mati** — kalau hakim jadi pemutus, naskah bisa buntu.
⇒ Mesin tetap jalan walau hakim mati (pagar P1/P2 dipertahankan).

### ④ Di mana POLA dalam rantai ini?
⚠️ **Pola TIDAK TERTULIS di diagram §6** — dan ini temuan Wulan yang jujur:
```
Diagram §6 resmi:  surveyor → hakim → MESIN → AI
Pola seharusnya    : berada di dalam "MESIN" ([3])
```
**Alasan:** profiler pola **membaca label** (`P7`: *"Profiler pola HANYA membaca dari
label surveyor; TIDAK BOLEH memutuskan label apa pun"*). Jadi pola **harus jalan
SETELAH label final** — yaitu **setelah hakim menajamkan**.
```
Kalau pola jalan SEBELUM hakim → pola menghitung dari label yang masih kasar
⇒ angka `nomor_terakhir` bisa salah
```
⇒ Urutan yang benar: **surveyor → hakim → MESIN (pola di dalamnya) → AI**.

---

## 4. 🧾 URUTAN BENAR — VERSI LENGKAP (Wulan lengkapi, berdasarkan dokumen)

```
NASKAH
  │
  ├─[1]─ JEV SURVEYOR   peta3_jev.petakan()
  │        keluaran: baris · kand · label · gabung · goyang · sistematika
  │        (+ S1 nanti: nilai `p` per label)          ⏳ BELUM ada `p`
  │
  ├─[2]─ JEV HAKIM      satpam (T①–T⑤) — PEER REVIEWER
  │        per bagian: sepakat / ragu / curiga  → LAPORAN
  │        aturan: TIDAK BOLEH menghentikan [3]/[4]
  │
  ├─[3]─ MESIN          ← PEMUTUS
  │        a. putuskan label (sepakat/ragu/curiga → gabung ke induk)
  │        b. PROFILER POLA (app/pola_penulisan.py) — baca label FINAL:
  │             skema_nomor · gaya_judul · butir · ada_tabel ·
  │             nomor_terakhir · pola_tetangga · judul_curiga
  │        c. hitung nomor baru (renumber) — ⏳ belum dikode
  │
  └─[4]─ AI             menulis revisi dipandu pola yang SUDAH tajam
```

---

## 4b. 🏠 ANALOGI BANGUN RUMAH (rumusan Bos — DITAMBAHKAN 09 Okt)

```
SURVEYOR    = TUKANG UKUR TANAH        → gambar denah
HAKIM PETA  = INSPEKTUR HASIL UKUR     → periksa denah SEBELUM bangun
              ("kalau salah ukur dibiarkan, temboknya terlanjur salah")
H   MESIN    = TUKANG BANGUN (+ juru hitung POLA)
AI          = PEKERJA YANG MENULIS
HAKIM MUTU  = INSPEKTUR BANGUNAN JADI  → periksa HASIL, memang paling akhir
```

⇒ **Ini akar kesalahan Wulan:** dua inspektur berbeda, **dua waktu berbeda**.
Wulan memakai inspektur bangunan-jadi untuk menjawab pertanyaan tentang inspektur
hasil-ukur. Bukan "hakim salah tempat" — **Wulan salah orang.**

| | **Hakim PETA** | **Hakim MUTU** |
|---|---|---|
| Yang diperiksa | Peta surveyor (label bab/sub-bab) | Naskah jadi (abstrak, novelty, pustaka) |
| **Posisi benar** | **TENGAH**: surveyor → hakim → mesin → AI | **PALING AKHIR**: setelah naskah jadi |
| Kenapa di situ | Butuh peta sbg bahan · pola butuh label final · AI butuh peta tajam | Naskah harus jadi dulu baru bisa dinilai |
| Berkas | `app/satpam.py` (rancangan T①) | `app/satpam.py:tanya_bebas_mutu` (konversi jurnal) |

---

## 5. 📊 POSISI SEBENARNYA SEKARANG (terverifikasi ke KODE, bukan dokumen)

| Bagian | Berkas | KODE | Dipakai produksi? |
|---|---|---|---|
| **Surveyor** | `peta3_jev.py` (root) | ✅ jadi, 6 aturan, teruji 3 naskah | ❌ **TIDAK** — `grep peta3_jev app/` hanya kena komentar |
| **Hakim** | `app/satpam.py` | ✅ jadi | ⚠️ LIVE tapi di jalur lain (`ai.py:2350`); **masih kirim peta MESIN** (`satpam.py:133-134`) ⇒ T① belum |
| **Pola** | `app/pola_penulisan.py` | ✅ jadi hari ini, gerbang 36/0 | ❌ **TIDAK** — tidak dipanggil siapa pun |
| **AI** | `prompts/revisi_produksi.txt` | ⏳ belum punya aturan bentuk tulisan | — |

**Bukti S1 belum ada** (surveyor belum keluarkan `p`):
```
grep -c "probabilities" peta3_jev.py  →  0
keluaran petakan() → {'baris','kand','label','goyang',...}  ← TANPA 'p'
```
⇒ Padahal rancangan §3 S1 mewajibkan surveyor keluarkan `p` per label,
supaya hakim bisa hemat (*"periksa ulang HANYA yang p < 0,85"*).

---

## 6. 🔴 YANG MASIH KURANG (jujur, dari §7b dokumen)

| Uji | Status | Catatan |
|---|---|---|
| U4 kalibrasi `p` | ✅ selesai | kesepakatan antar-putaran SELALU 1,00 ⇒ **`p` = confidence Jev** (0,36–0,99) |
| U4b kalibrasi ambang | ❌ **belum** | ambang 0,85 **salah tempat** (rata conf 0,839 ⇒ tangkap 46%) — wajib cari ambang dari naskah KACAU (fid=115) |
| U1 adversarial | ✅ 6/6 tapi **BELUM membuktikan hakim berguna** | itu menguji **JEV**, bukan HAKIM (Wulan susun sendiri jendelanya) |
| **U-KUNCI** | ❌ **BELUM** | *"apakah HAKIM menangkap yang SURVEYOR lewatkan?"* — ini uji sejati |
| U2 biaya | ✅ selesai | per-BAB 1 panggilan ~1 dtk ✅ · per-sub-bab 17 ⚠️ mahal · bertingkat **GAGAL** |
| U5 metrik | ⚠️ baseline | fid=115: 75 sub-bab · 51 palsu (68%) · 24 asli |

**Keputusan v3 dari uji biaya:**
1. ✅ Hakim naik kelas **SAMPAI LEVEL BAB saja** (per-BAB, 1 panggilan, ~1 dtk)
2. ❌ **Buang putaran bertingkat** — terbukti LEBIH MAHAL dari sekali-jalan
3. 🚫 Ambang 0,85 jangan dipakai buta — kalibrasi ulang dulu

---

## 7. 🎯 KENAPA HAKIM DI TARUH DI SITU (kata dokumen sendiri)

> *"Hakim naik kelas"* = dari **penjaga pintu** menjadi **PEER REVIEWER**:
> *"Dia memeriksa & melapor; **TIDAK PERNAH** meng-override peta surveyor."*

Tabel §5 dokumen (Hakim lama → Hakim baru):
```
Sumber bahan : peta MESIN (kasar)  →  PETA INDUK surveyor
Cakupan tanya: 1× seluruh naskah   →  per bagian (bab & sub-bab)
Keluaran     : lolos/tanya/tolak    →  + laporan kecurigaan per bagian
Peran        : Penjaga pintu        →  PEER REVIEWER
Pagar        : Lapor, tidak blokir  →  SAMA (dipertahankan)
```

⇒ **Hakim = penajam peta.** Jalan **setelah surveyor**, **sebelum mesin/AI**.

---

## 8. ✅ KESIMPULAN (1 paragraf)

Bos benar: urutan yang seharusnya adalah **SURVEYOR → HAKIM → MESIN (pola di dalam) → AI**,
dan Wulan salah menaruh hakim di akhir. Wulan keliru karena mencampur **"hakim peta"**
(dokumen ini) dengan **"hakim mutu"** (fitur konversi jurnal) — dua hal berbeda.
Alasan urutan itu **bukan selera**, tapi sebab teknis: hakim **butuh peta surveyor**
sebagai bahan (T①: *"kirim PETA INDUK, bukan peta mesin"*), dan **pola butuh label final**
(P7: *"profiler hanya membaca label surveyor, tidak boleh memutuskan"*) — jadi hakim
harus **mendahului** pola. Hakim tetap **LAPOR, bukan BLOKIR**; **mesin yang memutus**.

---

## 9. 📌 YANG BELUM DIKERJAKAN (urutan kerja yang benar)

| # | Langkah | Status | Ketergantungan |
|---|---|---|---|
| 1 | Surveyor masuk app (`peta3_jev.py`) | ❌ | — |
| 2 | **S1**: surveyor keluarkan `p` per label | ❌ | butuh #1 |
| 3 | **T①**: hakim periksa PETA SURVEYOR (bukan peta mesin) | ❌ | butuh #2 |
| 4 | **U4b**: kalibrasi ambang dari naskah KACAU | ❌ | butuh #2 |
| 5 | **U-KUNCI**: apakah hakim menangkap yang surveyor lewatkan? | ❌ | butuh #2–#4 |
| 6 | Sambung pola ke alur (baca label final) | ⏳ modul siap | butuh #3 |
| 7 | Kontrak AI revisi (pola → bentuk tulisan) | ❌ | butuh #6 |

⇒ **Urutan kerja supaya TIDAK salah lagi:** kalau hakim mau ditata dulu,
maka #1→#5 harus jalan **sebelum** #6 (pola) dan #7 (AI).

---

## 10. SUMBER (semua dibaca, bukan karangan)

- `RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md` — **§6 baris 236-240** (alur resmi) ·
  §5 (tabel hakim lama→baru) · §2 T①–T⑤ · §3 S1 · §7a (uji biaya) · §7b (uji lain) · §11 (U1–U5)
- `RANCANGAN_PROFILER_POLA_09OKT2026.md` — baris 29/167/195/256/258 (pola & hakim)
- KODE (verifikasi langsung): `app/satpam.py:133-134` (masih peta mesin) ·
  `peta3_jev.py:321` (keluaran TANPA `p`) · `grep peta3_jev app/` (hanya komentar) ·
  `app/ai.py:2347-2353` (satpam LIVE di jalur peta bab)
- `CATATAN_KEPUTUSAN_PETA3_09OKT2026.md` · `SESI_09OKT2026_KRONOLOGIS.md`
