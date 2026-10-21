<!-- RANCANGAN (RIWAYAT) — SOT: bukan sumber status. Status peta naskah ada di SOT.md §SESI TERAKHIR -->
<!-- 🔒 URUTAN RESMI & TERKUNCI: lihat `URUTAN_RESMI_PETA_NASKAH_TERKUNCI.md`.
     surveyor (ukur) → hakim (LAPOR, tak override) → mesin → AI. -->
<!-- ⛔ YANG DIHAPUS DARI DOKUMEN INI (dinyatakan SALAH oleh Bos 09 Okt):
     (a) "hakim setara surveyor" bila dibaca sebagai "hakim boleh override" — SALAH.
         Yang benar: hakim = PEER REVIEWER, memeriksa & melapor, TIDAK override.
     (b) "tambah criteria/aturan ke hakim supaya pintar" — SALAH.
         Yang benar: RAPIKAN KANDIDAT SURVEYOR, bukan menambah kerja hakim. -->
<!-- RANCANGAN v2 (revisi Bos 09 Okt 2026) — BELUM DIKODING. Dilarang koding sampai Bos bilang "mulai". -->

# 🧑⚖️ RANCANGAN — HAKIM JEV NAIK KELAS (v2, setelah review Bos)

> **Perintah Bos (09 Okt 2026, verbatim):** *"Saya mau kamu upgrade dulu jev hakim
> agar setara jev surveyor."*
> **Framing (koreksi Bos):** hakim = **PEER REVIEWER, bukan peer decider**.
> Dia memeriksa & melapor; **TIDAK PERNAH** meng-override peta surveyor.
> **Status:** 📝 RANCANGAN v2. Nol baris kode diubah sampai Bos bilang "mulai".

---

## 0. MASALAH YANG DIPECAHKAN (terukur, bukan dugaan)

Uji A (09 Okt, naskah Asih fid=81) membuktikan hakim **tidak menambah nilai**:

| Yang diukur | Hasil |
|---|---|
| Surveyor (`peta3_jev`) | BAB 5 · sub-bab 130 · paragraf 157 |
| Hakim (`satpam.periksa`) | BAB 5 (conf 0,99) — hanya **mengulang** |
| `kedalaman_subbab` dari Jev | **0** ← padahal ADA 130 sub-bab ❌ |
| Waktu hakim | 1,176 detik + 1 panggilan Jev |

**AKAR (4 sebab, semuanya terukur di kode):**

| # | Akar | Lokasi | Bukti |
|---|---|---|---|
| 1 | Hakim periksa peta **MESIN** (kasar), bukan peta surveyor | `satpam.py:150` → `deteksi_bab_besar` | Hakim sebut 5 bab (peta mesin), tak lihat 130 sub-bab |
| 2 | Bahan miskin: **400 kar per bab** | `satpam.py:130` | Jev jawab `kedalaman=0` padahal 130 sub-bab ADA |
| 3 | Pertanyaan cuma **jumlah bab** — tak bisa nilai tiap bagian | `satpam.py:66` (`TANYA`) | Tak ada pertanyaan "apakah bagian ini benar?" |
| 4 | Tak ada **posisi** (mulai/akhir) di bahan | `_susun_state()` | Hakim tak bisa tunjuk baris mana yang salah |

> **1 kalimat:** Hakim diperlakukan seperti **penjaga pintu** yang hanya memeriksa KTP
> (jumlah bab), padahal surveyor sudah punya **denah lengkap** — dan hakim tidak pernah diberi denah itu.

---

## 1. ASAS — JANGAN BIKIN BARU, OPTIMAL KAN YANG ADA

Aturan induk Bos: *"jangan buat baru tapi lebih optimal kan yang sudah ada jadi tidak
rumit dan lebih sederhana"* + *"jangan gabung beda fungsi"*.

