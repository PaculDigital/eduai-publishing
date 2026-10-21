# 🌉 RANCANGAN JEMBATAN SATPAM JEV — 05 Okt 2026

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


> **Status:** RANCANGAN. Belum ada kode yang ditulis.
> Semua fakta di bawah **TERUKUR** (uji nyata 04–05Okt26), bukan dugaan.

---

## 1. MENGAPA JEMBATAN INI PERLU

```text
MASALAH (terukur, bukan dugaan):
  · Provider "Openrouter JEV" di 9router = AKTIF ✅
  · Kunci OpenRouter tersimpan di sana ✅
  · defaultModel = typesafe/jev-1.13 ✅
  · TAPI 9router mengirim ke /chat/completions sedangkan Jev 1.13
    HANYA hidup di endpoint "decisions".

BUKTI (uji 05Okt26 lewat 9router):
  JEV/typesafe/jev-1.13 → HTTP 503
  "[400]: typesafe/jev-1.13 is a decisions model and cannot be used
   with the chat/completions endpoint. Use the /api/alpha/decisions
   endpoint instead."
  ⇒ Permintaan SAMPAI ke OpenRouter (jalur provider SEHAT), yang gagal
    hanya BENTUK PINTUNYA.

BUKTI (uji langsung, 05Okt26):
  POST https://openrouter.ai/api/alpha/decisions   → HTTP 200 ✅ (0,62 dtk)
  POST https://openrouter.ai/api/v1/systemone      → HTTP 200 ✅ (0,32 dtk)
  ⇒ DUA endpoint ini setara (balasan identik).
```

---

## 2. PUTUSAN BOS YANG SUDAH DIKUNCI

```text
1. Cara pemasangan     : JEMBATAN KECIL (opsi ii) — bukan ubah 9router
2. Tempat jembatan     : /opt/data/services/satpam-jev/
3. Kunci               : dari provider "Openrouter JEV" di 9router
                         ⇒ TIDAK ada kunci lain (Bos: "Tidak ada kunci lain")
4. Bentuk pesan        : OPSI (a) — jembatan = PIPA, bukan penafsir.
                         Pemanggil mengirim JSON {state, questions},
                         jembatan meneruskan apa adanya.
```

---

## 3. CARA KERJA JEMBATAN (1 berkas, ~90 baris)

```text
        ┌──────────────────────────────────────────────────────┐
        │  EduAi / 9router                                     │
        │  POST http://<jembatan>:8130/v1/chat/completions     │
        │  { "model": "SATPAM/typesafe/jev-1.13",              │
        │    "messages": [ { "role": "user",                   │
        │        "content": "{\"state\":\"...\",\"questions\":{...}}" } ] } │
        └──────────────────────┬───────────────────────────────┘
                               ↓
        ┌──────────────────────────────────────────────────────┐
        │  JEMBATAN (satpam-jev)                               │
        │  1. ambil content pesan TERAKHIR                     │
        │  2. json.loads → {state, questions}                   │
        │  3. kirim ke OpenRouter decisions (kunci dari 9router)│
        │  4. terima {answers, usage}                          │
        │  5. balas bentuk [OI]:                               │
        │     { "choices":[{"message":{"role":"assistant",     │
        │        "content": "<JSON answers>"}}], "usage":{...} }│
        └──────────────────────┬───────────────────────────────┘
                               ↓
        POST https://openrouter.ai/api/alpha/decisions
             { "model":"typesafe/jev-1.13",
               "state":"...", "questions":{...} }
                               ↓
             { "answers":{...}, "usage":{...}, "provider":"TypeSafe" }
```

```text
PRINSIP PIPA (penting):
  · Jembatan TIDAK menafsirkan isi naskah
  · Jembatan TIDAK menyusun pertanyaan
  · Jembatan TIDAK memutuskan apa pun tentang bab
  ⇒ Semua kecerdasan (pertanyaan + keputusan) ada di EduAi.
    Jembatan hanya MENERJEMAHKAN BENTUK PINTU.
```

---

## 4. BERKAS YANG DIBUAT (rencana)

