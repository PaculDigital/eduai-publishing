# 🛡️ RANCANGAN SATPAM JEV untuk EduAi — 04 Okt 2026

> 🚩 **DIPERBARUI 07 Okt 2026 — CARA PAKAI JEV DI SINI SUDAH USANG.**
> Sebagian isi catatan ini dibuat waktu Wulan **belum membaca dokumentasi resmi**,
> jadi ada **klaim yang keliru & berbahaya** (mis. *"skema Jev tertutup / hanya 3 nama"*,
> *"Jev tidak stabil"*, *"hanya 2 tipe sah"*, *"criteria boleh string"*).
> ⇒ **ACUAN TUNGGAL cara pakai Jev sekarang:** `PANDUAN_PAKAI_JEV.md`
>   + skill `typesafe-jev` (dokumentasi RESMI `docs.typesafe.ai`).
> ⇒ Blok lama **TIDAK dihapus** (riwayat) — tapi **DILARANG dipakai sebagai panduan**.
> ⇒ Penjaga: `_gerbang_skema_jev.py` + `_uji_gigi_skema_jev.py`.



<!-- ⏸️ SOT: RANCANGAN — belum dijalankan -->
> # ⏸️ RANCANGAN — belum dijalankan, BUKAN penentu status.
> Isi berkas ini = **usulan/rancangan yang MENUNGGU keputusan Bos**.
> ❌ JANGAN dibaca sebagai keadaan kini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> **Status:** RANCANGAN. Belum ada satu baris kode EduAi yang diubah.
> Semua angka di bawah **TERUKUR** dari uji nyata 04Okt26 (naskah asli Asih +
> 5 kasus berantakan), bukan dugaan.

---

## 1. MASALAH YANG DITUTUP (akar)

```text
AKAR (satu kalimat):
  EduAi MENEBАК bab dari pola tulisan (regex) di 11 mesin, lalu hasil
  tebakannya langsung dipakai — tanpa ADA satu pun pemeriksa.

AKIBAT TERUKUR:
  · 'BAB I' in 'BAB III' = True  → revisi BAB II/III/IV tercatat 'BAB I'
  · kategori 'bab' vs 'bab1'     → Mode Belajar terkunci
  · "BAB IIII" (salah tulis)     → diterima apa adanya (celah terbuka)
  · daftar isi ikut terbaca      → 15 kandidat bab padahal cuma 5 asli
  · tiap naskah baru = celah baru = tambal lagi (sampai kiamat)
```

---

## 2. APA YANG DIUJI NYATA (bukti, bukan teori)

**Jev = model "System One" TypeSafe. Keluarannya TIPE + PROBABILITAS,
tidak bisa menulis teks, jadi tidak bisa mengarang kalimat.**

### 2a. Naskah ASLI Asih (159.909 karakter, 5 bab)

```text
MESIN LAMA (regex)  : 15 kandidat judul bab
                       (5 dari daftar isi + 5 sampah + 5 asli)
                       ⇒ HARUS MENEBАК mana yang asli
JEV (diberi 15 baris  ): jumlah_bab = 5   confidence 1,00
                       : berurutan = 0,95
                       : ada_metode = 0,99 · ada_hasil = 0,99
                       ⇒ JEV TAHU jawabannya. Tidak tertipu.
BIAYA: in=515 out=102 token = Rp 0,34 · 0,89 detik (4 pertanyaan sekaligus)
```

### 2b. Lima kasus berantakan

```text
┌────┬──────────────────────────┬──────────────────┬─────────┬─────────┐
│ No │ KASUS                    │ JAWABAN JEV      │ BENAR?  │ CONFID. │
├────┼──────────────────────────┼──────────────────┼─────────┼─────────┤
│ U1 │ "BAB IIII" salah tulis   │ 5 bab            │ ✅      │ 0,97    │
│    │                          │ romawi SAH? 0,06 │ ✅      │ (tahu!) │
│    │                          │ berurutan 0,41   │ ⚠️ turun│         │
│ U2 │ Artikel jurnal (tanpa BAB)│ "5 bab" (prob.66)│ ❌      │ 0,59    │
│ U3 │ Proposal 3 bab           │ 3 bab            │ ✅      │ 0,86    │
│ U4 │ Daftar isi menggoda      │ 5 bab (bukan 10) │ ✅      │ 0,98    │
│ U5 │ Judul MENEMPEL           │ 5 bab            │ ✅      │ 0,95    │
└────┴──────────────────────────┴──────────────────┴─────────┴─────────┘
```