| Komponen yang DIPAKAI ULANG | Lokasi |
|---|---|
| `satpam.tanya_bebas(teks, peta, pertanyaan)` | `app/satpam.py:398` |
| `satpam._periksa_skema()` (pagar anti-503) | `app/satpam.py:345` |
| `peta3_jev.petakan(fid)` — SURVEYOR | `/app/peta3_jev.py:216` |
| Cara **jendela 3 baris** (terbukti 4/4) | `/app/peta_halus_jev.py:96` |
| `section_state` (tempat simpan peta) | DB produksi |
| `satpam.catat()` | `app/satpam.py:566` |

**❌ TIDAK dibuat:** tabel baru · dompet baru · jalur baru · fungsi Jev baru · tipe pertanyaan baru.

---

## 2. TUGAS HAKIM BARU (5 tugas)

### T① — PERIKSA PETA SURVEYOR (bukan peta mesin lagi)
```
DULU : _susun_state kirim peta MESIN (deteksi_bab_besar, 5 bab)
BARU : kirim PETA INDUK (hasil surveyor: bab + sub-bab + paragraf + batas)
```

### T② — CEK JUDUL vs LANJUTAN (tugas paling berguna)
```
Untuk tiap kandidat judul: bahan = jendela 3 baris ber-ID
  tanya = tipe `noul`: "Apakah baris tengah ini benar AWAL <bab|sub-bab>?"
  hasil = p ≥ 0,80 SEPAKAT · < 0,80 ⇒ TANDAI RAGU (bukan buang)
```

### T③ — HITUNG PER-BAB (bukan seluruh naskah)
```
DULU : "Berapa bab di SELURUH naskah?" → Jev lemah hitung besar (jawab "1"/"0")
BARU : "BAB INI (isi N kar) punya berapa sub-bab?" → per bab, cakupan kecil
```

### T④ — CEK KESEHATAN PETA (4 pertanyaan yang SUDAH SAH)
`jumlah_bab` (choice, per-bab) · `semua_romawi_sah` (noul) · `berurutan` (noul) ·
`kedalaman_subbab` (choice). ⚠️ **Tipe tetap 3** — sudut pandang baru = BAHAN beda.

### T⑤ — KELUARKAN DAFTAR KECURIGAAN (bukan cuma lolos/tolak)
```
BARU : {
  'keputusan': 'lolos',                     # tetap ada (kompatibel kode lama)
  'bagian': [
     {'i':191, 'label':'bab',    'judul':'BAB I',               'p':0.97, 'status':'sepakat'},
     {'i':606, 'label':'subbab', 'judul':'1.3. Tujuan Penelitian','p':0.62, 'status':'ragu'},
     {'i':961, 'label':'bab',    'judul':'BAB VI HASIL...',      'p':0.41, 'status':'curiga'},
  ],
  'jumlah_bab': 5, 'confidence': 0.99,
}
```

---

## 3. ⭐ PENYEMPURNAAN BOS (v2 — 3 butir presisi)

> 🚨 **KOREKSI v3 (hasil uji 09 Okt — S1 & S2 TERBUKTI SALAH ASUMSI, lihat §7a).**
> Wulan tulis `p = kesepakatan antar-putaran` ⇒ **TERUKUR SALAH** (U4: selalu
> **1,00** di 12/12 kandidat ⇒ ambang tanpa daya pisah). Yang benar: **`p` =
> `confidence` Jev** (terukur 0,36–0,99, punya daya tangkap).

### S1 — SURVEYOR WAJIB KELUARKAN NILAI `p` PER LABEL

**Masalah (Bos benar, terverifikasi ke kode):** `peta3_jev.petakan()` **tidak
mengeluarkan `p`** — hanya `label` keras. Padahal T② mau *"periksa ulang HANYA yang
p < 0,85"* untuk hemat biaya ⇒ **tanpa `p`, optimasi biaya TIDAK BISA JALAN.**

**Kabar baik — bahannya SUDAH ADA:**
```python
# peta3_jev.py:265 — jawaban tiap putaran SEMUA tersimpan:
semua = {i: [] for i, _t in kand}      # semua[i] = ['subbab','subbab','subbab'] dst.
...
return {..., 'semua': semua, ...}
```

