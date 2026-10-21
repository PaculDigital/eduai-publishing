# 🏛️ LAPORAN BANK SOAL (L2) — 04 Okt 2026

## HASIL DEPLOY

```text
Image LIVE   : eduai-app:20261004_133352-sot
Titik mundur : eduai-app:cadangan-pra-sot
Backup DB    : _arsip/pra-banksoal/20261004_133337/eduai.db
               (ab2e7449981afcdc6743940cea29700f · 24 tabel · 5 user · 27 berkas)
Backup berkas: _arsip/pre-banksoal-20261004/ (belajar.py · main.py · belajar_insight.html + MD5)
```

## APA YANG DIBANGUN

**L2 Bank Soal** = pertanyaan yang biasa ditanyakan penguji, **4 tingkat**:
`dasar` · `menengah` · `tajam` · `jebakan`. Setiap soal punya:
- **tanya** — pertanyaan penguji
- **tumpu** — KUTIPAN ASLI dari naskah (titik tumpu, bukan karangan)
- **kunci** — 1-2 kalimat ARAH jawaban (bahan penilaian nanti di L3)

## CARA TITIP DI YANG SUDAH ADA (patuh aturan "SUDAH ADA")

```text
✅ kolom `soal_json` di `belajar_naskah` SUDAH ADA sejak awal → tinggal dipakai
✅ halaman `/belajar/insight/{fid}` SUDAH ADA → Bank Soal dititipkan di bawah
✅ pola `PROMPT_*` + `_urai_*` + pagar hemat ditiru dari mesin insight (teruji)
✅ TIDAK ada tabel / halaman / dompet / jalur baru
```

## BERKAS

```text
app/belajar.py      : +PROMPT_SOAL · +_urai_soal · +hitung_soal ·
                      +baca_soal · +_simpan_soal · +SOAL_PER_BAB = 4
app/main.py         : rute POST menerima `minta` ('insight' | 'soal');
                      GET mengirim `soal` + `ada_soal` + `jml_soal` ke halaman
app/templates/belajar_insight.html : bagian "🏛️ Bank Soal Ujian" + 11 kelas CSS
                      BARU (`.bank*`, `.soal*`, `.lencana`, `.kosong2`) —
                      sengaja pakai nama baru supaya tidak bentrok
_uji_bank_soal.py   : 20 uji (di root proyek, TIDAK ikut image)
```

## UJI (naskah NYATA `TESIS_LENGKAP_Goras.docx`)

```text
Uji mesin                 : 20 LULUS / 0 GAGAL
AI nyata                  : 7,5 detik → 4 soal
PAGAR HEMAT               : panggil ke-2 = 0,00 detik, TIDAK panggil AI
Tiap soal punya tumpu     : 4/4 ✅ (kutipan asli naskah)
Level bervariasi          : dasar · menengah · tajam · jebakan ✅
soal_json tidak merusak insight_json ✅
Halaman nyata             : 4 kartu · 4 lencana · 4 tumpu · 4 kunci ✅
Potret + vision (desktop & HP) : rapi, tidak terpotong ✅
Gerbang visual             : BERSIH (produksi /belajar & /)
periksa_kode.sh            : LULUS
Produksi                   : / =200 · /masuk =200 · /belajar =303 · /kolaborasi =303
Data produksi              : 24 tabel · 5 user · 27 berkas UTUH
Berkas uji di image        : 0 ✅
```

## CONTOH MUTU SOAL (nyata dari AI, bukan contoh buatan)

```text
[DASAR] "Dalam Bab I ini, penulis menyebut digital readiness sebagai variabel
         mediasi. Boleh dijelaskan apa yang dimaksud?"
   📄 "digital readiness, yaitu kapasitas dan kemauan karyawan untuk mengadopsi"
   🔑 kapasitas & kemauan karyawan mengadopsi serta memanfaatkan teknologi...

[JEBAKAN] "Indikator 'kecepatan mempelajari peran atau tanggung jawab baru'
          dengan proporsi ragu-ragu 25,93% masuk variabel yang mana?"
   📄 "Kecepatan mempelajari peran atau tanggung jawab baru saat rotasi"
   🔑 Indikator ini masuk digital readiness, BUKAN adaptive performance...
```

## 🧭 STATUS 4 LAYER MODE BELAJAR (jawaban pertanyaan Bos)

```text
L1 INSIGHT per BAB    ✅ LIVE (deploy 13:08)
L2 BANK SOAL per BAB  ✅ LIVE (deploy 13:33)
L3 SIMULASI SIDANG    ⏳ BELUM — mahasiswa MENJAWAB, AI MENILAI → SKOR
L4 SKOR PENGUASAAN    ⏳ BELUM — progres per bab, bisa dilihat pembimbing
```

**Teknis L3+L4 (rancangan §4.9, belum dikoding):**
```text
soal dari bank → mahasiswa KETIK jawabannya sendiri → AI nilai
(bandingkan dgn `kunci`, tunjuk paragraf naskah) → nilai per soal →
skor tersimpan → naik ke L4 "Kesiapan Sidang X%"
Pagar: tanya dulu, jawab dulu, BARU nilai (anti ilusi paham);
       skor HANYA dari menjawab; setiap nilai sebut kutipan naskah.
```

## ⚠️ JEBAKAN BARU (catat)

```text
DB uji `/tmp/data_uji/eduai.db` KOSONG (4096 byte) setelah `bash jalankan.sh`
→ container dibangun ulang, `/tmp` hilang (bukan bind-mount).
→ SELALU jalankan `_siapkan_data_uji.py` lagi sesudah deploy; cek ukuran DB
  (>1 MB) sebelum uji.
```