**TEMUAN PALING PENTING:**

```text
1. JEV MENANGKAP "BAB IIII" — celah yang mesin regex BELUM bisa tutup.
2. JEV JUJUR: saat dia tidak tahu (U2 artikel jurnal), confidence-nya
   TURUN ke 0,59 — bukan mengarang 0,99. Kalibrasinya nyata.
3. JEV MENYARING daftar isi sendiri (U4: 5 bab, bukan 10).
```

---

## 3. CARA JEV DIPANGGIL (fakta teknis, sudah diuji)

```text
Endpoint : POST https://openrouter.ai/api/v1/systemone   ← BUKAN chat!
Model    : typesafe/jev-1.13   (alias: jev-latest)
Pintu    : /chat/completions DITOLAK:
           "typesafe/jev-1.13 is a decisions model and cannot be used
            with the chat/completions endpoint."

BENTUK KIRIMAN:
{
  "model": "typesafe/jev-1.13",
  "state": "teks naskah / kandidat bab",
  "questions": {
     "nama_pertanyaan": {
        "instructions": "pertanyaan bahasa manusia",
        "type": "noul"  |  "choice"  |  "score",
        "criteria": ["..."]  atau  {"opsi": "penjelasan"},
        "options": ["..."]
     }
  }
}

BENTUK BALASAN (nyata dari OpenRouter):
{
  "answers": {
     "nama_pertanyaan": {
        "type": "choice",
        "choice": "pendahuluan",
        "probabilities": {"tinjauan":0.04, "pendahuluan":0.78, "metode":0.18},
        "confidence": 0.68
     }
  },
  "usage": {"input_tokens":515, "output_tokens":102, "cost":0.00002163}
}

KUNCI: kunci OpenRouter yang SUDAH ADA di 9router — TERBUKTI DITERIMA.
BIAYA : Rp 0,22 – Rp 0,36 per panggilan (4 pertanyaan sekaligus).
WAKTU : 0,54 – 0,89 detik.
```

### ⚠️ CATATAN PENTING soal 9router

```text
Jev TIDAK BISA lewat 9router apa adanya: 9router mengirim ke
/chat/completions, sedangkan Jev hanya ada di /systemone.

🟢 PUTUSAN BOS 04Okt26 = JALAN (a): tambah jenis provider BARU
   "typesafe" di 9router dengan baseUrl /v1/systemone.
   ⇒ tetap SATU PINTU (aturan Bos terjaga).
   ⇒ WAJIB hati-hati: 9router melayani SEMUA proyek (EduAi, WAUPB,
     Insight-pro, statistik). Rusak = semua kena.
   ⇒ Urutan kerja WAJIB: baca kode definisi provider dulu → tunjukkan
     rancangan → BACKUP → baru ubah → uji.
```

### 4d. RENCANA PROVIDER "typesafe" DI 9ROUTER (terbaca dari kode 9router)