**Tambahan kecil (satu-satunya perubahan di sisi surveyor):**
```python
# p = tingkat kesepakatan antar-putaran (putaran=3)
#   3/3 → 1.00 · 2/3 → 0,67 · 1/3 atau beda-beda → ≤0,33
#
# ⚠️ NIT BOS (09 Okt): `dari`/`v_utama` di kode asli = variabel LOKAL di dalam
#    loop label (peta3_jev.py:~295 `dari = {}` / `utama = max(...)`).
#    ⇒ Implementator WAJIB menyesuaikan SCOPE: hitung `p[i]` di DALAM loop
#    yang sama dengan `dari`/`utama`, sedangkan `semua`/`kand` sudah di scope luar.
p = {}
for i, _t in kand:
    vs = [x for x in semua[i] if x]
    p[i] = round(dari[v_utama] / len(vs), 2) if vs else 0.0
```
❗ Catatan: `p` ini = **kesepakatan antar-putaran**, BUKAN probabilitas Jev.
Sudah ada bahan mentahnya; ini murni **mengolah yang sudah ada** (bukan mesin baru).

⚠️ **Batas jujur:** `goyang` = `len(dari) > 1`, jadi `goyang` ⇔ `p < 1,0`.
Kalau `putaran=3` dan jawaban 2 vs 1 → `p = 0,67` ⇒ masuk kategori **ragu**.
Artinya **semua label goyang otomatis masuk daftar periksa ulang** — dan itu memang
yang kita mau.

### S2 — PASTIKAN SUMBER NILAI `p` (jangan ambang presisi di atas angka asal)

**Masalah (Bos benar):** H6 (≥0,80 · 0,50–0,79 · <0,50) butuh `p` **terkalibrasi**.

**Aturan yang ditetapkan (WAJIB dipatuhi):**
```
1. `p` surveyor  = KESEPAKATAN ANTAR-PUTARAN (S1)  → 1,00 / 0,67 / 0,33 / 0
2. `p` hakim     = KESEPAKATAN ANTAR-PUTARAN HAKIM JUGA (pola sama)
   ❗ JANGAN bergantung pada 'probability' Jev untuk `choice`/`noul` —
      bentuk jawaban `noul` = {'noul': 0.96} (satuan noul),
      `choice`      = {'choice':'5','probabilities':{...},'confidence':0.99}.
      Dua skala BEDA ⇒ TIDAK boleh disamakan jadi satu ambang.
3. Ambang H6 HANYA sah dipakai kalau `p` berasal dari cara yang SAMA.
```

⚠️ **Wajib diukur sebelum produksi:** apakah `confidence` yang dikirim Jev
**benar-benar terkalibrasi** di skala 0–1 yang sama dengan kesepakatan antar-putaran?
Kalau TIDAK → pakai kesepakatan antar-putaran saja (deterministik, bisa diaudit).
**Jangan sampai ambangnya presisi tapi angkanya asal.**

### S3 — TUTUP LOOP 'RAGU' (kalau cuma dicatat di log, ROI-nya negatif)

**Masalah (Bos benar, paling penting):** nilai hakim = **nilai yang dipakai MESIN
langkah [3]**. Kalau `ragu` cuma masuk log → kita **bayar Jev, dapat hiasan**.

**Definisi persis — apa yang MESIN lakukan (WAJIB, bukan opsional):**

| Status hakim | Tindakan MESIN (langkah [3]) |
|---|---|
| **sepakat** (p ≥ 0,80) | Pakai label surveyor apa adanya |
| **ragu** (0,50–0,79) | **PERIKSA ULANG 1 putaran tambahan** (putaran=2) pada bagian itu saja. Masih ragu → label dipakai **DENGAN TANDA** (`p` disimpan, `boleh_dipakai_fitur=True`) |
| **curiga** (<0,50) | Label **DIBUANG dari daftar judul** → isinya **DIGABUNG ke bagian induk** (mis. ke paragraf sebelum) — **naskah TIDAK hilang**, hanya judulnya dilepas |
| Jev mati/gagal | Jalan lama apa adanya (pagar P1/P2) |

