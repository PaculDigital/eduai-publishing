# Rantai 3 Langkah: Jev → Hakim → Agen Kedua

**Status:** dibangun di branch `agen/wulan/optimalkan-jev-hakim-v5`,
`RULE_VERSION` `jev-peta-v12`. **Belum push, belum merge, belum deploy.**
Saklar produksi mati (`EDUAI_AGEN_KEDUA_AKTIF=0`, bawaan).

**Perintah Bos (Gas 11 Nov 2026 12:01 WIB):** naskah baru live tidak boleh
butuh admin melabeli. Admin memeriksa dan melabeli itu pekerjaan besar,
maka peran admin diganti agen kedua yang membaca dan memutuskan, supaya
naskah tetap presisi tanpa ada yang tak teridentifikasi atau salah
identifikasi.

## 1. Alur

1. **Jev melabeli seperti biasa** (model 1.14, lewat satpam). TypeSafe
   resmi masih 402 (kredit habis), jadi yang melayani adalah fallback
   OpenRouter `typesafe/jev-1.14-20261014` yang sudah Bos setujui.
   Bobot fallback belum terbukti identik dengan `jev-1.14.0` resmi.
2. **Hakim v2 menandai baris ragu/curiga seperti biasa** (log saja,
   tidak blokir, ambang 0,7, K5 sudah dihapus).
3. **Agen kedua memutuskan HANYA baris goyang** (suara Jev terbelah antar
   gelombang). Agen kedua membaca baris itu dengan konteks lebar: 3 baris
   sebelum, 3 baris sesudah, dan judul bab terdekat. Lalu memutuskan
   label `bab` / `subbab` / `paragraf` / `biasa` memakai patokan yang sama
   seperti label manusia:
   - penomoran yang mengepalai blok penjelasan sendiri = subbab;
   - penomoran dalam enumerasi sebaris = biasa;
   - kalimat pertama di bawah judul/butir = paragraf;
   - salinan sistematika/daftar isi, running head, fragmen tabel = biasa.
   - Suara Jev SENGAJA tidak ditunjukkan ke agen kedua (bacaan independen).
4. **Putusan (aturan Bos):**
   - agen kedua sepakat dengan Jev → label Jev dipakai (`tetap`);
   - agen kedua beda, bukan soal judul bab → keputusan agen kedua dipakai
     (`berbalik`);
   - agen kedua beda soal judul bab (salah satu bilang `bab`) → antrean
     manusia, label tidak dipaksa;
   - agen kedua gagal menjawab atau tidak yakin (confidence < 0,5) →
     antrean manusia.
5. **Antrean manusia HANYA untuk yang benar-benar buntu:**
   - naskah tanpa penanda bab sama sekali, atau
   - agen kedua dan Jev beda soal judul bab.
   Bukan untuk tiap baris ragu. Di 35 naskah uji tahap 5: 10 baris curiga
   yang wajib ditinjau, 380 ragu dari 2.400+ baris, 2.081 sepakat.

Rantai ini **menggantikan Lapis 2 `pendapat_kedua()`** v11 (yang 0 kali
jalan live di 35 run): fungsi yang sama kini disambung ke agen kedua yang
hidup, bukan jalur baru yang terpisah. Tanpa jawaban kedua, perilaku
identik v10 (aturan lama dipertahankan).

## 2. Model agen kedua + alasan

**Pilihan utama: `google/gemini-2.5-flash`, PINNED, lewat OpenRouter
langsung** (bukan Jev, bukan 9router).

Alasan (11 Nov 2026):
- Model instruksi umum, cara baca beda dari Jev 1.14 (model klasifikasi
  khusus TypeSafe). Syarat Bos: agen kedua harus beda model/cara baca
  supaya tidak mengulang salah yang sama.
- Murah: $0,30/1 juta token masuk, $2,50/1 juta keluar (terukur 11 Nov
  2026). Saldo akun OpenRouter saat itu ~$6,38.
