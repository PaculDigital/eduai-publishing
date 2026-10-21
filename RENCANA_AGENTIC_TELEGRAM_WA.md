# RENCANA PENGEMBANGAN — AGENTIC + TELEGRAM/WA (EduAi)

<!-- ⏸️ SOT: RANCANGAN — belum dijalankan -->
> # ⏸️ RANCANGAN — belum dijalankan, BUKAN penentu status.
> Isi berkas ini = **usulan/rancangan yang MENUNGGU keputusan Bos**.
> ❌ JANGAN dibaca sebagai keadaan kini.

> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.


> **STATUS: RANCANGAN SAJA — BELUM DIJALANKAN.**
> Dibuat 16 Sep 2026 atas arahan Bos: *"simpan dulu sebagai rencana pengembangan
> ke agentic dan telegram atau wa nantinya sekaligus rancang infrastrukturnya
> (tapi belum dijalankan) agar tidak tumpang tindih dengan infrastruktur yang
> sekarang."*
>
> **ATURAN FILE INI:** tidak ada satu pun langkah di sini yang dikerjakan tanpa
> ACC Bos. Ini dokumen peta, bukan perintah kerja.

---

## BAGIAN 0 — INVENTARIS INFRASTRUKTUR YANG ADA SEKARANG (hasil ukur, bukan teori)

Diukur 16 Sep 2026 dengan `docker ps` / `ss` / `docker network inspect`.

### 0.1 Container yang hidup

| Container | Port (host → container) | Fungsi | Terkait EduAi? |
|---|---|---|---|
| `eduai-app` | `127.0.0.1:8100 → 8000` | **EduAi produksi** (FastAPI) | ⭐ INTI |
| `oo-converter` | `127.0.0.1:18081 → 80` | OnlyOffice Document Server (editor) | ⭐ dipakai EduAi |
| `9router` | `172.17.0.1:20128` (tanpa port publish) | **Gerbang AI** (semua panggilan LLM) | ⭐ INTI |
| `hermes` | `0.0.0.0:9119` | Agent Hermes (Wulan) | alat kerja |
| `oja-*` (`nojs-ojs_web-1`, `oja-proxy`, `oja-ojs_db-1`, `oja-mcp`) | `80/443`, `8080`, `8765` | Penerbitan jurnal-ojs (proyek LAIN) | ✗ terpisah |
| `blast_app` | `0.0.0.0:8081` | UPB WA Blast (proyek LAIN) | ✗ terpisah |
| `UPB_WA_BLAST`, `gowa` | `gowa` exited, port `3000` | **GOWA** = WhatsApp gateway (go-whatsapp-web-multidevice) | 🔶 calon dipakai |
| `gs-compressor`, `doc-converter`, `AurixAgent` | — | alat bantu | ✗ |

### 0.2 Port yang SUDAH terpakai di host (JANGAN dipakai ulang)

```
80  443  8080  8081  8100  8765  9119  18081
```
Port `3000` (GOWA) saat ini kosong karena container-nya `Exited`.

### 0.3 Jaringan docker

| Jaringan | Anggota | Catatan |
|---|---|---|
| `eduai-net` | (kosong saat ini — EduAi jalan di `bridge` default) | dibuat tapi belum dipakai |
| `wa-blast-net` | `blast_app` | milik proyek WA Blast |
| `oja_ojs_net` | OJS | proyek lain |
| `bridge` | `eduai-app`, `oo-converter`, `gowa`, dll | default |

### 0.4 Jalur AI (satu-satunya)

```
eduai-app  →  http://172.17.0.1:20128/v1  →  container `9router`  →  model
              (EDUAI_ROUTER_BASE)            (combo "EduAi")
```
🔴 **ATURAN:** SEMUA panggilan AI lewat `9router`. Tidak ada jalur lain.
Gerbang biaya = `9router` usage log. Jangan bikin jalur AI kedua.

### 0.5 Jalur data

```
Naskah    : /app/uploads/<user_id>/*.docx     (bind-mount dari host)
Database  : /app/data/eduai.db                (SQLite, bind-mount)
Dokumen   : OnlyOffice via `oo-converter`     (127.0.0.1:18081)
```

### 0.6 Yang BELUM ada di EduAi (inventaris kosong)