⚠️ **PENTING (pagar H8):** bagian 'curiga' **TIDAK dibuang dari NASKAH** — hanya
statusnya turun dari 'judul' ke 'isi'. Nol karakter hilang.

**METRIK PRESISI (wajib diukur, bukan klaim):**
```
"dengan hakim, sub-bab PALSU turun dari X ke Y"

Cara ukur (naskah Wulandari-PDF, fid=115 — 89 dari 109 sub-bab PALSU):
  X = sub-bab palsu TANPA hakim   (angka baseline, sudah ada)
  Y = sub-bab palsu SESUDAH hakim (setelah 'curiga' dilepas jadi isi)
  Kalau Y < X  → hakim berguna (nilainya nyata, bukan hiasan)
  Kalau Y = X  → hakim TIDAK berguna ⇒ JANGAN dipasang (aturan Bos)
```

---

## 4. FRAMING (koreksi Bos) — PEER REVIEWER, BUKAN PEER DECIDER

**Judul lama "setara surveyor" boleh dipertahankan** — isinya sudah benar
(hakim melapor, tidak memvonis; H1/H2/H5 sudah menegakkan itu). **Tapi bahasanya
WAJIB konsisten: HAKIM = PEER REVIEWER, BUKAN PEER DECIDER.**

```
✅ BENAR (reviewer)                     ❌ DILARANG (decider)
────────────────────────────────────    ────────────────────────────────
"bagian ini saya curigai"                "bagian ini SALAH, buang"
"p 0,41 — perlu diperiksa manusia"       "p 0,41 — tolak peta surveyor"
"laporan untuk mesin & user"             "keputusan akhir milik hakim"
```

**Tabel istilah yang DIPAKAI (biar tidak ada yang salah kira):**

| Istilah | Arti |
|---|---|
| **PEER REVIEWER** | Hakim — memeriksa, melapor, **TIDAK memutuskan** |
| **PETA INDUK** | Keluaran surveyor — sumber tunggal struktur naskah |
| **LAPORAN KECURIGAAN** | Keluaran hakim — bahan pertimbangan, bukan vonis |
| **PEMUTUS** | MESIN (pakai/menandai/menggabung) — satu-satunya yang mengubah peta |

⇒ Pembaca berikutnya **TIDAK BOLEH** mengira hakim boleh meng-override surveyor.

---

## 5. PERBANDINGAN SEBELUM vs SESUDAH

| Aspek | HAKIM SEKARANG | HAKIM BARU |
|---|---|---|
| Sumber bahan | Peta MESIN (kasar) | **PETA INDUK surveyor** |
| Bentuk bahan | Cuplik 400 kar/bab | **Jendela 3 baris ber-ID** |
| Cakupan tanya | 1× seluruh naskah | **Per bagian** (bab & sub-bab) |
| Kedalaman nilai | Jumlah bab saja | **Sampai sub-bab** |
| Keluaran | lolos/tanya/tolak | **+ laporan kecurigaan per bagian** |
| Nilai `p` | ❌ tidak ada | ✅ ada (S1) — sumber jelas (S2) |
| Loop 'ragu' | ❌ cuma dicatat di log | ✅ **dipakai MESIN** (S3) |
| Peran | Penjaga pintu | **PEER REVIEWER** |
| Pagar | Lapor, tidak blokir | **SAMA** (dipertahankan) |

---

## 6. ALUR KERJA BARU

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

**Aturan:** langkah [2] **TIDAK BOLEH** menghentikan [3]/[4]. Hakim ragu/mati ⇒
mesin jalan seperti biasa (pagar P1 & P2 dipertahankan).

---

## 7. BIAYA & KECEPATAN — ⚠️ BELUM TERUKUR (wajib diukur sebelum produksi)

| Skenario | Panggilan Jev | Waktu |
|---|---|---|
| Sekarang (1× seluruh naskah) | 1 | ~1,2 dtk |
| Hakim baru, per-BAB (5 bab) | 1 panggilan (semua bab sekaligus) | perlu uji |
| Hakim baru, per-SUB-BAB (130), hanya p<0,85 | ? (bergantung berapa yang ragu) | perlu uji |
| Hakim baru, per-SUB-BAB (130), SEMUA | ~16 gelombang | ⚠️ kemungkinan mahal |