```text
BENTUK definisi provider di 9router (nyata, dari chunk 3753.js):

  { id:"openrouter", priority:10, hasFree:true, alias:"openrouter",
    display:{name:"OpenRouter", icon:"router", color:"#F97316",
             textIcon:"OR", website:"https://openrouter.ai",
             notice:{apiKeyUrl:"https://openrouter.ai/settings/keys"}},
    category:"freeTier", authType:"apikey", authModes:["apikey"],
    transport:{ baseUrl:"https://openrouter.ai/api/v1/chat/completions",
                thinkingFormat:"openai",
                headers:{"HTTP-Referer":"...","X-Title":"..."} },
    models:[ {id:"...", name:"..."}, ... ] }

⇒ 9router punya 77 provider. Yang dibutuhkan = SATU provider baru:
  { id:"typesafe", ...,
    transport:{ baseUrl:"https://openrouter.ai/api/v1/systemone" },
    models:[{id:"typesafe/jev-1.13", name:"Jev 1.13 (TypeSafe)"}] }

⛔ HAMBATAN YANG WULAN TEMUKAN (harus diselesaikan, jangan disembunyikan):
   9router merangkai permintaan dalam bentuk CHAT (messages[]) untuk
   SEMUA provider. Jev butuh bentuk LAIN:
      { state:"...", questions:{...} }  →  balas {answers:{...}}
   ⇒ Menambah entri provider SAJA tidak cukup — perlu KODE PENERJEMAH.
   ⇒ Kode inti 9router berbentuk BUNDLE hasil build (.next/server/chunks).
     Mengubah bundle = tidak sehat & hilang saat 9router di-update.

🔴 KOREKSI WULAN (04Okt26, penting — jangan diulang):
   Wulan sempat mengira `/api/translator` = fitur resmi menambah penerjemah
   provider. SETELAH DIBACA KODENYA → SALAH. Faktanya:
     · /api/translator/save  = tulis berkas contoh ke logs/translator/
     · /api/translator/load  = baca berkas contoh itu
     · hanya 8 nama berkas yang diterima (1_req_client.json …
       7_res_client.json) — jejak DEBUG permintaan.
   ⇒ Itu ALAT DEBUGGING, bukan jalur menambah provider.
   ⇒ PELAJARAN: baca kode sampai habis sebelum menyimpulkan.

JUMLAH PROVIDER di 9router: 77 (terbaca dari chunk 3753.js)
ENDPOINT yang mungkin relevan (belum dibedah): /api/provider-nodes,
/api/providers/[id]/test, /api/models, /api/combos.
```

---

## 4. ATURAN SATPAM (yang Bos harus periksa dulu)

### 4a. Tiga pertanyaan tetap

```text
Q1. jumlah_bab    (choice: 0 / 1 / 3 / 5 / 7)
    "Berapa bab akademik yang benar-benar ada di naskah ini?"

Q2. semua_romawi_sah (noul/ya-tidak)
    "Apakah semua nomor bab memakai angka romawi yang SAH (I..V)?"

Q3. berurutan (noul/ya-tidak)
    "Apakah urutan bab tidak melompat?"
```

### 4b. TIGA PINTU KEPUTUSAN (inilah satpamnya)

> **AMBANG DITETAPKAN BOS 04Okt26 = 0,80** (bukan 0,90).

```text
┌──────────────────────────┬────────────────────────────────────────────┐
│ KEPUTUSAN                │ SYARAT & TINDAKAN                          │
├──────────────────────────┼────────────────────────────────────────────┤
│ ✅ LOLOS — pakai hasil   │ confidence ≥ 0,80 DAN semua pertanyaan     │
│    lanjut otomatis       │ yang WAJIB dijawab TINGGI                  │
│    (mahasiswa tak tahu   │ Contoh terukur: naskah Asih (1,00/0,95)    │
│     ada satpam)          │ dan U4/U5 (0,95–0,98)                      │
├──────────────────────────┼────────────────────────────────────────────┤
│ ❓ TANYA mahasiswa 1×    │ confidence 0,50–0,79                       │
│    tampilkan hasil baca  │ Contoh terukur: U3 proposal (0,86)         │
│    + tombol betulkan     │ Kalimat: "EduAi membaca 5 bab: I · II ·    │
│                          │ III · IV · V — sudah pas?"                 │
│                          │ [Ya, benar]  [Ada yang perlu diubah]       │
├──────────────────────────┼────────────────────────────────────────────┤
│ ⛔ JANGAN PAKAI          │ confidence < 0,50                          │
│    minta mahasiswa       │ Contoh terukur: U2 artikel jurnal (0,59)   │
│    tunjukkan sendiri     │ Kalimat: "Naskah ini belum terbaca jelas.  │
│                          │ Tunjukkan bagian babnya, ya." + unggah     │
│                          │ atau tandai manual                         │
└──────────────────────────┴────────────────────────────────────────────┘
```

### 4b-1. CATATAN SOAL AMBANG 0,80 (jujur, terukur)

