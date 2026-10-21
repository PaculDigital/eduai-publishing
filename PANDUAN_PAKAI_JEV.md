# 🔑 CARA PAKAI JEV YANG BENAR — Rujukan Tetap EduAi

<!-- 📝 SOT: PANDUAN PAKAI JEV — berlaku untuk SEMUA titik aplikasi -->

> **Status:** ✅ BERLAKU. **Sumber:** dokumentasi resmi `docs.typesafe.ai`
> (12 berkas, skill `typesafe-jev`) + **pengukuran langsung** ke
> `openrouter.ai/api/v1/systemone` 07 Okt 2026.
> **DILARANG** memakai cara lama (lihat §5) — **berbahaya**.

---

## §1 · JEV ITU APA

Jev (**System One**, TypeSafe) **bukan** model penulis teks. Ia **menjawab
pertanyaan bertipe** tentang sebuah teks (`state`). Balasannya berupa
**nilai bertipe + probabilitas + keyakinan** — **tanpa teks**. Karena itu Jev
cocok jadi **MATA** (mengenali, memeriksa keberadaan), **bukan TANGAN** (menulis).

**Prinsip induk Bos (07 Okt 2026, verbatim):**
> *"jev selalu terdepan sebelum mesin dan Ai itu memang fungsi jev di mana pun.
> Agar mesin dan Ai enak dalam bekerja dan hasil presisi."*

⇒ Urutan baku: **① Jev kenali → ② mesin olah → ③ AI tulis → ④ Jev periksa hasil.**

---

## §2 · SKEMA YANG BENAR (3 aturan)

```
① NAMA pertanyaan  → BEBAS apa saja (tidak pernah dikirim ke model)
② TIPE             → HANYA 3:  noul  ·  choice  ·  score
③ criteria         → WAJIB PER-TIPE:
     noul    ⛔ TIDAK BOLEH ada criteria   (bentuk apa pun ⇒ HTTP 400)
     choice  ✅ OBJEK  {'opsi': 'deskripsi'} (WAJIB · maks 255 opsi)
     score   ✅ ARRAY  ['tingkat 0', …]      (WAJIB · 2–10 tingkat)
```

### Contoh BENAR

```python
{
  # choice — jenis naskah (criteria = OBJEK)
  'jenis_naskah': {
      'type': 'choice',
      'instructions': 'Tentukan jenis penelitian naskah akademik ini.',
      'criteria': {
          'kuantitatif': 'Memakai angka & uji statistik: sampel, regresi, SPSS.',
          'kualitatif':  'Memakai wawancara mendalam: informan, triangulasi, tema.',
          'literatur_review': 'Menelaah pustaka/karya lain, tanpa data lapangan.',
          'lainnya': 'Tidak sesuai ketiga opsi di atas.',
      },
  },

  # noul — keberadaan bagian (TANPA criteria!)
  'ada_abstrak': {
      'type': 'noul',
      'instructions': 'Apakah ada bagian yang BERJUDUL "ABSTRAK" atau "ABSTRACT"?',
  },

  # score — taraf kelengkapan (criteria = ARRAY)
  'kelengkapan_imrad': {
      'type': 'score',
      'instructions': 'Nilai kelengkapan STRUKTUR artikel IMRAD.',
      'criteria': ['Nyaris tak ada bagian.', 'Ada 1-2 bagian.', 'Ada 3-4 bagian.',
                   'Ada 5 bagian lengkap.', 'Semua bagian lengkap.'],
  },
}
```

### Cara kirim

```python
# Badan permintaan (bentuk [OI] chat → lewat jembatan/pipa yang ADA)
{'model': 'SATPAM/typesafe/jev-1.13',
 'messages': [{'role': 'user',
               'content': json.dumps({'state': bahan_teks, 'questions': PERTANYAAN})}]}
```

⚠️ **Semua tipe boleh dicampur** dalam **1 panggilan** — dievaluasi **paralel**.
Menambah pertanyaan **nyaris tak menambah waktu** ⇒ **pack sebanyak mungkin**.