**Strategi hemat yang dirancang:** periksa ulang **HANYA yang p < 0,85** — perlu
`p` dari S1 supaya bisa jalan. Kalau semua p = 1,00 ⇒ **nol periksa ulang**.

**⏱️ PERTANYAAN IMPLEMENTASI BOS (WAJIB DIJAWAB DI RANCANGAN):**
> **T② pakai berapa putaran?** 1× murah tapi goyang · 3× stabil tapi mahal.
>
> ~~**JAWABAN v2 — BERTINGKAT (hemat, sesuai anggaran):**~~  🚫 **DICORET 09 Okt 2026**
> ~~PUTARAN-2 (selektif): HANYA kandidat p < 0,85 · PUTARAN-3: HANYA p < 0,50~~
>
> **ALASAN DICORET (U4b terukur):** `p` BUKAN pengukur "baris palsu" — `p` = ukuran
> **"Jev ragu"**. Bukti: judul asli `'2.1.1 Pengertian Analisis SWOT'` bisa `p=0,20`.
> ⇒ Ambang apa pun yang dipakai sebagai SAKLAR akan salah sasaran.
> **PENGGANTI (putusan Bos 09 Okt): TANPA AMBANG** — lihat §7c.

**Biaya Jev = ditanggung Bos** (kebijakan tetap: *"jev adalah tulang punggung app"*).

---

## 7a. 🚨 HASIL UJI BIAYA (U2, 09 Okt) — STRATEGI HEMAT v2 **GAGAL**

**Terukur di Asih (131 sub-bab):**

| Skenario | Panggilan Jev | Waktu | Putusan |
|---|---|---|---|
| S0 sekarang (`satpam.periksa`) | 1 | 0,82 dtk | baseline |
| **S1 hakim baru per-BAB** | **1** | **1,01 dtk** | ✅ **INI YANG LAYAK** |
| S2a per-sub-bab SEMUA | 17 | ≈23 dtk | ⚠️ mahal |
| S2b per-sub-bab BERTINGKAT (p<0,85) | **25** | lebih lama | ❌ **LEBIH MAHAL dari S2a** |

**MENGAPA BERTINGKAT GAGAL:** Jev melaporkan `confidence` **< 0,85 pada 46%**
kandidat (terukur: 11 dari 24). Ingat U4 — rata-rata conf Jev = **0,839**, yaitu
**di bawah ambang 0,85**. ⇒ Ambang 0,85 menangkap hampir separuh ⇒ **nol penghematan**.

**KEPUTUSAN v3:**
1. ✅ **Hakim naik kelas SAMPAI LEVEL BAB saja** (per-BAB, 1 panggilan, ~1 dtk) — gratis.
2. ❌ **Buang putaran bertingkat** dari rancangan — terbukti menambah biaya.
3. ⚠️ Kalau kelak perlu per-sub-bab → **sekali jalan semua** (17), jangan bertingkat.
4. 🚫 **Ambang 0,85 tidak boleh dipakai buta** — harus dikalibrasi ulang dulu (§11 U4b).

---

## 7c. 🔓 PUTUSAN BOS 09 Okt 2026 — **AMBANG DIBUBARKAN** (skema 2-sumber, TANPA p)

> **Verbatim Bos:** *"Masalah ambang ini tidak perlu DISELESAIKAN. Perlu DIBUBARKAN.
> … Ini bukan masalah kalibrasi; ini masalah **salah alat ukur**."*

**Kebutuhan aslinya:** mesin [3] memutuskan **sepakat / ragu / curiga** per judul.
**Definisi baru TANPA `p`:**