- ❌ Tidak ada Telegram (nol baris kode)
- ❌ Tidak ada WA
- ❌ Tidak ada queue/celery/task worker
- ❌ Tidak ada agent loop (masih pipa tetap)
- ❌ Tidak ada webhook masuk selain OnlyOffice callback

---

## BAGIAN 1 — KENAPA RENCANA INI PERLU (alasan bisnis, bukan teknologi)

Tiga hal yang Bos soroti dan belum terjawab:

1. **Komentar pembimbing sering datang lewat WA/Telegram.** Mahasiswa meneruskan
   pesan dosen dari HP. Sekarang ia harus buka laptop, unggah, ketik ulang.
2. **Mahasiswa tidak tahu apa yang harus diminta.** Ia tahu "bab 3 saya kurang",
   tapi tidak tahu harus bilang apa ke AI. Prinsip Bos §4.17: *AI = PEMANDU,
   bukan penanya.*
3. **Revisi bisa bertingkat.** Revisi → AI lain menilai → kalau kurang, ulangi.
   Sekarang masih satu tembakan.

---

## BAGIAN 2 — URUTAN PEMBANGUNAN (7 LANGKAH, JANGAN LOMPAT)

Prinsip: **matangkan yang pasti dulu, baru tambah ketidakpastian.**

| # | Langkah | Status | Risiko kalau lompat |
|---|---|---|---|
| 1 | Lapis 1 jenis dokumen + prompt presisi | ✅ **SELESAI 16Sep26** | — |
| 2 | Uji simulasi komentar pembimbing ↔ naskah nyata | ⬜ **BERIKUTNYA** | Tanpa ini, tidak ada bukti cakupan revisi benar |
| 3 | Perbaiki sisa: dukung PDF + bug tampilan | ⬜ | PDF tidak terbaca = user unggah sia-sia |
| 4 | Agentic ringan: **revisi bertingkat** (revisi→nilai→ulang) | ⬜ | Kalau lewat, kualitas tidak terjamin |
| 5 | Agentic: **pemeriksa etika** (agent terpisah) | ⬜ | — |
| 6 | **Telegram/WA** (pintu masuk chat) | ⬜ | Kalau duluan, biaya bocor tanpa gerbang |
| 7 | Agentic penuh (AI putuskan urutan sendiri) | ⬜ | Paling mahal & paling sulit diprediksi |

### 🔴 ATURAN URUTAN (kenapa begini)

- **Langkah 6 (chat) JANGAN sebelum Langkah 4-5.** Chat = panggilan AI bebas.
  Tanpa gerbang biaya & mutu, biaya bocor.
- **Langkah 7 (agentic penuh) PALING AKHIR.** Agentic = AI memutuskan urutan.
  Kalau pipa tetapnya belum terbukti benar, agentic hanya menambah kekacauan.
- **Langkah 2 WAJIB sebelum 4.** Uji komentar pembimbing dulu — itu fondasi
  penilaian kualitas revisi. Tanpa itu, agentic tidak punya "ukuran benar".

---

## BAGIAN 3 — RANCANGAN INFRASTRUKTUR (BELUM DIJALANKAN)

### 3.1 PRINSIP: JANGAN TUMPANG TINDIH

| Prinsip | Arti praktis |
|---|---|
| **Satu jalur AI** | Semua lewat `9router`. Tidak bikin klien LLM kedua. |
| **Satu sumber kebenaran data** | Naskah & DB tetap di `eduai-app`. Bot chat **tidak** menyimpan salinan sendiri. |
| **Bot chat = PINTU, bukan otak** | Telegram/WA hanya meneruskan. Seluruh logika tetap di `app/` EduAi. |
| **Pakai ulang GOWA yang ada** | GOWA sudah terpasang. Jangan install gateway WA baru. |
| **Jangan ganggu proyek lain** | `blast_app`/`wa-blast-net` & OJS **tidak disentuh**. |

### 3.2 KOMPONEN BARU YANG DIUSULKAN

```
                        ┌──────────────────────────┐
   Mahasiswa (HP) ─────▶│  telegram-bot-eduai      │  container BARU
                        │  (pintu masuk chat)      │  port: bebas (mis. 8110)
                        └───────────┬──────────────┘
                                    │ HTTP internal
                                    │ (eduai-net)
                        ┌───────────▼──────────────┐
                        │  eduai-app (SUDAH ADA)   │  ⭐ OTAK — tidak diubah
                        │  + endpoint /api/chat/*  │     hanya DITAMBAH route
                        └───────────┬──────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
     ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐
     │ eduai.db       │  │ 9router          │  │ oo-converter   │
     │ (SUDAH ADA)    │  │ (SUDAH ADA)      │  │ (SUDAH ADA)    │
     └────────────────┘  └──────────────────┘  └────────────────┘
```