- JSON andal (balasan `json_object`, diurai ketat; gagal urai = antrean,
  bukan label tebakan), konteks 1 juta token.
- Dipakai pilot lewat koneksi `custom.openrouter` yang sudah terdaftar
  (kunci lewat surrogate authd, nilai kunci tidak pernah muncul di kode,
  argumen, atau log). Terverifikasi melayani `google/gemini-2.5-flash`
  di 21/21 panggilan pilot.

**Jalur produksi (di dalam container): combo umum 9router** yang diatur
Bos dari panel (bukan Jev). Model yang melayani = apa pun yang combo
layani saat itu, dicatat per panggilan dari balasan. **PENTING: combo ini
belum teruji live.** Uji coba 11 Nov 2026 gagal 2x (HTTP 503, pool model
`glm-5.3-flash` kehabisan provider). Pelari pilot berhenti sebelum
memakai panggilan Jev apa pun (fail-closed, sesuai rancangan). Jadi
transport produksi saat ini TIDAK BISA DIPAKAI dan BELUM TERUJI.

**Cadangan (bukan pilihan utama): Jev 1.13** lewat jalan tol
(`tanya_pembanding_113`). Dipakai HANYA bila model umum tidak bisa
dipakai live (kredit/akses), dan pemakaiannya WAJIB dicatat di hasil
(`model` = 1.13), tidak pernah diam-diam. 1.13 pensiun sekitar
13 Des 2026.

**Uji asap wajib sebelum saklar produksi dinyalakan:** 1 panggilan
combo 9router dari dalam container (cek balasan 200 + `model` tercatat).
Bila 503 lagi, saklar tetap mati dan rantai tidak jalan di produksi.

## 3. Yang dibangun

- `app/agen_kedua.py` (baru): saklar `EDUAI_AGEN_KEDUA_AKTIF` (bawaan 0
  = mati; nyala hanya bila env = `'1'`), `buat_pendapat_kedua_fn()`,
  `tanya_agen_kedua()` (gagal apa pun = None → antrean, tidak pernah
  label tebakan), `tanya_pembanding_113()`. Setiap keputusan dicatat
  (`fn.log` + `LOG_KEPUTUSAN`: idx, teks, suara Jev, label kedua,
  confidence, alasan, model, transport). Modul ini TIDAK berisi literal
  URL jembatan Jev / 9router / OpenRouter (lolos gerbang D1).
- `peta3_jev.py`: `pendapat_kedua()` dapat mode `'agen-kedua'` (aturan
  Bos di atas); mode `'suara'` lama tidak berubah. Wiring
  `_petakan_dari_hasil` memanggilnya per baris goyang, mengirim konteks
  lebar (5 argumen bila fn mendukung, kalau tidak 4 argumen supaya lambda
  uji lama tetap jalan), dan merekam `pk_jawaban` (idx, label Jev, label
  kedua, confidence, putusan, label akhir, alasan, model).

## 3b. v13 — Gating Hakim (Gas Bos 11 Nov 2026 12:27 WIB)

Keputusan Bos: agen kedua HANYA untuk baris yang ditandai Hakim
(ragu/curiga), **bukan per baris goyang**. `RULE_VERSION` v12 →
`jev-peta-v13`. `app/hakim_peta.py` dapat helper baru
`tandai_ragu_curiga(peta)` (tidak pernah melempar; hakim mati/galat →
himpunan kosong, gagal tertutup). `peta3_jev.py` merambatkan parameter
baru `hakim_tandai_fn` lewat `petakan()` / `petakan_dari_teks()` /
`_petakan_dari_hasil()`; Hakim mengaudit peta sementara pra-koreksi,
lalu Lapis 2 mengadili himpunan yang ditandai. Tanpa `hakim_tandai_fn`,
perilaku warisan v12 (per goyang) dipertahankan untuk uji/pelari lama.

