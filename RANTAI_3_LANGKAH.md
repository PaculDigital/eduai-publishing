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
  `RULE_VERSION` naik v11 → `jev-peta-v12`.
- `_sketsa/agen_kedua_openrouter.py` (perkakas pilot, bukan produksi):
  penanya OpenRouter model PINNED `google/gemini-2.5-flash`, cadangan
  `openai/gpt-4o-mini`.
- Uji offline `tests/test_jev_hakim.py`: **271 lulus, 0 gagal** (dari 247).
  Uji baru 12f: agen kedua sepakat → label Jev; beda → label agen kedua;
  beda soal bab → antrean; jawaban tidak yakin → antrean; saklar mati →
  perilaku v11 lama; konteks lebar diteruskan; jejak `pk_jawaban`.

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

**Rantai TERBUKTI memperbaiki label judul palsu yang ditandai Hakim**
(Arm B: 2/16 → 10/16) dan **tidak merusak satu baris pun** di pilot.
**Tapi rantai BELUM TERBUKTI menaikkan presisi keseluruhan:**
sampel kecil (21 baris yang bisa diadili), label v11 Arm B turunan
(bukan dari run live), konteks Arm B lebih sempit dari live, dan
pengukuran penuh di 35 naskah uji masih menunggu label manusia selesai
(dikerjakan agen lain secara paralel — jangan sentuh naskah uji sebelum
labelnya selesai).

**Yang masih kurang / perlu putusan Bos:**
1. **Pengukuran penuh di 35 naskah uji** (menunggu label selesai).
2. **Transport produksi belum teruji:** combo 9router 503 saat pilot.
   Wajib uji asap 1 panggilan dari dalam container sebelum saklar
   dinyalakan; bila masih 503, rantai tidak bisa jalan di produksi
   (opsi: OpenRouter PINNED sebagai transport produksi, perlu putusan).
3. **Selisih rancangan lawan wiring:** perintah Bos "agen kedua HANYA
   baris yang ditandai Hakim" (~11 panggilan/naskah, ~Rp50), tapi wiring
   Lapis 2 yang diganti memanggil agen kedua per baris goyang
   (~83 panggilan/naskah, ~Rp375). Hakim sendiri jalan SETELAH peta jadi,
   jadi gating Hakim butuh ubah urutan pipeline (Hakim dulu, baru agen
   kedua pada yang ditandai). Bos putuskan: tetap per goyang, atau ubah
   ke gating Hakim.
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