**Aturan penting:** `eduai-app` menyediakan **endpoint internal** yang dipanggil
bot. Bot **tidak pernah** menyentuh DB atau file langsung.

### 3.3 ENDPOINT INTERNAL YANG DIUSULKAN (di `eduai-app`, belum dibuat)

```
POST /api/chat/mulai        → tautkan chat_id ke akun EduAi (sekali)
POST /api/chat/naskah       → kirim naskah dari chat (unggah)
POST /api/chat/komentar     → kirim komentar pembimbing → AI merevisi
GET  /api/chat/status/<job> → cek kemajuan (untuk balasan bertahap)
GET  /api/chat/kuota        → sisa kuota user
```

Semua endpoint **wajib**:
- pakai **kunci internal** (bukan kunci user) — header `X-Internal-Key`
- ambil kuota dari DB yang sama (gerbang biaya sama seperti web)
- catat log ke tabel yang sama (`revisi_history`) — supaya laporan keuangan satu sumber

### 3.4 JALUR WA (pakai GOWA yang sudah ada)

```
Mahasiswa (WA) ─▶ gowa (SUDAH ADA, port 3000) ─▶ webhook ─▶ eduai-app
                                                            (endpoint sama)
```

**Yang perlu diperhatikan:**
- GOWA sekarang `Exited` → perlu dihidupkan **saat langkah 6**, bukan sekarang
- Nomor WA terpisah dari nomor UPB WA Blast (jangan pakai nomor yang sama —
  risiko akun terblokir & laporan keuangan bercampur)
- WA tidak punya tombol → kirim **teks nomor** untuk pilihan
  (`Balas: 1 = Skripsi, 2 = Tesis, ...`)

### 3.5 PENAUTAN AKUN (sekali per user)

```
Mahasiswa: /mulai
Bot      : "Masukkan kode tautan dari eduai.bikinaja.id/profil"
Mahasiswa: "A7X-2K9"
Bot      : "✅ Tersambung. Sisa Token Revisi: 12."
```
- Kode tautan **sekali pakai**, kedaluwarsa 10 menit
- Disimpan di tabel BARU `chat_tautan` (`chat_id`, `user_id`, `platform`, `dibuat`)
- ⚠️ **Tabel baru, bukan ubah tabel lama** — supaya web tidak terganggu

---

## BAGIAN 4 — RANCANGAN AGENTIC (BELUM DIJALANKAN)

### 4.1 Definisi jujur

| | Sekarang | Agentic |
|---|---|---|
| Siapa putuskan urutan | **Kode** (pipa tetap) | **AI** |
| Jumlah panggilan AI | 1 per komentar | bisa 2-5 (revisi→nilai→ulang) |
| Bisa pakai alat (tool) | ❌ | ✅ (mis. cari referensi) |
| Biaya | rendah & terprediksi | lebih tinggi, perlu batas |
| Sulit diprediksi | rendah | tinggi |

### 4.2 Agentic RINGAN yang diusulkan (Langkah 4-5)

**Agent 1 — Penyusun Revisi** *(sudah ada, dipakai ulang)*
Prompt: `prompts/revisi_produksi.txt` v2.0.

**Agent 2 — Penilai Revisi** *(BARU, Langkah 4)*
- Tugas: menilai jawaban Agent 1 dengan **rubrik terukur**
- Rubrik: (a) cakupan sesuai? (b) G1–G9 dipatuhi? (c) istilah konsisten?
  (d) posisi bab benar?
- Keluaran: `LULUS` / `ULANGI + alasan`
- Kalau `ULANGI` → Agent 1 dijalankan lagi **maks 1×** (biar biaya terkendali)
- 🔴 **Batas keras:** maks 2 putaran. Tanpa batas, biaya bisa tak terhingga.

**Agent 3 — Pemeriksa Etika** *(BARU, Langkah 5)*
- Bahasa regex **Rp 0 dulu** (contoh sudah ada: `penelitian-bot/agents/ethics-checker.js`)
- Menolak: fabrikasi data, paksa R²/p-value, lewati uji validitas
- AI hanya dipanggil kalau regex ragu