**Koreksi (11 Nov 2026, sebelum pengukuran live):** implementasi v13
pertama (commit `fb84999`) salah membaca keputusan — ia mengadili
`goyang ∩ ditandai`. Di 35 naskah uji itu hanya 61 baris (12 dari 252
baris TSV terpetakan), dan melewatkan 27 baris ditandai Hakim yang tidak
goyang, termasuk baris curiga kode. Yang benar: himpunan adjudikasi =
**semua baris ditandai Hakim** (390 baris di 35 naskah: 380 ragu + 10
curiga; 39 dari 252 baris TSV). Baris ditandai yang tidak goyang diadili
dari suara tunggalnya (label Jev saat ini); bila agen kedua gagal pada
baris itu, masuk antrean manusia (flag tidak hilang diam-diam).
Uji offline: **287 lulus, 0 gagal** (280 lama + 7 baru 13a-8/9/10).
ATURAN 5 TIDAK diubah (tugas terpisah, butuh Gas sendiri).
  `RULE_VERSION` naik v11 → `jev-peta-v12`.
- `_sketsa/agen_kedua_openrouter.py` (perkakas pilot, bukan produksi):
  penanya OpenRouter model PINNED `google/gemini-2.5-flash`, cadangan
  `openai/gpt-4o-mini`.
- Uji offline `tests/test_jev_hakim.py`: **271 lulus, 0 gagal** (dari 247).
  Uji baru 12f: agen kedua sepakat → label Jev; beda → label agen kedua;
  beda soal bab → antrean; jawaban tidak yakin → antrean; saklar mati →
  perilaku v11 lama; konteks lebar diteruskan; jejak `pk_jawaban`.

## 3c. Hasil ukur gating v13 (11 Nov 2026)

**Pengukuran penuh 279 baris label manusia (35 naskah uji): v11 136/279
(48,7%) → rantai gating v13 150/279 (53,8%), +14 net (18 diperbaiki,
4 dirusak), antrean 4.** McNemar pada pasangan tak sepakat (18 lawan 4):
p eksak binomial dua-sisi 0,004 — signifikan. Per label benar: biasa
49→55, paragraf 43→55, subbab 32→28, bab 12→12 (tidak berubah: 0 baris
benar-bab ditandai Hakim). Per kelompok: TypeSafe 76→83, OpenRouter
60→67 (seimbang). Per jenis: hakim_ragu 4→15 (dari 19 yang ditandai),
hakim_curiga 4→5, goyang_subbab 59→60, beda_subbab 4→5. 39 baris
ditandai (6 curiga + 32 ragu + 1 ambigu-serupa T3|73), 39 panggilan
agen kedua, 0 gagal. 2 baris berbalik ikut berubah oleh koreksi
deterministik pasca-L2 — keduanya membantu (paragraf→biasa, benar).
4 baris dirusak rantai: 3 agen kedua membalik subbab benar jadi biasa
(H1-71, B4-121, A4-244), 1 masuk antrean (F4-134: beda soal bab).

**Ruang lingkup vonis:** 279 baris adalah baris SENGKETA, bukan sampel
acak. +14 berlaku di baris sulit; di seluruh 2.400+ baris sebagian
besar sepakat dan tidak tersentuh rantai. Rantai tidak memperbaiki
label bab (judul_bab_sampah 3/35 tetap 3/35; goyang_bab 14/43 tetap
14/43) dan 26 baris gabung-saja bukan kandidat Hakim.

**Run live kecil AC2 (kode v13, container):** probe melayani
`typesafe/jev-1.14-20261014` lewat OpenRouter (TypeSafe resmi 402).
Perekam dipanggil tepat 14 baris = himpunan ditandai Hakim pra-koreksi
(lawan 63 goyang di wiring v12 lama); flag pasca-koreksi 13 baris —
selisih 1 (idx 89 hilang pasca-koreksi, labelnya berubah sehingga bukan
lagi kandidat). 10 panggilan Jev pipeline + 1 probe; DB tidak berubah
(sidik 28/108/235 tetap). Fase 2 (VM, 14 panggilan agen kedua): tetap 5,
berbalik 8, antrean 1 (idx 105: confidence agen kedua 0,0); baris TSV
no 174 diperbaiki (subbab→paragraf, benar).