---

## §3 · MEMBACA HASIL

| Tipe | Balikan | Cara baca |
|---|---|---|
| `choice` | `choice` + `probabilities` + `confidence` | `confidence` 1 = semua di satu opsi · 0 = sebaran rata (**jangan dipakai**) |
| `score` | `score` + `legend` + `probabilities` + `confidence` | `score` boleh pecahan (3,83) = taraf; `legend` = arti tiap tingkat |
| `noul` | `noul` (0..1) | ⚠️ **TIDAK ada `confidence`** ⇒ hitung **`abs(2p − 1)`**. **noul 0,5 = "tidak tahu"**, bukan "setengah benar" |

**Ambang resmi:** `confidence < 0,8` ⇒ **tanya manusia / eskalasi**.

**Ambang EduAi (dipakai `konversi.py`):**
```
< 0,35        → BELUM ADA
0,35 – 0,50   → RAGU   (JANGAN klaim apa pun — bahaya: user senang padahal cacat)
≥ 0,50        → ADA
keyakinan < 0,80 → "perlu diperiksa manusia"
```

---

## §4 · BATAS RESMI `jev-1.13` (9 kelemahan) — WAJIB TAHU

| # | Kelemahan | Aturan kita |
|---|---|---|
| 1 | **Literal reading** — menjawab pertanyaan yang **ditulis**, bukan yang **dimaksud** | tulis kondisi **PERSIS** |
| 2 | **Tidak bisa menghitung** — *"recognizes the shape of an answer rather than tallying"* | **hitungan di KODE**, bukan Jev |
| 3 | Tanggal/waktu dibaca sebagai teks | bandingkan di kode |
| 4 | **Indirection** — negasi ganda / banyak lompatan | tulis langsung |
| 5 | **Context rot** — state besar + tak relevan ⇒ akurasi turun | **kurasi bahan** dulu |
| 6 | Konten adversarial | kriteria tegas + uji kasus tepi |
| 7 | Instructions ⟷ criteria bertentangan | selaraskan |
| 8 | Urutan opsi choice | acak ulang, cek konsisten |
| 9 | **Bukan model penulis** | pakai model generatif untuk menulis |

**Batas teknis:** state **teks saja** (bukan gambar/audio) · **64k token** total ·
**Inggris paling akurat** (Indonesia **lebih rendah** ⇒ wajib uji sendiri) ·
biaya **$42/Mtok input**, **output GRATIS** · latensi **~0,6–0,9 dtk** (terukur kita).

---

## §5 · ❌ CARA LAMA — DILARANG (bahaya)

```
❌ {'type': 'noul', 'criteria': 'Ya bila X.'}        → 400 (expected object, received string)
❌ {'type': 'noul', 'criteria': {'yes': 'ada'}}      → 400 (invalid_union)
❌ {'type': 'choice', 'criteria': ['a','b']}          → 400 (expected record, received array)
❌ {'type': 'choice', 'options': ['a','b']}           → 400 (expected record, received undefined)
❌ {'type': 'score', 'criteria': {'0':'x','1':'y'}}   → 400 (expected array)
❌ tipe karangan: 'text' / 'pilih' / 'bebas' / tanpa type
```

**Akibatnya:** HTTP **400 Zod** yang **DISAMAR jadi HTTP 503** oleh 9router
(pesan asli dipotong) ⇒ tampak seolah *"Jev/9router rusak"*.

**🔴 Kesimpulan sesat yang PERNAH diambil (jangan terulang):**
| Klaim sesat | Kenyataan |
|---|---|
| "Skema Jev tertutup, hanya 3 nama" | yang terbatas = **bentuk `criteria`**; nama BEBAS |
| "Jev tidak stabil / flaky" | **KONSISTEN 100%** — salah bentuk = gagal |
| "Hanya 2 tipe sah" | ada **3 tipe** (noul, choice, **score**) |
| "Panjang state penyebabnya" | **24.000 kar LULUS** (terukur) |
| "Rate limit" | **10× tanpa jeda = LULUS** (terukur) |
| "Jev menolak dipakai lebih luas" | Jev **mampu** — Wulan yang salah bentuk |