### 4.3 Agentic PENUH (Langkah 7) — usulan, tapi dengan catatan

Usulan bentuknya: AI diberi **daftar alat** dan memilih sendiri:
```
alat tersedia:
  - baca_bagian(nama)      → baca sub-bab tertentu
  - cek_konsistensi()      → Rp 0
  - cari_referensi(kata)   → verifikasi nyata
  - petakan_bab()          → Rp 0
  - ajukan_ke_user(tanya)  → tanya mahasiswa
```

⚠️ **CATATAN PENTING WULAN (jujur):** untuk pekerjaan **merevisi naskah**,
agentic penuh **belum tentu lebih baik**. Revisi butuh **terkontrol**, bukan
bebas. Agentic lebih cocok untuk **mencari informasi**. Jadi Langkah 7 ini
sebaiknya diputuskan **setelah** langkah 4-6 terbukti.

---

## BAGIAN 5 — YANG **TIDAK** BOLEH DILAKUKAN (pagar)

| # | Larangan | Alasan |
|---|---|---|
| 1 | ❌ Jangan bikin jalur AI kedua | Gerbang biaya harus satu pintu (`9router`) |
| 2 | ❌ Jangan simpan naskah di bot chat | Dua salinan = data tidak sinkron |
| 3 | ❌ Jangan pakai jaringan `wa-blast-net` / `oja_ojs_net` | Milik proyek lain, bisa saling ganggu |
| 4 | ❌ Jangan pakai port `80/443/8080/8081/8100/8765/9119/18081` | Sudah terpakai |
| 5 | ❌ Jangan hardcode batas angka di JS/kode bot | Pelajaran 15Sep26: batas ukuran berkas |
| 6 | ❌ Jangan pakai nomor WA yang sama dengan UPB WA Blast | Laporan bercampur & risiko blokir |
| 7 | ❌ Jangan jalankan chat/agentic sebelum gerbang biaya diuji | Biaya bocor |
| 8 | ❌ Jangan ubah tabel DB lama untuk fitur chat | Pakai tabel baru (`chat_tautan`) |

---

## BAGIAN 6 — YANG PERLU DIPUTUSKAN BOS (sebelum langkah 6 dimulai)

1. **Nomor WA & nomor Telegram mana** yang dipakai EduAi? (terpisah dari UPB)
2. **Paket mana yang dapat akses chat?** Semua paket, atau minimal Penulis?
3. **Chat dihitung Token Revisi sama seperti web?** (Wulan usul: **ya**, sama)
4. **Kalau chat bebas tanya tanpa revisi** — apakah tetap kena kuota?
   (Wulan usul: pertanyaan konsultasi **gratis** dengan batas harian, revisi tetap berbayar)
5. **Nama bot** yang tampil ke mahasiswa?

---

## BAGIAN 7 — RINGKASAN SATU LAYAR

```
SEKARANG (LIVE):
  Mahasiswa → web eduai.bikinaja.id → unggah → komentar → AI revisi
  AI: 1 panggilan, pipa tetap, semua lewat 9router
  Jenis dokumen: sudah dideteksi ✅ (16Sep26)
  Prompt: sudah presisi 16 KB ✅ (16Sep26)

NANTI (RENCANA — belum dijalankan):
  Langkah 2: uji simulasi komentar pembimbing        ← berikutnya
  Langkah 3: dukung PDF + bug tampilan
  Langkah 4: agentic ringan (penilai revisi)         ← butuh keputusan
  Langkah 5: pemeriksa etika (regex Rp 0 dulu)
  Langkah 6: Telegram + WA (pakai GOWA yang ada)     ← butuh ACC Bos
  Langkah 7: agentic penuh                           ← diputuskan nanti

INFRASTRUKTUR BARU = MINIMAL:
  + 1 container bot chat (pintu masuk saja)
  + 1 tabel chat_tautan
  + beberapa endpoint /api/chat/* di eduai-app
  + 1 jaringan docker `eduai-net` (sudah ada, belum dipakai)
  TIDAK ada perubahan pada: 9router, DB, uploads, oo-converter
```

---

*Dibuat: 16 Sep 2026 · Status: RANCANGAN · Jangan dijalankan tanpa ACC Bos*