| Keputusan | Sumber | Aksi |
|---|---|---|
| **curiga** | **kode deterministik** — `judul_curiga` v5c (0 salah tuduh, Rp 0) | **lapor untuk review manusia** |
| **ragu** | **vonis Hakim sendiri** (per-BAB, murah) — menilai barisnya LANGSUNG, bukan membaca `p` | periksa ulang 1 putaran |
| **sepakat** | sisanya | pakai apa adanya |
| **`p`** | **HANYA info tampilan** (*"keyakinan surveyor: 0,20"*) | ⛔ **TIDAK PERNAH jadi input keputusan** |

**KENAPA INI MENYELESAIKAN:**
1. Tidak ada ambang ⇒ **tidak ada yang perlu dikalibrasi**.
2. Bukti `p=0,20` pada judul asli **tidak bisa merusak apa pun** (p bukan input).
3. Biaya dikendalikan **desain** (Hakim per-BAB), **bukan triase `p`**.
4. Selaras pagar: **H1** (lapor jangan blokir) · **P7** (profiler hanya membaca label
   surveyor) · **"mesin [3] yang memutus"**.

**TULIS ULANG TUJUAN S1:**
```
❌ SEBELUM (salah): S1 = alat HEMAT BIAYA  (hakim hanya diperiksa kalau p rendah)
✅ SESUDAH (benar): S1 = DATA DIAGNOSTIK/LAPORAN
   ⇒ `p` = info "keyakinan surveyor" yang DITAMPILKAN ke manusia,
     bukan saklar yang MENGURANGI pekerjaan hakim.
```

---

## 7b. 📊 HASIL UJI LAIN (09 Okt) — angka nyata, bukan tebakan

| Uji | Hasil terukur | Konsekuensi |
|---|---|---|
| **U5** baseline X | fid=115: **75 sub-bab · 51 PALSU (68%) · 24 ASLI** — BAB 4/4 BENAR | metrik X→Y punya titik mula |
| **U4** kalibrasi `p` | kesepakatan antar-putaran = **1,00 SELALU**; conf Jev 0,36–0,99 (rata 0,839) | → **`p` = confidence Jev** |
| **U1** adversarial | **6/6 BENAR** (angka "30"/"65" ditolak · typo "BAB VI" setia · butir daftar ditolak) | Jev tidak buta di 6 kasus ini |
| **U2** biaya | per-BAB 1 panggilan · per-sub-bab 17–25 | lihat §7a |

⚠️ **U1 BELUM membuktikan hakim berguna** (jujur): uji itu menguji **JEV**, bukan
**HAKIM** — Wulan menyusun sendiri jendela barisnya (= memberi Jev konteks bagus).
Adversarial SEJATI = kasus **asli di dalam naskah** (baris 356 Tesis 78), bukan tiruan.
⇒ **Uji kunci yang MASIH KURANG:** apakah HAKIM menangkap yang SURVEYOR lewatkan?

---

## 8. PAGAR (WAJIB MELEKAT)

| # | Pagar | Alasan |
|---|---|---|
| H1 | Hakim **LAPOR**, tidak **BLOKIR** | Kalau jadi penghalang, user stuck |
| H2 | **TIDAK digabung** jadi satu fungsi dengan surveyor | Aturan Bos |
| H3 | Tipe pertanyaan **tetap 3** (`noul`/`choice`/`score`) | Batas keras Jev; tipe baru = HTTP 503 |
| H4 | Bahan harus **KAYA** (jendela baris, bukan 400 kar) | Akar hakim buta |
| H5 | Hakim mati/gagal → **jalan lama apa adanya** | Pagar P1 & P2 |
| H6 | Ambang: **≥0,80 sepakat · 0,50–0,79 ragu · <0,50 curiga** | **HANYA sah kalau `p` terkalibrasi (S2)** |
| H7 | `criteria` **per-tipe** (noul ⛔, choice OBJEK, score ARRAY) | Pagar `_periksa_skema()` |
| H8 | Bagian 'curiga' **isinya TIDAK dibuang** — judulnya saja dilepas, isi digabung ke induk | Nol karakter naskah hilang |
| H9 | **Bahasanya = PEER REVIEWER**, bukan peer decider | Koreksi Bos (§4) |