**Biaya terukur:** flag 390 baris di 35 naskah = 11,1/naskah (median 7,
rentang 0–43; lawan goyang 83,1/naskah di v12). Agen kedua ~Rp50/naskah
rata-rata (~Rp32 median) pada ~Rp4,5/panggilan; total dengan Jev
pemetaan ~Rp210/naskah — target Boss tercapai (bukan ~Rp535).
Anggaran pengukuran: 64 panggilan (Fase B 39 + AC2 live 11 + AC2
Fase 2 14) dari batas ~100.

Caveat ukur: flag memakai peta final tersimpan (selisih pra/pasca
terukur di AC2: 1/14); jawaban Jev tahap 5 dipakai apa adanya (jawaban
segar bisa berbeda — flag live AC2 14 lawan 16 tersimpan); koreksi
pasca-L2 di Fase B tanpa kode_label (tidak tersimpan); semua biaya
estimasi lokal (jembatan tidak mengembalikan token usage).

## 4. Biaya per naskah (perkiraan)

Harga Jev: ~Rp10,5/panggilan (terukur: 40 panggilan Rp419). Jev memakai
~16 panggilan/naskah → **~Rp150-170/naskah**.
Harga agen kedua (Gemini 2.5 Flash, perkiraan batas atas chars/4):
~Rp4,5/panggilan (prompt ~1.600 karakter + jawaban JSON pendek).

Jumlah panggilan agen kedua per naskah TERGANTUNG pada himpunan baris
yang diadili. Di sini ada **selisih rancangan lawan wiring** yang Bos
perlu putuskan (lihat bagian 6):

| Himpunan baris diadili | Rata-rata/naskah (tahap 5, 35 naskah) | Biaya agen kedua |
|---|---|---|
| Tiap baris goyang (wiring saat ini) | 83,1 (2.907/35) | ~Rp375/naskah |
| Hanya baris ditandai Hakim (ragu+curiga) | 11,1 (390/35) | ~Rp50/naskah |

Dengan wiring saat ini, rantai menambah ~Rp375/naskah di atas Jev
(~Rp160), total ~Rp535/naskah. Dengan gating Hakim, total ~Rp210/naskah.
Pemeriksaan naskah sendiri GRATIS untuk pengguna (putusan Bos 10 Nov
2026 18:57 WIB); biaya ini biaya operasional EduAi, bukan tarif pengguna.
Teks layar proses: "Pemeriksaan sedang berlangsung" (bukan "gratis").

## 5. Hasil pilot live (11 Nov 2026)

Anggaran pilot: maks ~60 panggilan. Terpakai **52 panggilan**:
Jev 29 (3 probe + 26 pemetaan) + OpenRouter 23 (2 uji asap + 5 fase 2 +
16 Arm B). DB produksi hanya dibaca (sidik sebelum/sesudah sama di semua
run). Jev dilayani `typesafe/jev-1.14-20261014` lewat OpenRouter di semua
run (TypeSafe resmi 402, fallback dipakai).

### Fase 1: transport combo gagal (0 Jev terpakai)
Probe combo 9router dari container gagal 2x, HTTP 503 (pool
`glm-5.3-flash` habis). Pelari berhenti sebelum panggilan Jev (fail-closed
sesuai rancangan). Hasil: `_verifikasi_v11/hasil_rantai3_pilot.json`.