---

## §6 · POLA YANG DIDUKUNG UNTUK EDUAI (berbagai titik app)

| Pola | Berkas resmi | Pakai di EduAi |
|---|---|---|
| **Speculative fan-out** | `pattern-fan-out.md` | banyak pertanyaan 1 panggilan (sudah dipakai: 5–18) |
| **Confidence-gated routing** | `pattern-confidence-routing.md` | ragu < 0,8 ⇒ **tanya mahasiswa** (jangan tebak) |
| **Citation check** | `cookbook-citation-check.md` | cek **sitasi hilang** sesudah konversi |
| **Structure recovery** | `cookbook-structure-recovery.md` | **baca bentuk naskah berantakan** — mesin tak bisa |
| **LLM guardrails** | `cookbook-guardrails.md` | saring keluaran AI sebelum tampil |

### Titik app yang BOLEH disambung Jev (struktur/bentuk/keberadaan)

| Titik | Peran Jev | Tipe |
|---|---|---|
| **Konversi jurnal** | peta bab, bagian wajib, 11 elemen mutu | choice+noul+score ✅ terpasang |
| **Deteksi jenis** | konfirmasi kuantitatif/kualitatif/review | choice ✅ terbukti |
| **Bentuk naskah aneh** | kenali bentuk sebelum mesin memetakan | noul/choice |
| **Sesudah konversi** | sitasi hilang · bagian utuh | noul |
| **Abstrak 2 bahasa** | selaras ID↔EN | noul/score |

### 🗺️ PETA 3 TINGKAT (BAB + SUB-BAB + PARAGRAF) — CARA RESMI (08 Okt 2026) ⭐

**⚠️ §7b (peta bab) & §7c (peta halus) sudah DIGANTIKAN oleh bagian ini.**
Skrip lama sudah dihapus → `_arsip/pre-rapi-peta-08okt26-cara-lama/`.

**Skrip resmi:** `peta3_jev.py` + `saringan_bersih.py` + `_audit_per_aturan.py` (root proyek).
**SOT:** `SOT_PETA_NASKAH_SATU_PINTU_08OKT2026.md` · skill: `typesafe-jev` → `references/peta-3-tingkat-resmi.md`.

**Hasil terukur (Asih fid=81, SELURUH NASKAH 159.909 kar):** 5/5 BAB ✅ · 143 paragraf ·
1.029 kandidat · goyang 3,0% · 0,7–1,0 dtk/panggilan · 0 gagal.
Disertasi 5/5 (yakin 0,64–0,88) · Tesis S2 3/3.

**Cara (5 langkah):**
```
KODE: buang_daftar_isi() RESMI → saringan_bersih.dibuang() (5 aturan)
      BAB dilabeli DI KODE (regex) — TIDAK lewat Jev, nol biaya
JEV : 1 panggilan · tiap kandidat 1 pertanyaan CHOICE 4 pilihan
      (bab / subbab / paragraf / biasa)
KODE: rakit — goyang ⇒ 'biasa' (ragu JANGAN ditandai)
```

**⚠️ 3 pagar wajib:**
1. **JENDELA "APA ADANYA" — TERMASUK BARIS KOSONG** (membuangnya = UJI 19 ambruk 90%→18%).
2. **CAPTION hanya dibuang kalau ≤70 kar** (caption 23/62/64 kar vs paragraf 389/556 kar).
3. **GELOMBANG ≤120 tanya / ≤18.000 kar** (naskah besar ⇒ 503).
4. **UKUR RECALL, bukan cuma precision** — jalankan `_audit_per_aturan.py` tiap naskah baru.

**Pembagian tugas (INI kuncinya):**