---

## 9. YANG **TIDAK** DIUSULKAN

- ❌ Tabel/kolom baru di DB (pakai `section_state`)
- ❌ Dompet/token baru (Jev = biaya sistem)
- ❌ Fungsi Jev baru di `satpam.py` (pakai `tanya_bebas()`)
- ❌ Menggabungkan surveyor+hakim jadi satu modul
- ❌ Membuang hakim lama (LIVE di `ai.py:2350`; diupgrade, bukan dicabut)
- ❌ Mengubah logika `peta3_jev.py` selain menambah keluaran `p` (S1)

---

## 10. RISIKO

| # | Risiko | Mitigasi |
|---|---|---|
| R1 | Biaya Jev meledak | Putaran bertingkat (§7) + hanya p<0,85 |
| R2 | Hakim jadi penghalang | H1 + H5 |
| R3 | Hakim "setuju-setuju" saja | **UJI BERGIGI** (lihat §11) |
| R4 | Whack-a-mole | Perbaikan yang **MEMBUANG di kode**, bukan menambah definisi ke Jev |
| R5 | Surveyor & hakim **BUTA DI TITIK YANG SAMA** (blind spot berkorelasi) | **UJI ADVERSARIAL** (§11) |
| R6 | `p` tidak terkalibrasi tapi ambang dipakai | S2 — ukur dulu; kalau tak terkalibrasi, pakai kesepakatan antar-putaran |

---

## 11. YANG WAJIB DIUKUR SEBELUM PRODUKSI

### U1 — UJI TANGKAP **ADVERSARIAL** (koreksi Bos — bukan kesalahan suntikan acak)
**Pakai kasus NYATA dari kegagalan yang sudah terjadi** — bukan karangan:

| Kasus adversarial nyata | Asal | Harus tertangkap? |
|---|---|---|
| `"30"` jadi BAB palsu | Wulandari-PDF (nomor halaman) | ✅ |
| `"65"` jadi BAB palsu | Wulandari-PDF | ✅ |
| Typo `"BAB VI"` (harusnya V/setelah III) | Wulandari-PDF | ✅ **setia** (jangan diperbaiki!) |
| Butir daftar `"f. Pelayanan pelanggan"` jadi sub-bab | Wulandari | ✅ |
| `L000356 "PENDAHULUAN"` dianggap sub-bab | Tesis 78 | ✅ |
| `L000608 "1. Apakah…"` dianggap sub-bab | Tesis 78 | ✅ |

**TUJUAN TERBESAR UJI INI (koreksi Bos):** membuktikan surveyor & hakim **TIDAK buta
di titik yang sama**. Kalau keduanya sama-sama lewatkan satu kasus ⇒ **blind spot
berkorelasi** ⇒ hakim tidak berguna. Ini **cuma ketahuan lewat kasus nyata**, bukan
suntikan acak.

### U2 — UJI BIAYA
Berapa panggilan Jev + detik untuk Asih & Tesis 78 (dengan putaran bertingkat)?

### U3 — UJI PAGAR
Matikan Jev → revisi tetap jalan? (harus YA)

### U4 — UJI P (kalibrasi, S2) — ✅ **SELESAI 09 Okt**
Hasil (`HASIL_U4_KALIBRASI.json`): kesepakatan antar-putaran = **1,00 SELALU** ⇒
tak berguna jadi ambang. **`p` = confidence Jev** (0,36–0,99). Lihat §7b.

### U4b — KALIBRASI ULANG AMBANG (BARU, wajib sebelum pakai)
Ambang 0,85 **terbukti salah tempat** (rata-rata conf Jev = 0,839 ⇒ menangkap 46%).
Wajib: cari ambang dari sebaran conf **di naskah KACAU** (fid=115), bukan Asih yang rapi.

### U5 — METRIK PRESISI (S3)
**"sub-bab palsu turun dari X ke Y"** — naskah Wulandari-PDF (fid=115).

⚠️ **NIT BOS (09 Okt) — BASELINE WAJIB DIHITUNG ULANG DULU, JANGAN DIKUNCI BUTA.**