### Fase 1b: rekam (Jev saja) + Fase 2: adili offline
Rencana cadangan dua-fase: fase 1b memetakan J2, U2, D1 (naskah BELAJAR,
bukan naskah uji) dengan fn perekam (mencatat suara/confidence/konteks
tiap baris goyang, mengembalikan None); fase 2 memanggil agen kedua dari
VM lewat OpenRouter dan menerapkan `pendapat_kedua` mode agen-kedua yang
asli plus koreksi deterministik pasca-Lapis 2 yang asli (ATURAN 2/4/5,
v6 batas, kode_label) memakai helper `peta3_jev` sendiri.

Sampel: 11 baris berlabel manusia yang dulu goyang di tahap 1.
Di run ulang fase 1b, hanya 5 yang goyang lagi (model berubah antar run);
4 tidak goyang (rantai = v11, tidak bisa membantu); 2 bukan kandidat
(judul deterministik/pemisah, dinilai dari bukti deterministik).

| Baris | Benar | v11 | Agen kedua | Rantai | Putusan |
|---|---|---|---|---|---|
| J2-190 TINJAUAN PUSTAKA | bab | bab | — | bab | judul deterministik |
| J2-191 Ukuran sangat terbatas... | biasa | subbab | — | subbab | tidak goyang |
| J2-192 Didalam pengujian... | paragraf | biasa | — | biasa | tidak goyang |
| U2-59 pemisah dokumen | biasa | biasa | — | biasa | pemisah dibuang v11 |
| U2-60 Sistematika penulisan... | paragraf | paragraf | paragraf 0,9 | paragraf | tetap |
| U2-61 TINDAK PIDANA PEDOFILIA | bab | bab | — | bab | tidak goyang |
| U2-62 a) Persetubuhan | subbab | biasa | biasa 0,9 | biasa | berbalik (salah) |
| D1-137 Berdasarkan hasil penelitian... | paragraf | biasa | paragraf 0,9 | paragraf | berbalik (DIPERBAIKI) |
| D1-141 Pendidikan adalah penentu... | paragraf | paragraf | paragraf 0,9 | paragraf | tetap |
| D1-142 a. Garis-garis Besar Haluan... | biasa | biasa | biasa 0,9 | biasa | tetap |
| D1-143 b. Undang-Undang Nomor 22... | biasa | biasa | biasa 0,9 | biasa | tidak goyang |

**Arm A: v11 7/11 → rantai 8/11.** Pada 5 baris yang diadili: v11 3/5,
rantai 4/5, agen kedua sendiri 4/5. Satu baris diperbaiki (D1-137),
nol baris dirusak. Satu kesalahan agen kedua: U2-62 "a) Persetubuhan"
dinilai butir daftar (biasa), padahal label manusia subbab (penomoran
mengepalai blok penjelasan sendiri). Prompt perlu dipertajam untuk pola
penanda huruf (a)/b)).

### Arm B: agen kedua pada 16 baris ditandai Hakim
Baris berlabel manusia yang ditandai Hakim ragu (10) / curiga (6) di
tahap 3; label v11 diverifikasi dari hasil latih tersimpan (kandidat
judul = bab/subbab); konteks hanya sebelum/sesudah dari TSV (judul bab
terdekat TIDAK tersedia di TSV — rantai live punya konteks lebih lebar,
jadi Arm B cenderung MEREMEHKAN agen kedua).

**Arm B: v11 2/16 → rantai 10/16 (+1 antrean).** Agen kedua sendiri
11/16. Satu baris masuk antrean (N2-118: v11 bab, agen kedua biasa —
beda soal bab, manusia yang putuskan; agen kedua benar di baris itu).
Pola salah agen kedua: 4x bilang `paragraf` padahal benar `biasa`
(fragmen statistik "(X4) sebesar 0.428.", kutipan bernomor, butir
bernomor "2. Kepentingan instansi...", butir peluru "• Physical layer...")
dan 1x sepakat `subbab` padahal benar `biasa` (AP-1-8). Bila agen kedua
sepakat dengan label Jev yang salah, rantai tidak bisa membantu.