```text
/opt/data/services/satpam-jev/
   ├── jembatan.py          ~90 baris (FastAPI/uvicorn ringan)
   ├── Dockerfile           ringan (python:3.12-slim)
   ├── docker-compose.yml   port 8130, jaringan host-accessible
   ├── jalankan.sh          pola sama proyek Bos (build + up)
   └── BACA_INI.md          cara pasang / matikan / periksa

BACA KUNCI:
   jembatan baca DB 9router (/app/data/db/data.sqlite di container 9router)
   lewat `docker exec 9router` ATAU mount read-only DB-nya.
   ⚠️ WAJIB diuji dulu mana yang bisa dari sisi jembatan.
   Alternatif (kalau mount sulit): jalankan jembatan DI DALAM jaringan
   yang sama + baca DB lewat docker exec.
```

---

## 5. CARA DAFTAR KE 9ROUTER (jalur RESMI, Bos sudah pakai 17×)

```text
POST /api/provider-nodes
{
  "name"    : "Satpam JEV",
  "prefix"  : "SATPAM",
  "apiType" : "chat",
  "baseUrl" : "http://172.17.0.1:8130/v1",
  "type"    : "openai-compatible"
}
⇒ lalu tambahkan koneksi (kunci) untuk node itu — kunci apa saja
  (jembatan tidak memakai kunci 9router; dia pakai kunci OpenRouter sendiri)
  ⚠️ PERLU DIPUTUSKAN: node butuh kunci sendiri (dummy) supaya 9router
  mau mengirim. Wulan sarankan kunci dummy (mis. "satpam-lokal").
```

---

## 6. CARA MATIKAN (kalau bermasalah)

```text
1. docker stop satpam-jev          → jembatan mati
2. hapus provider node "Satpam JEV" di 9router
⇒ EduAi kembali seperti semula. TIDAK ada jejak di kode 9router.
```

---

## 7. UIJI YANG WAJIB LULUS SEBELUM DIPAKAI EDUAI

```text
T1. Panggil jembatan langsung (curl) → balasan bentuk [OI] benar
T2. Panggil lewat 9router → SATPAM/typesafe/jev-1.13 → 200
T3. Bandingkan hasil dengan panggilan LANGSUNG ke OpenRouter
    ⇒ harus IDENTIK (jawaban + confidence)
T4. Uji naskah Asih (5 bab) → jawab "5", confidence tinggi
T5. Uji kasus "BAB IIII" → tangkap kesalahan romawi
T6. Uji jembatan MATI → pastikan EduAi tidak menggantung (fail-open)
```

---

## 8. YANG TIDAK DISENTUH

```text
✅ Kode 9router        — TIDAK disentuh sama sekali
✅ Kode EduAi          — TIDAK disentuh (sampai Bos perintahkan)
✅ Proyek lain (OJS, WAUPB, statistik) — TIDAK disentuh
✅ Kunci lama           — TIDAK diubah; dibaca dari tempat yang sudah ada
```

---

## 9. RISIKO JUJUR

```text
⚠️ R1. Jembatan = komponen BARU (aturan Bos: "tidak mau buat baru").
       ⇒ sudah Bos setujui sebagai pengecualian (opsi ii).
⚠️ R2. Jembatan MATI → model JEV di 9router gagal. Proyek lain TIDAK
       terpengaruh (mereka tak memakai prefix SATPAM).
⚠️ R3. Kunci OpenRouter dibaca jembatan ⇒ salinan kunci ada di memori
       proses. Tidak ditulis ke berkas/slog.
⚠️ R4. Baru 1 naskah asli diuji. Perlu uji 3–5 naskah lagi.
```

---

## 10. LANGKAH BERIKUT (menunggu izin Bos)

```text
L1. Bos periksa rancangan ini (§3 pipa, §4 berkas, §5 daftar).
L2. Uji: apakah jembatan bisa membaca DB 9router (§4 ⚠️).
L3. Tulis kode jembatan + jalankan → uji T1–T3.
L4. Daftar ke 9router → uji T4–T5 (naskah Asih).
L5. Lapor hasil → Bos putuskan apakah lanjut ke EduAi.
```