```
KODE: saring kandidat · hitung PANJANG ISI sesudah baris · ambil ISI TERPANJANG
      per nomor romawi · rakit peta (mulai/akhir/yakin/asal)
JEV : satu pertanyaan noul per kandidat → "apakah baris ini awal bab?"
      state = FAKTA, bukan baris polos
```

**🔑 Kalimat pertanyaan YANG MENANG (terukur, rata-rata yakin 0,823):**
> `Baris X.baris_teks diikuti isi X.panjang_isi_setelahnya_karakter karakter.`
> `Apakah baris ini awal bab yang menaungi isi itu?`

| Varian kalimat | Rata2 yakin |
|---|---|
| **sebut panjang isi** | **0,823** 🏆 |
| "judul kepala" | 0,729 |
| "menaungi seluruh isi" | 0,616 |
| **paling SIMPEL** | **0,224** ❌ |

🚨 **Aturan baru (terukur):**
1. **Jev butuh FAKTA POSITIF** (panjang isi), bukan kalimat pendek.
2. **JANGAN tulis daftar LARANGAN** ("bukan daftar isi, bukan rujukan…") —
   menurunkan yakin (0,844 → 0,32–0,72).
3. **Jev TIDAK membandingkan antar pertanyaan** (tiap pertanyaan INDEPENDEN) ⇒
   **urutan & duplikat WAJIB diputuskan KODE**, jangan diharap dari Jev.
4. **Aturan "nomor harus naik" saja SALAH** — kalau daftar isi muncul lebih dulu,
   bab asli ikut terbuang. Yang benar: **ambil ISI TERPANJANG per nomor**.

### ⛔ Yang JANGAN disambung Jev (zona GAGAL — menilai MUTU tulisan)

Menilai mutu "bagus/tidak": konsistensi isi · etika · daftar pustaka **sebagai
penilaian mutu** · gambar · konteks · citation validator (mutu). Ini **bukan**
soal bentuk, tapi **penilaian** ⇒ Jev terbukti gagal. **Pakai aturan murni
(kode) atau model generatif.**

---

## §7 · PENJAGA OTOMATIS (jangan dilewati)

| Penjaga | Menjaga |
|---|---|
| `app/satpam.py::_periksa_skema()` | **pagar kode** — tolak bentuk salah SEBELUM ke jaringan; dipanggil `tanya_bebas()` & `tanya_bebas_mutu()` (gagal-cepat `raise ValueError`) |
| `_gerbang_skema_jev.py` | **34 asersi** — pagar ada & menangkap · semua pertanyaan sah · pagar dipanggil · tak ada klaim palsu · gerbang bergigi |
| `_uji_gigi_skema_jev.py` | **5 suntikan** (noul+criteria · choice+array · tipe karangan · pagar dilumpuhkan · klaim palsu) — semua **HARUS TERTANGKAP** |
| `_uji_3peran_jev_betul.py` | uji nyata 3 peran atas naskah asli + **verifikasi ke sumber** |
| `_gerbang_jev_optimasi.py` (56) · `_gerbang_jev_mata.py` (42) | peran Jev di konversi |

**Cara jalankan** (WAJIB di dalam container):
```bash
docker cp _gerbang_skema_jev.py eduai-app:/app/
docker exec -w /app eduai-app python3 _gerbang_skema_jev.py
```

---

## §8 · JEBAKAN OPERASIONAL

1. **9router memotong pesan galat** (jembatan potong 500 kar) ⇒ akar tak kelihatan.
   **Diagnosa benar:** tembak `https://openrouter.ai/api/v1/systemone` **LANGSUNG**,
   kunci dibaca dari DB 9router (`providerConnections`, name=`JEV`).
2. **Jangan menguji lewat model berawalan `JEV/`** — koneksi itu
   `openrouter.ai/api/v1/chat/completions` yang **MEMANG menolak** Jev
   (`"...is a decisions model..."`). Jalur BENAR = **`SATPAM/typesafe/jev-1.13`**
   (koneksi `SATPAM` → jembatan `satpam-jev/jembatan.py:8130` → `/systemone`).