Angka yang beredar sebelumnya **TIDAK VALID** (dari cara lama / skrip host, fid=112):

| Sumber | Angka | Status |
|---|---|---|
| Catatan lama (`CATATAN_KEPUTUSAN_...:105`) | "89 dari 109 sub-bab palsu" | ❌ **JANGAN dipakai** — asalnya skrip host (bukan jalur resmi) |
| Nit Bos | "38+11 dari 108" | ⚠️ perlu direkonsiliasi |

**HITUNG ULANG SUDAH DILAKUKAN (09 Okt, jalur RESMI `peta3_jev.petakan(115)`, putaran=1):**
```
kandidat    : 8.555
gabung      : 4       ← baris "BAB x" polos
sistematika : [451, 454, 459, 463, 468]
label 'bab' : 2 → [459, 468]   ← KEDUANYA anggota sistematika
label 'subbab': 74
paragraf    : 85 · biasa: 8.394 · goyang: 0
⇒ BAB ASLI  = 4 + (2 − 2) = 4   ✅ (cocok "BAB 4/4")
```

**⇒ X belum boleh dikunci.** Yang belum ada: berapa dari **74 sub-bab** itu yang
**PALSU** menurut mata manusia / verifikasi jalur resmi. Selama itu belum dihitung,
baseline = **belum ada**.

**Rencana penentuan X (WAJIB berurutan):**
```
1. Ambil 74 sub-bab fid=115 dari jalur RESMI (bukan skrip host)
2. Rekonsiliasi baris-per-baris dengan audit lama (38 + 11 dari 108) — cari selisihnya
3. Verifikasi ke SUMBER (buka naskah, lihat barisnya) — bukan percaya angka lama
4. Kunci X = jumlah sub-bab palsu TERVERIFIKASI
5. Sesudah hakim dipasang → hitung Y → bandingkan
```

**Kill-switch tetap:** `Y = X ⇒ JANGAN dipasang` (aturan Bos).

📌 PELAJARAN (jangan diulang): angka lama dari **skrip host Wulan** (fid=112) **TIDAK
BOLEH** dipakai sebagai baseline. Ingat pagar tetap: **uji/ukur naskah WAJIB lewat
jalur resmi** (`peta3_jev` / `app.ai._teks_dari_berkas`), JANGAN skrip sendiri.

---

## 12. LANGKAH SESUDAH IZIN BOS

```
1. Uji di jalur UJI dulu (bukan produksi) — U1..U5 di Asih + Tesis 78 + Wulandari
2. Ukur: menangkap kesalahan? blind spot? biaya? metrik X→Y?
3. Kalau BAGUS  → naikkan ke produksi via `tanya_bebas()` (bahan baru) + S1 di surveyor
   Kalau JELEK  → JANGAN gabung/paksa (aturan Bos) — hakim tetap apa adanya
4. Backup `_arsip/pre-hakim-naik-<tgl>/` SEBELUM sentuh kode
5. Gerbang `_gerbang_hakim_*.py` di DALAM container + uji bergigi (WAJIB bisa GAGAL)
```

**Catatan alur review (Bos):** *"Jadi saya review lagi begitu kodenya jadi."*
⇒ Rancangan v2 ini disetujui secara arah; **review final Bos setelah kode jadi.**

---

## 13. KAITAN BERKAS

- `SESI_09OKT2026_KRONOLOGIS.md` · `CATATAN_KEPUTUSAN_PETA3_09OKT2026.md`
- `PANDUAN_PAKAI_JEV.md` · skill `typesafe-jev`
- `HASIL_UKUR_PETA_HALUS_08OKT2026.md` · `CATATAN_GENERALISASI_JEV_09OKT2026.md`
- `SOT_PETA_NASKAH_SATU_PINTU_08OKT2026.md` (§2.6 biaya Jev)
- `app/satpam.py` (hakim) · `peta3_jev.py` + `peta_halus_jev.py` (surveyor)
- Alat uji: `/app/_uji_adu_surveyor_hakim.py`