### Gabungan (baris yang bisa diadili rantai)
v11 **5/21 (24%)** → rantai **14/21 (67%)** + 1 antrean (5%).
Agen kedua sendiri 15/21 (71%); rantai kehilangan 1 dibanding agen
kedua saja karena aturan Bos (beda soal bab → antrean, bukan pakai
jawaban agen kedua yang benar di baris itu).

Biaya pilot: Jev 29 panggilan ~Rp305 + OpenRouter 23 panggilan ~Rp105
= **~Rp410** (perkiraan batas atas).

## 6. Vonis jujur + yang masih kurang

**Rantai gating v13 TERBUKTI lebih presisi dari v11 pada 279 baris
sengketa** (150/279 lawan 136/279, +14 net, McNemar p=0,004), dengan
biaya agen kedua terukur ~Rp50/naskah (11,1 panggilan/naskah, median 7)
dan wiring live terbukti di AC2 (perekam tepat 14 baris ditandai).
**Tapi ini BUKAN produksi massal tanpa pengawasan:** 4 baris antrean
butuh manusia, label bab tidak membaik sama sekali, vonis hanya berlaku
di baris sulit (bukan seluruh peta), dan 4 baris dirusak rantai.

**Yang masih kurang / perlu putusan Bos:**
1. **Pengukuran penuh di 35 naskah uji — SELESAI 11 Nov 2026**
   (lihat 3c di atas).
2. **Transport produksi belum teruji:** combo 9router 503 saat pilot.
   Wajib uji asap 1 panggilan dari dalam container sebelum saklar
   dinyalakan; bila masih 503, rantai tidak bisa jalan di produksi
   (opsi: OpenRouter PINNED sebagai transport produksi, perlu putusan).
3. **Gating Hakim — SELESAI 11 Nov 2026 (Gas Bos 12:27 WIB):** wiring
   diubah ke gating Hakim (v13) dan diukur penuh. Koreksi di tengah
   jalan: v13 pertama salah memakai goyang yang ditandai (61 baris);
   diperbaiki menjadi semua baris ditandai (390 baris) sebelum ukur.
4. **Jebakan ATURAN 5 (temuan pilot, perlu aturan v13):** baris penanda
   huruf seperti "a) Persetubuhan" tidak pernah bisa jadi subbab — bila
   agen kedua bilang subbab, ATURAN 5 membatalkannya (huruf awal kecil)
   dan v6 membatalkan paragraf juga. Perbaikan butuh ubah
   `_huruf_awal_kecil` (kupas penanda huruf "a) "/"b) " dulu). BUKAN
   bagian tugas ini; jangan ubah tanpa Gas.
5. **Prompt perlu dipertajam** untuk dua pola salah terbanyak: penanda
   huruf yang mengepalai blok penjelasan (subbab, bukan butir daftar)
   dan fragmen/butir bernomor/peluru (biasa, bukan paragraf).

## 7. Berkas pilot

- `_verifikasi_v11/hasil_rantai3_pilot.json` — fase 1, combo 503.
- `_verifikasi_v11/hasil_rantai3_fase1b.json` — rekaman J2+U2 (16 Jev).
- `_verifikasi_v11/hasil_rantai3_fase1b_d1.json` — rekaman D1 (10 Jev).
- `_verifikasi_v11/hasil_rantai3_fase2.json` — adjudikasi 5 baris goyang.
- `_verifikasi_v11/hasil_rantai3_armb.json` — Arm B 16 baris.
- `_verifikasi_v11/jalankan_rantai3.py` — pelari fase 1 (combo, gagal).
- `_verifikasi_v11/jalankan_rantai3_fase1b.py` — pelari rekam.
- `_verifikasi_v11/fase2_rantai3.py` — adjudikasi offline + OpenRouter.
- `_verifikasi_v11/armb_agen_kedua.py` — Arm B.
- `_verifikasi_v11/sampel_rantai3.json`, `sampel_rantai3_d1.json` — sampel.