3. **Jev jawab "tidak ada" padahal ada** ⇒ periksa **BAHAN** dulu
   (`_bahan_mutu()`: abstrak & daftar pustaka ada di depan/belakang, **di luar bab**
   ⇒ `_susun_state()` tak mengirimnya).
4. **Ubah berkas** ⇒ pakai `bash scripts/salin_restart.sh eduai-app <berkas…>`
   (`docker cp` wajib `docker restart`; `uvicorn` tanpa `--reload`).
5. **Jangan mengubah ambang supaya uji lulus** — itu menipu diri.
6. **Dokumentasi internal proyek BUKAN acuan kemampuan Jev** ⇒ pakai skill
   `typesafe-jev` (dokumentasi resmi). Kalau docs berubah: `bash
   scripts/ambil_ulang.sh` di skill itu.

---

## §7c · ⛔ USANG — PETA HALUS (SUB-BAB) — DIGANTIKAN §7b (PETA 3 TINGKAT)

**JANGAN DIPAKAI.** Skrip `peta_halus_jev.py` sudah dihapus → `_arsip/pre-rapi-peta-08okt26-cara-lama/`.
Yang resmi sekarang **§7b: peta 3 tingkat** (`peta3_jev.py`) — sudah mencakup sub-bab **dan** bab **dan** paragraf dalam 1 panggilan.

*(Blok di bawah dipertahankan hanya untuk arkeologi/audit.)*

**Tujuan:** tunjuk **bagian tertentu di dalam bab** (bukan satu bab penuh) untuk
Kolaborasi — supaya **AI tidak menebak** bagian mana yang direvisi.

**Skrip resmi:** `peta_halus_jev.py` (root proyek) — `petakan(teks)`.

### Cara yang MENANG (v10 · TERUKUR 4/4 = nol salah)

```python
# 1. KODE: beri ID tiap baris — TANPA menebak bentuk
# 2. KODE: buang FAKTA yang pasti bukan judul (daftar isi, [[..]], caption, angka)
# 3. KODE: JENDELA 3 BARIS BER-ID per kandidat
    paket = {'baris_atas':  'L000618| melalui Relationship Marketing?',
             'tengah':     'L000620| 1.3. Tujuan Penelitian',       # ← ditanya
             'baris_bawah':'L000622| 1. Untuk menguji dan menganalisis…'}
    tanya = "Apakah baris tengah ini awal sub-bab?"                  # noul
# 4. KODE: rakit — p ≥ 0,80 = judul → mulai/akhir dari POSISI BARIS
```

**Hasil terukur (BAB I Tesis 78, KUNCI 358/606/620/638):** 4/4 ✅
`1.1 → ≥0,80` · `1.2 → 0,91` · `1.3 → 0,93` · `1.4 → 0,91`
Pemisahan bersih: **judul 0,86–0,95** vs **paragraf 0,04–0,31** · 0,6 dtk/gelombang.

### ⚠️ TIGA ATURAN KERAS (dari 10 versi ukur)

| # | Aturan | Bukti |
|---|---|---|
| 1 | **JANGAN kirim FAKTA HITUNGAN** (panjang isi) | v9: `1.3` & `1.4` terlewat (0,63/0,58) karena penghitung berhenti di baris pendek ⇒ isi=0 |
| 2 | **JANGAN pakai kalimat BERLARANGAN** ("bukan paragraf, bukan kalimat") | pelajaran peta bab: 0,844 → 0,32 |
| 3 | **BACA `p` LANGSUNG** — JANGAN `abs(2p-1)` | `p` ITU arah jawaban: 0,97=YA judul · 0,02=BUKAN |

### ⛔ 6 CARA GAGAL — JANGAN ULANG (v1–v6)

Semua gagal karena **KODE disuruh MENEBAK BENTUK** (dilarang):
pola nomor `1.1` → 0 kandidat · baris kosong sebagai pemisah → beda tiap naskah ·
gabung baris jadi paragraf → baris kosong Tesis memisah TIAP baris.