```text
Dampak ambang 0,80 vs 0,90 — dari 5 kasus uji 04Okt26:

  Kasus                       conf  | 0,90  | 0,80 (putusan Bos)
  Naskah Asih (5 bab)         1,00  | LOLOS | LOLOS
  U1 "BAB IIII"               0,97  | LOLOS | LOLOS
  U4 daftar isi               0,98  | LOLOS | LOLOS
  U5 judul menempel           0,95  | LOLOS | LOLOS
  U3 proposal 3 bab           0,86  | TANYA | LOLOS  ← BEDA
  U2 artikel jurnal           0,59  | TOLAK | TANYA  ← BEDA

⇒ Ambang 0,80 membuat:
   · lebih banyak naskah lolos otomatis (mahasiswa lebih sedikit terganggu)
   · U3 (proposal) lolos tanpa tanya — BENAR, hasil baca 3 bab memang tepat
   · U2 (artikel jurnal) masuk pintu TANYA (bukan TOLAK) — masih aman,
     karena mahasiswa tetap diminta konfirmasi, tidak langsung dipakai
⚠️ RISIKO YANG WULAN SAMPAIKAN TERBUKA: makin rendah ambang, makin besar
   peluang hasil SALAH dipakai tanpa tanya. 0,80 masih aman menurut data
   5 kasus ini, TAPI data masih sedikit → perlu uji 3–5 naskah lagi.
```

### 4c. Aturan tambahan (pagar)

```text
P1. Satpam TIDAK PERNAH memblokir pekerjaan tanpa jalan keluar —
    selalu ada tombol "saya tunjukkan sendiri".
P2. Satpam MATI → aplikasi tetap jalan pakai cara lama (fail-open).
    Kalau Jev tidak terjawab/down → lewati satpam, jangan gantung user.
P3. Hasil satpam yang sudah dikonfirmasi mahasiswa → SIMPAN sebagai
    PATOKAN naskah itu. Jangan tanya lagi untuk naskah yang sama.
P4. Teks ke mahasiswa DILARANG menyebut "AI"/"Jev"/nama model,
    DILARANG kata PERINGATAN/GAGAL/BAHAYA (aturan lama, tetap berlaku).
P5. Satpam tidak menilai MUTU tulisan — hanya STRUKTUR (jumlah bab,
    urutan, kesahan nomor). Mutu tetap tugas AI revisi.
```

---

## 5. APA YANG TIDAK DISENTUH

```text
✅ 11 mesin deteksi lama TETAP JALAN (satpam memeriksa hasilnya,
   bukan menggantikan)
✅ Tidak ada tabel baru — pakai section_state yang sudah ada
✅ Tidak ada halaman baru untuk mahasiswa (konfirmasi cukup 1 kartu
   di halaman yang sudah ada)
✅ Tidak mengubah alur revisi, dompet, atau harga
```

---

## 6. BIAYA (terukur)

```text
1 pemeriksaan naskah     = Rp 0,22 – 0,36
1.000 naskah             = Rp ~300
1 juta naskah            = Rp ~300.000
Per naskah, satpam LEBIH MURAH dari 1 Token Revisi (jauh).
```

---

## 7. YANG BELUM DIUJI (jujur)

```text
⚠️ 1 dari 5 kasus SALAH (U2 artikel jurnal) → maka pagar confidence
   itu WAJIB, bukan pilihan.
⚠️ Baru 1 naskah asli diuji. Butuh 3–5 naskah gaya kampus berbeda
   sebelum dinyatakan layak produksi.
⚠️ Belum diuji: naskah .doc lama, naskah pindai/PDF, naskah sangat
   panjang (>200rb karakter).
⚠️ Belum diukur: berapa persen mahasiswa yang akan masuk pintu
   "TANYA" (kalau ternyata 80%, satpam terasa mengganggu).
```

---

## 8. LANGKAH BERIKUT (menunggu putusan Bos)

```text
L1. Bos periksa ATURAN §4 (lolos/tanya/tolak) — betulkan kalau salah.
L2. Uji 3–5 naskah gaya kampus berbeda (naskah Bos sendiri, naskah uji
    lain yang sudah ada di proyek) → lihat apakah pintu "TANYA" jarang.
L3. Bos putuskan cara pasang: (a) provider baru di 9router, atau
    (b) satpam panggil langsung.
L4. BARU tulis kode: 1 berkas satpam (~100 baris) + 1 kartu konfirmasi.
L5. Uji bergigi: suntik kasus rusak → satpam HARUS menangkap.
```