**Fakta naskah yang membuktikan:** median panjang baris 3 naskah = 69/37/16 kar,
p90 = 82/383/65 ⇒ **baris ≠ paragraf**; paragraf Word pecah ~69–75 kar.

**Satu-satunya yang boleh ditebak kode: `pasti_bukan_judul()`** — fakta pasti
(titik-pengarah daftar isi, penanda `[[..]]`, caption, angka murni). Sisanya **JEV**.

---

## §9 · ⛔ CARA LAMA YANG DIBUANG (08 Okt 2026) — JANGAN DIPAKAI LAGI

Cara-cara di bawah ini **TERBUKTI TIDAK PRESISI** saat diukur di 3 naskah nyata.
Sudah **diganti** cara resmi §7b di atas (`peta_bab_jev.py`). Backup: `_arsip/pre-peta-jev-lama-08okt26/`.

| ⛔ Cara lama (BUANG) | Kenapa salah | Terukur |
|---|---|---|
| Tanya Jev **"berapa bab?"** | Jev **tidak bisa menghitung** (kelemahan resmi #2) | jawab "1" lalu "0" padahal 5 bab |
| Tanya Jev **"sebutkan judul bab"** | Jev **bukan penulis teks** (#9) + salah tipe (`noul` = ya/tidak) | selalu kosong |
| **Beri Jev peta kasar, minta vonis ya/tidak** | Jev jadi **penilai tebakan kode** — bukan pembaca struktur | jawaban mepet 0,5 |
| **Tanya pakai baris POLOS** (tanpa fakta) | Jev tak punya bukti ⇒ menjawab "shape", bukan isi | yakin 0,16–0,27 ❌ |
| **Daftar LARANGAN** dalam pertanyaan ("bukan daftar isi, bukan rujukan…") | merusak jawaban | yakin 0,844 → 0,32–0,72 ❌ |
| **Aturan "nomor romawi harus NAIK"** untuk buang duplikat | kalau daftar isi muncul lebih dulu, **bab asli ikut terbuang** | Asih salah pilih baris 138–226 (daftar isi) |
| **Harap Jev membandingkan antar baris** | **Mustahil** — tiap pertanyaan Jev INDEPENDEN | "BAB I" palsu & asli sama-sama dijawab "ya" |
| **Regex untuk MENGENALI bentuk naskah** | tak sanggup ribuan naskah; Bos marah 08 Okt | peta lama Disertasi: **0 dari 5 bab** ❌ |
| **Mengharap Jev menilai MUTU tulisan** (bagus/tidak) | wilayah Jev **terbukti gagal** | 8 modul mutu dicabut |

**Prinsip pengganti (jangan dilanggar):**
> **KODE yang bisa diputuskan kode (hitung, urutkan, bandingkan, normalisasi) — JANGAN tanya Jev.
> JEV hanya untuk JUDGMENT yang kode tak bisa.** Dan Jev **butuh FAKTA POSITIF** di state
> (mis. panjang isi sesudah baris) — bukan baris telanjang, bukan daftar larangan.

**Rujukan lengkap:** `HASIL_UKUR_PETA_JEV_08OKT2026.md` (§3 tabel kalimat · §4 jebakan).

### ⛔ JEBAKAN: KONTEKS PANJANG DITEMPEL KE SETIAP PERTANYAAN (10 Okt 2026)

Menyelipkan teks konteks (mis. PANDUAN jenis ~1.500 kar) ke `instructions` TIAP
pertanyaan TIDAK menaikkan akurasi — TERUKUR GAGAL: `max_tokens_exceeded`,
7.195/8.555 kandidat (84%) tak terjawab. Hukum #5 (context rot).

✅ YANG BENAR: (a) jenis naskah -> TANYA Jev (choice, conf 1,00), bukan diberi tahu;
(b) bahan = JENDELA fakta saja; (c) siring kandidat di KODE.
Lihat `VONIS_KONTEKS_JENIS_DIBUANG_10OKT2026.md`.
